"""
backend/api/game_controller.py
REST API endpoints cho Chess AI.

API Contract:
    POST /api/move        — Thực hiện nước đi của người chơi
    GET  /api/legal-moves  — Lấy danh sách nước đi hợp lệ
    POST /api/ai-move      — AI tính và trả về nước đi
    GET  /api/benchmark    — Lấy kết quả benchmark
"""

import math

from flask import Blueprint, request, jsonify
from backend.engine.board import Board, Square, Move
from backend.engine.move_generator import MoveGenerator
from backend.engine.benchmark_logger import BenchmarkLogger

from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent

game_bp = Blueprint("game", __name__, url_prefix="/api")

# Khởi tạo các service
move_generator = MoveGenerator()
benchmark_logger = BenchmarkLogger()

# Registry các AI agent
AGENTS = {
    "greedy": GreedyAgent(),
    "minimax": MinimaxAgent(depth=2),
    "mcts": MCTSAgent(simulations=100),
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
    data = request.get_json(silent=True) or {}
    try:
        board = Board.from_fen(data["fen"])
        requested_move = Move(
            from_sq=Square(data["move"]["from"]["row"], data["move"]["from"]["col"]),
            to_sq=Square(data["move"]["to"]["row"], data["move"]["to"]["col"]),
            promotion=data["move"].get("promotion"),
        )

        # Kiểm tra nước đi hợp lệ
        legal_moves = move_generator.generate_legal_moves(board, requested_move.from_sq)
        move = next(
            (
                candidate
                for candidate in legal_moves
                if candidate.from_sq == requested_move.from_sq
                and candidate.to_sq == requested_move.to_sq
                and candidate.promotion == requested_move.promotion
            ),
            None,
        )

        if move is None:
            return _json_response({"error": "Nước đi không hợp lệ"}, 400)

        # Thực hiện nước đi
        new_board = board.make_move(move)
        game_state = _serialize_game_state(new_board)

        return _json_response({
            "move": _serialize_move(move),
            "newFen": game_state["fen"],
            "gameState": game_state,
        })

    except (KeyError, TypeError, ValueError, IndexError) as e:
        return _json_response({"error": str(e)}, 400)
    except Exception as e:
        return _json_response({"error": str(e)}, 500)


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
        return _json_response({"error": "Missing 'fen' parameter"}, 400)

    try:
        board = Board.from_fen(fen)

        square = None
        row = request.args.get("row", type=int)
        col = request.args.get("col", type=int)
        if row is not None and col is not None:
            square = Square(row, col)

        moves = move_generator.generate_legal_moves(board, square)

        return _json_response({
            "moves": [_serialize_move(m) for m in moves],
        })
    except (TypeError, ValueError, IndexError) as e:
        return _json_response({"error": str(e)}, 400)


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
        "depth": 2,           // optional, dùng cho minimax
        "simulations": 100    // optional, dùng cho mcts
    }
    """
    data = request.get_json(silent=True) or {}
    try:
        fen = data["fen"]
        algorithm = data.get("algorithm", "minimax")
        board = Board.from_fen(fen)

        agent = AGENTS.get(algorithm)
        if agent is None:
            return _json_response({
                "error": f"Unknown algorithm: {algorithm}",
            }, 400)

        # Cấu hình agent (nếu có)
        if hasattr(agent, "set_depth"):
            depth = int(data.get("depth", 2))
            if not 1 <= depth <= MinimaxAgent.MAX_DEPTH:
                return _json_response({
                    "error": (
                        f"Depth must be between 1 and "
                        f"{MinimaxAgent.MAX_DEPTH}"
                    ),
                }, 400)
            agent.set_depth(depth)
        if hasattr(agent, "set_simulations"):
            simulations = int(data.get("simulations", 100))
            if not 1 <= simulations <= 10000:
                return _json_response({
                    "error": "Simulations must be between 1 and 10000",
                }, 400)
            agent.set_simulations(simulations)

        # AI suy nghĩ
        benchmark_logger.start_timer()
        move = agent.get_move(board)
        thinking_time = benchmark_logger.stop_timer()

        if move is None:
            return _json_response({
                "error": "AI không tìm được nước đi",
                "gameState": _serialize_game_state(board),
            }, 400)

        # Lấy stats
        stats = agent.get_stats()
        stats.thinking_time_ms = thinking_time

        # Thực hiện nước đi
        new_board = board.make_move(move)
        game_state = _serialize_game_state(new_board)
        status = game_state["status"]

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

        return _json_response({
            "move": _serialize_move(move),
            "newFen": game_state["fen"],
            "gameState": game_state,
            "stats": {
                "algorithm": stats.algorithm,
                "thinkingTimeMs": round(stats.thinking_time_ms, 2),
                "nodesEvaluated": stats.nodes_evaluated,
                "depthReached": stats.depth_reached,
                "evaluationScore": round(stats.evaluation_score, 4),
            },
        })

    except (KeyError, TypeError, ValueError, IndexError) as e:
        return _json_response({"error": str(e)}, 400)
    except Exception as e:
        return _json_response({"error": str(e)}, 500)


# ==============================================================
# GET /api/benchmark — Kết quả benchmark
# ==============================================================
@game_bp.route("/benchmark", methods=["GET"])
def get_benchmark():
    """Trả về kết quả benchmark tổng hợp."""
    try:
        summary = benchmark_logger.get_summary_by_algorithm()
        records = benchmark_logger.read_all_records()

        return _json_response({
            "summary": summary,
            "totalRecords": len(records),
        })

    except Exception as e:
        return _json_response({"error": str(e)}, 500)


# ==============================================================
# Helpers
# ==============================================================

def _sanitize_json_value(value):
    """Recursively replace non-finite floats with JSON null."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {
            key: _sanitize_json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize_json_value(item) for item in value]
    return value


def _json_response(payload: dict, status: int = 200):
    """Create a browser-safe strict JSON response."""
    return jsonify(_sanitize_json_value(payload)), status


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


def _serialize_game_state(board: Board) -> dict:
    """Chuyển toàn bộ Board cần cho frontend demo sang JSON."""
    return {
        "fen": board.to_fen(),
        "board": [
            [
                None if piece is None else {
                    "type": piece.piece_type,
                    "color": piece.color,
                }
                for piece in row
            ]
            for row in board.grid
        ],
        "currentPlayer": board.current_player,
        "status": move_generator.get_game_status(board),
        "castling": {
            "whiteKingSide": board.castling.white_king_side,
            "whiteQueenSide": board.castling.white_queen_side,
            "blackKingSide": board.castling.black_king_side,
            "blackQueenSide": board.castling.black_queen_side,
        },
        "enPassant": (
            None if board.en_passant is None else {
                "row": board.en_passant.row,
                "col": board.en_passant.col,
            }
        ),
        "halfMoveClock": board.half_move_clock,
        "fullMoveNumber": board.full_move_number,
    }
