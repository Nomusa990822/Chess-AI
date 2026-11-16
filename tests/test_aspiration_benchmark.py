"""Tests for the reproducible aspiration benchmark harness."""

import pytest

from benchmarks.aspiration_window_sweep import POSITIONS, select_positions


def test_aspiration_benchmark_position_selection_is_explicit_and_ordered():
    selected = select_positions("tactical_black,pawn_endgame")
    assert [name for name, _ in selected] == ["tactical_black", "pawn_endgame"]
    assert len(select_positions(None)) == len(POSITIONS)


@pytest.mark.parametrize("selection", ["", "unknown_position", "pawn_endgame,pawn_endgame"])
def test_aspiration_benchmark_rejects_invalid_position_selection(selection):
    with pytest.raises(ValueError):
        select_positions(selection)
