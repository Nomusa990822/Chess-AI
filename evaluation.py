"""
evaluation.py

Heuristic evaluation for the chess AI.
Scores are positive for White advantage and negative for Black advantage.
"""

PIECE_VALUES = {
    "K": 0,
    "Q": 9.0,
    "R": 5.0,
    "B": 3.25,
    "N": 3.0,
    "P": 1.0
}

CENTER_SQUARES = {(3, 3), (3, 4), (4, 3), (4, 4)}

# Piece-square tables (white perspective; black uses mirrored version)
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

KING_TABLE_MIDDLEGAME = [
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.3, -0.4, -0.4, -0.5, -0.5, -0.4, -0.4, -0.3],
    [-0.2, -0.3, -0.3, -0.4, -0.4, -0.3, -0.3, -0.2],
    [-0.1, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.1],
    [0.2, 0.2, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2],
    [0.2, 0.3, 0.1, 0.0, 0.0, 0.1, 0.3, 0.2]
]

KING_TABLE_ENDGAME = [
    [-0.5, -0.3, -0.3, -0.3, -0.3, -0.3, -0.3, -0.5],
    [-0.3, -0.1, 0.0, 0.0, 0.0, 0.0, -0.1, -0.3],
    [-0.3, 0.0, 0.2, 0.3, 0.3, 0.2, 0.0, -0.3],
    [-0.3, 0.0, 0.3, 0.4, 0.4, 0.3, 0.0, -0.3],
    [-0.3, 0.0, 0.3, 0.4, 0.4, 0.3, 0.0, -0.3],
    [-0.3, 0.0, 0.2, 0.3, 0.3, 0.2, 0.0, -0.3],
    [-0.3, -0.1, 0.0, 0.0, 0.0, 0.0, -0.1, -0.3],
    [-0.5, -0.3, -0.3, -0.3, -0.3, -0.3, -0.3, -0.5]
]

PIECE_SQUARE_TABLES = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE
}


def mirror_row(row):
    return 7 - row


def get_piece_square_bonus(piece_type, row, col, is_white, endgame=False):
    if piece_type == "K":
        table = KING_TABLE_ENDGAME if endgame else KING_TABLE_MIDDLEGAME
    else:
        table = PIECE_SQUARE_TABLES.get(piece_type)

    if table is None:
        return 0.0

    if is_white:
        return table[row][col]
    return table[mirror_row(row)][col]


def is_endgame(board):
    """
    Very simple endgame detector.
    """
    queens = 0
    minor_major_count = 0

    for row in board:
        for piece in row:
            if piece == "--":
                continue
            if piece[1] == "Q":
                queens += 1
            if piece[1] in ("R", "B", "N"):
                minor_major_count += 1

    return queens == 0 or minor_major_count <= 4


def count_material(board):
    score = 0.0
    for row in board:
        for piece in row:
            if piece == "--":
                continue
            value = PIECE_VALUES[piece[1]]
            score += value if piece[0] == "w" else -value
    return score


def center_control_score(board):
    score = 0.0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue
            if (r, c) in CENTER_SQUARES:
                bonus = 0.2
                score += bonus if piece[0] == "w" else -bonus
    return score


def pawn_structure_score(board):
    """
    Basic pawn structure:
    - reward passed pawns
    - penalize doubled pawns
    """
    score = 0.0

    white_pawns_by_file = {c: [] for c in range(8)}
    black_pawns_by_file = {c: [] for c in range(8)}

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "wP":
                white_pawns_by_file[c].append(r)
            elif piece == "bP":
                black_pawns_by_file[c].append(r)

    # Doubled pawns
    for c in range(8):
        if len(white_pawns_by_file[c]) > 1:
            score -= 0.15 * (len(white_pawns_by_file[c]) - 1)
        if len(black_pawns_by_file[c]) > 1:
            score += 0.15 * (len(black_pawns_by_file[c]) - 1)

    # Passed pawns
    for c in range(8):
        for r in white_pawns_by_file[c]:
            blocked = False
            for adj in (c - 1, c, c + 1):
                if 0 <= adj < 8:
                    for br in black_pawns_by_file[adj]:
                        if br < r:
                            blocked = True
                            break
                if blocked:
                    break
            if not blocked:
                score += 0.25

        for r in black_pawns_by_file[c]:
            blocked = False
            for adj in (c - 1, c, c + 1):
                if 0 <= adj < 8:
                    for wr in white_pawns_by_file[adj]:
                        if wr > r:
                            blocked = True
                            break
                if blocked:
                    break
            if not blocked:
                score -= 0.25

    return score


def king_distance_bonus(gs):
    """
    Useful especially in endgames and forced-win mode.
    Reward bringing the stronger side's king closer to the enemy king.
    """
    wk = gs.white_king_location
    bk = gs.black_king_location

    distance = abs(wk[0] - bk[0]) + abs(wk[1] - bk[1])
    material = count_material(gs.board)

    if material > 1:
        return (14 - distance) * 0.03
    if material < -1:
        return -(14 - distance) * 0.03
    return 0.0


def king_corner_pressure(gs):
    """
    In strong winning endgames, pushing the enemy king toward the edge matters.
    """
    br, bc = gs.black_king_location
    wr, wc = gs.white_king_location

    def edge_score(r, c):
        return max(abs(3.5 - r), abs(3.5 - c))

    score = 0.0
    material = count_material(gs.board)

    if material > 1:
        score += edge_score(br, bc) * 0.15
    elif material < -1:
        score -= edge_score(wr, wc) * 0.15

    return score


def mobility_score(gs):
    """
    Compare move counts for each side.
    """
    current_turn = gs.white_to_move

    white_count = 0
    black_count = 0

    gs.white_to_move = True
    white_count = len(gs.get_valid_moves())

    gs.white_to_move = False
    black_count = len(gs.get_valid_moves())

    gs.white_to_move = current_turn
    return 0.05 * (white_count - black_count)


def piece_square_score(board):
    endgame = is_endgame(board)
    score = 0.0

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue
            color = piece[0]
            ptype = piece[1]
            bonus = get_piece_square_bonus(ptype, r, c, color == "w", endgame)
            score += bonus if color == "w" else -bonus

    return score


def evaluate_position(gs, mode="fair"):
    """
    Evaluate the current position from White's perspective.
    Positive = White better
    Negative = Black better
    """
    if gs.checkmate:
        if gs.white_to_move:
            return -9999
        return 9999

    if gs.stalemate or gs.draw_by_repetition:
        return 0

    material = count_material(gs.board)
    pst = piece_square_score(gs.board)
    center = center_control_score(gs.board)
    pawns = pawn_structure_score(gs.board)
    king_distance = king_distance_bonus(gs)
    corner_pressure = king_corner_pressure(gs)

    if mode == "fair":
        return material + 0.6 * pst + 0.5 * center + 0.5 * pawns

    if mode == "hard":
        mobility = mobility_score(gs)
        return (
            material
            + 0.7 * pst
            + 0.6 * center
            + 0.6 * pawns
            + 0.8 * mobility
            + 0.4 * king_distance
        )

    # forced-win mode
    mobility = mobility_score(gs)
    return (
        material
        + 0.7 * pst
        + 0.4 * center
        + 0.5 * pawns
        + 0.9 * mobility
        + 1.0 * king_distance
        + 1.2 * corner_pressure
    )


def explain_move(gs_before, move, gs_after, mode="fair"):
    """
    Human-readable AI move explanation.
    """
    moved = move.piece_moved
    captured = move.piece_captured

    reasons = []

    if captured != "--":
        reasons.append(f"wins material by capturing {captured}")

    if move.is_castle_move:
        reasons.append("improves king safety by castling")

    if move.is_pawn_promotion:
        reasons.append(f"promotes a pawn to a {move.promotion_choice}")

    before_score = evaluate_position(gs_before, mode)
    after_score = evaluate_position(gs_after, mode)

    if after_score > before_score + 0.5 and moved[0] == "w":
        reasons.append("improves White's position significantly")
    elif after_score < before_score - 0.5 and moved[0] == "b":
        reasons.append("improves Black's position significantly")

    if mode == "forced":
        reasons.append("tightens control in the winning endgame")

    if not reasons:
        reasons.append("improves piece activity and overall position")

    return "; ".join(reasons)
