# Tổng hợp ép tải đợt duoc-CR-661…670 (duoc-CR-671) — 22/10/2026

## Bài kiểm mới (đều xanh, 0 xfail)
| Tệp | Bài | Phủ |
|---|---|---|
| test_stress_nghi_phep_dinh_kem_ket_so_cr661_664.py | 19 | CR-661 đính kèm bắt buộc; CR-664 kết sổ 500 NV, số âm/0/lớn, phạm vi, số truy vấn cố định |
| test_stress_chuong_duyet_bao_cao_phong_cr662_663.py | 18 | CR-662 200 user quyền trộn, inactive, fallback admin, YCTT, new_rules=False, truy vấn 20=200; CR-663 1000 dòng, đổi tên phòng, id=0, Str255 → 422 |
| test_stress_viec_treo_cong_viec_cr665_667.py | 11 | CR-665 250 việc treo, MAX_ROWS; CR-667 sửa bình luận 100 lần, quá 5000 ký tự, thùng rác 50 vòng |
| test_stress_cong_viec_to_chuc_cr666_cr669.py | 12 | CR-666 50+50 người, không spam, cựu thành viên; CR-669 2000→3000 người truy vấn cố định, vòng quản lý/phòng, chuỗi 50 tầng, mồ côi |
| org-chart-tree-stress.test.ts (vitest) | 5 | 2000 người ngẫu nhiên có vòng < 1s, chuỗi 2000 cấp, vòng 2000 nút cắt đúng 1 cạnh |
| test_nhat_ky_khong_chan_vong_su_kien.py | 3 | canh bản sửa middleware (gỡ bản sửa → đỏ cả 3) |

Sửa tay sau agent: bỏ 1 xfail vô nghĩa (SQLite không ép VARCHAR) → kiểm schema; 8 bài CR-669 bị gắn xfail sai lý do (fixture cấp quyền thiếu `read=True` → 403) → sửa fixture, bỏ xfail; bài «truy vấn cố định» chỉ khẳng định `> 0` → so 2000 với 3000 người.

## Đo tải HTTP (local, 1 tiến trình uvicorn --reload, sau bản sửa)
| Đường | x1 p50 | x10 p95 | x50 p95 | lỗi x50 |
|---|---|---|---|---|
| leave-balances/close-year/review | 7 ms | 54 ms | 22,2 s | 0/150 |
| employees/{id}/pending-work | 29 ms | 440 ms | 846 ms | 0/150 |
| org-chart | 29 ms | 370 ms | 3,0 s | 0/150 |
| work/lists/1/trash | 18 ms | 209 ms | 12,4 s | 0/150 |
| reports/procurement/summary | 28 ms | 805 ms | 2,8 s | 0/150 |

p95 nhiều giây ở x50 = chờ bể kết nối (F3), không phải truy vấn chậm. Báo «404 pending-work» của agent = gọi id nhân sự không có (17), không phải lỗi.

## Phát hiện
- **F1 — NẶNG, có từ trước, ĐÃ SỬA.** `core/request_middleware.py`: `_write`, `_touch`, `flush_changes` mở `SessionLocal()` đồng bộ trong `dispatch` async → bể đầy thì vòng sự kiện chờ kết nối, kết nối chỉ trả khi vòng chạy tiếp → khóa chết (py-spy: MainThread kẹt ở `_write` → `pool._do_get`; MySQL 25 kết nối «Sleep» giữ giao dịch). Repro 60 đồng thời: trước 52/120 đạt, max 90 s; sau 120/120, max 2,8 s. Sửa: `await run_in_threadpool(...)`.
- **F2 — VỪA, có từ trước, ĐÃ SỬA.** 15 script `seed_help_*` dựng lại cây bằng SQL → đoạn vector của bài cũ ở lại (28 nguồn mồ côi sau 2 lần chạy), `search_docs` vẫn trích. Thêm `indexer.orphan_source_refs` + `reindex_help_rag.py --purge-orphans`; local còn 0 mồ côi, 103/103 bài.
- **F3 — NẶNG khi dồn tải, có từ trước, ĐÃ SỬA (hướng a).** 150 lượt dồn 1 tiến trình: 277/300 hết giờ chờ. py-spy: 37/40 luồng anyio chờ kết nối ở `auth.get_current_user`; 25 kết nối nằm ở lượt gọi đã qua `get_current_user`, đang chờ luồng cho `require`/endpoint. 40 luồng > 25 kết nối (10+15) ⇒ giữ chỗ của nhau, mỗi 30 s nổ `QueuePool TimeoutError`. Sửa: `core/concurrency_gate.py` (≤ 20 lượt /api/tiến trình, xếp hàng, 30 s → 503 `server_busy`). Sau sửa 150 đồng thời: org-chart 300/300 max 2,6 s; báo cáo mua hàng 300/300 max 4,7 s.
- Không phát hiện lỗi nào trong mã của CR-661…670.

## Seed chạy lại
5 script × 2 lần: 103 bài, 0 trùng (parent_id+title); script Thu mua giữ id. Không thử 2 bản Thu mua song song (bỏ qua — 2 lượt tuần tự đủ chứng minh idempotent; song song có thể trùng vì không có UNIQUE, rủi ro thấp vì chạy tay).

## Ghi chú ngoài phạm vi
- 4 bài đỏ khi chạy 82 tệp dùng `app.main`: `can_import NOT NULL` (CR-660 chưa commit — model thêm cột, migration test chèn SQL thô; cần `server_default`), đếm công cụ trợ lý 8≠9, mã `UI_ACTION` lệch TS/Python — không dính bản sửa này.
