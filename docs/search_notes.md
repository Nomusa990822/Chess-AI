# Search Notes

## Overview

The AI in this project is based on classical adversarial search.

Its main goal is to answer the question:

> Given the current board state, what move leads to the best achievable outcome under optimal play?

To answer that, the search system combines several techniques.

---

## 1. Minimax

Minimax is the core decision-making algorithm.

It assumes:
- the AI chooses moves that maximize its outcome
- the opponent chooses moves that minimize that outcome

This makes it suitable for two-player zero-sum games like chess.

At each level of the search tree:
- one side tries to maximize the score
- the other side tries to minimize it

---

## 2. Alpha-Beta Pruning

Minimax alone is expensive because the number of possible positions grows very quickly.

Alpha-Beta pruning improves efficiency by skipping branches that cannot affect the final result.

Two bounds are used:
- **alpha** = best score the maximizing player can guarantee so far
- **beta** = best score the minimizing player can guarantee so far

If a branch cannot improve the outcome, it is pruned.

This reduces the number of nodes explored while keeping the same final decision.

---

## 3. Iterative Deepening

Instead of searching directly to one fixed depth, the engine searches progressively:

- depth 1
- depth 2
- depth 3
- and so on

This provides:
- better move ordering
- a usable best move even if time runs out
- more stable search behavior

It also mirrors how stronger engines often manage time.

---

## 4. Move Ordering

The order of moves matters a lot for Alpha-Beta pruning.

Good move ordering leads to earlier cutoffs and faster search.

This project prioritizes moves such as:
- captures
- promotions
- castling
- forcing tactical moves
- transposition-table best moves

Better move ordering improves efficiency without changing the underlying logic.

---

## 5. Transposition Table

The same position can often be reached through different move orders.

A transposition table stores previously evaluated positions so they do not need to be searched again.

Each stored entry may include:
- depth searched
- score
- bound type
- best move

This improves performance and helps move ordering.

---

## 6. Quiescence Search

A normal depth-limited search can stop in unstable tactical positions.

For example, it may evaluate a position:
- right before a capture
- right before a recapture
- right before a tactical exchange

This leads to the **horizon effect**.

Quiescence search extends the search beyond the normal depth limit, but only through tactical continuations such as:
- captures
- promotions
- optionally checks

The goal is to evaluate quieter, more stable positions.

---

## 7. Principal Variation

The principal variation is the best line of play currently predicted by the AI.

Instead of returning only one move, the AI can also display a line such as:

- `Qg2+`
- `Kxg2`
- `Kf2`

This shows the sequence of moves the engine currently believes to be optimal.

Principal variation output makes the AI feel much more transparent and professional.

---

## 8. Evaluation Function

When the search does not reach checkmate or another terminal result, the position must be estimated heuristically.

This project evaluates positions using:
- material balance
- piece-square tables
- center control
- pawn structure
- mobility
- game phase awareness
- king activity in the endgame
- edge pressure in forced-win conversions

This allows the AI to choose strong moves even when the full outcome is not yet known.

---

## 9. Game Phase Awareness

The evaluation does not treat all positions the same.

The engine distinguishes between:
- opening
- middlegame
- endgame

This matters because the importance of features changes across phases.

For example:
- king safety matters more in the opening and middlegame
- king activity matters more in the endgame

This makes evaluation more context-sensitive.

---

## 10. Forced-Win Mode Search Behavior

In Forced-Win mode, the engine starts from a winning position.

The evaluation is adjusted to encourage:
- restricting the defending king
- pushing the king toward the edge
- improving king coordination
- converting material advantage into mate

This makes the AI behave more like an endgame conversion engine.

---

## Why this search design is strong

This project does not attempt to solve chess.

Instead, it demonstrates a serious classical AI pipeline that includes:
- adversarial search
- pruning
- caching
- tactical extension
- strategic evaluation
- search transparency

Together, these components make the system much deeper than a basic minimax implementation.
