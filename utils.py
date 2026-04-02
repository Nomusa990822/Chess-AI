"""
utils.py

Helper utilities for display, move parsing, and small UI features.
"""

from engine import Move


def color_text(text, color):
    """
    Minimal ANSI coloring for terminal output.
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_welcome_banner():
    banner = r"""
   _____ _    _ ______  _____ _____        _____ _____
  / ____| |  | |  ____|/ ____/ ____|      / ____|_   _|
 | |    | |__| | |__  | (___| (___ ______| |      | |
 | |    |  __  |  __|  \___ \\___ \______| |      | |
 | |____| |  | | |____ ____) |___) |     | |____ _| |_
  \_____|_|  |_|______|_____/_____/       \_____|_____|

        CS50 AI Project - Chess AI with Forced Advantage
    """
    print(color_text(banner, "cyan"))


def print_mode_info(mode):
    if mode == "fair":
        print(color_text("\nFair Mode:", "green"))
        print("Balanced AI. Lower search depth, simpler evaluation.")
    elif mode == "hard":
        print(color_text("\nHard Mode:", "yellow"))
        print("Stronger AI. Deeper search, better positional evaluation.")
    else:
        print(color_text("\nForced-Win Mode:", "red"))
        print("The AI starts from a theoretically winning position.")


def print_help():
    print("\nInstructions:")
    print("1. Enter moves in coordinate notation, e.g. e2e4")
    print("2. Promotion example: e7e8q")
    print("3. Castling is entered by moving the king:")
    print("   - e1g1 for White kingside")
    print("   - e1c1 for White queenside")
    print("   - e8g8 for Black kingside")
    print("   - e8c8 for Black queenside")
    print("4. Type 'moves' to list all legal moves")
    print("5. Type 'quit' to exit")


def print_board(board):
    """
    Pretty-print the board to the terminal.
    """
    print("\n    a    b    c    d    e    f    g    h")
    print("  " + "-" * 41)
    for r in range(8):
        print(f"{8-r} |", end="")
        for c in range(8):
            piece = board[r][c]
            display = piece if piece != "--" else "  "

            if piece.startswith("w"):
                cell = color_text(f"{display}", "green")
            elif piece.startswith("b"):
                cell = color_text(f"{display}", "cyan")
            else:
                cell = display

            print(f" {cell} |", end="")
        print(f" {8-r}")
        print("  " + "-" * 41)
    print("    a    b    c    d    e    f    g    h")


def parse_user_move(user_input, board):
    """
    Parse input like:
    - e2e4
    - e7e8q
    Return Move object or None if invalid format.
    """
    if len(user_input) not in (4, 5):
        return None

    start_file = user_input[0]
    start_rank = user_input[1]
    end_file = user_input[2]
    end_rank = user_input[3]

    if (
        start_file not in Move.files_to_cols
        or end_file not in Move.files_to_cols
        or start_rank not in Move.ranks_to_rows
        or end_rank not in Move.ranks_to_rows
    ):
        return None

    start_row = Move.ranks_to_rows[start_rank]
    start_col = Move.files_to_cols[start_file]
    end_row = Move.ranks_to_rows[end_rank]
    end_col = Move.files_to_cols[end_file]

    promotion_choice = "Q"
    if len(user_input) == 5:
        promotion_choice = user_input[4].upper()
        if promotion_choice not in ("Q", "R", "B", "N"):
            return None

    return Move(
        (start_row, start_col),
        (end_row, end_col),
        board,
        promotion_choice=promotion_choice
    )
