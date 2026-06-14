/**
 * frontend/src/hooks/useGame.js
 * Custom hook quản lý game state và tương tác với backend API.
 */

import { useState, useCallback } from 'react';
import { makeMove, getLegalMoves, getAiMove, getBenchmark } from '../api.js';

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

/**
 * Hook quản lý toàn bộ logic game.
 *
 * Returns:
 *   gameState, selectedSquare, legalMoves, stats, benchmarkData,
 *   handleSquareClick, handleAiMove, handleNewGame,
 *   handleAlgorithmChange, handleDepthChange,
 *   algorithm, depth, isThinking
 */
export function useGame() {
  const [fen, setFen] = useState(STARTING_FEN);
  const [gameState, setGameState] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [legalMoves, setLegalMoves] = useState([]);
  const [stats, setStats] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [algorithm, setAlgorithm] = useState('greedy');
  const [depth, setDepth] = useState(3);
  const [isThinking, setIsThinking] = useState(false);

  // Click vào ô trên bàn cờ
  const handleSquareClick = useCallback(async (row, col) => {
    if (selectedSquare) {
      // Đã chọn quân → thử di chuyển
      const isLegal = legalMoves.some(m => m.to.row === row && m.to.col === col);

      if (isLegal) {
        try {
          const response = await makeMove(fen, {
            from: selectedSquare,
            to: { row, col },
          });
          setFen(response.newFen);
          setGameState(response.gameState);
          setSelectedSquare(null);
          setLegalMoves([]);
        } catch (error) {
          console.error('Move failed:', error);
        }
      } else {
        // Click ô khác → chọn quân mới hoặc bỏ chọn
        setSelectedSquare(null);
        setLegalMoves([]);

        // Nếu click vào quân của mình → chọn
        try {
          const response = await getLegalMoves(fen, row, col);
          if (response.moves.length > 0) {
            setSelectedSquare({ row, col });
            setLegalMoves(response.moves);
          }
        } catch (error) {
          console.error('Get legal moves failed:', error);
        }
      }
    } else {
      // Chưa chọn quân → chọn
      try {
        const response = await getLegalMoves(fen, row, col);
        if (response.moves.length > 0) {
          setSelectedSquare({ row, col });
          setLegalMoves(response.moves);
        }
      } catch (error) {
        console.error('Get legal moves failed:', error);
      }
    }
  }, [fen, selectedSquare, legalMoves]);

  // AI đi
  const handleAiMove = useCallback(async () => {
    setIsThinking(true);
    setSelectedSquare(null);
    setLegalMoves([]);

    try {
      const response = await getAiMove(fen, algorithm, depth);
      setFen(response.newFen);
      setGameState(response.gameState);
      setStats(response.stats);
    } catch (error) {
      console.error('AI move failed:', error);
    } finally {
      setIsThinking(false);
    }
  }, [fen, algorithm, depth]);

  // Ván mới
  const handleNewGame = useCallback(() => {
    setFen(STARTING_FEN);
    setGameState(null);
    setSelectedSquare(null);
    setLegalMoves([]);
    setStats(null);
  }, []);

  // Đổi thuật toán
  const handleAlgorithmChange = useCallback((alg) => {
    setAlgorithm(alg);
  }, []);

  // Đổi depth
  const handleDepthChange = useCallback((d) => {
    setDepth(d);
  }, []);

  return {
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
    algorithm,
    depth,
    isThinking,
  };
}
