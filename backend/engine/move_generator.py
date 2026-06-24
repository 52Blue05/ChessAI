"""
backend/engine/move_generator.py
Sinh nước đi hợp lệ cho bàn cờ.

Module này chịu trách nhiệm:
- Sinh tất cả nước đi pseudo-legal cho từng loại quân
- Lọc ra nước đi hợp lệ (không để vua bị chiếu)
- Kiểm tra trạng thái chiếu/chiếu hết/hòa
"""

from __future__ import annotations
from typing import List, Optional
from .board import Board, Square, Move, Piece


class MoveGenerator:
    """
    Bộ sinh nước đi hợp lệ.

    Usage:
        generator = MoveGenerator()
        legal_moves = generator.generate_legal_moves(board)
        is_check = generator.is_in_check(board, 'white')
    """

    # ------------------------------------------------------------------
    # Hướng di chuyển cho từng loại quân
    # ------------------------------------------------------------------
    ROOK_DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    QUEEN_DIRS = ROOK_DIRS + BISHOP_DIRS
    KNIGHT_OFFSETS = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1),
    ]
    KING_OFFSETS = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    ]
    PROMOTION_PIECES = ("queen", "rook", "bishop", "knight")

    def generate_legal_moves(self, board: Board, square: Optional[Square] = None) -> List[Move]:
        """
        Sinh tất cả nước đi hợp lệ.

        Args:
            board: Trạng thái bàn cờ hiện tại.
            square: Nếu chỉ định, chỉ sinh nước đi cho quân tại ô đó.

        Returns:
            Danh sách các nước đi hợp lệ.

        TODO: Implement đầy đủ
        - Sinh pseudo-legal moves cho từng loại quân
        - Lọc bỏ nước đi khiến vua bị chiếu
        - Xử lý nhập thành
        - Xử lý bắt tốt qua đường (en passant)
        - Xử lý phong cấp
        """
        pseudo_moves = []
        color = board.current_player

        if square:
            # Chỉ sinh cho 1 quân cụ thể
            piece = board.get_piece(square)
            if piece and piece.color == color:
                pseudo_moves.extend(self._generate_piece_moves(board, square, piece))
        else:
            # Sinh cho tất cả quân của bên đang đi
            for r in range(8):
                for c in range(8):
                    sq = Square(r, c)
                    piece = board.get_piece(sq)
                    if piece and piece.color == color:
                        pseudo_moves.extend(self._generate_piece_moves(board, sq, piece))

        # Lọc bỏ nước đi để vua bị chiếu
        legal_moves = []
        for move in pseudo_moves:
            new_board = board.make_move(move)
            if not self.is_in_check(new_board, color):
                legal_moves.append(move)

        return legal_moves

    def _generate_piece_moves(self, board: Board, square: Square, piece: Piece) -> List[Move]:
        """Sinh pseudo-legal moves cho một quân cờ cụ thể."""
        generators = {
            "pawn": self._gen_pawn_moves,
            "knight": self._gen_knight_moves,
            "bishop": self._gen_bishop_moves,
            "rook": self._gen_rook_moves,
            "queen": self._gen_queen_moves,
            "king": self._gen_king_moves,
        }
        gen_func = generators.get(piece.piece_type)
        if gen_func:
            return gen_func(board, square, piece.color)
        return []

    # ------------------------------------------------------------------
    # Sinh nước đi cho từng loại quân
    # ------------------------------------------------------------------

    def _gen_pawn_moves(self, board: Board, sq: Square, color: str) -> List[Move]:
        """
        Sinh nước đi cho quân tốt.
        Đã hỗ trợ:
        - Đi thẳng 1 ô
        - Đi thẳng 2 ô (từ vị trí ban đầu)
        - Bắt chéo
        - Phong cấp

        TODO: Bắt tốt qua đường (en passant)
        """
        moves = []
        direction = -1 if color == "white" else 1
        start_row = 6 if color == "white" else 1
        promo_row = 0 if color == "white" else 7

        one_step = Square(sq.row + direction, sq.col)
        if one_step.is_valid() and board.get_piece(one_step) is None:
            self._append_pawn_moves(moves, sq, one_step, promo_row)

            two_step = Square(sq.row + 2 * direction, sq.col)
            if (
                sq.row == start_row
                and two_step.is_valid()
                and board.get_piece(two_step) is None
            ):
                moves.append(Move(sq, two_step))

        for col_offset in (-1, 1):
            target = Square(sq.row + direction, sq.col + col_offset)
            if not target.is_valid():
                continue

            target_piece = board.get_piece(target)
            if target_piece is not None and target_piece.color != color:
                self._append_pawn_moves(
                    moves,
                    sq,
                    target,
                    promo_row,
                    captured=target_piece,
                )

        return moves

    def _append_pawn_moves(
        self,
        moves: List[Move],
        from_sq: Square,
        to_sq: Square,
        promotion_row: int,
        captured: Optional[Piece] = None,
    ) -> None:
        """Thêm một nước tốt thường hoặc bốn lựa chọn phong cấp."""
        if to_sq.row == promotion_row:
            for promotion in self.PROMOTION_PIECES:
                moves.append(
                    Move(
                        from_sq,
                        to_sq,
                        promotion=promotion,
                        captured=captured,
                    )
                )
        else:
            moves.append(Move(from_sq, to_sq, captured=captured))

    def _gen_knight_moves(self, board: Board, sq: Square, color: str) -> List[Move]:
        """Sinh nước đi cho quân mã."""
        moves = []
        for dr, dc in self.KNIGHT_OFFSETS:
            target = Square(sq.row + dr, sq.col + dc)
            if target.is_valid():
                target_piece = board.get_piece(target)
                if target_piece is None or target_piece.color != color:
                    moves.append(Move(sq, target, captured=target_piece))
        return moves

    def _gen_sliding_moves(self, board: Board, sq: Square, color: str,
                           directions: list) -> List[Move]:
        """Sinh nước đi cho quân trượt (xe, tượng, hậu)."""
        moves = []
        for dr, dc in directions:
            r, c = sq.row + dr, sq.col + dc
            while 0 <= r <= 7 and 0 <= c <= 7:
                target = Square(r, c)
                target_piece = board.get_piece(target)
                if target_piece is None:
                    moves.append(Move(sq, target))
                elif target_piece.color != color:
                    moves.append(Move(sq, target, captured=target_piece))
                    break
                else:
                    break
                r += dr
                c += dc
        return moves

    def _gen_bishop_moves(self, board: Board, sq: Square, color: str) -> List[Move]:
        return self._gen_sliding_moves(board, sq, color, self.BISHOP_DIRS)

    def _gen_rook_moves(self, board: Board, sq: Square, color: str) -> List[Move]:
        return self._gen_sliding_moves(board, sq, color, self.ROOK_DIRS)

    def _gen_queen_moves(self, board: Board, sq: Square, color: str) -> List[Move]:
        return self._gen_sliding_moves(board, sq, color, self.QUEEN_DIRS)

    def _gen_king_moves(self, board: Board, sq: Square, color: str) -> List[Move]:
        """
        Sinh nước đi cho quân vua.
        TODO: Thêm nhập thành (castling).
        """
        moves = []
        for dr, dc in self.KING_OFFSETS:
            target = Square(sq.row + dr, sq.col + dc)
            if target.is_valid():
                target_piece = board.get_piece(target)
                if target_piece is None or target_piece.color != color:
                    moves.append(Move(sq, target, captured=target_piece))
        return moves

    # ------------------------------------------------------------------
    # Kiểm tra trạng thái
    # ------------------------------------------------------------------

    def is_in_check(self, board: Board, color: str) -> bool:
        """
        Kiểm tra xem vua của bên `color` có đang bị chiếu không.

        TODO: Implement
        - Tìm vị trí vua
        - Kiểm tra xem có quân đối phương nào tấn công được vua không
        """
        king_sq = board.find_king(color)
        if king_sq is None:
            return False

        opponent = "black" if color == "white" else "white"
        # TODO: Kiểm tra tấn công từ các hướng

        return False

    def is_checkmate(self, board: Board) -> bool:
        """Kiểm tra chiếu hết."""
        color = board.current_player
        if not self.is_in_check(board, color):
            return False
        return len(self.generate_legal_moves(board)) == 0

    def is_stalemate(self, board: Board) -> bool:
        """Kiểm tra hòa do hết nước đi (stalemate)."""
        color = board.current_player
        if self.is_in_check(board, color):
            return False
        return len(self.generate_legal_moves(board)) == 0

    def get_game_status(self, board: Board) -> str:
        """
        Xác định trạng thái ván đấu.

        Returns:
            'playing', 'check', 'checkmate', 'stalemate', 'draw'
        """
        if self.is_checkmate(board):
            return "checkmate"
        if self.is_stalemate(board):
            return "stalemate"
        if board.half_move_clock >= 100:
            return "draw"
        if self.is_in_check(board, board.current_player):
            return "check"
        return "playing"
