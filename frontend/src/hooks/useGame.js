/**
 * frontend/src/hooks/useGame.js
 * Custom hook quản lý game state và tương tác với backend API.
 */

import { useState, useCallback } from 'react';
import { makeMove, getLegalMoves, getAiMove } from '../api.js';

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const TERMINAL_STATUSES = new Set(['checkmate', 'stalemate', 'draw']);
const FEN_PIECES = {
  k: { type: 'king', color: 'black' },
  q: { type: 'queen', color: 'black' },
  r: { type: 'rook', color: 'black' },
  b: { type: 'bishop', color: 'black' },
  n: { type: 'knight', color: 'black' },
  p: { type: 'pawn', color: 'black' },
  K: { type: 'king', color: 'white' },
  Q: { type: 'queen', color: 'white' },
  R: { type: 'rook', color: 'white' },
  B: { type: 'bishop', color: 'white' },
  N: { type: 'knight', color: 'white' },
  P: { type: 'pawn', color: 'white' },
};

function createGameStateFromFen(fen) {
  const [placement, activeColor, castling, enPassant, halfMove, fullMove] = fen.split(' ');
  const board = placement.split('/').map(row => {
    const squares = [];
    for (const token of row) {
      if (/\d/.test(token)) {
        squares.push(...Array(Number(token)).fill(null));
      } else {
        squares.push({ ...FEN_PIECES[token] });
      }
    }
    return squares;
  });

  return {
    fen,
    board,
    currentPlayer: activeColor === 'w' ? 'white' : 'black',
    status: 'playing',
    castling: {
      whiteKingSide: castling.includes('K'),
      whiteQueenSide: castling.includes('Q'),
      blackKingSide: castling.includes('k'),
      blackQueenSide: castling.includes('q'),
    },
    enPassant: enPassant === '-' ? null : algebraicToSquare(enPassant),
    halfMoveClock: Number(halfMove),
    fullMoveNumber: Number(fullMove),
  };
}

function algebraicToSquare(notation) {
  return {
    row: 8 - Number(notation[1]),
    col: notation.charCodeAt(0) - 'a'.charCodeAt(0),
  };
}

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
  const [gameState, setGameState] = useState(() => createGameStateFromFen(STARTING_FEN));
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [legalMoves, setLegalMoves] = useState([]);
  const [stats, setStats] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [algorithm, setAlgorithm] = useState('greedy');
  const [depth, setDepth] = useState(3);
  const [simulations, setSimulations] = useState(100);
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState(null);

  // Click vào ô trên bàn cờ
  const handleSquareClick = useCallback(async (row, col) => {
    if (isThinking || TERMINAL_STATUSES.has(gameState.status)) {
      return;
    }

    setError(null);

    if (selectedSquare) {
      // Đã chọn quân → thử di chuyển
      const matchingMoves = legalMoves.filter(
        move => move.to.row === row && move.to.col === col,
      );

      if (matchingMoves.length > 0) {
        try {
          // UI chưa có hộp chọn promotion; mặc định phong hậu cho demo.
          const selectedMove = (
            matchingMoves.find(move => move.promotion === 'queen')
            || matchingMoves[0]
          );
          const response = await makeMove(gameState.fen, {
            from: selectedSquare,
            to: { row, col },
            ...(selectedMove.promotion && { promotion: selectedMove.promotion }),
          });
          setGameState(response.gameState);
          setSelectedSquare(null);
          setLegalMoves([]);
        } catch (error) {
          console.error('Move failed:', error);
          setError(error.message);
        }
      } else {
        // Click ô khác → chọn quân mới hoặc bỏ chọn
        setSelectedSquare(null);
        setLegalMoves([]);

        // Nếu click vào quân của mình → chọn
        try {
          const response = await getLegalMoves(gameState.fen, row, col);
          if (response.moves.length > 0) {
            setSelectedSquare({ row, col });
            setLegalMoves(response.moves);
          }
        } catch (error) {
          console.error('Get legal moves failed:', error);
          setError(error.message);
        }
      }
    } else {
      // Chưa chọn quân → chọn
      try {
        const response = await getLegalMoves(gameState.fen, row, col);
        if (response.moves.length > 0) {
          setSelectedSquare({ row, col });
          setLegalMoves(response.moves);
        }
      } catch (error) {
        console.error('Get legal moves failed:', error);
        setError(error.message);
      }
    }
  }, [gameState, selectedSquare, legalMoves, isThinking]);

  // AI đi
  const handleAiMove = useCallback(async () => {
    if (TERMINAL_STATUSES.has(gameState.status)) {
      return;
    }

    setIsThinking(true);
    setError(null);
    setSelectedSquare(null);
    setLegalMoves([]);

    try {
      const response = await getAiMove(
        gameState.fen,
        algorithm,
        depth,
        simulations,
      );
      setGameState(response.gameState);
      setStats(response.stats);
    } catch (error) {
      console.error('AI move failed:', error);
      setError(error.message);
    } finally {
      setIsThinking(false);
    }
  }, [gameState, algorithm, depth, simulations]);

  // Ván mới
  const handleNewGame = useCallback(() => {
    setGameState(createGameStateFromFen(STARTING_FEN));
    setSelectedSquare(null);
    setLegalMoves([]);
    setStats(null);
    setError(null);
  }, []);

  // Đổi thuật toán
  const handleAlgorithmChange = useCallback((alg) => {
    setAlgorithm(alg);
  }, []);

  // Đổi depth
  const handleDepthChange = useCallback((d) => {
    if (Number.isFinite(d)) {
      setDepth(Math.min(6, Math.max(1, d)));
    }
  }, []);

  const handleSimulationsChange = useCallback((value) => {
    if (Number.isFinite(value)) {
      setSimulations(Math.min(10000, Math.max(1, value)));
    }
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
    handleSimulationsChange,
    algorithm,
    depth,
    simulations,
    isThinking,
    error,
  };
}
