"""Small compatibility checks for the Pygame desktop layer."""

from gui.benchmark_screen import (
    MCTS_SIMULATIONS,
    MINIMAX_DEPTH,
    BenchmarkScreen,
)
from gui.game_screen import ACTIVE_GAME_STATUSES, GameScreen


def test_check_is_an_active_game_status():
    assert ACTIVE_GAME_STATUSES == {"playing", "check"}


def test_desktop_uses_demo_friendly_ai_defaults():
    screen = GameScreen(mode="ai_vs_ai")

    assert screen.agents["minimax"].depth == 2
    assert screen.agents["mcts"].simulations == 100


def test_benchmark_screen_has_session_controls_and_matching_defaults():
    screen = BenchmarkScreen()

    assert MINIMAX_DEPTH == 2
    assert MCTS_SIMULATIONS == 100
    assert screen.logger is None
    assert screen.btn_restart.text
    assert screen.btn_clear.text
