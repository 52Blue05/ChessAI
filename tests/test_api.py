"""Integration tests for the frontend-facing game API contract."""

from unittest.mock import patch

import pytest

from backend.api import game_controller
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _post_move(client, fen, from_row, from_col, to_row, to_col, promotion=None):
    move = {
        "from": {"row": from_row, "col": from_col},
        "to": {"row": to_row, "col": to_col},
    }
    if promotion is not None:
        move["promotion"] = promotion
    return client.post("/api/move", json={"fen": fen, "move": move})


def test_player_move_returns_complete_game_state(client):
    response = _post_move(
        client,
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        6,
        4,
        4,
        4,
    )

    assert response.status_code == 200
    payload = response.get_json()
    state = payload["gameState"]

    assert payload["newFen"] == state["fen"]
    assert state["currentPlayer"] == "black"
    assert state["status"] == "playing"
    assert state["board"][4][4] == {"type": "pawn", "color": "white"}
    assert state["board"][6][4] is None
    assert state["enPassant"] == {"row": 5, "col": 4}


def test_castling_response_contains_moved_king_and_rook(client):
    response = _post_move(
        client,
        "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
        7,
        4,
        7,
        6,
    )

    assert response.status_code == 200
    state = response.get_json()["gameState"]
    assert state["board"][7][6] == {"type": "king", "color": "white"}
    assert state["board"][7][5] == {"type": "rook", "color": "white"}
    assert state["board"][7][4] is None
    assert state["board"][7][7] is None


def test_en_passant_response_removes_captured_pawn(client):
    response = _post_move(
        client,
        "4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1",
        4,
        3,
        5,
        4,
    )

    assert response.status_code == 200
    state = response.get_json()["gameState"]
    assert state["board"][5][4] == {"type": "pawn", "color": "black"}
    assert state["board"][4][4] is None
    assert state["board"][4][3] is None
    assert state["enPassant"] is None


def test_promotion_requires_and_returns_selected_piece(client):
    fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"

    missing = _post_move(client, fen, 1, 0, 0, 0)
    promoted = _post_move(client, fen, 1, 0, 0, 0, promotion="queen")

    assert missing.status_code == 400
    assert promoted.status_code == 200
    payload = promoted.get_json()
    assert payload["move"]["promotion"] == "queen"
    assert payload["gameState"]["board"][0][0] == {
        "type": "queen",
        "color": "white",
    }


def test_ai_move_returns_board_and_stats(client):
    with patch.object(game_controller.benchmark_logger, "log_move"):
        response = client.post(
            "/api/ai-move",
            json={
                "fen": (
                    "rnbqkbnr/pppppppp/8/8/8/8/"
                    "PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                ),
                "algorithm": "greedy",
            },
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["newFen"] == payload["gameState"]["fen"]
    assert payload["gameState"]["currentPlayer"] == "black"
    assert len(payload["gameState"]["board"]) == 8
    assert payload["stats"]["algorithm"] == "greedy"
    assert payload["stats"]["nodesEvaluated"] > 0
