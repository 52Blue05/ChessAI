"""
gui/constants.py
Hằng số thiết kế cho giao diện desktop Chess AI.
Màu sắc, kích thước, font — thiết kế premium dark theme.
"""

import pygame

# ==============================================================
# Window
# ==============================================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 750
FPS = 60
TITLE = "Chess AI"

# ==============================================================
# Board
# ==============================================================
BOARD_SIZE = 560          # px — bàn cờ vuông
SQUARE_SIZE = BOARD_SIZE // 8  # 70px
BOARD_OFFSET_X = 40
BOARD_OFFSET_Y = 90

# ==============================================================
# Colors — Premium dark theme
# ==============================================================
# Background
COLOR_BG = (15, 15, 35)
COLOR_SURFACE = (26, 26, 46)
COLOR_SURFACE_HOVER = (37, 37, 74)
COLOR_BORDER = (45, 45, 80)

# Primary / Accent
COLOR_PRIMARY = (108, 99, 255)
COLOR_PRIMARY_HOVER = (90, 82, 213)
COLOR_PRIMARY_LIGHT = (140, 133, 255)
COLOR_ACCENT = (255, 107, 107)
COLOR_SUCCESS = (81, 207, 102)
COLOR_WARNING = (255, 212, 59)

# Text
COLOR_TEXT = (228, 228, 240)
COLOR_TEXT_MUTED = (136, 136, 170)
COLOR_TEXT_DARK = (60, 60, 90)

# Board squares
COLOR_BOARD_LIGHT = (240, 217, 181)
COLOR_BOARD_DARK = (181, 136, 99)

# Bar chart colors
COLOR_GREEDY = (81, 207, 102)
COLOR_MINIMAX = (108, 99, 255)
COLOR_MCTS = (255, 107, 107)

ALGO_COLORS = {
    "greedy": COLOR_GREEDY,
    "minimax": COLOR_MINIMAX,
    "mcts": COLOR_MCTS,
}

ALGO_LABELS = {
    "greedy": "Greedy (Tham lam)",
    "minimax": "Minimax + Alpha-Beta",
    "mcts": "MCTS (Monte Carlo)",
}

# ==============================================================
# Chess piece Unicode symbols
# ==============================================================
PIECE_SYMBOLS = {
    ("king", "white"): "\u2654", ("queen", "white"): "\u2655",
    ("rook", "white"): "\u2656", ("bishop", "white"): "\u2657",
    ("knight", "white"): "\u2658", ("pawn", "white"): "\u2659",
    ("king", "black"): "\u265a", ("queen", "black"): "\u265b",
    ("rook", "black"): "\u265c", ("bishop", "black"): "\u265d",
    ("knight", "black"): "\u265e", ("pawn", "black"): "\u265f",
}


# ==============================================================
# Fonts — stored in a mutable container so all importers
# see the same updated references after init_fonts().
# ==============================================================
class Fonts:
    """Container for fonts initialized after pygame.init()."""
    title = None
    heading = None
    body = None
    small = None
    piece = None
    label = None
    mono = None

fonts = Fonts()

def init_fonts():
    """Khởi tạo font sau khi pygame.init() được gọi."""
    fonts.title = pygame.font.SysFont("Segoe UI", 36, bold=True)
    fonts.heading = pygame.font.SysFont("Segoe UI", 22, bold=True)
    fonts.body = pygame.font.SysFont("Segoe UI", 16)
    fonts.small = pygame.font.SysFont("Segoe UI", 13)
    fonts.label = pygame.font.SysFont("Segoe UI", 14, bold=True)
    fonts.piece = pygame.font.SysFont("Segoe UI Symbol", 44)
    fonts.mono = pygame.font.SysFont("Consolas", 14)
