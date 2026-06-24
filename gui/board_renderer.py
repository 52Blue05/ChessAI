"""
gui/board_renderer.py
Vẽ bàn cờ 8×8, quân cờ, highlight nước đi hợp lệ.
"""

import pygame
from gui.constants import *
from backend.engine.board import Board, Square


class BoardRenderer:
    """Renderer bàn cờ với highlight và animation."""

    def __init__(self, offset_x=BOARD_OFFSET_X, offset_y=BOARD_OFFSET_Y):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.selected_square = None     # (row, col) or None
        self.legal_move_squares = []    # [(row, col), ...]
        self.last_move = None           # (from_sq, to_sq)
        self.check_square = None        # (row, col) or None

    def draw(self, surface, board: Board):
        """Vẽ toàn bộ bàn cờ."""
        self._draw_board_background(surface)
        self._draw_squares(surface)
        self._draw_highlights(surface)
        self._draw_pieces(surface, board)
        self._draw_coordinates(surface)

    def _draw_board_background(self, surface):
        """Vẽ nền và viền bàn cờ."""
        border = 4
        bg_rect = pygame.Rect(
            self.offset_x - border, self.offset_y - border,
            BOARD_SIZE + border * 2, BOARD_SIZE + border * 2,
        )
        pygame.draw.rect(surface, COLOR_BORDER, bg_rect, border_radius=4)

    def _draw_squares(self, surface):
        """Vẽ 64 ô cờ."""
        for r in range(8):
            for c in range(8):
                is_light = (r + c) % 2 == 0
                color = COLOR_BOARD_LIGHT if is_light else COLOR_BOARD_DARK
                rect = self._get_square_rect(r, c)
                pygame.draw.rect(surface, color, rect)

    def _draw_highlights(self, surface):
        """Vẽ highlight: ô đang chọn, nước đi hợp lệ, nước đi cuối, chiếu."""
        # Last move highlight
        if self.last_move:
            for sq in self.last_move:
                rect = self._get_square_rect(sq[0], sq[1])
                highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                highlight.fill((255, 235, 59, 60))
                surface.blit(highlight, rect.topleft)

        # Check highlight
        if self.check_square:
            rect = self._get_square_rect(self.check_square[0], self.check_square[1])
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill((255, 60, 60, 100))
            surface.blit(highlight, rect.topleft)

        # Selected square
        if self.selected_square:
            r, c = self.selected_square
            rect = self._get_square_rect(r, c)
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill((108, 99, 255, 120))
            surface.blit(highlight, rect.topleft)
            pygame.draw.rect(surface, COLOR_PRIMARY, rect, width=3)

        # Legal moves
        for (r, c) in self.legal_move_squares:
            rect = self._get_square_rect(r, c)
            center = rect.center
            # Chấm tròn cho ô trống, vòng tròn cho ô có quân
            dot_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (108, 99, 255, 100),
                               (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 10)
            surface.blit(dot_surf, rect.topleft)

    def _draw_pieces(self, surface, board: Board):
        """Vẽ quân cờ bằng Unicode."""
        for r in range(8):
            for c in range(8):
                piece = board.grid[r][c]
                if piece:
                    symbol = PIECE_SYMBOLS.get((piece.piece_type, piece.color), "?")
                    text_surf = fonts.piece.render(symbol, True, (0, 0, 0))
                    rect = self._get_square_rect(r, c)
                    text_rect = text_surf.get_rect(center=rect.center)
                    # Shadow for white pieces
                    if piece.color == "white":
                        shadow_surf = fonts.piece.render(symbol, True, (50, 50, 50))
                        shadow_rect = text_rect.copy()
                        shadow_rect.x += 1
                        shadow_rect.y += 1
                        surface.blit(shadow_surf, shadow_rect)
                    surface.blit(text_surf, text_rect)

    def _draw_coordinates(self, surface):
        """Vẽ tọa độ a-h, 1-8."""
        for c in range(8):
            letter = chr(ord("a") + c)
            text = fonts.small.render(letter, True, COLOR_TEXT_MUTED)
            x = self.offset_x + c * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_width() // 2
            y = self.offset_y + BOARD_SIZE + 4
            surface.blit(text, (x, y))

        for r in range(8):
            number = str(8 - r)
            text = fonts.small.render(number, True, COLOR_TEXT_MUTED)
            x = self.offset_x - 16
            y = self.offset_y + r * SQUARE_SIZE + SQUARE_SIZE // 2 - text.get_height() // 2
            surface.blit(text, (x, y))

    def _get_square_rect(self, row, col) -> pygame.Rect:
        """Lấy Rect của ô (row, col)."""
        return pygame.Rect(
            self.offset_x + col * SQUARE_SIZE,
            self.offset_y + row * SQUARE_SIZE,
            SQUARE_SIZE, SQUARE_SIZE,
        )

    def get_square_from_pos(self, pos) -> tuple:
        """Chuyển tọa độ pixel sang (row, col). Trả về None nếu ngoài bàn cờ."""
        mx, my = pos
        col = (mx - self.offset_x) // SQUARE_SIZE
        row = (my - self.offset_y) // SQUARE_SIZE
        if 0 <= row <= 7 and 0 <= col <= 7:
            return (row, col)
        return None
