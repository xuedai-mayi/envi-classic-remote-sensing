from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .discovery import discover_envi_classic
from .models import SessionInfo
from .win32 import close_window, enum_windows_for_pid, wait_for_window


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_name(value: str, fallback: str = "experiment") -> str:
    cleaned = re.sub(r"[^\w\-.\u4e00-\u9fff]+", "-", value, flags=re.UNICODE).strip("-._")
    return (cleaned or fallback)[:80]


@dataclass
class Session:
    session_id: str
    process: subprocess.Popen[bytes]
    experiment_name: str
    mode: str
    workspace_root: Path
    run_dir: Path
    screenshots_dir: Path
    manifest_path: Path
    launched_at: str

    @property
    def process_id(self) -> int:
        return self.process.pid

    @property
    def is_running(self) -> bool:
        return self.process.poll() is None

    def to_info(self) -> SessionInfo:
        windows = enum_windows_for_pid(self.process_id) if self.is_running else []
        main = next((window for window in windows if window.title == "ENVI Classic"), None)
        if main is None and windows:
            main = max(windows, key=lambda window: window.width * window.height)
        return SessionInfo(
            session_id=self.session_id,
            process_id=self.process_id,
            experiment_name=self.experiment_name,
            mode=self.mode,
            workspace_root=str(self.workspace_root),
            run_dir=str(self.run_dir),
            screenshots_dir=str(self.screenshots_dir),
            manifest_path=str(self.manifest_path),
            main_window=main,
        )


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.RLock()

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(1 for session in self._sessions.values() if session.is_running)

    def launch(
        self,
        workspace_root: str,
        experiment_name: str,
        timeout_seconds: float = 30.0,
        mode: str = "experiment",
    ) -> Session:
        if os.name != "nt":
            raise RuntimeError("ENVI Classic 5.6 GUI 自动化仅支持 Windows。")
        root = Path(workspace_root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"实验工作区不存在或不是目录：{root}")
        if mode not in {"experiment", "diagnostic"}:
            raise ValueError("mode 只能是 experiment 或 diagnostic。")

        installation = discover_envi_classic()
        if not installation.found or not installation.executable:
            raise RuntimeError("无法启动 ENVI Classic：" + "；".join(installation.problems))

        session_id = uuid.uuid4().hex
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_name = f"{timestamp}-{_safe_name(experiment_name)}-{session_id[:8]}"
        run_dir = root / ".envi-runs" / run_name
        screenshots_dir = run_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=False)
        manifest_path = run_dir / "report-evidence.json"

        command = [installation.executable, *installation.launch_arguments]
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        process = subprocess.Popen(command, cwd=run_dir, creationflags=creation_flags)
        session = Session(
            session_id=session_id,
            process=process,
            experiment_name=experiment_name,
            mode=mode,
            workspace_root=root,
            run_dir=run_dir,
            screenshots_dir=screenshots_dir,
            manifest_path=manifest_path,
            launched_at=_utc_now(),
        )

        try:
            wait_for_window(process.pid, "ENVI Classic", timeout_seconds=timeout_seconds)
        except Exception:
            if process.poll() is None:
                process.terminate()
            raise

        initial_manifest = {
            "schema_version": "2.0",
            "session": {
                "session_id": session_id,
                "process_id": process.pid,
                "experiment_name": experiment_name,
                "mode": mode,
                "workspace_root": str(root),
                "run_dir": str(run_dir),
                "launched_at": session.launched_at,
                "envi_version": installation.version,
                "envi_executable": installation.executable,
            },
            "inputs": [],
            "stage_plan": None,
            "required_stages": [],
            "steps": [],
            "outputs": [],
            "validation": None,
        }
        manifest_path.write_text(json.dumps(initial_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str, require_running: bool = True) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"未知 ENVI 会话：{session_id}")
        if require_running and not session.is_running:
            raise RuntimeError(f"ENVI 会话已经结束：{session_id}")
        return session

    def close(self, session_id: str, force: bool = False, timeout_seconds: float = 8.0) -> dict[str, object]:
        session = self.get(session_id, require_running=False)
        if not session.is_running:
            return {"session_id": session_id, "closed": True, "forced": False, "message": "会话已结束。"}

        windows = enum_windows_for_pid(session.process_id)
        for window in windows:
            close_window(window.handle)

        deadline = time.monotonic() + timeout_seconds
        while session.is_running and time.monotonic() < deadline:
            time.sleep(0.2)

        forced = False
        if session.is_running and force:
            session.process.terminate()
            forced = True
            try:
                session.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                session.process.kill()
                session.process.wait(timeout=5)

        closed = not session.is_running
        message = "会话已关闭。" if closed else "ENVI 仍在运行；可能有未保存提示。请检查界面，或显式设置 force=true。"
        return {"session_id": session_id, "closed": closed, "forced": forced, "message": message}


SESSIONS = SessionManager()
