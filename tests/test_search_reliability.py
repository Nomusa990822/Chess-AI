"""Regression tests for search timeout safety and quiescence check evasions."""

import os
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import ai
from engine import GameState, Move


def state_snapshot(gs):
    return {
        "board": [row[:] for row in gs.board],
        "white_to_move": gs.white_to_move,
        "move_log": list(gs.move_log),
        "white_king": gs.white_king_location,
        "black_king": gs.black_king_location,
        "ep": gs.en_passant_possible,
        "ep_log": list(gs.en_passant_possible_log),
        "rights": (
            gs.current_castling_rights.wks, gs.current_castling_rights.wqs,
            gs.current_castling_rights.bks, gs.current_castling_rights.bqs,
        ),
        "counts": dict(gs.position_counts),
    }


def test_choose_move_with_expired_deadline_keeps_legal_fallback():
    gs = GameState()
    moves = gs.get_valid_moves()
    move, info = ai.choose_ai_move(gs, moves, max_depth=4, time_budget=0)
    assert move in moves
    assert info["depth_reached"] == 0
    assert info["timed_out"] is True
    assert state_snapshot(gs) == state_snapshot(GameState())


def test_minimax_timeout_propagates_and_restores_board(monkeypatch):
    gs = GameState()
    before = state_snapshot(gs)
    move = gs.get_valid_moves()[0]
    gs.make_move(move)
    try:
        with pytest.raises(ai.SearchTimeout):
            ai.minimax(gs, 3, -float("inf"), float("inf"), gs.white_to_move,
                       "fair", {}, {"nodes": 0, "prunes": 0, "tt_hits": 0,
                                    "q_nodes": 0}, time.monotonic() - 1)
    finally:
        gs.undo_move()
    assert state_snapshot(gs) == before


def test_quiescence_in_check_searches_quiet_evasions(monkeypatch):
    gs = GameState()
    gs.board = [["--" for _ in range(8)] for _ in range(8)]
    gs.board[7][4] = "wK"
    gs.board[0][0] = "bK"
    gs.board[6][4] = "bR"
    gs.white_king_location = (7, 4)
    gs.black_king_location = (0, 0)
    gs.white_to_move = True
    before = state_snapshot(gs)
    moves = gs.get_valid_moves()
    assert moves
    assert any(not ai.is_tactical_move(m) for m in moves)

    searched = []
    original = ai.quiescence_search

    def recording_search(position, alpha, beta, maximizing, mode, stats, deadline,
                         q_depth=0, max_q_depth=8, ply=0):
        if q_depth == 1:
            searched.append(position.move_log[-1])
            return 0.0
        return original(position, alpha, beta, maximizing, mode, stats, deadline,
                        q_depth, max_q_depth, ply)

    monkeypatch.setattr(ai, "quiescence_search", recording_search)
    stats = {"q_nodes": 0, "prunes": 0}
    ai.quiescence_search(gs, -float("inf"), float("inf"), True, "fair",
                         stats, time.monotonic() + 5)
    assert searched
    assert any(not ai.is_tactical_move(m) for m in searched)
    assert state_snapshot(gs) == before


def test_interrupted_root_iteration_does_not_publish_partial_depth(monkeypatch):
    gs = GameState()
    moves = gs.get_valid_moves()
    original = ai.minimax
    calls = {"count": 0}

    def timeout_after_first_root(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise ai.SearchTimeout
        return 0.0, []

    monkeypatch.setattr(ai, "minimax", timeout_after_first_root)
    move, info = ai.choose_ai_move(gs, moves, max_depth=3, time_budget=5)
    assert move in moves
    assert info["depth_reached"] == 0
    assert info["completed_iterations"] == []
    assert info["timed_out"] is True
    assert state_snapshot(gs) == state_snapshot(GameState())
    monkeypatch.setattr(ai, "minimax", original)


def test_completed_iteration_is_preserved_when_next_depth_times_out(monkeypatch):
    gs = GameState()
    moves = gs.get_valid_moves()
    calls = {"count": 0}

    def controlled_search(*args, **kwargs):
        calls["count"] += 1
        # Depth one has 20 root calls. Interrupt the second iteration.
        if calls["count"] > len(moves) + 1:
            raise ai.SearchTimeout
        return float(calls["count"]), []

    monkeypatch.setattr(ai, "minimax", controlled_search)
    move, info = ai.choose_ai_move(gs, moves, max_depth=4, time_budget=5)
    assert move in moves
    assert info["depth_reached"] == 1
    assert info["completed_iterations"] == [1]
    assert info["timed_out"] is True


def test_transposition_key_distinguishes_halfmove_clocks():
    gs = GameState()
    same_position = GameState()
    same_position.halfmove_clock = 42
    assert gs.get_position_key() == same_position.get_position_key()
    assert ai._transposition_key(gs) != ai._transposition_key(same_position)


def test_transposition_key_distinguishes_repetition_histories():
    gs = GameState()
    alternate_history = GameState()
    shared_position = gs.get_position_key()
    alternate_history.position_counts[shared_position] = 2
    assert gs.get_position_key() == alternate_history.get_position_key()
    assert ai._transposition_key(gs) != ai._transposition_key(alternate_history)


def test_transposition_key_restores_after_make_undo():
    gs = GameState()
    original_key = ai._transposition_key(gs)
    move = gs.get_valid_moves()[0]
    gs.make_move(move)
    assert ai._transposition_key(gs) != original_key
    gs.undo_move()
    assert ai._transposition_key(gs) == original_key


def test_transposition_table_keeps_deeper_entry():
    table = {}
    shallow = ai.TranspositionEntry(2, 1.0, "EXACT", None, [])
    deep = ai.TranspositionEntry(5, 2.0, "LOWERBOUND", None, [])
    ai._store_tt_entry(table, "position", deep)
    ai._store_tt_entry(table, "position", shallow)
    assert table["position"] is deep


def test_transposition_table_prefers_exact_at_equal_depth():
    table = {}
    bound = ai.TranspositionEntry(4, 1.0, "LOWERBOUND", None, [])
    exact = ai.TranspositionEntry(4, 2.0, "EXACT", None, [])
    ai._store_tt_entry(table, "position", bound)
    ai._store_tt_entry(table, "position", exact)
    assert table["position"] is exact


def test_quiet_cutoff_move_is_promoted_by_killer_ordering():
    gs = GameState()
    quiet_moves = [move for move in gs.get_valid_moves()
                   if not ai.is_tactical_move(move)]
    assert len(quiet_moves) >= 2
    preferred = quiet_moves[-1]
    stats = {"killer_moves": {}, "history_scores": {}}
    ai._record_quiet_cutoff(gs, preferred, depth=3, ply=2, stats=stats)
    ordered = ai.order_moves(gs, quiet_moves, ply=2, stats=stats)
    assert ordered[0] == preferred
    assert stats["history_scores"][ai._quiet_history_key(gs, preferred)] == 9


def test_killer_history_state_does_not_mutate_game_position():
    gs = GameState()
    before = state_snapshot(gs)
    move = next(m for m in gs.get_valid_moves() if not ai.is_tactical_move(m))
    stats = {}
    ai._record_quiet_cutoff(gs, move, depth=2, ply=1, stats=stats)
    ai.order_moves(gs, gs.get_valid_moves(), ply=1, stats=stats)
    assert state_snapshot(gs) == before

@pytest.mark.parametrize("black_to_move", [False, True])
def test_pvs_matches_full_window_minimax_and_restores_state(black_to_move):
    gs = GameState()
    if black_to_move:
        gs.make_move(gs.get_valid_moves()[0])
    before = state_snapshot(gs)

    def search(use_pvs):
        stats = {
            "nodes": 0, "prunes": 0, "tt_hits": 0, "q_nodes": 0,
            "killer_moves": {}, "history_scores": {},
            "pvs_null_window_searches": 0, "pvs_researches": 0,
        }
        score, pv = ai.minimax(
            gs, 3, -float("inf"), float("inf"), gs.white_to_move,
            "fair", {}, stats, time.monotonic() + 30, use_pvs=use_pvs
        )
        return score, pv, stats

    reference_score, _, _ = search(False)
    pvs_score, pvs_line, pvs_stats = search(True)

    assert pvs_score == pytest.approx(reference_score, abs=1e-9)
    assert pvs_line
    assert pvs_stats["pvs_null_window_searches"] > 0
    assert state_snapshot(gs) == before


@pytest.mark.parametrize("fen", [
    # Complex middlegame with castling rights and tactical contact.
    "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1",
    # Black-to-move variant exercises the minimizing root.
    "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R b KQkq - 0 1",
    # Sparse pawn ending with kings and a passed-pawn race potential.
    "8/5pk1/6p1/8/3P4/5K2/8/8 w - - 0 1",
])
def test_pvs_matches_full_window_and_returns_legal_principal_variation(fen):
    from tests.test_perft import load_fen_position

    gs = load_fen_position(fen)
    before = state_snapshot(gs)

    def search(use_pvs):
        stats = {
            "nodes": 0, "prunes": 0, "tt_hits": 0, "q_nodes": 0,
            "killer_moves": {}, "history_scores": {},
            "pvs_null_window_searches": 0, "pvs_researches": 0,
        }
        score, pv = ai.minimax(
            gs, 2, -float("inf"), float("inf"), gs.white_to_move,
            "fair", {}, stats, time.monotonic() + 60, use_pvs=use_pvs
        )
        return score, pv, stats

    reference_score, _, _ = search(False)
    pvs_score, pv, pvs_stats = search(True)

    assert pvs_score == pytest.approx(reference_score, abs=1e-9)
    assert pv, "PVS must return a principal variation for a non-terminal position"

    # Replay every reported PV move against the live legal-move generator.
    for uci in pv:
        legal_by_notation = {move.get_chess_notation(): move for move in gs.get_valid_moves()}
        assert uci in legal_by_notation, f"PVS returned illegal PV move {uci} in {fen}"
        gs.make_move(legal_by_notation[uci])

    assert state_snapshot(gs) != before  # The PV was actually replayed.
    while gs.move_log:
        gs.undo_move()
    assert state_snapshot(gs) == before
    assert pvs_stats["pvs_null_window_searches"] > 0


@pytest.mark.parametrize("use_pvs", [False, True])
def test_choose_move_expired_deadline_preserves_state_in_both_search_modes(use_pvs):
    gs = GameState()
    before = state_snapshot(gs)
    legal_moves = gs.get_valid_moves()

    move, info = ai.choose_ai_move(
        gs, legal_moves, max_depth=4, time_budget=0, use_pvs=use_pvs
    )

    assert move in legal_moves
    assert info["depth_reached"] == 0
    assert info["timed_out"] is True
    assert state_snapshot(gs) == before


@pytest.mark.parametrize("fen", [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R b KQkq - 0 1",
    "8/5pk1/6p1/8/3P4/5K2/8/8 w - - 0 1",
])
def test_root_pvs_matches_full_window_move_and_score(fen):
    from tests.test_perft import load_fen_position

    def run(use_pvs):
        gs = load_fen_position(fen)
        moves = gs.get_valid_moves()
        move, info = ai.choose_ai_move(
            gs, moves, mode="fair", max_depth=2, time_budget=60,
            use_pvs=use_pvs
        )
        assert move in moves
        assert info["depth_reached"] == 2
        return move.get_chess_notation(), info

    full_move, full_info = run(False)
    pvs_move, pvs_info = run(True)

    assert pvs_info["score"] == pytest.approx(full_info["score"], abs=1e-9)
    assert pvs_move == full_move
    assert pvs_info["root_pvs_null_window_searches"] > 0
