import pytest
from mcp import Client

from envi_classic_mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_exposes_expected_tools_and_health_result() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        assert {
            "envi_classic_health_check",
            "envi_classic_launch",
            "envi_classic_register_inputs",
            "envi_classic_set_stage_plan",
            "envi_classic_list_windows",
            "envi_classic_list_menu_items",
            "envi_classic_invoke_menu",
            "envi_classic_run_recipe",
            "envi_classic_capture_evidence",
            "envi_classic_register_output",
            "envi_classic_finalize_evidence",
            "envi_classic_close_session",
        } <= names

        result = await client.call_tool("envi_classic_health_check", {})
        assert result.is_error is False
        assert result.structured_content["platform"]
        assert isinstance(result.structured_content["envi"]["found"], bool)
        if result.structured_content["envi"]["found"]:
            assert result.structured_content["envi"]["version"].startswith("5.6")
