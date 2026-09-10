# PHÂN HỆ ĐIỂM CÀ PHÊ — GIAO DIỆN (frontend-v2)

**Bản:** 1.0 — 08/09/2026 · Đọc sau [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md) ·
Áp các quy ước nền tảng của `frontend-v2` (DataTable, khung CRUD khai báo, `read-only-value`,
icon lucide, token semantic) và sổ case `/ui` — chỗ nào tài liệu này im lặng thì các quy ước
đó quyết.

## 0. Chỗ đứng

- Phân hệ mới **"Bán lẻ & quán"** (`ban_le`) — đúng ô thứ chín mà `09` §4 đã đặt tên, chỉ
  hiện với người có quyền. Một dòng ở `src/app/router/module-registry.ts`, thư mục
  `src/modules/coffee-point/`.
- Trạng thái/loại/cấp đọc từ file TS sinh bởi `gen_status_ts.py` — **không hand-write** bộ
  nhãn nào.
- Điểm hiển thị bằng số nguyên có phân tách nghìn (`format-money` dùng chung); dòng âm tô
  `text-destructive`. Không đơn vị "đ" — đơn vị là **điểm** (dù đang đề nghị 1 điểm = 1 đồng,
  nhãn phải là điểm để sau này đổi tỷ lệ không phải sửa chữ).

## 1. Ví điểm của tôi — `/retail/my-wallet` (C-02)

- **Khối trên:** thẻ số dư — con số to (`text-3xl font-semibold`), kèm hai dòng phụ: *Được
  cấp kỳ này* · *Đã tiêu kỳ này*. Dữ liệu từ `GET /api/coffee/my-wallet`, TanStack Query.
- **Khối dưới:** bảng lịch sử trên `DataTable`: Ngày · Loại (badge theo `CoffeeLedgerType`)
  · Điểm (± có màu) · Lý do/Đơn hàng (mã bill `pos_code` nếu là dòng tiêu) · Kỳ. Lọc theo kỳ.
- Người chưa được gán vào chương trình (không có `coffee_member`): **empty-state tử tế** —
  "Bạn chưa thuộc chương trình điểm cà phê, liên hệ Nhân sự" — không phải bảng trống trơ.

## 2. Chính sách cấp điểm — `/retail/policies` (A-01)

- `CrudListPage` thuần khai báo (`coffee-point/config/policy-crud.tsx`): cột Cấp (nhãn từ
  enum) · Mức điểm/tháng · Hiệu lực từ · Ghi chú.
- Thêm/Sửa qua `CrudFormDialog` (popup theo case **C-01**: chặn Esc/click-ngoài khi form dở,
  chỉ đóng bằng Hủy/X — khung CRUD chung đã có sẵn hành vi này).
- Dòng đã qua kỳ cấp (backend chặn sửa): nút Sửa **ẩn theo dữ liệu trả về**, và người dùng
  được dẫn "đổi mức = thêm dòng hiệu lực mới" ngay trong mô tả dialog. `can()` chỉ là tiện
  UI — chặn thật ở service.

## 3. Thành viên & ghép POS365 — `/retail/members` (B-01…B-04)

- `CrudListPage`: cột Mã NV · Họ tên (join hồ sơ nhân sự để hiển thị, không chép) · Cấp ·
  Trạng thái (badge `CoffeeMemberStatus`) · Ghép POS365 (mã `KH-…` hoặc nhãn *Chưa ghép*
  màu cảnh báo) · Số dư.
- **Dialog ghép** (thao tác nhanh → **popup theo C-01**, khuôn `booking-reason-dialog`):
  ô tìm gọi `pos-search` (SĐT/tên) → danh sách kết quả bên POS365 → chọn một dòng → nút
  **Xác nhận ghép**. Đã ghép rồi thì dialog chỉ hiện thông tin + nút *Gỡ ghép* (hỏi xác
  nhận, ghi audit) — **không cho ghép đè**.
- Nút **Tạo khách trên POS365** (B-03) hiện khi chưa ghép và tìm không ra: xem trước
  (tên, SĐT, mã NV sẽ gửi) rồi mới gọi — vì đây là hành động GHI sang hệ ngoài.
- Giá trị chỉ xem trong dialog dùng `read-only-value`, **cấm `<Input disabled>`**.

## 4. Sổ điểm & đối soát — `/retail/ledger` (C-03, D-02, D-04, D-05)

Một trang, **4 tab** (chỉ render tab đã làm — không render tab rỗng):

| Tab | Nội dung |
|---|---|
| **Sổ cái** | `DataTable`: Ngày · Nhân sự · Kỳ · Loại · Điểm · Lý do · Người ghi. Lọc người/kỳ/loại. Nút **Điều chỉnh** (quyền `coffee_ledger.write`) mở popup C-01: người, ±điểm, **lý do bắt buộc** |
| **Đơn chưa khớp** | Các `pos_order` UNMATCHED: Ngày · Mã bill · Khách POS365 · Điểm. Hành động từng dòng: *Gán người* (chọn nhân sự → sinh dòng tiêu) hoặc *Bỏ qua* (lý do bắt buộc) |
| **Đối soát** | Bảng lệch theo ngày: Tổng bên POS365 · Tổng sổ · Chênh. Dòng lệch có nút xử lý → dialog `adjust`. **Không có nút "tự sửa hết"** — cố ý |
| **Nhật ký đồng bộ** | `tab_pos_sync_run`: Lúc chạy · Loại · Kết quả · Kéo/Ghi/Bỏ qua · Lỗi. Nút **Chạy đồng bộ** (quyền `pos_order.write`) chọn loại — chạy xong refresh |

## 5. Tra cứu số dư cho quầy — `/retail/lookup` (C-04)

- Màn **tối giản cho tablet đặt ở quầy**: một ô nhập (mã NV hoặc SĐT) + Enter → tên + số dư
  **chữ rất to** (đọc được từ xa), nền đổi theo trạng thái: đủ dùng / số dư 0 / âm.
- Không bảng, không menu phụ; auto-clear sau 30 giây (người sau không thấy số của người
  trước). Đăng nhập bằng tài khoản vai trò `coffee_counter` — API chỉ trả `{name, balance}`
  nên màn không thể lộ hơn kể cả viết ẩu.
- Đây là **lớp vá số 2** cho việc POS365 không tự chặn người hết điểm — thu ngân liếc màn
  này trước khi bấm phương thức "Trừ điểm" với đơn lớn.

## 6. Việc KHÔNG làm ở bản giao diện đầu

| Không làm | Vì sao |
|---|---|
| Màn đặt món / self-order trong ERP | POS365 là màn order duy nhất (quyết định `17` §1); tự dựng order là gánh nghĩa vụ POS — `09` §12 |
| Dashboard riêng của phân hệ | Chưa có số liệu tích lũy; báo cáo E-01 ở bản 2 rồi tính |
| Thông báo đẩy "bạn vừa bị trừ X điểm" | Trễ đồng bộ tới 5 phút, bắn thông báo trễ gây hiểu nhầm hơn là giúp; cân nhắc lại khi có webhook |
| Sửa/xóa dòng sổ trên UI | Sổ chỉ-INSERT — UI không được vẽ nút mà backend không có |

**Tiếp theo:** [`06-lo-trinh-phase.md`](./06-lo-trinh-phase.md).
