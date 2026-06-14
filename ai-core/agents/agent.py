"""
ai-core/agents/agent.py
Interface chung cho tất cả AI Agent.

Mọi thuật toán AI phải kế thừa class này và implement:
    - get_move(board) -> Move
    - get_stats() -> BenchmarkStats

Kiến trúc Plug-and-Play: dễ dàng thêm thuật toán mới
bằng cách tạo class mới kế thừa Agent.
"""

from abc import ABC, abstractmethod
from typing import Optional
import sys
from pathlib import Path

# Thêm path để import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.board import Board, Move
from backend.engine.benchmark_logger import BenchmarkStats


class Agent(ABC):
    """
    Abstract base class cho AI Agent.

    Attributes:
        name: Tên thuật toán (dùng cho logging/display).
        _last_stats: Thống kê lần suy nghĩ gần nhất.
    """

    def __init__(self, name: str):
        self.name = name
        self._last_stats = BenchmarkStats(algorithm=name)

    @abstractmethod
    def get_move(self, board: Board) -> Optional[Move]:
        """
        Tính toán và trả về nước đi tốt nhất.

        Args:
            board: Trạng thái bàn cờ hiện tại.

        Returns:
            Nước đi tốt nhất, hoặc None nếu không có nước đi hợp lệ.
        """
        pass

    def get_stats(self) -> BenchmarkStats:
        """Trả về thống kê hiệu năng lần suy nghĩ gần nhất."""
        return self._last_stats

    def _reset_stats(self) -> None:
        """Reset thống kê trước mỗi lần suy nghĩ mới."""
        self._last_stats = BenchmarkStats(algorithm=self.name)

    @abstractmethod
    def evaluate(self, board: Board) -> float:
        """
        Hàm lượng giá tĩnh (Static Evaluation Function).
        Đánh giá trạng thái bàn cờ cho bên trắng.

        Returns:
            Điểm dương = trắng có lợi.
            Điểm âm = đen có lợi.
            0 = cân bằng.
        """
        pass

    def __repr__(self) -> str:
        return f"Agent({self.name})"
