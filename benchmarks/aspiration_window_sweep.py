"""Sweep aspiration-window widths against full-window and plain PVS search."""
import argparse, json, statistics, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import chess
from ai import choose_ai_move
from tests.test_perft import load_fen_position, engine_move_uci

POSITIONS = (
    ("quiet_start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("quiet_open_game", "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
    ("tactical_white", "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1"),
    ("tactical_black", "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R b KQkq - 0 1"),
    ("pawn_endgame", "8/5pk1/6p1/8/3P4/5K2/8/8 w - - 0 1"),
)

def run_one(fen, depth, repeats, use_pvs, window, adaptive=False):
    samples, final_move, final_score = [], None, None
    for _ in range(repeats):
        state = load_fen_position(fen)
        legal = state.get_valid_moves()
        before = state.get_position_key()
        started = time.perf_counter()
        move, info = choose_ai_move(state, legal, mode="fair", max_depth=depth,
            time_budget=90.0, use_pvs=use_pvs, use_aspiration=window is not None,
            aspiration_window=window if window is not None else 0.5,
            use_adaptive_aspiration=adaptive)
        elapsed = time.perf_counter() - started
        if info["depth_reached"] != depth:
            raise RuntimeError(f"wanted depth {depth}, got {info['depth_reached']}")
        if move not in legal or state.get_position_key() != before:
            raise RuntimeError("illegal move or root state was not restored")
        sample_move, sample_score = engine_move_uci(move), info["score"]
        samples.append({"move": sample_move, "score": sample_score,
            "seconds": elapsed, "nodes": info["nodes"],
            "searches": info["aspiration_searches"], "retries": info["aspiration_retries"],
            "fail_low": info["aspiration_fail_low"], "fail_high": info["aspiration_fail_high"],
            "adaptive_windows": info.get("adaptive_aspiration_windows", []),
            "score_changes": info.get("adaptive_score_changes", [])})
        if final_move is not None and (
            sample_move != final_move or abs(sample_score - final_score) > 1e-9
        ):
            raise RuntimeError("repeated benchmark runs were not deterministic")
        final_move, final_score = sample_move, sample_score
    return {"move": final_move, "score": final_score,
        "median_seconds": statistics.median(x["seconds"] for x in samples),
        "median_nodes": statistics.median(x["nodes"] for x in samples),
        "median_searches": statistics.median(x["searches"] for x in samples),
        "median_retries": statistics.median(x["retries"] for x in samples),
        "median_fail_low": statistics.median(x["fail_low"] for x in samples),
        "median_fail_high": statistics.median(x["fail_high"] for x in samples), "samples": samples}

def select_positions(selection):
    """Return requested fixed positions in caller order; reject unknown names."""
    available = dict(POSITIONS)
    if selection is None:
        return list(POSITIONS)
    names = [name.strip() for name in selection.split(",") if name.strip()]
    if not names:
        raise ValueError("--positions must name at least one benchmark position")
    if len(names) != len(set(names)):
        raise ValueError("--positions must not contain duplicate names")
    unknown = [name for name in names if name not in available]
    if unknown:
        raise ValueError(f"unknown benchmark position(s): {', '.join(unknown)}")
    return [(name, available[name]) for name in names]


def assert_matches_reference(result, reference, label):
    """Check every repetition, not only the final sample, against the oracle."""
    if result["move"] != reference["move"] or abs(result["score"] - reference["score"]) > 1e-9:
        raise RuntimeError(f"{label}: result differs from full-window reference")
    if len(result["samples"]) != len(reference["samples"]):
        raise RuntimeError(f"{label}: repetition count differs from reference")
    for index, (sample, expected) in enumerate(zip(result["samples"], reference["samples"]), 1):
        if sample["move"] != expected["move"] or abs(sample["score"] - expected["score"]) > 1e-9:
            raise RuntimeError(f"{label}: repetition {index} differs from full-window reference")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--windows", default="0.05,0.1,0.25,0.5,1.0,2.0")
    parser.add_argument("--include-adaptive", action="store_true",
                        help="compare adaptive aspiration with full-window alpha-beta")
    parser.add_argument("--positions", default=None,
                        help="comma-separated position names; defaults to all fixed positions")
    args = parser.parse_args()
    if args.depth < 1 or args.repeats < 1: parser.error("--depth and --repeats must be positive")
    try: windows = [float(v) for v in args.windows.split(",")]
    except ValueError: parser.error("--windows must be comma-separated positive numbers")
    if not windows or any(not (v > 0 and v < float("inf")) for v in windows):
        parser.error("--windows must contain finite positive numbers")
    try:
        selected_positions = select_positions(args.positions)
    except ValueError as exc:
        parser.error(str(exc))
    output = []
    for name, fen in selected_positions:
        board = chess.Board(fen)
        if not board.is_valid(): raise RuntimeError(f"{name}: invalid benchmark FEN")
        state = load_fen_position(fen)
        if {engine_move_uci(m) for m in state.get_valid_moves()} != {m.uci() for m in board.legal_moves}:
            raise RuntimeError(f"{name}: engine legal moves differ from python-chess")
        full = run_one(fen, args.depth, args.repeats, False, None)
        pvs = run_one(fen, args.depth, args.repeats, True, None)
        assert_matches_reference(pvs, full, f"{name}: PVS")
        adaptive_result = None
        if args.include_adaptive:
            adaptive_result = run_one(fen, args.depth, args.repeats, True, 0.5, adaptive=True)
            assert_matches_reference(adaptive_result, full, f"{name}: adaptive aspiration")
        sweep = []
        for window in windows:
            result = run_one(fen, args.depth, args.repeats, True, window)
            assert_matches_reference(result, full, f"{name}, window={window}: aspiration")
            sweep.append({"window": window, **result})
        output.append({"position": name, "fen": fen, "full_window": full, "pvs": pvs, "aspiration_sweep": sweep, "adaptive_aspiration": adaptive_result})
    print(json.dumps({"benchmark": "aspiration-window-sensitivity", "depth": args.depth,
        "repeats": args.repeats, "windows": windows,
        "positions": [name for name, _ in selected_positions],
        "position_count": len(selected_positions), "adaptive_included": args.include_adaptive,
        "results": output}, indent=2))

if __name__ == "__main__": main()
