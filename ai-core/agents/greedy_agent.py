"""
ai-core/agents/greedy_agent.py
Greedy Best-First Search — Thuật toán Tham lam.

Vai trò: Baseline Model để đo lường.

Cơ chế hoạt động:
    - Duyệt qua tất cả nước đi hợp lệ ở trạng thái hiện tại (depth=1)
    - Chọn ngay nước đi mang lại điểm số cao nhất theo hàm lượng giá tĩnh
    - KHÔNG xét các bước tiếp theo (không tìm kiếm sâu)

Đặc điểm:
    ✅ Phản hồi gần như tức thời, tiêu tốn rất ít tài nguyên
    ❌ Rất "thiển cận", dễ rơi vào bẫy chiến thuật
"""

from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.board import Board, Move
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkStats
from .agent import Agent


# Giá trị quân cờ (đơn vị: centipawn)
PIECE_VALUES = {
    "pawn": 100,
    "knight": 320,
    "bishop": 330,
    "rook": 500,
    "queen": 900,
    "king": 20000,
}


class GreedyAgent(Agent):
    """
    AI Tham lam — chọn nước đi tốt nhất ngay lập tức (depth=1).

    Usage:
        agent = GreedyAgent()
        move = agent.get_move(board)
        stats = agent.get_stats()
    """

    def __init__(self):
        super().__init__(name="greedy")
        self.move_generator = MoveGenerator()

    def get_move(self, board: Board) -> Optional[Move]:
        """
        Tìm nước đi tốt nhất bằng cách đánh giá tất cả nước đi hợp lệ
        và chọn nước có evaluation score cao nhất.
        """
        self._reset_stats()

        legal_moves = self.move_generator.generate_legal_moves(board)
        if not legal_moves:
            return None

        best_move = None
        best_score = float("-inf")
        color = board.current_player

        for move in legal_moves:
            self._last_stats.nodes_evaluated += 1

            # Thực hiện nước đi trên bản sao
            new_board = board.make_move(move)

            # Đánh giá trạng thái mới
            score = self.evaluate(new_board)

            # Nếu là bên đen, đảo dấu (vì evaluate luôn đánh giá cho trắng)
            if color == "black":
                score = -score

            if score > best_score:
                best_score = score
                best_move = move

        self._last_stats.depth_reached = 1
        self._last_stats.evaluation_score = best_score

        return best_move

    def evaluate(self, board: Board) -> float:
        """
        Hàm lượng giá tĩnh (Static Evaluation Function).
        Đánh giá dựa trên tổng giá trị quân cờ.

        Điểm dương = trắng có lợi.
        Điểm âm = đen có lợi.

        TODO: Có thể cải thiện thêm:
        - Piece-Square Tables (vị trí quân trên bàn)
        - Kiểm soát trung tâm
        - An toàn vua
        - Cấu trúc tốt (doubled pawns, isolated pawns, ...)
        """
        score = 0.0

        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece is None:
                    continue

                value = PIECE_VALUES.get(piece.piece_type, 0)
                if piece.color == "white":
                    score += value
                else:
                    score -= value

        return score
