/**
 * frontend/src/api.js
 * HTTP client gọi backend API.
 *
 * Base URL: http://localhost:8080/api
 */

const API_BASE = '/api';

/**
 * POST /api/move — Người chơi thực hiện nước đi.
 * @param {string} fen - FEN string hiện tại
 * @param {Object} move - { from: {row, col}, to: {row, col}, promotion? }
 * @returns {Promise<MoveResponse>}
 */
export async function makeMove(fen, move) {
  const response = await fetch(`${API_BASE}/move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, move }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Move failed');
  }

  return response.json();
}

/**
 * GET /api/legal-moves — Lấy danh sách nước đi hợp lệ.
 * @param {string} fen - FEN string hiện tại
 * @param {number} [row] - Row của ô (optional)
 * @param {number} [col] - Col của ô (optional)
 * @returns {Promise<LegalMovesResponse>}
 */
export async function getLegalMoves(fen, row, col) {
  const params = new URLSearchParams({ fen });
  if (row !== undefined) params.set('row', row);
  if (col !== undefined) params.set('col', col);

  const response = await fetch(`${API_BASE}/legal-moves?${params}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get legal moves');
  }

  return response.json();
}

/**
 * POST /api/ai-move — AI tính và trả về nước đi.
 * @param {string} fen - FEN string hiện tại
 * @param {string} algorithm - 'greedy' | 'minimax' | 'mcts'
 * @param {number} [depth] - Độ sâu cho Minimax
 * @param {number} [simulations] - Số simulations cho MCTS
 * @returns {Promise<MoveResponse>}
 */
export async function getAiMove(fen, algorithm, depth, simulations) {
  const body = { fen, algorithm };
  if (depth !== undefined) body.depth = depth;
  if (simulations !== undefined) body.simulations = simulations;

  const response = await fetch(`${API_BASE}/ai-move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'AI move failed');
  }

  return response.json();
}

/**
 * GET /api/benchmark — Lấy kết quả benchmark.
 * @returns {Promise<BenchmarkResponse>}
 */
export async function getBenchmark() {
  const response = await fetch(`${API_BASE}/benchmark`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get benchmark');
  }

  return response.json();
}
