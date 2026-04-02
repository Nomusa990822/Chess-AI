"""
main.py

Terminal-based Chess AI project for CS50's Introduction to AI with Python.

Features:
- Fair Mode
- Hard Mode
- Forced-Win Mode
- Human vs AI
- Legal move validation
- Check / Checkmate / Stalemate
- Castling, en passant, promotion
- AI move explanations
"""

from engine import GameState, Move
from ai import find_best_move
from forced_positions import get_forced_position
from utils import (
    print_welcome_banner,
    print_board,
    print_help,
    parse_user_move,
    print_mode_info,
    color_text
)

WHITE = "w"
BLACK = "b"


def choose_mode():
    """
    Prompt the user to choose one of the available game modes.
    """
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


def choose_side(mode):
    """
    Let the user choose which side to play.
    In Forced-Win mode, the AI is black by default in the provided setups,
    so the user will generally play white unless the selected position says otherwise.
    """
    while True:
        choice = input("\nChoose your side (w/b): ").strip().lower()
        if choice in ("w", "b"):
            return choice
        print(color_text("Invalid choice. Please enter 'w' or 'b'.", "red"))


def setup_game(mode):
    """
    Create a GameState based on the selected mode.
    """
    if mode == "forced":
        gs = get_forced_position("kqk_black_to_move")
    else:
        gs = GameState()

    return gs


def get_ai_config(mode):
    """
    Return search depth and descriptive label for each mode.
    """
    if mode == "fair":
        return {
            "depth": 2,
            "name": "Fair Mode AI"
        }
    if mode == "hard":
        return {
            "depth": 3,
            "name": "Hard Mode AI"
        }
    return {
        "depth": 4,
        "name": "Forced-Win AI"
    }


def print_game_status(gs):
    """
    Print current high-level game status.
    """
    print("\n" + "=" * 70)
    print(f"Turn: {'White' if gs.white_to_move else 'Black'}")
    print(f"Move number: {len(gs.move_log) + 1}")
    print_board(gs.board)
    print("=" * 70)

    if gs.in_check(gs.white_to_move):
        print(color_text("CHECK!", "yellow"))


def handle_human_turn(gs):
    """
    Handle human input until a valid move is made or the user exits.
    """
    valid_moves = gs.get_valid_moves()

    while True:
        print("\nEnter your move in coordinate form, e.g. e2e4")
        print("Promotion example: e7e8q")
        print("Type 'help' for instructions, 'moves' to list legal moves, or 'quit' to exit.")

        user_input = input("Your move: ").strip().lower()

        if user_input == "quit":
            return "quit"

        if user_input == "help":
            print_help()
            continue

        if user_input == "moves":
            print("\nLegal moves:")
            for mv in valid_moves:
                print(f" - {mv.get_chess_notation()}")
            continue

        move = parse_user_move(user_input, gs.board)
        if move is None:
            print(color_text("Invalid input format. Try something like e2e4.", "red"))
            continue

        matched_move = None
        for valid_move in valid_moves:
            if move == valid_move:
                matched_move = valid_move
                break

        if matched_move:
            gs.make_move(matched_move)
            return "moved"

        print(color_text("Illegal move. Try again.", "red"))


def handle_ai_turn(gs, mode):
    """
    Ask the AI for the best move and play it.
    """
    config = get_ai_config(mode)
    valid_moves = gs.get_valid_moves()

    if not valid_moves:
        return

    best_move, stats = find_best_move(gs, valid_moves, depth=config["depth"], mode=mode)

    if best_move is None:
        # Fallback just in case
        best_move = valid_moves[0]

    gs.make_move(best_move)

    print(color_text(f"\n{config['name']} plays: {best_move.get_chess_notation()}", "cyan"))
    print(f"AI evaluation: {stats.get('score', 0):.2f}")
    print(f"Nodes explored: {stats.get('nodes', 0)}")

    explanation = stats.get("explanation")
    if explanation:
        print(color_text(f"AI explanation: {explanation}", "blue"))


def print_result(gs, human_side):
    """
    Print the final game result.
    """
    print("\n" + "=" * 70)
    print("GAME OVER")
    print_board(gs.board)

    if gs.checkmate:
        winner = "Black" if gs.white_to_move else "White"
        print(color_text(f"Checkmate! {winner} wins.", "green"))

        if (winner == "White" and human_side == "w") or (winner == "Black" and human_side == "b"):
            print(color_text("Congratulations — you defeated the AI.", "green"))
        else:
            print(color_text("The AI wins this game.", "cyan"))

    elif gs.stalemate:
        print(color_text("Stalemate! The game is a draw.", "yellow"))

    elif gs.draw_by_repetition:
        print(color_text("Draw by repetition.", "yellow"))

    else:
        print(color_text("Game ended.", "yellow"))

    print("\nMove history:")
    for i, move in enumerate(gs.move_log, start=1):
        prefix = f"{(i + 1) // 2}." if i % 2 == 1 else "..."
        print(f"{prefix} {move.get_chess_notation()}")


def main():
    """
    Main game loop.
    """
    print_welcome_banner()

    mode = choose_mode()
    print_mode_info(mode)

    gs = setup_game(mode)

    if mode == "forced":
        print(color_text("\nForced-Win Mode starts from a pre-configured winning position for the AI.", "yellow"))

    human_side = choose_side(mode)
    ai_side = BLACK if human_side == WHITE else WHITE

    print(color_text(f"\nYou are playing as {'White' if human_side == WHITE else 'Black'}.", "green"))
    print(color_text(f"AI is {'White' if ai_side == WHITE else 'Black'}.", "cyan"))

    while True:
        gs.update_game_status()

        if gs.checkmate or gs.stalemate or gs.draw_by_repetition:
            break

        print_game_status(gs)

        current_side = WHITE if gs.white_to_move else BLACK

        if current_side == human_side:
            result = handle_human_turn(gs)
            if result == "quit":
                print(color_text("\nGame exited by user.", "yellow"))
                return
        else:
            handle_ai_turn(gs, mode)

    print_result(gs, human_side)


if __name__ == "__main__":
    main()
