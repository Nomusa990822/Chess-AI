"""
Position evaluation for the Chess AI project.

Features:
- material
- piece-square tables
- center control
- advanced pawn structure evaluation
- mobility
- game phase awareness
- endgame king activity
- edge pressure in winning endgames
"""

PIECE_VALUES = {
    "K": 0.0,
    "Q": 9.0,
    "R": 5.0,
    "B": 3.25,
    "N": 3.0,
    "P": 1.0
}

CENTER_SQUARES = {(3, 3), (3, 4), (4, 3), (4, 4)}
EXTENDED_CENTER = {
    (2, 2), (2, 3), (2, 4), (2, 5),
    (3, 2), (3, 3), (3, 4), (3, 5),
    (4, 2), (4, 3), (4, 4), (4, 5),
    (5, 2), (5, 3), (5, 4), (5, 5)
}

PAWN_TABLE = [
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
    [0.1, 0.1, 0.2, 0.3, 0.3, 0.2, 0.1, 0.1],
    [0.05, 0.05, 0.1, 0.25, 0.25, 0.1, 0.05, 0.05],
    [0.0, 0.0, 0.0, 0.2, 0.2, 0.0, 0.0, 0.0],
    [0.05, -0.05, -0.1, 0.0, 0.0, -0.1, -0.05, 0.05],
    [0.05, 0.1, 0.1, -0.2, -0.2, 0.1, 0.1, 0.05],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
]

KNIGHT_TABLE = [
    [-0.5, -0.4, -0.3, -0.3, -0.3, -0.3, -0.4, -0.5],
    [-0.4, -0.2, 0.0, 0.05, 0.05, 0.0, -0.2, -0.4],
    [-0.3, 0.05, 0.1, 0.15, 0.15, 0.1, 0.05, -0.3],
    [-0.3, 0.0, 0.15, 0.2, 0.2, 0.15, 0.0, -0.3],
    [-0.3, 0.05, 0.15, 0.2, 0.2, 0.15, 0.05, -0.3],
    [-0.3, 0.0, 0.1, 0.15, 0.15, 0.1, 0.0, -0.3],
    [-0.4, -0.2, 0.0, 0.0, 0.0, 0.0, -0.2, -0.4],
    [-0.5, -0.4, -0.3, -0.3, -0.3, -0.3, -0.4, -0.5]
]

BISHOP_TABLE = [
    [-0.2, -0.1, -0.1, -0.1, -0.1, -0.1, -0.1, -0.2],
    [-0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1],
    [-0.1, 0.0, 0.05, 0.1, 0.1, 0.05, 0.0, -0.1],
    [-0.1, 0.05, 0.05, 0.1, 0.1, 0.05, 0.05, -0.1],
    [-0.1, 0.0, 0.1, 0.1, 0.1, 0.1, 0.0, -0.1],
    [-0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, -0.1],
    [-0.1, 0.05, 0.0, 0.0, 0.0, 0.0, 0.05, -0.1],
    [-0.2, -0.1, -0.1, -0.1, -0.1, -0.1, -0.1, -0.2]
]

ROOK_TABLE = [
    [0.0, 0.0, 0.0, 0.05, 0.05, 0.0, 0.0, 0.0],
    [-0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.05],
    [-0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.05],
    [-0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.05],
    [-0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.05],
    [-0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.05],
    [0.05, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.05],
    [0.0, 0.0, 0.0, 0.05, 0.05, 0.0, 0.0, 0.0]
]

QUEEN_TABLE = [
    [-0.2, -0.1, -0.1, -0.05, -0.05, -0.1, -0.1, -0.2],
    [-0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1],
    [-0.1, 0.0, 0.05, 0.05, 0.05, 0.05, 0.0, -0.1],
    [-0.05, 0.0, 0.05, 0.05, 0.05, 0.05, 0.0, -0.05],
    [0.0, 0.0, 0.05, 0.05, 0.05, 0.05, 0.0, -0.05],
    [-0.1, 0.05, 0.05, 0.05, 0.05, 0.05, 0.0, -0.1],
    [-0.1, 0.0, 0.05, 0.0, 0.0, 0.0, 0.0, -0.1],
    [-0.2, -0.1, -0.1, -0.05, -0.05, -0.1, -0.1, -0.2]
]

KING_MIDDLEGAME = [
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.2, -0.3, -0.3, -0.4, -0.4, -0.3, -0.3, -0.2],
    [-0.1, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.1],
    [0.2, 0.2, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2],
    [0.2, 0.3, 0.1, 0.0, 0.0, 0.1, 0.3, 0.2]
]

KING_ENDGAME = [
    [-0.5, -0.3, -0.3, -0.3, -0.3, -0.3, -0.3, -0.5],
    [-0.3, -0.1, 0.0, 0.0, 0.0, 0.0, -0.1, -0.3],
    [-0.3, 0.0, 0.2, 0.3, 0.3, 0.2, 0.0, -0.3],
    [-0.3, 0.0, 0.3, 0.4, 0.4, 0.3, 0.0, -0.3],
    [-0.3, 0.0, 0.3, 0.4, 0.4, 0.3, 0.0, -0.3],
    [-0.3, 0.0, 0.2, 0.3, 0.3, 0.2, 0.0, -0.3],
    [-0.3, -0.1, 0.0, 0.0, 0.0, 0.0, -0.1, -0.3],
    [-0.5, -0.3, -0.3, -0.3, -0.3, -0.3, -0.3, -0.5]
]


def mirrored_row(row):
    return 7 - row


def get_game_phase(board):
    """
    Classify the position into opening, middlegame, or endgame.
    """
    total_material = 0.0
    for row in board:
        for piece in row:
            if piece != "--" and piece[1] != "K":
                total_material += PIECE_VALUES[piece[1]]

    if total_material > 40:
        return "opening"
    if total_material > 18:
        return "middlegame"
    return "endgame"


def material_score(board):
    """
    Simple material count.
    Positive means White is ahead, negative means Black is ahead.
    """
    score = 0.0
    for row in board:
        for piece in row:
            if piece == "--":
                continue
            value = PIECE_VALUES[piece[1]]
            score += value if piece[0] == "w" else -value
    return score


def piece_square_score(board, phase):
    """
    Positional bonuses based on piece placement.
    """
    score = 0.0

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue

            p = piece[1]
            if p == "P":
                table = PAWN_TABLE
            elif p == "N":
                table = KNIGHT_TABLE
            elif p == "B":
                table = BISHOP_TABLE
            elif p == "R":
                table = ROOK_TABLE
            elif p == "Q":
                table = QUEEN_TABLE
            elif p == "K":
                table = KING_ENDGAME if phase == "endgame" else KING_MIDDLEGAME
            else:
                table = None

            if table is None:
                continue

            if piece[0] == "w":
                score += table[r][c]
            else:
                score -= table[mirrored_row(r)][c]

    return score


def center_control_score(board):
    """
    Reward presence in the center and extended center.
    """
    score = 0.0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue

            if (r, c) in CENTER_SQUARES:
                score += 0.25 if piece[0] == "w" else -0.25
            elif (r, c) in EXTENDED_CENTER:
                score += 0.10 if piece[0] == "w" else -0.10

    return score


def pawn_structure_score(board):
    """
    Evaluate pawn structure.

    Included features:
    - doubled pawn penalty
    - isolated pawn penalty
    - pawn chain bonus
    - passed pawn bonus
    - reduced passed-pawn bonus for doubled pawns
    - passed pawn scaling by rank
    """
    score = 0.0

    white_pawns = {c: [] for c in range(8)}
    black_pawns = {c: [] for c in range(8)}

    # Collect pawn positions by file
    for r in range(8):
        for c in range(8):
            if board[r][c] == "wP":
                white_pawns[c].append(r)
            elif board[r][c] == "bP":
                black_pawns[c].append(r)

    # -------------------------------------------------
    # 1. Doubled pawn penalty
    # -------------------------------------------------
    for c in range(8):
        if len(white_pawns[c]) > 1:
            score -= 0.35 * (len(white_pawns[c]) - 1)

        if len(black_pawns[c]) > 1:
            score += 0.35 * (len(black_pawns[c]) - 1)

    # -------------------------------------------------
    # 2. Isolated pawn penalty
    # A pawn is isolated if there are no friendly pawns
    # on the adjacent files.
    # -------------------------------------------------
    for c in range(8):
        for r in white_pawns[c]:
            isolated = True
            for adj in (c - 1, c + 1):
                if 0 <= adj < 8 and len(white_pawns[adj]) > 0:
                    isolated = False
                    break
            if isolated:
                score -= 0.20

        for r in black_pawns[c]:
            isolated = True
            for adj in (c - 1, c + 1):
                if 0 <= adj < 8 and len(black_pawns[adj]) > 0:
                    isolated = False
                    break
            if isolated:
                score += 0.20

    # -------------------------------------------------
    # 3. Passed pawn bonus with scaling by rank
    # A pawn is passed if no enemy pawns are ahead of it
    # on the same or adjacent files.
    # -------------------------------------------------
    for c in range(8):
        for r in white_pawns[c]:
            blocked = False

            for adj in (c - 1, c, c + 1):
                if 0 <= adj < 8:
                    for br in black_pawns[adj]:
                        if br < r:
                            blocked = True
                            break
                if blocked:
                    break

            if not blocked:
                advance = 7 - r  # larger means more advanced for White
                base_bonus = 0.10 if len(white_pawns[c]) > 1 else 0.30
                score += base_bonus + (advance * 0.05)

        for r in black_pawns[c]:
            blocked = False

            for adj in (c - 1, c, c + 1):
                if 0 <= adj < 8:
                    for wr in white_pawns[adj]:
                        if wr > r:
                            blocked = True
                            break
                if blocked:
                    break

            if not blocked:
                advance = r  # larger means more advanced for Black
                base_bonus = 0.10 if len(black_pawns[c]) > 1 else 0.30
                score -= base_bonus + (advance * 0.05)

    # -------------------------------------------------
    # 4. Pawn chain bonus
    # Reward pawns supported diagonally by another pawn.
    # -------------------------------------------------
    for r in range(8):
        for c in range(8):
            if board[r][c] == "wP":
                for dc in (-1, 1):
                    support_col = c + dc
                    support_row = r + 1
                    if 0 <= support_col < 8 and 0 <= support_row < 8:
                        if board[support_row][support_col] == "wP":
                            score += 0.15

            elif board[r][c] == "bP":
                for dc in (-1, 1):
                    support_col = c + dc
                    support_row = r - 1
                    if 0 <= support_col < 8 and 0 <= support_row < 8:
                        if board[support_row][support_col] == "bP":
                            score -= 0.15

    return score


def mobility_score(gs):
    """
    Reward having more legal moves than the opponent.
    """
    current_turn = gs.white_to_move

    gs.white_to_move = True
    white_moves = len(gs.get_valid_moves())

    gs.white_to_move = False
    black_moves = len(gs.get_valid_moves())

    gs.white_to_move = current_turn

    return 0.05 * (white_moves - black_moves)


def king_activity_score(gs, phase):
    """
    In the endgame, active kings matter much more.
    Reward the stronger side's king moving closer to the enemy king.
    """
    if phase != "endgame":
        return 0.0

    wk_r, wk_c = gs.white_king_location
    bk_r, bk_c = gs.black_king_location

    distance = abs(wk_r - bk_r) + abs(wk_c - bk_c)
    mat = material_score(gs.board)

    if mat > 1.0:
        return (14 - distance) * 0.04
    if mat < -1.0:
        return -(14 - distance) * 0.04
    return 0.0


def edge_pressure_score(gs):
    """
    Reward pushing the weaker king toward the edge in winning endgames.
    Useful especially in Forced-Win mode.
    """
    def edge_bonus(row, col):
        return max(abs(3.5 - row), abs(3.5 - col))

    mat = material_score(gs.board)
    score = 0.0

    if mat > 1.0:
        br, bc = gs.black_king_location
        score += edge_bonus(br, bc) * 0.20
    elif mat < -1.0:
        wr, wc = gs.white_king_location
        score -= edge_bonus(wr, wc) * 0.20

    return score


def evaluate_position(gs, mode="fair"):
    """
    Main evaluation function.

    Positive score = White better
    Negative score = Black better
    """
    if gs.checkmate:
        return -9999 if gs.white_to_move else 9999

    if gs.stalemate or gs.draw_by_repetition:
        return 0.0

    phase = get_game_phase(gs.board)

    mat = material_score(gs.board)
    pst = piece_square_score(gs.board, phase)
    center = center_control_score(gs.board)
    pawns = pawn_structure_score(gs.board)
    mobility = mobility_score(gs)
    king_activity = king_activity_score(gs, phase)
    edge_pressure = edge_pressure_score(gs)

    if mode == "fair":
        return (
            1.0 * mat
            + 0.6 * pst
            + 0.4 * center
            + 0.5 * pawns
        )

    if mode == "hard":
        return (
            1.0 * mat
            + 0.7 * pst
            + 0.5 * center
            + 0.7 * pawns
            + 0.8 * mobility
            + 0.6 * king_activity
        )

    # forced-win mode
    return (
        1.0 * mat
        + 0.7 * pst
        + 0.4 * center
        + 0.8 * pawns
        + 0.9 * mobility
        + 0.9 * king_activity
        + 1.2 * edge_pressure
    )


def explain_move(gs_before, move, gs_after, mode="fair"):
    """
    Generate a readable explanation for the AI's chosen move.
    """
    reasons = []
    phase = get_game_phase(gs_before.board)

    before_eval = evaluate_position(gs_before, mode)
    after_eval = evaluate_position(gs_after, mode)
    delta = after_eval - before_eval

    mover_is_white = move.piece_moved[0] == "w"

    if move.piece_captured != "--":
        reasons.append(f"wins material by capturing {move.piece_captured}")

    if move.is_castle_move:
        reasons.append("improves king safety by castling")

    if move.is_pawn_promotion:
        reasons.append(f"promotes a pawn to a {move.promotion_choice}")

    if phase == "opening":
        reasons.append("supports development and early positional control")
    elif phase == "middlegame":
        reasons.append("improves piece activity in the middlegame")
    else:
        reasons.append("strengthens endgame conversion")

    if mode == "forced":
        reasons.append("restricts the defending king and pushes the win")

    if mover_is_white and delta > 0.4:
        reasons.append("improves White's position significantly")
    elif not mover_is_white and delta < -0.4:
        reasons.append("improves Black's position significantly")

    if not reasons:
        reasons.append("improves the overall position")

    return "; ".join(reasons)
