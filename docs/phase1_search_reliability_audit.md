# Phase 1 — Search Reliability Audit

**Repository:** Nomusa990822/Chess-AI  
**Working branch:** `phase-1/search-reliability`  
**Scope:** Search correctness, timeout safety, quiescence-search legality, and regression coverage.

## Baseline preservation

Phase 1 work is isolated on `phase-1/search-reliability`. The default branch has not been modified. The branch was created from `main` before any Phase 1 code changes.

The previously reported 49 passing tests are historical user-provided evidence. They have not been rerun in this audit environment and must not be represented as a fresh test result.

## Findings

### P1 — Incomplete root iterations can be accepted

In `choose_ai_move`, the root loop breaks when the deadline is reached, but the code subsequently accepts `current_best_move` whenever at least one root move was searched. That result may represent only a subset of legal root moves at the current depth.

**Required correction:** Treat each iterative-deepening depth as an atomic iteration. Publish its move, score, candidate list, and principal variation only after every required root move has completed. If the deadline interrupts an iteration, discard that iteration and retain the result from the last fully completed depth.

### P1 — Recursive timeout is converted into an ordinary evaluation

In `minimax` and `quiescence_search`, a deadline check currently returns a static evaluation. Parent nodes cannot distinguish that incomplete result from a completed search result. This can contaminate scores, principal variations, and transposition-table entries.

**Required correction:** Propagate a dedicated search-timeout signal. Ensure every speculative move is undone in a `finally` block. Do not store incomplete nodes in the transposition table.

### P1 — Quiescence search does not handle check evasions

The current quiescence routine always calculates a stand-pat score and searches only captures/promotions. When the side to move is in check, standing pat is illegal and all legal check evasions must be considered, including quiet king moves and interpositions.

**Required correction:** Detect check before stand-pat evaluation. In check, search all legal evasions and do not permit stand-pat cutoffs. At a configured quiescence safety limit, return a documented bounded fallback only after handling terminal state; add tests that prove legal evasions are searched.

### P2 — Terminal positions need explicit search scoring

Search terminal handling currently delegates to `evaluate_position`. The search layer should explicitly distinguish checkmate from stalemate and repetition, and score mate by distance where practical. This avoids depending on heuristic evaluation to encode game-theoretic terminal outcomes.

### P2 — Board-state integrity needs regression coverage

Timeouts can occur at arbitrary recursion points. Tests must assert that the board, side to move, move log, king locations, en-passant state, castling rights, and repetition counts are restored after search, including when timeout interrupts recursion.

## Phase 1 implementation order

1. Add search-timeout propagation and guaranteed make/undo safety.
2. Make iterative-deepening root iterations atomic.
3. Correct quiescence search for check, checkmate, stalemate, and quiet evasions.
4. Add focused regression tests for each defect.
5. Run the complete existing test suite and new tests in the project environment.
6. Record measured results and update the search documentation.

## Acceptance criteria

- A partially searched root depth is never reported as completed.
- The last fully completed iteration remains available after timeout.
- Timeout cannot be mistaken for a valid leaf evaluation.
- No incomplete search result is written to the transposition table.
- Quiescence search never stands pat while in check.
- Quiescence search considers all legal evasions while in check.
- Search leaves the supplied game state unchanged, including after an interrupted search.
- Existing gameplay and evaluation tests remain passing.

## Audit limitations

This is a source-level audit. No local project environment or GitHub Actions execution was available during this inspection, so no new runtime or performance claims are made.


## Perft validation update

The first complex-position fixture was labelled Kiwipete and asserted the commonly
quoted 48/2039 node counts. An independent python-chess comparison established
that the exact FEN stored in that test has 45 legal root moves, and the engine's
root legal-move set matches the oracle exactly. The discrepancy was therefore in
the fixture/reference-count pairing, not a demonstrated root move-generation
defect. The test has been corrected to compare recursive perft counts at depths
1–3 against python-chess for the exact FEN. This avoids asserting reference
counts that do not belong to the tested position. The independent library is
installed only in CI as a test oracle; it is not a runtime dependency.

## Special-move oracle validation update

A follow-up review found that castling generation trusted castling-rights flags
without verifying that the king remained on its original square or that the
corresponding rook remained on its original corner. This could generate
impossible castling moves in custom positions with stale rights. The generator
now requires the king and rook to occupy their original squares before
considering path and attack constraints.

The perft FEN test helper now preserves the en-passant target square. New
python-chess oracle comparisons cover stale castling rights with a missing rook,
a displaced king, an en-passant capture that would expose its own king to a rook,
and all four promotion choices. These are targeted special-move regressions;
they do not by themselves establish complete FIDE-rule coverage.


The promotion oracle exposed a genuine legal-move-generation defect: the engine
generated only queen promotions, while standard chess permits queen, rook,
bishop, and knight promotions. Pawn move generation now emits all four choices
for both quiet promotions and promotion captures. The failing oracle test remains
in the suite to prevent regression.


## Terminal-position and side-to-move validation update

Additional oracle-backed cases now cover a complex position with Black to move,
castling through an attacked transit square, and Black's four promotion choices.
Separate terminal fixtures assert that the engine distinguishes checkmate from
stalemate. These tests extend targeted coverage; they are not a substitute for
a complete standard perft suite or a full audit of all draw rules.


## Repetition identity and fifty-move counter update

Position identity now ignores an en-passant target unless the side to move has a legal en-passant capture, including king-safety constraints. The game state tracks the halfmove clock, resets it after pawn moves and captures, restores it on undo, and exposes the 100-halfmove draw threshold. Search scores that draw as zero. The 75-move automatic-draw rule and insufficient-material detection remain outside this batch.


## Automatic draw and insufficient-material update

The engine now tracks fivefold repetition and the 75-move automatic-draw threshold
(150 halfmoves), alongside its existing threefold and 50-move claim handling.
Search returns a terminal draw score for these states. The material detector is
intentionally conservative: it recognises king-versus-king, a lone bishop or
knight against a bare king, and bishop-only positions where all bishops occupy
the same square colour. It does not claim that all other minor-piece endings are
dead positions. Regression tests cover these recognised cases and a rook-positive
control. The halfmove clock and its history are now included in perft state
restoration snapshots.


## Draw-rule precedence and state-history validation update

Regression coverage now verifies that checkmate takes precedence over the 75-move
automatic-draw threshold when both conditions are represented in the terminal
position. Repetition-history undo is checked against an exact pre-move count
snapshot, and castling rights are confirmed to distinguish otherwise identical
board/side-to-move positions. Capture halfmove-clock reset and undo restoration
are also tested. A three-occurrence position is explicitly distinguished from
the five-occurrence automatic threshold.

The engine continues to simplify threefold repetition and the 50-move rule as
immediate search draws; tournament adjudication normally requires a claim for
those thresholds. The tests validate the engine's documented search policy, not
a complete FIDE arbiter implementation.


## Deterministic game-history oracle validation

A deterministic multi-game regression now plays legal moves selected from
python-chess and compares the engine's complete legal-move set at every ply.
After each move it also compares the halfmove clock, threefold-repetition
detection, and fivefold-repetition detection with python-chess. Four fixed random
seeds make failures reproducible while exercising varied pawn moves, captures,
and evolving castling/en-passant rights. Insufficient-material validation is
one-sided by design: the conservative engine detector may return false for a
dead position, but it must not return true when python-chess considers the
position live.

This is a bounded deterministic sample, not exhaustive proof over all legal
games or a full formal verification of repetition adjudication.


## Transposition-table draw-context validation

Transposition-table entries are now keyed by the ordinary position identity,
the exact halfmove clock, and a sorted snapshot of the complete repetition
position-count map. This prevents positions with identical boards but different
50/75-move counters or prior repetition histories from sharing cached scores.
The full count map is retained rather than only currently repeated positions:
a position seen once earlier in the game can become a repetition later in a
search line. The trade-off is reduced cache reuse across different game
histories and additional key memory/construction cost. This is a correctness-
first implementation; its performance impact remains to be benchmarked.

Regression tests assert that equal board identities with different halfmove
clocks or repetition histories receive distinct cache keys, and that make/undo
restores the original cache identity.
