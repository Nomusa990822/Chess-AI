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
    ep_square = fields[3]
    if ep_square == "-":
        gs.en_passant_possible = ()
    else:
        files = "abcdefgh"
        ranks = "87654321"
        gs.en_passant_possible = (ranks.index(ep_square[1]), files.index(ep_square[0]))
    gs.en_passant_possible_log = [gs.en_passant_possible]
    for row in range(8):
        for col in range(8):
            if gs.board[row][col] == "wK":
                gs.white_king_location = (row, col)
            elif gs.board[row][col] == "bK":
                gs.black_king_location = (row, col)
    gs.position_counts = {}
    gs.record_current_position()
    return gs


def engine_move_uci(move):
    """Convert the engine coordinate move to UCI notation."""
    files = "abcdefgh"
    ranks = "87654321"
    start = files[move.start_col] + ranks[move.start_row]
    end = files[move.end_col] + ranks[move.end_row]
    promotion = move.promotion_choice.lower() if move.is_pawn_promotion else ""
    return start + end + promotion


def test_kiwipete_legal_moves_match_python_chess_oracle():
    """Compare root legal moves against an independent chess-rules implementation."""
    import chess

    fen = (
        "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/"
        "2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1"
    )
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}

    assert actual == expected, (
        f"Missing legal moves: {sorted(expected - actual)}; "
        f"unexpected moves: {sorted(actual - expected)}"
    )

def python_chess_perft(board, depth):
    """Independent recursive perft implementation using python-chess."""
    if depth == 0:
        return 1

    nodes = 0
    for move in list(board.legal_moves):
        board.push(move)
        try:
            nodes += python_chess_perft(board, depth - 1)
        finally:
            board.pop()
    return nodes


def test_complex_castling_position_matches_python_chess_perft():
    """Compare legal move-tree counts with an independent chess-rules oracle."""
    import chess

    fen = (
        "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/"
        "2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1"
    )
    gs = load_fen_position(fen)
    oracle = chess.Board(fen)

    for depth in (1, 2, 3):
        assert perft(gs, depth) == python_chess_perft(oracle, depth)



def test_castling_requires_original_rook_even_when_right_is_set():
    """Stale castling flags must not create a castle when the rook is absent."""
    import chess

    fen = "4k3/8/8/8/8/8/8/4K3 w KQ - 0 1"
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected
    assert "e1g1" not in actual and "e1c1" not in actual


def test_castling_requires_king_on_home_square():
    """A displaced king cannot castle using stale castling rights."""
    import chess

    fen = "4k3/8/8/8/8/8/4K3/7R w K - 0 1"
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected


def test_en_passant_that_exposes_own_king_is_rejected():
    """En passant must be filtered when removing both pawns opens a rook line."""
    import chess

    fen = "k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected
    assert "e5d6" not in actual


def test_all_promotion_choices_match_python_chess():
    """All four promotion choices must be represented in legal move generation."""
    import chess

    fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected
    assert {move[-1] for move in actual if move.startswith("a7a8")} == set("qrbn")


def test_black_to_move_complex_position_matches_python_chess():
    """The independent oracle must agree when the side to move is black."""
    import chess

    fen = (
        "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/"
        "2N2N2/PPQBBPPP/R3K2R b KQkq - 0 1"
    )
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected


def test_castling_through_attacked_transit_square_is_rejected():
    """A rook attack on f1 prevents white kingside castling."""
    import chess

    fen = "4kr2/8/8/8/8/8/8/4K2R w K - 0 1"
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected
    assert "e1g1" not in actual


def test_black_pawn_generates_all_four_promotion_choices():
    """Black promotions must offer queen, rook, bishop, and knight."""
    import chess

    fen = "4k3/8/8/8/8/8/7p/4K3 b - - 0 1"
    gs = load_fen_position(fen)
    expected = {move.uci() for move in chess.Board(fen).legal_moves}
    actual = {engine_move_uci(move) for move in gs.get_valid_moves()}
    assert actual == expected
    assert {move[-1] for move in actual if move.startswith("h2h1")} == set("qrbn")


def test_checkmate_and_stalemate_flags_match_terminal_fens():
    """Terminal-position classification must distinguish mate from stalemate."""
    mate = load_fen_position("7k/6Q1/5K2/8/8/8/8/8 b - - 0 1")
    assert mate.get_valid_moves() == []
    assert mate.checkmate is True
    assert mate.stalemate is False

    stalemate = load_fen_position("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert stalemate.get_valid_moves() == []
    assert stalemate.checkmate is False
    assert stalemate.stalemate is True
