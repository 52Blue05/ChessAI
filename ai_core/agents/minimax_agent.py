"""
ai_core/agents/minimax_agent.py
Minimax kết hợp Cắt tỉa Alpha-Beta (Alpha-Beta Pruning).

Vai trò: Thuật toán cốt lõi truyền thống.

Cơ chế hoạt động:
    - Xây dựng cây trò chơi, đóng vai trò MAX (tối đa hóa lợi thế)
      và MIN (đối thủ tối thiểu hóa lợi thế)
    - Cắt tỉa Alpha-Beta loại bỏ các nhánh không cần thiết
    - Move Ordering: sắp xếp nước đi để tối ưu cắt tỉa

Đặc điểm:
    ✅ Tính toán chiến thuật sâu, phòng thủ chặt chẽ
    ❌ Hiệu năng phụ thuộc vào hàm lượng giá và move ordering
"""

from typing import Optional, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.board import Board, Move
from backend.engine.move_generator import MoveGenerator
from .agent import Agent


class MinimaxAgent(Agent):
    """
    AI Minimax với Alpha-Beta Pruning.

    Usage:
        agent = MinimaxAgent(depth=2)
        move = agent.get_move(board)
        stats = agent.get_stats()
    """

    MAX_DEPTH = 4

    def __init__(self, depth: int = 2):
        super().__init__(name="minimax")
        self.depth = max(1, min(self.MAX_DEPTH, int(depth)))
        self.move_generator = MoveGenerator()

    def set_depth(self, depth: int) -> None:
        """Cài đặt độ sâu tìm kiếm."""
        self.depth = max(1, min(self.MAX_DEPTH, int(depth)))

    def get_move(self, board: Board) -> Optional[Move]:
        """
        Tìm nước đi tốt nhất bằng Minimax + Alpha-Beta Pruning.
        """
        self._reset_stats()

        best_move, best_score = self._minimax(
            board,
            depth=self.depth,
            alpha=-self.SEARCH_BOUND,
            beta=self.SEARCH_BOUND,
            root=True,
            ply=0,
        )

        self._last_stats.depth_reached = self.depth
        self._last_stats.evaluation_score = float(best_score)

        return best_move

    def _minimax(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        root: bool = False,
        ply: int = 0,
    ) -> Tuple[Optional[Move], float]:
        """
        Thuật toán Minimax với Alpha-Beta Pruning.

        Args:
            board: Trạng thái bàn cờ.
            depth: Độ sâu còn lại.
            alpha: Giá trị alpha (best score cho MAX).
            beta: Giá trị beta (best score cho MIN).
            root: True nếu là node gốc (cần trả về move).

        Returns:
            (best_move, best_score) — best_move chỉ có ý nghĩa ở root.
        """
        legal_moves = self.move_generator.generate_legal_moves(board)
        terminal = self.terminal_score(board, legal_moves, ply)
        if terminal is not None:
            self._last_stats.nodes_evaluated += 1
            return None, terminal

        if depth == 0:
            self._last_stats.nodes_evaluated += 1
            return None, self.evaluate(board)

        # Move Ordering: sắp xếp nước đi để cắt tỉa hiệu quả hơn
        legal_moves = self._order_moves(board, legal_moves)

        best_move = legal_moves[0]

        if board.current_player == "white":
            max_eval = -self.SEARCH_BOUND
            for move in legal_moves:
                new_board = board.make_move(move)
                _, eval_score = self._minimax(
                    new_board, depth - 1, alpha, beta,
                    ply=ply + 1,
                )
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff — cắt tỉa!
            return best_move if root else None, max_eval
        else:
            min_eval = self.SEARCH_BOUND
            for move in legal_moves:
                new_board = board.make_move(move)
                _, eval_score = self._minimax(
                    new_board, depth - 1, alpha, beta,
                    ply=ply + 1,
                )
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff — cắt tỉa!
            return best_move if root else None, min_eval

    def _order_moves(self, board: Board, moves: list) -> list:
        """
        Sắp xếp nước đi để cắt tỉa Alpha-Beta hiệu quả hơn.
        Ưu tiên: bắt quân giá trị cao > bắt quân > nước đi thường.

        TODO: Cải thiện thêm:
        - Killer Heuristic
        - History Heuristic
        - Hash Move (từ Transposition Table)
        """
        return sorted(
            moves,
            key=lambda move: self.move_order_score(board, move),
            reverse=True,
        )
