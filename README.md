# ♟ Chess AI — So sánh thuật toán AI trong cờ vua

## Mô tả dự án

Dự án xây dựng ứng dụng chơi cờ vua có tích hợp 3 thuật toán AI:

| Thuật toán | Mô tả | Vai trò |
|---|---|---|
| **Greedy Best-First Search** | Thuật toán tham lam, chọn nước đi tốt nhất ở depth=1 | Baseline Model |
| **Minimax + Alpha-Beta Pruning** | Thuật toán cổ điển, tìm kiếm sâu có cắt tỉa | Thuật toán logic truyền thống |
| **Monte Carlo Tree Search (MCTS)** | Thuật toán dựa trên mô phỏng ngẫu nhiên + UCB1 | Thuật toán xác suất hiện đại |

## Cấu trúc dự án

```
ChessAI/
├── frontend/                  # React UI
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChessBoard.jsx       # UI bàn cờ 8×8
│   │   │   ├── GameControls.jsx     # Chọn AI, depth
│   │   │   └── BenchmarkChart.jsx   # Biểu đồ metrics
│   │   ├── hooks/
│   │   │   └── useGame.js           # Custom hook quản lý game state
│   │   ├── api.js                   # HTTP client gọi backend
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # Python Flask API + Game Engine
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── board.py                 # State bàn cờ (FEN, piece placement)
│   │   ├── move_generator.py        # Sinh nước đi hợp lệ
│   │   └── benchmark_logger.py      # Ghi metrics ra CSV
│   ├── api/
│   │   ├── __init__.py
│   │   └── game_controller.py       # REST API endpoints
│   ├── app.py                       # Flask app entry point
│   └── requirements.txt
│
├── ai-core/                   # AI Agents (Plug-and-Play)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── agent.py                 # Interface chung (Abstract class)
│   │   ├── greedy_agent.py          # Greedy Best-First Search
│   │   ├── minimax_agent.py         # Minimax + Alpha-Beta Pruning
│   │   └── mcts_agent.py           # Monte Carlo Tree Search
│   └── __init__.py
│
├── shared/
│   └── types.ts                     # GameState, Move, Piece, Player, AlgorithmType
│
├── tests/
│   └── engine/
│       ├── __init__.py
│       └── test_board.py            # Unit test engine + AI
│
├── scripts/
│   └── run_benchmark.py             # Round Robin tự động giữa 3 AI
│
├── benchmark_results.csv            # Dữ liệu thực nghiệm
├── docker-compose.yml               # Chạy toàn bộ 1 lệnh
└── README.md
```

## API Contract

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/api/move` | Thực hiện nước đi của người chơi |
| `GET` | `/api/legal-moves` | Lấy danh sách nước đi hợp lệ |
| `POST` | `/api/ai-move` | AI tính và trả về nước đi |
| `GET` | `/api/benchmark` | Lấy kết quả benchmark |

## Agent Interface

```python
class Agent(ABC):
    def get_move(self, board: Board) -> Move:
        """Trả về nước đi tốt nhất theo thuật toán"""
        ...

    def get_stats(self) -> BenchmarkStats:
        """Trả về thống kê: thời gian, số node duyệt, ..."""
        ...
```

## Phân chia nhánh Git

| Thành viên | Nhánh sở hữu | Không được sửa |
|---|---|---|
| **TV-A** | `feature/ui-board`, `feature/ui-controls`, `feature/ui-benchmark` | `backend/`, `ai-core/` |
| **TV-B** | `feature/game-engine`, `feature/api-endpoints` | `frontend/`, `ai-core/agents/` |
| **TV-C** | `feature/greedy-agent`, `feature/minimax-agent`, `feature/mcts-agent` | `frontend/`, `backend/engine/` |

## Hướng dẫn Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional)

### Chạy bằng Docker (Khuyến nghị)
```bash
docker-compose up --build
```

### Chạy thủ công

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python app.py
# Server chạy tại http://localhost:8080
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# UI chạy tại http://localhost:3000
```

## Metrics đánh giá

- ⏱ **Thời gian suy nghĩ trung bình** (ms/move)
- 🔢 **Số lượng trạng thái đã duyệt** (nodes evaluated)
- 🏆 **Tỷ lệ chiến thắng** (win rate) qua các ván đấu giả lập Round Robin