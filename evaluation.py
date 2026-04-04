"""
Stronger position evaluation for the Chess AI project.

Includes:
- material
- piece-square tables
- center control
- pawn structure:
    * doubled pawns
    * isolated pawns
    * pawn chains
    * passed pawns scaled by rank
- bishop pair
- rook activity
- mobility
- game phase awareness
- king safety / king activity
- endgame conversion pressure
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
    score = 0.0
    for row in board:
        for piece in row:
            if piece == "--":
                continue
            score += PIECE_VALUES[piece[1]] if piece[0] == "w" else -PIECE_VALUES[piece[1]]
    return score


def piece_square_score(board, phase):
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
    score = 0.0
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue
            if (r, c) in CENTER_SQUARES:
                score += 0.25 if piece[0] == "w" else -0.25
            elif (r, c) in EXTENDED_CENTER:
                score += 0.1 if piece[0] == "w" else -0.1
    return score


def build_pawn_maps(board):
    white_pawns = {c: [] for c in range(8)}
    black_pawns = {c: [] for c in range(8)}

    for r in range(8):
        for c in range(8):
            if board[r][c] == "wP":
                white_pawns[c].append(r)
            elif board[r][c] == "bP":
                black_pawns[c].append(r)

    return white_pawns, black_pawns


def is_isolated(file_index, pawn_map):
    left_empty = (file_index - 1 < 0) or (len(pawn_map[file_index - 1]) == 0)
    right_empty = (file_index + 1 > 7) or (len(pawn_map[file_index + 1]) == 0)
    return left_empty and right_empty


def has_white_chain_support(r, c, board):
    supporters = []
    if r + 1 < 8 and c - 1 >= 0:
        supporters.append(board[r + 1][c - 1] == "wP")
    if r + 1 < 8 and c + 1 < 8:
        supporters.append(board[r + 1][c + 1] == "wP")
    return any(supporters)


def has_black_chain_support(r, c, board):
    supporters = []
    if r - 1 >= 0 and c - 1 >= 0:
        supporters.append(board[r - 1][c - 1] == "bP")
    if r - 1 >= 0 and c + 1 < 8:
        supporters.append(board[r - 1][c + 1] == "bP")
    return any(supporters)


def white_passed_pawn_bonus(r):
    advancement = 6 - r
    return 0.15 + advancement * 0.06


def black_passed_pawn_bonus(r):
    advancement = r - 1
    return 0.15 + advancement * 0.06


def pawn_structure_score(board):
    score = 0.0
    white_pawns, black_pawns = build_pawn_maps(board)

    # Doubled pawns
    for c in range(8):
        if len(white_pawns[c]) > 1:
            score -= 0.35 * (len(white_pawns[c]) - 1)
        if len(black_pawns[c]) > 1:
            score += 0.35 * (len(black_pawns[c]) - 1)

    # Isolated pawns
    for c in range(8):
        if white_pawns[c] and is_isolated(c, white_pawns):
            score -= 0.20 * len(white_pawns[c])
        if black_pawns[c] and is_isolated(c, black_pawns):
            score += 0.20 * len(black_pawns[c])

    # White pawn features
    for c in range(8):
        for r in white_pawns[c]:
            doubled = len(white_pawns[c]) > 1

            # Passed pawn
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
                bonus = white_passed_pawn_bonus(r)
                if doubled:
                    bonus *= 0.45
                score += bonus

            # Pawn chain bonus
            if has_white_chain_support(r, c, board):
                score += 0.10

    # Black pawn features
    for c in range(8):
        for r in black_pawns[c]:
            doubled = len(black_pawns[c]) > 1

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
                bonus = black_passed_pawn_bonus(r)
                if doubled:
                    bonus *= 0.45
                score -= bonus

            if has_black_chain_support(r, c, board):
                score -= 0.10

    return score


def bishop_pair_score(board):
    white_bishops = 0
    black_bishops = 0

    for row in board:
        for piece in row:
            if piece == "wB":
                white_bishops += 1
            elif piece == "bB":
                black_bishops += 1

    score = 0.0
    if white_bishops >= 2:
        score += 0.30
    if black_bishops >= 2:
        score -= 0.30
    return score


def rook_activity_score(board):
    score = 0.0
    white_pawns, black_pawns = build_pawn_maps(board)

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--" or piece[1] != "R":
                continue

            own_pawns = white_pawns if piece[0] == "w" else black_pawns
            opp_pawns = black_pawns if piece[0] == "w" else white_pawns

            own_file_empty = len(own_pawns[c]) == 0
            opp_file_empty = len(opp_pawns[c]) == 0

            bonus = 0.0
            if own_file_empty and opp_file_empty:
                bonus += 0.30  # open file
            elif own_file_empty:
                bonus += 0.18  # semi-open file

            if piece[0] == "w" and r == 1:
                bonus += 0.20  # 7th rank
            if piece[0] == "b" and r == 6:
                bonus += 0.20  # 2nd rank from black perspective

            score += bonus if piece[0] == "w" else -bonus

    return score


def knight_outpost_score(board):
    score = 0.0

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece not in ("wN", "bN"):
                continue

            if piece == "wN":
                if r in (2, 3, 4) and c in (2, 3, 4, 5):
                    # supported by pawn?
                    supported = False
                    if r + 1 < 8 and c - 1 >= 0 and board[r + 1][c - 1] == "wP":
                        supported = True
                    if r + 1 < 8 and c + 1 < 8 and board[r + 1][c + 1] == "wP":
                        supported = True
                    if supported:
                        score += 0.20

            if piece == "bN":
                if r in (3, 4, 5) and c in (2, 3, 4, 5):
                    supported = False
                    if r - 1 >= 0 and c - 1 >= 0 and board[r - 1][c - 1] == "bP":
                        supported = True
                    if r - 1 >= 0 and c + 1 < 8 and board[r - 1][c + 1] == "bP":
                        supported = True
                    if supported:
                        score -= 0.20

    return score


def mobility_score(gs):
    current_turn = gs.white_to_move

    gs.white_to_move = True
    white_moves = len(gs.get_valid_moves())

    gs.white_to_move = False
    black_moves = len(gs.get_valid_moves())

    gs.white_to_move = current_turn

    return 0.05 * (white_moves - black_moves)


def king_safety_score(gs, phase):
    if phase == "endgame":
        return 0.0

    score = 0.0

    wk_r, wk_c = gs.white_king_location
    bk_r, bk_c = gs.black_king_location

    # Penalize central kings in opening / middlegame
    white_penalty = 0.0
    black_penalty = 0.0

    if wk_c in (3, 4) and wk_r > 1:
        white_penalty += 0.25
    if bk_c in (3, 4) and bk_r < 6:
        black_penalty += 0.25

    # Slight reward if king looks castled
    if (wk_r, wk_c) in ((7, 6), (7, 2)):
        white_penalty -= 0.15
    if (bk_r, bk_c) in ((0, 6), (0, 2)):
        black_penalty -= 0.15

    score -= white_penalty
    score += black_penalty

    return score


def king_activity_score(gs, phase):
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


def enemy_king_escape_squares(gs, white_attacking):
    if white_attacking:
        kr, kc = gs.black_king_location
        enemy_is_white = False
    else:
        kr, kc = gs.white_king_location
        enemy_is_white = True

    escape_count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r, c = kr + dr, kc + dc
            if 0 <= r < 8 and 0 <= c < 8:
                piece = gs.board[r][c]
                if piece == "--" or (piece[0] == ("w" if enemy_is_white else "b")):
                    if not gs.square_under_attack(r, c, attacking_white=white_attacking):
                        escape_count += 1
    return escape_count


def edge_pressure_score(gs):
    def edge_bonus(row, col):
        return max(abs(3.5 - row), abs(3.5 - col))

    mat = material_score(gs.board)
    score = 0.0

    if mat > 1.0:
        br, bc = gs.black_king_location
        score += edge_bonus(br, bc) * 0.2
        score += (8 - enemy_king_escape_squares(gs, white_attacking=True)) * 0.05
    elif mat < -1.0:
        wr, wc = gs.white_king_location
        score -= edge_bonus(wr, wc) * 0.2
        score -= (8 - enemy_king_escape_squares(gs, white_attacking=False)) * 0.05

    return score


def evaluate_position(gs, mode="fair"):
    """
    Positive = White better
    Negative = Black better
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
    bishops = bishop_pair_score(gs.board)
    rooks = rook_activity_score(gs.board)
    outposts = knight_outpost_score(gs.board)
    mobility = mobility_score(gs)
    king_safety = king_safety_score(gs, phase)
    king_activity = king_activity_score(gs, phase)
    edge_pressure = edge_pressure_score(gs)

    if mode == "fair":
        return (
            1.0 * mat
            + 0.6 * pst
            + 0.4 * center
            + 0.7 * pawns
            + 0.3 * bishops
            + 0.2 * rooks
            + 0.2 * outposts
            + 0.2 * king_safety
        )

    if mode == "hard":
        return (
            1.0 * mat
            + 0.7 * pst
            + 0.5 * center
            + 0.9 * pawns
            + 0.4 * bishops
            + 0.35 * rooks
            + 0.25 * outposts
            + 0.8 * mobility
            + 0.45 * king_safety
            + 0.6 * king_activity
        )

    return (
        1.0 * mat
        + 0.7 * pst
        + 0.4 * center
        + 1.0 * pawns
        + 0.4 * bishops
        + 0.35 * rooks
        + 0.25 * outposts
        + 0.9 * mobility
        + 0.35 * king_safety
        + 0.9 * king_activity
        + 1.2 * edge_pressure
    )


def explain_move(gs_before, move, gs_after, mode="fair"):
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
        reasons.append("supports development and positional control")
    elif phase == "middlegame":
        reasons.append("improves piece activity and coordination")
    else:
        reasons.append("strengthens endgame conversion")

    if mode == "forced":
        reasons.append("restricts the defending king and presses the winning plan")

    if mover_is_white and delta > 0.4:
        reasons.append("improves White's position significantly")
    elif (not mover_is_white) and delta < -0.4:
        reasons.append("improves Black's position significantly")

    if not reasons:
        reasons.append("improves the overall position")

    return "; ".join(reasons)
