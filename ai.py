"""
Search engine for the Chess AI project.

Implements:
- iterative deepening
- minimax
- alpha-beta pruning
- transposition table
- move ordering
- quiescence search
- principal variation tracking
- search reporting
"""

import time
from copy import deepcopy

from evaluation import evaluate_position, explain_move, get_game_phase

CHECKMATE_SCORE = 9999


class TranspositionEntry:
    """
    Stores a search result for a previously evaluated position.
    """

    def __init__(self, depth, score, flag, best_move, principal_variation):
        self.depth = depth
        self.score = score
        self.flag = flag  # EXACT, LOWERBOUND, UPPERBOUND
        self.best_move = best_move
        self.principal_variation = principal_variation


PIECE_VALUES = {
    "K": 0,
    "Q": 9,
    "R": 5,
    "B": 3.25,
    "N": 3,
    "P": 1
}


def move_priority_hint(gs, move):
    """
    Heuristic used to order moves before searching them.
    Better move ordering improves alpha-beta efficiency.
    """
    score = 0.0

    if move.piece_captured != "--":
        captured_value = PIECE_VALUES[move.piece_captured[1]]
        moved_value = PIECE_VALUES[move.piece_moved[1]]
        score += 10 + captured_value - 0.1 * moved_value

    if move.is_pawn_promotion:
        score += 8

    if move.is_castle_move:
        score += 3

    if move.piece_moved[1] == "P" and abs(move.start_row - move.end_row) == 2:
        score += 0.5

    if move.piece_moved[1] in ("N", "B") and move.end_row in (2, 3, 4, 5):
        score += 0.4

    # Bonus for giving check
    gs.make_move(move)
    if gs.in_check(gs.white_to_move):
        score += 5
    gs.undo_move()

    return score


def order_moves(gs, moves, tt_move=None):
    """
    Order moves so strong candidates are searched first.
    """
    scored_moves = []

    for move in moves:
        score = move_priority_hint(gs, move)

        if tt_move is not None and move == tt_move:
            score += 100

        scored_moves.append((score, move))

    scored_moves.sort(key=lambda x: x[0], reverse=True)
    return [move for _, move in scored_moves]


def is_tactical_move(move):
    """
    A move considered tactical for quiescence search.
    """
    return (
        move.piece_captured != "--"
        or move.is_pawn_promotion
    )


def get_tactical_moves(gs, moves):
    """
    Restrict move list for quiescence search.
    """
    tactical = [move for move in moves if is_tactical_move(move)]
    return order_moves(gs, tactical)


def choose_ai_move(gs, valid_moves, mode="fair", max_depth=4, time_budget=2.0):
    """
    Top-level AI interface.

    Returns:
        best_move, search_info
    """
    start_time = time.time()
    deadline = start_time + time_budget

    transposition_table = {}

    stats = {
        "nodes": 0,
        "prunes": 0,
        "tt_hits": 0,
        "q_nodes": 0,
        "score": 0.0,
        "depth_reached": 0,
        "explanation": "",
        "top_lines": [],
        "principal_variation": [],
        "phase": get_game_phase(gs.board)
    }

    best_move = None
    best_score = evaluate_position(gs, mode)
    best_line = []

    for depth in range(1, max_depth + 1):
        if time.time() >= deadline:
            break

        root_tt_move = None
        position_key = gs.get_position_key()
        if position_key in transposition_table:
            root_tt_move = transposition_table[position_key].best_move

        root_moves = order_moves(gs, valid_moves, tt_move=root_tt_move)

        current_best_move = None
        current_best_score = -float("inf") if gs.white_to_move else float("inf")
        current_best_line = []
        move_scores = []

        alpha = -float("inf")
        beta = float("inf")

        for move in root_moves:
            if time.time() >= deadline:
                break

            gs.make_move(move)

            score, pv = minimax(
                gs=gs,
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
                maximizing_player=gs.white_to_move,
                mode=mode,
                tt=transposition_table,
                stats=stats,
                deadline=deadline
            )

            gs.undo_move()

            full_line = [move.get_chess_notation()] + pv
            move_scores.append((move, score, full_line))

            if current_best_move is None:
                current_best_move = move
                current_best_score = score
                current_best_line = full_line
            else:
                if gs.white_to_move and score > current_best_score:
                    current_best_move = move
                    current_best_score = score
                    current_best_line = full_line
                elif (not gs.white_to_move) and score < current_best_score:
                    current_best_move = move
                    current_best_score = score
                    current_best_line = full_line

            if gs.white_to_move:
                alpha = max(alpha, score)
            else:
                beta = min(beta, score)

        if current_best_move is not None:
            best_move = current_best_move
            best_score = current_best_score
            best_line = current_best_line
            stats["depth_reached"] = depth

            move_scores.sort(key=lambda x: x[1], reverse=gs.white_to_move)
            stats["top_lines"] = [
                {"move": move.get_chess_notation(), "score": float(score)}
                for move, score, _ in move_scores[:3]
            ]
            stats["principal_variation"] = best_line

    stats["score"] = float(best_score)

    if best_move is not None:
        before = deepcopy(gs)
        gs.make_move(best_move)
        after = deepcopy(gs)
        gs.undo_move()
        stats["explanation"] = explain_move(before, best_move, after, mode)

    return best_move, stats


def minimax(gs, depth, alpha, beta, maximizing_player, mode, tt, stats, deadline):
    """
    Minimax with alpha-beta pruning and transposition table.

    Returns:
        (score, principal_variation_list)
    """
    if time.time() >= deadline:
        return evaluate_position(gs, mode), []

    stats["nodes"] += 1
    gs.update_game_status()

    if gs.checkmate or gs.stalemate or gs.draw_by_repetition:
        return evaluate_position(gs, mode), []

    if depth == 0:
        return quiescence_search(gs, alpha, beta, maximizing_player, mode, stats, deadline), []

    original_alpha = alpha
    original_beta = beta

    position_key = gs.get_position_key()
    if position_key in tt and tt[position_key].depth >= depth:
        entry = tt[position_key]
        stats["tt_hits"] += 1

        if entry.flag == "EXACT":
            return entry.score, entry.principal_variation
        if entry.flag == "LOWERBOUND":
            alpha = max(alpha, entry.score)
        elif entry.flag == "UPPERBOUND":
            beta = min(beta, entry.score)

        if alpha >= beta:
            return entry.score, entry.principal_variation

    valid_moves = gs.get_valid_moves()
    if not valid_moves:
        return evaluate_position(gs, mode), []

    tt_move = tt[position_key].best_move if position_key in tt else None
    valid_moves = order_moves(gs, valid_moves, tt_move=tt_move)

    best_move = valid_moves[0]
    best_pv = []

    if maximizing_player:
        best_score = -float("inf")

        for move in valid_moves:
            gs.make_move(move)
            child_score, child_pv = minimax(
                gs, depth - 1, alpha, beta, False, mode, tt, stats, deadline
            )
            gs.undo_move()

            if child_score > best_score:
                best_score = child_score
                best_move = move
                best_pv = [move.get_chess_notation()] + child_pv

            alpha = max(alpha, best_score)
            if alpha >= beta:
                stats["prunes"] += 1
                break

    else:
        best_score = float("inf")

        for move in valid_moves:
            gs.make_move(move)
            child_score, child_pv = minimax(
                gs, depth - 1, alpha, beta, True, mode, tt, stats, deadline
            )
            gs.undo_move()

            if child_score < best_score:
                best_score = child_score
                best_move = move
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

    tt[position_key] = TranspositionEntry(
        depth=depth,
        score=best_score,
        flag=flag,
        best_move=best_move,
        principal_variation=best_pv
    )

    return best_score, best_pv


def quiescence_search(gs, alpha, beta, maximizing_player, mode, stats, deadline, q_depth=0, max_q_depth=8):
    """
    Extends leaf-node search through tactical continuations only.
    Helps reduce the horizon effect.
    """
    if time.time() >= deadline:
        return evaluate_position(gs, mode)

    stats["q_nodes"] += 1

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

    tactical_moves = get_tactical_moves(gs, gs.get_valid_moves())

    if not tactical_moves:
        return stand_pat

    if maximizing_player:
        value = stand_pat
        for move in tactical_moves:
            gs.make_move(move)
            score = quiescence_search(
                gs, alpha, beta, False, mode, stats, deadline, q_depth + 1, max_q_depth
            )
            gs.undo_move()

            value = max(value, score)
            alpha = max(alpha, value)
            if alpha >= beta:
                stats["prunes"] += 1
                break
        return value

    value = stand_pat
    for move in tactical_moves:
        gs.make_move(move)
        score = quiescence_search(
            gs, alpha, beta, True, mode, stats, deadline, q_depth + 1, max_q_depth
        )
        gs.undo_move()

        value = min(value, score)
        beta = min(beta, value)
        if alpha >= beta:
            stats["prunes"] += 1
            break
    return value
