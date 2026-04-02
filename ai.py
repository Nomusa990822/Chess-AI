
"""
ai.py

Minimax + Alpha-Beta Pruning based chess AI.
"""

from copy import deepcopy
from evaluation import evaluate_position, explain_move

CHECKMATE = 9999
STALEMATE = 0


def order_moves(gs, moves):
    """
    Simple move ordering to improve alpha-beta pruning efficiency.
    Captures, promotions, and castling are searched first.
    """
    def move_priority(move):
        score = 0

        if move.piece_captured != "--":
            score += 10
        if move.is_pawn_promotion:
            score += 8
        if move.is_castle_move:
            score += 4

        moved_piece_value = {
            "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0
        }[move.piece_moved[1]]

        captured_piece_value = 0
        if move.piece_captured != "--":
            captured_piece_value = {
                "P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0
            }[move.piece_captured[1]]

        score += captured_piece_value - 0.1 * moved_piece_value
        return score

    return sorted(moves, key=move_priority, reverse=True)


def find_best_move(gs, valid_moves, depth=3, mode="fair"):
    """
    Top-level AI move selection.
    Returns:
        best_move, stats
    """
    stats = {
        "nodes": 0,
        "score": 0,
        "explanation": ""
    }

    ordered_moves = order_moves(gs, valid_moves)

    if gs.white_to_move:
        best_score = -float("inf")
        best_move = None

        for move in ordered_moves:
            gs.make_move(move)
            score = minimax(gs, depth - 1, -float("inf"), float("inf"), False, mode, stats)
            gs.undo_move()

            if score > best_score:
                best_score = score
                best_move = move

        stats["score"] = best_score
    else:
        best_score = float("inf")
        best_move = None

        for move in ordered_moves:
            gs.make_move(move)
            score = minimax(gs, depth - 1, -float("inf"), float("inf"), True, mode, stats)
            gs.undo_move()

            if score < best_score:
                best_score = score
                best_move = move

        stats["score"] = best_score

    if best_move is not None:
        before = deepcopy(gs)
        gs.make_move(best_move)
        after = deepcopy(gs)
        gs.undo_move()
        stats["explanation"] = explain_move(before, best_move, after, mode)

    return best_move, stats


def minimax(gs, depth, alpha, beta, maximizing_player, mode, stats):
    """
    Recursive minimax with alpha-beta pruning.
    """
    stats["nodes"] += 1
    gs.update_game_status()

    if depth == 0 or gs.checkmate or gs.stalemate or gs.draw_by_repetition:
        return evaluate_position(gs, mode)

    moves = order_moves(gs, gs.get_valid_moves())

    if maximizing_player:
        max_eval = -float("inf")
        for move in moves:
            gs.make_move(move)
            eval_score = minimax(gs, depth - 1, alpha, beta, False, mode, stats)
            gs.undo_move()

            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)

            if beta <= alpha:
                break

        return max_eval

    min_eval = float("inf")
    for move in moves:
        gs.make_move(move)
        eval_score = minimax(gs, depth - 1, alpha, beta, True, mode, stats)
        gs.undo_move()

        min_eval = min(min_eval, eval_score)
        beta = min(beta, eval_score)

        if beta <= alpha:
            break

    return min_eval
