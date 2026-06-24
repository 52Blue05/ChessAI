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

from backend.engine.board import Board, Move, Square
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkStats
from .agent import Agent


# Giá trị quân cờ
PIECE_VALUES = {
    "pawn": 100,
    "knight": 320,
    "bishop": 330,
    "rook": 500,
    "queen": 900,
    "king": 20000,
}

# Piece-Square Tables (bonus vị trí cho quân trắng, đảo cho đen)
# Giá trị tham khảo từ Chess Programming Wiki
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

PST = {
    "pawn": PAWN_TABLE,
    "knight": KNIGHT_TABLE,
    # TODO: Thêm bảng cho bishop, rook, queen, king
}


class MinimaxAgent(Agent):
    """
    AI Minimax với Alpha-Beta Pruning.

    Usage:
        agent = MinimaxAgent(depth=3)
        move = agent.get_move(board)
        stats = agent.get_stats()
    """

    def __init__(self, depth: int = 3):
        super().__init__(name="minimax")
        self.depth = depth
        self.move_generator = MoveGenerator()

    def set_depth(self, depth: int) -> None:
        """Cài đặt độ sâu tìm kiếm."""
        self.depth = depth

    def get_move(self, board: Board) -> Optional[Move]:
        """
        Tìm nước đi tốt nhất bằng Minimax + Alpha-Beta Pruning.
        """
        self._reset_stats()

        is_maximizing = board.current_player == "white"

        best_move, best_score = self._minimax(
            board,
            depth=self.depth,
            alpha=float("-inf"),
            beta=float("inf"),
            is_maximizing=is_maximizing,
            root=True,
        )

        self._last_stats.depth_reached = self.depth
        self._last_stats.evaluation_score = best_score

        return best_move

    def _minimax(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool,
        root: bool = False,
    ) -> Tuple[Optional[Move], float]:
        """
        Thuật toán Minimax với Alpha-Beta Pruning.

        Args:
            board: Trạng thái bàn cờ.
            depth: Độ sâu còn lại.
            alpha: Giá trị alpha (best score cho MAX).
            beta: Giá trị beta (best score cho MIN).
            is_maximizing: True nếu đang ở lượt MAX.
            root: True nếu là node gốc (cần trả về move).

        Returns:
            (best_move, best_score) — best_move chỉ có ý nghĩa ở root.
        """
        # Base case: đạt độ sâu hoặc game over
        if depth == 0:
            self._last_stats.nodes_evaluated += 1
            return None, self.evaluate(board)

        legal_moves = self.move_generator.generate_legal_moves(board)

        # Checkmate hoặc stalemate
        if not legal_moves:
            self._last_stats.nodes_evaluated += 1
            if self.move_generator.is_in_check(board, board.current_player):
                # Checkmate — thua là -inf cho bên đang đi
                return None, float("-inf") if is_maximizing else float("inf")
            else:
                # Stalemate — hòa
                return None, 0.0

        # Move Ordering: sắp xếp nước đi để cắt tỉa hiệu quả hơn
        legal_moves = self._order_moves(board, legal_moves)

        best_move = legal_moves[0]

        if is_maximizing:
            max_eval = float("-inf")
            for move in legal_moves:
                new_board = board.make_move(move)
                _, eval_score = self._minimax(
                    new_board, depth - 1, alpha, beta,
                    is_maximizing=False,
                )
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff — cắt tỉa!
            return best_move if root else None, max_eval
        else:
            min_eval = float("inf")
            for move in legal_moves:
                new_board = board.make_move(move)
                _, eval_score = self._minimax(
                    new_board, depth - 1, alpha, beta,
                    is_maximizing=True,
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
        def move_score(move: Move) -> int:
            score = 0
            # Ưu tiên bắt quân (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
            target = board.get_piece(move.to_sq)
            if target:
                score += PIECE_VALUES.get(target.piece_type, 0) * 10
                attacker = board.get_piece(move.from_sq)
                if attacker:
                    score -= PIECE_VALUES.get(attacker.piece_type, 0)
            # Ưu tiên phong cấp
            if move.promotion:
                score += 800
            return score

        return sorted(moves, key=move_score, reverse=True)

    def evaluate(self, board: Board) -> float:
        """
        Hàm lượng giá tĩnh nâng cao.
        Sử dụng Material + Piece-Square Tables.

        Điểm dương = trắng có lợi, điểm âm = đen có lợi.
        """
        score = 0.0

        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece is None:
                    continue

                # Material value
                value = PIECE_VALUES.get(piece.piece_type, 0)

                # Piece-Square Table bonus
                pst = PST.get(piece.piece_type)
                if pst:
                    if piece.color == "white":
                        value += pst[r * 8 + c]
                    else:
                        # Đảo bảng cho quân đen
                        value += pst[(7 - r) * 8 + c]

                if piece.color == "white":
                    score += value
                else:
                    score -= value

        return score
