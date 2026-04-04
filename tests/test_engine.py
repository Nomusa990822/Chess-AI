"""
Tests for the core chess engine:
- initial position
- move generation
- move making / undo
- promotion
- en passant
- castling rights
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine import GameState, Move, CastleRights


def test_initial_position_has_legal_moves():
    """
    The starting position should generate legal moves.
    In standard chess, the opening position has 20 legal moves.
    """
    gs = GameState()
    moves = gs.get_valid_moves()

    assert len(moves) == 20


def test_make_move_updates_board_correctly():
    """
    Making a basic move should update the board and move log.
    Example: e2e4
    """
    gs = GameState()

    move = Move((6, 4), (4, 4), gs.board)  # e2 -> e4
    gs.make_move(move)

    assert gs.board[6][4] == "--"
    assert gs.board[4][4] == "wP"
    assert len(gs.move_log) == 1
    assert gs.white_to_move is False


def test_undo_move_restores_board_correctly():
    """
    Undoing a move should restore the previous board state.
    """
    gs = GameState()
    original_board = [row[:] for row in gs.board]

    move = Move((6, 4), (4, 4), gs.board)  # e2 -> e4
    gs.make_move(move)
    gs.undo_move()

    assert gs.board == original_board
    assert len(gs.move_log) == 0
    assert gs.white_to_move is True


def test_white_pawn_promotion_to_queen():
    """
    A white pawn reaching the last rank should promote.
    """
    gs = GameState()

    # Clear board
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    # Place kings so the position remains valid
    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"
    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 4)

    # Place white pawn on a7
    gs.board[1][0] = "wP"

    move = Move((1, 0), (0, 0), gs.board, promotion_choice="Q")
    gs.make_move(move)

    assert gs.board[0][0] == "wQ"
    assert move.is_pawn_promotion is True


def test_black_pawn_promotion_to_knight():
    """
    A black pawn reaching the last rank should promote correctly.
    """
    gs = GameState()

    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"
    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 4)

    gs.board[6][7] = "bP"
    gs.white_to_move = False

    move = Move((6, 7), (7, 7), gs.board, promotion_choice="N")
    gs.make_move(move)

    assert gs.board[7][7] == "bN"
    assert move.is_pawn_promotion is True


def test_en_passant_is_generated():
    """
    Test whether en passant becomes available after a double pawn move.
    """
    gs = GameState()

    # Clear board
    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    # Kings
    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"
    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 4)

    # White pawn on e5, black pawn on d7
    gs.board[3][4] = "wP"  # e5
    gs.board[1][3] = "bP"  # d7

    gs.white_to_move = False

    # Black plays d7d5
    black_move = Move((1, 3), (3, 3), gs.board)
    gs.make_move(black_move)

    # White should now have en passant e5xd6
    valid_moves = gs.get_valid_moves()
    en_passant_moves = [m for m in valid_moves if m.is_en_passant_move]

    assert len(en_passant_moves) == 1
    assert en_passant_moves[0].start_row == 3
    assert en_passant_moves[0].start_col == 4
    assert en_passant_moves[0].end_row == 2
    assert en_passant_moves[0].end_col == 3


def test_en_passant_execution():
    """
    Executing en passant should remove the captured pawn correctly.
    """
    gs = GameState()

    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    gs.board[7][4] = "wK"
    gs.board[0][4] = "bK"
    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 4)

    gs.board[3][4] = "wP"  # e5
    gs.board[3][3] = "bP"  # d5
    gs.white_to_move = True
    gs.en_passant_possible = (2, 3)
    gs.en_passant_possible_log = [(), (2, 3)]

    move = Move((3, 4), (2, 3), gs.board, is_en_passant_move=True)
    gs.make_move(move)

    assert gs.board[3][4] == "--"
    assert gs.board[3][3] == "--"
    assert gs.board[2][3] == "wP"


def test_castling_rights_removed_after_king_move():
    """
    Moving the king should remove both castling rights for that side.
    """
    gs = GameState()

    move = Move((7, 4), (6, 4), gs.board)  # White king moves e1 -> e2
    gs.make_move(move)

    assert gs.current_castling_rights.wks is False
    assert gs.current_castling_rights.wqs is False


def test_castling_rights_removed_after_rook_move():
    """
    Moving a rook should remove the relevant castling right.
    """
    gs = GameState()

    # Clear path not needed for rights test; just move rook directly
    gs.board[6][0] = "--"  # clear a2 so rook can move conceptually
    move = Move((7, 0), (6, 0), gs.board)  # rook a1 -> a2
    gs.make_move(move)

    assert gs.current_castling_rights.wqs is False


def test_kingside_castle_move_is_generated():
    """
    If path is clear and squares are safe, kingside castling should be legal.
    """
    gs = GameState()

    gs.board = [["--" for _ in range(8)] for _ in range(8)]

    # White pieces
    gs.board[7][4] = "wK"
    gs.board[7][7] = "wR"
    gs.white_king_location = (7, 4)

    # Black king
    gs.board[0][4] = "bK"
    gs.black_king_location = (0, 4)

    gs.current_castling_rights = CastleRights(True, False, False, False)
    gs.castle_rights_log = [gs.current_castling_rights.copy()]
    gs.white_to_move = True

    valid_moves = gs.get_valid_moves()
    castle_moves = [m for m in valid_moves if m.is_castle_move]

    assert len(castle_moves) == 1
    assert castle_moves[0].end_col == 6  # g1


def test_draw_by_repetition_flag():
    """
    Repeating the same position three times should trigger repetition draw.
    """
    gs = GameState()

    # Repeat a knight shuffle
    move1 = Move((7, 6), (5, 5), gs.board)  # g1f3
    move2 = Move((0, 6), (2, 5), gs.board)  # g8f6
    move3 = Move((5, 5), (7, 6), gs.board)  # f3g1
    move4 = Move((2, 5), (0, 6), gs.board)  # f6g8

    for _ in range(3):
        gs.make_move(move1)
        gs.make_move(move2)
        gs.make_move(move3)
        gs.make_move(move4)

    gs.update_game_status()
    assert gs.draw_by_repetition is True
