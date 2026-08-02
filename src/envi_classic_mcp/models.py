from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EnviInstallation(StrictModel):
    found: bool
    version: str | None = None
    install_dir: str | None = None
    idl_install_dir: str | None = None
    executable: str | None = None
    save_file: str | None = None
    launch_arguments: list[str] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)


class HealthResult(StrictModel):
    ok: bool
    platform: str
    architecture: str
    envi: EnviInstallation
    active_server_sessions: int
    notes: list[str] = Field(default_factory=list)


class WindowInfo(StrictModel):
    handle: int
    title: str
    class_name: str
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int
    visible: bool


class MenuItem(StrictModel):
    path: list[str]
    command_id: int | None = None
    enabled: bool = True
    has_submenu: bool = False


class SessionInfo(StrictModel):
    session_id: str
    process_id: int
    experiment_name: str
    mode: Literal["experiment", "diagnostic"]
    workspace_root: str
    run_dir: str
    screenshots_dir: str
    manifest_path: str
    main_window: WindowInfo | None = None


class InputArtifact(StrictModel):
    role: Literal["guide", "template", "data"]
    path: str
    sha256: str
    size_bytes: int


class InputRegistrationResult(StrictModel):
    session_id: str
    inputs: list[InputArtifact]
    manifest_path: str


class StageRequirement(StrictModel):
    stage_id: str
    caption: str
    evidence_type: Literal["tool", "parameter", "result", "comparison", "output"]
    action_summary: str
    required_parameters: list[str] = Field(default_factory=list)
    expected_window_contains: str | None = None


class StagePlanResult(StrictModel):
    session_id: str
    stage_count: int
    minimum_screenshots: int
    require_output: bool
    locked: bool
    manifest_path: str


class WindowListResult(StrictModel):
    session_id: str
    windows: list[WindowInfo]


class MenuListResult(StrictModel):
    session_id: str
    total: int
    offset: int
    next_offset: int | None
    items: list[MenuItem]


class MenuInvokeResult(StrictModel):
    session_id: str
    menu_path: list[str]
    command_id: int


class RecipeAction(StrictModel):
    type: Literal[
        "invoke_menu",
        "wait_window",
        "click",
        "double_click",
        "type_text",
        "key",
        "sleep",
        "capture",
    ]
    menu_path: list[str] | None = None
    window_title_contains: str | None = None
    x_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    y_ratio: float | None = Field(default=None, ge=0.0, le=1.0)
    text: str | None = None
    key: str | None = None
    seconds: float | None = Field(default=None, ge=0.0, le=30.0)
    timeout_seconds: float = Field(default=15.0, ge=0.1, le=120.0)
    stage_id: str | None = None
    caption: str | None = None
    evidence_type: Literal["tool", "parameter", "result", "comparison", "output"] = "result"
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_action_fields(self) -> "RecipeAction":
        required: dict[str, tuple[str, ...]] = {
            "invoke_menu": ("menu_path",),
            "wait_window": ("window_title_contains",),
            "click": ("window_title_contains", "x_ratio", "y_ratio"),
            "double_click": ("window_title_contains", "x_ratio", "y_ratio"),
            "type_text": ("window_title_contains", "text"),
            "key": ("window_title_contains", "key"),
            "sleep": ("seconds",),
            "capture": ("stage_id", "caption"),
        }
        missing = [name for name in required[self.type] if getattr(self, name) is None]
        if missing:
            raise ValueError(f"{self.type} 缺少字段：{', '.join(missing)}")
        if self.type == "invoke_menu" and not self.menu_path:
            raise ValueError("menu_path 不能为空")
        return self


class RecipeResult(StrictModel):
    session_id: str
    dry_run: bool
    completed_actions: int
    results: list[dict[str, Any]]


class EvidenceStep(StrictModel):
    ordinal: int
    stage_id: str
    caption: str
    action_summary: str
    parameters: dict[str, Any]
    evidence_type: Literal["tool", "parameter", "result", "comparison", "output"] = "result"
    window_title: str
    screenshot_path: str
    sha256: str
    captured_at: str
    width: int
    height: int


class RegisteredOutput(StrictModel):
    label: str
    path: str
    sha256: str
    size_bytes: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class FinalizeResult(StrictModel):
    complete: bool
    input_count: int
    missing_input_roles: list[str]
    invalid_inputs: list[str]
    stage_plan_locked: bool
    missing_stages: list[str]
    duplicate_stages: list[str]
    out_of_order_stages: list[str]
    invalid_screenshots: list[str]
    screenshot_count: int
    output_count: int
    manifest_path: str
    evidence_markdown_path: str
    message: str
