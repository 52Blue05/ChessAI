/**
 * frontend/src/components/ChessBoard.jsx
 * Component hiển thị bàn cờ 8×8.
 *
 * TV-A sở hữu (feature/ui-board)
 */

import React from 'react';

// Unicode chess pieces
const PIECE_SYMBOLS = {
  king:   { white: '♔', black: '♚' },
  queen:  { white: '♕', black: '♛' },
  rook:   { white: '♖', black: '♜' },
  bishop: { white: '♗', black: '♝' },
  knight: { white: '♘', black: '♞' },
  pawn:   { white: '♙', black: '♟' },
};

/**
 * Render bàn cờ 8×8.
 *
 * Props:
 *   gameState: { board: (Piece|null)[][] }
 *   selectedSquare: { row, col } | null
 *   legalMoves: Move[]
 *   onSquareClick: (row, col) => void
 */
function ChessBoard({ gameState, selectedSquare, legalMoves = [], onSquareClick }) {
  const board = gameState?.board || createEmptyBoard();

  const isLegalMove = (row, col) => {
    return legalMoves.some(m => m.to.row === row && m.to.col === col);
  };

  const isSelected = (row, col) => {
    return selectedSquare && selectedSquare.row === row && selectedSquare.col === col;
  };

  return (
    <div className="chess-board" id="chess-board">
      {board.map((row, r) =>
        row.map((piece, c) => {
          const isLight = (r + c) % 2 === 0;
          const selected = isSelected(r, c);
          const legal = isLegalMove(r, c);
          const hasPiece = piece !== null;

          const classNames = [
            'chess-square',
            isLight ? 'light' : 'dark',
            selected ? 'selected' : '',
            legal ? 'legal-move' : '',
            legal && hasPiece ? 'has-piece' : '',
          ].filter(Boolean).join(' ');

          return (
            <div
              key={`${r}-${c}`}
              className={classNames}
              id={`square-${r}-${c}`}
              onClick={() => onSquareClick?.(r, c)}
            >
              {piece && getPieceSymbol(piece)}
            </div>
          );
        })
      )}
    </div>
  );
}

function getPieceSymbol(piece) {
  const symbols = PIECE_SYMBOLS[piece.type];
  return symbols ? symbols[piece.color] : '?';
}

function createEmptyBoard() {
  // Tạo bàn cờ khởi đầu mặc định (hiển thị khi chưa có gameState)
  const board = Array(8).fill(null).map(() => Array(8).fill(null));

  // Hàng 8 (đen)
  const backRow = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook'];
  for (let c = 0; c < 8; c++) {
    board[0][c] = { type: backRow[c], color: 'black' };
    board[1][c] = { type: 'pawn', color: 'black' };
    board[6][c] = { type: 'pawn', color: 'white' };
    board[7][c] = { type: backRow[c], color: 'white' };
  }

  return board;
}

export default ChessBoard;
