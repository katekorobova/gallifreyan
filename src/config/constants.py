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
CANVAS_BG = 'black'  # 'white'
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600

# ==========================
# Color Constants
# ==========================
WORD_BG = 'black'
SYLLABLE_BG = 'black'

WORD_COLOR = '#91a2ff'
SYLLABLE_COLOR = '#af92ff'
VOWEL_COLOR = '#d1ceff'
DOT_COLOR = VOWEL_COLOR

# ==========================
# Scaling and Geometry Constants
# ==========================
WORD_INITIAL_POSITION = (300, 300)

SYLLABLE_INITIAL_SCALE_MIN = 0.6
SYLLABLE_INITIAL_SCALE_MAX = 0.8
SYLLABLE_SCALE_MIN = 0.3
SYLLABLE_SCALE_MAX = 0.85

INNER_CIRCLE_INITIAL_SCALE_MIN = 0.4
INNER_CIRCLE_INITIAL_SCALE_MAX = 0.6
INNER_CIRCLE_SCALE_MIN = 0.2
INNER_CIRCLE_SCALE_MAX = 0.7

OUTER_CIRCLE_SCALE_MIN = 1.2
OUTER_CIRCLE_SCALE_MAX = 2

# ==========================
# Radius and Distance Constants
# ==========================
DEFAULT_WORD_RADIUS = 200
DEFAULT_DOT_RADIUS = DEFAULT_WORD_RADIUS / 20
MIN_RADIUS = 1

DEFAULT_HALF_LINE_DISTANCE = 8
MIN_HALF_LINE_DISTANCE = 2

WORD_IMAGE_RADIUS = math.ceil(
    (DEFAULT_WORD_RADIUS * OUTER_CIRCLE_SCALE_MAX + 4 * DEFAULT_HALF_LINE_DISTANCE) * SYLLABLE_SCALE_MAX)
SYLLABLE_IMAGE_RADIUS = math.ceil((DEFAULT_WORD_RADIUS + 4 * DEFAULT_HALF_LINE_DISTANCE) * SYLLABLE_SCALE_MAX)

# ==========================
# Line Width Constants
# ==========================
LINE_WIDTHS = {'1': 3, '2': 8}
MIN_LINE_WIDTH = {'1': 1, '2': 2}

# ==========================
# Animation
# ==========================
CYCLE = 180
DELAY = 100

# ==========================
# Miscellaneous Constants
# ==========================
ALEPH = 'א'  # Hebrew Aleph letter
SEPARATOR = '-'
SPACE = ' '
