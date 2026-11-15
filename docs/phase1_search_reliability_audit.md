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


## Search move-ordering and transposition replacement

The transposition table now uses a depth-preferred replacement policy: a
shallower result cannot overwrite a deeper result for the same history-aware
key, and an exact entry can replace a bound entry at equal depth.

Move ordering retains the existing hash-move and tactical priorities and adds
two standard quiet-move heuristics. Killer moves are remembered per search ply
when a quiet move causes an alpha-beta cutoff. A bounded history score is
updated for the same quiet move and side-to-move context, with larger search
depths receiving larger bonuses. These heuristics affect ordering only; they do
not change position evaluation or legal move generation.

Principal Variation Search (PVS) is deliberately deferred until these ordering
changes are measured and independently validated. PVS relies on strong move
ordering and null-window re-search correctness, so introducing it in the same
change would make performance and correctness regressions harder to isolate.

## Reproducible search benchmark baseline

A fixed-position benchmark has been added at `benchmarks/search_benchmark.py`.
It evaluates an opening, a complex middlegame, and a pawn endgame from fixed
FENs. Each repetition creates a fresh game state and calls the public
`choose_ai_move` entry point, so each run starts with a fresh transposition
table. The JSON output records the FEN, completed depth, selected move, score,
node and quiescence-node counts, alpha-beta prunes, transposition hits, elapsed
time, and nodes per second. Position summaries use medians across repetitions.

Elapsed time covers the complete `choose_ai_move` call, including its
post-search explanation generation; it is therefore an end-to-end engine-call
measurement, not isolated search-loop time. CI runs two repetitions at depth
two to keep routine verification bounded. The script defaults to depth three
and three repetitions for a more informative manual comparison.

This is the reference measurement point for the upcoming PVS experiment. It
must not be described as a pre-killer/history measurement: those heuristics
were already present when this benchmark was introduced. Compare PVS against
this same benchmark, on the same runner class and parameters, and report the
raw per-position results as well as aggregate medians. Runtime measurements
are environment-sensitive and do not establish playing strength or Elo.

### CI reference measurements (Python 3.12, GitHub-hosted Ubuntu)

The benchmark completed successfully in workflow run
[43775396834](https://github.com/Nomusa990822/Chess-AI/actions/runs/43775396834)
at depth two with two repetitions per position. The median measurements were:

| Position | Median elapsed (s) | Median nodes | Median q-nodes | Median NPS | Median prunes |
|---|---:|---:|---:|---:|---:|
| Opening | 0.2254 | 193 | 183 | 856.3 | 21 |
| Middlegame | 1.6838 | 174 | 987 | 103.3 | 237 |
| Endgame | 0.0409 | 58 | 69 | 1417.0 | 7 |

Both repetitions completed the requested depth and selected a legal move in
all three positions. The observed moves in the final repetition were b1c3,
e2a6, and f3e4 respectively. These are measurements from one CI run, not
universal performance guarantees. The middlegame's larger quiescence workload
is visible in its 987 median q-nodes and lower end-to-end NPS.

The complete test suite also passed in that workflow: 92 tests passed. The
benchmark's first CI attempt exposed a script import-path issue; the script was
corrected to add the repository root to `sys.path`, and the subsequent full
workflow passed, including all benchmark positions.

## Principal Variation Search experiment

PVS is implemented as an opt-in search mode in `ai.py`. At each non-root
alpha-beta node, the first ordered move receives the full window. Later moves
are searched with a narrow window of `1e-6` in the appropriate direction.
A move whose result improves the incumbent without already causing a cutoff
is re-searched with the full window. Search timeout exceptions continue to
propagate, and speculative board moves remain protected by `finally` undo
blocks. Search statistics expose null-window search and full-window re-search
counts. The `choose_ai_move` API accepts `use_pvs=True` to enable the
experiment; the default remains full-window alpha-beta until PVS demonstrates
a repeatable benefit.

Regression tests compare PVS and full-window minimax scores at depth three for
both White-to-move and Black-to-move positions, and verify board-state
restoration. The CI benchmark now runs both modes on the same fixed positions,
depth, repetition count, and runner.

### Paired CI comparison

Workflow
[43775677962](https://github.com/Nomusa990822/Chess-AI/actions/runs/43775677962)
passed the complete test suite and both benchmark modes (depth two, two
repetitions). Median end-to-end call times were:

| Position | Full-window (s) | PVS (s) | Full-window nodes | PVS nodes |
|---|---:|---:|---:|---:|
| Opening | 0.4132 | 0.4989 | 193 | 221 |
| Middlegame | 3.0133 | 3.0397 | 174 | 175 |
| Endgame | 0.0744 | 0.0795 | 58 | 62 |

Both modes selected the same move and returned the same score in each
benchmark position. At this shallow depth PVS was slower in all three
positions and visited slightly more nodes. The measurements do not justify
making PVS the default. It therefore remains available for controlled
experiments while the production/default path continues using the existing
full-window search. A deeper paired benchmark is needed before reconsidering
that decision; no strength or Elo claim is inferred from these timings.


### Expanded PVS correctness verification

The follow-up regression batch broadens the PVS/full-window equivalence check
beyond the initial position. Three fixed positions are now compared: the
complex middlegame with White to move, the same position with Black to move,
and the pawn ending. Each comparison requires scores to agree within
(10^{-9}), replays every move in the PVS principal variation against the
engine's legal-move generator, and verifies exact state restoration after
undoing the replay. Separate timeout tests confirm that both full-window and
PVS modes retain a legal fallback, report depth zero when the deadline is
already expired, and leave the supplied position unchanged.

Workflow
[43776068475](https://github.com/Nomusa990822/Chess-AI/actions/runs/43776068475)
passed on commit
[04f6e130c6603974eded9427fc1936545f314e0e](https://github.com/Nomusa990822/Chess-AI/commit/04f6e130c6603974eded9427fc1936545f314e0e):
99 tests passed in 19.27 seconds, application compilation passed, and both
fixed-position benchmark modes completed successfully.

The paired depth-two benchmark on this run reported these median end-to-end
times (seconds) and node counts:

| Position | Full-window time | PVS time | Full-window nodes | PVS nodes |
|---|---:|---:|---:|---:|
| Opening | 0.3034 | 0.3625 | 193 | 221 |
| Middlegame | 2.2568 | 2.2275 | 174 | 175 |
| Endgame | 0.0561 | 0.0588 | 58 | 62 |

The two modes selected the same final move in each position and their scores
matched in the benchmark. PVS was slower in the opening and endgame, marginally
faster in the middlegame, and searched more nodes in all three cases. This
single shallow run does not establish a repeatable speedup; PVS therefore
remains opt-in and full-window alpha-beta remains the default. The earlier
statement that PVS was deferred describes the stage before this later opt-in
experiment and is superseded by the implementation and verification sections
above.


### Deeper paired benchmark (depth three)

The CI workflow now adds a one-repetition depth-three comparison after the
two-repetition depth-two check. It also runs when documentation changes, so
recorded benchmark evidence and the verification workflow stay connected.
Workflow
[43776212761](https://github.com/Nomusa990822/Chess-AI/actions/runs/43776212761)
passed on commit
[262d36a6b810f8e26622fb52de3272814469d04e](https://github.com/Nomusa990822/Chess-AI/commit/262d36a6b810f8e26622fb52de3272814469d04e):
application compilation passed, all 99 tests passed in 13.86 seconds, and
both benchmark modes completed depth two (two repetitions) and depth three
(one repetition) on all three fixed positions.

Depth-three end-to-end measurements (one sample per position, seconds):

| Position | Full-window time | PVS time | Full-window nodes | PVS nodes | Full-window score | PVS score |
|---|---:|---:|---:|---:|---:|---:|
| Opening | 1.0190 | 1.0729 | 847 | 903 | 0.340 | 0.340 |
| Middlegame | 7.3595 | 7.0198 | 2034 | 2074 | -0.119 | -0.119 |
| Endgame | 0.1279 | 0.1532 | 249 | 303 | -0.900 | -0.900 |

The selected moves also matched between modes (b1c3, e2a6, and d4d5). PVS
was approximately 5.3% slower in the opening, 4.6% faster in the middlegame,
and 19.7% slower in the endgame in this single-sample run. It searched more
nodes in every position. This mixed result is insufficient to establish a
repeatable improvement, so PVS remains an experimental opt-in and the
full-window search remains the default. A single depth-three sample is
informative but not statistically robust; repeated measurements on multiple
runner instances would be needed before changing the default.


## Root-level Principal Variation Search

Root move selection now applies the same PVS principle as recursive nodes.
The first ordered root move is searched with the full current window. Later
moves are searched with a null window on the correct side of the incumbent
bound, and any result that improves the incumbent without proving a cutoff is
re-searched with the full window. Root null-window searches and root
re-searches have separate counters in the search statistics and benchmark
output.

The root-window direction is derived from the side to move after the candidate
root move has been made: after a White root move, Black is to move and the
child is searched with the narrow alpha window; after a Black root move, White
is to move and the child is searched with the narrow beta window. PVS now
avoids constructing a null window from an infinite bound. When the relevant
bound is still infinite, that node uses a full-window search instead. This
guard is important because an invalid `[-inf, -inf]` or `[inf, inf]` window
can otherwise propagate infinite scores into root selection.

Three fixed-position root tests compare the selected move and final score
against full-window search at depth two, including White-to-move opening and
endgame positions and a Black-to-move middlegame. The test suite also retains
recursive PVS score-equivalence, legal-PV replay, timeout, and state-restoration
coverage.

Workflow
[43776898988](https://github.com/Nomusa990822/Chess-AI/actions/runs/43776898988)
passed on commit
[22feab9a5daa982b5776a553515777ea79e5c351](https://github.com/Nomusa990822/Chess-AI/commit/22feab9a5daa982b5776a553515777ea79e5c351):
application compilation passed and all 102 tests passed in 39.24 seconds.
Both search modes completed the fixed-position benchmark at depths two and
three. The results remained mixed: PVS improved the middlegame timings at both
depths, while the opening was slower at both depths; the endgame was slower at
depth two but faster at depth three. PVS also searched more nodes in the
opening and endgame, while its middlegame node count was similar or slightly
lower. These results still do not establish a general speedup, so PVS remains
opt-in and full-window alpha-beta remains the default.

The benchmark now reports root PVS null-window and re-search counts separately
from recursive PVS counters, allowing future comparisons to distinguish root
search activity from recursive search activity. This section's final recorded
counts and measurements are refreshed by the CI run triggered by this
documentation update.
