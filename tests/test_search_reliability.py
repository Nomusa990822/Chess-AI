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
