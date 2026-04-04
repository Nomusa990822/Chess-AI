"""
Terminal helpers:
- colors
- banner
- separators
- board printing
- input parsing
"""

from engine import Move


def color_text(text, color):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_separator():
    print("\n" + "=" * 78)


def print_welcome_banner():
    banner = r"""
==============================================================
                        CHESS AI
==============================================================

        CS50 AI Project - Chess AI with Forced Advantage
"""
    print(color_text(banner, "cyan"))


def print_mode_info(mode):
    if mode == "fair":
        print(color_text("\nFair Mode", "green"))
        print("Balanced search depth and lighter evaluation.")
    elif mode == "hard":
        print(color_text("\nHard Mode", "yellow"))
        print("Deeper search, better move ordering, stronger evaluation.")
    else:
        print(color_text("\nForced-Win Mode", "red"))
        print("Starts from a winning position and emphasizes endgame conversion.")


def print_help():
    print("\nInstructions")
    print("1. Enter moves in coordinate notation, e.g. e2e4")
    print("2. Promotion example: e7e8q")
    print("3. Castling is entered as king movement:")
    print("   e1g1, e1c1, e8g8, e8c8")
    print("4. Commands:")
    print("   help  -> show instructions")
    print("   moves -> list legal moves")
    print("   undo  -> undo the last full turn")
    print("   quit  -> exit game")


def print_board(board):
    print("\n     a    b    c    d    e    f    g    h")
    print("   " + "-" * 41)

    for r in range(8):
        print(f" {8-r} |", end="")
        for c in range(8):
            piece = board[r][c]
            display = piece if piece != "--" else "  "

            if piece.startswith("w"):
                display = color_text(display, "green")
            elif piece.startswith("b"):
                display = color_text(display, "cyan")

            print(f" {display} |", end="")
        print(f" {8-r}")
        print("   " + "-" * 41)

    print("     a    b    c    d    e    f    g    h")


def parse_user_move(user_input, board):
    """
    Parse user input like:
    e2e4
    e7e8q
    """
    if len(user_input) not in (4, 5):
        return None

    start_file, start_rank, end_file, end_rank = user_input[:4]

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
