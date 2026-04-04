# Chess AI Project Architecture

## Overview

This project follows a modular architecture that separates:

- user interaction
- game control
- chess rules
- AI search
- evaluation logic
- forced scenario loading

The goal of this structure is to improve:

- readability
- maintainability
- testing
- extensibility

Rather than placing all logic in one file, the project is divided into specialized components.

---

## Architectural Layers

### 1. Presentation Layer

This layer is responsible for all user-facing interaction.

It handles:
- the menu
- the board display
- user input
- help messages
- AI search reports

**Files involved**
- `main.py`
- `utils.py`

This layer should not contain chess rules or search logic.

---

### 2. Game Control Layer

This layer coordinates the overall flow of the game.

It decides:
- when to ask for input
- when to call the AI
- when the game is over
- what should be displayed after each move

**File involved**
- `main.py`

This acts as the orchestrator of the full system.

---

### 3. Chess Engine Layer

This is the legal source of truth for the game.

It handles:
- board state
- move generation
- move validation
- applying moves
- undoing moves
- check and mate detection
- stalemate and repetition
- castling
- en passant
- promotion

**File involved**
- `engine.py`

This is the foundation of the project.

---

### 4. Search Layer

This layer is the AI decision engine.

It handles:
- iterative deepening
- minimax
- alpha-beta pruning
- transposition table lookup
- move ordering
- quiescence search
- principal variation tracking
- search statistics

**File involved**
- `ai.py`

This layer determines the best move to play from a given position.

---

### 5. Evaluation Layer

This layer scores chess positions when the search cannot reach a terminal state.

It considers:
- material balance
- piece activity
- piece-square tables
- center control
- mobility
- pawn structure
- game phase
- endgame conversion pressure

**File involved**
- `evaluation.py`

This provides strategic guidance to the search layer.

---

### 6. Scenario Layer

This layer provides pre-configured positions for Forced-Win mode.

It is responsible for:
- loading winning endgames
- resetting rights correctly
- preparing custom board states

**File involved**
- `forced_positions.py`

---

### 7. Configuration Layer

This layer stores project-wide settings and mode-specific tuning values.

It includes:
- Fair / Hard / Forced mode parameters
- search settings
- feature toggles
- display preferences

**Files involved**
- `config.py`
- `constants.py`

---

## Architecture Flow

```text
User Input / Terminal
        ↓
     main.py
        ↓
 ┌───────────────┬────────────────┬──────────────────┐
 │               │                │                  │
engine.py      ai.py        forced_positions.py    utils.py
 │               │
 │         evaluation.py
 │
Board State + Legal Moves
```

---

## Search Flow

```
Current Position
      ↓
Generate Legal Moves
      ↓
Order Moves
      ↓
Iterative Deepening
      ↓
Minimax Search
      ↓
Alpha-Beta Pruning
      ↓
Transposition Table Lookup
      ↓
Quiescence Search at leaf nodes
      ↓
Evaluation Function
      ↓
Best Move + Principal Variation
```

---

## Design Principles

### 1. Separation of Concerns

Each file has one primary responsibility.
**Examples:**
- ```engine.py``` handles rules
- ```ai.py``` handles search
- ```evaluation.py``` handles scoring
- ```utils.py``` handles helpers

This makes the project easier to debug and improve.

### 2. Modularity

The system is designed so that one module can be improved without rewriting the others.
**For example:**
- evaluation can be improved without changing move generation
- search can be upgraded without changing the terminal UI
- more forced scenarios can be added without changing the engine

### 3. Explainability

The AI does not simply output a move.
**It also exposes:**
- evaluation score
- search depth
- nodes explored
- top candidate moves
- principal variation
- textual explanation

_This improves both transparency and presentation quality._

---

## Conclusion
The architecture is intentionally layered and modular so that the chess engine, search system, and evaluation logic remain independent but cooperative.

