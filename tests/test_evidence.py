from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

from PIL import Image

from envi_classic_mcp.evidence import finalize_evidence, register_inputs, register_output, set_stage_plan
from envi_classic_mcp.models import StageRequirement


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fake_session(tmp_path):
    run_dir = tmp_path / ".envi-runs" / "test-run"
    screenshots = run_dir / "screenshots"
    screenshots.mkdir(parents=True)
    manifest_path = run_dir / "report-evidence.json"
    manifest = {
        "schema_version": "2.0",
        "session": {
            "experiment_name": "测试实验",
            "envi_version": "5.6",
            "run_dir": str(run_dir),
        },
        "inputs": [],
        "stage_plan": None,
        "required_stages": [],
        "steps": [],
        "outputs": [],
        "validation": None,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return SimpleNamespace(
        session_id="test-session",
        workspace_root=tmp_path.resolve(),
        run_dir=run_dir.resolve(),
        screenshots_dir=screenshots.resolve(),
        manifest_path=manifest_path.resolve(),
    )


def _add_step(session, stage_id, ordinal):
    path = session.screenshots_dir / f"{ordinal:03d}-{stage_id}.png"
    Image.new("RGB", (320, 200), color=(ordinal * 20, 30, 40)).save(path)
    manifest = json.loads(session.manifest_path.read_text(encoding="utf-8"))
    manifest["steps"].append(
        {
            "ordinal": ordinal,
            "stage_id": stage_id,
            "caption": f"步骤 {ordinal}",
            "action_summary": "测试动作",
            "parameters": {},
            "window_title": "ENVI Classic",
            "screenshot_path": str(path.resolve()),
            "sha256": _sha256(path),
            "captured_at": "2026-01-01T00:00:00+00:00",
            "width": 320,
            "height": 200,
        }
    )
    session.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")


def test_finalize_passes_only_with_ordered_screenshots_and_output(tmp_path) -> None:
    session = _fake_session(tmp_path)
    _add_step(session, "01-open", 1)
    _add_step(session, "02-parameter", 2)
    output = tmp_path / "result.dat"
    output.write_bytes(b"real-result")
    register_output(session, str(output), "实验结果")

    result = finalize_evidence(
        session,
        required_stages=["01-open", "02-parameter"],
        min_screenshots=2,
        require_output=True,
        require_inputs=False,
        require_stage_plan=False,
    )

    assert result.complete is True
    assert result.missing_stages == []
    assert (session.run_dir / "report-evidence.md").is_file()


def test_finalize_rejects_missing_stage(tmp_path) -> None:
    session = _fake_session(tmp_path)
    _add_step(session, "01-open", 1)

    result = finalize_evidence(
        session,
        required_stages=["01-open", "02-parameter"],
        min_screenshots=2,
        require_output=False,
        require_inputs=False,
        require_stage_plan=False,
    )

    assert result.complete is False
    assert result.missing_stages == ["02-parameter"]


def test_finalize_rejects_tampered_screenshot(tmp_path) -> None:
    session = _fake_session(tmp_path)
    _add_step(session, "01-open", 1)
    screenshot = next(session.screenshots_dir.glob("*.png"))
    screenshot.write_bytes(b"tampered")

    result = finalize_evidence(
        session,
        required_stages=["01-open"],
        min_screenshots=1,
        require_output=False,
        require_inputs=False,
        require_stage_plan=False,
    )

    assert result.complete is False
    assert result.invalid_screenshots == ["01-open"]


def test_register_output_rejects_file_outside_workspace(tmp_path) -> None:
    session = _fake_session(tmp_path / "workspace")
    outside = tmp_path / "outside.dat"
    outside.write_bytes(b"outside")

    try:
        register_output(session, str(outside), "越界文件")
    except ValueError as error:
        assert "工作区内" in str(error)
    else:
        raise AssertionError("应拒绝登记工作区外文件")


def test_registered_inputs_and_stage_plan_are_frozen(tmp_path) -> None:
    session = _fake_session(tmp_path / "workspace")
    guide = session.workspace_root / "guide.pdf"
    template = session.workspace_root / "template.docx"
    data = session.workspace_root / "image.dat"
    guide.write_bytes(b"guide")
    template.write_bytes(b"template")
    data.write_bytes(b"data")

    result = register_inputs(session, str(guide), str(template), [str(data)])
    assert {artifact.role for artifact in result.inputs} == {"guide", "template", "data"}

    plan = set_stage_plan(
        session,
        stages=[
            StageRequirement(
                stage_id="01-parameter",
                caption="参数设置",
                evidence_type="parameter",
                action_summary="设置 3×3 模板",
                required_parameters=["kernel"],
            ),
            StageRequirement(
                stage_id="02-result",
                caption="处理结果",
                evidence_type="result",
                action_summary="显示处理结果",
            ),
        ],
    )
    assert plan.locked is True
    assert plan.stage_count == 2

    try:
        finalize_evidence(session, required_stages=["01-parameter"])
    except ValueError as error:
        assert "冻结" in str(error)
    else:
        raise AssertionError("验收时不应允许删减冻结的阶段")


def test_finalize_requires_teacher_inputs_and_locked_plan(tmp_path) -> None:
    session = _fake_session(tmp_path)
    result = finalize_evidence(session)
    assert result.complete is False
    assert set(result.missing_input_roles) == {"guide", "template", "data"}
    assert result.stage_plan_locked is False
