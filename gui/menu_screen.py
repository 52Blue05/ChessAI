"""
gui/menu_screen.py
Màn hình menu chính — chọn chế độ chơi.
"""

import pygame
from gui.constants import *
from gui.widgets import Button, draw_text


class MenuScreen:
    """
    Màn hình menu chính.

    Chế độ:
    1. Người vs AI
    2. AI vs AI (xem)
    3. Benchmark Round Robin
    """

    def __init__(self):
        self.buttons = []
        self._build_buttons()
        self.result = None  # "human_vs_ai", "ai_vs_ai", "benchmark"
        self._anim_offset = 0
        self._anim_dir = 1

    def _build_buttons(self):
        cx = WINDOW_WIDTH // 2
        btn_w = 380
        btn_h = 56
        start_y = 320

        self.btn_human_ai = Button(
            cx - btn_w // 2, start_y, btn_w, btn_h,
            "♟  Người vs AI",
            color=COLOR_PRIMARY,
        )
        self.btn_ai_ai = Button(
            cx - btn_w // 2, start_y + 76, btn_w, btn_h,
            "🤖  AI vs AI (Xem trận đấu)",
            color=(50, 50, 90),
        )
        self.btn_benchmark = Button(
            cx - btn_w // 2, start_y + 152, btn_w, btn_h,
            "📊  Benchmark Round Robin",
            color=(50, 50, 90),
        )
        self.buttons = [self.btn_human_ai, self.btn_ai_ai, self.btn_benchmark]

    def handle_event(self, event):
        if self.btn_human_ai.handle_event(event):
            self.result = "human_vs_ai"
        elif self.btn_ai_ai.handle_event(event):
            self.result = "ai_vs_ai"
        elif self.btn_benchmark.handle_event(event):
            self.result = "benchmark"

    def update(self):
        self._anim_offset += 0.02 * self._anim_dir
        if abs(self._anim_offset) > 5:
            self._anim_dir *= -1

    def draw(self, surface):
        surface.fill(COLOR_BG)

        # Title with gradient effect (simulated)
        title_y = 100 + self._anim_offset
        draw_text(surface, "♟ Chess AI", (WINDOW_WIDTH // 2, title_y),
                  font=fonts.title, color=COLOR_PRIMARY, center=True)

        draw_text(surface, "So sánh thuật toán: Greedy · Minimax · MCTS",
                  (WINDOW_WIDTH // 2, 155),
                  font=fonts.body, color=COLOR_TEXT_MUTED, center=True)

        # Decorative line
        line_y = 200
        pygame.draw.line(surface, COLOR_BORDER,
                         (WINDOW_WIDTH // 2 - 180, line_y),
                         (WINDOW_WIDTH // 2 + 180, line_y), 1)

        # Subtitle
        draw_text(surface, "Chọn chế độ chơi",
                  (WINDOW_WIDTH // 2, 260),
                  font=fonts.heading, color=COLOR_TEXT, center=True)

        # Buttons
        for btn in self.buttons:
            btn.draw(surface)

        # Footer
        draw_text(surface, "HUST — Nhập môn Trí tuệ Nhân tạo",
                  (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 40),
                  font=fonts.small, color=COLOR_TEXT_MUTED, center=True)

    def get_result(self):
        """Trả về chế độ đã chọn và reset."""
        result = self.result
        self.result = None
        return result
