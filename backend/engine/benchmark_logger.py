"""Benchmark metrics and isolated CSV session logging."""

from __future__ import annotations

import csv
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_CSV_PATH = PROJECT_ROOT / "benchmark_results.csv"
BENCHMARK_RESULTS_DIR = PROJECT_ROOT / "benchmark_results"

CSV_HEADERS = [
    "timestamp",
    "game_id",
    "move_number",
    "algorithm",
    "depth",
    "thinking_time_ms",
    "nodes_evaluated",
    "evaluation_score",
    "move_uci",
    "fen_before",
    "fen_after",
    "game_result",
    "record_type",
    "white_algorithm",
    "black_algorithm",
    "run_config",
]


@dataclass
class BenchmarkStats:
    """Performance statistics for one AI decision."""

    algorithm: str
    thinking_time_ms: float = 0.0
    nodes_evaluated: int = 0
    depth_reached: int = 0
    evaluation_score: float = 0.0


@dataclass
class GameRecord:
    """Summary of one AI-vs-AI game."""

    game_id: str
    white_algorithm: str
    black_algorithm: str
    result: str
    total_moves: int = 0
    white_avg_time_ms: float = 0.0
    black_avg_time_ms: float = 0.0
    white_total_nodes: int = 0
    black_total_nodes: int = 0


class BenchmarkLogger:
    """Write benchmark moves, configuration, and results to CSV."""

    def __init__(
        self,
        csv_path: Optional[str] = None,
        run_config: Optional[dict] = None,
    ):
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
        self._timer_start: Optional[float] = None
        self._ensure_csv_exists()
        if run_config:
            self.log_run_config(run_config)

    @classmethod
    def create_session(
        cls,
        run_config: dict,
        output_dir: Optional[str] = None,
        prefix: str = "benchmark",
    ) -> "BenchmarkLogger":
        """Create a uniquely named CSV for one benchmark run."""
        results_dir = Path(output_dir) if output_dir else BENCHMARK_RESULTS_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        session_id = uuid.uuid4().hex[:8]
        csv_path = results_dir / f"{prefix}_{timestamp}_{session_id}.csv"
        return cls(str(csv_path), run_config=run_config)

    @staticmethod
    def clear_session_files(output_dir: Optional[str] = None) -> int:
        """Delete generated session CSVs without touching the legacy CSV."""
        results_dir = Path(output_dir) if output_dir else BENCHMARK_RESULTS_DIR
        if not results_dir.exists():
            return 0

        deleted = 0
        for csv_path in results_dir.glob("*.csv"):
            if csv_path.is_file():
                csv_path.unlink()
                deleted += 1
        return deleted

    def _ensure_csv_exists(self) -> None:
        if self.csv_path.exists():
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(CSV_HEADERS)

    def start_timer(self) -> None:
        self._timer_start = time.perf_counter()

    def stop_timer(self) -> float:
        if self._timer_start is None:
            return 0.0
        elapsed = (time.perf_counter() - self._timer_start) * 1000
        self._timer_start = None
        return elapsed

    def log_run_config(self, run_config: dict) -> None:
        self._append_row(
            record_type="CONFIG",
            run_config=json.dumps(
                run_config,
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    def log_move(
        self,
        game_id: str,
        move_number: int,
        stats: BenchmarkStats,
        move_uci: str,
        fen_before: str,
        fen_after: str,
        game_result: str = "ongoing",
        white_algorithm: str = "",
        black_algorithm: str = "",
    ) -> None:
        self._append_row(
            record_type="MOVE",
            game_id=game_id,
            move_number=move_number,
            algorithm=stats.algorithm,
            depth=stats.depth_reached,
            thinking_time_ms=round(stats.thinking_time_ms, 2),
            nodes_evaluated=stats.nodes_evaluated,
            evaluation_score=round(stats.evaluation_score, 4),
            move_uci=move_uci,
            fen_before=fen_before,
            fen_after=fen_after,
            game_result=game_result,
            white_algorithm=white_algorithm,
            black_algorithm=black_algorithm,
        )

    def log_game_result(
        self,
        game_id: str,
        result: str,
        white_algorithm: str = "",
        black_algorithm: str = "",
    ) -> None:
        self._append_row(
            record_type="RESULT",
            game_id=game_id,
            move_number=-1,
            algorithm="RESULT",
            game_result=result,
            white_algorithm=white_algorithm,
            black_algorithm=black_algorithm,
        )

    def _append_row(self, **values) -> None:
        with open(self.csv_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            row = {header: "" for header in CSV_HEADERS}
            row["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            row.update(values)
            writer.writerow(row)

    def read_all_records(self) -> List[dict]:
        if not self.csv_path.exists():
            return []
        with open(self.csv_path, "r", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    def get_summary_by_algorithm(self) -> dict:
        """Aggregate exact per-algorithm metrics and game outcomes."""
        move_data = {}
        game_results = {}

        for record in self.read_all_records():
            record_type = record.get("record_type", "")
            algorithm = record.get("algorithm", "")

            if record_type == "RESULT" or algorithm == "RESULT":
                game_results[record.get("game_id", "")] = {
                    "result": record.get("game_result", ""),
                    "white": record.get("white_algorithm", ""),
                    "black": record.get("black_algorithm", ""),
                }
                continue

            if record_type not in ("", "MOVE") or not algorithm:
                continue

            data = move_data.setdefault(
                algorithm,
                {"times": [], "nodes": []},
            )
            try:
                data["times"].append(
                    float(record.get("thinking_time_ms", 0) or 0)
                )
                data["nodes"].append(
                    int(record.get("nodes_evaluated", 0) or 0)
                )
            except (TypeError, ValueError):
                continue

        algorithms = set(move_data)
        for game in game_results.values():
            algorithms.update(
                name for name in (game["white"], game["black"]) if name
            )

        summary = {}
        for algorithm in sorted(algorithms):
            data = move_data.get(algorithm, {"times": [], "nodes": []})
            wins = losses = draws = 0

            for game in game_results.values():
                white = game["white"]
                black = game["black"]
                result = game["result"]
                if algorithm not in {white, black}:
                    continue
                if result == "draw":
                    draws += 1
                elif (
                    result == "white_win" and algorithm == white
                ) or (
                    result == "black_win" and algorithm == black
                ):
                    wins += 1
                elif result in {"white_win", "black_win"}:
                    losses += 1

            total_moves = len(data["times"])
            games = wins + losses + draws
            summary[algorithm] = {
                "avg_time_ms": round(
                    sum(data["times"]) / total_moves
                    if total_moves else 0,
                    2,
                ),
                "avg_nodes": round(
                    sum(data["nodes"]) / total_moves
                    if total_moves else 0
                ),
                "total_moves": total_moves,
                "games": games,
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "win_rate": round(wins / games, 4) if games else 0,
            }
        return summary
