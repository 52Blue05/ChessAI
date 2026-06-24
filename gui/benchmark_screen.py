"""
gui/benchmark_screen.py
Màn hình Benchmark — chạy Round Robin tự động giữa 3 AI.
Hiển thị progress bar, bảng kết quả, biểu đồ bar chart.
"""

import pygame
import threading
import time
import uuid
from gui.constants import *
from gui.widgets import Button, Panel, ProgressBar, BarChart, draw_text
from backend.engine.board import Board
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkLogger
from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent


class BenchmarkScreen:
    """Màn hình benchmark với progress bar + kết quả."""

    def __init__(self):
        self.result = None  # "back_to_menu"
        self.move_gen = MoveGenerator()
        self.logger = BenchmarkLogger()

        # Config
        self.games_per_pair = 10
        self.max_moves = 150

        # State
        self.is_running = False
        self.is_done = False
        self.progress = 0.0
        self.progress_text = ""
        self.current_game_info = ""

        # Results
        self.results = {}  # {name: {wins, losses, draws}}
        self.matchups = []
        self.algo_stats = {}  # {name: {avg_time, avg_nodes}}

        # UI
        self._build_ui()

    def _build_ui(self):
        cx = WINDOW_WIDTH // 2
        btn_w = 200

        # Config buttons
        self.btn_10 = Button(cx - btn_w - 20, 160, btn_w, 42,
                              "10 ván / cặp", color=COLOR_PRIMARY)
        self.btn_20 = Button(cx + 20, 160, btn_w, 42,
                              "20 ván / cặp", color=COLOR_SURFACE_HOVER)

        # Start button
        self.btn_start = Button(cx - 120, 230, 240, 48,
                                 "▶ Bắt đầu Benchmark", color=COLOR_SUCCESS)

        # Back button
        self.btn_back = Button(30, 20, 160, 38,
                                "◀ Quay lại menu", color=COLOR_SURFACE_HOVER)

        # Progress bar
        self.progress_bar = ProgressBar(cx - 300, 310, 600, 28, color=COLOR_PRIMARY)

        # Bar charts
        chart_y = 400
        chart_w = 350
        chart_h = 110
        self.chart_time = BarChart(40, chart_y, chart_w, chart_h)
        self.chart_nodes = BarChart(40, chart_y + 130, chart_w, chart_h)
        self.chart_winrate = BarChart(420, chart_y, chart_w, chart_h)

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            self.result = "back_to_menu"
            return

        if not self.is_running:
            if self.btn_10.handle_event(event):
                self.games_per_pair = 10
                self.btn_10.color = COLOR_PRIMARY
                self.btn_20.color = COLOR_SURFACE_HOVER
            elif self.btn_20.handle_event(event):
                self.games_per_pair = 20
                self.btn_20.color = COLOR_PRIMARY
                self.btn_10.color = COLOR_SURFACE_HOVER

            if self.btn_start.handle_event(event):
                self._start_benchmark()

    def _start_benchmark(self):
        """Bắt đầu benchmark trong thread riêng."""
        self.is_running = True
        self.is_done = False
        self.progress = 0.0
        self.results = {}
        self.matchups = []
        self.algo_stats = {}

        thread = threading.Thread(target=self._run_benchmark, daemon=True)
        thread.start()

    def _run_benchmark(self):
        """Chạy Round Robin benchmark."""
        agents = {
            "greedy": GreedyAgent(),
            "minimax": MinimaxAgent(depth=2),
            "mcts": MCTSAgent(simulations=100),
        }

        pairs = [
            ("greedy", "minimax"),
            ("greedy", "mcts"),
            ("minimax", "mcts"),
        ]

        total_games = len(pairs) * self.games_per_pair
        games_played = 0

        # Init results
        self.results = {name: {"wins": 0, "losses": 0, "draws": 0} for name in agents}
        matchup_data = []

        # Stats tracking
        algo_times = {name: [] for name in agents}
        algo_nodes = {name: [] for name in agents}

        for name_a, name_b in pairs:
            matchup = {"pair": f"{name_a} vs {name_b}",
                        "a_wins": 0, "b_wins": 0, "draws": 0}

            for game_num in range(self.games_per_pair):
                # Đổi bên
                if game_num % 2 == 0:
                    w_name, b_name = name_a, name_b
                else:
                    w_name, b_name = name_b, name_a

                self.current_game_info = f"{w_name} (T) vs {b_name} (Đ)"
                self.progress_text = f"Game {games_played + 1}/{total_games}"

                result = self._play_game(
                    agents[w_name], agents[b_name],
                    w_name, b_name,
                    algo_times, algo_nodes,
                )

                # Update results
                if result == "white_win":
                    self.results[w_name]["wins"] += 1
                    self.results[b_name]["losses"] += 1
                    if w_name == name_a:
                        matchup["a_wins"] += 1
                    else:
                        matchup["b_wins"] += 1
                elif result == "black_win":
                    self.results[b_name]["wins"] += 1
                    self.results[w_name]["losses"] += 1
                    if b_name == name_a:
                        matchup["a_wins"] += 1
                    else:
                        matchup["b_wins"] += 1
                else:
                    self.results[name_a]["draws"] += 1
                    self.results[name_b]["draws"] += 1
                    matchup["draws"] += 1

                games_played += 1
                self.progress = games_played / total_games

            matchup_data.append(matchup)

        self.matchups = matchup_data

        # Compute algo stats
        for name in agents:
            times = algo_times[name]
            nodes = algo_nodes[name]
            self.algo_stats[name] = {
                "avg_time_ms": sum(times) / len(times) if times else 0,
                "avg_nodes": sum(nodes) / len(nodes) if nodes else 0,
            }

        self._update_charts()
        self.is_running = False
        self.is_done = True

    def _play_game(self, white_agent, black_agent,
                    w_name, b_name,
                    algo_times, algo_nodes) -> str:
        """Chơi 1 ván đấu, trả về 'white_win', 'black_win', 'draw'."""
        board = Board.from_fen()
        game_id = str(uuid.uuid4())[:8]

        for move_num in range(1, self.max_moves + 1):
            current = white_agent if board.current_player == "white" else black_agent
            curr_name = w_name if board.current_player == "white" else b_name

            start_t = time.perf_counter()
            move = current.get_move(board)
            elapsed = (time.perf_counter() - start_t) * 1000

            if move is None:
                status = self.move_gen.get_game_status(board)
                if status == "checkmate":
                    return "black_win" if board.current_player == "white" else "white_win"
                return "draw"

            stats = current.get_stats()
            algo_times[curr_name].append(elapsed)
            algo_nodes[curr_name].append(stats.nodes_evaluated)

            board = board.make_move(move)
            status = self.move_gen.get_game_status(board)

            if status == "checkmate":
                return "black_win" if board.current_player == "white" else "white_win"
            if status in ("stalemate", "draw"):
                return "draw"

        return "draw"

    def _update_charts(self):
        """Cập nhật dữ liệu biểu đồ."""
        algo_names = ["greedy", "minimax", "mcts"]

        # Time chart
        self.chart_time.set_data([
            {"label": ALGO_LABELS[n].split("(")[0].strip(),
             "value": self.algo_stats.get(n, {}).get("avg_time_ms", 0),
             "color": ALGO_COLORS[n],
             "formatted": f"{self.algo_stats.get(n, {}).get('avg_time_ms', 0):.1f} ms"}
            for n in algo_names
        ], title="⏱ Thời gian TB (ms/move)")

        # Nodes chart
        self.chart_nodes.set_data([
            {"label": ALGO_LABELS[n].split("(")[0].strip(),
             "value": self.algo_stats.get(n, {}).get("avg_nodes", 0),
             "color": ALGO_COLORS[n],
             "formatted": f"{self.algo_stats.get(n, {}).get('avg_nodes', 0):,.0f}"}
            for n in algo_names
        ], title="🔢 Nodes duyệt TB")

        # Win rate chart
        self.chart_winrate.set_data([
            {"label": ALGO_LABELS[n].split("(")[0].strip(),
             "value": self._get_win_rate(n),
             "color": ALGO_COLORS[n],
             "formatted": f"{self._get_win_rate(n):.1f}%"}
            for n in algo_names
        ], title="🏆 Tỷ lệ thắng (%)")

    def _get_win_rate(self, algo_name):
        """Tính win rate cho 1 thuật toán."""
        r = self.results.get(algo_name, {})
        total = r.get("wins", 0) + r.get("losses", 0) + r.get("draws", 0)
        if total == 0:
            return 0
        return r.get("wins", 0) / total * 100

    def update(self):
        pass

    def draw(self, surface):
        surface.fill(COLOR_BG)

        # Header
        draw_text(surface, "📊 Benchmark — Round Robin",
                  (WINDOW_WIDTH // 2, 40),
                  font=fonts.heading, color=COLOR_PRIMARY, center=True)

        draw_text(surface, "3 thuật toán AI đấu vòng tròn tự động",
                  (WINDOW_WIDTH // 2, 75),
                  font=fonts.body, color=COLOR_TEXT_MUTED, center=True)

        self.btn_back.draw(surface)

        if not self.is_running and not self.is_done:
            # Config screen
            draw_text(surface, "Số ván mỗi cặp:",
                      (WINDOW_WIDTH // 2, 140),
                      font=fonts.label, color=COLOR_TEXT_MUTED, center=True)
            self.btn_10.draw(surface)
            self.btn_20.draw(surface)
            self.btn_start.draw(surface)

            # Info
            total = 3 * self.games_per_pair
            draw_text(surface,
                      f"Tổng số ván: {total} (3 cặp × {self.games_per_pair} ván)",
                      (WINDOW_WIDTH // 2, 300),
                      font=fonts.small, color=COLOR_TEXT_MUTED, center=True)

        elif self.is_running:
            # Running — show progress
            self.progress_bar.set_progress(self.progress, self.progress_text)
            self.progress_bar.draw(surface)

            draw_text(surface, self.current_game_info,
                      (WINDOW_WIDTH // 2, 355),
                      font=fonts.body, color=COLOR_TEXT, center=True)

            # Thinking animation dots
            t = time.time()
            dots = "." * (int(t * 2) % 4)
            draw_text(surface, f"Đang chạy benchmark{dots}",
                      (WINDOW_WIDTH // 2, 380),
                      font=fonts.small, color=COLOR_PRIMARY, center=True)

        elif self.is_done:
            # Results
            self._draw_results(surface)

    def _draw_results(self, surface):
        """Vẽ kết quả benchmark."""
        # Leaderboard table
        draw_text(surface, "🏆 Bảng xếp hạng",
                  (WINDOW_WIDTH // 2, 115),
                  font=fonts.heading, color=COLOR_TEXT, center=True)

        # Sort by wins
        sorted_algos = sorted(
            self.results.items(),
            key=lambda x: x[1]["wins"],
            reverse=True,
        )

        # Table header
        table_x = WINDOW_WIDTH // 2 - 280
        header_y = 150
        headers = ["#", "Thuật toán", "Thắng", "Thua", "Hòa", "Win Rate"]
        col_widths = [30, 180, 60, 60, 60, 80]

        x = table_x
        for h, w in zip(headers, col_widths):
            draw_text(surface, h, (x, header_y),
                      font=fonts.label, color=COLOR_TEXT_MUTED)
            x += w

        pygame.draw.line(surface, COLOR_BORDER,
                         (table_x, header_y + 22),
                         (table_x + sum(col_widths), header_y + 22), 1)

        # Table rows
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, data) in enumerate(sorted_algos):
            row_y = header_y + 30 + i * 28
            x = table_x

            total = data["wins"] + data["losses"] + data["draws"]
            wr = data["wins"] / total * 100 if total > 0 else 0

            values = [
                medals[i] if i < 3 else str(i + 1),
                ALGO_LABELS.get(name, name),
                str(data["wins"]),
                str(data["losses"]),
                str(data["draws"]),
                f"{wr:.1f}%",
            ]
            colors = [
                COLOR_TEXT,
                ALGO_COLORS.get(name, COLOR_TEXT),
                COLOR_SUCCESS,
                COLOR_ACCENT,
                COLOR_TEXT_MUTED,
                COLOR_WARNING,
            ]

            for val, col, w in zip(values, colors, col_widths):
                draw_text(surface, val, (x, row_y),
                          font=fonts.body, color=col)
                x += w

        # Matchup details
        matchup_y = header_y + 30 + len(sorted_algos) * 28 + 20
        draw_text(surface, "📋 Chi tiết cặp đấu",
                  (table_x, matchup_y),
                  font=fonts.label, color=COLOR_TEXT_MUTED)

        for i, m in enumerate(self.matchups):
            y = matchup_y + 22 + i * 22
            text = f"{m['pair']}:   {m['a_wins']} - {m['b_wins']}   (hòa: {m['draws']})"
            draw_text(surface, text, (table_x + 10, y),
                      font=fonts.small, color=COLOR_TEXT)

        # Charts
        self.chart_time.draw(surface)
        self.chart_nodes.draw(surface)
        self.chart_winrate.draw(surface)

        # Restart button
        restart_btn = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 60,
                              200, 38, "🔄 Chạy lại",
                              color=COLOR_SURFACE_HOVER)
        restart_btn.draw(surface)

    def get_result(self):
        result = self.result
        self.result = None
        return result
