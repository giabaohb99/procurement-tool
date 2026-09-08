# P-03 — Ngày công và sổ quỹ ✅ XONG (CR-259)

## Đã làm

| Tệp | Việc |
|---|---|
| `leave/workday_service.py` | Đếm ngày nghỉ, đã trừ T7/CN + `tab_holiday`. Nơi DUY NHẤT tính. |
| `leave/balance_service.py` | Thâm niên · cấp phát · `reserve` / `consume` / `release` / `refund_used` · `check_enough`. |
| `test/backend/test_nghi_phep_quy_va_ngay_cong.py` | 30 bài. |

## Quyết định đáng ghi

- **Quy ước hai ô buổi giữ y hệt `document/type_metadata.suggested_days()`**:
  `morning` và `afternoon` đều là **0.5** ở cả hai đầu. Đổi ở đây thôi thì cùng
  một tờ đơn ra hai con số khác nhau tùy nhập qua màn Nghỉ phép hay qua giấy GNP.
- **Ngày lễ lặp hằng năm khớp theo ngày/tháng**, bất kể năm lưu trong bảng. Tết Âm
  và Giỗ Tổ **không** lặp được — trôi theo lịch âm.
- **Bậc thâm niên lấy bậc CAO NHẤT khớp được, không cộng dồn.** Cộng dồn thì mỗi
  lần thêm một bậc là mọi người thâm niên cao tự nhiên được thêm ngày.
- **`release` kẹp ở 0.** `pending_days` âm nghĩa là quỹ tự phình ra, và nó phình
  lặng lẽ.
- **`check_enough(..., exclude_days=)`** — bỏ phần giữ chỗ của chính tờ đơn đang
  sửa ra. Thiếu tham số này thì sửa đơn từ 3 ngày xuống 2 ngày cũng báo hết phép.
- Q1 (cấp một lần đầu năm hay cộng dần theo tháng) nằm gọn trong `ensure_balance`,
  đổi sau được.

## Nghiệm thu

30 bài xanh, gồm các ca biên: khoảng ngược trả `0.0` chứ không nổ; ngày lễ của
pháp nhân khác không dính tới mình; `exclude_holiday=False` đếm cả cuối tuần.
