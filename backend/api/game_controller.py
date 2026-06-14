"""
backend/api/game_controller.py
REST API endpoints cho Chess AI.

API Contract:
    POST /api/move        — Thực hiện nước đi của người chơi
    GET  /api/legal-moves  — Lấy danh sách nước đi hợp lệ
    POST /api/ai-move      — AI tính và trả về nước đi
    GET  /api/benchmark    — Lấy kết quả benchmark
"""

from flask import Blueprint, request, jsonify
from backend.engine.board import Board, Square, Move
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkLogger

# Import AI agents
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent

game_bp = Blueprint("game", __name__, url_prefix="/api")

# Khởi tạo các service
move_generator = MoveGenerator()
benchmark_logger = BenchmarkLogger()

# Registry các AI agent
AGENTS = {
    "greedy": GreedyAgent(),
    "minimax": MinimaxAgent(),
    "mcts": MCTSAgent(),
}


# ==============================================================
# POST /api/move — Người chơi thực hiện nước đi
# ==============================================================
@game_bp.route("/move", methods=["POST"])
def make_move():
    """
    Request body:
    {
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "move": {
            "from": {"row": 6, "col": 4},
            "to": {"row": 4, "col": 4},
            "promotion": null
        }
    }
    """
    data = request.get_json()
    try:
        board = Board.from_fen(data["fen"])
        move = Move(
            from_sq=Square(data["move"]["from"]["row"], data["move"]["from"]["col"]),
            to_sq=Square(data["move"]["to"]["row"], data["move"]["to"]["col"]),
            promotion=data["move"].get("promotion"),
        )

        # Kiểm tra nước đi hợp lệ
        legal_moves = move_generator.generate_legal_moves(board, move.from_sq)
        is_legal = any(
            m.from_sq.row == move.from_sq.row and m.from_sq.col == move.from_sq.col
            and m.to_sq.row == move.to_sq.row and m.to_sq.col == move.to_sq.col
            for m in legal_moves
        )

        if not is_legal:
            return jsonify({"error": "Nước đi không hợp lệ"}), 400

        # Thực hiện nước đi
        new_board = board.make_move(move)
        status = move_generator.get_game_status(new_board)

        return jsonify({
            "move": _serialize_move(move),
            "newFen": new_board.to_fen(),
            "gameState": {
                "fen": new_board.to_fen(),
                "currentPlayer": new_board.current_player,
                "status": status,
            },
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/legal-moves — Lấy nước đi hợp lệ
# ==============================================================
@game_bp.route("/legal-moves", methods=["GET"])
def get_legal_moves():
    """
    Query params:
        fen: FEN string (required)
        row: Row của ô cần lấy nước đi (optional)
        col: Col của ô cần lấy nước đi (optional)
    """
    fen = request.args.get("fen")
    if not fen:
        return jsonify({"error": "Missing 'fen' parameter"}), 400

    board = Board.from_fen(fen)

    square = None
    row = request.args.get("row", type=int)
    col = request.args.get("col", type=int)
    if row is not None and col is not None:
        square = Square(row, col)

    moves = move_generator.generate_legal_moves(board, square)

    return jsonify({
        "moves": [_serialize_move(m) for m in moves],
    })


# ==============================================================
# POST /api/ai-move — AI tính nước đi
# ==============================================================
@game_bp.route("/ai-move", methods=["POST"])
def get_ai_move():
    """
    Request body:
    {
        "fen": "...",
        "algorithm": "greedy" | "minimax" | "mcts",
        "depth": 3,           // optional, dùng cho minimax
        "simulations": 1000   // optional, dùng cho mcts
    }
    """
    data = request.get_json()
    try:
        fen = data["fen"]
        algorithm = data.get("algorithm", "greedy")
        board = Board.from_fen(fen)

        agent = AGENTS.get(algorithm)
        if agent is None:
            return jsonify({"error": f"Unknown algorithm: {algorithm}"}), 400

        # Cấu hình agent (nếu có)
        if hasattr(agent, "set_depth") and "depth" in data:
            agent.set_depth(data["depth"])
        if hasattr(agent, "set_simulations") and "simulations" in data:
            agent.set_simulations(data["simulations"])

        # AI suy nghĩ
        benchmark_logger.start_timer()
        move = agent.get_move(board)
        thinking_time = benchmark_logger.stop_timer()

        if move is None:
            return jsonify({"error": "AI không tìm được nước đi"}), 500

        # Lấy stats
        stats = agent.get_stats()
        stats.thinking_time_ms = thinking_time

        # Thực hiện nước đi
        new_board = board.make_move(move)
        status = move_generator.get_game_status(new_board)

        # Log benchmark
        benchmark_logger.log_move(
            game_id="interactive",
            move_number=board.full_move_number,
            stats=stats,
            move_uci=move.to_uci(),
            fen_before=fen,
            fen_after=new_board.to_fen(),
            game_result=status if status in ["checkmate", "stalemate", "draw"] else "ongoing",
        )

        return jsonify({
            "move": _serialize_move(move),
            "newFen": new_board.to_fen(),
            "gameState": {
                "fen": new_board.to_fen(),
                "currentPlayer": new_board.current_player,
                "status": status,
            },
            "stats": {
                "algorithm": stats.algorithm,
                "thinkingTimeMs": round(stats.thinking_time_ms, 2),
                "nodesEvaluated": stats.nodes_evaluated,
                "depthReached": stats.depth_reached,
                "evaluationScore": round(stats.evaluation_score, 4),
            },
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# GET /api/benchmark — Kết quả benchmark
# ==============================================================
@game_bp.route("/benchmark", methods=["GET"])
def get_benchmark():
    """Trả về kết quả benchmark tổng hợp."""
    try:
        summary = benchmark_logger.get_summary_by_algorithm()
        records = benchmark_logger.read_all_records()

        return jsonify({
            "summary": summary,
            "totalRecords": len(records),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================
# Helpers
# ==============================================================

def _serialize_move(move: Move) -> dict:
    """Chuyển đổi Move object sang JSON-serializable dict."""
    result = {
        "from": {"row": move.from_sq.row, "col": move.from_sq.col},
        "to": {"row": move.to_sq.row, "col": move.to_sq.col},
    }
    if move.promotion:
        result["promotion"] = move.promotion
    if move.captured:
        result["captured"] = {
            "type": move.captured.piece_type,
            "color": move.captured.color,
        }
    return result
