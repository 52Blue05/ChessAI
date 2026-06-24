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
        - Đi thẳng 1 ô
        - Đi thẳng 2 ô (từ vị trí ban đầu)
        - Bắt chéo
        - Bắt tốt qua đường (en passant)
        - Phong cấp
        """
        moves = []
        direction = -1 if color == "white" else 1
        start_row = 6 if color == "white" else 1
        promo_row = 0 if color == "white" else 7
        promotion_pieces = ["queen", "rook", "bishop", "knight"]

        # --- Đi thẳng 1 ô ---
        one_ahead = Square(sq.row + direction, sq.col)
        if one_ahead.is_valid() and board.get_piece(one_ahead) is None:
            if one_ahead.row == promo_row:
                # Phong cấp
                for promo in promotion_pieces:
                    moves.append(Move(sq, one_ahead, promotion=promo))
            else:
                moves.append(Move(sq, one_ahead))

            # --- Đi thẳng 2 ô (từ vị trí ban đầu) ---
            if sq.row == start_row:
                two_ahead = Square(sq.row + 2 * direction, sq.col)
                if two_ahead.is_valid() and board.get_piece(two_ahead) is None:
                    moves.append(Move(sq, two_ahead))

        # --- Bắt chéo ---
        for dc in [-1, 1]:
            capture_sq = Square(sq.row + direction, sq.col + dc)
            if not capture_sq.is_valid():
                continue

            target = board.get_piece(capture_sq)
            if target and target.color != color:
                if capture_sq.row == promo_row:
                    for promo in promotion_pieces:
                        moves.append(Move(sq, capture_sq, promotion=promo, captured=target))
                else:
                    moves.append(Move(sq, capture_sq, captured=target))

            # --- Bắt tốt qua đường (en passant) ---
            if (board.en_passant and
                capture_sq.row == board.en_passant.row and
                capture_sq.col == board.en_passant.col):
                # Quân tốt bị bắt nằm cạnh (cùng hàng với quân đang đi)
                captured_pawn = board.get_piece(Square(sq.row, sq.col + dc))
                moves.append(Move(sq, capture_sq, captured=captured_pawn))

        return moves

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
        Sinh nước đi cho quân vua, bao gồm nhập thành (castling).
        """
        moves = []
        for dr, dc in self.KING_OFFSETS:
            target = Square(sq.row + dr, sq.col + dc)
            if target.is_valid():
                target_piece = board.get_piece(target)
                if target_piece is None or target_piece.color != color:
                    moves.append(Move(sq, target, captured=target_piece))

        # --- Nhập thành (Castling) ---
        # Chỉ khi vua chưa bị chiếu
        if not self.is_in_check(board, color):
            back_row = 7 if color == "white" else 0
            if sq.row == back_row and sq.col == 4:
                # King-side castling (O-O)
                can_ks = (board.castling.white_king_side if color == "white"
                          else board.castling.black_king_side)
                if can_ks:
                    # Ô f và g phải trống
                    if (board.get_piece(Square(back_row, 5)) is None and
                        board.get_piece(Square(back_row, 6)) is None):
                        # Vua không đi qua ô bị tấn công
                        temp1 = board.make_move(Move(sq, Square(back_row, 5)))
                        if not self.is_in_check(temp1, color):
                            moves.append(Move(sq, Square(back_row, 6)))

                # Queen-side castling (O-O-O)
                can_qs = (board.castling.white_queen_side if color == "white"
                          else board.castling.black_queen_side)
                if can_qs:
                    # Ô b, c, d phải trống
                    if (board.get_piece(Square(back_row, 1)) is None and
                        board.get_piece(Square(back_row, 2)) is None and
                        board.get_piece(Square(back_row, 3)) is None):
                        # Vua không đi qua ô bị tấn công
                        temp1 = board.make_move(Move(sq, Square(back_row, 3)))
                        if not self.is_in_check(temp1, color):
                            moves.append(Move(sq, Square(back_row, 2)))

        return moves

    # ------------------------------------------------------------------
    # Kiểm tra trạng thái
    # ------------------------------------------------------------------

    def is_in_check(self, board: Board, color: str) -> bool:
        """
        Kiểm tra xem vua của bên `color` có đang bị chiếu không.
        Kiểm tra tấn công từ tất cả loại quân đối phương.
        """
        king_sq = board.find_king(color)
        if king_sq is None:
            return False

        opponent = "black" if color == "white" else "white"
        kr, kc = king_sq.row, king_sq.col

        # --- Kiểm tra tấn công từ Mã (Knight) ---
        for dr, dc in self.KNIGHT_OFFSETS:
            sq = Square(kr + dr, kc + dc)
            if sq.is_valid():
                p = board.get_piece(sq)
                if p and p.color == opponent and p.piece_type == "knight":
                    return True

        # --- Kiểm tra tấn công từ quân trượt thẳng: Xe, Hậu (Rook, Queen) ---
        for dr, dc in self.ROOK_DIRS:
            r, c = kr + dr, kc + dc
            while 0 <= r <= 7 and 0 <= c <= 7:
                p = board.get_piece(Square(r, c))
                if p:
                    if p.color == opponent and p.piece_type in ("rook", "queen"):
                        return True
                    break  # Bị chặn bởi quân khác
                r += dr
                c += dc

        # --- Kiểm tra tấn công từ quân trượt chéo: Tượng, Hậu (Bishop, Queen) ---
        for dr, dc in self.BISHOP_DIRS:
            r, c = kr + dr, kc + dc
            while 0 <= r <= 7 and 0 <= c <= 7:
                p = board.get_piece(Square(r, c))
                if p:
                    if p.color == opponent and p.piece_type in ("bishop", "queen"):
                        return True
                    break
                r += dr
                c += dc

        # --- Kiểm tra tấn công từ Tốt (Pawn) ---
        pawn_dir = 1 if color == "white" else -1  # Tốt đối phương tấn công từ hướng nào
        for dc in [-1, 1]:
            sq = Square(kr + pawn_dir, kc + dc)
            if sq.is_valid():
                p = board.get_piece(sq)
                if p and p.color == opponent and p.piece_type == "pawn":
                    return True

        # --- Kiểm tra tấn công từ Vua đối phương ---
        for dr, dc in self.KING_OFFSETS:
            sq = Square(kr + dr, kc + dc)
            if sq.is_valid():
                p = board.get_piece(sq)
                if p and p.color == opponent and p.piece_type == "king":
                    return True

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
