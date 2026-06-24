"""
gui/widgets.py
UI components tái sử dụng: Button, ProgressBar, BarChart, Panel.
Thiết kế premium với hover effects và animations.
"""

import pygame
from gui.constants import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_SURFACE, COLOR_SURFACE_HOVER,
    COLOR_BORDER, COLOR_BG, fonts,
)


class Button:
    """Nút bấm với hover effect và rounded corners."""

    def __init__(self, x, y, width, height, text,
                 color=COLOR_PRIMARY, hover_color=None,
                 text_color=COLOR_TEXT, border_radius=8):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color or tuple(max(0, c - 18) for c in color)
        self.text_color = text_color
        self.border_radius = border_radius
        self.is_hovered = False
        self.enabled = True

    def draw(self, surface):
        font = fonts.body

        color = self.hover_color if self.is_hovered and self.enabled else self.color
        if not self.enabled:
            color = tuple(max(0, c - 60) for c in self.color)

        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 40), shadow_surf.get_rect(),
                         border_radius=self.border_radius)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Button body
        pygame.draw.rect(surface, color, self.rect,
                         border_radius=self.border_radius)

        # Border highlight on hover
        if self.is_hovered and self.enabled:
            pygame.draw.rect(surface, COLOR_PRIMARY_LIGHT, self.rect,
                             width=2, border_radius=self.border_radius)

        # Text
        text_color = self.text_color if self.enabled else COLOR_TEXT_MUTED
        if font:
            text_surf = font.render(self.text, True, text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    def handle_event(self, event) -> bool:
        """Returns True if button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.enabled:
                return True
        return False


class ProgressBar:
    """Thanh progress bar với animation."""

    def __init__(self, x, y, width, height, color=COLOR_PRIMARY):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.progress = 0.0  # 0.0 - 1.0
        self.text = ""
        self._display_progress = 0.0  # For smooth animation

    def set_progress(self, value, text=""):
        self.progress = max(0.0, min(1.0, value))
        self.text = text

    def draw(self, surface):
        # Smooth animation
        diff = self.progress - self._display_progress
        self._display_progress += diff * 0.15

        # Background track
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, border_radius=4)

        # Fill
        if self._display_progress > 0:
            fill_width = int(self.rect.width * self._display_progress)
            fill_rect = pygame.Rect(self.rect.x, self.rect.y,
                                     fill_width, self.rect.height)
            pygame.draw.rect(surface, self.color, fill_rect, border_radius=4)

        # Text
        if self.text and fonts.small:
            text_surf = fonts.small.render(self.text, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

        # Percentage
        if fonts.small:
            pct_text = f"{self._display_progress * 100:.0f}%"
            pct_surf = fonts.small.render(pct_text, True, COLOR_TEXT_MUTED)
            surface.blit(pct_surf, (self.rect.right + 8, self.rect.y))


class BarChart:
    """Biểu đồ bar chart cho benchmark."""

    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.data = []  # List of {"label": str, "value": float, "color": tuple}
        self.title = ""

    def set_data(self, data, title=""):
        self.data = data
        self.title = title

    def draw(self, surface):
        if not self.data:
            return

        # Title
        if self.title and fonts.label:
            title_surf = fonts.label.render(self.title, True, COLOR_TEXT)
            surface.blit(title_surf, (self.rect.x, self.rect.y))

        max_val = max((d["value"] for d in self.data), default=1)
        if max_val == 0:
            max_val = 1

        bar_height = 24
        gap = 8
        label_width = 90
        value_width = 80
        bar_area_width = self.rect.width - label_width - value_width - 20

        start_y = self.rect.y + 25

        for i, item in enumerate(self.data):
            y = start_y + i * (bar_height + gap)

            # Label
            if fonts.small:
                label_surf = fonts.small.render(item["label"], True, COLOR_TEXT_MUTED)
                label_rect = label_surf.get_rect(right=self.rect.x + label_width - 5,
                                                  centery=y + bar_height // 2)
                surface.blit(label_surf, label_rect)

            # Bar track
            track_rect = pygame.Rect(self.rect.x + label_width, y,
                                      bar_area_width, bar_height)
            pygame.draw.rect(surface, COLOR_SURFACE, track_rect, border_radius=4)

            # Bar fill
            fill_pct = item["value"] / max_val
            fill_width = max(2, int(bar_area_width * fill_pct))
            fill_rect = pygame.Rect(self.rect.x + label_width, y,
                                     fill_width, bar_height)
            pygame.draw.rect(surface, item["color"], fill_rect, border_radius=4)

            # Value text
            if fonts.small:
                fmt_val = item.get("formatted", f"{item['value']:.1f}")
                val_surf = fonts.small.render(fmt_val, True, COLOR_TEXT)
                val_rect = val_surf.get_rect(
                    left=self.rect.x + label_width + bar_area_width + 8,
                    centery=y + bar_height // 2,
                )
                surface.blit(val_surf, val_rect)


class Panel:
    """Panel nền với border và rounded corners."""

    def __init__(self, x, y, width, height, title="",
                 bg_color=COLOR_SURFACE, border_color=COLOR_BORDER):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.bg_color = bg_color
        self.border_color = border_color

    def draw(self, surface):
        # Shadow
        shadow = self.rect.copy()
        shadow.x += 3
        shadow.y += 3
        shadow_surf = pygame.Surface((shadow.w, shadow.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (5, 5, 15, 120), shadow_surf.get_rect(),
                         border_radius=12)
        surface.blit(shadow_surf, shadow.topleft)

        # Background
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=12)

        # Border
        pygame.draw.rect(surface, self.border_color, self.rect,
                         width=1, border_radius=12)

        # Title
        if self.title and fonts.heading:
            title_surf = fonts.heading.render(self.title, True, COLOR_PRIMARY)
            surface.blit(title_surf, (self.rect.x + 16, self.rect.y + 12))


def draw_text(surface, text, pos, font=None, color=COLOR_TEXT, center=False):
    """Helper vẽ text."""
    if font is None:
        font = fonts.body
    if font is None:
        return
    text_surf = font.render(str(text), True, color)
    if center:
        rect = text_surf.get_rect(center=pos)
        surface.blit(text_surf, rect)
    else:
        surface.blit(text_surf, pos)
