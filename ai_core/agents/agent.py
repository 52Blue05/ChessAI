"""
ai_core/agents/agent.py
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

from backend.engine.board import Board, Move, Square
from backend.engine.benchmark_logger import BenchmarkStats
from backend.engine.move_generator import MoveGenerator


PIECE_VALUES = {
    "pawn": 100,
    "knight": 320,
    "bishop": 330,
    "rook": 500,
    "queen": 900,
    "king": 0,
}

PIECE_SQUARE_TABLES = {
    "pawn": [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    "knight": [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    "bishop": [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    "rook": [
         0,  0,  0,  5,  5,  0,  0,  0,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         5, 10, 10, 10, 10, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    "queen": [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -10,  5,  5,  5,  5,  5,  0,-10,
          0,  0,  5,  5,  5,  5,  0, -5,
         -5,  0,  5,  5,  5,  5,  0, -5,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20,
    ],
    "king": [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20,
    ],
}


class Agent(ABC):
    """
    Abstract base class cho AI Agent.

    Attributes:
        name: Tên thuật toán (dùng cho logging/display).
        _last_stats: Thống kê lần suy nghĩ gần nhất.
    """

    MATE_SCORE = 1_000_000.0
    SEARCH_BOUND = 2_000_000.0
    CENTER_SQUARES = (
        Square(3, 3),
        Square(3, 4),
        Square(4, 3),
        Square(4, 4),
    )

    def __init__(self, name: str):
        self.name = name
        self._last_stats = BenchmarkStats(algorithm=name)
        self.move_generator = MoveGenerator()

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

    def evaluate(self, board: Board) -> float:
        """
        Hàm lượng giá chung: material + PST + mobility + center + king safety.

        Returns:
            Điểm dương = trắng có lợi.
            Điểm âm = đen có lợi.
            0 = cân bằng.
        """
        score = self._material_and_position_score(board)
        score += self._mobility_score(board)
        score += self._center_control_score(board)
        score += self._king_safety_score(board)

        if self.move_generator.is_in_check(board, "black"):
            score += 35
        if self.move_generator.is_in_check(board, "white"):
            score -= 35

        return float(score)

    def terminal_score(
        self,
        board: Board,
        legal_moves: Optional[list[Move]] = None,
        ply: int = 0,
    ) -> Optional[float]:
        """Finite terminal score using the same white-positive convention."""
        moves = (
            legal_moves
            if legal_moves is not None
            else self.move_generator.generate_legal_moves(board)
        )
        if not moves:
            if self.move_generator.is_in_check(board, board.current_player):
                if board.current_player == "white":
                    return -self.MATE_SCORE + ply
                return self.MATE_SCORE - ply
            return 0.0
        if (
            board.half_move_clock >= 100
            or self.move_generator.is_insufficient_material(board)
        ):
            return 0.0
        return None

    def find_mate_in_one(
        self,
        board: Board,
        moves: list[Move],
    ) -> Optional[Move]:
        """Return the first legal move that immediately checkmates."""
        mate_move, _ = self.find_mate_and_checking_moves(board, moves)
        return mate_move

    def find_mate_and_checking_moves(
        self,
        board: Board,
        moves: list[Move],
    ) -> tuple[Optional[Move], list[Move]]:
        """Classify checking moves and stop early when one is checkmate."""
        checking_moves = []
        for move in moves:
            new_board = board.make_move(move)
            if not self.move_generator.is_in_check(
                new_board,
                new_board.current_player,
            ):
                continue
            checking_moves.append(move)
            if not self.move_generator.generate_legal_moves(new_board):
                return move, checking_moves
        return None, checking_moves

    def move_order_score(self, board: Board, move: Move) -> float:
        """Cheap tactical score shared by Minimax ordering and MCTS rollout."""
        attacker = board.get_piece(move.from_sq)
        captured = move.captured or board.get_piece(move.to_sq)
        score = 0.0

        if captured is not None:
            score += PIECE_VALUES.get(captured.piece_type, 0) * 10
            if attacker is not None:
                score -= PIECE_VALUES.get(attacker.piece_type, 0)
        if move.promotion:
            score += PIECE_VALUES.get(move.promotion, 0) + 8_000
        if move.to_sq in self.CENTER_SQUARES:
            score += 40

        new_board = board.make_move(move)
        gives_check = self.move_generator.is_in_check(
            new_board,
            new_board.current_player,
        )
        if gives_check:
            score += 1_000
            if not self.move_generator.generate_legal_moves(new_board):
                score += self.MATE_SCORE

        return score

    def _material_and_position_score(self, board: Board) -> float:
        score = 0.0
        for row in range(8):
            for col in range(8):
                piece = board.grid[row][col]
                if piece is None:
                    continue

                value = PIECE_VALUES.get(piece.piece_type, 0)
                table = PIECE_SQUARE_TABLES.get(piece.piece_type)
                if table:
                    table_row = row if piece.color == "white" else 7 - row
                    value += table[table_row * 8 + col]

                score += value if piece.color == "white" else -value
        return score

    def _mobility_score(self, board: Board) -> float:
        white_moves = self._legal_move_count(board, "white")
        black_moves = self._legal_move_count(board, "black")
        return (white_moves - black_moves) * 2.0

    def _legal_move_count(self, board: Board, color: str) -> int:
        temp_board = board.copy()
        if color != board.current_player:
            temp_board.en_passant = None
        temp_board.current_player = color
        return len(self.move_generator.generate_legal_moves(temp_board))

    def _center_control_score(self, board: Board) -> float:
        score = 0.0
        for square in self.CENTER_SQUARES:
            piece = board.get_piece(square)
            if piece is not None:
                score += 12 if piece.color == "white" else -12
            if self.move_generator.is_square_attacked(board, square, "white"):
                score += 3
            if self.move_generator.is_square_attacked(board, square, "black"):
                score -= 3
        return score

    def _king_safety_score(self, board: Board) -> float:
        return (
            self._king_safety_for_color(board, "white")
            - self._king_safety_for_color(board, "black")
        )

    def _king_safety_for_color(self, board: Board, color: str) -> float:
        king = board.find_king(color)
        if king is None:
            return -self.MATE_SCORE / 2

        score = 0.0
        if king.col in (2, 6):
            score += 25

        rights = board.castling
        if color == "white":
            score += 5 * (
                rights.white_king_side + rights.white_queen_side
            )
            pawn_row = king.row - 1
        else:
            score += 5 * (
                rights.black_king_side + rights.black_queen_side
            )
            pawn_row = king.row + 1

        for col in range(max(0, king.col - 1), min(7, king.col + 1) + 1):
            pawn = board.get_piece(Square(pawn_row, col))
            if pawn is not None and pawn.piece_type == "pawn" and pawn.color == color:
                score += 8

        opponent = "black" if color == "white" else "white"
        for row in range(max(0, king.row - 1), min(7, king.row + 1) + 1):
            for col in range(max(0, king.col - 1), min(7, king.col + 1) + 1):
                if self.move_generator.is_square_attacked(
                    board,
                    Square(row, col),
                    opponent,
                ):
                    score -= 4

        return score

    def __repr__(self) -> str:
        return f"Agent({self.name})"
