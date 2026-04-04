<p align="center">

<img src="https://img.shields.io/badge/Project-Chess%20AI-blue?style=for-the-badge" />
<img src="https://img.shields.io/badge/AI-Minimax%20%2B%20Alpha--Beta-purple?style=for-the-badge" />
<img src="https://img.shields.io/badge/Search-Quiescence%20%2B%20PV-orange?style=for-the-badge" />
<img src="https://img.shields.io/badge/Explainable-AI-green?style=for-the-badge" />
<img src="https://img.shields.io/badge/Language-Python-yellow?style=for-the-badge" />

</p>

<p align="center">

<img src="https://img.shields.io/github/last-commit/Nomusa990822/Chess-AI?style=for-the-badge" />
<img src="https://img.shields.io/github/languages/top/Nomusa990822/Chess-AI?style=for-the-badge" />
<img src="https://img.shields.io/github/repo-size/Nomusa990822/Chess-AI?style=for-the-badge" />

</p>

---

<h1 align="center">♟️ Chess AI with Forced Advantage</h1>

<p align="center">
A deep, explainable chess engine built with adversarial search, advanced evaluation, and transparent AI reasoning.
</p>

<p align="center">
Built for <strong>CS50’s Introduction to AI with Python</strong>
</p>

---

## Overview

This project is a **terminal-based Chess AI engine** designed to demonstrate how classical AI techniques can produce strong, explainable decision-making.

Unlike basic chess implementations, this engine combines:

- Minimax + Alpha-Beta pruning  
- Quiescence search  
- Principal variation tracking  
- Advanced evaluation heuristics  
- Explainable AI output  
- Full test coverage  

It is not just a game — it is a **transparent decision-making system**.

---

## Key Features

### Chess Engine
- Legal move generation
- Check / checkmate / stalemate detection
- Castling, en passant, promotion
- Undo move functionality
- Draw by repetition

### AI Engine
- Minimax search
- Alpha-Beta pruning
- Iterative deepening
- Quiescence search
- Move ordering
- Principal variation tracking
- Search diagnostics (nodes, depth, pruning)

### Evaluation System
- Material balance
- Piece-square tables
- Center control
- Pawn structure (doubled, isolated, passed, chains)
- Bishop pair bonus
- Rook file + 7th rank bonuses
- Knight outposts
- King safety (pawn shield)
- Mobility
- Game phase awareness
- Endgame king activity
- Edge pressure

### Explainable AI
- Why the move was chosen
- Evaluation breakdown
- Before/after evaluation delta
- Top candidate moves
- Principal variation

---

## Game Modes

| Mode | Description |
|------|-------------|
| **Fair** | Balanced gameplay |
| **Hard** | Stronger positional AI |
| **Forced-Win** | AI starts with advantage and converts |

---

## System Architecture

```mermaid
flowchart TD
    A[User Input] --> B[main.py]

    B --> C[GameState Engine]
    B --> D[AI Engine]

    %% Engine Layer
    C --> C1[Move Generator]
    C --> C2[Game Rules]
    C --> C3[Board Update]

    C3 --> C4[Display Output]

    %% AI Layer
    D --> D1[Best Move Selection]
    D --> D2[Search Controller]

    D2 --> D3[Minimax Algorithm]
    D3 --> D4[Alpha-Beta Pruning]
    D4 --> D5[Transposition Table]
    D5 --> D6[Quiescence Search]
    D6 --> D7[Evaluation Function]

    %% Evaluation Layer
    D7 --> E1[Material Score]
    D7 --> E2[Positional Score]
    D7 --> E3[Mobility & King Safety]
    D7 --> E4[Pawn Structure]

    %% Feedback Loop
    D1 --> C
```

---

## AI Decision Process

```mermaid
flowchart TD
    A[Current Board State] --> B[Generate Legal Moves]
    B --> C[Order Moves]

    C --> D[Iterative Deepening]
    D --> E[Minimax Search]

    E --> F[Alpha-Beta Pruning]
    F --> G[Transposition Table Lookup]

    G --> H[Quiescence Search]
    H --> I[Evaluate Positions]

    I --> J[Track Principal Variation]
    J --> K[Select Best Move]
    K --> L[Return Move]
```

---

## Evaluation Breakdown

The engine evaluates positions using multiple components:
* **Material** → piece values
* **Piece-Square Tables** → positional placement
* **Center Control** → board dominance
* **Pawn Structure** → long-term stability
* **Mobility** → number of legal moves
* **King Safety** → pawn shield
* **Endgame Activity** → king positioning
* **Edge Pressure** → forcing king to edge

---

## Explainability Example


---

## Project Structure
```
Chess-AI/
│
├── main.py
├── engine.py
├── ai.py
├── evaluation.py
├── forced_positions.py
├── utils.py
│
├── tests/
│   ├── test_engine.py
│   ├── test_evaluation.py
│   └── test_forced_positions.py
│
├── assets/
│   └── game.jpg
│
├── requirements.txt
├── .gitignore
└── README.md
```

---
## How to Run
```
git clone https://github.com/Nomusa990822/Chess-AI.git
cd Chess-AI
pip install -r requirements.txt
python main.py
```
### Run Tests

```pytest```

---

## Preview 


---

## What This Project Demonstrates
* Adversarial search (Minimax)
* Search optimization (Alpha-Beta)
* Tactical extensions (Quiescence)
* Heuristic evaluation design
* Explainable AI systems
* Clean modular architecture
* Software testing practices

---

## Important Notes
* Scores are from White’s perspective
  - Positive → White advantage
  - Negative → Black advantage
* Search evaluation ≠ static evaluation
  - Search includes lookahead
  - Static evaluates current position only
---

## Future Improvements
* Opening book
* Killer move heuristic
* Zobrist hashing
* GUI version (Pygame/Web)
* AI vs AI mode
* PGN export

---
## Author
Nomusa Shongwe

---
## Final Note
> This project shows that powerful AI does not require machine learning — it can emerge from structured reasoning, search, and well-designed evaluation.
