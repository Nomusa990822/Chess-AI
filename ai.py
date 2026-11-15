"""Reliable classical chess search: iterative deepening, alpha-beta and quiescence."""

import time
from copy import deepcopy

from evaluation import evaluate_position, explain_move, get_game_phase

CHECKMATE_SCORE = 9999
PVS_WINDOW = 1e-6
PIECE_VALUES = {"K": 0, "Q": 9, "R": 5, "B": 3.25, "N": 3, "P": 1}


class SearchTimeout(Exception):
    """Raised internally when the search deadline is reached."""


class TranspositionEntry:
    def __init__(self, depth, score, flag, best_move, principal_variation):
        self.depth = depth
        self.score = score
        self.flag = flag
        self.best_move = best_move
        self.principal_variation = principal_variation


def _check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise SearchTimeout


def move_priority_hint(gs, move):
    score = 0.0
    if move.piece_captured != "--":
        score += 10 + PIECE_VALUES[move.piece_captured[1]] - 0.1 * PIECE_VALUES[move.piece_moved[1]]
    if move.is_pawn_promotion:
        score += 8
    if move.is_castle_move:
        score += 3
    if move.piece_moved[1] == "P" and abs(move.start_row - move.end_row) == 2:
        score += 0.5
    if move.piece_moved[1] in ("N", "B") and move.end_row in (2, 3, 4, 5):
        score += 0.4

    gs.make_move(move)
    try:
        if gs.in_check(gs.white_to_move):
            score += 5
    finally:
        gs.undo_move()
    return score


def _quiet_history_key(gs, move):
    return (gs.white_to_move, move.piece_moved, move.start_row,
            move.start_col, move.end_row, move.end_col)


def order_moves(gs, moves, tt_move=None, ply=0, stats=None):
    """Order hash move, tactical moves, killers, then history-scored quiets."""
    stats = stats if stats is not None else {}
    killers = stats.setdefault("killer_moves", {})
    history = stats.setdefault("history_scores", {})
    ply_killers = killers.get(ply, ())
    scored = []
    for move in moves:
        score = move_priority_hint(gs, move)
        if tt_move is not None and move == tt_move:
            score += 1000000
        elif is_tactical_move(move):
            score += 10000
        else:
            notation = move.get_chess_notation()
            if notation in ply_killers:
                score += 5000 - ply_killers.index(notation) * 100
            score += history.get(_quiet_history_key(gs, move), 0)
        scored.append((score, move))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [move for _, move in scored]


def _record_quiet_cutoff(gs, move, depth, ply, stats):
    if is_tactical_move(move):
        return
    killers = stats.setdefault("killer_moves", {})
    notation = move.get_chess_notation()
    current = [item for item in killers.get(ply, ()) if item != notation]
    killers[ply] = (notation, *current[:1])
    history = stats.setdefault("history_scores", {})
    key = _quiet_history_key(gs, move)
    history[key] = min(1000000, history.get(key, 0) + depth * depth)


def _store_tt_entry(tt, key, entry):
    """Prefer deeper results; at equal depth prefer exact over bound entries."""
    previous = tt.get(key)
    if (previous is None or entry.depth > previous.depth
            or (entry.depth == previous.depth
                and entry.flag == "EXACT" and previous.flag != "EXACT")):
        tt[key] = entry


def is_tactical_move(move):
    return move.piece_captured != "--" or move.is_pawn_promotion


def get_tactical_moves(gs, moves):
    return order_moves(gs, [m for m in moves if is_tactical_move(m)])


def _transposition_key(gs):
    """Include draw-relevant game history in the cache identity."""
    repetition_context = tuple(sorted(gs.position_counts.items()))
    return (gs.get_position_key(), gs.halfmove_clock, repetition_context)


def _terminal_score(gs, ply):
    """Return a white-perspective terminal score, or None for non-terminal."""
    gs.update_game_status()
    if gs.checkmate:
        # The side to move has been checkmated.
        return -CHECKMATE_SCORE + ply if gs.white_to_move else CHECKMATE_SCORE - ply
    if (gs.stalemate or gs.draw_by_repetition or gs.draw_by_fifty_move
            or gs.draw_by_seventyfive_move or gs.draw_by_fivefold_repetition
            or gs.draw_by_insufficient_material):
        return 0.0
    return None


def choose_ai_move(gs, valid_moves, mode="fair", max_depth=4, time_budget=2.0, use_pvs=False):
    """Return (best_move, search_info); only fully completed depths are published."""
    started = time.monotonic()
    deadline = started + max(0.0, time_budget)
    tt = {}
    stats = {
        "nodes": 0, "prunes": 0, "tt_hits": 0, "q_nodes": 0,
        "score": 0.0, "depth_reached": 0, "explanation": "",
        "top_lines": [], "principal_variation": [],
        "phase": get_game_phase(gs.board), "timed_out": False,
        "completed_iterations": [], "killer_moves": {}, "history_scores": {},
        "pvs_null_window_searches": 0, "pvs_researches": 0,
        "root_pvs_null_window_searches": 0, "root_pvs_researches": 0
    }

    best_move = valid_moves[0] if valid_moves else None
    best_score = evaluate_position(gs, mode)
    best_line = []

    for depth in range(1, max(0, max_depth) + 1):
        root_key = _transposition_key(gs)
        root_entry = tt.get(root_key)
        root_moves = order_moves(gs, valid_moves,
                                 root_entry.best_move if root_entry else None,
                                 ply=0, stats=stats)
        if not root_moves:
            best_move = None
            break

        iteration_best_move = None
        iteration_best_score = -float("inf") if gs.white_to_move else float("inf")
        iteration_best_line = []
        iteration_scores = []
        alpha, beta = -float("inf"), float("inf")

        try:
            _check_deadline(deadline)
            for move in root_moves:
                _check_deadline(deadline)
                gs.make_move(move)
                try:
                    if use_pvs and iteration_scores:
                        stats["root_pvs_null_window_searches"] += 1
                        if gs.white_to_move:
                            score, child_pv = minimax(
                                gs, depth - 1, alpha, min(beta, alpha + PVS_WINDOW),
                                gs.white_to_move, mode, tt, stats, deadline,
                                ply=1, use_pvs=use_pvs
                            )
                        else:
                            score, child_pv = minimax(
                                gs, depth - 1, max(alpha, beta - PVS_WINDOW), beta,
                                gs.white_to_move, mode, tt, stats, deadline,
                                ply=1, use_pvs=use_pvs
                            )
                        if alpha < score < beta:
                            stats["root_pvs_researches"] += 1
                            score, child_pv = minimax(
                                gs, depth - 1, alpha, beta, gs.white_to_move,
                                mode, tt, stats, deadline, ply=1, use_pvs=use_pvs
                            )
                    else:
                        score, child_pv = minimax(
                            gs, depth - 1, alpha, beta, gs.white_to_move,
                            mode, tt, stats, deadline, ply=1, use_pvs=use_pvs
                        )
                finally:
                    gs.undo_move()

                _check_deadline(deadline)
                line = [move.get_chess_notation()] + child_pv
                iteration_scores.append((move, score, line))

                better = (iteration_best_move is None or
                          (score > iteration_best_score if gs.white_to_move
                           else score < iteration_best_score))
                if better:
                    iteration_best_move = move
                    iteration_best_score = score
                    iteration_best_line = line

                if gs.white_to_move:
                    alpha = max(alpha, iteration_best_score)
                else:
                    beta = min(beta, iteration_best_score)

        except SearchTimeout:
            stats["timed_out"] = True
            break

        # Atomic publication: no result from a partial root iteration escapes.
        if iteration_best_move is not None:
            best_move = iteration_best_move
            best_score = iteration_best_score
            best_line = iteration_best_line
            stats["depth_reached"] = depth
            stats["completed_iterations"].append(depth)
            iteration_scores.sort(key=lambda item: item[1], reverse=gs.white_to_move)
            stats["top_lines"] = [
                {"move": m.get_chess_notation(), "score": float(s)}
                for m, s, _ in iteration_scores[:3]
            ]
            stats["principal_variation"] = best_line

    stats["score"] = float(best_score)
    if best_move is not None:
        before = deepcopy(gs)
        gs.make_move(best_move)
        try:
            after = deepcopy(gs)
        finally:
            gs.undo_move()
        stats["explanation"] = explain_move(before, best_move, after, mode)
    return best_move, stats


def minimax(gs, depth, alpha, beta, maximizing_player, mode, tt, stats, deadline, ply=0, use_pvs=True):
    """White-perspective minimax. Raises SearchTimeout; never returns partial scores."""
    _check_deadline(deadline)
    stats["nodes"] += 1

    terminal = _terminal_score(gs, ply)
    if terminal is not None:
        return terminal, []
    if depth <= 0:
        return quiescence_search(gs, alpha, beta, maximizing_player, mode, stats,
                                 deadline, ply=ply), []

    original_alpha, original_beta = alpha, beta
    key = _transposition_key(gs)
    entry = tt.get(key)
    if entry is not None and entry.depth >= depth:
        stats["tt_hits"] += 1
        if entry.flag == "EXACT":
            return entry.score, list(entry.principal_variation)
        if entry.flag == "LOWERBOUND":
            alpha = max(alpha, entry.score)
        elif entry.flag == "UPPERBOUND":
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score, list(entry.principal_variation)

    moves = gs.get_valid_moves()
    if not moves:
        terminal = _terminal_score(gs, ply)
        return (terminal if terminal is not None else evaluate_position(gs, mode)), []

    tt_move = entry.best_move if entry else None
    moves = order_moves(gs, moves, tt_move, ply=ply, stats=stats)
    best_move, best_pv = None, []

    if maximizing_player:
        best_score = -float("inf")
        for move_index, move in enumerate(moves):
            _check_deadline(deadline)
            gs.make_move(move)
            try:
                if use_pvs and move_index > 0:
                    stats["pvs_null_window_searches"] = stats.get("pvs_null_window_searches", 0) + 1
                    score, child_pv = minimax(
                        gs, depth - 1, alpha, min(beta, alpha + PVS_WINDOW),
                        False, mode, tt, stats, deadline, ply + 1, use_pvs
                    )
                    if alpha < score < beta:
                        stats["pvs_researches"] = stats.get("pvs_researches", 0) + 1
                        score, child_pv = minimax(
                            gs, depth - 1, alpha, beta, False, mode, tt,
                            stats, deadline, ply + 1, use_pvs
                        )
                else:
                    score, child_pv = minimax(
                        gs, depth - 1, alpha, beta, False, mode, tt,
                        stats, deadline, ply + 1, use_pvs
                    )
            finally:
                gs.undo_move()
            if score > best_score:
                best_score, best_move = score, move
                best_pv = [move.get_chess_notation()] + child_pv
            alpha = max(alpha, best_score)
            if alpha >= beta:
                _record_quiet_cutoff(gs, move, depth, ply, stats)
                stats["prunes"] += 1
                break
    else:
        best_score = float("inf")
        for move_index, move in enumerate(moves):
            _check_deadline(deadline)
            gs.make_move(move)
            try:
                if use_pvs and move_index > 0:
                    stats["pvs_null_window_searches"] = stats.get("pvs_null_window_searches", 0) + 1
                    score, child_pv = minimax(
                        gs, depth - 1, max(alpha, beta - PVS_WINDOW), beta,
                        True, mode, tt, stats, deadline, ply + 1, use_pvs
                    )
                    if alpha < score < beta:
                        stats["pvs_researches"] = stats.get("pvs_researches", 0) + 1
                        score, child_pv = minimax(
                            gs, depth - 1, alpha, beta, True, mode, tt,
                            stats, deadline, ply + 1, use_pvs
                        )
                else:
                    score, child_pv = minimax(
                        gs, depth - 1, alpha, beta, True, mode, tt,
                        stats, deadline, ply + 1, use_pvs
                    )
            finally:
                gs.undo_move()
            if score < best_score:
                best_score, best_move = score, move
                best_pv = [move.get_chess_notation()] + child_pv
            beta = min(beta, best_score)
            if alpha >= beta:
                stats["prunes"] += 1
                break

    flag = "EXACT"
    if best_score <= original_alpha:
        flag = "UPPERBOUND"
    elif best_score >= original_beta:
        flag = "LOWERBOUND"
    _store_tt_entry(
        tt, key, TranspositionEntry(depth, best_score, flag, best_move, best_pv)
    )
    return best_score, best_pv


def quiescence_search(gs, alpha, beta, maximizing_player, mode, stats, deadline,
                      q_depth=0, max_q_depth=8, ply=0):
    """Capture/promotion continuation; in-check nodes search every legal evasion."""
    _check_deadline(deadline)
    stats["q_nodes"] += 1

    terminal = _terminal_score(gs, ply)
    if terminal is not None:
        return terminal

    in_check = gs.in_check(gs.white_to_move)
    if in_check:
        # Stand-pat is illegal in check. All legal evasions, including quiet
        # king moves and interpositions, must be considered.
        moves = gs.get_valid_moves()
        if not moves:
            terminal = _terminal_score(gs, ply)
            return terminal if terminal is not None else evaluate_position(gs, mode)
        if q_depth >= max_q_depth:
            # Safety bound: do not claim a stand-pat score in check. The
            # static score is only a bounded fallback at the hard q-search cap.
            return evaluate_position(gs, mode)
        moves = order_moves(gs, moves)
        value = -float("inf") if maximizing_player else float("inf")
    else:
        stand_pat = evaluate_position(gs, mode)
        if maximizing_player:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)

        if q_depth >= max_q_depth:
            return stand_pat
        moves = get_tactical_moves(gs, gs.get_valid_moves())
        if not moves:
            return stand_pat
        value = stand_pat

    for move in moves:
        _check_deadline(deadline)
        gs.make_move(move)
        try:
            score = quiescence_search(
                gs, alpha, beta, not maximizing_player, mode, stats, deadline,
                q_depth + 1, max_q_depth, ply + 1
            )
        finally:
            gs.undo_move()

        if maximizing_player:
            value = max(value, score)
            alpha = max(alpha, value)
        else:
            value = min(value, score)
            beta = min(beta, value)
        if alpha >= beta:
            stats["prunes"] += 1
            break
    return value
