"""Unit tests for src/myproject/menu.py."""

from src.myproject.menu import GLOBAL_RULES, MENU_INDEX


def test_menu_index_contains_required_items():
    """Verify the static menu index contains expected keys and structures."""
    required_keys = ["taco_pastor", "taco_puffy_picadillo", "drink_big_red"]
    for key in required_keys:
        assert key in MENU_INDEX
        assert "price" in MENU_INDEX[key]
        assert "dietary_info" in MENU_INDEX[key]


def test_global_rules_exist():
    """Verify global LLM rules are populated."""
    assert "system_warning" in GLOBAL_RULES
    assert "modifiers" in GLOBAL_RULES["system_warning"]
