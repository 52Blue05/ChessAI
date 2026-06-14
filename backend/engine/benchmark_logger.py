"""
backend/engine/benchmark_logger.py
Ghi metrics hiệu năng AI ra file CSV.

Metrics:
- Thuật toán sử dụng
- Thời gian suy nghĩ (ms)
- Số node đã duyệt
- Độ sâu tìm kiếm
- Điểm đánh giá
- Kết quả ván đấu
"""

from __future__ import annotations
import csv
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


# Đường dẫn file CSV mặc định
DEFAULT_CSV_PATH = Path(__file__).parent.parent.parent / "benchmark_results.csv"

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
    "game_result",  # white_win, black_win, draw, ongoing
]


@dataclass
class BenchmarkStats:
    """Thống kê hiệu năng của mỗi lần AI suy nghĩ."""
    algorithm: str
    thinking_time_ms: float = 0.0
    nodes_evaluated: int = 0
    depth_reached: int = 0
    evaluation_score: float = 0.0


@dataclass
class GameRecord:
    """Kết quả một ván đấu."""
    game_id: str
    white_algorithm: str
    black_algorithm: str
    result: str  # white_win, black_win, draw
    total_moves: int = 0
    white_avg_time_ms: float = 0.0
    black_avg_time_ms: float = 0.0
    white_total_nodes: int = 0
    black_total_nodes: int = 0


class BenchmarkLogger:
    """
    Logger ghi benchmark metrics ra CSV.

    Usage:
        logger = BenchmarkLogger()

        # Ghi từng nước đi
        logger.log_move(game_id, move_number, stats, move_uci, fen_before, fen_after)

        # Timer tiện ích
        logger.start_timer()
        # ... AI suy nghĩ ...
        elapsed_ms = logger.stop_timer()

        # Đọc kết quả
        records = logger.get_game_records()
    """

    def __init__(self, csv_path: Optional[str] = None):
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
        self._timer_start: Optional[float] = None
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        """Tạo file CSV với headers nếu chưa tồn tại."""
        if not self.csv_path.exists():
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------

    def start_timer(self) -> None:
        """Bắt đầu đếm thời gian."""
        self._timer_start = time.perf_counter()

    def stop_timer(self) -> float:
        """Dừng đếm thời gian, trả về milliseconds."""
        if self._timer_start is None:
            return 0.0
        elapsed = (time.perf_counter() - self._timer_start) * 1000
        self._timer_start = None
        return elapsed

    # ------------------------------------------------------------------
    # Ghi log
    # ------------------------------------------------------------------

    def log_move(
        self,
        game_id: str,
        move_number: int,
        stats: BenchmarkStats,
        move_uci: str,
        fen_before: str,
        fen_after: str,
        game_result: str = "ongoing",
    ) -> None:
        """Ghi log một nước đi vào CSV."""
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                game_id,
                move_number,
                stats.algorithm,
                stats.depth_reached,
                round(stats.thinking_time_ms, 2),
                stats.nodes_evaluated,
                round(stats.evaluation_score, 4),
                move_uci,
                fen_before,
                fen_after,
                game_result,
            ])

    def log_game_result(self, game_id: str, result: str) -> None:
        """Cập nhật kết quả ván đấu (ghi thêm 1 dòng summary)."""
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S"),
                game_id,
                -1,  # move_number = -1 => summary row
                "RESULT",
                0, 0, 0, 0,
                "",
                "",
                "",
                result,
            ])

    # ------------------------------------------------------------------
    # Đọc kết quả
    # ------------------------------------------------------------------

    def read_all_records(self) -> List[dict]:
        """Đọc tất cả records từ CSV."""
        records = []
        if not self.csv_path.exists():
            return records

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records

    def get_summary_by_algorithm(self) -> dict:
        """
        Tổng hợp thống kê theo từng thuật toán.

        Returns:
            {
                "greedy": {"avg_time_ms": ..., "avg_nodes": ..., "games": ..., "wins": ...},
                "minimax": {...},
                "mcts": {...},
            }

        TODO: Implement aggregation logic
        """
        records = self.read_all_records()
        summary = {}
        # TODO: Aggregate records by algorithm
        return summary
