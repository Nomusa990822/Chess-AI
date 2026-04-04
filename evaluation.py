"""
Advanced position evaluation for the Chess AI project.

Features:
- material
- piece-square tables
- center control
- advanced pawn structure evaluation
- bishop pair bonus
- rook open/semi-open file bonus
- rook on 7th rank bonus
- knight outpost bonus
- king pawn shield
- mobility
- game phase awareness
- endgame king activity
- edge pressure in winning endgames
- evaluation breakdown printing
- move explanation support
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
            value = PIECE_VALUES[piece[1]]
            score += value if piece[0] == "w" else -value
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
                score += 0.10 if piece[0] == "w" else -0.10

    return score


def pawn_structure_score(board):
    score = 0.0

    white_pawns = {c: [] for c in range(8)}
    black_pawns = {c: [] for c in range(8)}

    for r in range(8):
        for c in range(8):
            if board[r][c] == "wP":
                white_pawns[c].append(r)
            elif board[r][c] == "bP":
                black_pawns[c].append(r)

    # Doubled pawns
    for c in range(8):
        if len(white_pawns[c]) > 1:
            score -= 0.35 * (len(white_pawns[c]) - 1)
        if len(black_pawns[c]) > 1:
            score += 0.35 * (len(black_pawns[c]) - 1)

    # Isolated pawns
    for c in range(8):
        for _r in white_pawns[c]:
            isolated = True
            for adj in (c - 1, c + 1):
                if 0 <= adj < 8 and len(white_pawns[adj]) > 0:
                    isolated = False
                    break
            if isolated:
                score -= 0.20

        for _r in black_pawns[c]:
            isolated = True
            for adj in (c - 1, c + 1):
                if 0 <= adj < 8 and len(black_pawns[adj]) > 0:
                    isolated = False
                    break
            if isolated:
                score += 0.20

    # Passed pawns with scaling by rank
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
                advance = 7 - r
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
                advance = r
                base_bonus = 0.10 if len(black_pawns[c]) > 1 else 0.30
                score -= base_bonus + (advance * 0.05)

    # Pawn chains
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


def bishop_pair_bonus(board):
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
        score += 0.35
    if black_bishops >= 2:
        score -= 0.35
    return score


def rook_file_bonus(board):
    score = 0.0

    for c in range(8):
        white_pawn_on_file = False
        black_pawn_on_file = False
        white_rooks = 0
        black_rooks = 0

        for r in range(8):
            piece = board[r][c]
            if piece == "wP":
                white_pawn_on_file = True
            elif piece == "bP":
                black_pawn_on_file = True
            elif piece == "wR":
                white_rooks += 1
            elif piece == "bR":
                black_rooks += 1

        if white_rooks > 0:
            if not white_pawn_on_file and not black_pawn_on_file:
                score += 0.30 * white_rooks
            elif not white_pawn_on_file and black_pawn_on_file:
                score += 0.15 * white_rooks

        if black_rooks > 0:
            if not white_pawn_on_file and not black_pawn_on_file:
                score -= 0.30 * black_rooks
            elif not black_pawn_on_file and white_pawn_on_file:
                score -= 0.15 * black_rooks

    return score


def rook_seventh_rank_bonus(board):
    score = 0.0
    for c in range(8):
        if board[1][c] == "wR":
            score += 0.20
        if board[6][c] == "bR":
            score -= 0.20
    return score


def knight_outpost_bonus(board):
    score = 0.0

    for r in range(8):
        for c in range(8):
            piece = board[r][c]

            if piece == "wN":
                if r <= 4:
                    supported = False
                    for dc in (-1, 1):
                        sr = r + 1
                        sc = c + dc
                        if 0 <= sr < 8 and 0 <= sc < 8 and board[sr][sc] == "wP":
                            supported = True

                    enemy_pawn_can_chase = False
                    for dc in (-1, 1):
                        er = r - 1
                        ec = c + dc
                        if 0 <= er < 8 and 0 <= ec < 8 and board[er][ec] == "bP":
                            enemy_pawn_can_chase = True

                    if supported and not enemy_pawn_can_chase:
                        score += 0.25

            elif piece == "bN":
                if r >= 3:
                    supported = False
                    for dc in (-1, 1):
                        sr = r - 1
                        sc = c + dc
                        if 0 <= sr < 8 and 0 <= sc < 8 and board[sr][sc] == "bP":
                            supported = True

                    enemy_pawn_can_chase = False
                    for dc in (-1, 1):
                        er = r + 1
                        ec = c + dc
                        if 0 <= er < 8 and 0 <= ec < 8 and board[er][ec] == "wP":
                            enemy_pawn_can_chase = True

                    if supported and not enemy_pawn_can_chase:
                        score -= 0.25

    return score


def king_pawn_shield_score(gs, phase):
    if phase == "endgame":
        return 0.0

    score = 0.0

    wr, wc = gs.white_king_location
    white_shield = 0
    for dc in (-1, 0, 1):
        rr = wr - 1
        cc = wc + dc
        if 0 <= rr < 8 and 0 <= cc < 8 and gs.board[rr][cc] == "wP":
            white_shield += 1
    score += 0.12 * white_shield

    br, bc = gs.black_king_location
    black_shield = 0
    for dc in (-1, 0, 1):
        rr = br + 1
        cc = bc + dc
        if 0 <= rr < 8 and 0 <= cc < 8 and gs.board[rr][cc] == "bP":
            black_shield += 1
    score -= 0.12 * black_shield

    return score


def mobility_score(gs):
    current_turn = gs.white_to_move

    gs.white_to_move = True
    white_moves = len(gs.get_valid_moves())

    gs.white_to_move = False
    black_moves = len(gs.get_valid_moves())

    gs.white_to_move = current_turn

    return 0.05 * (white_moves - black_moves)


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


def edge_pressure_score(gs):
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


def get_evaluation_weights(mode):
    if mode == "fair":
        return {
            "Material": 1.0,
            "Piece-Square": 0.6,
            "Center Control": 0.4,
            "Pawns": 0.5,
            "Bishops": 0.2,
            "Rooks": 0.2,
            "Knights": 0.2,
            "King Shield": 0.2,
            "Mobility": 0.0,
            "King Activity": 0.0,
            "Edge Pressure": 0.0
        }

    if mode == "hard":
        return {
            "Material": 1.0,
            "Piece-Square": 0.7,
            "Center Control": 0.5,
            "Pawns": 0.7,
            "Bishops": 0.4,
            "Rooks": 0.4,
            "Knights": 0.4,
            "King Shield": 0.5,
            "Mobility": 0.8,
            "King Activity": 0.6,
            "Edge Pressure": 0.0
        }

    return {
        "Material": 1.0,
        "Piece-Square": 0.7,
        "Center Control": 0.4,
        "Pawns": 0.8,
        "Bishops": 0.4,
        "Rooks": 0.4,
        "Knights": 0.4,
        "King Shield": 0.4,
        "Mobility": 0.9,
        "King Activity": 0.9,
        "Edge Pressure": 1.2
    }


def evaluate_breakdown(gs, mode="fair"):
    """
    Returns a weighted breakdown of the position evaluation.
    """
    if gs.checkmate:
        total = -9999 if gs.white_to_move else 9999
        return {"Total": total}

    if gs.stalemate or gs.draw_by_repetition:
        return {"Total": 0.0}

    phase = get_game_phase(gs.board)

    raw = {
        "Material": material_score(gs.board),
        "Piece-Square": piece_square_score(gs.board, phase),
        "Center Control": center_control_score(gs.board),
        "Pawns": pawn_structure_score(gs.board),
        "Bishops": bishop_pair_bonus(gs.board),
        "Rooks": rook_file_bonus(gs.board) + rook_seventh_rank_bonus(gs.board),
        "Knights": knight_outpost_bonus(gs.board),
        "King Shield": king_pawn_shield_score(gs, phase),
        "Mobility": mobility_score(gs),
        "King Activity": king_activity_score(gs, phase),
        "Edge Pressure": edge_pressure_score(gs)
    }

    weights = get_evaluation_weights(mode)

    weighted = {}
    total = 0.0

    for key, value in raw.items():
        weighted_value = value * weights[key]
        weighted[key] = weighted_value
        total += weighted_value

    weighted["Total"] = total
    return weighted


def evaluate_position(gs, mode="fair"):
    """
    Main evaluation function.
    Positive = White better
    Negative = Black better
    """
    breakdown = evaluate_breakdown(gs, mode)
    return breakdown["Total"]


def print_evaluation_breakdown(gs, mode="fair"):
    """
    Pretty-print the weighted evaluation breakdown.
    Clarifies that this is STATIC evaluation (not search).
    """
    breakdown = evaluate_breakdown(gs, mode)

    print("\nStatic Evaluation Breakdown (current position):")

    for key, value in breakdown.items():
        if key != "Total":
            print(f"{key:15}: {value:+.2f}")

    print("-" * 32)
    print(f"{'Static Total':15}: {breakdown['Total']:+.2f}")


def explain_move(gs_before, move, gs_after, mode="fair"):
    """
    Explain why the move was chosen using the change in evaluation breakdown.
    """
    reasons = []
    phase = get_game_phase(gs_before.board)

    before = evaluate_breakdown(gs_before, mode)
    after = evaluate_breakdown(gs_after, mode)

    mover_is_white = move.piece_moved[0] == "w"
    improving_threshold = 0.08

    if move.piece_captured != "--":
        reasons.append(f"wins material by capturing {move.piece_captured}")

    if move.is_castle_move:
        reasons.append("improves king safety by castling")

    if move.is_pawn_promotion:
        reasons.append(f"promotes a pawn to a {move.promotion_choice}")

    component_deltas = []
    for key in before:
        if key == "Total":
            continue
        delta = after[key] - before[key]
        component_deltas.append((key, delta))

    if mover_is_white:
        positive_components = sorted(component_deltas, key=lambda x: x[1], reverse=True)
        for name, delta in positive_components:
            if delta > improving_threshold:
                if name == "Material":
                    reasons.append("improves the material balance")
                elif name == "Piece-Square":
                    reasons.append("places pieces on better squares")
                elif name == "Center Control":
                    reasons.append("improves central control")
                elif name == "Pawns":
                    reasons.append("improves the pawn structure")
                elif name == "Bishops":
                    reasons.append("improves bishop coordination")
                elif name == "Rooks":
                    reasons.append("activates the rooks")
                elif name == "Knights":
                    reasons.append("improves knight activity")
                elif name == "King Shield":
                    reasons.append("improves king safety")
                elif name == "Mobility":
                    reasons.append("increases move flexibility")
                elif name == "King Activity":
                    reasons.append("improves king activity")
                elif name == "Edge Pressure":
                    reasons.append("pushes the enemy king toward the edge")
                if len(reasons) >= 4:
                    break
    else:
        negative_components = sorted(component_deltas, key=lambda x: x[1])
        for name, delta in negative_components:
            if delta < -improving_threshold:
                if name == "Material":
                    reasons.append("improves the material balance")
                elif name == "Piece-Square":
                    reasons.append("places pieces on better squares")
                elif name == "Center Control":
                    reasons.append("improves central control")
                elif name == "Pawns":
                    reasons.append("improves the pawn structure")
                elif name == "Bishops":
                    reasons.append("improves bishop coordination")
                elif name == "Rooks":
                    reasons.append("activates the rooks")
                elif name == "Knights":
                    reasons.append("improves knight activity")
                elif name == "King Shield":
                    reasons.append("improves king safety")
                elif name == "Mobility":
                    reasons.append("increases move flexibility")
                elif name == "King Activity":
                    reasons.append("improves king activity")
                elif name == "Edge Pressure":
                    reasons.append("pushes the enemy king toward the edge")
                if len(reasons) >= 4:
                    break

    if phase == "opening":
        reasons.append("fits the opening plan")
    elif phase == "middlegame":
        reasons.append("strengthens the middlegame position")
    else:
        reasons.append("improves endgame conversion")

    if mode == "forced":
        reasons.append("supports the forced-win strategy")

    # Remove duplicates while keeping order
    unique_reasons = []
    seen = set()
    for reason in reasons:
        if reason not in seen:
            unique_reasons.append(reason)
            seen.add(reason)

    if not unique_reasons:
        return "chosen because it improves the overall position"

    return "; ".join(unique_reasons[:5])
