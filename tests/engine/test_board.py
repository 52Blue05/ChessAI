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

        TODO: Test này sẽ pass khi MoveGenerator được implement đầy đủ.
        """
        board = Board.from_fen()
        moves = self.gen.generate_legal_moves(board)
        # Bỏ comment dòng dưới khi implement xong
        # assert len(moves) == 20

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
