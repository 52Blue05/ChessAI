"""
tests/engine/test_board.py
Unit tests cho Board (engine) và AI agents.

Chạy: pytest tests/ -v
"""

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
# Test AI Agents
# ==============================================================

class TestAgents:
    """Test cơ bản cho các AI agent."""

    def test_greedy_agent_returns_move(self):
        """GreedyAgent phải trả về một nước đi."""
        from ai_core.agents import GreedyAgent

        agent = GreedyAgent()
        board = Board.from_fen()
        move = agent.get_move(board)

        # TODO: Uncomment khi MoveGenerator hoàn thiện
        # assert move is not None
        # assert isinstance(move, Move)

    def test_minimax_agent_returns_move(self):
        """MinimaxAgent phải trả về một nước đi."""
        from ai_core.agents import MinimaxAgent

        agent = MinimaxAgent(depth=2)
        board = Board.from_fen()
        move = agent.get_move(board)

        # TODO: Uncomment khi MoveGenerator hoàn thiện
        # assert move is not None

    def test_mcts_agent_returns_move(self):
        """MCTSAgent phải trả về một nước đi."""
        from ai_core.agents import MCTSAgent

        agent = MCTSAgent(simulations=100)
        board = Board.from_fen()
        move = agent.get_move(board)

        # TODO: Uncomment khi MoveGenerator hoàn thiện
        # assert move is not None

    def test_agent_stats(self):
        """Agent phải trả về stats sau khi suy nghĩ."""
        from ai_core.agents import GreedyAgent

        agent = GreedyAgent()
        stats = agent.get_stats()

        assert isinstance(stats, BenchmarkStats)
        assert stats.algorithm == "greedy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
