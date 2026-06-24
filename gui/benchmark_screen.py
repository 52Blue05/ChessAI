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


MINIMAX_DEPTH = 2
MCTS_SIMULATIONS = 100

REPORT_BG = (244, 247, 251)
REPORT_HEADER = (40, 88, 132)
REPORT_TABLE_HEADER = (53, 124, 184)
REPORT_SECTION_BG = (221, 238, 216)
REPORT_SECTION_BORDER = (167, 206, 151)
REPORT_SECTION_TEXT = (38, 105, 54)
REPORT_ROW_A = (255, 255, 255)
REPORT_ROW_B = (229, 239, 249)
REPORT_GRID = (154, 187, 218)
REPORT_TEXT = (37, 48, 63)
REPORT_MUTED = (84, 102, 122)
REPORT_SUMMARY_BG = (255, 246, 210)
REPORT_SUMMARY_HEADER = (211, 151, 0)


class BenchmarkScreen:
    """Màn hình benchmark với progress bar + kết quả."""

    def __init__(self):
        self.result = None  # "back_to_menu"
        self.move_gen = MoveGenerator()
        self.logger = None

        # Config
        self.games_per_pair = 10
        self.max_moves = 150
        self.run_config = {}

        # State
        self.is_running = False
        self.is_done = False
        self.progress = 0.0
        self.progress_text = ""
        self.current_game_info = ""
        self.notice = ""

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
                                "< Quay lại menu", color=COLOR_SURFACE_HOVER)

        self.btn_restart = Button(
            815, 694, 165, 34,
            "Chạy lại",
            color=REPORT_HEADER,
        )
        self.btn_clear = Button(
            992, 694, 165, 34,
            "Xóa CSV mới",
            color=(178, 72, 72),
        )

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
            if self.is_done and self.btn_restart.handle_event(event):
                self._start_benchmark()
                return
            if self.is_done and self.btn_clear.handle_event(event):
                deleted = BenchmarkLogger.clear_session_files()
                self._reset_results_view()
                self.notice = f"Đã xóa {deleted} file benchmark session."
                return

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
        self.run_config = {
            "games_per_pair": self.games_per_pair,
            "max_moves": self.max_moves,
            "minimax_depth": MINIMAX_DEPTH,
            "mcts_simulations": MCTS_SIMULATIONS,
            "algorithms": ["greedy", "minimax", "mcts"],
        }
        self.logger = BenchmarkLogger.create_session(
            self.run_config,
            prefix="pygame_benchmark",
        )
        self.is_running = True
        self.is_done = False
        self.progress = 0.0
        self.results = {}
        self.matchups = []
        self.algo_stats = {}
        self.notice = ""

        thread = threading.Thread(target=self._run_benchmark, daemon=True)
        thread.start()

    def _reset_results_view(self):
        self.is_running = False
        self.is_done = False
        self.progress = 0.0
        self.progress_text = ""
        self.current_game_info = ""
        self.results = {}
        self.matchups = []
        self.algo_stats = {}
        self.chart_time.set_data([])
        self.chart_nodes.set_data([])
        self.chart_winrate.set_data([])
        self.logger = None

    def _run_benchmark(self):
        """Chạy Round Robin benchmark."""
        agents = {
            "greedy": GreedyAgent(),
            "minimax": MinimaxAgent(depth=MINIMAX_DEPTH),
            "mcts": MCTSAgent(simulations=MCTS_SIMULATIONS),
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
        algo_depths = {name: [] for name in agents}

        for name_a, name_b in pairs:
            matchup = {"pair": f"{name_a} vs {name_b}",
                        "a_wins": 0, "b_wins": 0, "draws": 0}
            matchup_stats = {
                name_a: {"times": [], "nodes": [], "depths": []},
                name_b: {"times": [], "nodes": [], "depths": []},
            }

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
                    algo_times, algo_nodes, algo_depths,
                    matchup_stats,
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

            matchup["performance"] = {
                name: self._summarize_samples(samples)
                for name, samples in matchup_stats.items()
            }
            matchup_data.append(matchup)

        self.matchups = matchup_data

        # Compute algo stats
        for name in agents:
            times = algo_times[name]
            nodes = algo_nodes[name]
            self.algo_stats[name] = {
                "avg_time_ms": sum(times) / len(times) if times else 0,
                "avg_nodes": sum(nodes) / len(nodes) if nodes else 0,
                "avg_depth": (
                    sum(algo_depths[name]) / len(algo_depths[name])
                    if algo_depths[name] else 0
                ),
                "total_moves": len(times),
            }

        self._update_charts()
        self.is_running = False
        self.is_done = True

    def _play_game(self, white_agent, black_agent,
                    w_name, b_name,
                    algo_times, algo_nodes, algo_depths,
                    matchup_stats) -> str:
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
                    result = (
                        "black_win"
                        if board.current_player == "white"
                        else "white_win"
                    )
                else:
                    result = "draw"
                self.logger.log_game_result(
                    game_id,
                    result,
                    white_algorithm=w_name,
                    black_algorithm=b_name,
                )
                return result

            stats = current.get_stats()
            stats.thinking_time_ms = elapsed
            algo_times[curr_name].append(elapsed)
            algo_nodes[curr_name].append(stats.nodes_evaluated)
            algo_depths[curr_name].append(stats.depth_reached)
            matchup_stats[curr_name]["times"].append(elapsed)
            matchup_stats[curr_name]["nodes"].append(stats.nodes_evaluated)
            matchup_stats[curr_name]["depths"].append(stats.depth_reached)

            fen_before = board.to_fen()
            board = board.make_move(move)
            fen_after = board.to_fen()
            status = self.move_gen.get_game_status(board)

            game_result = "ongoing"
            if status == "checkmate":
                game_result = (
                    "black_win"
                    if board.current_player == "white"
                    else "white_win"
                )
            elif status in ("stalemate", "draw"):
                game_result = "draw"

            self.logger.log_move(
                game_id=game_id,
                move_number=move_num,
                stats=stats,
                move_uci=move.to_uci(),
                fen_before=fen_before,
                fen_after=fen_after,
                game_result=game_result,
                white_algorithm=w_name,
                black_algorithm=b_name,
            )

            if game_result != "ongoing":
                self.logger.log_game_result(
                    game_id,
                    game_result,
                    white_algorithm=w_name,
                    black_algorithm=b_name,
                )
                return game_result

        self.logger.log_game_result(
            game_id,
            "draw",
            white_algorithm=w_name,
            black_algorithm=b_name,
        )
        return "draw"

    @staticmethod
    def _summarize_samples(samples):
        moves = len(samples["times"])
        return {
            "avg_time_ms": (
                sum(samples["times"]) / moves if moves else 0
            ),
            "avg_nodes": (
                sum(samples["nodes"]) / moves if moves else 0
            ),
            "avg_depth": (
                sum(samples["depths"]) / moves if moves else 0
            ),
            "moves": moves,
        }

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
        if self.is_done:
            self.btn_back.rect.topleft = (72, 34)
            self._draw_results(surface)
            return

        self.btn_back.rect.topleft = (30, 20)
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
            draw_text(
                surface,
                (
                    f"Minimax depth {MINIMAX_DEPTH} · "
                    f"MCTS {MCTS_SIMULATIONS} simulations"
                ),
                (WINDOW_WIDTH // 2, 325),
                font=fonts.small,
                color=COLOR_TEXT_MUTED,
                center=True,
            )
            if self.notice:
                draw_text(
                    surface,
                    self.notice,
                    (WINDOW_WIDTH // 2, 355),
                    font=fonts.small,
                    color=COLOR_SUCCESS,
                    center=True,
                )

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
            if self.logger:
                draw_text(
                    surface,
                    self.logger.csv_path.name,
                    (WINDOW_WIDTH // 2, 405),
                    font=fonts.small,
                    color=COLOR_TEXT_MUTED,
                    center=True,
                )

    def _draw_results(self, surface):
        """Vẽ báo cáo benchmark theo bố cục bảng thống kê."""
        surface.fill(REPORT_BG)
        self._draw_report_header(surface)
        self.btn_back.draw(surface)

        self._draw_section_title(
            surface,
            100,
            "1. Tỷ lệ thắng AI vs AI",
        )
        self._draw_table(
            surface,
            x=68,
            y=132,
            headers=[
                "Cặp mô hình",
                "Greedy thắng",
                "Minimax thắng",
                "MCTS thắng",
                "Hòa",
            ],
            rows=self._build_win_rows(),
            column_widths=[320, 185, 185, 185, 189],
            row_height=23,
        )

        self._draw_section_title(
            surface,
            245,
            "2. Hiệu năng phản hồi trung bình trong ván",
        )
        self._draw_table(
            surface,
            x=68,
            y=277,
            headers=[
                "Cặp mô hình",
                "Mô hình",
                "Thời gian TB",
                "Nodes",
                "Độ sâu TB",
                "Số nước",
            ],
            rows=self._build_performance_rows(),
            column_widths=[260, 180, 170, 150, 150, 154],
            row_height=20,
        )

        self._draw_algorithm_summary(surface)
        self._draw_config_summary(surface)
        self.btn_restart.draw(surface)
        self.btn_clear.draw(surface)

    def _draw_report_header(self, surface):
        rect = pygame.Rect(60, 22, 1080, 66)
        pygame.draw.rect(surface, REPORT_HEADER, rect, border_radius=7)
        draw_text(
            surface,
            "BÁO CÁO SO SÁNH HIỆU QUẢ 3 MÔ HÌNH AI CỜ VUA",
            (WINDOW_WIDTH // 2, 45),
            font=fonts.heading,
            color=(255, 255, 255),
            center=True,
        )
        draw_text(
            surface,
            (
                f"Benchmark mẫu: {self.games_per_pair} ván/cặp  |  "
                f"Bàn cờ: 8×8  |  Minimax depth: {MINIMAX_DEPTH}  |  "
                f"MCTS: {MCTS_SIMULATIONS} simulations"
            ),
            (WINDOW_WIDTH // 2, 70),
            font=fonts.small,
            color=(218, 231, 244),
            center=True,
        )

    @staticmethod
    def _draw_section_title(surface, y, title):
        rect = pygame.Rect(62, y, 1068, 24)
        pygame.draw.rect(surface, REPORT_SECTION_BG, rect, border_radius=4)
        pygame.draw.rect(
            surface,
            REPORT_SECTION_BORDER,
            rect,
            width=1,
            border_radius=4,
        )
        draw_text(
            surface,
            title,
            (78, y + 4),
            font=fonts.label,
            color=REPORT_SECTION_TEXT,
        )

    @staticmethod
    def _draw_table(
        surface,
        x,
        y,
        headers,
        rows,
        column_widths,
        row_height,
    ):
        header_height = 25
        table_width = sum(column_widths)
        table_height = header_height + row_height * len(rows)
        pygame.draw.rect(
            surface,
            REPORT_GRID,
            pygame.Rect(x, y, table_width, table_height),
            width=1,
        )

        cursor_x = x
        for header, width in zip(headers, column_widths):
            rect = pygame.Rect(cursor_x, y, width, header_height)
            pygame.draw.rect(surface, REPORT_TABLE_HEADER, rect)
            pygame.draw.rect(surface, REPORT_GRID, rect, width=1)
            draw_text(
                surface,
                header,
                (cursor_x + 7, y + 5),
                font=fonts.label,
                color=(255, 255, 255),
            )
            cursor_x += width

        for row_index, row in enumerate(rows):
            row_y = y + header_height + row_index * row_height
            background = REPORT_ROW_A if row_index % 2 == 0 else REPORT_ROW_B
            cursor_x = x
            for value, width in zip(row, column_widths):
                rect = pygame.Rect(cursor_x, row_y, width, row_height)
                pygame.draw.rect(surface, background, rect)
                pygame.draw.rect(surface, REPORT_GRID, rect, width=1)
                draw_text(
                    surface,
                    value,
                    (cursor_x + 6, row_y + 3),
                    font=fonts.small,
                    color=REPORT_TEXT,
                )
                cursor_x += width

    def _build_win_rows(self):
        rows = []
        for matchup in self.matchups:
            name_a, name_b = matchup["pair"].split(" vs ")
            total = (
                matchup["a_wins"]
                + matchup["b_wins"]
                + matchup["draws"]
            )
            win_counts = {
                name_a: matchup["a_wins"],
                name_b: matchup["b_wins"],
            }
            rows.append([
                f"{self._algo_name(name_a)} vs {self._algo_name(name_b)}",
                self._result_fraction(win_counts, "greedy", total),
                self._result_fraction(win_counts, "minimax", total),
                self._result_fraction(win_counts, "mcts", total),
                f"{matchup['draws']}/{total}",
            ])
        return rows

    def _build_performance_rows(self):
        rows = []
        for matchup in self.matchups:
            name_a, name_b = matchup["pair"].split(" vs ")
            pair_label = (
                f"{self._algo_name(name_a)} vs {self._algo_name(name_b)}"
            )
            performance = matchup.get("performance", {})
            for row_index, name in enumerate((name_a, name_b)):
                data = performance.get(name, {})
                rows.append([
                    pair_label if row_index == 0 else "",
                    self._algo_name(name),
                    f"{data.get('avg_time_ms', 0):.2f} ms",
                    f"{data.get('avg_nodes', 0):,.0f}",
                    f"{data.get('avg_depth', 0):.1f}",
                    str(data.get("moves", 0)),
                ])
        return rows

    @staticmethod
    def _result_fraction(win_counts, algorithm, total):
        if algorithm not in win_counts:
            return "-"
        return f"{win_counts[algorithm]}/{total}"

    @staticmethod
    def _algo_name(name):
        return {
            "greedy": "Greedy",
            "minimax": "Minimax",
            "mcts": "MCTS",
        }.get(name, name)

    def _draw_algorithm_summary(self, surface):
        box = pygame.Rect(60, 440, 520, 228)
        pygame.draw.rect(surface, (255, 255, 255), box, border_radius=6)
        pygame.draw.rect(
            surface,
            REPORT_GRID,
            box,
            width=2,
            border_radius=6,
        )
        header = pygame.Rect(60, 440, 520, 28)
        pygame.draw.rect(surface, REPORT_TABLE_HEADER, header, border_radius=5)
        draw_text(
            surface,
            "3. Tổng hợp hiệu năng theo mô hình",
            (74, 446),
            font=fonts.label,
            color=(255, 255, 255),
        )

        for index, name in enumerate(("greedy", "minimax", "mcts")):
            data = self.algo_stats.get(name, {})
            result = self.results.get(name, {})
            total_games = sum(
                result.get(key, 0)
                for key in ("wins", "losses", "draws")
            )
            win_rate = (
                result.get("wins", 0) / total_games * 100
                if total_games else 0
            )
            y = 482 + index * 58
            draw_text(
                surface,
                self._algo_name(name),
                (76, y),
                font=fonts.label,
                color=REPORT_HEADER,
            )
            draw_text(
                surface,
                f"Thắng {win_rate:.1f}%",
                (485, y),
                font=fonts.small,
                color=REPORT_SECTION_TEXT,
            )
            draw_text(
                surface,
                (
                    f"{data.get('avg_time_ms', 0):.2f} ms/nước  |  "
                    f"{data.get('avg_nodes', 0):,.0f} nodes  |  "
                    f"depth {data.get('avg_depth', 0):.1f}  |  "
                    f"{data.get('total_moves', 0)} nước"
                ),
                (76, y + 23),
                font=fonts.small,
                color=REPORT_MUTED,
            )

    def _draw_config_summary(self, surface):
        box = pygame.Rect(595, 440, 545, 228)
        pygame.draw.rect(surface, REPORT_SUMMARY_BG, box, border_radius=6)
        pygame.draw.rect(
            surface,
            REPORT_SUMMARY_HEADER,
            box,
            width=2,
            border_radius=6,
        )
        header = pygame.Rect(595, 440, 545, 28)
        pygame.draw.rect(
            surface,
            REPORT_SUMMARY_HEADER,
            header,
            border_radius=5,
        )
        draw_text(
            surface,
            "Cấu hình benchmark trên cùng thế cờ chuẩn",
            (610, 446),
            font=fonts.label,
            color=(255, 255, 255),
        )

        total_games = len(self.matchups) * self.games_per_pair
        lines = [
            (
                f"Số ván: {self.games_per_pair}/cặp · "
                f"Tổng cộng: {total_games} ván"
            ),
            "Mỗi cặp luân phiên bên Trắng/Đen · Bàn cờ 8×8",
            f"Greedy: evaluation chiến thuật 1 ply",
            f"Minimax: depth {MINIMAX_DEPTH} + Alpha-Beta",
            f"MCTS: {MCTS_SIMULATIONS} simulations + rollout chiến thuật",
        ]
        if self.logger:
            filename = self.logger.csv_path.name
            if len(filename) > 57:
                filename = filename[:54] + "..."
            lines.append(f"CSV: {filename}")

        for index, line in enumerate(lines):
            draw_text(
                surface,
                line,
                (612, 484 + index * 28),
                font=fonts.small,
                color=REPORT_TEXT,
            )

    def get_result(self):
        result = self.result
        self.result = None
        return result
