"""
Entry point and game controller for the Chess AI project.

Features:
- Fair / Hard / Forced-Win modes
- Human vs AI gameplay
- AI search report
- Principal variation output
- Static evaluation breakdown (AI moves only)
- Static evaluation delta (AI moves only)
"""

from copy import deepcopy

from engine import GameState
from ai import choose_ai_move
from forced_positions import get_forced_position
from evaluation import print_evaluation_breakdown, print_evaluation_delta
from utils import (
    print_welcome_banner,
    print_board,
    print_help,
    parse_user_move,
    print_mode_info,
    color_text,
    print_separator
)

WHITE = "w"
BLACK = "b"

MODE_CONFIG = {
    "fair": {
        "label": "Fair Mode",
        "time_budget": 1.0,
        "max_depth": 2
    },
    "hard": {
        "label": "Hard Mode",
        "time_budget": 2.0,
        "max_depth": 4
    },
    "forced": {
        "label": "Forced-Win Mode",
        "time_budget": 2.5,
        "max_depth": 5
    }
}


def choose_mode():
    while True:
        print("\nChoose a mode:")
        print("1. Fair Mode")
        print("2. Hard Mode")
        print("3. Forced-Win Mode")

        choice = input("Enter 1, 2, or 3: ").strip()

        if choice == "1":
            return "fair"
        if choice == "2":
            return "hard"
        if choice == "3":
            return "forced"

        print(color_text("Invalid choice. Please select 1, 2, or 3.", "red"))


def choose_side():
    while True:
        side = input("\nChoose your side (w/b): ").strip().lower()

        if side in ("w", "b"):
            return side

        print(color_text("Invalid side. Enter 'w' or 'b'.", "red"))


def setup_game(mode):
    if mode == "forced":
        return get_forced_position("kqk_black_to_move")
    return GameState()


def display_status(gs):
    print_separator()
    print(f"Turn: {'White' if gs.white_to_move else 'Black'}")
    print(f"Half-moves played: {len(gs.move_log)}")
    print_board(gs.board)

    if gs.in_check(gs.white_to_move):
        print(color_text("CHECK!", "yellow"))

    if gs.draw_by_repetition:
        print(color_text("Current state is repeated.", "yellow"))


def human_turn(gs):
    valid_moves = gs.get_valid_moves()

    while True:
        print("\nEnter move like e2e4")
        print("Promotion example: e7e8q")
        print("Commands: help, moves, undo, quit")

        user_input = input("Your move: ").strip().lower()

        if user_input == "quit":
            return "quit"

        if user_input == "help":
            print_help()
            continue

        if user_input == "moves":
            print("\nLegal moves:")
            for move in valid_moves:
                print(f" - {move.get_chess_notation()}")
            continue

        if user_input == "undo":
            if len(gs.move_log) >= 2:
                gs.undo_move()
                gs.undo_move()
                return "undone"

            print(color_text("Not enough moves to undo.", "red"))
            continue

        parsed_move = parse_user_move(user_input, gs.board)
        if parsed_move is None:
            print(color_text("Invalid move format.", "red"))
            continue

        matched_move = None
        for valid_move in valid_moves:
            if parsed_move == valid_move:
                matched_move = valid_move
                break

        if matched_move:
            gs.make_move(matched_move)
            return "moved"

        print(color_text("Illegal move.", "red"))


def ai_turn(gs, mode):
    config = MODE_CONFIG[mode]
    valid_moves = gs.get_valid_moves()

    if not valid_moves:
        return

    before_position = deepcopy(gs)

    move, search_info = choose_ai_move(
        gs,
        valid_moves,
        mode=mode,
        max_depth=config["max_depth"],
        time_budget=config["time_budget"]
    )

    if move is None:
        move = valid_moves[0]

    gs.make_move(move)

    print(color_text(f"\nAI plays: {move.get_chess_notation()}", "cyan"))
    print(color_text("AI Search Report", "blue"))
    print(f"Depth reached: {search_info['depth_reached']}")
    print(f"Nodes explored: {search_info['nodes']}")
    print(f"Quiescence nodes: {search_info['q_nodes']}")
    print(f"Prunes: {search_info['prunes']}")
    print(f"TT hits: {search_info['tt_hits']}")
    print(f"Search evaluation: {search_info['score']:.2f}")
    print(f"Game phase: {search_info['phase']}")

    if search_info["top_lines"]:
        print("\nTop candidate moves:")
        for idx, entry in enumerate(search_info["top_lines"], start=1):
            print(f"  {idx}. {entry['move']} -> {entry['score']:.2f}")

    if search_info["principal_variation"]:
        print("\nBest line (Principal Variation):")
        print("  " + " -> ".join(search_info["principal_variation"]))

    if search_info["explanation"]:
        print(color_text("\nWhy this move was chosen:", "yellow"))
        print(f"  {search_info['explanation']}")

    print_evaluation_breakdown(gs, mode)
    print_evaluation_delta(before_position, gs, mode)


def print_result(gs, human_side):
    print_separator()
    print(color_text("GAME OVER", "yellow"))
    print_board(gs.board)

    if gs.checkmate:
        winner = "Black" if gs.white_to_move else "White"
        print(color_text(f"Checkmate! {winner} wins.", "green"))

        user_won = (winner == "White" and human_side == "w") or (winner == "Black" and human_side == "b")
        if user_won:
            print(color_text("You defeated the AI.", "green"))
        else:
            print(color_text("The AI wins.", "cyan"))

    elif gs.stalemate:
        print(color_text("Stalemate. Draw.", "yellow"))

    elif gs.draw_by_repetition:
        print(color_text("Draw by repetition.", "yellow"))

    else:
        print(color_text("Game ended.", "yellow"))

    print("\nMove history:")
    for i, move in enumerate(gs.move_log, start=1):
        turn_marker = f"{(i + 1) // 2}." if i % 2 == 1 else "..."
        print(f"{turn_marker} {move.get_chess_notation()}")


def main():
    print_welcome_banner()

    mode = choose_mode()
    print_mode_info(mode)

    gs = setup_game(mode)

    if mode == "forced":
        print(color_text("\nForced-Win Mode starts from a winning position for the AI.", "yellow"))

    human_side = choose_side()
    ai_side = BLACK if human_side == WHITE else WHITE

    print(color_text(f"\nYou are {'White' if human_side == WHITE else 'Black'}.", "green"))
    print(color_text(f"AI is {'White' if ai_side == WHITE else 'Black'}.", "cyan"))

    while True:
        gs.update_game_status()

        if gs.checkmate or gs.stalemate or gs.draw_by_repetition:
            break

        display_status(gs)

        current_side = WHITE if gs.white_to_move else BLACK

        if current_side == human_side:
            outcome = human_turn(gs)

            if outcome == "quit":
                print(color_text("Game exited.", "yellow"))
                return
        else:
            ai_turn(gs, mode)

    print_result(gs, human_side)


if __name__ == "__main__":
    main()
