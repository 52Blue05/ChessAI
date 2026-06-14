"""
scripts/run_benchmark.py
Script chạy benchmark Round Robin tự động giữa 3 AI.

Mỗi cặp AI đấu với nhau (cả 2 bên trắng/đen), mỗi cặp đấu N ván.
Kết quả ghi vào benchmark_results.csv.

Chạy:
    python scripts/run_benchmark.py
    python scripts/run_benchmark.py --games 20 --max-moves 200

Output:
    - benchmark_results.csv (chi tiết từng nước đi)
    - In bảng tổng hợp ra console
"""

import argparse
import sys
import uuid
import time
from pathlib import Path
from itertools import combinations

# Thêm root vào path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.engine.board import Board
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkLogger, BenchmarkStats
from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent


def play_game(
    white_agent,
    black_agent,
    move_generator: MoveGenerator,
    logger: BenchmarkLogger,
    max_moves: int = 150,
) -> str:
    """
    Chơi 1 ván đấu giữa 2 AI.

    Returns:
        'white_win', 'black_win', 'draw'
    """
    game_id = str(uuid.uuid4())[:8]
    board = Board.from_fen()

    for move_num in range(1, max_moves + 1):
        # Xác định agent đang đi
        current_agent = white_agent if board.current_player == "white" else black_agent

        # AI suy nghĩ
        logger.start_timer()
        move = current_agent.get_move(board)
        thinking_time = logger.stop_timer()

        if move is None:
            # Không có nước đi → kiểm tra trạng thái
            status = move_generator.get_game_status(board)
            if status == "checkmate":
                result = "black_win" if board.current_player == "white" else "white_win"
            else:
                result = "draw"

            logger.log_game_result(game_id, result)
            return result

        # Lấy stats
        stats = current_agent.get_stats()
        stats.thinking_time_ms = thinking_time

        fen_before = board.to_fen()
        board = board.make_move(move)
        fen_after = board.to_fen()

        # Kiểm tra trạng thái
        status = move_generator.get_game_status(board)

        # Log
        game_result = "ongoing"
        if status == "checkmate":
            game_result = "black_win" if board.current_player == "white" else "white_win"
        elif status in ["stalemate", "draw"]:
            game_result = "draw"

        logger.log_move(
            game_id=game_id,
            move_number=move_num,
            stats=stats,
            move_uci=move.to_uci(),
            fen_before=fen_before,
            fen_after=fen_after,
            game_result=game_result,
        )

        if game_result != "ongoing":
            logger.log_game_result(game_id, game_result)
            return game_result

    # Hết max_moves → hòa
    logger.log_game_result(game_id, "draw")
    return "draw"


def run_round_robin(games_per_pair: int = 10, max_moves: int = 150):
    """
    Chạy Round Robin giữa 3 AI.
    Mỗi cặp đấu games_per_pair ván (đổi bên trắng/đen).
    """
    # Khởi tạo agents
    agents = {
        "greedy": GreedyAgent(),
        "minimax": MinimaxAgent(depth=3),
        "mcts": MCTSAgent(simulations=500),
    }

    move_generator = MoveGenerator()
    logger = BenchmarkLogger()

    # Kết quả
    results = {name: {"wins": 0, "losses": 0, "draws": 0} for name in agents}
    matchups = []

    pairs = list(combinations(agents.keys(), 2))

    print("=" * 60)
    print("♟  Chess AI Benchmark — Round Robin")
    print("=" * 60)
    print(f"Agents: {', '.join(agents.keys())}")
    print(f"Games per pair: {games_per_pair}")
    print(f"Max moves per game: {max_moves}")
    print("=" * 60)

    for name_a, name_b in pairs:
        matchup = {
            "pair": f"{name_a} vs {name_b}",
            "a_wins": 0, "b_wins": 0, "draws": 0,
        }

        for game_num in range(games_per_pair):
            # Đổi bên mỗi ván
            if game_num % 2 == 0:
                white_name, black_name = name_a, name_b
            else:
                white_name, black_name = name_b, name_a

            white_agent = agents[white_name]
            black_agent = agents[black_name]

            print(f"\n🎮 Game {game_num + 1}/{games_per_pair}: "
                  f"{white_name} (W) vs {black_name} (B) ... ", end="", flush=True)

            start = time.time()
            result = play_game(white_agent, black_agent, move_generator, logger, max_moves)
            elapsed = time.time() - start

            print(f"{result} ({elapsed:.1f}s)")

            # Cập nhật kết quả
            if result == "white_win":
                results[white_name]["wins"] += 1
                results[black_name]["losses"] += 1
                if white_name == name_a:
                    matchup["a_wins"] += 1
                else:
                    matchup["b_wins"] += 1
            elif result == "black_win":
                results[black_name]["wins"] += 1
                results[white_name]["losses"] += 1
                if black_name == name_a:
                    matchup["a_wins"] += 1
                else:
                    matchup["b_wins"] += 1
            else:
                results[name_a]["draws"] += 1
                results[name_b]["draws"] += 1
                matchup["draws"] += 1

        matchups.append(matchup)

    # In bảng tổng hợp
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG HỢP")
    print("=" * 60)

    print(f"\n{'Algorithm':<15} {'Wins':>6} {'Losses':>8} {'Draws':>7} {'Win Rate':>10}")
    print("-" * 50)
    for name, stats in results.items():
        total = stats["wins"] + stats["losses"] + stats["draws"]
        win_rate = stats["wins"] / total * 100 if total > 0 else 0
        print(f"{name:<15} {stats['wins']:>6} {stats['losses']:>8} {stats['draws']:>7} "
              f"{win_rate:>9.1f}%")

    print(f"\n{'Matchup':<25} {'A Wins':>8} {'B Wins':>8} {'Draws':>7}")
    print("-" * 50)
    for m in matchups:
        print(f"{m['pair']:<25} {m['a_wins']:>8} {m['b_wins']:>8} {m['draws']:>7}")

    print(f"\n✅ Chi tiết đã lưu vào: {logger.csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chess AI Benchmark — Round Robin")
    parser.add_argument("--games", type=int, default=10,
                        help="Số ván đấu mỗi cặp (mặc định: 10)")
    parser.add_argument("--max-moves", type=int, default=150,
                        help="Số nước đi tối đa mỗi ván (mặc định: 150)")

    args = parser.parse_args()
    run_round_robin(games_per_pair=args.games, max_moves=args.max_moves)
