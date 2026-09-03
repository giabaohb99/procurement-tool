# P-05 — Cắm vào bộ máy duyệt ✅ XONG (CR-259)

## Đã làm

`leave/approval_bridge.py` — entity `leave_request`:

- `entity_hooks.register(...)` bốn kết cục · `register_subject` · `register_reader`;
- `start_approval()` trình phiếu, trả `0` khi chưa khai luồng;
- `create_leave_document()` sinh giấy **GNP** vào sổ văn thư sau khi duyệt (QĐ-NP5);
- `cancel_request()` rút phiên duyệt rồi hủy đơn.

Test: `test_nghi_phep_qua_bo_may_duyet.py` — 16 bài chạy trên **luồng thật**, để
bộ máy tự gọi hook.

## Quyết định đáng ghi

- **Ba kết cục không-duyệt gộp một hàm `_release_and_set`.** Cả ba làm đúng một
  việc với quỹ; tách ba bản chép thì sớm muộn có một bản quên dòng `release`, và
  lỗi đó **không có triệu chứng** cho tới khi ai đó cộng tay lại sổ cuối năm.
- **Trừ quỹ TRƯỚC, sinh giấy SAU.** Trừ quỹ là phần bắt buộc đúng; sinh giấy gọi
  sang cả một phân hệ khác nên khả năng hỏng cao hơn nhiều.
- **Không có loại văn bản `GNP` thì bỏ qua im lặng.** Văn thư là phân hệ tùy chọn;
  bắt mọi nơi phải có nó mới nộp được đơn là buộc hai phân hệ vào nhau vô ích.
- **Giấy GNP sinh ra ở trạng thái Nháp và KHÔNG tự gửi duyệt** — nó đã được duyệt
  rồi, ở chính tờ đơn. Đẩy vào luồng `document` lần nữa là ký hai lượt cho một việc.
- **`register_reader` là bắt buộc.** Thiếu nó thì bộ máy trả `True` cho mọi người
  và `/api/approvals/of/leave_request/<id>` phơi tên người nghỉ cho bất kỳ ai đăng
  nhập — đúng lỗ hổng đã dựng lại được với văn bản 25/08/2026.
- **Chưa khai luồng thì vẫn nộp được** (`start` trả `None` → `instance_id = 0`),
  và người có `leave_request.approve` bấm duyệt thẳng.

## Lỗi đã sửa trong đợt này

**Hủy đơn đang trong luồng bị chặn** — dựng lại được 03/09/2026 lúc chạy thử API:
đường hủy gọi nhầm `block_legacy_path`, nên người xin nghỉ đổi ý ăn đúng câu
*"đừng bấm duyệt thẳng ở đây"*, vô nghĩa với thao tác họ vừa làm, và **không còn
cách nào rút đơn**. Tệ hơn: bỏ chốt đó mà không rút phiên thì phiếu duyệt vẫn
chạy, người duyệt ký xong là hook trừ quỹ cho một tờ đơn đã hủy.

Cách sửa: `cancel_request()` **rút phiên duyệt** (`action_service.withdraw`) rồi
mới hủy. Hai luật của bộ máy vọng ra và cả hai đều đúng với nghỉ phép — *chỉ người
trình mới rút được* và *đã có người ký thì không rút*. Ba bài kiểm chốt chỗ này;
đã thử đổi ngược lại, đúng ba bài đó đỏ.

Kèm theo: `cancel_request` đặt ở **bridge chứ không ở controller**. Để ở controller
thì không bài kiểm nào chạm tới được — mà đúng thứ tự hai bước này là chỗ đã sai.
