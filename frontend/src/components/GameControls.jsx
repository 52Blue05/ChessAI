/**
 * frontend/src/components/GameControls.jsx
 * Panel điều khiển: chọn AI, depth, nút bấm.
 *
 * TV-A sở hữu (feature/ui-controls)
 */

import React from 'react';

const ALGORITHMS = [
  { value: 'greedy',  label: '🟢 Greedy (Tham lam)',     desc: 'Depth=1, nhanh nhất' },
  { value: 'minimax', label: '🔵 Minimax + Alpha-Beta', desc: 'Tìm kiếm sâu, chính xác' },
  { value: 'mcts',    label: '🔴 MCTS (Monte Carlo)',   desc: 'Mô phỏng ngẫu nhiên' },
];

/**
 * Panel điều khiển game.
 *
 * Props:
 *   algorithm: string
 *   depth: number
 *   simulations: number
 *   isThinking: boolean
 *   stats: BenchmarkStats | null
 *   gameState: { currentPlayer, status }
 *   onAlgorithmChange: (algorithm) => void
 *   onDepthChange: (depth) => void
 *   onAiMove: () => void
 *   onNewGame: () => void
 *   onToggleBenchmark: () => void
 */
function GameControls({
  algorithm,
  depth,
  simulations,
  whiteAiAlgorithm,
  blackAiAlgorithm,
  isAutoPlaying,
  autoPlayDelay,
  maxAutoPlies,
  autoPlayPlies,
  isThinking,
  error,
  stats,
  gameState,
  onAlgorithmChange,
  onDepthChange,
  onSimulationsChange,
  onWhiteAiAlgorithmChange,
  onBlackAiAlgorithmChange,
  onStartAutoPlay,
  onPauseAutoPlay,
  onStepAutoPlay,
  onAutoPlayDelayChange,
  onMaxAutoPliesChange,
  onAiMove,
  onNewGame,
  onToggleBenchmark,
}) {
  const status = gameState?.status || 'playing';
  const currentPlayer = gameState?.currentPlayer || 'white';

  return (
    <div className="game-controls" id="game-controls">
      <h2>⚙ Điều khiển</h2>

      {/* Trạng thái */}
      <div className={`status-badge ${status}`} id="game-status">
        {status === 'playing' && `🎮 Lượt: ${currentPlayer === 'white' ? 'Trắng' : 'Đen'}`}
        {status === 'check' && `⚠ Chiếu! Lượt: ${currentPlayer === 'white' ? 'Trắng' : 'Đen'}`}
        {status === 'checkmate' && `🏆 Chiếu hết!`}
        {status === 'stalemate' && `🤝 Hòa (Stalemate)`}
        {status === 'draw' && `🤝 Hòa`}
      </div>

      {/* Chọn thuật toán */}
      <div className="control-group">
        <label htmlFor="select-algorithm">Thuật toán AI</label>
        <select
          id="select-algorithm"
          value={algorithm}
          onChange={(e) => onAlgorithmChange?.(e.target.value)}
        >
          {ALGORITHMS.map(alg => (
            <option key={alg.value} value={alg.value}>
              {alg.label}
            </option>
          ))}
        </select>
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
          {ALGORITHMS.find(a => a.value === algorithm)?.desc}
        </p>
      </div>

      {/* Depth (cho Minimax) */}
      {algorithm === 'minimax' && (
        <div className="control-group">
          <label htmlFor="input-depth">Độ sâu tìm kiếm (Depth)</label>
          <input
            id="input-depth"
            type="number"
            min="1"
            max="4"
            value={depth}
            onChange={(e) => onDepthChange?.(parseInt(e.target.value))}
          />
        </div>
      )}

      {/* Simulations (cho MCTS) */}
      {algorithm === 'mcts' && (
        <div className="control-group">
          <label htmlFor="input-simulations">Số lần mô phỏng</label>
          <input
            id="input-simulations"
            type="number"
            min="1"
            max="10000"
            step="25"
            value={simulations}
            onChange={(e) => onSimulationsChange?.(parseInt(e.target.value))}
          />
        </div>
      )}

      {/* Nút bấm */}
      <button
        className="btn btn-primary"
        id="btn-ai-move"
        onClick={onAiMove}
        disabled={
          isThinking
          || isAutoPlaying
          || status === 'checkmate'
          || status === 'stalemate'
          || status === 'draw'
        }
      >
        {isThinking ? '🤔 AI đang suy nghĩ...' : '🤖 AI đi'}
      </button>

      <button className="btn btn-secondary" id="btn-new-game" onClick={onNewGame}>
        🔄 Ván mới
      </button>

      <button className="btn btn-secondary" id="btn-benchmark" onClick={onToggleBenchmark}>
        📊 Benchmark
      </button>

      <div className="auto-play-panel">
        <h3>♟ AI vs AI</h3>

        <div className="control-group">
          <label htmlFor="select-white-ai">AI Trắng</label>
          <select
            id="select-white-ai"
            value={whiteAiAlgorithm}
            disabled={isAutoPlaying}
            onChange={(e) => onWhiteAiAlgorithmChange?.(e.target.value)}
          >
            {ALGORITHMS.map(alg => (
              <option key={`white-${alg.value}`} value={alg.value}>
                {alg.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="select-black-ai">AI Đen</label>
          <select
            id="select-black-ai"
            value={blackAiAlgorithm}
            disabled={isAutoPlaying}
            onChange={(e) => onBlackAiAlgorithmChange?.(e.target.value)}
          >
            {ALGORITHMS.map(alg => (
              <option key={`black-${alg.value}`} value={alg.value}>
                {alg.label}
              </option>
            ))}
          </select>
        </div>

        <div className="auto-play-inputs">
          <div className="control-group">
            <label htmlFor="input-auto-delay">Delay (ms)</label>
            <input
              id="input-auto-delay"
              type="number"
              min="100"
              max="5000"
              step="100"
              value={autoPlayDelay}
              disabled={isAutoPlaying}
              onChange={(e) => onAutoPlayDelayChange?.(parseInt(e.target.value))}
            />
          </div>

          <div className="control-group">
            <label htmlFor="input-max-plies">Max plies</label>
            <input
              id="input-max-plies"
              type="number"
              min="1"
              max="1000"
              value={maxAutoPlies}
              disabled={isAutoPlaying}
              onChange={(e) => onMaxAutoPliesChange?.(parseInt(e.target.value))}
            />
          </div>
        </div>

        <p className="auto-play-status">
          {isAutoPlaying ? 'Đang chạy' : 'Đã dừng'} · Ply {autoPlayPlies}/{maxAutoPlies}
        </p>

        <button
          className="btn btn-primary"
          id="btn-start-auto-play"
          onClick={onStartAutoPlay}
          disabled={
            isAutoPlaying
            || isThinking
            || status === 'checkmate'
            || status === 'stalemate'
            || status === 'draw'
          }
        >
          ▶ Start AI vs AI
        </button>

        <div className="auto-play-actions">
          <button
            className="btn btn-secondary"
            id="btn-pause-auto-play"
            onClick={onPauseAutoPlay}
            disabled={!isAutoPlaying}
          >
            ⏸ Pause / Stop
          </button>
          <button
            className="btn btn-secondary"
            id="btn-step-auto-play"
            onClick={onStepAutoPlay}
            disabled={
              isAutoPlaying
              || isThinking
              || autoPlayPlies >= maxAutoPlies
              || status === 'checkmate'
              || status === 'stalemate'
              || status === 'draw'
            }
          >
            ⏭ Step AI Move
          </button>
        </div>

        <p className="auto-play-note">
          Auto-play dùng Minimax depth 2 và MCTS 100 simulations.
        </p>
      </div>

      {error && (
        <p style={{ color: 'var(--color-accent)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
          {error}
        </p>
      )}

      {/* Thinking animation */}
      {isThinking && (
        <div className="thinking-indicator">
          <div className="thinking-dot"></div>
          <div className="thinking-dot"></div>
          <div className="thinking-dot"></div>
          <span>Đang tính toán...</span>
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="stats-panel" id="stats-panel">
          <h3>📈 Thống kê lần đi gần nhất</h3>
          <div className="stat-row">
            <span className="stat-label">Thuật toán</span>
            <span className="stat-value">{stats.algorithm}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Thời gian</span>
            <span className="stat-value">{stats.thinkingTimeMs?.toFixed(1)} ms</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Nodes duyệt</span>
            <span className="stat-value">{stats.nodesEvaluated?.toLocaleString()}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Depth</span>
            <span className="stat-value">{stats.depthReached}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Evaluation</span>
            <span className="stat-value">{stats.evaluationScore?.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default GameControls;
