import math

# ==========================
# UI Constants
# ==========================
BUTTON_WIDTH = 3
BUTTON_HEIGHT = 1
BUTTON_IMAGE_SIZE = 36

PADX = 10
PADY = 10

FONT = ('Segoe UI', 14)
WINDOW_BG = 'midnightblue'
BUTTON_BG = '#11114D'
CANVAS_BG = 'white'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
MENU_BAR_HEIGHT = 22

# ==========================
# Color Constants (RGBA)
# ==========================
SYLLABLE_BG = (150, 150, 255, 200)
WORD_BG = (200, 220, 255, 255)
SYLLABLE_COLOR = (34, 42, 131, 255)
WORD_COLOR = (0, 50, 150, 255)

# ==========================
# Scaling and Geometry Constants
# ==========================
WORD_INITIAL_POSITION = (300, 300)

WORD_INITIAL_SCALE_MIN = 0.8
WORD_SCALE_MIN = 0.3

SYLLABLE_INITIAL_SCALE_MIN = 0.8
SYLLABLE_INITIAL_SCALE_MAX = 0.8
SYLLABLE_SCALE_MIN = 0.3
SYLLABLE_SCALE_MAX = 0.85

INNER_INITIAL_SCALE_MIN = 0.5
INNER_INITIAL_SCALE_MAX = 0.5
INNER_SCALE_MIN = 0.2
INNER_SCALE_MAX = 0.7

# ==========================
# Radius and Distance Constants
# ==========================
OUTER_CIRCLE_RADIUS = 200
HALF_LINE_DISTANCE = 8
MIN_HALF_LINE_DISTANCE = 2
MIN_RADIUS = 1

WORD_IMAGE_RADIUS = OUTER_CIRCLE_RADIUS + 4 * HALF_LINE_DISTANCE
SYLLABLE_IMAGE_RADIUS = math.ceil(OUTER_CIRCLE_RADIUS * SYLLABLE_SCALE_MAX) + 4 * HALF_LINE_DISTANCE

DOT_RADIUS = OUTER_CIRCLE_RADIUS / 20
MIN_DOT_RADIUS = 0

# ==========================
# Line Width Constants
# ==========================
LINE_WIDTHS = {'1': 4, '2': 10}
MIN_LINE_WIDTH = {'1': 1, '2': 2}

# ==========================
# Miscellaneous Constants
# ==========================
ALEPH = 'א'  # Hebrew Aleph letter
