"""Regression tests for isolated benchmark sessions and exact summaries."""

import json

from backend.engine.benchmark_logger import BenchmarkLogger, BenchmarkStats


def _stats(algorithm, time_ms, nodes):
    return BenchmarkStats(
        algorithm=algorithm,
        thinking_time_ms=time_ms,
        nodes_evaluated=nodes,
        depth_reached=2,
        evaluation_score=12.5,
    )


def test_benchmark_session_records_config_and_uses_unique_file(tmp_path):
    config = {
        "games_per_pair": 2,
        "minimax_depth": 2,
        "mcts_simulations": 100,
    }

    first = BenchmarkLogger.create_session(config, output_dir=str(tmp_path))
    second = BenchmarkLogger.create_session(config, output_dir=str(tmp_path))

    assert first.csv_path != second.csv_path
    assert first.csv_path.parent == tmp_path

    config_record = first.read_all_records()[0]
    assert config_record["record_type"] == "CONFIG"
    assert json.loads(config_record["run_config"]) == config


def test_benchmark_summary_tracks_sides_wins_losses_and_draws(tmp_path):
    logger = BenchmarkLogger.create_session(
        {"minimax_depth": 2},
        output_dir=str(tmp_path),
    )

    logger.log_move(
        game_id="game-1",
        move_number=1,
        stats=_stats("greedy", 10, 20),
        move_uci="e2e4",
        fen_before="before",
        fen_after="after",
        white_algorithm="greedy",
        black_algorithm="minimax",
    )
    logger.log_move(
        game_id="game-1",
        move_number=2,
        stats=_stats("minimax", 30, 60),
        move_uci="e7e5",
        fen_before="before",
        fen_after="after",
        game_result="white_win",
        white_algorithm="greedy",
        black_algorithm="minimax",
    )
    logger.log_game_result(
        "game-1",
        "white_win",
        white_algorithm="greedy",
        black_algorithm="minimax",
    )

    logger.log_move(
        game_id="game-2",
        move_number=1,
        stats=_stats("minimax", 50, 100),
        move_uci="d2d4",
        fen_before="before",
        fen_after="after",
        white_algorithm="minimax",
        black_algorithm="greedy",
    )
    logger.log_move(
        game_id="game-2",
        move_number=2,
        stats=_stats("greedy", 20, 40),
        move_uci="d7d5",
        fen_before="before",
        fen_after="after",
        game_result="draw",
        white_algorithm="minimax",
        black_algorithm="greedy",
    )
    logger.log_game_result(
        "game-2",
        "draw",
        white_algorithm="minimax",
        black_algorithm="greedy",
    )

    summary = logger.get_summary_by_algorithm()

    assert summary["greedy"] == {
        "avg_time_ms": 15.0,
        "avg_nodes": 30,
        "total_moves": 2,
        "games": 2,
        "wins": 1,
        "losses": 0,
        "draws": 1,
        "win_rate": 0.5,
    }
    assert summary["minimax"] == {
        "avg_time_ms": 40.0,
        "avg_nodes": 80,
        "total_moves": 2,
        "games": 2,
        "wins": 0,
        "losses": 1,
        "draws": 1,
        "win_rate": 0.0,
    }


def test_clear_session_files_only_removes_generated_directory(tmp_path):
    generated = tmp_path / "generated"
    legacy = tmp_path / "benchmark_results.csv"
    legacy.write_text("keep me", encoding="utf-8")

    BenchmarkLogger.create_session({}, output_dir=str(generated))
    BenchmarkLogger.create_session({}, output_dir=str(generated))

    assert BenchmarkLogger.clear_session_files(str(generated)) == 2
    assert list(generated.glob("*.csv")) == []
    assert legacy.read_text(encoding="utf-8") == "keep me"
