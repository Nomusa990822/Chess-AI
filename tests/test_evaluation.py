"""
Full evaluation test suite for the Chess AI project.

Covers:
- initial balance
- material scoring
- game phase detection
- center control
- pawn structure
- bishop pair
- rook file bonuses
- rook on 7th rank
- knight outposts
- king pawn shield
- forced-win style evaluation
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
    pawn_structure_score,
    bishop_pair_bonus,
    rook_file_bonus,
    rook_seventh_rank_bonus,
    knight_outpost_bonus,
    king_pawn_shield_score
)


def empty_board_with_kings():
    """
    Helper function:
    returns an otherwise empty legal position with only kings.
    """
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"

    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 4)

    gs.white_to_move = True
    return gs


# =========================================================
# BASIC EVALUATION TESTS
# =========================================================

def test_initial_position_is_balanced():
    """
    The initial chess position should be roughly balanced.
    """
    gs = GameState()
    score = evaluate_position(gs, mode="fair")

    assert abs(score) < 2.0


def test_extra_white_queen_increases_score():
    """
    Giving White an extra queen should strongly increase the evaluation.
    """
    gs = GameState()
    gs.board[4][4] = "wQ"

    score = evaluate_position(gs, mode="fair")
    assert score > 7.0


def test_extra_black_queen_decreases_score():
    """
    Giving Black an extra queen should strongly decrease the evaluation.
    """
    gs = GameState()
    gs.board[4][4] = "bQ"

    score = evaluate_position(gs, mode="fair")
    assert score < -7.0


def test_material_score_detects_advantage():
    """
    Material score should reflect simple extra material.
    """
    gs = GameState()
    gs.board[4][4] = "wR"

    score = material_score(gs.board)
    assert score > 4.0


# =========================================================
# GAME PHASE TESTS
# =========================================================

def test_opening_phase_detected_in_start_position():
    """
    The starting position should be classified as opening.
    """
    gs = GameState()
    phase = get_game_phase(gs.board)

    assert phase == "opening"


def test_endgame_phase_detected_on_sparse_board():
    """
    A board with only kings should be classified as endgame.
    """
    gs = empty_board_with_kings()
    phase = get_game_phase(gs.board)

    assert phase == "endgame"


# =========================================================
# CENTER CONTROL TESTS
# =========================================================

def test_center_control_improves_score_for_white():
    """
    A white piece in the center should produce a positive center score.
    """
    gs = empty_board_with_kings()
    gs.board[3][3] = "wN"

    score = center_control_score(gs.board)
    assert score > 0


def test_center_control_improves_score_for_black_negative():
    """
    A black piece in the center should produce a negative center score
    from White's perspective.
    """
    gs = empty_board_with_kings()
    gs.board[3][3] = "bN"

    score = center_control_score(gs.board)
    assert score < 0


# =========================================================
# PAWN STRUCTURE TESTS
# =========================================================

def test_doubled_white_pawns_score_worse_than_single_white_pawn():
    """
    Doubled white pawns should score worse than a single white pawn
    on the same file.
    """
    gs_single = empty_board_with_kings()
    gs_single.board[6][0] = "wP"
    single_score = pawn_structure_score(gs_single.board)

    gs_doubled = empty_board_with_kings()
    gs_doubled.board[6][0] = "wP"
    gs_doubled.board[5][0] = "wP"
    doubled_score = pawn_structure_score(gs_doubled.board)

    assert doubled_score < single_score


def test_isolated_white_pawn_scores_worse_than_supported_white_pawn():
    """
    An isolated white pawn should score worse than one with friendly
    pawn support on an adjacent file.
    """
    gs_isolated = empty_board_with_kings()
    gs_isolated.board[6][3] = "wP"
    isolated_score = pawn_structure_score(gs_isolated.board)

    gs_supported = empty_board_with_kings()
    gs_supported.board[6][3] = "wP"
    gs_supported.board[6][4] = "wP"
    supported_score = pawn_structure_score(gs_supported.board)

    assert supported_score > isolated_score


def test_white_pawn_chain_scores_positive():
    """
    A white pawn chain should produce a positive structure bonus.
    """
    gs = empty_board_with_kings()

    # White pawn chain
    gs.board[5][3] = "wP"
    gs.board[6][2] = "wP"

    score = pawn_structure_score(gs.board)
    assert score > 0


def test_black_pawn_chain_scores_negative():
    """
    A black pawn chain should produce a negative structure score
    from White's perspective.
    """
    gs = empty_board_with_kings()

    gs.board[2][3] = "bP"
    gs.board[1][2] = "bP"

    score = pawn_structure_score(gs.board)
    assert score < 0


def test_advanced_passed_white_pawn_scores_better_than_less_advanced_one():
    """
    A more advanced passed white pawn should score better than one farther back.
    """
    gs_back = empty_board_with_kings()
    gs_back.board[6][0] = "wP"
    back_score = pawn_structure_score(gs_back.board)

    gs_advanced = empty_board_with_kings()
    gs_advanced.board[3][0] = "wP"
    advanced_score = pawn_structure_score(gs_advanced.board)

    assert advanced_score > back_score


# =========================================================
# BISHOP TESTS
# =========================================================

def test_bishop_pair_bonus_for_white():
    """
    White bishop pair should give a positive bishop-pair bonus.
    """
    gs = empty_board_with_kings()
    gs.board[6][2] = "wB"
    gs.board[6][5] = "wB"

    score = bishop_pair_bonus(gs.board)
    assert score > 0


def test_bishop_pair_bonus_for_black():
    """
    Black bishop pair should give a negative bishop-pair bonus
    from White's perspective.
    """
    gs = empty_board_with_kings()
    gs.board[1][2] = "bB"
    gs.board[1][5] = "bB"

    score = bishop_pair_bonus(gs.board)
    assert score < 0


def test_no_bishop_pair_no_bonus():
    """
    A single bishop should not trigger bishop-pair bonus.
    """
    gs = empty_board_with_kings()
    gs.board[6][2] = "wB"

    score = bishop_pair_bonus(gs.board)
    assert score == 0


# =========================================================
# ROOK TESTS
# =========================================================

def test_white_rook_on_open_file_gets_bonus():
    """
    White rook on a completely open file should receive a positive bonus.
    """
    gs = empty_board_with_kings()
    gs.board[4][0] = "wR"

    score = rook_file_bonus(gs.board)
    assert score > 0


def test_black_rook_on_open_file_gets_negative_bonus():
    """
    Black rook on a completely open file should reduce evaluation
    from White's perspective.
    """
    gs = empty_board_with_kings()
    gs.board[4][0] = "bR"

    score = rook_file_bonus(gs.board)
    assert score < 0


def test_white_rook_on_semi_open_file_gets_bonus():
    """
    White rook with no white pawn on file, but a black pawn present,
    should get a semi-open file bonus.
    """
    gs = empty_board_with_kings()
    gs.board[4][0] = "wR"
    gs.board[1][0] = "bP"

    score = rook_file_bonus(gs.board)
    assert score > 0


def test_rook_open_file_better_than_blocked_file():
    """
    A rook on an open file should score better than one blocked
    by its own pawn.
    """
    gs_open = empty_board_with_kings()
    gs_open.board[4][0] = "wR"
    open_score = rook_file_bonus(gs_open.board)

    gs_blocked = empty_board_with_kings()
    gs_blocked.board[4][0] = "wR"
    gs_blocked.board[6][0] = "wP"
    blocked_score = rook_file_bonus(gs_blocked.board)

    assert open_score > blocked_score


def test_white_rook_on_seventh_rank_bonus():
    """
    White rook on row 1 should receive a positive 7th-rank bonus.
    """
    gs = empty_board_with_kings()
    gs.board[1][3] = "wR"

    score = rook_seventh_rank_bonus(gs.board)
    assert score > 0


def test_black_rook_on_seventh_rank_bonus():
    """
    Black rook on row 6 should produce a negative bonus
    from White's perspective.
    """
    gs = empty_board_with_kings()
    gs.board[6][3] = "bR"

    score = rook_seventh_rank_bonus(gs.board)
    assert score < 0


# =========================================================
# KNIGHT TESTS
# =========================================================

def test_white_knight_outpost_bonus():
    """
    A supported white knight on an advanced square with no enemy pawn
    challenge should receive an outpost bonus.
    """
    gs = empty_board_with_kings()

    # White knight on d5
    gs.board[3][3] = "wN"

    # Supported by white pawn on c4
    gs.board[4][2] = "wP"

    score = knight_outpost_bonus(gs.board)
    assert score > 0


def test_black_knight_outpost_bonus():
    """
    A supported black knight on an advanced square with no enemy pawn
    challenge should receive an outpost bonus.
    """
    gs = empty_board_with_kings()

    gs.board[4][4] = "bN"
    gs.board[3][3] = "bP"

    score = knight_outpost_bonus(gs.board)
    assert score < 0


def test_knight_without_support_gets_no_outpost_bonus():
    """
    Unsupported knight should not receive an outpost bonus.
    """
    gs = empty_board_with_kings()
    gs.board[3][3] = "wN"

    score = knight_outpost_bonus(gs.board)
    assert score == 0


# =========================================================
# KING SAFETY TESTS
# =========================================================

def test_white_king_pawn_shield_bonus():
    """
    White king with a pawn shield should receive a positive king shield score.
    """
    gs = empty_board_with_kings()

    gs.board[7][6] = "wK"
    gs.board[7][4] = "--"
    gs.white_king_location = (7, 6)

    gs.board[6][5] = "wP"
    gs.board[6][6] = "wP"
    gs.board[6][7] = "wP"

    score = king_pawn_shield_score(gs, "middlegame")
    assert score > 0


def test_black_king_pawn_shield_bonus_negative():
    """
    Black king with a pawn shield should decrease evaluation
    from White's perspective.
    """
    gs = empty_board_with_kings()

    gs.board[0][6] = "bK"
    gs.board[0][4] = "--"
    gs.black_king_location = (0, 6)

    gs.board[1][5] = "bP"
    gs.board[1][6] = "bP"
    gs.board[1][7] = "bP"

    score = king_pawn_shield_score(gs, "middlegame")
    assert score < 0


def test_king_pawn_shield_not_counted_in_endgame():
    """
    Pawn shield should not matter in the endgame.
    """
    gs = empty_board_with_kings()

    gs.board[6][3] = "wP"
    gs.board[6][4] = "wP"
    gs.board[6][5] = "wP"

    score = king_pawn_shield_score(gs, "endgame")
    assert score == 0


# =========================================================
# FULL EVALUATION TESTS
# =========================================================

def test_forced_style_position_favors_black():
    """
    In a simple winning black endgame, evaluation should favor Black.
    """
    gs = empty_board_with_kings()

    gs.board[7][7] = "wK"
    gs.white_king_location = (7, 7)

    gs.board[5][5] = "bK"
    gs.board[5][6] = "bQ"
    gs.black_king_location = (5, 5)

    gs.white_to_move = False

    fair_score = evaluate_position(gs, mode="fair")
    forced_score = evaluate_position(gs, mode="forced")

    assert fair_score < 0
    assert forced_score < 0


def test_position_with_multiple_white_positional_strengths_scores_positive():
    """
    A position with several white positional advantages should score positively.
    """
    gs = empty_board_with_kings()

    # White bishop pair
    gs.board[6][2] = "wB"
    gs.board[6][5] = "wB"

    # White rook on open file
    gs.board[4][0] = "wR"

    # White knight outpost
    gs.board[3][3] = "wN"
    gs.board[4][2] = "wP"

    # White king shield
    gs.board[7][6] = "wK"
    gs.board[7][4] = "--"
    gs.white_king_location = (7, 6)
    gs.board[6][6] = "wP"
    gs.board[6][7] = "wP"

    score = evaluate_position(gs, mode="hard")
    assert score > 0


def test_position_with_multiple_black_positional_strengths_scores_negative():
    """
    A position with several black positional advantages should score negatively
    from White's perspective.
    """
    gs = empty_board_with_kings()

    # Black bishop pair
    gs.board[1][2] = "bB"
    gs.board[1][5] = "bB"

    # Black rook on open file
    gs.board[3][0] = "bR"

    # Black knight outpost
    gs.board[4][4] = "bN"
    gs.board[3][3] = "bP"

    # Black king shield
    gs.board[0][6] = "bK"
    gs.board[0][4] = "--"
    gs.black_king_location = (0, 6)
    gs.board[1][6] = "bP"
    gs.board[1][7] = "bP"

    score = evaluate_position(gs, mode="hard")
    assert score < 0
