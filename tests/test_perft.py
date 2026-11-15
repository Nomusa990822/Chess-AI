"""Reference perft tests for legal move generation.

Perft counts leaf nodes in the legal move tree. These tests do not evaluate
move quality; they detect move-generation and make/undo regressions.
"""

from engine import GameState


def perft(gs, depth):
    if depth == 0:
        return 1

    nodes = 0
    for move in gs.get_valid_moves():
        gs.make_move(move)
        try:
            nodes += perft(gs, depth - 1)
        finally:
            gs.undo_move()
    return nodes


def state_snapshot(gs):
    rights = gs.current_castling_rights
    return {
        "board": tuple(tuple(row) for row in gs.board),
        "white_to_move": gs.white_to_move,
        "move_log": tuple(move.move_id for move in gs.move_log),
        "white_king": gs.white_king_location,
        "black_king": gs.black_king_location,
        "en_passant": gs.en_passant_possible,
        "en_passant_log": tuple(gs.en_passant_possible_log),
        "castling": (rights.wks, rights.wqs, rights.bks, rights.bqs),
        "castling_log": tuple(
            (r.wks, r.wqs, r.bks, r.bqs) for r in gs.castle_rights_log
        ),
        "position_counts": dict(gs.position_counts),
    }


def test_initial_position_perft_reference_counts():
    """Standard initial-position reference counts: 20, 400, 8902."""
    gs = GameState()

    assert perft(gs, 1) == 20
    assert perft(gs, 2) == 400
    assert perft(gs, 3) == 8902


def test_perft_restores_complete_game_state():
    """A full recursive traversal must leave the supplied position unchanged."""
    gs = GameState()
    before = state_snapshot(gs)

    perft(gs, 3)

    assert state_snapshot(gs) == before


def load_fen_position(fen):
    """Load the board fields needed by perft fixtures without a runtime FEN dependency."""
    from engine import CastleRights

    gs = GameState()
    fields = fen.split()
    rows = []
    for fen_row in fields[0].split("/"):
        row = []
        for symbol in fen_row:
            if symbol.isdigit():
                row.extend(["--"] * int(symbol))
            else:
                color = "w" if symbol.isupper() else "b"
                row.append(color + symbol.upper())
        rows.append(row)

    gs.board = rows
    gs.white_to_move = fields[1] == "w"
    rights = fields[2]
    gs.current_castling_rights = CastleRights(
        "K" in rights, "Q" in rights, "k" in rights, "q" in rights
    )
    gs.castle_rights_log = [gs.current_castling_rights.copy()]
    gs.en_passant_possible = ()
    gs.en_passant_possible_log = [()]
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == "wK":
                gs.white_king_location = (row, col)
            elif gs.board[row][col] == "bK":
                gs.black_king_location = (row, col)
    gs.position_counts = {}
    gs.record_current_position()
    return gs


def test_kiwipete_perft_castling_and_tactical_legality():
    """Kiwipete reference counts exercise castling and complex legal move filtering."""
    gs = load_fen_position(
        "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1"
    )

    root_moves = gs.get_valid_moves()
    assert len(root_moves) == 48, sorted(m.get_chess_notation() for m in root_moves)
    assert perft(gs, 2) == 2039
