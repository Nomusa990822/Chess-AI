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
