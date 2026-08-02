from __future__ import annotations

import time
from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .discovery import health_result
from .evidence import (
    capture_evidence,
    finalize_evidence,
    register_inputs,
    register_output,
    set_stage_plan,
)
from .models import (
    EvidenceStep,
    FinalizeResult,
    HealthResult,
    InputRegistrationResult,
    MenuInvokeResult,
    MenuListResult,
    RecipeAction,
    RecipeResult,
    RegisteredOutput,
    SessionInfo,
    StagePlanResult,
    StageRequirement,
    WindowListResult,
)
from .sessions import SESSIONS
from .win32 import (
    click_window,
    enum_windows_for_pid,
    find_window,
    invoke_menu_path,
    list_menu_items,
    press_key,
    type_text,
    wait_for_window,
)


SERVER_INSTRUCTIONS = """仅用于 ENVI Classic 5.6 遥感实验自动化。先 health_check，再 launch；随后登记老师的数据、指导书和模板，并在任何截图前冻结由指导书拆出的步骤计划。只能操作本服务启动的 ENVI 会话；先用 list_menu_items 找到真实菜单路径，再调用 invoke_menu 或 run_recipe。每个工具状态、参数对话框和结果视图都必须按冻结计划 capture_evidence。实验输出必须 register_output。最终验收只能使用冻结计划，不能临时删减必需步骤；complete=false 时不得生成或宣称完成实验报告。不要把同一截图冒充多个步骤，也不要使用本服务操作其他桌面应用。"""

mcp = MCPServer(
    name="envi_classic_mcp",
    title="ENVI Classic 5.6 遥感实验自动化",
    description="受限控制 ENVI Classic 5.6，并生成逐步截图与可验证报告证据包。",
    instructions=SERVER_INSTRUCTIONS,
    version="0.3.0",
    log_level="ERROR",
)


READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
LOCAL_MUTATION = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)


@mcp.tool(
    title="检查 ENVI Classic 5.6 环境",
    description="读取本机注册表和安装文件，确认 ENVI Classic 5.6（64 位）能否被安全启动。",
    annotations=READ_ONLY,
    structured_output=True,
)
def envi_classic_health_check() -> HealthResult:
    return health_result(SESSIONS.active_count)


@mcp.tool(
    title="启动受控 ENVI Classic 会话",
    description="在指定实验工作区下创建全新的证据目录并启动 ENVI Classic 5.6。只返回本服务可控制的会话 ID。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_launch(
    workspace_root: str,
    experiment_name: str,
    timeout_seconds: float = 30.0,
    mode: str = "experiment",
) -> SessionInfo:
    session = SESSIONS.launch(
        workspace_root,
        experiment_name,
        timeout_seconds=timeout_seconds,
        mode=mode,
    )
    return session.to_info()


@mcp.tool(
    title="登记老师提供的实验输入",
    description="在截图前登记老师的数据、实验指导书和报告模板，逐文件计算 SHA-256 并写入证据清单；输入必须位于实验工作区内。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_register_inputs(
    session_id: str,
    guide_path: str,
    template_path: str,
    data_paths: list[str],
) -> InputRegistrationResult:
    session = SESSIONS.get(session_id)
    return register_inputs(
        session,
        guide_path=guide_path,
        template_path=template_path,
        data_paths=data_paths,
    )


@mcp.tool(
    title="冻结指导书步骤与截图计划",
    description="把指导书拆出的有序阶段、证据类型、必填参数和预期窗口写入清单并锁定。锁定后不能替换或降低阶段要求。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_set_stage_plan(
    session_id: str,
    stages: list[StageRequirement],
    require_output: bool = True,
) -> StagePlanResult:
    session = SESSIONS.get(session_id)
    return set_stage_plan(session, stages=stages, require_output=require_output)


@mcp.tool(
    title="列出会话的 ENVI 窗口",
    description="列出指定受控 ENVI 进程当前拥有的可见顶层窗口、标题和几何信息。",
    annotations=READ_ONLY,
    structured_output=True,
)
def envi_classic_list_windows(session_id: str) -> WindowListResult:
    session = SESSIONS.get(session_id)
    return WindowListResult(session_id=session_id, windows=enum_windows_for_pid(session.process_id))


@mcp.tool(
    title="列出 ENVI Classic 原生菜单",
    description="分页返回 ENVI Classic 主窗口的真实 Win32 菜单路径和命令 ID；可用 filter_text 缩小结果。",
    annotations=READ_ONLY,
    structured_output=True,
)
def envi_classic_list_menu_items(
    session_id: str,
    filter_text: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> MenuListResult:
    if offset < 0:
        raise ValueError("offset 不能为负数。")
    if limit < 1 or limit > 200:
        raise ValueError("limit 必须在 1 到 200 之间。")
    session = SESSIONS.get(session_id)
    main = find_window(session.process_id, "ENVI Classic")
    items = list_menu_items(main.handle)
    if filter_text:
        needle = filter_text.casefold()
        items = [item for item in items if needle in " -> ".join(item.path).casefold()]
    page = items[offset : offset + limit]
    next_offset = offset + limit if offset + limit < len(items) else None
    return MenuListResult(
        session_id=session_id,
        total=len(items),
        offset=offset,
        next_offset=next_offset,
        items=page,
    )


@mcp.tool(
    title="调用 ENVI Classic 菜单",
    description="按完整菜单名称路径调用原生 WM_COMMAND，不依赖菜单像素坐标。路径示例：[\"Filter\", \"Convolutions and Morphology\"]。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_invoke_menu(session_id: str, menu_path: list[str]) -> MenuInvokeResult:
    session = SESSIONS.get(session_id)
    main = find_window(session.process_id, "ENVI Classic")
    command_id = invoke_menu_path(main.handle, menu_path)
    return MenuInvokeResult(session_id=session_id, menu_path=menu_path, command_id=command_id)


def _execute_action(session_id: str, action: RecipeAction) -> dict[str, Any]:
    session = SESSIONS.get(session_id)
    if action.type == "invoke_menu":
        main = find_window(session.process_id, "ENVI Classic")
        command_id = invoke_menu_path(main.handle, action.menu_path or [])
        return {"type": action.type, "menu_path": action.menu_path, "command_id": command_id}
    if action.type == "wait_window":
        window = wait_for_window(
            session.process_id,
            action.window_title_contains or "",
            timeout_seconds=action.timeout_seconds,
        )
        return {"type": action.type, "window": window.model_dump(mode="json")}
    if action.type in {"click", "double_click"}:
        window = find_window(session.process_id, action.window_title_contains)
        x, y = click_window(
            window,
            action.x_ratio if action.x_ratio is not None else 0.5,
            action.y_ratio if action.y_ratio is not None else 0.5,
            double=action.type == "double_click",
        )
        return {"type": action.type, "window_title": window.title, "screen_point": [x, y]}
    if action.type == "type_text":
        window = find_window(session.process_id, action.window_title_contains)
        type_text(window, action.text or "")
        return {"type": action.type, "window_title": window.title, "characters_typed": len(action.text or "")}
    if action.type == "key":
        window = find_window(session.process_id, action.window_title_contains)
        press_key(window, action.key or "")
        return {"type": action.type, "window_title": window.title, "key": action.key}
    if action.type == "sleep":
        time.sleep(action.seconds or 0.0)
        return {"type": action.type, "seconds": action.seconds}
    if action.type == "capture":
        step = capture_evidence(
            session,
            stage_id=action.stage_id or "",
            caption=action.caption or "",
            action_summary="配方自动截图",
            parameters=action.parameters,
            window_title_contains=action.window_title_contains,
            evidence_type=action.evidence_type,
        )
        return {"type": action.type, "evidence": step.model_dump(mode="json")}
    raise ValueError(f"未知配方动作：{action.type}")


@mcp.tool(
    title="执行受限 ENVI GUI 配方",
    description="顺序执行最多 100 个受限动作：菜单、等待窗口、窗口内相对点击、文本、按键、短等待和证据截图。dry_run 只验证动作，不操作 GUI。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_run_recipe(
    session_id: str,
    actions: list[RecipeAction],
    dry_run: bool = False,
) -> RecipeResult:
    SESSIONS.get(session_id)
    if not actions:
        raise ValueError("actions 不能为空。")
    if len(actions) > 100:
        raise ValueError("单个配方最多包含 100 个动作。")
    if dry_run:
        return RecipeResult(
            session_id=session_id,
            dry_run=True,
            completed_actions=0,
            results=[{"index": index, "type": action.type, "valid": True} for index, action in enumerate(actions, 1)],
        )

    results: list[dict[str, Any]] = []
    for index, action in enumerate(actions, 1):
        result = _execute_action(session_id, action)
        results.append({"index": index, **result})
    return RecipeResult(
        session_id=session_id,
        dry_run=False,
        completed_actions=len(results),
        results=results,
    )


@mcp.tool(
    title="保存一步实验截图证据",
    description="截取指定受控 ENVI 窗口，按顺序保存 PNG，并把阶段、说明、参数、窗口标题、时间和 SHA-256 写入证据清单。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_capture_evidence(
    session_id: str,
    stage_id: str,
    caption: str,
    action_summary: str = "",
    parameters: dict[str, Any] | None = None,
    window_title_contains: str | None = None,
    evidence_type: str = "result",
) -> EvidenceStep:
    session = SESSIONS.get(session_id)
    return capture_evidence(
        session,
        stage_id=stage_id,
        caption=caption,
        action_summary=action_summary,
        parameters=parameters,
        window_title_contains=window_title_contains,
        evidence_type=evidence_type,
    )


@mcp.tool(
    title="登记实验输出文件",
    description="登记实验工作区内已经生成的结果文件并计算哈希。不会修改结果文件，也不允许读取工作区外的文件。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_register_output(
    session_id: str,
    path: str,
    label: str,
    metadata: dict[str, Any] | None = None,
) -> RegisteredOutput:
    session = SESSIONS.get(session_id, require_running=False)
    return register_output(session, path=path, label=label, metadata=metadata)


@mcp.tool(
    title="校验并完成报告证据包",
    description="按指导书顺序检查必需阶段、截图哈希、重复项、顺序和输出文件；生成 JSON 与 Markdown 证据包。complete=false 时不得进入报告生成。",
    annotations=LOCAL_MUTATION,
    structured_output=True,
)
def envi_classic_finalize_evidence(
    session_id: str,
) -> FinalizeResult:
    session = SESSIONS.get(session_id, require_running=False)
    return finalize_evidence(session)


@mcp.tool(
    title="关闭受控 ENVI 会话",
    description="只关闭由本服务启动的指定 ENVI 进程。默认先正常关闭；若存在未保存提示则保留进程。force=true 才会强制终止。",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False),
    structured_output=True,
)
def envi_classic_close_session(
    session_id: str,
    force: bool = False,
    timeout_seconds: float = 8.0,
) -> dict[str, object]:
    return SESSIONS.close(session_id, force=force, timeout_seconds=timeout_seconds)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
