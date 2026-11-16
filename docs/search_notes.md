# Search & Decision-Making Notes

This note summarises the implemented search pipeline. The complete mathematical
derivations and feature equations are in
[Mathematical Foundations](mathematical_foundations.md).

## Search model

The engine treats chess as a deterministic, two-player, zero-sum,
perfect-information game. Evaluation scores are always from White's
perspective. White maximises the score and Black minimises it.

For state \(s\), legal actions \(A(s)\), transition \(T(s,a)\), static
evaluation \(E(s)\), and remaining depth \(d\):

\[
V(s,d)=
\begin{cases}
E(s), & d=0,\\
\max_{a\in A(s)}V(T(s,a),d-1), & \text{White to move},\\
\min_{a\in A(s)}V(T(s,a),d-1), & \text{Black to move}.
\end{cases}
\]

## Alpha-Beta pruning

Alpha-Beta maintains a lower bound \(\alpha\) for the maximizing player and
an upper bound \(\beta\) for the minimizing player. A branch is cut off when
\(\alpha\geq\beta\). Pruning preserves the minimax result while reducing
the number of nodes that need to be visited. Its effectiveness depends strongly
on move ordering.

## Iterative deepening and deadlines

The search completes depth 1, then 2, then 3, up to the configured limit or
deadline. Only a fully completed iteration replaces the current best move,
score and principal variation. A timeout never publishes a partial iteration.

## Move ordering

The ordering pipeline prioritises a transposition-table move, tactical moves,
killer moves and history-scored quiet moves. A quiet beta/alpha cutoff updates
the history score by \(d^2\), capped at 1,000,000; up to two killer moves are
kept per ply. These heuristics influence search order, not move legality or
the evaluation function.

## Transposition table

Entries contain search depth, score, bound type, best move and principal
variation. Exact entries can be returned directly; lower/upper bounds tighten
the active alpha/beta window. The key includes position identity, halfmove
clock and a sorted repetition-history snapshot to avoid reusing a score across
different draw contexts. Replacement favours deeper entries and exact entries
at equal depth.

## Quiescence search

At a quiet leaf, stand-pat evaluation is considered alongside captures and
promotions. If the side to move is in check, stand-pat is invalid and all legal
evasions are searched, including quiet evasions. A hard quiescence-depth cap of
8 bounds the extension.

## Experimental search modes

- **PVS:** first ordered move uses the full window; later moves use a
  null-window probe of width \(10^{-6}\), with full-window re-search when the
  result may improve the incumbent.
- **Aspiration windows:** centre the search window around the previous
  completed iteration's score; widen and retry on fail-low/fail-high, then
  fall back to a full window after the retry limit.
- **Adaptive aspiration:** adjusts the next window using the absolute change
  between completed iteration scores. Benchmarks show no consistent advantage
  over fixed width 0.5.

Full-window Alpha-Beta remains the production default. PVS and aspiration
variants are opt-in experiments; the benchmark evidence does not justify
claiming a general speedup or playing-strength/Elo gain.

## Complexity and limitations

With branching factor \(b\) and depth \(d\), minimax has a worst-case
tree-size order of \(O(b^d)\). Ideal move ordering can bring Alpha-Beta's
effective leaf count towards \(O(b^{d/2})\); poor ordering retains the
\(O(b^d)\) worst case. Quiescence reduces some horizon effects but cannot
guarantee that all long tactical sequences are resolved.

The search is depth- and time-bounded, and the leaf evaluator is handcrafted.
Consequently, a minimax result is optimal only relative to the searched tree
and its evaluation model, not a proof of the globally optimal chess move.
