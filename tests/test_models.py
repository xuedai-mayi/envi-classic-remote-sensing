import pytest
from pydantic import ValidationError

from envi_classic_mcp.models import RecipeAction


def test_click_action_rejects_out_of_window_ratio() -> None:
    with pytest.raises(ValidationError):
        RecipeAction(
            type="click",
            window_title_contains="ENVI",
            x_ratio=1.1,
            y_ratio=0.5,
        )


def test_capture_requires_stage_and_caption() -> None:
    with pytest.raises(ValidationError):
        RecipeAction(type="capture", stage_id="01-open")


def test_menu_action_requires_nonempty_path() -> None:
    with pytest.raises(ValidationError):
        RecipeAction(type="invoke_menu", menu_path=[])
