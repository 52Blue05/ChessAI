/**
 * frontend/src/components/BenchmarkChart.jsx
 * Biểu đồ so sánh metrics giữa 3 thuật toán AI.
 *
 * TV-A sở hữu (feature/ui-benchmark)
 *
 * Hiển thị:
 * - Thời gian suy nghĩ trung bình (ms/move)
 * - Số node đã duyệt trung bình
 * - Tỷ lệ chiến thắng (win rate)
 */

import React from 'react';

const ALGORITHM_COLORS = {
  greedy: '#51cf66',
  minimax: '#6c63ff',
  mcts: '#ff6b6b',
};

const ALGORITHM_LABELS = {
  greedy: 'Greedy',
  minimax: 'Minimax',
  mcts: 'MCTS',
};

/**
 * Component biểu đồ benchmark.
 *
 * Props:
 *   data: {
 *     results: BenchmarkResult[],
 *     matchups: Matchup[]
 *   }
 */
function BenchmarkChart({ data }) {
  // Dữ liệu mẫu nếu chưa có data thật
  const results = data?.results || [
    { algorithm: 'greedy',  avgThinkingTimeMs: 0, avgNodesEvaluated: 0, winRate: 0 },
    { algorithm: 'minimax', avgThinkingTimeMs: 0, avgNodesEvaluated: 0, winRate: 0 },
    { algorithm: 'mcts',    avgThinkingTimeMs: 0, avgNodesEvaluated: 0, winRate: 0 },
  ];

  return (
    <div className="benchmark-section" id="benchmark-section">
      <h2>📊 Benchmark — So sánh thuật toán</h2>

      <div className="benchmark-grid">
        {/* Thời gian suy nghĩ */}
        <div className="benchmark-card">
          <h3>⏱ Thời gian TB (ms/move)</h3>
          <BarChart
            data={results}
            valueKey="avgThinkingTimeMs"
            formatValue={(v) => `${v.toFixed(1)} ms`}
          />
        </div>

        {/* Số node duyệt */}
        <div className="benchmark-card">
          <h3>🔢 Nodes duyệt TB</h3>
          <BarChart
            data={results}
            valueKey="avgNodesEvaluated"
            formatValue={(v) => v.toLocaleString()}
          />
        </div>

        {/* Win rate */}
        <div className="benchmark-card">
          <h3>🏆 Tỷ lệ thắng</h3>
          <BarChart
            data={results}
            valueKey="winRate"
            maxValue={1}
            formatValue={(v) => `${(v * 100).toFixed(1)}%`}
          />
        </div>
      </div>

      {/* Hướng dẫn */}
      {(!data || results.every(r => r.avgThinkingTimeMs === 0)) && (
        <p style={{
          textAlign: 'center',
          color: 'var(--color-text-muted)',
          marginTop: '1.5rem',
          fontSize: '0.9rem',
        }}>
          💡 Chạy <code>python scripts/run_benchmark.py</code> để tạo dữ liệu benchmark.
        </p>
      )}
    </div>
  );
}

/**
 * Component bar chart đơn giản (CSS-only, không cần thư viện).
 */
function BarChart({ data, valueKey, maxValue, formatValue = (v) => v }) {
  const max = maxValue || Math.max(...data.map(d => d[valueKey]), 1);

  return (
    <div className="bar-chart">
      {data.map(item => {
        const value = item[valueKey] || 0;
        const percentage = (value / max) * 100;

        return (
          <div className="bar-row" key={item.algorithm}>
            <span className="bar-label">{ALGORITHM_LABELS[item.algorithm]}</span>
            <div className="bar-track">
              <div
                className={`bar-fill ${item.algorithm}`}
                style={{ width: `${Math.max(percentage, 2)}%` }}
              >
                {percentage > 15 ? formatValue(value) : ''}
              </div>
            </div>
            {percentage <= 15 && (
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', minWidth: '50px' }}>
                {formatValue(value)}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default BenchmarkChart;
