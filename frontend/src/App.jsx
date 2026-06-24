/**
 * frontend/src/App.jsx
 * Component gốc — layout chính của ứng dụng Chess AI.
 */

import React, { useState } from 'react';
import ChessBoard from './components/ChessBoard.jsx';
import GameControls from './components/GameControls.jsx';
import BenchmarkChart from './components/BenchmarkChart.jsx';
import { useGame } from './hooks/useGame.js';
import './App.css';

function App() {
  const {
    gameState,
    selectedSquare,
    legalMoves,
    stats,
    benchmarkData,
    handleSquareClick,
    handleAiMove,
    handleNewGame,
    handleAlgorithmChange,
    handleDepthChange,
    handleSimulationsChange,
    handleStartAutoPlay,
    handlePauseAutoPlay,
    handleStepAutoPlay,
    handleAutoPlayDelayChange,
    handleMaxAutoPliesChange,
    setWhiteAiAlgorithm,
    setBlackAiAlgorithm,
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
  } = useGame();

  const [showBenchmark, setShowBenchmark] = useState(false);

  return (
    <div className="app">
      <header className="app-header">
        <h1>♟ Chess AI</h1>
        <p className="subtitle">So sánh thuật toán: Greedy · Minimax · MCTS</p>
      </header>

      <main className="app-main">
        <div className="game-area">
          {/* Bàn cờ */}
          <ChessBoard
            gameState={gameState}
            selectedSquare={selectedSquare}
            legalMoves={legalMoves}
            onSquareClick={isAutoPlaying ? undefined : handleSquareClick}
          />

          {/* Điều khiển */}
          <GameControls
            algorithm={algorithm}
            depth={depth}
            simulations={simulations}
            whiteAiAlgorithm={whiteAiAlgorithm}
            blackAiAlgorithm={blackAiAlgorithm}
            isAutoPlaying={isAutoPlaying}
            autoPlayDelay={autoPlayDelay}
            maxAutoPlies={maxAutoPlies}
            autoPlayPlies={autoPlayPlies}
            isThinking={isThinking}
            error={error}
            stats={stats}
            gameState={gameState}
            onAlgorithmChange={handleAlgorithmChange}
            onDepthChange={handleDepthChange}
            onSimulationsChange={handleSimulationsChange}
            onWhiteAiAlgorithmChange={setWhiteAiAlgorithm}
            onBlackAiAlgorithmChange={setBlackAiAlgorithm}
            onStartAutoPlay={handleStartAutoPlay}
            onPauseAutoPlay={handlePauseAutoPlay}
            onStepAutoPlay={handleStepAutoPlay}
            onAutoPlayDelayChange={handleAutoPlayDelayChange}
            onMaxAutoPliesChange={handleMaxAutoPliesChange}
            onAiMove={handleAiMove}
            onNewGame={handleNewGame}
            onToggleBenchmark={() => setShowBenchmark(!showBenchmark)}
          />
        </div>

        {/* Biểu đồ Benchmark */}
        {showBenchmark && (
          <BenchmarkChart data={benchmarkData} />
        )}
      </main>

      <footer className="app-footer">
        <p>HUST — Nhập môn Trí tuệ Nhân tạo</p>
      </footer>
    </div>
  );
}

export default App;
