"""
main.py
Entry point cho Chess AI Desktop App.

Chạy: python main.py

Không cần Docker, không cần localhost.
"""

import sys
from pathlib import Path

# Thêm root vào path để import backend/ai-core
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import pygame
from gui.constants import *
from gui.menu_screen import MenuScreen
from gui.game_screen import GameScreen
from gui.benchmark_screen import BenchmarkScreen


class ChessAIApp:
    """Ứng dụng Chess AI Desktop."""

    def __init__(self):
        pygame.init()
        init_fonts()

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        # Screens
        self.current_screen = "menu"
        self.menu_screen = MenuScreen()
        self.game_screen = None
        self.benchmark_screen = None

    def run(self):
        """Main loop."""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)

        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.current_screen != "menu":
                    self._go_to_menu()
                else:
                    self.running = False
                return

            # Dispatch to current screen
            if self.current_screen == "menu":
                self.menu_screen.handle_event(event)
            elif self.current_screen == "game":
                self.game_screen.handle_event(event)
            elif self.current_screen == "benchmark":
                self.benchmark_screen.handle_event(event)

    def _update(self):
        if self.current_screen == "menu":
            self.menu_screen.update()
            result = self.menu_screen.get_result()
            if result == "human_vs_ai":
                self.game_screen = GameScreen(mode="human_vs_ai")
                self.current_screen = "game"
            elif result == "ai_vs_ai":
                self.game_screen = GameScreen(mode="ai_vs_ai")
                self.current_screen = "game"
            elif result == "benchmark":
                self.benchmark_screen = BenchmarkScreen()
                self.current_screen = "benchmark"

        elif self.current_screen == "game":
            self.game_screen.update()
            result = self.game_screen.get_result()
            if result == "back_to_menu":
                self._go_to_menu()

        elif self.current_screen == "benchmark":
            self.benchmark_screen.update()
            result = self.benchmark_screen.get_result()
            if result == "back_to_menu":
                self._go_to_menu()

    def _draw(self):
        if self.current_screen == "menu":
            self.menu_screen.draw(self.screen)
        elif self.current_screen == "game":
            self.game_screen.draw(self.screen)
        elif self.current_screen == "benchmark":
            self.benchmark_screen.draw(self.screen)

        pygame.display.flip()

    def _go_to_menu(self):
        self.current_screen = "menu"
        self.menu_screen = MenuScreen()


if __name__ == "__main__":
    app = ChessAIApp()
    print("[Chess AI Desktop] Dang khoi dong...")
    print("   Dong cua so hoac nhan ESC de thoat.")
    app.run()
