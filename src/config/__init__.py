import math

# =============================================
# UI Constants
# =============================================
BUTTON_WIDTH = 3
BUTTON_HEIGHT = 1
BUTTON_IMAGE_SIZE = 36

PADX = 10
PADY = 10

PRIMARY_FONT = ('Segoe UI', 12)
SECONDARY_FONT = ('Segoe UI', 10)

WINDOW_BG = '#00004d'
PRESSED_BG = WINDOW_BG
ITEM_BG = '#dddddd'

TEXT_COLOR = 'black'
LABEL_TEXT_COLOR = ITEM_BG
DISABLED_TEXT_COLOR = 'gray40'

DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 600

# =============================================
# Color Constants
# =============================================
CANVAS_BG = WINDOW_BG
WORD_BG = WINDOW_BG
SYLLABLE_BG = '#101060'

WORD_COLOR = ITEM_BG
SYLLABLE_COLOR = '#cccccc'
VOWEL_COLOR = ITEM_BG
DOT_COLOR = VOWEL_COLOR

# =============================================
# Scaling and Geometry Constants
# =============================================
SYLLABLE_INITIAL_SCALE_MIN = 0.6
SYLLABLE_INITIAL_SCALE_MAX = 0.8
SYLLABLE_SCALE_MIN = 0.3
SYLLABLE_SCALE_MAX = 0.85

INNER_CIRCLE_INITIAL_SCALE_MIN = 0.4
INNER_CIRCLE_INITIAL_SCALE_MAX = 0.6
INNER_CIRCLE_SCALE_MIN = 0.2
INNER_CIRCLE_SCALE_MAX = 0.7

DIGIT_SCALE_MIN = 0.6
DIGIT_SCALE_MAX = 1.2

OUTER_CIRCLE_SCALE_MIN = 1.2
OUTER_CIRCLE_SCALE_MAX = 2

# =============================================
# Radius and Distance Constants
# =============================================
DEFAULT_WORD_RADIUS = 200
DEFAULT_DOT_RADIUS = DEFAULT_WORD_RADIUS / 20
MIN_RADIUS = 1

DEFAULT_HALF_LINE_DISTANCE = 8
MIN_HALF_LINE_DISTANCE = 2

WORD_IMAGE_RADIUS = math.ceil((DEFAULT_WORD_RADIUS * OUTER_CIRCLE_SCALE_MAX
                               + 4 * DEFAULT_HALF_LINE_DISTANCE) * SYLLABLE_SCALE_MAX)
SYLLABLE_IMAGE_RADIUS = math.ceil((DEFAULT_WORD_RADIUS
                                   + 4 * DEFAULT_HALF_LINE_DISTANCE) * SYLLABLE_SCALE_MAX)

# =============================================
# Line Width Constants
# =============================================
LINE_WIDTHS = {'1': 3, '2': 8}
MIN_LINE_WIDTH = {'1': 1, '2': 2}

# =============================================
# Animation
# =============================================
CYCLE_MIN = 10
CYCLE_MAX = 360
CYCLE_DEFAULT = 180
CYCLE_STEP = 10

DELAY_MIN = 100
DELAY_MAX = 500
DELAY_DEFAULT = 100
DELAY_STEP = 50

# =============================================
# Miscellaneous Constants
# =============================================
ALEPH = 'א'  # Hebrew Aleph letter
SEPARATOR = '|'
SPACE = ' '
MINUS_SIGN = '-'
