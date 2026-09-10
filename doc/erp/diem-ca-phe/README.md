# PHÂN HỆ ĐIỂM CÀ PHÊ (POS365) — BỘ TÀI LIỆU KỸ THUẬT

**Lập:** 08/09/2026 · **Trạng thái:** thiết kế đã soát, CHƯA viết code — việc kế tiếp là
phase **CP0 (POC)** trong [`06-lo-trinh-phase.md`](./06-lo-trinh-phase.md).

Bài toán: quầy cà phê công ty bán trên **POS365**; nhân sự order và thanh toán bằng
**phương thức "Trừ điểm"** trên tài khoản điểm cá nhân; điểm **reset đầu mỗi tháng theo cấp
nhân sự**. ERP là **sổ cái duy nhất** — POS365 không giữ số dư.

## Gốc gác — đọc theo thứ tự nào

| Tài liệu | Vai trò |
|---|---|
| [`../09-phuc-loi-diem-va-pos.md`](../09-phuc-loi-diem-va-pos.md) | Bản **định hướng** (12/08): vì sao tách chính sách khỏi đầu nối, 3 phương án ai giữ số dư, 10 câu nghiệp vụ, 4 chỗ mất tiền thật. Các LUẬT ở đây vẫn hiệu lực |
| [`../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md`](../17-ke-hoach-trien-khai-pos365-diem-ca-phe.md) | Bản **quyết định phương án** (07/09): đổi từ "đẩy điểm" sang "phương thức thanh toán"; chốt reset tháng; phần API đã kiểm chứng + Phụ lục A chờ POC. Chỗ nào lệch `09` thì lấy `17` |
| **Thư mục này** | Bản **thiết kế thực thi** (08/09): tính năng có mã, bảng dữ liệu, thuật toán, phân quyền, giao diện, phase. Chỗ nào lệch `17` thì lấy thư mục này |

## Sáu tệp

| Tệp | Nội dung |
|---|---|
| [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md) | **31 tính năng** chia 7 nhóm (N nền · A chính sách · B thành viên · C sổ điểm · D đồng bộ · E báo cáo · G quyền), 22 thuộc bản đầu; mã N-xx/A-xx… là mã tra cứu chung của cả bộ |
| [`02-bang-du-lieu.md`](./02-bang-du-lieu.md) | 5 bảng + 6 IntEnum + biến cấu hình + 13 endpoint `/api/coffee/...`. Điểm đáng soát nhất: sổ cái chỉ-INSERT với cột `uniq_key` gánh mọi lời hứa chống trùng |
| [`03-tich-hop-pos365.md`](./03-tich-hop-pos365.md) | Client (phiên `ss-id`, retry, cầu dao `POS365_HARD_OFF`, lọc `Password`), thuật toán 5 task Celery, **POC 7 câu P1–P7**, bảng kịch bản hỏng |
| [`04-phan-quyen.md`](./04-phan-quyen.md) | 4 entity + SCOPE_FIELDS (test B-07 lên 48/48), ma trận action, 3 vai trò seed, 5 chỗ dễ hở phải soát lúc review |
| [`05-giao-dien.md`](./05-giao-dien.md) | Phân hệ "Bán lẻ & quán", 5 màn (Ví của tôi · Chính sách · Thành viên & ghép · Sổ & đối soát · Tra cứu quầy) theo khung CRUD + sổ case `/ui` |
| [`06-lo-trinh-phase.md`](./06-lo-trinh-phase.md) | **CP0 → CP5**, mỗi phase có điều kiện cần/đủ kiểm được + đường lui; tổng bản 1 ≈ **17–18 ngày công** 1 dev |

## Bốn câu nghiệp vụ còn treo (không chặn CP0–CP3, CHẶN CỨNG CP4)

1. **Bộ cấp phúc lợi** (`CoffeeLevel`) + bảng mức điểm từng cấp — A-02.
2. Có cần **duyệt bảng cấp phát từng kỳ** không (đề nghị: không — mức đã duyệt ở chính sách) — A-06.
3. **Âm điểm** xử lý thế nào (trừ kỳ sau / thu tiền) — C-05.
4. **Thuế TNCN** cho phúc lợi này — hỏi kế toán, quyết định khuôn xuất E-02.

## Ba luật một dòng, nhắc để khỏi mở lại tài liệu

- **Sổ chỉ ghi thêm** — mọi thay đổi số dư là một dòng sổ, kể cả sửa sai.
- **Không tự sửa khi lệch** — lệch lên màn hình, người xử lý, có lý do.
- **`POS365_HARD_OFF` mặc định bật** — chỉ prod được tắt; dev chạy cả ngày không một call ra quán thật.
