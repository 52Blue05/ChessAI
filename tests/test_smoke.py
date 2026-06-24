"""Minimal startup smoke tests for the ChessAI backend."""

import unittest

from backend.app import create_app
from ai_core.agents import GreedyAgent, MinimaxAgent, MCTSAgent


class BackendSmokeTests(unittest.TestCase):
    def test_ai_agents_import(self):
        self.assertIsNotNone(GreedyAgent)
        self.assertIsNotNone(MinimaxAgent)
        self.assertIsNotNone(MCTSAgent)

    def test_health_endpoint(self):
        app = create_app()
        client = app.test_client()

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "status": "ok",
                "service": "chess-ai-backend",
            },
        )


if __name__ == "__main__":
    unittest.main()
