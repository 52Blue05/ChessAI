"""
ai_core/agents/mcts_agent.py
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
    UNVISITED_SCORE = 1_000_000.0

    def ucb1(
        self,
        exploration_constant: float = 1.414,
        maximize_root: bool = True,
    ) -> float:
        """
        Tính giá trị UCB1 (Upper Confidence Bound).

        UCB1 = Wi/Ni + C * sqrt(ln(N) / Ni)
        """
        if self.visits == 0:
            return self.UNVISITED_SCORE

        root_value = self.wins / self.visits
        exploitation = root_value if maximize_root else 1.0 - root_value
        exploration = exploration_constant * math.sqrt(
            math.log(max(1, self.parent.visits)) / self.visits
        )
        return exploitation + exploration

    def is_fully_expanded(self) -> bool:
        """Kiểm tra đã mở rộng hết chưa."""
        return len(self.untried_moves) == 0

    def is_terminal(self) -> bool:
        """Kiểm tra node lá (game over)."""
        return len(self.children) == 0 and self.is_fully_expanded()

    def best_child(
        self,
        exploration_constant: float = 1.414,
        maximize_root: bool = True,
    ) -> "MCTSNode":
        """Chọn node con tốt nhất theo UCB1."""
        return max(
            self.children,
            key=lambda child: child.ucb1(
                exploration_constant,
                maximize_root,
            ),
        )

    def best_move_child(self) -> "MCTSNode":
        """Chọn node con có nhiều visits nhất (robust child)."""
        return max(self.children, key=lambda c: c.visits)


class MCTSAgent(Agent):
    """
    AI Monte Carlo Tree Search.

    Usage:
        agent = MCTSAgent(simulations=100)
        move = agent.get_move(board)
        stats = agent.get_stats()
    """

    def __init__(self, simulations: int = 100, exploration_constant: float = 1.414):
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
        root_player = board.current_player

        # Tạo root node
        root = MCTSNode(board=board.copy())
        root.untried_moves = self.move_generator.generate_legal_moves(board)

        current_terminal = self.terminal_score(board, root.untried_moves)
        if current_terminal is not None:
            self._last_stats.evaluation_score = float(current_terminal)
            return None

        if not root.untried_moves:
            return None

        mate_move = self.find_mate_in_one(board, root.untried_moves)
        if mate_move is not None:
            mate_board = board.make_move(mate_move)
            self._last_stats.nodes_evaluated = 1
            self._last_stats.depth_reached = 1
            self._last_stats.evaluation_score = float(
                self.terminal_score(mate_board, [], ply=1)
            )
            return mate_move

        # Chạy simulations
        for i in range(self.simulations):
            self._last_stats.nodes_evaluated += 1

            # 1. Selection
            node = self._select(root, root_player)

            # 2. Expansion
            if not node.is_fully_expanded():
                node = self._expand(node)

            # 3. Simulation (Rollout)
            result, rollout_depth = self._simulate(
                node.board,
                root_player,
            )
            self._last_stats.depth_reached = max(
                self._last_stats.depth_reached,
                rollout_depth,
            )

            # 4. Backpropagation
            self._backpropagate(node, result)

        # Chọn nước đi tốt nhất (robust child)
        if not root.children:
            return root.untried_moves[0] if root.untried_moves else None

        best_child = root.best_move_child()
        terminal = self.terminal_score(best_child.board)
        self._last_stats.evaluation_score = float(
            terminal
            if terminal is not None
            else self.evaluate(best_child.board)
        )

        return best_child.move

    # ------------------------------------------------------------------
    # MCTS phases
    # ------------------------------------------------------------------

    def _select(self, node: MCTSNode, root_player: str) -> MCTSNode:
        """
        Phase 1 — Selection.
        Đi xuống cây theo UCB1 cho đến khi gặp node chưa mở rộng hết
        hoặc node lá.
        """
        while node.is_fully_expanded() and node.children:
            node = node.best_child(
                self.exploration_constant,
                maximize_root=node.board.current_player == root_player,
            )
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Phase 2 — Expansion.
        Chọn 1 nước đi chưa thử, tạo node con mới.
        """
        move = max(
            node.untried_moves,
            key=lambda candidate: self.move_order_score(node.board, candidate),
        )
        node.untried_moves.remove(move)
        new_board = node.board.make_move(move)

        child = MCTSNode(
            board=new_board,
            parent=node,
            move=move,
        )
        child.untried_moves = self.move_generator.generate_legal_moves(new_board)

        node.children.append(child)
        return child

    def _simulate(
        self,
        board: Board,
        root_player: str,
        max_moves: int = 3,
    ) -> tuple[float, int]:
        """
        Phase 3 — Simulation (Rollout).
        Chơi ngẫu nhiên cho đến khi game over hoặc đạt max_moves.

        Returns:
            1.0 = root player thắng
            0.0 = root player thua
            0.5 = hòa
        """
        sim_board = board.copy()

        for ply in range(max_moves):
            moves = self.move_generator.generate_legal_moves(sim_board)
            terminal = self.terminal_score(sim_board, moves, ply)
            if terminal is not None:
                if terminal == 0:
                    return 0.5, ply
                white_wins = terminal > 0
                root_wins = (
                    white_wins
                    if root_player == "white"
                    else not white_wins
                )
                return (1.0 if root_wins else 0.0), ply

            move = self._choose_rollout_move(sim_board, moves)
            sim_board = sim_board.make_move(move)

        score = max(-2_000.0, min(2_000.0, self.evaluate(sim_board)))
        white_probability = 1.0 / (1.0 + math.exp(-score / 600.0))
        root_probability = (
            white_probability
            if root_player == "white"
            else 1.0 - white_probability
        )
        return root_probability, max_moves

    def _choose_rollout_move(self, board: Board, moves: list[Move]) -> Move:
        """Ưu tiên mate, promotion, capture, check, rồi mới ngẫu nhiên."""
        mate_move, checking_moves = self.find_mate_and_checking_moves(
            board,
            moves,
        )
        if mate_move is not None:
            return mate_move

        promotions = [move for move in moves if move.promotion]
        if promotions:
            return max(
                promotions,
                key=lambda move: self.move_order_score(board, move),
            )

        captures = [move for move in moves if move.captured is not None]
        if captures:
            return max(
                captures,
                key=lambda move: self.move_order_score(board, move),
            )

        if checking_moves:
            return random.choice(checking_moves)
        return random.choice(moves)

    def _backpropagate(self, node: MCTSNode, result: float) -> None:
        """
        Phase 4 — Backpropagation.
        Cập nhật wins/visits ngược lên root.
        """
        while node is not None:
            node.visits += 1
            node.wins += result
            node = node.parent
