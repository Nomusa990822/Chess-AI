"""
Shared constants used across the Chess AI project.
"""

# Board dimensions
BOARD_ROWS = 8
BOARD_COLS = 8

# Colors / sides
WHITE = "w"
BLACK = "b"

# Empty square marker
EMPTY = "--"

# Search score constants
CHECKMATE_SCORE = 9999
STALEMATE_SCORE = 0
INFINITY = float("inf")

# Piece values
PIECE_VALUES = {
    "K": 0.0,
    "Q": 9.0,
    "R": 5.0,
    "B": 3.25,
    "N": 3.0,
    "P": 1.0
}

# Evaluation weights by mode
EVALUATION_WEIGHTS = {
    "fair": {
        "material": 1.0,
        "piece_square": 0.6,
        "center_control": 0.4,
        "pawn_structure": 0.4,
        "mobility": 0.0,
        "king_activity": 0.0,
        "edge_pressure": 0.0
    },
    "hard": {
        "material": 1.0,
        "piece_square": 0.7,
        "center_control": 0.5,
        "pawn_structure": 0.6,
        "mobility": 0.8,
        "king_activity": 0.6,
        "edge_pressure": 0.0
    },
    "forced": {
        "material": 1.0,
        "piece_square": 0.7,
        "center_control": 0.4,
        "pawn_structure": 0.5,
        "mobility": 0.9,
        "king_activity": 0.9,
        "edge_pressure": 1.2
    }
}

# Board region definitions
CENTER_SQUARES = {
    (3, 3), (3, 4),
    (4, 3), (4, 4)
}

EXTENDED_CENTER = {
    (2, 2), (2, 3), (2, 4), (2, 5),
    (3, 2), (3, 3), (3, 4), (3, 5),
    (4, 2), (4, 3), (4, 4), (4, 5),
    (5, 2), (5, 3), (5, 4), (5, 5)
}

# ANSI terminal colors
ANSI_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "reset": "\033[0m"
}
