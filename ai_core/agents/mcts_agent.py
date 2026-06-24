"""
ai-core/agents/mcts_agent.py
Monte Carlo Tree Search (MCTS) — Tìm kiếm cây Monte Carlo.

Vai trò: Thuật toán hiện đại dựa trên xác suất thống kê.

Cơ chế hoạt động:
    1. Selection: Chọn node theo công thức UCB1
    2. Expansion: Mở rộng node lá
    3. Simulation (Rollout): Mô phỏng ván đấu ngẫu nhiên
    4. Backpropagation: Cập nhật thống kê ngược lên gốc

Công thức UCB1:
    UCB1 = Wi/Ni + C * sqrt(ln(N) / Ni)
    - Wi: số lần thắng
    - Ni: số lần visit node con
    - N: số lần visit node cha
    - C: hằng số exploration (thường = sqrt(2))

Đặc điểm:
    ✅ Không cần hàm lượng giá chi tiết, tư duy toàn cục
    ❌ Cần nhiều simulations, kết quả phụ thuộc vào số lần mô phỏng
"""

from __future__ import annotations
import math
import random
from typing import Optional, List
from dataclasses import dataclass, field
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.board import Board, Move
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkStats
from .agent import Agent


@dataclass
class MCTSNode:
    """
    Node trong cây MCTS.

    Attributes:
        board: Trạng thái bàn cờ tại node này.
        parent: Node cha.
        move: Nước đi từ cha đến node này.
        children: Danh sách node con.
        wins: Số lần thắng.
        visits: Số lần visit.
        untried_moves: Nước đi chưa được thử.
    """
    board: Board
    parent: Optional["MCTSNode"] = None
    move: Optional[Move] = None
    children: list = field(default_factory=list)
    wins: float = 0.0
    visits: int = 0
    untried_moves: list = field(default_factory=list)

    def ucb1(self, exploration_constant: float = 1.414) -> float:
        """
        Tính giá trị UCB1 (Upper Confidence Bound).

        UCB1 = Wi/Ni + C * sqrt(ln(N) / Ni)
        """
        if self.visits == 0:
            return float("inf")

        exploitation = self.wins / self.visits
        exploration = exploration_constant * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploitation + exploration

    def is_fully_expanded(self) -> bool:
        """Kiểm tra đã mở rộng hết chưa."""
        return len(self.untried_moves) == 0

    def is_terminal(self) -> bool:
        """Kiểm tra node lá (game over)."""
        return len(self.children) == 0 and self.is_fully_expanded()

    def best_child(self, exploration_constant: float = 1.414) -> "MCTSNode":
        """Chọn node con tốt nhất theo UCB1."""
        return max(self.children, key=lambda c: c.ucb1(exploration_constant))

    def best_move_child(self) -> "MCTSNode":
        """Chọn node con có nhiều visits nhất (robust child)."""
        return max(self.children, key=lambda c: c.visits)


class MCTSAgent(Agent):
    """
    AI Monte Carlo Tree Search.

    Usage:
        agent = MCTSAgent(simulations=1000)
        move = agent.get_move(board)
        stats = agent.get_stats()
    """

    def __init__(self, simulations: int = 1000, exploration_constant: float = 1.414):
        super().__init__(name="mcts")
        self.simulations = simulations
        self.exploration_constant = exploration_constant
        self.move_generator = MoveGenerator()

    def set_simulations(self, simulations: int) -> None:
        """Cài đặt số lượng simulations."""
        self.simulations = simulations

    def get_move(self, board: Board) -> Optional[Move]:
        """
        Tìm nước đi tốt nhất bằng MCTS.

        Quy trình:
        1. Tạo root node từ trạng thái hiện tại
        2. Lặp `simulations` lần:
           a. Selection: Chọn node theo UCB1
           b. Expansion: Mở rộng node
           c. Simulation: Rollout ngẫu nhiên
           d. Backpropagation: Cập nhật thống kê
        3. Chọn nước đi từ node con có nhiều visits nhất
        """
        self._reset_stats()

        # Tạo root node
        root = MCTSNode(board=board.copy())
        root.untried_moves = self.move_generator.generate_legal_moves(board)

        if not root.untried_moves:
            return None

        # Chạy simulations
        for i in range(self.simulations):
            self._last_stats.nodes_evaluated += 1

            # 1. Selection
            node = self._select(root)

            # 2. Expansion
            if not node.is_fully_expanded():
                node = self._expand(node)

            # 3. Simulation (Rollout)
            result = self._simulate(node.board)

            # 4. Backpropagation
            self._backpropagate(node, result)

        # Chọn nước đi tốt nhất (robust child)
        if not root.children:
            return root.untried_moves[0] if root.untried_moves else None

        best_child = root.best_move_child()
        self._last_stats.depth_reached = self.simulations
        self._last_stats.evaluation_score = (
            best_child.wins / best_child.visits if best_child.visits > 0 else 0
        )

        return best_child.move

    # ------------------------------------------------------------------
    # MCTS phases
    # ------------------------------------------------------------------

    def _select(self, node: MCTSNode) -> MCTSNode:
        """
        Phase 1 — Selection.
        Đi xuống cây theo UCB1 cho đến khi gặp node chưa mở rộng hết
        hoặc node lá.
        """
        while node.is_fully_expanded() and node.children:
            node = node.best_child(self.exploration_constant)
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Phase 2 — Expansion.
        Chọn 1 nước đi chưa thử, tạo node con mới.
        """
        move = node.untried_moves.pop(random.randrange(len(node.untried_moves)))
        new_board = node.board.make_move(move)

        child = MCTSNode(
            board=new_board,
            parent=node,
            move=move,
        )
        child.untried_moves = self.move_generator.generate_legal_moves(new_board)

        node.children.append(child)
        return child

    def _simulate(self, board: Board, max_moves: int = 100) -> float:
        """
        Phase 3 — Simulation (Rollout).
        Chơi ngẫu nhiên cho đến khi game over hoặc đạt max_moves.

        Returns:
            1.0 = trắng thắng
            0.0 = đen thắng
            0.5 = hòa
        """
        sim_board = board.copy()

        for _ in range(max_moves):
            # Kiểm tra game over
            status = self.move_generator.get_game_status(sim_board)
            if status == "checkmate":
                # Bên đang đi bị chiếu hết → bên kia thắng
                return 0.0 if sim_board.current_player == "white" else 1.0
            if status in ["stalemate", "draw"]:
                return 0.5

            # Chọn nước đi ngẫu nhiên
            moves = self.move_generator.generate_legal_moves(sim_board)
            if not moves:
                return 0.5

            move = random.choice(moves)
            sim_board = sim_board.make_move(move)

        # Hết max_moves → đánh giá bằng material
        return self._evaluate_material(sim_board)

    def _backpropagate(self, node: MCTSNode, result: float) -> None:
        """
        Phase 4 — Backpropagation.
        Cập nhật wins/visits ngược lên root.
        """
        while node is not None:
            node.visits += 1
            # Đổi kết quả theo perspective của node
            if node.board.current_player == "black":
                # Node đã thực hiện nước đi của trắng → kết quả cho trắng
                node.wins += result
            else:
                # Node đã thực hiện nước đi của đen → kết quả cho đen
                node.wins += (1.0 - result)
            node = node.parent

    def _evaluate_material(self, board: Board) -> float:
        """Đánh giá vật chất đơn giản cho rollout."""
        piece_values = {
            "pawn": 1, "knight": 3, "bishop": 3,
            "rook": 5, "queen": 9, "king": 0,
        }
        white_score = 0
        black_score = 0

        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece:
                    val = piece_values.get(piece.piece_type, 0)
                    if piece.color == "white":
                        white_score += val
                    else:
                        black_score += val

        total = white_score + black_score
        if total == 0:
            return 0.5
        return white_score / total

    def evaluate(self, board: Board) -> float:
        """Hàm lượng giá (MCTS không thực sự cần, dùng cho interface)."""
        return self._evaluate_material(board)
