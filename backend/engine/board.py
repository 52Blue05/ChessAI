"""
backend/engine/board.py
Quản lý trạng thái bàn cờ (State bàn cờ).

Sử dụng chuẩn FEN (Forsyth–Edwards Notation) để biểu diễn trạng thái.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from copy import deepcopy


# Mapping ký tự FEN -> (loại quân, màu)
FEN_PIECE_MAP = {
    "K": ("king", "white"), "Q": ("queen", "white"), "R": ("rook", "white"),
    "B": ("bishop", "white"), "N": ("knight", "white"), "P": ("pawn", "white"),
    "k": ("king", "black"), "q": ("queen", "black"), "r": ("rook", "black"),
    "b": ("bishop", "black"), "n": ("knight", "black"), "p": ("pawn", "black"),
}

PIECE_TO_FEN = {v: k for k, v in FEN_PIECE_MAP.items()}

# FEN khởi đầu tiêu chuẩn
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@dataclass
class Square:
    """Tọa độ một ô trên bàn cờ (0-indexed)."""
    row: int  # 0 = hàng 8 (đen), 7 = hàng 1 (trắng)
    col: int  # 0 = cột a, 7 = cột h

    def to_algebraic(self) -> str:
        """Chuyển sang ký hiệu đại số, ví dụ: (6, 4) -> 'e2'."""
        return chr(ord("a") + self.col) + str(8 - self.row)

    @staticmethod
    def from_algebraic(notation: str) -> "Square":
        """Chuyển từ ký hiệu đại số sang Square, ví dụ: 'e2' -> (6, 4)."""
        col = ord(notation[0]) - ord("a")
        row = 8 - int(notation[1])
        return Square(row, col)

    def is_valid(self) -> bool:
        return 0 <= self.row <= 7 and 0 <= self.col <= 7


@dataclass
class Piece:
    """Một quân cờ."""
    piece_type: str   # king, queen, rook, bishop, knight, pawn
    color: str        # white, black

    def to_fen_char(self) -> str:
        return PIECE_TO_FEN[(self.piece_type, self.color)]


@dataclass
class Move:
    """Nước đi."""
    from_sq: Square
    to_sq: Square
    promotion: Optional[str] = None   # Phong cấp: queen, rook, bishop, knight
    captured: Optional[Piece] = None  # Quân bị bắt

    def to_uci(self) -> str:
        """Chuyển sang UCI notation, ví dụ: 'e2e4'."""
        uci = self.from_sq.to_algebraic() + self.to_sq.to_algebraic()
        if self.promotion:
            uci += self.promotion[0].lower()
        return uci


@dataclass
class CastlingRights:
    """Quyền nhập thành."""
    white_king_side: bool = True
    white_queen_side: bool = True
    black_king_side: bool = True
    black_queen_side: bool = True


@dataclass
class Board:
    """
    Trạng thái bàn cờ.

    Attributes:
        grid: Bàn cờ 8x8, mỗi ô là Piece hoặc None.
        current_player: Lượt đi hiện tại ('white' hoặc 'black').
        castling: Quyền nhập thành.
        en_passant: Ô bắt tốt qua đường (en passant), None nếu không có.
        half_move_clock: Đếm nước đi cho luật 50 nước.
        full_move_number: Số lượt đi đầy đủ.
    """
    grid: list = field(default_factory=lambda: [[None] * 8 for _ in range(8)])
    current_player: str = "white"
    castling: CastlingRights = field(default_factory=CastlingRights)
    en_passant: Optional[Square] = None
    half_move_clock: int = 0
    full_move_number: int = 1

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def from_fen(fen: str = STARTING_FEN) -> "Board":
        """Tạo Board từ chuỗi FEN."""
        parts = fen.split()
        board = Board()

        # 1. Piece placement
        rows = parts[0].split("/")
        for r, row_str in enumerate(rows):
            col = 0
            for ch in row_str:
                if ch.isdigit():
                    col += int(ch)
                else:
                    piece_info = FEN_PIECE_MAP.get(ch)
                    if piece_info:
                        board.grid[r][col] = Piece(piece_info[0], piece_info[1])
                    col += 1

        # 2. Active color
        board.current_player = "white" if parts[1] == "w" else "black"

        # 3. Castling availability
        castling_str = parts[2]
        board.castling = CastlingRights(
            white_king_side="K" in castling_str,
            white_queen_side="Q" in castling_str,
            black_king_side="k" in castling_str,
            black_queen_side="q" in castling_str,
        )

        # 4. En passant target square
        if parts[3] != "-":
            board.en_passant = Square.from_algebraic(parts[3])
        else:
            board.en_passant = None

        # 5. Halfmove clock & fullmove number
        board.half_move_clock = int(parts[4])
        board.full_move_number = int(parts[5])

        return board

    def to_fen(self) -> str:
        """Xuất trạng thái bàn cờ ra chuỗi FEN."""
        # 1. Piece placement
        rows = []
        for r in range(8):
            empty = 0
            row_str = ""
            for c in range(8):
                piece = self.grid[r][c]
                if piece is None:
                    empty += 1
                else:
                    if empty > 0:
                        row_str += str(empty)
                        empty = 0
                    row_str += piece.to_fen_char()
            if empty > 0:
                row_str += str(empty)
            rows.append(row_str)
        placement = "/".join(rows)

        # 2. Active color
        color = "w" if self.current_player == "white" else "b"

        # 3. Castling
        castling = ""
        if self.castling.white_king_side: castling += "K"
        if self.castling.white_queen_side: castling += "Q"
        if self.castling.black_king_side: castling += "k"
        if self.castling.black_queen_side: castling += "q"
        if not castling:
            castling = "-"

        # 4. En passant
        ep = self.en_passant.to_algebraic() if self.en_passant else "-"

        return f"{placement} {color} {castling} {ep} {self.half_move_clock} {self.full_move_number}"

    # ------------------------------------------------------------------
    # Board operations
    # ------------------------------------------------------------------

    def get_piece(self, square: Square) -> Optional[Piece]:
        """Lấy quân cờ tại ô chỉ định."""
        if not square.is_valid():
            return None
        return self.grid[square.row][square.col]

    def set_piece(self, square: Square, piece: Optional[Piece]) -> None:
        """Đặt quân cờ tại ô chỉ định."""
        self.grid[square.row][square.col] = piece

    def make_move(self, move: Move) -> "Board":
        """
        Thực hiện nước đi và trả về Board MỚI (immutable pattern).
        Board cũ không bị thay đổi.

        TODO: Implement đầy đủ:
        - Di chuyển quân
        - Bắt quân
        - Phong cấp
        - Nhập thành
        - Bắt tốt qua đường (en passant)
        - Cập nhật castling rights
        - Đổi lượt
        """
        new_board = deepcopy(self)

        piece = new_board.get_piece(move.from_sq)
        captured = new_board.get_piece(move.to_sq)
        move.captured = captured

        # Di chuyển quân
        new_board.set_piece(move.to_sq, piece)
        new_board.set_piece(move.from_sq, None)

        # Phong cấp
        if move.promotion and piece:
            new_board.set_piece(move.to_sq, Piece(move.promotion, piece.color))

        # TODO: Nhập thành, en passant, cập nhật castling rights

        # Đổi lượt
        new_board.current_player = "black" if self.current_player == "white" else "white"

        # Cập nhật counters
        if piece and piece.piece_type == "pawn" or captured:
            new_board.half_move_clock = 0
        else:
            new_board.half_move_clock = self.half_move_clock + 1

        if self.current_player == "black":
            new_board.full_move_number = self.full_move_number + 1

        return new_board

    def copy(self) -> "Board":
        """Tạo bản sao deep copy."""
        return deepcopy(self)

    def find_king(self, color: str) -> Optional[Square]:
        """Tìm vị trí vua của một bên."""
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.piece_type == "king" and piece.color == color:
                    return Square(r, c)
        return None

    def __repr__(self) -> str:
        """Hiển thị bàn cờ dạng text (debug)."""
        lines = ["  a b c d e f g h"]
        for r in range(8):
            row_str = f"{8 - r} "
            for c in range(8):
                piece = self.grid[r][c]
                if piece:
                    row_str += piece.to_fen_char() + " "
                else:
                    row_str += ". "
            row_str += f"{8 - r}"
            lines.append(row_str)
        lines.append("  a b c d e f g h")
        return "\n".join(lines)
