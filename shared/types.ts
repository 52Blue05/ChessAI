/**
 * shared/types.ts
 * ⚠ File chung — chỉ sửa khi cả nhóm đồng ý
 *
 * Định nghĩa các kiểu dữ liệu dùng chung giữa frontend, backend, ai-core.
 */

// ============================================================
// Enum & Literal Types
// ============================================================

/** Loại quân cờ */
export type PieceType = "king" | "queen" | "rook" | "bishop" | "knight" | "pawn";

/** Màu quân */
export type Player = "white" | "black";

/** Thuật toán AI */
export type AlgorithmType = "greedy" | "minimax" | "mcts";

// ============================================================
// Core Models
// ============================================================

/** Một quân cờ trên bàn */
export interface Piece {
  type: PieceType;
  color: Player;
}

/** Một ô trên bàn cờ (0-indexed) */
export interface Square {
  row: number; // 0-7
  col: number; // 0-7
}

/** Nước đi */
export interface Move {
  from: Square;
  to: Square;
  promotion?: PieceType; // Phong cấp (nếu tốt đến hàng cuối)
  captured?: Piece;      // Quân bị bắt (nếu có)
}

/**
 * Trạng thái ván cờ — dùng FEN hoặc JSON schema.
 * Backend serialize/deserialize thông qua object này.
 */
export interface GameState {
  /** FEN string mô tả trạng thái bàn cờ */
  fen: string;

  /** Bàn cờ dạng 2D array (8×8), null = ô trống */
  board: (Piece | null)[][];

  /** Lượt đi hiện tại */
  currentPlayer: Player;

  /** Trạng thái ván đấu */
  status: "playing" | "check" | "checkmate" | "stalemate" | "draw";

  /** Lịch sử nước đi */
  moveHistory: Move[];

  /** Thông tin nhập thành */
  castling: {
    whiteKingSide: boolean;
    whiteQueenSide: boolean;
    blackKingSide: boolean;
    blackQueenSide: boolean;
  };

  /** Ô bắt tốt qua đường (en passant), null nếu không có */
  enPassant: Square | null;

  /** Số nước đi không bắt quân / không đi tốt (cho luật 50 nước) */
  halfMoveClock: number;

  /** Số lượt đi đầy đủ */
  fullMoveNumber: number;
}

// ============================================================
// API Request / Response DTOs
// ============================================================

/** POST /api/move — Người chơi thực hiện nước đi */
export interface MoveRequest {
  fen: string;
  move: Move;
}

/** POST /api/ai-move — AI tính nước đi */
export interface AiMoveRequest {
  fen: string;
  algorithm: AlgorithmType;
  depth?: number;        // Dùng cho Minimax (mặc định 3)
  simulations?: number;  // Dùng cho MCTS (mặc định 1000)
}

/** Response chung cho các API trả về nước đi */
export interface MoveResponse {
  move: Move;
  newFen: string;
  gameState: GameState;
  stats?: BenchmarkStats;
}

/** GET /api/legal-moves */
export interface LegalMovesRequest {
  fen: string;
  square?: Square; // Nếu chỉ định, trả về nước đi của quân tại ô đó
}

export interface LegalMovesResponse {
  moves: Move[];
}

// ============================================================
// Benchmark & Statistics
// ============================================================

/** Thống kê hiệu năng của mỗi lần AI suy nghĩ */
export interface BenchmarkStats {
  /** Thuật toán đã dùng */
  algorithm: AlgorithmType;

  /** Thời gian suy nghĩ (milliseconds) */
  thinkingTimeMs: number;

  /** Số lượng trạng thái (node) đã duyệt */
  nodesEvaluated: number;

  /** Độ sâu thực tế đã tìm kiếm */
  depthReached: number;

  /** Điểm đánh giá (evaluation score) */
  evaluationScore: number;
}

/** GET /api/benchmark — Kết quả benchmark tổng hợp */
export interface BenchmarkResult {
  algorithm: AlgorithmType;
  totalGames: number;
  wins: number;
  losses: number;
  draws: number;
  avgThinkingTimeMs: number;
  avgNodesEvaluated: number;
  winRate: number; // 0.0 - 1.0
}

export interface BenchmarkResponse {
  results: BenchmarkResult[];
  matchups: Matchup[];
}

/** Kết quả đối đầu giữa 2 AI */
export interface Matchup {
  white: AlgorithmType;
  black: AlgorithmType;
  whiteWins: number;
  blackWins: number;
  draws: number;
  totalGames: number;
}
