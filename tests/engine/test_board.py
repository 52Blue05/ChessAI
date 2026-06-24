"""
tests/engine/test_board.py
Unit tests cho Board (engine) và AI agents.

Chạy: pytest tests/ -v
"""

import math
import sys
from pathlib import Path

# Thêm root vào path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from backend.engine.board import Board, Square, Move, Piece, STARTING_FEN
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkStats


# ==============================================================
# Test Board
# ==============================================================

class TestBoard:
    """Test class Board."""

    def test_from_starting_fen(self):
        """Board khởi tạo từ FEN mặc định."""
        board = Board.from_fen()

        # Kiểm tra quân trắng hàng 1
        assert board.grid[7][0].piece_type == "rook"
        assert board.grid[7][0].color == "white"
        assert board.grid[7][4].piece_type == "king"

        # Kiểm tra quân đen hàng 8
        assert board.grid[0][0].piece_type == "rook"
        assert board.grid[0][0].color == "black"
        assert board.grid[0][4].piece_type == "king"

        # Kiểm tra tốt
        for c in range(8):
            assert board.grid[1][c].piece_type == "pawn"
            assert board.grid[1][c].color == "black"
            assert board.grid[6][c].piece_type == "pawn"
            assert board.grid[6][c].color == "white"

        # Ô trống
        for r in range(2, 6):
            for c in range(8):
                assert board.grid[r][c] is None

    def test_to_fen(self):
        """Board -> FEN -> Board round-trip."""
        board = Board.from_fen(STARTING_FEN)
        fen = board.to_fen()
        assert fen == STARTING_FEN

    def test_current_player(self):
        """Kiểm tra lượt đi."""
        board = Board.from_fen()
        assert board.current_player == "white"

    def test_make_move_changes_player(self):
        """make_move phải đổi lượt."""
        board = Board.from_fen()
        move = Move(Square(6, 4), Square(4, 4))  # e2-e4
        new_board = board.make_move(move)

        assert new_board.current_player == "black"
        assert board.current_player == "white"  # Board cũ không đổi

    def test_make_move_moves_piece(self):
        """make_move phải di chuyển quân."""
        board = Board.from_fen()
        move = Move(Square(6, 4), Square(4, 4))  # e2-e4
        new_board = board.make_move(move)

        assert new_board.grid[4][4].piece_type == "pawn"
        assert new_board.grid[4][4].color == "white"
        assert new_board.grid[6][4] is None

    def test_black_pawn_e7_to_e5(self):
        """Tốt đen được đi hai ô từ vị trí ban đầu khi đến lượt đen."""
        board = Board.from_fen()
        board = board.make_move(Move(Square(6, 4), Square(4, 4)))  # e2-e4
        board = board.make_move(Move(Square(1, 4), Square(3, 4)))  # e7-e5

        assert board.grid[3][4] == Piece("pawn", "black")
        assert board.grid[1][4] is None
        assert board.current_player == "white"

    def test_capture_updates_board(self):
        """Bắt quân phải xóa quân bị bắt và đặt quân đi vào ô đích."""
        board = Board.from_fen("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1")
        move = Move(Square(4, 4), Square(3, 3))  # e4xd5
        new_board = board.make_move(move)

        assert new_board.grid[3][3] == Piece("pawn", "white")
        assert new_board.grid[4][4] is None
        assert move.captured == Piece("pawn", "black")
        assert board.grid[3][3] == Piece("pawn", "black")

    def test_make_move_rejects_empty_square(self):
        board = Board.from_fen()

        with pytest.raises(ValueError, match="empty square"):
            board.make_move(Move(Square(4, 4), Square(3, 4)))

    def test_make_move_rejects_wrong_color(self):
        board = Board.from_fen()

        with pytest.raises(ValueError, match="wrong color"):
            board.make_move(Move(Square(1, 4), Square(3, 4)))

    def test_make_move_rejects_obviously_invalid_move(self):
        board = Board.from_fen()

        with pytest.raises(ValueError, match="Invalid pawn move"):
            board.make_move(Move(Square(6, 4), Square(3, 4)))  # e2-e5

        with pytest.raises(ValueError, match="same color"):
            board.make_move(Move(Square(7, 0), Square(6, 0)))  # Ra1xa2

        with pytest.raises(ValueError, match="path is blocked"):
            board.make_move(Move(Square(7, 0), Square(4, 0)))  # Ra1-a4

    def test_find_king(self):
        """Tìm vua."""
        board = Board.from_fen()
        white_king = board.find_king("white")
        black_king = board.find_king("black")

        assert white_king.row == 7 and white_king.col == 4  # e1
        assert black_king.row == 0 and black_king.col == 4  # e8

    def test_square_algebraic(self):
        """Chuyển đổi ký hiệu đại số."""
        sq = Square(6, 4)
        assert sq.to_algebraic() == "e2"

        sq2 = Square.from_algebraic("e2")
        assert sq2.row == 6 and sq2.col == 4

    def test_custom_fen(self):
        """Khởi tạo từ FEN tùy chỉnh."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        board = Board.from_fen(fen)

        assert board.current_player == "black"
        assert board.grid[4][4].piece_type == "pawn"
        assert board.grid[4][4].color == "white"

    def test_valid_fen_is_accepted(self):
        fen = "4k3/8/8/8/8/8/8/4K3 b - - 17 42"

        board = Board.from_fen(fen)

        assert board.to_fen() == fen

    @pytest.mark.parametrize(
        ("fen", "message"),
        [
            (
                "8/8/8/8/8/8/8/4K3 w - - 0 1",
                "exactly one white king and one black king",
            ),
            (
                "4k3/8/8/8/8/8/8/3K3 w - - 0 1",
                "exactly 8 squares",
            ),
            (
                "4k3/8/8/8/8/8/8/3XK3 w - - 0 1",
                "Invalid FEN piece symbol",
            ),
            (
                "4k3/8/8/8/8/8/8/4K3 x - - 0 1",
                "active color",
            ),
        ],
    )
    def test_invalid_fen_is_rejected(self, fen, message):
        with pytest.raises(ValueError, match=message):
            Board.from_fen(fen)

    @pytest.mark.parametrize(
        "fen",
        [
            "4k3/8/8/8/8/8/8/4K3 w - - 0",
            "4k3/8/8/8/8/8/8/4K3 w KK - 0 1",
            "4k3/8/8/8/8/8/8/4K3 w A - 0 1",
            "4k3/8/8/8/8/8/8/4K3 w - z9 0 1",
            "4k3/8/8/8/8/8/8/4K3 w - - -1 1",
            "4k3/8/8/8/8/8/8/4K3 w - - 0 0",
        ],
    )
    def test_invalid_fen_metadata_is_rejected(self, fen):
        with pytest.raises(ValueError):
            Board.from_fen(fen)


# ==============================================================
# Test MoveGenerator
# ==============================================================

class TestMoveGenerator:
    """Test class MoveGenerator."""

    def setup_method(self):
        self.gen = MoveGenerator()

    def test_starting_position_move_count(self):
        """
        Vị trí khởi đầu: trắng có 20 nước đi hợp lệ.
        (16 nước tốt + 4 nước mã)
        """
        board = Board.from_fen()
        moves = self.gen.generate_legal_moves(board)
        assert len(moves) == 20

    def test_white_pawn_e2_to_e4_is_generated(self):
        board = Board.from_fen()
        moves = self.gen.generate_legal_moves(board, Square(6, 4))

        assert {move.to_sq.to_algebraic() for move in moves} == {"e3", "e4"}

    def test_black_pawn_e7_to_e5_is_generated(self):
        board = Board.from_fen(
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        )
        moves = self.gen.generate_legal_moves(board, Square(1, 4))

        assert {move.to_sq.to_algebraic() for move in moves} == {"e5", "e6"}

    def test_pawn_diagonal_capture(self):
        board = Board.from_fen("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(4, 4))

        capture = next(move for move in moves if move.to_sq == Square(3, 3))
        assert capture.captured == Piece("pawn", "black")

    def test_pawn_promotion_generation(self):
        board = Board.from_fen("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(1, 0))

        assert {move.promotion for move in moves} == {
            "queen",
            "rook",
            "bishop",
            "knight",
        }
        assert all(move.to_sq == Square(0, 0) for move in moves)

        promoted = board.make_move(
            next(move for move in moves if move.promotion == "queen")
        )
        assert promoted.grid[0][0] == Piece("queen", "white")

    def test_knight_moves_from_starting_position(self):
        board = Board.from_fen()

        b1_moves = self.gen.generate_legal_moves(board, Square(7, 1))
        g1_moves = self.gen.generate_legal_moves(board, Square(7, 6))

        assert {move.to_sq.to_algebraic() for move in b1_moves} == {"a3", "c3"}
        assert {move.to_sq.to_algebraic() for move in g1_moves} == {"f3", "h3"}

    @pytest.mark.parametrize(
        ("square", "piece_type"),
        [
            (Square(7, 0), "rook"),
            (Square(7, 2), "bishop"),
            (Square(7, 3), "queen"),
        ],
    )
    def test_sliding_pieces_blocked_at_start(self, square, piece_type):
        board = Board.from_fen()

        assert board.get_piece(square).piece_type == piece_type
        assert self.gen.generate_legal_moves(board, square) == []

    @pytest.mark.parametrize(
        ("fen", "square", "expected_count"),
        [
            ("k7/8/8/8/3B4/8/8/7K w - - 0 1", Square(4, 3), 13),
            ("k7/8/8/8/3R4/8/8/7K w - - 0 1", Square(4, 3), 14),
            ("k7/8/8/8/3Q4/8/8/7K w - - 0 1", Square(4, 3), 27),
            ("k7/8/8/8/3K4/8/8/8 w - - 0 1", Square(4, 3), 8),
        ],
    )
    def test_open_board_piece_movement(self, fen, square, expected_count):
        board = Board.from_fen(fen)

        moves = self.gen.generate_legal_moves(board, square)

        assert len(moves) == expected_count

    def test_no_moves_empty_board(self):
        """Bàn cờ chỉ có vua → ít nước đi."""
        fen = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
        board = Board.from_fen(fen)
        moves = self.gen.generate_legal_moves(board)
        assert len(moves) > 0  # Vua luôn có nước đi


# ==============================================================
# Test Chess Legality
# ==============================================================

class TestChessLegality:
    """Kiểm tra attack map, self-check, checkmate và stalemate."""

    def setup_method(self):
        self.gen = MoveGenerator()

    @pytest.mark.parametrize(
        "fen",
        [
            "4r2k/8/8/8/8/8/8/4K3 w - - 0 1",  # rook
            "7k/8/8/8/1b6/8/8/4K3 w - - 0 1",  # bishop
            "4q2k/8/8/8/8/8/8/4K3 w - - 0 1",  # queen
            "7k/8/8/8/8/5n2/8/4K3 w - - 0 1",  # knight
            "7k/8/8/8/8/8/3p4/4K3 w - - 0 1",  # pawn
            "8/8/8/8/8/8/4k3/4K3 w - - 0 1",   # adjacent king
        ],
    )
    def test_white_king_is_in_check_by_each_piece_type(self, fen):
        board = Board.from_fen(fen)

        assert self.gen.is_in_check(board, "white")
        assert self.gen.is_square_attacked(
            board,
            board.find_king("white"),
            "black",
        )

    def test_legal_moves_never_capture_opponent_king(self):
        board = Board.from_fen("4k3/8/8/8/8/8/4R3/K7 w - - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(6, 4))

        assert Square(0, 4) not in [move.to_sq for move in moves]
        assert all(
            move.captured is None or move.captured.piece_type != "king"
            for move in moves
        )

    def test_pinned_piece_cannot_expose_king(self):
        board = Board.from_fen("k3r3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(6, 4))

        assert moves
        assert all(move.to_sq.col == 4 for move in moves)
        assert Square(6, 3) not in [move.to_sq for move in moves]

    def test_king_cannot_move_into_check(self):
        board = Board.from_fen("4r2k/8/8/8/8/8/8/4K3 w - - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(7, 4))

        assert Square(6, 4) not in [move.to_sq for move in moves]

    def test_side_in_check_only_has_moves_that_resolve_check(self):
        board = Board.from_fen("4r2k/8/8/8/8/8/R7/4K3 w - - 0 1")
        moves = self.gen.generate_legal_moves(board)

        assert moves
        assert all(
            not self.gen.is_in_check(board.make_move(move), "white")
            for move in moves
        )
        assert any(
            move.from_sq == Square.from_algebraic("a2")
            and move.to_sq == Square.from_algebraic("e2")
            for move in moves
        )
        assert not any(
            move.from_sq == Square.from_algebraic("a2")
            and move.to_sq == Square.from_algebraic("a3")
            for move in moves
        )

    def test_simple_checkmate_position(self):
        board = Board.from_fen("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1")

        assert self.gen.is_in_check(board, "black")
        assert self.gen.is_checkmate(board)
        assert self.gen.get_game_status(board) == "checkmate"
        assert self.gen.generate_legal_moves(board) == []

    def test_simple_stalemate_position(self):
        board = Board.from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")

        assert not self.gen.is_in_check(board, "black")
        assert self.gen.is_stalemate(board)
        assert self.gen.get_game_status(board) == "stalemate"
        assert self.gen.generate_legal_moves(board) == []

    def test_game_status_check_and_playing(self):
        checked = Board.from_fen("4r2k/8/8/8/8/8/8/4K3 w - - 0 1")
        playing = Board.from_fen()

        assert self.gen.get_game_status(checked) == "check"
        assert self.gen.get_game_status(playing) == "playing"


# ==============================================================
# Test Draw Rules
# ==============================================================

class TestDrawRules:
    def setup_method(self):
        self.gen = MoveGenerator()

    def test_fifty_move_rule_draw_at_one_hundred_halfmoves(self):
        board = Board.from_fen(
            "4k3/8/8/8/8/8/8/R3K3 w - - 100 51"
        )

        assert self.gen.get_game_status(board) == "draw"

    def test_pawn_move_resets_halfmove_clock(self):
        board = Board.from_fen(
            "4k3/8/8/8/8/8/4P3/4K3 w - - 99 50"
        )

        result = board.make_move(
            Move(
                Square.from_algebraic("e2"),
                Square.from_algebraic("e3"),
            )
        )

        assert result.half_move_clock == 0

    def test_capture_resets_halfmove_clock(self):
        board = Board.from_fen(
            "4k3/8/8/8/8/8/n7/R3K3 w - - 99 50"
        )

        result = board.make_move(
            Move(
                Square.from_algebraic("a1"),
                Square.from_algebraic("a2"),
            )
        )

        assert result.half_move_clock == 0

    def test_quiet_non_pawn_move_increments_halfmove_clock(self):
        board = Board.from_fen(
            "4k3/8/8/8/8/8/8/1N2K3 w - - 41 21"
        )

        result = board.make_move(
            Move(
                Square.from_algebraic("b1"),
                Square.from_algebraic("c3"),
            )
        )

        assert result.half_move_clock == 42

    @pytest.mark.parametrize(
        "fen",
        [
            "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
            "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1",
            "4k3/8/8/8/8/8/8/1N2K3 w - - 0 1",
            "4kb2/8/8/8/8/8/8/2B1K3 w - - 0 1",
        ],
    )
    def test_insufficient_material_is_draw(self, fen):
        board = Board.from_fen(fen)

        assert self.gen.is_insufficient_material(board)
        assert self.gen.get_game_status(board) == "draw"

    def test_opposite_color_bishops_are_not_automatically_insufficient(self):
        board = Board.from_fen(
            "4k1b1/8/8/8/8/8/8/2B1K3 w - - 0 1"
        )

        assert not self.gen.is_insufficient_material(board)
        assert self.gen.get_game_status(board) == "playing"


# ==============================================================
# Test Castling
# ==============================================================

class TestCastling:
    def setup_method(self):
        self.gen = MoveGenerator()

    @pytest.mark.parametrize(
        ("fen", "destination", "king_square", "rook_square", "color"),
        [
            (
                "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
                "g1",
                "g1",
                "f1",
                "white",
            ),
            (
                "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
                "c1",
                "c1",
                "d1",
                "white",
            ),
            (
                "r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1",
                "g8",
                "g8",
                "f8",
                "black",
            ),
            (
                "r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1",
                "c8",
                "c8",
                "d8",
                "black",
            ),
        ],
    )
    def test_castling_generated_and_executed(
        self,
        fen,
        destination,
        king_square,
        rook_square,
        color,
    ):
        board = Board.from_fen(fen)
        king_from = board.find_king(color)
        moves = self.gen.generate_legal_moves(board, king_from)
        castle = next(
            move for move in moves
            if move.to_sq == Square.from_algebraic(destination)
        )

        result = board.make_move(castle)

        assert result.get_piece(Square.from_algebraic(king_square)) == Piece(
            "king",
            color,
        )
        assert result.get_piece(Square.from_algebraic(rook_square)) == Piece(
            "rook",
            color,
        )
        assert result.get_piece(king_from) is None

    def test_castling_not_allowed_after_king_moves(self):
        board = Board.from_fen("4k3/8/8/8/8/8/8/4K2R w K - 0 1")
        board = board.make_move(Move(Square(7, 4), Square(7, 5)))
        board = board.make_move(Move(Square(0, 4), Square(0, 5)))
        board = board.make_move(Move(Square(7, 5), Square(7, 4)))

        moves = self.gen.generate_legal_moves(board, Square(7, 4))

        assert not board.castling.white_king_side
        assert Square(7, 6) not in [move.to_sq for move in moves]

    def test_castling_not_allowed_after_rook_moves(self):
        board = Board.from_fen("4k3/8/8/8/8/8/8/4K2R w K - 0 1")
        board = board.make_move(Move(Square(7, 7), Square(6, 7)))
        board = board.make_move(Move(Square(0, 4), Square(0, 5)))
        board = board.make_move(Move(Square(6, 7), Square(7, 7)))

        moves = self.gen.generate_legal_moves(board, Square(7, 4))

        assert not board.castling.white_king_side
        assert Square(7, 6) not in [move.to_sq for move in moves]

    def test_castling_not_allowed_while_in_check(self):
        board = Board.from_fen("4r2k/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(7, 4))

        destinations = {move.to_sq.to_algebraic() for move in moves}
        assert "g1" not in destinations
        assert "c1" not in destinations

    def test_castling_not_allowed_through_attacked_square(self):
        board = Board.from_fen("k4r2/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(7, 4))

        destinations = {move.to_sq.to_algebraic() for move in moves}
        assert "g1" not in destinations
        assert "c1" in destinations

    def test_castling_not_allowed_into_attacked_square(self):
        board = Board.from_fen("k5r1/8/8/8/8/8/8/R3K2R w KQ - 0 1")
        moves = self.gen.generate_legal_moves(board, Square(7, 4))

        destinations = {move.to_sq.to_algebraic() for move in moves}
        assert "g1" not in destinations
        assert "c1" in destinations

    def test_castling_rights_update_after_rook_capture(self):
        board = Board.from_fen("4k3/8/8/8/8/8/6b1/R3K2R b KQ - 0 1")
        result = board.make_move(Move(Square(6, 6), Square(7, 7)))

        assert not result.castling.white_king_side
        assert result.castling.white_queen_side
        assert result.to_fen().split()[2] == "Q"


# ==============================================================
# Test En Passant
# ==============================================================

class TestEnPassant:
    def setup_method(self):
        self.gen = MoveGenerator()

    @staticmethod
    def _position_after_e2_e4() -> Board:
        board = Board.from_fen("4k3/8/8/8/3p4/8/4P3/4K3 w - - 0 1")
        return board.make_move(Move(Square(6, 4), Square(4, 4)))

    def test_en_passant_target_after_two_square_pawn_move(self):
        board = self._position_after_e2_e4()

        assert board.en_passant == Square.from_algebraic("e3")
        assert board.to_fen().split()[3] == "e3"

    def test_en_passant_capture_is_generated(self):
        board = self._position_after_e2_e4()
        moves = self.gen.generate_legal_moves(
            board,
            Square.from_algebraic("d4"),
        )

        capture = next(
            move for move in moves
            if move.to_sq == Square.from_algebraic("e3")
        )
        assert capture.captured == Piece("pawn", "white")

    def test_en_passant_capture_removes_correct_pawn(self):
        board = self._position_after_e2_e4()
        move = next(
            move
            for move in self.gen.generate_legal_moves(
                board,
                Square.from_algebraic("d4"),
            )
            if move.to_sq == Square.from_algebraic("e3")
        )

        result = board.make_move(move)

        assert result.get_piece(Square.from_algebraic("e3")) == Piece(
            "pawn",
            "black",
        )
        assert result.get_piece(Square.from_algebraic("e4")) is None
        assert result.get_piece(Square.from_algebraic("d4")) is None
        assert result.en_passant is None

    def test_en_passant_expires_after_one_move(self):
        board = self._position_after_e2_e4()
        board = board.make_move(Move(Square(0, 4), Square(1, 4)))

        assert board.en_passant is None

    def test_en_passant_illegal_if_it_exposes_own_king(self):
        board = Board.from_fen(
            "k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"
        )
        moves = self.gen.generate_legal_moves(
            board,
            Square.from_algebraic("e5"),
        )

        assert Square.from_algebraic("d6") not in [
            move.to_sq for move in moves
        ]


# ==============================================================
# Test AI Agents
# ==============================================================

class TestAgents:
    """Test cơ bản cho các AI agent."""

    def test_greedy_agent_returns_legal_move(self):
        """GreedyAgent phải trả về một nước đi."""
        from ai_core.agents import GreedyAgent

        agent = GreedyAgent()
        board = Board.from_fen()
        move = agent.get_move(board)

        assert move is not None
        assert isinstance(move, Move)
        assert move in MoveGenerator().generate_legal_moves(board)

    def test_minimax_agent_returns_legal_move(self):
        """MinimaxAgent phải trả về một nước đi."""
        from ai_core.agents import MinimaxAgent

        agent = MinimaxAgent(depth=2)
        board = Board.from_fen()
        move = agent.get_move(board)

        assert move is not None
        assert isinstance(move, Move)
        assert move in MoveGenerator().generate_legal_moves(board)

    def test_mcts_agent_returns_legal_move(self):
        """MCTSAgent phải trả về một nước đi."""
        from ai_core.agents import MCTSAgent

        agent = MCTSAgent(simulations=5)
        board = Board.from_fen()
        move = agent.get_move(board)

        assert move is not None
        assert isinstance(move, Move)
        assert move in MoveGenerator().generate_legal_moves(board)

    def test_mcts_terminal_score_uses_root_player_perspective(self):
        from ai_core.agents import MCTSAgent

        agent = MCTSAgent(simulations=1)
        black_wins = Board.from_fen(
            "7K/6q1/5k2/8/8/8/8/8 w - - 0 1"
        )

        black_result, black_depth = agent._simulate(
            black_wins,
            root_player="black",
        )
        white_result, white_depth = agent._simulate(
            black_wins,
            root_player="white",
        )

        assert black_result == 1.0
        assert white_result == 0.0
        assert black_depth == white_depth == 0

    def test_mcts_prefers_mate_in_one_with_one_simulation(self):
        from ai_core.agents import MCTSAgent

        generator = MoveGenerator()
        board = Board.from_fen("7k/8/5KQ1/8/8/8/8/8 w - - 0 1")
        agent = MCTSAgent(simulations=1)

        move = agent.get_move(board)

        assert move in generator.generate_legal_moves(board)
        assert generator.get_game_status(board.make_move(move)) == "checkmate"
        assert math.isfinite(agent.get_stats().evaluation_score)
        assert agent.get_stats().evaluation_score > 900_000

    def test_minimax_finds_mate_in_one(self):
        from ai_core.agents import MinimaxAgent

        generator = MoveGenerator()
        board = Board.from_fen("7k/8/5KQ1/8/8/8/8/8 w - - 0 1")
        agent = MinimaxAgent(depth=2)

        move = agent.get_move(board)

        assert move in generator.generate_legal_moves(board)
        assert generator.get_game_status(board.make_move(move)) == "checkmate"
        assert math.isfinite(agent.get_stats().evaluation_score)
        assert agent.get_stats().evaluation_score > 900_000

    def test_shared_evaluation_uses_white_positive_convention(self):
        from ai_core.agents import GreedyAgent

        agent = GreedyAgent()
        white_advantage = Board.from_fen(
            "4k3/8/8/8/8/8/8/Q3K3 w - - 0 1"
        )
        black_advantage = Board.from_fen(
            "q3k3/8/8/8/8/8/8/4K3 w - - 0 1"
        )

        assert agent.evaluate(white_advantage) > 0
        assert agent.evaluate(black_advantage) < 0

    def test_greedy_prefers_free_queen_capture(self):
        from ai_core.agents import GreedyAgent

        board = Board.from_fen("4k3/8/8/8/8/8/q7/R3K3 w Q - 0 1")
        agent = GreedyAgent()

        move = agent.get_move(board)

        assert move.from_sq == Square.from_algebraic("a1")
        assert move.to_sq == Square.from_algebraic("a2")
        assert move.captured == Piece("queen", "black")

    def test_minimax_does_not_play_self_check_move(self):
        from ai_core.agents import MinimaxAgent

        generator = MoveGenerator()
        board = Board.from_fen("k3r3/8/8/8/8/8/4R3/4K3 w - - 0 1")
        agent = MinimaxAgent(depth=2)

        move = agent.get_move(board)

        assert move in generator.generate_legal_moves(board)
        result = board.make_move(move)
        assert not generator.is_in_check(result, "white")
        if move.from_sq == Square.from_algebraic("e2"):
            assert move.to_sq.col == Square.from_algebraic("e2").col

    def test_minimax_avoids_allowing_immediate_checkmate(self):
        from ai_core.agents import MinimaxAgent

        generator = MoveGenerator()
        board = Board.from_fen(
            "4k3/8/2b5/8/8/7q/5P1P/R5K1 w - - 0 1"
        )

        blunder = next(
            move
            for move in generator.generate_legal_moves(board)
            if move.to_uci() == "a1b1"
        )
        blunder_board = board.make_move(blunder)
        assert any(
            generator.get_game_status(blunder_board.make_move(reply))
            == "checkmate"
            for reply in generator.generate_legal_moves(blunder_board)
        )

        agent = MinimaxAgent(depth=2)
        move = agent.get_move(board)
        result = board.make_move(move)

        assert move in generator.generate_legal_moves(board)
        assert not any(
            generator.get_game_status(result.make_move(reply)) == "checkmate"
            for reply in generator.generate_legal_moves(result)
        )

    @pytest.mark.parametrize(
        "agent_name",
        ["greedy", "minimax", "mcts"],
    )
    def test_agents_stop_on_insufficient_material_draw(self, agent_name):
        from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent

        factories = {
            "greedy": lambda: GreedyAgent(),
            "minimax": lambda: MinimaxAgent(depth=2),
            "mcts": lambda: MCTSAgent(simulations=2),
        }
        agent = factories[agent_name]()
        board = Board.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")

        assert agent.get_move(board) is None
        assert agent.get_stats().evaluation_score == 0.0
        assert math.isfinite(agent.get_stats().evaluation_score)

    @pytest.mark.parametrize(
        ("agent_name", "search_size"),
        [
            ("greedy", None),
            ("minimax", 1),
            ("mcts", 2),
        ],
    )
    def test_agent_search_stats_are_finite(self, agent_name, search_size):
        from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent

        factories = {
            "greedy": lambda: GreedyAgent(),
            "minimax": lambda: MinimaxAgent(depth=search_size),
            "mcts": lambda: MCTSAgent(simulations=search_size),
        }
        agent = factories[agent_name]()
        move = agent.get_move(Board.from_fen())
        stats = agent.get_stats()

        assert move is not None
        assert stats.algorithm == agent_name
        assert math.isfinite(stats.evaluation_score)
        assert stats.nodes_evaluated > 0

    def test_agent_stats(self):
        """Agent phải trả về stats sau khi suy nghĩ."""
        from ai_core.agents import GreedyAgent

        agent = GreedyAgent()
        stats = agent.get_stats()

        assert isinstance(stats, BenchmarkStats)
        assert stats.algorithm == "greedy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
