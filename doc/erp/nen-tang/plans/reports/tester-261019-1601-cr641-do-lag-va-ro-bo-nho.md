# CR-641 — đo lag + rò bộ nhớ của bộ thu hành vi (19/10/2026)

Môi trường: local, Vite DEV (React dev build), Chrome DevTools MCP, admin DEGO0001. Bộ thu bật.

## Phía server — POST /api/telemetry/ui-events
| Đo | Kết quả |
|---|---|
| 25 lô × 100 sự kiện, tuần tự | p50 17 ms · p95 49 ms · max 83 ms, 100% 200 |
| Giới hạn | 30 lô/phút/người (429 quá trần); giao diện thật gửi ~2 lô/phút (30 s/lần) |
| Tải ước tính 100 người | ~3 req/s, mỗi lô 1 lệnh ghi gộp |
Đã xóa 5.300 dòng đo khỏi `tab_ui_event` local.

## Phía trình duyệt — chi phí bộ thu (nạp thẳng module qua Vite)
| Đo | Kết quả |
|---|---|
| `enqueue` | 0,37 µs/lần (100.000 lần) — không JSON.stringify lúc thêm |
| Bộ đệm sau 100.000 lần thêm | 300 (đúng trần) |
| Đóng gói + gửi 300 sự kiện | 1,1 ms, 3 lô, 40,5 KB |
| Máy chủ trả 204 (tắt thu) | ngừng nhận, bộ đệm 0 |
⇒ không gây lag: chi phí nhỏ hơn 1 khung hình (16 ms) hàng trăm lần.

## Rò bộ nhớ
| Kịch bản | Heap sau GC | DOM | Detached | Đối tượng bộ thu |
|---|---|---|---|---|
| Mốc (sau khởi động) | 74,4 MB | 1.282 | 0 | — |
| +50 lần chuyển trang (5 màn × 10) | 83,1 MB | 1.282 | 0 | 1 bản mỗi loại |
| +50 lần nữa | 83,6 MB (+0,5) | 1.282 | 0 | 1 bản mỗi loại |
| Mở/đóng «Lập hợp đồng» ×20 | 96,6 → 97,6 MB | 1.013 | 0 | `finish` 2→2, không closure nào tăng ~1/lần |
⇒ tăng đợt đầu = cache TanStack Query, đợt sau phẳng → không rò.

Nhiễu chỉ có ở bản DEV (không phải lỗi, không có trên prod):
- `PerformanceMeasure` tăng ~2.400/lần chuyển trang = track «Components ⚛» của React 19.2 dev build (280.077/280.524 entry).
- `AXObject*` = cache trợ năng của Chrome do DevTools chụp cây a11y.
- Sau HMR, closure bộ thu xuất hiện 2 bản (module cũ còn giữ) — chỉ khi dev sửa mã nóng.

## Câu hỏi mở
- Chưa đo trên bản build production (`vite build` + preview); số dev đã đủ kết luận vì prod nhẹ hơn.
