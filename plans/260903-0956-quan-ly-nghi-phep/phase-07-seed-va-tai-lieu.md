# P-07 — Seed, tài liệu, gói tri thức ✅ XONG (CR-259)

## Đã làm

| Việc | Ở đâu |
|---|---|
| Seed 7 loại nghỉ · 4 bậc thâm niên · 11 ngày lễ 2026 · luồng duyệt | `backend/app/seed_nghi_phep.py` |
| Tài liệu chức năng | `doc/tai-lieu-chuc-nang/17-nghi-phep.md` + mục 30 ở `00-muc-luc.md` |
| Gói tri thức Trợ lý AI (~1 500 token) | `backend/app/modules/assistant/packs/40-nghi-phep.md` |
| Nhật ký thay đổi | dòng **CR-259** ở `doc/tai-lieu-ky-thuat/change-log.md` |

## Quyết định đáng ghi

- **Seed KHÔNG nằm trong `app/seed.py`**, nên `start.sh` không tự chạy. Nạp 7 loại
  nghỉ + luồng duyệt vào một môi trường chưa dùng phân hệ này là bày ra danh mục
  rác. Chạy tay khi bật phân hệ:
  `docker compose exec api python -m app.seed_nghi_phep`.
- **Chỉ THÊM, không xóa, không ghi đè** — chạy mười lần ra một bộ. Đã kiểm: lần
  hai in ra `thêm 0` ở cả ba nhóm và `Luồng duyệt: đã có`.
- **`code` của loại nghỉ khớp `core/leave_codes.LEAVE_TYPE_SET`** — đó là mã ghi
  sang metadata của giấy GNP; lệch một ký tự là giấy sinh ra mang loại nghỉ vô nghĩa.
- **Luồng `NP_DON_NGHI_PHEP` không khai điều kiện** — mọi đơn đi đường này. Muốn
  luồng riêng cho một loại nghỉ thì thêm luồng `priority` cao hơn kèm điều kiện
  `leave_type_id in [...]`; bối cảnh đã đưa sẵn ô đó ra.
- Luồng này **cùng tồn tại** với `VB_NGHI_PHEP` (entity `document`) của CR-159, và
  đó là đúng: đơn chạy trước, giấy GNP sinh ra sau khi đơn đã duyệt và không vào
  luồng nào nữa.
- Gói tri thức viết theo ba nguyên tắc ở `packs/README.md`, nặng nhất là phần
  **CẤM nói**: không tiết lộ đơn của người khác (hệ trả 404 chứ không 403, nên
  trợ lý **không được** nói "đơn không tồn tại"), và không tự đoán số ngày còn lại.

## Việc còn lại của người vận hành

1. `docker compose exec api python -m app.seed_nghi_phep` trên môi trường đích.
2. **Cấp bốn khóa quyền** cho các vai trò đang chạy (seed không ghi đè — D-018).
3. **Nhập `hire_date`** cho hồ sơ cũ trước khi cấp quỹ, nếu không thâm niên tính
   bằng 0 (Q4). Nút *Cấp quỹ năm* trả về danh sách người còn thiếu và giao diện
   hiện cảnh báo.
4. Rà lại **lịch ngày lễ 2026** với quyết định nghỉ lễ chính thức — bộ seed dựng
   theo thông lệ, ngày Tết Âm có thể xê dịch.
