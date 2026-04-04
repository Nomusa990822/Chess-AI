"""
Central configuration for the Chess AI project.

This file stores:
- mode settings
- search settings
- feature toggles
- UI/reporting preferences

Keeping configuration separate makes the project easier to tune
without editing the core engine or search logic.
"""

MODE_CONFIG = {
    "fair": {
        "label": "Fair Mode",
        "description": "Balanced AI with shallow search and simpler evaluation.",
        "max_depth": 2,
        "time_budget": 1.0,
        "use_quiescence": True,
        "show_top_moves": True,
        "show_principal_variation": True,
        "explanation_level": "basic"
    },
    "hard": {
        "label": "Hard Mode",
        "description": "Stronger AI with deeper search and better positional understanding.",
        "max_depth": 4,
        "time_budget": 2.0,
        "use_quiescence": True,
        "show_top_moves": True,
        "show_principal_variation": True,
        "explanation_level": "detailed"
    },
    "forced": {
        "label": "Forced-Win Mode",
        "description": "AI starts from a winning position and focuses on conversion.",
        "max_depth": 5,
        "time_budget": 2.5,
        "use_quiescence": True,
        "show_top_moves": True,
        "show_principal_variation": True,
        "explanation_level": "detailed"
    }
}

SEARCH_CONFIG = {
    "iterative_deepening": True,
    "use_alpha_beta": True,
    "use_transposition_table": True,
    "use_move_ordering": True,
    "use_quiescence_search": True,
    "max_quiescence_depth": 8,
    "track_principal_variation": True,
    "store_top_candidate_moves": 3
}

UI_CONFIG = {
    "use_colors": True,
    "show_search_report": True,
    "show_move_history": True,
    "show_board_coordinates": True,
    "show_game_phase": True
}

FORCED_MODE_DEFAULT_POSITION = "kqk_black_to_move"
