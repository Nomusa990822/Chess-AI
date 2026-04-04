"""
Tests for forced-win preset positions.
"""

from forced_positions import get_forced_position


def test_kqk_black_to_move_loads_correctly():
    """
    Test the king + queen vs king position.
    """
    gs = get_forced_position("kqk_black_to_move")

    assert gs.board[7][7] == "wK"
    assert gs.board[5][5] == "bK"
    assert gs.board[5][6] == "bQ"

    assert gs.white_king_location == (7, 7)
    assert gs.black_king_location == (5, 5)
    assert gs.white_to_move is False


def test_krk_black_to_move_loads_correctly():
    """
    Test the king + rook vs king position.
    """
    gs = get_forced_position("krk_black_to_move")

    assert gs.board[7][7] == "wK"
    assert gs.board[5][5] == "bK"
    assert gs.board[4][7] == "bR"

    assert gs.white_king_location == (7, 7)
    assert gs.black_king_location == (5, 5)
    assert gs.white_to_move is False


def test_queen_up_endgame_black_to_move_loads_correctly():
    """
    Test a queen-up simplified endgame setup.
    """
    gs = get_forced_position("queen_up_endgame_black_to_move")

    assert gs.board[7][6] == "wK"
    assert gs.board[6][5] == "wP"
    assert gs.board[0][6] == "bK"
    assert gs.board[1][4] == "bQ"
    assert gs.board[2][5] == "bP"

    assert gs.white_king_location == (7, 6)
    assert gs.black_king_location == (0, 6)
    assert gs.white_to_move is False


def test_forced_positions_disable_castling_rights():
    """
    Forced positions should not allow castling.
    """
    gs = get_forced_position("kqk_black_to_move")

    rights = gs.current_castling_rights
    assert rights.wks is False
    assert rights.wqs is False
    assert rights.bks is False
    assert rights.bqs is False


def test_forced_position_has_only_expected_pieces():
    """
    KQK setup should contain exactly:
    - White king
    - Black king
    - Black queen
    """
    gs = get_forced_position("kqk_black_to_move")

    pieces = []
    for row in gs.board:
        for piece in row:
            if piece != "--":
                pieces.append(piece)

    assert sorted(pieces) == sorted(["wK", "bK", "bQ"])


def test_unknown_forced_position_raises_error():
    """
    Requesting an unknown forced position should raise ValueError.
    """
    try:
        get_forced_position("not_a_real_position")
        assert False, "Expected ValueError for invalid position name"
    except ValueError:
        assert True


def test_forced_position_can_generate_moves():
    """
    The loaded forced position should still be playable and generate legal moves.
    """
    gs = get_forced_position("kqk_black_to_move")
    moves = gs.get_valid_moves()

    assert len(moves) > 0
