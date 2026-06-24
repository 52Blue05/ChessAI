# Chess AI Desktop

Dự án cờ vua với AI (Artificial Intelligence) hỗ trợ so sánh (benchmark) 3 thuật toán phổ biến trong game playing: Greedy, Minimax, và Monte Carlo Tree Search (MCTS).

Phiên bản mới nhất đã được chuyển đổi từ Web (React/Flask) sang ứng dụng Desktop chạy bằng Python và Pygame, loại bỏ sự phụ thuộc vào Docker và Localhost, giúp việc cài đặt và chạy trực tiếp trên máy trở nên dễ dàng và mượt mà hơn.

## Tính năng
- ♟️ **Người vs AI**: Chơi trực tiếp với AI. Chọn thuật toán AI mong muốn và đánh bại nó.
- 🤖 **AI vs AI**: Chọn 2 thuật toán và xem chúng thi đấu tự động với nhau.
- 📊 **Benchmark**: Chế độ giả lập tự động vòng tròn (Round Robin). Các AI tự động thi đấu với nhau (10 - 20 ván mỗi cặp) để thu thập dữ liệu thống kê (thời gian suy nghĩ, số node đã duyệt, tỉ lệ thắng) và hiển thị kết quả bằng bảng và biểu đồ.

## Thuật toán AI
1. **Greedy**: Lựa chọn nước đi tốt nhất ngay lập tức (tham lam) dựa trên đánh giá hiện tại, không nhìn xa.
2. **Minimax + Alpha-Beta Pruning**: Duyệt cây trò chơi với độ sâu xác định, tìm kiếm nước đi tối ưu và cắt tỉa (pruning) các nhánh không cần thiết để tăng tốc độ.
3. **MCTS (Monte Carlo Tree Search)**: Dùng mô phỏng ngẫu nhiên (random rollouts) để đánh giá các nước đi, cực kỳ hiệu quả khi cây trò chơi quá lớn.

## Cài đặt và Chạy

### Yêu cầu
- Python 3.10+
- Pygame >= 2.5.0

### Hướng dẫn
1. Clone repository về máy:
   ```bash
   git clone <repo_url>
   cd ChessAI
   ```
2. (Khuyến nghị) Tạo môi trường ảo:
   ```bash
   python -m venv venv
   # Kích hoạt trên Windows:
   venv\Scripts\activate
   # Kích hoạt trên MacOS/Linux:
   source venv/bin/activate
   ```
3. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
4. Chạy game:
   ```bash
   python main.py
   ```

## Cấu trúc thư mục mới
- `ai_core/`: Chứa mã nguồn của 3 thuật toán AI (`greedy`, `minimax`, `mcts`) và interface cơ sở.
- `backend/engine/`: Logic core của cờ vua (Board, MoveGenerator, BenchmarkLogger).
- `gui/`: Chứa toàn bộ giao diện desktop viết bằng Pygame (constants, widgets, renderer, screens).
- `main.py`: File entry point để khởi động ứng dụng.