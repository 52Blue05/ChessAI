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
PROMOTION_PIECES = {"queen", "rook", "bishop", "knight"}

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

        Kiểm tra và thực hiện di chuyển cơ bản, bắt quân, phong cấp,
        nhập thành và bắt tốt qua đường. Việc kiểm tra nước đi có để
        vua bị chiếu hay không thuộc trách nhiệm của MoveGenerator.
        """
        piece, captured = self._validate_move(move)
        new_board = deepcopy(self)
        is_castling = (
            piece.piece_type == "king"
            and move.from_sq.row == move.to_sq.row
            and abs(move.to_sq.col - move.from_sq.col) == 2
        )
        is_en_passant = (
            piece.piece_type == "pawn"
            and move.from_sq.col != move.to_sq.col
            and self.get_piece(move.to_sq) is None
            and self.en_passant == move.to_sq
        )

        move.captured = captured

        # Di chuyển quân
        new_board.set_piece(move.to_sq, deepcopy(piece))
        new_board.set_piece(move.from_sq, None)

        # Bắt tốt qua đường: quân bị bắt nằm cạnh ô xuất phát.
        if is_en_passant:
            captured_sq = Square(move.from_sq.row, move.to_sq.col)
            new_board.set_piece(captured_sq, None)

        # Nhập thành: di chuyển xe sang phía bên kia của vua.
        if is_castling:
            rook_from_col = 7 if move.to_sq.col == 6 else 0
            rook_to_col = 5 if move.to_sq.col == 6 else 3
            rook_from = Square(move.from_sq.row, rook_from_col)
            rook_to = Square(move.from_sq.row, rook_to_col)
            rook = new_board.get_piece(rook_from)
            new_board.set_piece(rook_to, rook)
            new_board.set_piece(rook_from, None)

        # Phong cấp
        if move.promotion:
            new_board.set_piece(move.to_sq, Piece(move.promotion, piece.color))

        new_board._update_castling_rights(piece, move, captured)

        # En passant chỉ có hiệu lực đúng một lượt.
        new_board.en_passant = None
        if (
            piece.piece_type == "pawn"
            and move.from_sq.col == move.to_sq.col
            and abs(move.to_sq.row - move.from_sq.row) == 2
        ):
            new_board.en_passant = Square(
                (move.from_sq.row + move.to_sq.row) // 2,
                move.from_sq.col,
            )

        # Đổi lượt
        new_board.current_player = "black" if self.current_player == "white" else "white"

        # Cập nhật counters
        if piece.piece_type == "pawn" or captured:
            new_board.half_move_clock = 0
        else:
            new_board.half_move_clock = self.half_move_clock + 1

        if self.current_player == "black":
            new_board.full_move_number = self.full_move_number + 1

        return new_board

    def _validate_move(self, move: Move) -> tuple[Piece, Optional[Piece]]:
        """Kiểm tra một nước đi pseudo-legal trước khi cập nhật bàn cờ."""
        if not move.from_sq.is_valid() or not move.to_sq.is_valid():
            raise ValueError("Move squares must be on the board")
        if move.from_sq == move.to_sq:
            raise ValueError("Source and destination squares must differ")

        piece = self.get_piece(move.from_sq)
        if piece is None:
            raise ValueError("Cannot move from an empty square")
        if piece.color != self.current_player:
            raise ValueError("Cannot move a piece of the wrong color")

        captured = self.get_piece(move.to_sq)
        if captured and captured.color == piece.color:
            raise ValueError("Cannot capture a piece of the same color")
        if captured and captured.piece_type == "king":
            raise ValueError("Cannot capture the opponent king")

        row_delta = move.to_sq.row - move.from_sq.row
        col_delta = move.to_sq.col - move.from_sq.col
        abs_row = abs(row_delta)
        abs_col = abs(col_delta)

        if piece.piece_type == "pawn":
            captured = self._validate_pawn_move(move, piece, captured)
        elif piece.piece_type == "knight":
            if (abs_row, abs_col) not in {(1, 2), (2, 1)}:
                raise ValueError("Invalid knight move")
        elif piece.piece_type == "bishop":
            if abs_row == 0 or abs_row != abs_col:
                raise ValueError("Invalid bishop move")
            self._validate_clear_path(move)
        elif piece.piece_type == "rook":
            if not ((row_delta == 0) ^ (col_delta == 0)):
                raise ValueError("Invalid rook move")
            self._validate_clear_path(move)
        elif piece.piece_type == "queen":
            is_straight = (row_delta == 0) ^ (col_delta == 0)
            is_diagonal = abs_row > 0 and abs_row == abs_col
            if not (is_straight or is_diagonal):
                raise ValueError("Invalid queen move")
            self._validate_clear_path(move)
        elif piece.piece_type == "king":
            if row_delta == 0 and abs_col == 2:
                self._validate_castling_structure(move, piece)
            elif max(abs_row, abs_col) != 1:
                raise ValueError("Invalid king move")
        else:
            raise ValueError(f"Unknown piece type: {piece.piece_type}")

        if piece.piece_type != "pawn" and move.promotion is not None:
            raise ValueError("Only pawns can be promoted")

        return piece, captured

    def _validate_pawn_move(
        self,
        move: Move,
        piece: Piece,
        captured: Optional[Piece],
    ) -> Optional[Piece]:
        """Kiểm tra nước tiến, bắt chéo và phong cấp của tốt."""
        direction = -1 if piece.color == "white" else 1
        start_row = 6 if piece.color == "white" else 1
        promotion_row = 0 if piece.color == "white" else 7
        row_delta = move.to_sq.row - move.from_sq.row
        col_delta = move.to_sq.col - move.from_sq.col

        if col_delta == 0:
            if captured is not None:
                raise ValueError("Pawn cannot capture straight ahead")
            if row_delta == direction:
                pass
            elif row_delta == 2 * direction and move.from_sq.row == start_row:
                middle = Square(move.from_sq.row + direction, move.from_sq.col)
                if self.get_piece(middle) is not None:
                    raise ValueError("Pawn cannot jump over a piece")
            else:
                raise ValueError("Invalid pawn move")
        elif abs(col_delta) == 1 and row_delta == direction:
            if captured is None:
                if self.en_passant != move.to_sq:
                    raise ValueError("Pawn diagonal move requires a capture")
                captured_sq = Square(move.from_sq.row, move.to_sq.col)
                captured = self.get_piece(captured_sq)
                if (
                    captured is None
                    or captured.piece_type != "pawn"
                    or captured.color == piece.color
                ):
                    raise ValueError("Invalid en passant capture")
        else:
            raise ValueError("Invalid pawn move")

        reaches_promotion = move.to_sq.row == promotion_row
        if reaches_promotion:
            if move.promotion not in PROMOTION_PIECES:
                raise ValueError("Pawn reaching the last rank must promote")
        elif move.promotion is not None:
            raise ValueError("Pawn can only promote on the last rank")

        return captured

    def _validate_castling_structure(self, move: Move, king: Piece) -> None:
        """Kiểm tra quyền, vị trí quân và khoảng trống khi nhập thành."""
        home_row = 7 if king.color == "white" else 0
        if move.from_sq != Square(home_row, 4):
            raise ValueError("King is not on its castling square")

        king_side = move.to_sq == Square(home_row, 6)
        queen_side = move.to_sq == Square(home_row, 2)
        if not (king_side or queen_side):
            raise ValueError("Invalid castling destination")

        if king.color == "white":
            has_right = (
                self.castling.white_king_side
                if king_side
                else self.castling.white_queen_side
            )
        else:
            has_right = (
                self.castling.black_king_side
                if king_side
                else self.castling.black_queen_side
            )
        if not has_right:
            raise ValueError("Castling rights are not available")

        rook_col = 7 if king_side else 0
        rook = self.get_piece(Square(home_row, rook_col))
        if rook != Piece("rook", king.color):
            raise ValueError("Required rook is not on its castling square")

        between_cols = (5, 6) if king_side else (1, 2, 3)
        if any(
            self.get_piece(Square(home_row, col)) is not None
            for col in between_cols
        ):
            raise ValueError("Castling path is blocked")

    def _validate_clear_path(self, move: Move) -> None:
        """Từ chối nước đi của quân trượt nếu có quân cản đường."""
        row_step = (move.to_sq.row > move.from_sq.row) - (
            move.to_sq.row < move.from_sq.row
        )
        col_step = (move.to_sq.col > move.from_sq.col) - (
            move.to_sq.col < move.from_sq.col
        )

        row = move.from_sq.row + row_step
        col = move.from_sq.col + col_step
        while (row, col) != (move.to_sq.row, move.to_sq.col):
            if self.get_piece(Square(row, col)) is not None:
                raise ValueError("Sliding piece path is blocked")
            row += row_step
            col += col_step

    def _update_castling_rights(
        self,
        piece: Piece,
        move: Move,
        captured: Optional[Piece],
    ) -> None:
        """Cập nhật quyền nhập thành sau khi vua/xe đi hoặc xe bị bắt."""
        if piece.piece_type == "king":
            if piece.color == "white":
                self.castling.white_king_side = False
                self.castling.white_queen_side = False
            else:
                self.castling.black_king_side = False
                self.castling.black_queen_side = False

        if piece.piece_type == "rook":
            self._disable_rook_castling_right(piece.color, move.from_sq)

        if captured and captured.piece_type == "rook":
            self._disable_rook_castling_right(captured.color, move.to_sq)

    def _disable_rook_castling_right(self, color: str, square: Square) -> None:
        """Tắt quyền nhập thành gắn với ô xuất phát của một xe."""
        if color == "white":
            if square == Square(7, 0):
                self.castling.white_queen_side = False
            elif square == Square(7, 7):
                self.castling.white_king_side = False
        else:
            if square == Square(0, 0):
                self.castling.black_queen_side = False
            elif square == Square(0, 7):
                self.castling.black_king_side = False

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
