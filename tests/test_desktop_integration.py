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


def test_benchmark_report_builds_three_matchups_and_six_performance_rows():
    screen = BenchmarkScreen()
    screen.matchups = [
        {
            "pair": "greedy vs minimax",
            "a_wins": 1,
            "b_wins": 2,
            "draws": 1,
            "performance": {
                "greedy": {
                    "avg_time_ms": 10,
                    "avg_nodes": 20,
                    "avg_depth": 1,
                    "moves": 80,
                },
                "minimax": {
                    "avg_time_ms": 500,
                    "avg_nodes": 200,
                    "avg_depth": 2,
                    "moves": 82,
                },
            },
        },
        {
            "pair": "greedy vs mcts",
            "a_wins": 2,
            "b_wins": 1,
            "draws": 1,
            "performance": {
                "greedy": {
                    "avg_time_ms": 11,
                    "avg_nodes": 21,
                    "avg_depth": 1,
                    "moves": 70,
                },
                "mcts": {
                    "avg_time_ms": 600,
                    "avg_nodes": 100,
                    "avg_depth": 3,
                    "moves": 72,
                },
            },
        },
        {
            "pair": "minimax vs mcts",
            "a_wins": 1,
            "b_wins": 1,
            "draws": 2,
            "performance": {
                "minimax": {
                    "avg_time_ms": 510,
                    "avg_nodes": 210,
                    "avg_depth": 2,
                    "moves": 90,
                },
                "mcts": {
                    "avg_time_ms": 620,
                    "avg_nodes": 100,
                    "avg_depth": 3,
                    "moves": 91,
                },
            },
        },
    ]

    win_rows = screen._build_win_rows()
    performance_rows = screen._build_performance_rows()

    assert len(win_rows) == 3
    assert win_rows[0] == [
        "Greedy vs Minimax",
        "1/4",
        "2/4",
        "-",
        "1/4",
    ]
    assert len(performance_rows) == 6
    assert performance_rows[0][0:2] == [
        "Greedy vs Minimax",
        "Greedy",
    ]
