from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import ImageGrab

from .models import (
    EvidenceStep,
    FinalizeResult,
    InputArtifact,
    InputRegistrationResult,
    RegisteredOutput,
    StagePlanResult,
    StageRequirement,
)
from .sessions import Session
from .win32 import find_window, focus_window


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load(session: Session) -> dict[str, Any]:
    return json.loads(session.manifest_path.read_text(encoding="utf-8"))


def _save(session: Session, manifest: dict[str, Any]) -> None:
    temporary = session.manifest_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(session.manifest_path)


def _safe_stage_id(stage_id: str) -> str:
    cleaned = re.sub(r"[^\w\-.\u4e00-\u9fff]+", "-", stage_id, flags=re.UNICODE).strip("-._")
    if not cleaned:
        raise ValueError("stage_id 必须包含字母、数字或中文。")
    return cleaned[:80]


def capture_evidence(
    session: Session,
    stage_id: str,
    caption: str,
    action_summary: str = "",
    parameters: dict[str, Any] | None = None,
    window_title_contains: str | None = None,
    evidence_type: str = "result",
) -> EvidenceStep:
    if not caption.strip():
        raise ValueError("caption 不能为空。")
    manifest = _load(session)
    plan = manifest.get("stage_plan")
    if not plan or not plan.get("locked"):
        raise ValueError("必须先根据指导书冻结步骤计划，之后才能截图。")
    requirements = {item["stage_id"]: item for item in plan["stages"]}
    requirement = requirements.get(stage_id)
    if requirement is None:
        raise ValueError(f"stage_id 不在冻结的步骤计划中：{stage_id}")
    if any(step["stage_id"] == stage_id for step in manifest["steps"]):
        raise ValueError(f"该阶段已经截图，不能用另一张图替换：{stage_id}")
    if evidence_type != requirement["evidence_type"]:
        raise ValueError(
            f"{stage_id} 的证据类型应为 {requirement['evidence_type']}，实际为 {evidence_type}。"
        )
    actual_parameters = parameters or {}
    missing_parameters = [
        name for name in requirement.get("required_parameters", []) if name not in actual_parameters
    ]
    if missing_parameters:
        raise ValueError(f"{stage_id} 缺少必需参数：{', '.join(missing_parameters)}")
    ordinal = len(manifest["steps"]) + 1
    safe_stage = _safe_stage_id(stage_id)
    target_filter = window_title_contains or requirement.get("expected_window_contains")
    target = find_window(session.process_id, target_filter)
    focus_window(target.handle)
    time.sleep(0.25)

    screenshot_path = session.screenshots_dir / f"{ordinal:03d}-{safe_stage}.png"
    if screenshot_path.exists():
        raise FileExistsError(f"不会覆盖既有截图：{screenshot_path}")

    image = ImageGrab.grab(
        bbox=(target.left, target.top, target.right, target.bottom),
        include_layered_windows=True,
        all_screens=True,
    )
    image.save(screenshot_path, format="PNG")
    width, height = image.size
    step = EvidenceStep(
        ordinal=ordinal,
        stage_id=stage_id,
        caption=caption.strip(),
        action_summary=action_summary.strip(),
        parameters=actual_parameters,
        evidence_type=evidence_type,
        window_title=target.title,
        screenshot_path=str(screenshot_path.resolve()),
        sha256=_sha256(screenshot_path),
        captured_at=_utc_now(),
        width=width,
        height=height,
    )
    manifest["steps"].append(step.model_dump(mode="json"))
    _save(session, manifest)
    return step


def _within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def _input_artifact(session: Session, path: str, role: str) -> InputArtifact:
    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        raise ValueError(f"{role} 输入文件不存在：{candidate}")
    if not _within(session.workspace_root, candidate):
        raise ValueError(f"{role} 输入必须位于实验工作区内：{candidate}")
    return InputArtifact(
        role=role,
        path=str(candidate),
        sha256=_sha256(candidate),
        size_bytes=candidate.stat().st_size,
    )


def register_inputs(
    session: Session,
    guide_path: str,
    template_path: str,
    data_paths: list[str],
) -> InputRegistrationResult:
    if not data_paths:
        raise ValueError("data_paths 至少包含一个老师提供的数据文件。")
    manifest = _load(session)
    if manifest.get("steps") or manifest.get("stage_plan"):
        raise ValueError("必须在冻结步骤计划和截图前登记老师输入。")
    if manifest.get("inputs"):
        raise ValueError("老师输入已经登记；为保证审计链，不允许中途替换。")

    guide = _input_artifact(session, guide_path, "guide")
    template = _input_artifact(session, template_path, "template")
    data = [_input_artifact(session, path, "data") for path in data_paths]
    paths = [artifact.path.casefold() for artifact in [guide, template, *data]]
    if len(paths) != len(set(paths)):
        raise ValueError("指导书、模板和数据路径不能重复。")

    artifacts = [guide, template, *data]
    manifest["inputs"] = [artifact.model_dump(mode="json") for artifact in artifacts]
    manifest["validation"] = None
    _save(session, manifest)
    return InputRegistrationResult(
        session_id=session.session_id,
        inputs=artifacts,
        manifest_path=str(session.manifest_path),
    )


def set_stage_plan(
    session: Session,
    stages: list[StageRequirement],
    require_output: bool = True,
) -> StagePlanResult:
    if not stages:
        raise ValueError("步骤计划不能为空。")
    manifest = _load(session)
    roles = {item.get("role") for item in manifest.get("inputs", [])}
    diagnostic = manifest.get("session", {}).get("mode") == "diagnostic"
    if not diagnostic and not {"guide", "template", "data"} <= roles:
        raise ValueError("必须先登记老师的数据、指导书和模板。")
    if manifest.get("steps"):
        raise ValueError("已有截图后不能再建立或修改步骤计划。")
    if manifest.get("stage_plan"):
        raise ValueError("步骤计划已经冻结，不能在同一会话中替换。")

    stage_ids = [stage.stage_id.strip() for stage in stages]
    if any(not stage_id for stage_id in stage_ids):
        raise ValueError("stage_id 不能为空。")
    if len(stage_ids) != len(set(stage_ids)):
        raise ValueError("步骤计划中的 stage_id 必须唯一。")
    if any(not stage.caption.strip() or not stage.action_summary.strip() for stage in stages):
        raise ValueError("每个步骤必须包含图题和可复现的操作摘要。")

    plan = {
        "locked": True,
        "locked_at": _utc_now(),
        "minimum_screenshots": len(stages),
        "require_output": require_output,
        "stages": [stage.model_dump(mode="json") for stage in stages],
    }
    manifest["stage_plan"] = plan
    manifest["required_stages"] = stage_ids
    manifest["validation"] = None
    _save(session, manifest)
    return StagePlanResult(
        session_id=session.session_id,
        stage_count=len(stages),
        minimum_screenshots=len(stages),
        require_output=require_output,
        locked=True,
        manifest_path=str(session.manifest_path),
    )


def register_output(
    session: Session,
    path: str,
    label: str,
    metadata: dict[str, Any] | None = None,
) -> RegisteredOutput:
    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        raise ValueError(f"输出文件不存在：{candidate}")
    if not _within(session.workspace_root, candidate):
        raise ValueError("只允许登记实验工作区内的输出文件。")
    if not label.strip():
        raise ValueError("label 不能为空。")
    output = RegisteredOutput(
        label=label.strip(),
        path=str(candidate),
        sha256=_sha256(candidate),
        size_bytes=candidate.stat().st_size,
        metadata=metadata or {},
    )
    manifest = _load(session)
    manifest["outputs"].append(output.model_dump(mode="json"))
    _save(session, manifest)
    return output


def _render_markdown(manifest: dict[str, Any], validation: dict[str, Any]) -> str:
    session = manifest["session"]
    lines = [
        "# ENVI Classic 实验报告证据包",
        "",
        f"- 实验：{session['experiment_name']}",
        f"- ENVI 版本：{session.get('envi_version', '未知')}",
        f"- 运行目录：`{session['run_dir']}`",
        f"- 完整性：{'通过' if validation['complete'] else '未通过'}",
        "",
        "## 老师输入",
        "",
    ]
    for artifact in manifest.get("inputs", []):
        lines.append(
            f"- {artifact['role']}：`{artifact['path']}`（SHA-256 `{artifact['sha256']}`）"
        )
    plan = manifest.get("stage_plan") or {}
    lines.extend(
        [
            "",
            "## 冻结的步骤计划",
            "",
            f"- 阶段数：{len(plan.get('stages', []))}",
            f"- 已冻结：{'是' if plan.get('locked') else '否'}",
            "",
            "## 逐步截图",
            "",
        ]
    )
    for step in manifest["steps"]:
        lines.extend(
            [
                f"### {step['ordinal']}. {step['caption']}",
                "",
                f"- 阶段 ID：`{step['stage_id']}`",
                f"- 操作：{step.get('action_summary') or '未填写'}",
                f"- 证据类型：{step.get('evidence_type', 'result')}",
                f"- 窗口：{step['window_title']}",
                f"- 参数：`{json.dumps(step.get('parameters', {}), ensure_ascii=False)}`",
                f"- SHA-256：`{step['sha256']}`",
                f"- 截图：`{step['screenshot_path']}`",
                "",
                f"![{step['caption']}]({Path(step['screenshot_path']).as_posix()})",
                "",
            ]
        )
    lines.extend(["## 输出文件", ""])
    if manifest["outputs"]:
        for output in manifest["outputs"]:
            lines.append(f"- {output['label']}：`{output['path']}`（SHA-256 `{output['sha256']}`）")
    else:
        lines.append("- 尚未登记输出文件。")
    lines.extend(["", "## 完整性检查", "", "```json", json.dumps(validation, ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def finalize_evidence(
    session: Session,
    required_stages: list[str] | None = None,
    min_screenshots: int | None = None,
    require_output: bool | None = None,
    require_inputs: bool = True,
    require_stage_plan: bool = True,
) -> FinalizeResult:
    manifest = _load(session)
    diagnostic_mode = manifest.get("session", {}).get("mode") == "diagnostic"
    if diagnostic_mode:
        require_inputs = False
    plan = manifest.get("stage_plan")
    plan_locked = bool(plan and plan.get("locked"))
    planned_stages = [stage["stage_id"] for stage in (plan or {}).get("stages", [])]
    supplied = [stage.strip() for stage in (required_stages or []) if stage.strip()]
    if plan_locked and supplied and supplied != planned_stages:
        raise ValueError("required_stages 与冻结的指导书步骤计划不一致，不能降低证据要求。")
    required = planned_stages if plan_locked else supplied
    if len(set(required)) != len(required):
        raise ValueError("required_stages 本身不能包含重复项。")

    planned_minimum = int((plan or {}).get("minimum_screenshots", len(required) or 1))
    if min_screenshots is None:
        min_screenshots = planned_minimum
    elif plan_locked and min_screenshots < planned_minimum:
        raise ValueError("min_screenshots 不能低于冻结步骤计划的阶段数。")
    if min_screenshots < 1:
        raise ValueError("min_screenshots 必须至少为 1。")

    planned_output = bool((plan or {}).get("require_output", True))
    if require_output is None:
        require_output = planned_output
    elif plan_locked and planned_output and not require_output:
        raise ValueError("冻结步骤计划要求输出文件，不能在验收时关闭。")

    steps = manifest["steps"]
    captured = [step["stage_id"] for step in steps]
    counts = Counter(captured)
    missing = [stage for stage in required if counts[stage] == 0]
    duplicate = [stage for stage, count in counts.items() if count > 1]

    required_positions = [captured.index(stage) for stage in required if stage in captured]
    out_of_order: list[str] = []
    if required_positions != sorted(required_positions):
        last_position = -1
        for stage in required:
            if stage in captured:
                position = captured.index(stage)
                if position < last_position:
                    out_of_order.append(stage)
                last_position = max(last_position, position)

    invalid_screenshots: list[str] = []
    for step in steps:
        screenshot = Path(step["screenshot_path"])
        if not screenshot.is_file() or _sha256(screenshot) != step["sha256"]:
            invalid_screenshots.append(step["stage_id"])

    inputs = manifest.get("inputs", [])
    roles = {artifact.get("role") for artifact in inputs}
    missing_input_roles = (
        [] if diagnostic_mode else [role for role in ("guide", "template", "data") if role not in roles]
    )
    invalid_inputs: list[str] = []
    for artifact in inputs:
        path = Path(artifact["path"])
        if not path.is_file() or _sha256(path) != artifact["sha256"]:
            invalid_inputs.append(artifact["path"])

    enough_screenshots = len(steps) >= min_screenshots
    output_ok = bool(manifest["outputs"]) or not require_output
    inputs_ok = (not missing_input_roles and not invalid_inputs) or not require_inputs
    plan_ok = plan_locked or not require_stage_plan
    complete = (
        not missing
        and not duplicate
        and not out_of_order
        and not invalid_screenshots
        and enough_screenshots
        and output_ok
        and inputs_ok
        and plan_ok
    )

    reasons: list[str] = []
    if require_inputs and missing_input_roles:
        reasons.append("缺少老师输入角色：" + "、".join(missing_input_roles))
    if require_inputs and invalid_inputs:
        reasons.append("老师输入缺失或哈希不一致：" + "、".join(invalid_inputs))
    if require_stage_plan and not plan_locked:
        reasons.append("尚未冻结指导书步骤计划")
    if missing:
        reasons.append("缺少阶段：" + "、".join(missing))
    if duplicate:
        reasons.append("阶段截图重复：" + "、".join(duplicate))
    if out_of_order:
        reasons.append("阶段顺序错误：" + "、".join(out_of_order))
    if invalid_screenshots:
        reasons.append("截图缺失或哈希不一致：" + "、".join(invalid_screenshots))
    if not enough_screenshots:
        reasons.append(f"截图数量 {len(steps)} 少于要求 {min_screenshots}")
    if not output_ok:
        reasons.append("尚未登记任何实验输出文件")
    message = "证据包完整，可以进入报告生成。" if complete else "证据包不完整：" + "；".join(reasons)

    validation = {
        "validated_at": _utc_now(),
        "session_mode": manifest.get("session", {}).get("mode", "experiment"),
        "complete": complete,
        "input_count": len(inputs),
        "missing_input_roles": missing_input_roles,
        "invalid_inputs": invalid_inputs,
        "stage_plan_locked": plan_locked,
        "required_stages": required,
        "missing_stages": missing,
        "duplicate_stages": duplicate,
        "out_of_order_stages": out_of_order,
        "invalid_screenshots": invalid_screenshots,
        "screenshot_count": len(steps),
        "minimum_screenshots": min_screenshots,
        "output_count": len(manifest["outputs"]),
        "require_output": require_output,
        "message": message,
    }
    manifest["required_stages"] = required
    manifest["validation"] = validation
    _save(session, manifest)

    evidence_markdown = session.run_dir / "report-evidence.md"
    evidence_markdown.write_text(_render_markdown(manifest, validation), encoding="utf-8")
    return FinalizeResult(
        complete=complete,
        input_count=len(inputs),
        missing_input_roles=missing_input_roles,
        invalid_inputs=invalid_inputs,
        stage_plan_locked=plan_locked,
        missing_stages=missing,
        duplicate_stages=duplicate,
        out_of_order_stages=out_of_order,
        invalid_screenshots=invalid_screenshots,
        screenshot_count=len(steps),
        output_count=len(manifest["outputs"]),
        manifest_path=str(session.manifest_path),
        evidence_markdown_path=str(evidence_markdown),
        message=message,
    )
