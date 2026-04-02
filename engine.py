"""
engine.py

Core chess engine:
- Board state
- Legal move generation
- Check / checkmate / stalemate
- Castling
- En passant
- Promotion
"""

from copy import deepcopy

ROWS = 8
COLS = 8


class CastleRights:
    """
    Stores castling rights for both sides.
    """
    def __init__(self, wks, wqs, bks, bqs):
        self.wks = wks
        self.wqs = wqs
        self.bks = bks
        self.bqs = bqs

    def copy(self):
        return CastleRights(self.wks, self.wqs, self.bks, self.bqs)


class Move:
    """
    Represents a chess move.
    """

    ranks_to_rows = {
        "1": 7, "2": 6, "3": 5, "4": 4,
        "5": 3, "6": 2, "7": 1, "8": 0
    }
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}

    files_to_cols = {
        "a": 0, "b": 1, "c": 2, "d": 3,
        "e": 4, "f": 5, "g": 6, "h": 7
    }
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(
        self,
        start_sq,
        end_sq,
        board,
        is_en_passant_move=False,
        is_castle_move=False,
        promotion_choice="Q"
    ):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]

        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        self.is_pawn_promotion = False
        if self.piece_moved == "wP" and self.end_row == 0:
            self.is_pawn_promotion = True
        elif self.piece_moved == "bP" and self.end_row == 7:
            self.is_pawn_promotion = True

        self.promotion_choice = promotion_choice.upper()

        self.is_en_passant_move = is_en_passant_move
        if self.is_en_passant_move:
            self.piece_captured = "bP" if self.piece_moved == "wP" else "wP"

        self.is_castle_move = is_castle_move

        self.move_id = (
            self.start_row * 1000
            + self.start_col * 100
            + self.end_row * 10
            + self.end_col
        )

    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        return (
            self.move_id == other.move_id
            and self.promotion_choice == other.promotion_choice
        )

    def get_chess_notation(self):
        """
        Return move in coordinate notation (e.g. e2e4, e7e8q).
        """
        start = self.get_rank_file(self.start_row, self.start_col)
        end = self.get_rank_file(self.end_row, self.end_col)

        if self.is_castle_move:
            if self.end_col - self.start_col == 2:
                return "O-O"
            return "O-O-O"

        if self.is_pawn_promotion:
            return f"{start}{end}{self.promotion_choice.lower()}"
        return f"{start}{end}"

    @classmethod
    def get_rank_file(cls, r, c):
        return cls.cols_to_files[c] + cls.rows_to_ranks[r]


class GameState:
    """
    Stores the entire current state of the chess game.
    """

    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        self.move_functions = {
            "P": self.get_pawn_moves,
            "R": self.get_rook_moves,
            "N": self.get_knight_moves,
            "B": self.get_bishop_moves,
            "Q": self.get_queen_moves,
            "K": self.get_king_moves
        }

        self.white_to_move = True
        self.move_log = []

        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)

        self.checkmate = False
        self.stalemate = False
        self.draw_by_repetition = False

        self.en_passant_possible = ()
        self.en_passant_possible_log = [self.en_passant_possible]

        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [self.current_castling_rights.copy()]

        self.position_counts = {}
        self.record_current_position()

    def record_current_position(self):
        """
        Store a simplified position signature for repetition detection.
        """
        key = self.get_position_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def unrecord_current_position(self):
        """
        Undo position count entry when undoing a move.
        """
        key = self.get_position_key()
        if key in self.position_counts:
            self.position_counts[key] -= 1
            if self.position_counts[key] <= 0:
                del self.position_counts[key]

    def get_position_key(self):
        """
        Basic repetition key:
        board + side to move + castling rights + en passant square
        """
        board_str = "".join("".join(row) for row in self.board)
        side = "w" if self.white_to_move else "b"
        rights = (
            f"{int(self.current_castling_rights.wks)}"
            f"{int(self.current_castling_rights.wqs)}"
            f"{int(self.current_castling_rights.bks)}"
            f"{int(self.current_castling_rights.bqs)}"
        )
        ep = str(self.en_passant_possible)
        return f"{board_str}|{side}|{rights}|{ep}"

    def make_move(self, move):
        """
        Execute a move on the board.
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)

        # Update king location
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # Pawn promotion
        if move.is_pawn_promotion:
            promoted_piece = move.piece_moved[0] + move.promotion_choice
            self.board[move.end_row][move.end_col] = promoted_piece

        # En passant
        if move.is_en_passant_move:
            self.board[move.start_row][move.end_col] = "--"

        # Update en passant square
        if move.piece_moved[1] == "P" and abs(move.start_row - move.end_row) == 2:
            self.en_passant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.en_passant_possible = ()

        self.en_passant_possible_log.append(self.en_passant_possible)

        # Castling move
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:
                # King side
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:
                # Queen side
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        # Update castling rights
        self.update_castle_rights(move)
        self.castle_rights_log.append(self.current_castling_rights.copy())

        self.white_to_move = not self.white_to_move
        self.record_current_position()

    def undo_move(self):
        """
        Undo the most recent move.
        """
        if not self.move_log:
            return

        self.unrecord_current_position()

        move = self.move_log.pop()
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured

        self.white_to_move = not self.white_to_move

        # Restore king locations
        if move.piece_moved == "wK":
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.start_row, move.start_col)

        # Undo en passant
        if move.is_en_passant_move:
            self.board[move.end_row][move.end_col] = "--"
            self.board[move.start_row][move.end_col] = move.piece_captured

        self.en_passant_possible_log.pop()
        self.en_passant_possible = self.en_passant_possible_log[-1]

        # Undo castling rights
        self.castle_rights_log.pop()
        self.current_castling_rights = self.castle_rights_log[-1].copy()

        # Undo castling rook move
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = "--"
            else:
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"

        self.checkmate = False
        self.stalemate = False
        self.draw_by_repetition = False

    def update_castle_rights(self, move):
        """
        Update castling rights after a move or capture.
        """
        # If a king moves, that side loses both castling rights
        if move.piece_moved == "wK":
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif move.piece_moved == "bK":
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False

        # If a rook moves, that side may lose the relevant right
        elif move.piece_moved == "wR":
            if move.start_row == 7:
                if move.start_col == 0:
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:
                    self.current_castling_rights.wks = False

        elif move.piece_moved == "bR":
            if move.start_row == 0:
                if move.start_col == 0:
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:
                    self.current_castling_rights.bks = False

        # If a rook is captured, remove that side's corresponding right
        if move.piece_captured == "wR":
            if move.end_row == 7:
                if move.end_col == 0:
                    self.current_castling_rights.wqs = False
                elif move.end_col == 7:
                    self.current_castling_rights.wks = False

        elif move.piece_captured == "bR":
            if move.end_row == 0:
                if move.end_col == 0:
                    self.current_castling_rights.bqs = False
                elif move.end_col == 7:
                    self.current_castling_rights.bks = False

    def get_valid_moves(self):
        """
        Generate all legal moves for the current player.
        """
        temp_en_passant = self.en_passant_possible
        temp_castle_rights = self.current_castling_rights.copy()

        moves = self.get_all_possible_moves()

        if self.white_to_move:
            self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves)
        else:
            self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        legal_moves = []
        for move in moves:
            self.make_move(move)
            self.white_to_move = not self.white_to_move
            if not self.in_check(self.white_to_move):
                legal_moves.append(move)
            self.white_to_move = not self.white_to_move
            self.undo_move()

        self.en_passant_possible = temp_en_passant
        self.current_castling_rights = temp_castle_rights

        if len(legal_moves) == 0:
            if self.in_check(self.white_to_move):
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        return legal_moves

    def update_game_status(self):
        """
        Update game-ending conditions.
        """
        _ = self.get_valid_moves()

        key = self.get_position_key()
        if self.position_counts.get(key, 0) >= 3:
            self.draw_by_repetition = True
        else:
            self.draw_by_repetition = False

    def in_check(self, white_side):
        """
        Is the specified side's king currently in check?
        """
        if white_side:
            king_row, king_col = self.white_king_location
        else:
            king_row, king_col = self.black_king_location
        return self.square_under_attack(king_row, king_col, attacking_white=not white_side)

    def square_under_attack(self, row, col, attacking_white):
        """
        Determine whether a square is attacked by the specified side.
        """
        enemy_color = "w" if attacking_white else "b"
        ally_color = "b" if attacking_white else "w"

        # Pawn attacks
        pawn_dir = -1 if enemy_color == "w" else 1
        for dc in (-1, 1):
            r = row + pawn_dir
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if self.board[r][c] == enemy_color + "P":
                    return True

        # Knight attacks
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            r = row + dr
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if self.board[r][c] == enemy_color + "N":
                    return True

        # Straight-line attacks (rook, queen)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            for i in range(1, 8):
                r = row + dr * i
                c = col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                piece = self.board[r][c]
                if piece == "--":
                    continue
                if piece[0] == ally_color:
                    break
                if piece[0] == enemy_color and piece[1] in ("R", "Q"):
                    return True
                break

        # Diagonal attacks (bishop, queen)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            for i in range(1, 8):
                r = row + dr * i
                c = col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break
                piece = self.board[r][c]
                if piece == "--":
                    continue
                if piece[0] == ally_color:
                    break
                if piece[0] == enemy_color and piece[1] in ("B", "Q"):
                    return True
                break

        # King attacks
        king_moves = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        for dr, dc in king_moves:
            r = row + dr
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                if self.board[r][c] == enemy_color + "K":
                    return True

        return False

    def get_all_possible_moves(self):
        """
        Generate pseudo-legal moves without considering self-check.
        """
        moves = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece == "--":
                    continue

                color = piece[0]
                if (color == "w" and self.white_to_move) or (color == "b" and not self.white_to_move):
                    piece_type = piece[1]
                    self.move_functions[piece_type](row, col, moves)
        return moves

    def get_pawn_moves(self, row, col, moves):
        """
        Generate pawn moves including promotions and en passant.
        """
        if self.white_to_move:
            if row - 1 >= 0 and self.board[row - 1][col] == "--":
                moves.append(Move((row, col), (row - 1, col), self.board))
                if row == 6 and self.board[row - 2][col] == "--":
                    moves.append(Move((row, col), (row - 2, col), self.board))

            for dc in (-1, 1):
                if 0 <= col + dc < 8 and row - 1 >= 0:
                    end_piece = self.board[row - 1][col + dc]
                    if end_piece.startswith("b"):
                        moves.append(Move((row, col), (row - 1, col + dc), self.board))
                    if (row - 1, col + dc) == self.en_passant_possible:
                        moves.append(Move((row, col), (row - 1, col + dc), self.board, is_en_passant_move=True))
        else:
            if row + 1 < 8 and self.board[row + 1][col] == "--":
                moves.append(Move((row, col), (row + 1, col), self.board))
                if row == 1 and self.board[row + 2][col] == "--":
                    moves.append(Move((row, col), (row + 2, col), self.board))

            for dc in (-1, 1):
                if 0 <= col + dc < 8 and row + 1 < 8:
                    end_piece = self.board[row + 1][col + dc]
                    if end_piece.startswith("w"):
                        moves.append(Move((row, col), (row + 1, col + dc), self.board))
                    if (row + 1, col + dc) == self.en_passant_possible:
                        moves.append(Move((row, col), (row + 1, col + dc), self.board, is_en_passant_move=True))

    def get_rook_moves(self, row, col, moves):
        directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        enemy = "b" if self.white_to_move else "w"

        for dr, dc in directions:
            for i in range(1, 8):
                r = row + dr * i
                c = col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break

                end_piece = self.board[r][c]
                if end_piece == "--":
                    moves.append(Move((row, col), (r, c), self.board))
                elif end_piece[0] == enemy:
                    moves.append(Move((row, col), (r, c), self.board))
                    break
                else:
                    break

    def get_knight_moves(self, row, col, moves):
        knight_jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                        (1, -2), (1, 2), (2, -1), (2, 1)]
        ally = "w" if self.white_to_move else "b"

        for dr, dc in knight_jumps:
            r = row + dr
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                end_piece = self.board[r][c]
                if end_piece == "--" or end_piece[0] != ally:
                    moves.append(Move((row, col), (r, c), self.board))

    def get_bishop_moves(self, row, col, moves):
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        enemy = "b" if self.white_to_move else "w"

        for dr, dc in directions:
            for i in range(1, 8):
                r = row + dr * i
                c = col + dc * i
                if not (0 <= r < 8 and 0 <= c < 8):
                    break

                end_piece = self.board[r][c]
                if end_piece == "--":
                    moves.append(Move((row, col), (r, c), self.board))
                elif end_piece[0] == enemy:
                    moves.append(Move((row, col), (r, c), self.board))
                    break
                else:
                    break

    def get_queen_moves(self, row, col, moves):
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    def get_king_moves(self, row, col, moves):
        king_steps = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        ally = "w" if self.white_to_move else "b"

        for dr, dc in king_steps:
            r = row + dr
            c = col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                end_piece = self.board[r][c]
                if end_piece == "--" or end_piece[0] != ally:
                    moves.append(Move((row, col), (r, c), self.board))

    def get_castle_moves(self, row, col, moves):
        """
        Add castle moves if legal.
        """
        if self.square_under_attack(row, col, attacking_white=not self.white_to_move):
            return

        if self.white_to_move:
            if self.current_castling_rights.wks:
                self.get_kingside_castle_moves(row, col, moves)
            if self.current_castling_rights.wqs:
                self.get_queenside_castle_moves(row, col, moves)
        else:
            if self.current_castling_rights.bks:
                self.get_kingside_castle_moves(row, col, moves)
            if self.current_castling_rights.bqs:
                self.get_queenside_castle_moves(row, col, moves)

    def get_kingside_castle_moves(self, row, col, moves):
        if col + 2 < 8:
            if self.board[row][col + 1] == "--" and self.board[row][col + 2] == "--":
                if (
                    not self.square_under_attack(row, col + 1, attacking_white=not self.white_to_move)
                    and not self.square_under_attack(row, col + 2, attacking_white=not self.white_to_move)
                ):
                    moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def get_queenside_castle_moves(self, row, col, moves):
        if col - 3 >= 0:
            if (
                self.board[row][col - 1] == "--"
                and self.board[row][col - 2] == "--"
                and self.board[row][col - 3] == "--"
            ):
                if (
                    not self.square_under_attack(row, col - 1, attacking_white=not self.white_to_move)
                    and not self.square_under_attack(row, col - 2, attacking_white=not self.white_to_move)
                ):
                    moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))
