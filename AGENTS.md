# AGENTS.md - ChessAI Development Instructions

## Project Context

Repository path:

F:\AIchess\ChessAI

Project: ChessAI

Stack:
- Backend: Python Flask
- Frontend: React + Vite
- AI algorithms:
  - Greedy Best-First Search
  - Minimax with Alpha-Beta Pruning
  - Monte Carlo Tree Search

Target environment:
- Windows
- PowerShell
- Python 3.12.10

## High-Level Goal

Make this project runnable and complete enough for a functional chess AI application.

The priority order is:

1. Backend runtime correctness
2. Chess engine correctness
3. AI algorithm correctness
4. API/frontend integration
5. Frontend polish only if necessary

Do not redesign or rewrite the whole project unless strictly necessary.

## Working Rules

1. Inspect the repository before editing.
2. Make small, testable changes.
3. Preserve the existing architecture where possible.
4. Explain each major change briefly.
5. Prefer correctness over UI polish.
6. Do not make unrelated formatting-only changes.
7. Update or add tests when fixing logic.
8. Keep the project runnable on Windows PowerShell.
9. After each phase, run relevant checks or explain why they cannot be run.

## Important Files to Inspect First

- README.md
- backend/app.py
- backend/api/game_controller.py
- backend/engine/board.py
- backend/engine/move_generator.py
- ai-core/agents/agent.py
- ai-core/agents/greedy_agent.py
- ai-core/agents/minimax_agent.py
- ai-core/agents/mcts_agent.py
- tests/engine/test_board.py
- frontend/src/api.js
- frontend/src/hooks/useGame.js
- frontend/src/components/ChessBoard.jsx
- frontend/src/components/GameControls.jsx

## Known Suspected Issues

### 1. requirements.txt formatting

backend/requirements.txt may be incorrectly formatted as one line.

Expected format:

```txt
flask>=3.0.0
flask-cors>=4.0.0