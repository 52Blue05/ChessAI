"""
gui/game_screen.py
Màn hình chơi cờ — Human vs AI và AI vs AI.
"""

import pygame
import time
import threading
from gui.constants import *
from gui.widgets import Button, Panel, draw_text
from gui.board_renderer import BoardRenderer
from backend.engine.board import Board, Square, Move
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkLogger
from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent


ACTIVE_GAME_STATUSES = {"playing", "check"}


class GameScreen:
    """
    Màn hình chơi cờ.

    mode:
        "human_vs_ai" — Người (trắng) vs AI (đen)
        "ai_vs_ai"    — AI vs AI (xem tự động)
    """

    def __init__(self, mode="human_vs_ai"):
        self.mode = mode
        self.board = Board.from_fen()
        self.move_gen = MoveGenerator()
        self.board_renderer = BoardRenderer()
        self.logger = BenchmarkLogger()

        # AI Agents
        self.agents = {
            "greedy": GreedyAgent(),
            "minimax": MinimaxAgent(depth=2),
            "mcts": MCTSAgent(simulations=100),
        }

        # Settings
        self.white_algo = "minimax"  # For AI vs AI mode
        self.black_algo = "mcts"    # For both modes
        self.selected_algo = "minimax"  # For Human vs AI mode (AI side)

        # State
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.stats = None
        self.game_status = "playing"
        self.is_thinking = False
        self.status_text = ""
        self.move_history = []

        # UI elements
        self._build_ui()

        # For AI vs AI auto-play
        self.ai_delay = 0.3  # seconds between moves
        self._last_ai_time = 0
        self.result = None  # "back_to_menu"

    def _build_ui(self):
        """Xây dựng các elements UI."""
        panel_x = BOARD_OFFSET_X + BOARD_SIZE + 30
        panel_y = BOARD_OFFSET_Y
        panel_w = WINDOW_WIDTH - panel_x - 30

        self.panel = Panel(panel_x, panel_y, panel_w, BOARD_SIZE, "⚙ Điều khiển")

        bx = panel_x + 16
        bw = panel_w - 32

        # Algorithm buttons (for selecting AI)
        self.algo_buttons = {}
        algo_names = ["greedy", "minimax", "mcts"]
        for i, name in enumerate(algo_names):
            btn = Button(bx, panel_y + 50 + i * 44, bw, 36,
                         ALGO_LABELS[name],
                         color=COLOR_SURFACE_HOVER,
                         border_radius=6)
            self.algo_buttons[name] = btn

        # Action buttons
        btn_y_base = panel_y + 200

        self.btn_ai_move = Button(bx, btn_y_base, bw, 42,
                                   "🤖 AI đi", color=COLOR_PRIMARY)
        self.btn_new_game = Button(bx, btn_y_base + 52, bw, 38,
                                    "🔄 Ván mới", color=COLOR_SURFACE_HOVER)
        self.btn_back = Button(bx, btn_y_base + 100, bw, 38,
                                "◀ Quay lại menu", color=COLOR_SURFACE_HOVER)

    def handle_event(self, event):
        # Back button
        if self.btn_back.handle_event(event):
            self.result = "back_to_menu"
            return

        # New game
        if self.btn_new_game.handle_event(event):
            self._new_game()
            return

        if self.mode == "human_vs_ai":
            self._handle_human_mode(event)
        # AI vs AI doesn't need click events (auto-play)

    def _handle_human_mode(self, event):
        """Xử lý input cho chế độ Người vs AI."""
        # Algorithm selection
        for name, btn in self.algo_buttons.items():
            if btn.handle_event(event):
                self.selected_algo = name
                return

        # AI move button (khi đến lượt AI = đen)
        if self.btn_ai_move.handle_event(event):
            if (self.board.current_player == "black" and
                not self.is_thinking and
                self.game_status in ACTIVE_GAME_STATUSES):
                self._request_ai_move(self.selected_algo)
            return

        # Board clicks (chỉ khi lượt trắng = người chơi)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.board.current_player == "white" and not self.is_thinking:
                sq = self.board_renderer.get_square_from_pos(event.pos)
                if sq:
                    self._handle_board_click(sq[0], sq[1])

    def _handle_board_click(self, row, col):
        """Xử lý click vào bàn cờ."""
        if self.game_status not in ACTIVE_GAME_STATUSES:
            return

        target_sq = Square(row, col)

        if self.selected_square:
            # Đã chọn quân → thử di chuyển
            from_sq = Square(*self.selected_square)
            matching_move = None
            for m in self.legal_moves:
                if m.to_sq.row == row and m.to_sq.col == col:
                    matching_move = m
                    break

            if matching_move:
                # Phong cấp → tự động chọn hậu
                if matching_move.promotion:
                    matching_move = Move(from_sq, target_sq, promotion="queen")

                self._make_move(matching_move)
                self.selected_square = None
                self.legal_moves = []
                self.board_renderer.selected_square = None
                self.board_renderer.legal_move_squares = []

                # Auto trigger AI move after human move
                if (self.mode == "human_vs_ai" and
                    self.board.current_player == "black" and
                    self.game_status in ACTIVE_GAME_STATUSES):
                    pygame.time.set_timer(pygame.USEREVENT + 1, 500, loops=1)
                return
            else:
                # Click ô khác → bỏ chọn hoặc chọn quân mới
                self.selected_square = None
                self.legal_moves = []

        # Chọn quân
        piece = self.board.get_piece(target_sq)
        if piece and piece.color == self.board.current_player:
            moves = self.move_gen.generate_legal_moves(self.board, target_sq)
            if moves:
                self.selected_square = (row, col)
                self.legal_moves = moves
                self.board_renderer.selected_square = (row, col)
                self.board_renderer.legal_move_squares = [
                    (m.to_sq.row, m.to_sq.col) for m in moves
                ]
            else:
                self.board_renderer.selected_square = None
                self.board_renderer.legal_move_squares = []
        else:
            self.board_renderer.selected_square = None
            self.board_renderer.legal_move_squares = []

    def _make_move(self, move: Move):
        """Thực hiện nước đi."""
        self.board = self.board.make_move(move)
        self.last_move = ((move.from_sq.row, move.from_sq.col),
                          (move.to_sq.row, move.to_sq.col))
        self.board_renderer.last_move = self.last_move
        self.move_history.append(move)

        # Cập nhật game status
        self.game_status = self.move_gen.get_game_status(self.board)
        self._update_check_highlight()

    def _request_ai_move(self, algo_name):
        """Yêu cầu AI tính nước đi (chạy trong thread riêng)."""
        if self.is_thinking:
            return
        self.is_thinking = True
        self.status_text = f"🤔 {ALGO_LABELS[algo_name]} đang suy nghĩ..."

        def _think():
            agent = self.agents[algo_name]
            self.logger.start_timer()
            move = agent.get_move(self.board)
            thinking_time = self.logger.stop_timer()

            if move:
                stats = agent.get_stats()
                stats.thinking_time_ms = thinking_time
                self.stats = {
                    "algorithm": stats.algorithm,
                    "thinking_time_ms": round(stats.thinking_time_ms, 2),
                    "nodes_evaluated": stats.nodes_evaluated,
                    "depth_reached": stats.depth_reached,
                    "evaluation_score": round(stats.evaluation_score, 4),
                }
                self._make_move(move)

            self.is_thinking = False
            self.status_text = ""

        thread = threading.Thread(target=_think, daemon=True)
        thread.start()

    def _update_check_highlight(self):
        """Cập nhật highlight vua bị chiếu."""
        if self.game_status in ("check", "checkmate"):
            king_sq = self.board.find_king(self.board.current_player)
            if king_sq:
                self.board_renderer.check_square = (king_sq.row, king_sq.col)
        else:
            self.board_renderer.check_square = None

    def _new_game(self):
        """Reset ván mới."""
        self.board = Board.from_fen()
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.stats = None
        self.game_status = "playing"
        self.is_thinking = False
        self.move_history = []
        self.board_renderer.selected_square = None
        self.board_renderer.legal_move_squares = []
        self.board_renderer.last_move = None
        self.board_renderer.check_square = None

    def update(self):
        """Update logic — dùng cho AI vs AI auto-play."""
        if self.mode == "ai_vs_ai" and not self.is_thinking:
            if self.game_status in ACTIVE_GAME_STATUSES:
                now = time.time()
                if now - self._last_ai_time > self.ai_delay:
                    algo = self.white_algo if self.board.current_player == "white" else self.black_algo
                    self._request_ai_move(algo)
                    self._last_ai_time = now

        # Handle auto AI move timer
        for event in pygame.event.get(pygame.USEREVENT + 1):
            if (self.mode == "human_vs_ai" and
                self.board.current_player == "black" and
                not self.is_thinking and
                self.game_status in ACTIVE_GAME_STATUSES):
                self._request_ai_move(self.selected_algo)

    def draw(self, surface):
        surface.fill(COLOR_BG)

        # Header
        mode_label = "Người vs AI" if self.mode == "human_vs_ai" else "AI vs AI"
        draw_text(surface, f"♟ Chess AI — {mode_label}",
                  (BOARD_OFFSET_X, 20),
                  font=fonts.heading, color=COLOR_PRIMARY)

        # Board
        self.board_renderer.draw(surface, self.board)

        # Panel
        self.panel.draw(surface)
        px = self.panel.rect.x + 16
        py = self.panel.rect.y

        # Algorithm selection
        if self.mode == "human_vs_ai":
            draw_text(surface, "THUẬT TOÁN AI (ĐEN)", (px, py + 45),
                      font=fonts.label, color=COLOR_TEXT_MUTED)
            for name, btn in self.algo_buttons.items():
                if name == self.selected_algo:
                    btn.color = ALGO_COLORS[name]
                else:
                    btn.color = COLOR_SURFACE_HOVER
                btn.draw(surface)

            self.btn_ai_move.enabled = (
                self.board.current_player == "black" and
                not self.is_thinking and
                self.game_status in ACTIVE_GAME_STATUSES
            )
            self.btn_ai_move.draw(surface)
        else:
            # AI vs AI — hiển thị cặp đấu
            draw_text(surface, "CẶP ĐẤU", (px, py + 45),
                      font=fonts.label, color=COLOR_TEXT_MUTED)
            draw_text(surface, f"⬜ {ALGO_LABELS[self.white_algo]}",
                      (px, py + 70), font=fonts.body, color=COLOR_TEXT)
            draw_text(surface, f"⬛ {ALGO_LABELS[self.black_algo]}",
                      (px, py + 95), font=fonts.body, color=COLOR_TEXT)

        self.btn_new_game.draw(surface)
        self.btn_back.draw(surface)

        # Status badge
        status_y = py + 320
        status_text, status_color = self._get_status_display()
        draw_text(surface, status_text, (px, status_y),
                  font=fonts.body, color=status_color)

        # Thinking indicator
        if self.is_thinking and self.status_text:
            draw_text(surface, self.status_text, (px, status_y + 28),
                      font=fonts.small, color=COLOR_PRIMARY)

        # Stats panel
        if self.stats:
            self._draw_stats(surface, px, status_y + 60)

        # Move counter
        move_count = len(self.move_history)
        draw_text(surface, f"Nước đi: {move_count}",
                  (px, py + BOARD_SIZE - 30),
                  font=fonts.small, color=COLOR_TEXT_MUTED)

    def _get_status_display(self):
        """Trả về text và color cho trạng thái game."""
        if self.game_status == "checkmate":
            winner = "Đen" if self.board.current_player == "white" else "Trắng"
            return f"🏆 Chiếu hết! {winner} thắng!", COLOR_ACCENT
        elif self.game_status == "stalemate":
            return "🤝 Hòa (Stalemate)", COLOR_WARNING
        elif self.game_status == "draw":
            return "🤝 Hòa", COLOR_WARNING
        elif self.game_status == "check":
            player = "Trắng" if self.board.current_player == "white" else "Đen"
            return f"⚠ Chiếu! Lượt: {player}", COLOR_WARNING
        else:
            player = "Trắng" if self.board.current_player == "white" else "Đen"
            return f"🎮 Lượt: {player}", COLOR_SUCCESS

    def _draw_stats(self, surface, x, y):
        """Vẽ thống kê AI."""
        draw_text(surface, "📈 Thống kê", (x, y),
                  font=fonts.label, color=COLOR_TEXT_MUTED)

        stats_items = [
            ("Thuật toán", self.stats["algorithm"]),
            ("Thời gian", f"{self.stats['thinking_time_ms']:.1f} ms"),
            ("Nodes", f"{self.stats['nodes_evaluated']:,}"),
            ("Depth", str(self.stats["depth_reached"])),
            ("Eval", f"{self.stats['evaluation_score']:.2f}"),
        ]

        for i, (label, value) in enumerate(stats_items):
            row_y = y + 22 + i * 20
            draw_text(surface, label, (x, row_y),
                      font=fonts.small, color=COLOR_TEXT_MUTED)
            draw_text(surface, value, (x + 100, row_y),
                      font=fonts.small, color=COLOR_PRIMARY_LIGHT)

    def get_result(self):
        result = self.result
        self.result = None
        return result
