"""Reproducible fixed-position search benchmark for PVS comparisons.

The benchmark measures complete choose_ai_move calls, including the engine's
post-search explanation generation. Each repetition starts from a fresh state
and transposition table. It is a comparative microbenchmark, not an Elo test.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai import choose_ai_move
from tests.test_perft import load_fen_position, engine_move_uci


POSITIONS = (
    (
        "opening",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    ),
    (
        "middlegame",
        "r3k2r/p1ppqpb1/bn2pnp1/2pP4/1p2P3/2N2N2/PPQBBPPP/R3K2R w KQkq - 0 1",
    ),
    (
        "endgame",
        "8/5pk1/6p1/8/3P4/5K2/8/8 w - - 0 1",
    ),
)


def run_benchmark(depth, repeats, search_mode="pvs"):
    results = []
    for name, fen in POSITIONS:
        samples = []
        last_info = None
        last_move = None
        for repetition in range(repeats):
            state = load_fen_position(fen)
            legal_moves = state.get_valid_moves()
            started = time.perf_counter()
            move, info = choose_ai_move(
                state, legal_moves, mode="fair", max_depth=depth,
                time_budget=120.0, use_pvs=search_mode != "full-window",
                use_aspiration=search_mode == "pvs-aspiration",
            )
            elapsed = time.perf_counter() - started
            if info["depth_reached"] != depth:
                raise RuntimeError(
                    f"{name} repetition {repetition + 1}: requested depth "
                    f"{depth}, completed {info['depth_reached']} "
                    f"(timed_out={info['timed_out']})"
                )
            if move not in legal_moves:
                raise RuntimeError(f"{name}: engine returned an illegal move")
            samples.append({
                "elapsed_seconds": elapsed,
                "nodes": info["nodes"],
                "q_nodes": info["q_nodes"],
                "prunes": info["prunes"],
                "tt_hits": info["tt_hits"],
                "pvs_null_window_searches": info["pvs_null_window_searches"],
                "pvs_researches": info["pvs_researches"],
                "root_pvs_null_window_searches": info["root_pvs_null_window_searches"],
                "root_pvs_researches": info["root_pvs_researches"],
                "aspiration_searches": info["aspiration_searches"],
                "aspiration_retries": info["aspiration_retries"],
                "aspiration_fail_low": info["aspiration_fail_low"],
                "aspiration_fail_high": info["aspiration_fail_high"],
                "nodes_per_second": info["nodes"] / elapsed if elapsed else 0.0,
            })
            last_info = info
            last_move = engine_move_uci(move)

        elapsed_values = [sample["elapsed_seconds"] for sample in samples]
        nps_values = [sample["nodes_per_second"] for sample in samples]
        results.append({
            "position": name,
            "fen": fen,
            "depth": depth,
            "repeats": repeats,
            "best_move_last_repeat": last_move,
            "score_last_repeat": last_info["score"],
            "median_elapsed_seconds": statistics.median(elapsed_values),
            "median_nodes_per_second": statistics.median(nps_values),
            "median_nodes": statistics.median(s["nodes"] for s in samples),
            "median_q_nodes": statistics.median(s["q_nodes"] for s in samples),
            "median_prunes": statistics.median(s["prunes"] for s in samples),
            "median_tt_hits": statistics.median(s["tt_hits"] for s in samples),
            "median_pvs_null_window_searches": statistics.median(s["pvs_null_window_searches"] for s in samples),
            "median_pvs_researches": statistics.median(s["pvs_researches"] for s in samples),
            "median_root_pvs_null_window_searches": statistics.median(s["root_pvs_null_window_searches"] for s in samples),
            "median_root_pvs_researches": statistics.median(s["root_pvs_researches"] for s in samples),
            "median_aspiration_searches": statistics.median(s["aspiration_searches"] for s in samples),
            "median_aspiration_retries": statistics.median(s["aspiration_retries"] for s in samples),
            "median_aspiration_fail_low": statistics.median(s["aspiration_fail_low"] for s in samples),
            "median_aspiration_fail_high": statistics.median(s["aspiration_fail_high"] for s in samples),
            "samples": samples,
        })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--search-mode", choices=("pvs", "full-window", "pvs-aspiration"), default="pvs")
    args = parser.parse_args()
    if args.depth < 1 or args.repeats < 1:
        parser.error("--depth and --repeats must both be positive")
    print(json.dumps({
        "benchmark": "phase1-search-mode-comparison",
        "search_mode": args.search_mode,
        "measurement": "complete choose_ai_move call, including explanation",
        "depth": args.depth,
        "repeats": args.repeats,
        "results": run_benchmark(args.depth, args.repeats, search_mode=args.search_mode),
    }, indent=2))


if __name__ == "__main__":
    main()
