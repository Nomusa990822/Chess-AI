"""
Preset positions for Forced-Win mode.
"""

from engine import GameState, CastleRights


def clear_board():
    return [["--" for _ in range(8)] for _ in range(8)]


def get_forced_position(name="kqk_black_to_move"):
    """
    Return a GameState initialized to a forced-win position.
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
        # White king on h1
        # Black king on f3
        # Black queen on g3
        # Black to move
        gs.board[7][7] = "wK"
        gs.board[5][5] = "bK"
        gs.board[5][6] = "bQ"

        gs.white_king_location = (7, 7)
        gs.black_king_location = (5, 5)
        gs.white_to_move = False

    elif name == "krk_black_to_move":
        gs.board[7][7] = "wK"
        gs.board[5][5] = "bK"
        gs.board[4][7] = "bR"

        gs.white_king_location = (7, 7)
        gs.black_king_location = (5, 5)
        gs.white_to_move = False

    elif name == "queen_up_endgame_black_to_move":
        gs.board[7][6] = "wK"
        gs.board[6][5] = "wP"
        gs.board[0][6] = "bK"
        gs.board[1][4] = "bQ"
        gs.board[2][5] = "bP"

        gs.white_king_location = (7, 6)
        gs.black_king_location = (0, 6)
        gs.white_to_move = False

    else:
        raise ValueError(f"Unknown forced position: {name}")

    gs.record_current_position()
    return gs
