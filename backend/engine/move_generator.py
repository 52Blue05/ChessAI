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

        Nước đi pseudo-legal được áp dụng lên một Board mới rồi lọc bỏ nếu
        vua của bên đang đi vẫn bị chiếu. Cách lọc này xử lý cả quân bị ghim
        và en passant làm lộ đường tấn công vào vua.
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
        - Bắt tốt qua đường (en passant)
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
            if (
                target_piece is not None
                and target_piece.color != color
                and target_piece.piece_type != "king"
            ):
                self._append_pawn_moves(
                    moves,
                    sq,
                    target,
                    promo_row,
                    captured=target_piece,
                )

        if board.en_passant is not None:
            target = board.en_passant
            if (
                target.row == sq.row + direction
                and abs(target.col - sq.col) == 1
                and board.get_piece(target) is None
            ):
                captured = board.get_piece(Square(sq.row, target.col))
                if (
                    captured is not None
                    and captured.piece_type == "pawn"
                    and captured.color != color
                ):
                    moves.append(Move(sq, target, captured=captured))

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
                if target_piece is None:
                    moves.append(Move(sq, target))
                elif (
                    target_piece.color != color
                    and target_piece.piece_type != "king"
                ):
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
                    if target_piece.piece_type != "king":
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
        """Sinh nước đi thường và nhập thành cho quân vua."""
        moves = []
        for dr, dc in self.KING_OFFSETS:
            target = Square(sq.row + dr, sq.col + dc)
            if target.is_valid():
                target_piece = board.get_piece(target)
                if target_piece is None:
                    moves.append(Move(sq, target))
                elif (
                    target_piece.color != color
                    and target_piece.piece_type != "king"
                ):
                    moves.append(Move(sq, target, captured=target_piece))
        moves.extend(self._gen_castling_moves(board, sq, color))
        return moves

    def _gen_castling_moves(
        self,
        board: Board,
        king_sq: Square,
        color: str,
    ) -> List[Move]:
        """Sinh nhập thành khi quyền, quân, khoảng trống và attack map hợp lệ."""
        home_row = 7 if color == "white" else 0
        if king_sq != Square(home_row, 4):
            return []

        opponent = self._opponent(color)
        if self.is_square_attacked(board, king_sq, opponent):
            return []

        if color == "white":
            rights = (
                board.castling.white_king_side,
                board.castling.white_queen_side,
            )
        else:
            rights = (
                board.castling.black_king_side,
                board.castling.black_queen_side,
            )

        moves = []
        candidates = (
            (
                rights[0],
                7,
                (5, 6),
                (5, 6),
                6,
            ),
            (
                rights[1],
                0,
                (1, 2, 3),
                (3, 2),
                2,
            ),
        )
        for has_right, rook_col, empty_cols, king_path, destination_col in candidates:
            if not has_right:
                continue
            if board.get_piece(Square(home_row, rook_col)) != Piece("rook", color):
                continue
            if any(
                board.get_piece(Square(home_row, col)) is not None
                for col in empty_cols
            ):
                continue
            if any(
                self._king_transit_square_is_attacked(
                    board,
                    king_sq,
                    Square(home_row, col),
                    color,
                    opponent,
                )
                for col in king_path
            ):
                continue
            moves.append(Move(king_sq, Square(home_row, destination_col)))

        return moves

    def _king_transit_square_is_attacked(
        self,
        board: Board,
        from_sq: Square,
        transit_sq: Square,
        color: str,
        opponent: str,
    ) -> bool:
        """Kiểm tra ô nhập thành sau khi tạm dời vua khỏi ô xuất phát."""
        transit_board = board.copy()
        transit_board.set_piece(from_sq, None)
        transit_board.set_piece(transit_sq, Piece("king", color))
        return self.is_square_attacked(transit_board, transit_sq, opponent)

    # ------------------------------------------------------------------
    # Kiểm tra trạng thái
    # ------------------------------------------------------------------

    def is_square_attacked(
        self,
        board: Board,
        square: Square,
        by_color: str,
    ) -> bool:
        """Kiểm tra attack map mà không sinh legal moves hoặc gọi đệ quy."""
        pawn_direction = -1 if by_color == "white" else 1
        pawn_row = square.row - pawn_direction
        for pawn_col in (square.col - 1, square.col + 1):
            attacker = Square(pawn_row, pawn_col)
            if (
                attacker.is_valid()
                and board.get_piece(attacker) == Piece("pawn", by_color)
            ):
                return True

        for dr, dc in self.KNIGHT_OFFSETS:
            attacker = Square(square.row + dr, square.col + dc)
            if (
                attacker.is_valid()
                and board.get_piece(attacker) == Piece("knight", by_color)
            ):
                return True

        for dr, dc in self.KING_OFFSETS:
            attacker = Square(square.row + dr, square.col + dc)
            if (
                attacker.is_valid()
                and board.get_piece(attacker) == Piece("king", by_color)
            ):
                return True

        if self._is_attacked_by_slider(
            board,
            square,
            by_color,
            self.ROOK_DIRS,
            {"rook", "queen"},
        ):
            return True

        return self._is_attacked_by_slider(
            board,
            square,
            by_color,
            self.BISHOP_DIRS,
            {"bishop", "queen"},
        )

    def _is_attacked_by_slider(
        self,
        board: Board,
        square: Square,
        by_color: str,
        directions: list,
        piece_types: set,
    ) -> bool:
        """Tìm xe/tượng/hậu đầu tiên nhìn thấy từ một ô theo các tia."""
        for dr, dc in directions:
            row, col = square.row + dr, square.col + dc
            while 0 <= row <= 7 and 0 <= col <= 7:
                piece = board.get_piece(Square(row, col))
                if piece is not None:
                    if piece.color == by_color and piece.piece_type in piece_types:
                        return True
                    break
                row += dr
                col += dc
        return False

    def is_in_check(self, board: Board, color: str) -> bool:
        """Trả về True nếu vua của `color` đang bị đối phương tấn công."""
        king_sq = board.find_king(color)
        if king_sq is None:
            return False

        return self.is_square_attacked(board, king_sq, self._opponent(color))

    @staticmethod
    def _opponent(color: str) -> str:
        return "black" if color == "white" else "white"

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
