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


### Final paired measurements with root-PVS instrumentation

Workflow
[43777094177](https://github.com/Nomusa990822/Chess-AI/actions/runs/43777094177)
passed on the final root-PVS documentation commit
`fecedd776be8f97675c2c782658a6d9533a66d90`. Application compilation passed,
all 102 tests passed in 38.70 seconds, and the benchmark completed both
search modes at depth two (two repetitions) and depth three (one repetition)
for all three fixed positions.

Depth-two median end-to-end time and node counts:

| Position | Full-window time (s) | PVS time (s) | Full-window nodes | PVS nodes |
|---|---:|---:|---:|---:|
| Opening | 0.4136 | 0.5603 | 193 | 273 |
| Middlegame | 2.9940 | 2.6843 | 174 | 174 |
| Endgame | 0.0742 | 0.0835 | 58 | 72 |

Depth-three end-to-end time and node counts (one sample):

| Position | Full-window time (s) | PVS time (s) | Full-window nodes | PVS nodes |
|---|---:|---:|---:|---:|
| Opening | 1.9374 | 2.2454 | 847 | 1048 |
| Middlegame | 13.8824 | 12.8859 | 2034 | 1990 |
| Endgame | 0.2450 | 0.2199 | 249 | 231 |

Both modes selected the same moves and returned the same scores in every
paired position: b1c3, e2a6, f3e4 at depth two; b1c3, e2a6, d4d5 at depth
three. At depth two, PVS was slower in the opening and endgame but faster in
the middlegame. At depth three, PVS was slower in the opening and faster in
the middlegame and endgame. These small, environment-sensitive samples do not
justify changing the default search mode.

The instrumented PVS counts (null-window searches / full-window re-searches)
were:

| Position | Depth | Recursive PVS | Root PVS |
|---|---:|---:|---:|
| Opening | 2 | 190 / 13 | 38 / 7 |
| Middlegame | 2 | 39 / 0 | 88 / 0 |
| Endgame | 2 | 39 / 3 | 16 / 2 |
| Opening | 3 | 826 / 21 | 57 / 9 |
| Middlegame | 3 | 1683 / 0 | 132 / 0 |
| Endgame | 3 | 138 / 4 | 24 / 2 |

Root PVS is therefore implemented, tested, and measurable, but remains an
experimental opt-in. Full-window alpha-beta remains the default because
performance is position-dependent and no broad, repeatable advantage has
been demonstrated.



## Aspiration-window search experiment

An opt-in aspiration-window mode has been added to the root iterative-deepening
search. Starting at depth two, it centres a finite alpha-beta window on the
score from the last fully completed iteration. Depth one remains a full-window
search because no previous completed score exists. If the root result fails
low or high, the corresponding bound is widened exponentially and the whole
root iteration is searched again. After the configured retry limit, the engine
uses a full-window pass to obtain an exact root result.

The feature is exposed through
`choose_ai_move(..., use_aspiration=True)`; it is disabled by default. It can
be combined with the existing opt-in PVS mode. The default engine therefore
continues to use full-window alpha-beta. Search diagnostics separately count
aspiration-window iterations, retries, fail-low events and fail-high events.
Only a fully completed iteration is published. A timeout during a retry leaves
the previous completed depth and its move intact.

### Correctness and failure-path tests

The regression suite now includes:
- Synthetic fail-high and fail-low cases that force aspiration retries and
  exercise the bounded full-window fallback.
- Three fixed FEN positions (opening, Black-to-move complex middlegame and
  pawn endgame) comparing PVS with aspiration against full-window alpha-beta.
  The selected root move and score must match, the principal variation must be
  present, and the original board state must be restored.
- A timeout deliberately injected during an aspiration retry; the last
  completed depth-one result must remain published.
- Existing PVS, legal-PV replay, move-state restoration and timeout tests.

Four intermediate push-triggered runs (43777629542, 43777669929,
43777673934 and 43777718421) were automatically cancelled as subsequent
commits superseded their branch heads while this batch was being assembled.
They did not complete verification and are not counted as passes or failures.
The corrected, complete workflow succeeded as run
[43777722334](https://github.com/Nomusa990822/Chess-AI/actions/runs/43777722334)
on commit
[51454e38f39f5cea9e72ddada7d29d942b0e6bb4](https://github.com/Nomusa990822/Chess-AI/commit/51454e38f39f5cea9e72ddada7d29d942b0e6bb4).
Python 3.12 compilation passed and the complete suite passed: **108 tests**.
All six fixed-position benchmark invocations (three modes at depths two and
three) completed at the requested depth.

### Three-way benchmark methodology

The benchmark compares:
1. Full-window alpha-beta (`full-window`).
2. Principal Variation Search (`pvs`).
3. PVS with aspiration windows (`pvs-aspiration`).

All modes use the same three fixed FEN positions, move ordering, evaluation,
runner class and public `choose_ai_move` entry point. Depth two uses two
repetitions and reports medians; depth three uses one sample. Elapsed time
covers the complete engine call, including explanation generation. Timings are
environment-sensitive and are not playing-strength or Elo measurements.

### Depth-two paired CI results

Workflow 43777722334, Python 3.12 on GitHub-hosted Ubuntu, two repetitions.
Elapsed times are median seconds; node counts are medians.

| Position | Full-window s / nodes | PVS s / nodes | PVS + aspiration s / nodes |
|---|---:|---:|---:|
| Opening | 0.2501 / 193 | 0.3395 / 273 | 0.2671 / 214 |
| Middlegame | 1.8547 / 174 | 1.6635 / 174 | 1.6585 / 174 |
| Endgame | 0.0461 / 58 | 0.0513 / 72 | 0.0514 / 72 |

All three modes selected the same moves and scores:
- Opening: `b1c3`, score `6.661338147750939`.
- Middlegame: `e2a6`, score `-0.024000000000000042`.
- Endgame: `f3e4`, score `-0.9550000000000001`.

### Depth-three paired CI results

The following are one-sample elapsed times and node counts from the same
workflow run.

| Position | Full-window s / nodes | PVS s / nodes | PVS + aspiration s / nodes |
|---|---:|---:|---:|
| Opening | 1.1734 / 847 | 1.3700 / 1048 | 1.3010 / 993 |
| Middlegame | 8.5806 / 2034 | 7.9856 / 1990 | 7.9608 / 1990 |
| Endgame | 0.1508 / 249 | 0.1360 / 231 | 0.1397 / 231 |

All three modes again selected identical moves and scores:
- Opening: `b1c3`, score `0.33999999999999997`.
- Middlegame: `e2a6`, score `-0.11900000000000008`.
- Endgame: `d4d5`, score `-0.8999999999999999`.

The aspiration mode recorded one finite-window search per position at depth
two and two per position at depth three (one for each completed depth after
depth one). No aspiration re-search was needed in these six benchmark
position/depth combinations: fail-low, fail-high and retry counters were all
zero. The separate synthetic regression tests exercise both failure directions
and the full-window fallback.

### Interpretation and decision

Aspiration windows reduced the measured PVS time in the opening at both
benchmarked depths and slightly reduced the middlegame time. The endgame was
marginally slower than PVS at both depths. Against full-window alpha-beta,
PVS plus aspiration remained slower in the opening, faster in the middlegame,
and slightly slower at depth two but faster at depth three in the endgame.
Node counts were lower than PVS in the opening and unchanged in the other
positions. These are small samples, especially at depth three, and do not
establish a repeatable general speedup.

Aspiration windows therefore remain experimental and opt-in, just like PVS.
Full-window alpha-beta remains the default. The experiment is implemented,
regression-tested and benchmarked; no claim of stronger play or Elo gain is
made.



## Aspiration-window stress testing and width sensitivity

The next experiment expanded aspiration validation beyond the three initial
fixed positions. A dedicated benchmark,
`benchmarks/aspiration_window_sweep.py`, now checks five position types:

- Quiet initial position.
- Quiet open-game position after 1.e4 e5.
- Complex tactical middlegame with White to move.
- The same tactical middlegame with Black to move.
- Sparse pawn endgame.

Before searching, the benchmark validates each FEN with python-chess and
compares the engine's legal root move set with python-chess. It then runs
full-window alpha-beta, PVS without aspiration, and PVS with six initial
aspiration widths: 0.05, 0.1, 0.25, 0.5, 1.0 and 2.0 evaluation points.
Each configuration is repeated twice at depth two. The script fails if any
configuration does not reach the requested depth, changes the root position,
returns an illegal move, or differs from the full-window reference move or
score. Reported times cover the complete `choose_ai_move` call, including
explanation generation.

### Stress sweep CI results

Workflow
[43778822628](https://github.com/Nomusa990822/Chess-AI/actions/runs/43778822628)
passed on commit
[32f290d8c2c3c9de6ea7ea169dfb846b6a2ef288](https://github.com/Nomusa990822/Chess-AI/commit/32f290d8c2c3c9de6ea7ea169dfb846b6a2ef288).
Application compilation passed and the expanded complete suite passed:
**120 tests in 110.31 seconds**. The original six fixed-position comparison
runs and the five-position/six-width sensitivity sweep all completed.

All five positions produced the same selected move and score in full-window,
plain PVS, and every aspiration width:

| Position | Selected move | Score (White perspective) |
|---|---:|---:|
| Quiet start | `b1c3` | 0.000 |
| Quiet open game | `b1c3` | 0.000 |
| Tactical, White to move | `e2a6` | -0.024 |
| Tactical, Black to move | `b4c3` | -2.458 |
| Pawn endgame | `f3e4` | -0.955 |

Median elapsed seconds / nodes are shown below. Each aspiration cell also
includes the median number of retries.

| Position | Full-window | PVS | 0.05 | 0.1 | 0.25 | 0.5 | 1.0 | 2.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Quiet start | 0.414 / 193 | 0.557 / 273 | 0.428 / 236 / 2 | 0.610 / 325 / 2 | 0.626 / 319 / 1 | 0.436 / 214 / 0 | 0.555 / 273 / 0 | 0.557 / 273 / 0 |
| Quiet open game | 1.561 / 286 | 1.541 / 395 | 1.522 / 378 / 2 | 2.266 / 519 / 2 | 1.787 / 469 / 1 | 1.345 / 315 / 0 | 1.541 / 395 / 0 | 1.541 / 395 / 0 |
| Tactical, White | 3.021 / 174 | 2.726 / 174 | 2.573 / 174 / 0 | 2.624 / 174 / 0 | 2.682 / 174 / 0 | 2.686 / 174 / 0 | 2.701 / 174 / 0 | 2.710 / 174 / 0 |
| Tactical, Black | 5.852 / 215 | 5.802 / 264 | 12.261 / 618 / 4 | 10.396 / 494 / 3 | 9.020 / 442 / 2 | 6.438 / 317 / 1 | 5.684 / 229 / 0 | 5.837 / 264 / 0 |
| Pawn endgame | 0.076 / 58 | 0.085 / 72 | 0.102 / 101 / 2 | 0.091 / 88 / 1 | 0.082 / 69 / 0 | 0.083 / 72 / 0 | 0.084 / 72 / 0 | 0.084 / 72 / 0 |

For aspiration columns, each cell is **seconds / nodes / retries**. Full-window
and PVS columns are **seconds / nodes**. Values are medians of two repetitions
on the same GitHub-hosted runner.

### Findings and tuning decision

The narrowest windows were not consistently efficient. The Black-to-move
tactical position exposed the clearest failure case: width 0.05 caused four
fail-high retries, width 0.1 caused three, width 0.25 caused two, and width
0.5 caused one. Widths 1.0 and 2.0 avoided retries; 1.0 was the fastest
measured configuration for that position. In the pawn ending, narrow widths
caused fail-low retries, while 0.25 and wider avoided them. Quiet positions
also showed that very narrow windows can trigger unnecessary retries.

No single width was fastest across all five positions. Width 0.5 gave the
best measured result for the quiet opening and quiet open game; 0.05 was
fastest in the tactical White-to-move position, although all widths searched
the same node count there; width 1.0 was fastest in the tactical Black-to-move
position; and 0.25 was fastest in the pawn ending. These are two-repetition,
depth-two microbenchmarks and should not be interpreted as broad performance
guarantees.

The current 0.5 default is retained as a balanced experimental starting
point, not as a proven global optimum. Aspiration windows and PVS remain
opt-in; full-window alpha-beta remains the production default. The new sweep
is part of the Phase 1 CI workflow so future changes can be compared against
the same position and width matrix. No playing-strength or Elo claim is made.


## Adaptive aspiration-window experiment

An additional opt-in mode, `use_adaptive_aspiration=True`, now adjusts the
initial aspiration window from the absolute score change between the two most
recently completed iterative-deepening iterations. The first aspiration
iteration has no pair of completed search scores to compare, so it uses the
configured base width (0.5 by default). Subsequent windows use a bounded,
deterministic scaling rule: stable scores narrow the window, while larger
score swings widen it. The current bounds are 0.1 to 4.0 evaluation points. The raw scaling is
`base_window * (0.5 + 0.5 * min(score_change, 4.0))`, clamped to those bounds.
Fail-low/fail-high widening and the full-window fallback remain unchanged.
Adaptive mode implicitly enables aspiration search but does not enable PVS;
PVS remains a separate opt-in flag.

The adaptive window is based only on completed search results. A timeout does
not publish a partial iteration or update the score-change history. The
feature remains disabled by default; the production search path is unchanged.

### Regression coverage

New tests cover:
- The deterministic window-scaling formula, including lower and upper bounds.
- Stable and large score changes across completed iterative-deepening depths.
- Timeout during a later adaptive iteration while preserving the last
  completed result and the root board state.
- Move/score parity with full-window alpha-beta while combining adaptive
  aspiration and PVS.
- Existing synthetic fail-low/fail-high retries and aspiration timeout tests,
  which continue to exercise the retry/fallback machinery.

### Adaptive benchmark methodology

The aspiration sweep can restrict its fixed position set with `--positions`
and now checks determinism and full-window parity for every repetition, not
just the final sample. With `--include-adaptive`, it compares full-window
alpha-beta, plain PVS, adaptive PVS/aspiration, and the requested fixed-width
sweep. Every mode must reach the requested depth, return a legal move, restore
the root position and match the full-window selected move and score on every
repetition. CI retains the depth-two six-width sweep and adds depth-three
comparisons (three repetitions) and depth-four comparisons (two repetitions)
for tactical White-to-move, tactical Black-to-move, and pawn-endgame positions.
Timings remain environment-sensitive and are not Elo or playing-strength
evidence.

### Depth-three adaptive comparison results

The final implementation workflow,
[run 43781393412](https://github.com/Nomusa990822/Chess-AI/actions/runs/43781393412),
passed on commit
[d43398636f8be86d33654f533003f36457bf8882](https://github.com/Nomusa990822/Chess-AI/commit/d43398636f8be86d33654f533003f36457bf8882).
Compilation passed and the complete suite passed: **129 tests in 61.65
seconds**. The existing fixed-position benchmarks, depth-two six-width
aspiration sweep, and depth-three adaptive comparison all completed.

All adaptive depth-three runs selected the same move and returned the same
score as full-window alpha-beta:

| Position | Move | Score (White perspective) |
|---|---|---:|
| Quiet start | `b1c3` | 0.340 |
| Quiet open game | `b1c3` | 0.340 |
| Tactical, White to move | `e2a6` | -0.119 |
| Tactical, Black to move | `b4c3` | -3.403 |
| Pawn endgame | `d4d5` | -0.900 |

One-repetition elapsed seconds / nodes are shown below. Fixed and adaptive
aspiration columns also include retry counts. The adaptive-window column is
the window selected for the third search depth (the first adaptive aspiration
iteration uses the configured base width of 0.5).

| Position | Full-window s / nodes | Fixed 0.5 s / nodes / retries | Adaptive s / nodes / retries | Adaptive depth-three window |
|---|---:|---:|---:|---:|
| Quiet start | 1.059 / 847 | 1.180 / 993 / 0 | 0.887 / 792 / 2 | 0.335 |
| Quiet open game | 4.019 / 1514 | 4.456 / 1845 / 0 | 2.646 / 1196 / 2 | 0.335 |
| Tactical, White | 7.764 / 2034 | 7.232 / 1990 / 0 | 7.342 / 1990 / 0 | 0.250 |
| Tactical, Black | 9.113 / 2088 | 11.102 / 2515 / 2 | 11.214 / 2515 / 2 | 0.442 |
| Pawn endgame | 0.138 / 249 | 0.125 / 231 / 0 | 0.129 / 231 / 0 | 0.305 |

The adaptive mode reduced measured nodes and elapsed time in both quiet
positions, but required two retries in each. It was essentially neutral or
slightly slower than fixed 0.5 in the tactical and endgame positions. This
small, single-repetition depth-three sample does not establish a general
performance advantage. It does show that adaptive sizing preserves the
reference move and score across all five tested positions while changing its
window in response to observed score stability.

### Decision

Adaptive aspiration is implemented, regression-tested and benchmarked, but
remains opt-in. It is not promoted to the default and no speedup, playing
strength or Elo claim is made. Full-window alpha-beta remains the production
default; PVS and both fixed/adaptive aspiration modes remain experimental.


## Repeated depth-three and depth-four adaptive comparison

The expanded benchmark was run by
[GitHub Actions run 43783254870](https://github.com/Nomusa990822/Chess-AI/actions/runs/43783254870)
on commit
[3b11e4b8aa60d02e2817c3d87b6f01aac12821ef](https://github.com/Nomusa990822/Chess-AI/commit/3b11e4b8aa60d02e2817c3d87b6f01aac12821ef).
The final branch-head workflow passed compilation, the complete test suite
(**133 passed in 81.78 seconds**), all existing fixed-position benchmarks,
the depth-two width sweep, and both new repeated comparisons.

The repeated comparisons used three positions: the tactical middlegame with
White to move, the same position with Black to move, and the pawn endgame.
Depth three used three repetitions per configuration; depth four used two.
Each run compared full-window alpha-beta, plain PVS, fixed 0.5 aspiration,
and adaptive aspiration with PVS. All configurations reached the requested
depth. Every repetition returned the same selected move and score as its
full-window reference, and restored the root position.

### Depth three

Values are median elapsed seconds / median nodes. Aspiration columns include
median retries.

| Position | Move | Score | Full-window | PVS | Fixed 0.5 | Adaptive |
|---|---|---:|---:|---:|---:|---:|
| Tactical, White | `e2a6` | -0.119 | 10.342 / 2034 | 9.581 / 1990 | 9.570 / 1990 / 0 | 9.546 / 1990 / 0 |
| Tactical, Black | `b4c3` | -3.403 | 12.074 / 2088 | 12.139 / 2229 | 14.892 / 2515 / 2 | 14.884 / 2515 / 2 |
| Pawn endgame | `d4d5` | -0.900 | 0.180 / 249 | 0.161 / 231 | 0.162 / 231 / 0 | 0.161 / 231 / 0 |

### Depth four

| Position | Move | Score | Full-window | PVS | Fixed 0.5 | Adaptive |
|---|---|---:|---:|---:|---:|---:|
| Tactical, White | `e2a6` | -0.119 | 51.277 / 6880 | 41.870 / 6837 | 41.739 / 6837 / 0 | 41.834 / 6837 / 0 |
| Tactical, Black | `b4c3` | -3.403 | 59.710 / 7513 | 51.702 / 8325 | 50.945 / 7216 / 2 | 50.724 / 7215 / 2 |
| Pawn endgame | `f3e4` | -0.880 | 0.473 / 641 | 0.519 / 736 | 0.525 / 736 / 0 | 0.522 / 736 / 0 |

Across these repeated runs, adaptive aspiration did not show a material
advantage over fixed 0.5. At depth three, the adaptive and fixed modes had
identical node counts in all three positions. At depth four, node counts were
identical in two positions and differed by one node in the tactical
Black-to-move position. Their elapsed-time differences were small and should
not be treated as a robust speedup. In the tactical Black-to-move position,
both aspiration modes needed two retries; in the other tested cases they
needed none.

The deeper results strengthen the conclusion that adaptive sizing preserves
search correctness, but do not justify replacing fixed aspiration or changing
the production default. Adaptive aspiration remains an opt-in experiment.
Full-window alpha-beta remains the production default, and no general speed,
playing-strength or Elo claim is made.
