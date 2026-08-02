"""Run an opt-in real ENVI Classic smoke test through the MCP client."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from mcp import Client

from envi_classic_mcp.server import mcp


async def run(workspace_root: Path) -> dict[str, object]:
    session_id: str | None = None
    summary: dict[str, object] = {}
    async with Client(mcp, raise_exceptions=True) as client:
        health = await client.call_tool("envi_classic_health_check", {})
        if not health.structured_content["ok"]:
            raise RuntimeError(health.structured_content)
        summary["health"] = health.structured_content

        launched = await client.call_tool(
            "envi_classic_launch",
            {
                "workspace_root": str(workspace_root.resolve()),
                "experiment_name": "MCP-smoke-test",
                "timeout_seconds": 45,
                "mode": "diagnostic",
            },
        )
        session_id = launched.structured_content["session_id"]
        summary["session"] = launched.structured_content

        planned = await client.call_tool(
            "envi_classic_set_stage_plan",
            {
                "session_id": session_id,
                "require_output": False,
                "stages": [
                    {
                        "stage_id": "01-open-convolution-tool",
                        "caption": "打开 ENVI Classic 卷积与形态学工具",
                        "evidence_type": "tool",
                        "action_summary": "Filter > Convolutions and Morphology",
                        "required_parameters": ["purpose"],
                        "expected_window_contains": "Convolutions and Morphology Tool"
                    },
                    {
                        "stage_id": "02-set-image-add-back",
                        "caption": "设置 Image Add Back 参数为 10%",
                        "evidence_type": "parameter",
                        "action_summary": "在卷积工具中设置 Image Add Back",
                        "required_parameters": ["image_add_back_percent"],
                        "expected_window_contains": "Convolutions and Morphology Tool"
                    }
                ]
            },
        )
        summary["stage_plan"] = planned.structured_content

        try:
            await asyncio.sleep(2.0)
            discovered = await client.call_tool(
                "envi_classic_list_menu_items",
                {
                    "session_id": session_id,
                    "filter_text": "Convolutions and Morphology",
                    "limit": 20,
                },
            )
            if discovered.structured_content["total"] < 1:
                raise RuntimeError("未发现 Convolutions and Morphology 原生菜单。")
            summary["discovered_menu"] = discovered.structured_content

            for attempt in range(2):
                invoked = await client.call_tool(
                    "envi_classic_invoke_menu",
                    {
                        "session_id": session_id,
                        "menu_path": ["Filter", "Convolutions and Morphology"],
                    },
                )
                summary[f"menu_attempt_{attempt + 1}"] = invoked.structured_content
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    windows = await client.call_tool("envi_classic_list_windows", {"session_id": session_id})
                    titles = [window["title"] for window in windows.structured_content["windows"]]
                    if any("Convolutions and Morphology Tool" in title for title in titles):
                        summary["windows"] = titles
                        break
                    await asyncio.sleep(0.25)
                if "windows" in summary:
                    break
                await asyncio.sleep(1.0)
            else:
                raise TimeoutError(f"卷积工具窗口在两次受控调用后仍未出现；当前窗口：{titles}")

            captured = await client.call_tool(
                "envi_classic_capture_evidence",
                {
                    "session_id": session_id,
                    "stage_id": "01-open-convolution-tool",
                    "caption": "打开 ENVI Classic 卷积与形态学工具",
                    "action_summary": "Filter > Convolutions and Morphology",
                    "parameters": {"purpose": "MCP GUI smoke test"},
                    "window_title_contains": "Convolutions and Morphology Tool",
                    "evidence_type": "tool",
                },
            )
            summary["evidence"] = captured.structured_content

            recipe = await client.call_tool(
                "envi_classic_run_recipe",
                {
                    "session_id": session_id,
                    "actions": [
                        {
                            "type": "click",
                            "window_title_contains": "Convolutions and Morphology Tool",
                            "x_ratio": 0.50,
                            "y_ratio": 0.40
                        },
                        {
                            "type": "key",
                            "window_title_contains": "Convolutions and Morphology Tool",
                            "key": "CTRL+A"
                        },
                        {
                            "type": "type_text",
                            "window_title_contains": "Convolutions and Morphology Tool",
                            "text": "10"
                        },
                        {
                            "type": "key",
                            "window_title_contains": "Convolutions and Morphology Tool",
                            "key": "TAB"
                        },
                        {"type": "sleep", "seconds": 0.4}
                    ],
                    "dry_run": False
                },
            )
            if recipe.is_error:
                raise RuntimeError(recipe.content[0].text)
            summary["recipe"] = recipe.structured_content

            parameter_capture = await client.call_tool(
                "envi_classic_capture_evidence",
                {
                    "session_id": session_id,
                    "stage_id": "02-set-image-add-back",
                    "caption": "设置 Image Add Back 参数为 10%",
                    "action_summary": "在卷积工具中设置 Image Add Back",
                    "parameters": {"image_add_back_percent": 10},
                    "window_title_contains": "Convolutions and Morphology Tool",
                    "evidence_type": "parameter",
                },
            )
            summary["parameter_evidence"] = parameter_capture.structured_content

            finalized = await client.call_tool(
                "envi_classic_finalize_evidence",
                {
                    "session_id": session_id,
                },
            )
            summary["finalized"] = finalized.structured_content
            if not finalized.structured_content["complete"]:
                raise RuntimeError(finalized.structured_content["message"])
        finally:
            closed = await client.call_tool(
                "envi_classic_close_session",
                {"session_id": session_id, "force": True, "timeout_seconds": 5},
            )
            summary["closed"] = closed.structured_content
    return summary


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_root", type=Path)
    args = parser.parse_args()
    result = asyncio.run(run(args.workspace_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
