"""
forced_positions.py

Preset positions for Forced-Win mode.
"""

from engine import GameState, CastleRights


def clear_board():
    return [["--" for _ in range(8)] for _ in range(8)]


def get_forced_position(name="kqk_black_to_move"):
    """
    Return a GameState initialized to a forced-win position.

    Available:
    - kqk_black_to_move
    - krk_black_to_move
    - queen_up_endgame_black_to_move
    """
    gs = GameState()
    gs.board = clear_board()
    gs.move_log = []
    gs.en_passant_possible = ()
    gs.en_passant_possible_log = [()]
    gs.current_castling_rights = CastleRights(False, False, False, False)
    gs.castle_rights_log = [gs.current_castling_rights.copy()]
    gs.position_counts = {}

    if name == "kqk_black_to_move":
        # White: King on h1
        # Black: King on f3, Queen on g3
        # Black to move from a winning endgame structure
        gs.board[7][7] = "wK"   # h1
        gs.board[5][5] = "bK"   # f3
        gs.board[5][6] = "bQ"   # g3

        gs.white_king_location = (7, 7)
        gs.black_king_location = (5, 5)
        gs.white_to_move = False

    elif name == "krk_black_to_move":
        gs.board[7][7] = "wK"   # h1
        gs.board[5][5] = "bK"   # f3
        gs.board[4][7] = "bR"   # h4

        gs.white_king_location = (7, 7)
        gs.black_king_location = (5, 5)
        gs.white_to_move = False

    elif name == "queen_up_endgame_black_to_move":
        gs.board[7][6] = "wK"   # g1
        gs.board[6][5] = "wP"   # f2
        gs.board[0][6] = "bK"   # g8
        gs.board[1][4] = "bQ"   # e7
        gs.board[2][5] = "bP"   # f6

        gs.white_king_location = (7, 6)
        gs.black_king_location = (0, 6)
        gs.white_to_move = False

    else:
        raise ValueError(f"Unknown forced position: {name}")

    gs.record_current_position()
    return gs
