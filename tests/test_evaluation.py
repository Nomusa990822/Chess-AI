"""
Tests for the evaluation system:
- material advantage
- game phase detection
- center control
- forced-win style scoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine import GameState
from evaluation import (
    evaluate_position,
    get_game_phase,
    material_score,
    center_control_score,
    pawn_structure_score
)


def test_initial_position_is_balanced():
    """
    The starting position should be approximately balanced.
    """
    gs = GameState()
    score = evaluate_position(gs, mode="fair")

    assert abs(score) < 2.0


def test_extra_white_queen_increases_score():
    """
    Giving White an extra queen should increase the score strongly.
    """
    gs = GameState()
    gs.board[4][4] = "wQ"

    score = evaluate_position(gs, mode="fair")
    assert score > 7.0


def test_extra_black_queen_decreases_score():
    """
    Giving Black an extra queen should decrease the score strongly.
    """
    gs = GameState()
    gs.board[4][4] = "bQ"

    score = evaluate_position(gs, mode="fair")
    assert score < -7.0


def test_material_score_detects_advantage():
    """
    Material score should reflect simple piece advantage.
    """
    gs = GameState()

    # Add extra white rook
    gs.board[4][4] = "wR"
    score = material_score(gs.board)

    assert score > 4.0


def test_opening_phase_detected_in_start_position():
    """
    The starting position should be classified as opening.
    """
    gs = GameState()
    phase = get_game_phase(gs.board)

    assert phase == "opening"


def test_endgame_phase_detected_on_sparse_board():
    """
    A very sparse board should be classified as endgame.
    """
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"
    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 4)

    phase = get_game_phase(gs.board)
    assert phase == "endgame"


def test_center_control_improves_score_for_white():
    """
    Placing a white piece in the center should improve center control score.
    """
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"

    gs.board[3][3] = "wN"  # central square

    score = center_control_score(gs.board)
    assert score > 0


def test_center_control_improves_score_for_black_negative():
    """
    Placing a black piece in the center should shift score negatively.
    """
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"

    gs.board[3][3] = "bN"

    score = center_control_score(gs.board)
    assert score < 0


def test_pawn_structure_penalizes_doubled_white_pawns():
    """
    Doubled white pawns should reduce White's pawn structure score.
    """
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"

    gs.board[6][0] = "wP"
    gs.board[5][0] = "wP"

    score = pawn_structure_score(gs.board)
    assert score < 0


def test_forced_style_position_favors_black():
    """
    In a simple winning black endgame, evaluation should favor Black.
    """
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    # White king trapped-ish
    gs.board[7][7] = "wK"
    gs.white_king_location = (7, 7)

    # Black king and queen
    gs.board[5][5] = "bK"
    gs.board[5][6] = "bQ"
    gs.black_king_location = (5, 5)

    gs.white_to_move = False

    fair_score = evaluate_position(gs, mode="fair")
    forced_score = evaluate_position(gs, mode="forced")

    assert fair_score < 0
    assert forced_score < 0
