"""
ai_core/agents/greedy_agent.py
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
from .agent import Agent, PIECE_VALUES


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
        current_terminal = self.terminal_score(board, legal_moves)
        if current_terminal is not None:
            self._last_stats.evaluation_score = float(current_terminal)
            return None
        if not legal_moves:
            return None

        best_move = None
        best_selection_score = -self.SEARCH_BOUND
        best_position_score = 0.0
        color = board.current_player

        for move in legal_moves:
            self._last_stats.nodes_evaluated += 1

            # Thực hiện nước đi trên bản sao
            new_board = board.make_move(move)

            opponent_moves = self.move_generator.generate_legal_moves(new_board)
            terminal = self.terminal_score(
                new_board,
                opponent_moves,
                ply=1,
            )
            position_score = (
                terminal if terminal is not None else self.evaluate(new_board)
            )
            selection_score = (
                position_score if color == "white" else -position_score
            )

            # Tie-break theo chiến thuật: promotion/capture/check/center.
            selection_score += self.move_order_score(board, move) * 0.02

            # Tránh treo quân giá trị cao ngay sau một nước tham lam.
            moved_piece = new_board.get_piece(move.to_sq)
            if (
                terminal is None
                and moved_piece is not None
                and self.move_generator.is_square_attacked(
                    new_board,
                    move.to_sq,
                    new_board.current_player,
                )
            ):
                selection_score -= (
                    PIECE_VALUES.get(moved_piece.piece_type, 0) * 0.5
                )

            if selection_score > best_selection_score:
                best_selection_score = selection_score
                best_position_score = position_score
                best_move = move

        self._last_stats.depth_reached = 1
        self._last_stats.evaluation_score = float(best_position_score)

        return best_move
