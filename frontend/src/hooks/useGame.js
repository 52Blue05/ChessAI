/**
 * frontend/src/hooks/useGame.js
 * Custom hook quản lý game state và tương tác với backend API.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { makeMove, getLegalMoves, getAiMove } from '../api.js';

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const TERMINAL_STATUSES = new Set(['checkmate', 'stalemate', 'draw']);
const AUTO_PLAY_DEPTH = 2;
const AUTO_PLAY_SIMULATIONS = 100;
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
  const [algorithm, setAlgorithm] = useState('minimax');
  const [depth, setDepth] = useState(2);
  const [simulations, setSimulations] = useState(100);
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState(null);
  const [whiteAiAlgorithm, setWhiteAiAlgorithm] = useState('minimax');
  const [blackAiAlgorithm, setBlackAiAlgorithm] = useState('greedy');
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [autoPlayDelay, setAutoPlayDelay] = useState(500);
  const [maxAutoPlies, setMaxAutoPlies] = useState(200);
  const [autoPlayPlies, setAutoPlayPlies] = useState(0);
  const aiRequestInFlight = useRef(false);
  const gameGeneration = useRef(0);

  // Click vào ô trên bàn cờ
  const handleSquareClick = useCallback(async (row, col) => {
    if (
      isThinking
      || isAutoPlaying
      || TERMINAL_STATUSES.has(gameState.status)
    ) {
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
  }, [gameState, selectedSquare, legalMoves, isThinking, isAutoPlaying]);

  const requestAiMove = useCallback(async (
    selectedAlgorithm,
    selectedDepth,
    selectedSimulations,
  ) => {
    if (
      aiRequestInFlight.current
      || TERMINAL_STATUSES.has(gameState.status)
    ) {
      return false;
    }

    aiRequestInFlight.current = true;
    const requestGeneration = gameGeneration.current;
    setIsThinking(true);
    setError(null);
    setSelectedSquare(null);
    setLegalMoves([]);

    try {
      const response = await getAiMove(
        gameState.fen,
        selectedAlgorithm,
        selectedDepth,
        selectedSimulations,
      );
      if (requestGeneration !== gameGeneration.current) {
        return false;
      }
      setGameState(response.gameState);
      setStats(response.stats);
      if (TERMINAL_STATUSES.has(response.gameState.status)) {
        setIsAutoPlaying(false);
      }
      return true;
    } catch (error) {
      if (requestGeneration !== gameGeneration.current) {
        return false;
      }
      console.error('AI move failed:', error);
      setError(error.message);
      setIsAutoPlaying(false);
      return false;
    } finally {
      aiRequestInFlight.current = false;
      setIsThinking(false);
    }
  }, [gameState]);

  // AI đi trong chế độ người-vs-AI hiện tại.
  const handleAiMove = useCallback(async () => {
    if (isAutoPlaying) {
      return;
    }
    await requestAiMove(algorithm, depth, simulations);
  }, [isAutoPlaying, requestAiMove, algorithm, depth, simulations]);

  const handleStepAutoPlay = useCallback(async () => {
    if (
      isAutoPlaying
      || autoPlayPlies >= maxAutoPlies
      || TERMINAL_STATUSES.has(gameState.status)
    ) {
      return;
    }

    const selectedAlgorithm = (
      gameState.currentPlayer === 'white'
        ? whiteAiAlgorithm
        : blackAiAlgorithm
    );
    const moved = await requestAiMove(
      selectedAlgorithm,
      AUTO_PLAY_DEPTH,
      AUTO_PLAY_SIMULATIONS,
    );
    if (moved) {
      setAutoPlayPlies(count => count + 1);
    }
  }, [
    isAutoPlaying,
    autoPlayPlies,
    maxAutoPlies,
    gameState,
    whiteAiAlgorithm,
    blackAiAlgorithm,
    requestAiMove,
  ]);

  const handleStartAutoPlay = useCallback(() => {
    if (
      aiRequestInFlight.current
      || TERMINAL_STATUSES.has(gameState.status)
    ) {
      return;
    }

    setError(null);
    setSelectedSquare(null);
    setLegalMoves([]);
    setAutoPlayPlies(0);
    setIsAutoPlaying(true);
  }, [gameState.status]);

  const handlePauseAutoPlay = useCallback(() => {
    setIsAutoPlaying(false);
  }, []);

  useEffect(() => {
    if (!isAutoPlaying) {
      return undefined;
    }

    if (
      autoPlayPlies >= maxAutoPlies
      || TERMINAL_STATUSES.has(gameState.status)
    ) {
      setIsAutoPlaying(false);
      return undefined;
    }

    const timer = window.setTimeout(async () => {
      const selectedAlgorithm = (
        gameState.currentPlayer === 'white'
          ? whiteAiAlgorithm
          : blackAiAlgorithm
      );
      const moved = await requestAiMove(
        selectedAlgorithm,
        AUTO_PLAY_DEPTH,
        AUTO_PLAY_SIMULATIONS,
      );
      if (moved) {
        setAutoPlayPlies(count => count + 1);
      }
    }, autoPlayDelay);

    return () => window.clearTimeout(timer);
  }, [
    isAutoPlaying,
    autoPlayPlies,
    maxAutoPlies,
    autoPlayDelay,
    gameState,
    whiteAiAlgorithm,
    blackAiAlgorithm,
    requestAiMove,
  ]);

  // Ván mới
  const handleNewGame = useCallback(() => {
    gameGeneration.current += 1;
    setIsAutoPlaying(false);
    setGameState(createGameStateFromFen(STARTING_FEN));
    setSelectedSquare(null);
    setLegalMoves([]);
    setStats(null);
    setError(null);
    setAutoPlayPlies(0);
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

  const handleAutoPlayDelayChange = useCallback((value) => {
    if (Number.isFinite(value)) {
      setAutoPlayDelay(Math.min(5000, Math.max(100, value)));
    }
  }, []);

  const handleMaxAutoPliesChange = useCallback((value) => {
    if (Number.isFinite(value)) {
      setMaxAutoPlies(Math.min(1000, Math.max(1, value)));
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
  };
}
