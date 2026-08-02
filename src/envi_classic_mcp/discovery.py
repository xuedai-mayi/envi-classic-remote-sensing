from __future__ import annotations

import os
import platform
from pathlib import Path

from .models import EnviInstallation, HealthResult


REGISTRY_PATHS = (
    r"SOFTWARE\Harris\ENVI\5.6",
    r"SOFTWARE\Exelis\ENVI\5.6",
)


def _read_registry_installation() -> tuple[str | None, str | None, str | None]:
    if os.name != "nt":
        return None, None, None

    import winreg

    access_modes = [winreg.KEY_READ]
    if hasattr(winreg, "KEY_WOW64_64KEY"):
        access_modes.insert(0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)

    for registry_path in REGISTRY_PATHS:
        for access in access_modes:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, access) as key:
                    install_dir = str(winreg.QueryValueEx(key, "InstallDir")[0])
                    idl_install_dir = str(winreg.QueryValueEx(key, "IDLInstallDir")[0])
                    try:
                        version = str(winreg.QueryValueEx(key, "Version")[0])
                    except OSError:
                        version = "5.6"
                    return install_dir, idl_install_dir, version
            except OSError:
                continue
    return None, None, None


def discover_envi_classic() -> EnviInstallation:
    problems: list[str] = []
    if os.name != "nt":
        return EnviInstallation(found=False, problems=["ENVI Classic GUI 自动化仅支持 Windows。"])

    install_dir, idl_install_dir, version = _read_registry_installation()
    if not install_dir or not idl_install_dir:
        return EnviInstallation(
            found=False,
            version=version,
            install_dir=install_dir,
            idl_install_dir=idl_install_dir,
            problems=["未在注册表中找到 ENVI 5.6 安装信息。"],
        )

    executable = Path(idl_install_dir) / "bin" / "bin.x86_64" / "idlrt.exe"
    save_file = Path(idl_install_dir) / "lib" / "hook" / "envi.sav"
    if not executable.is_file():
        problems.append(f"未找到 64 位 IDL Runtime：{executable}")
    if not save_file.is_file():
        problems.append(f"未找到 ENVI Classic 保存文件：{save_file}")

    return EnviInstallation(
        found=not problems,
        version=version or "5.6",
        install_dir=str(Path(install_dir).resolve()),
        idl_install_dir=str(Path(idl_install_dir).resolve()),
        executable=str(executable.resolve()),
        save_file=str(save_file.resolve()),
        launch_arguments=["-nodemowarn", "-novm", str(save_file.resolve())],
        problems=problems,
    )


def health_result(active_sessions: int) -> HealthResult:
    envi = discover_envi_classic()
    notes = [
        "目标应用为 ENVI Classic 5.6（64 位）。",
        "MCP 只控制自己启动的 ENVI 进程，且不暴露任意命令执行。",
    ]
    return HealthResult(
        ok=envi.found,
        platform=platform.platform(),
        architecture=platform.machine(),
        envi=envi,
        active_server_sessions=active_sessions,
        notes=notes,
    )
