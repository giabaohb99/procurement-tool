# Phase 06 — Tài liệu, HDSD, RAG, sổ, triển khai

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P2 · 3 giờ · sau 05. Giao `tai-lieu-kiem-thu` cho HDSD + soát màn.

## Tài liệu (cùng commit với mã của phase tương ứng)
- `doc/erp/thu-mua/chuc-nang/01-yeu-cau-chuc-nang.md`: thêm `CN-THUMUA-NN` (Tác động giá, Bảng giá VTBB, Báo giá, Ngưỡng
  giá, Định mức bao bì, Nhập định mức).
- `doc/erp/thu-mua/chuc-nang/02-yeu-cau-phi-chuc-nang.md`: `PCN` hiệu năng (<= 7 truy vấn, mục tiêu ms), dữ liệu nhạy
  cảm (khóa `packaging_cost` trong `SENSITIVE_PROCUREMENT_ENTITIES`), trần đầu vào (500 mã, 20.000 dòng nhập).
- Tạo `doc/erp/thu-mua/chuc-nang/21-tac-dong-gia-bao-bi.md`: luật nghiệp vụ (công thức, cũ/mới, ngưỡng, nguồn sổ giá).
- `doc/erp/thu-mua/tai-lieu-ky-thuat/api.md`: dựng lại bảng mục 1 bằng `scripts/dung_bang_api.py` (không sửa tay cột Mục
  đích / Quyền), ghi tay cột Phạm vi + Ai gọi.
- Tạo `doc/erp/thu-mua/tai-lieu-ky-thuat/so-gia-san-pham.md`: bảng, luật đồng bộ, danh sách mốc hook, script hòa giải,
  bẫy (tỉ giá, nạp lại legacy). `mo-hinh-du-lieu-san-pham.md` §11 chỉ thêm **một dòng liên kết** tới tệp này (một sự thật một chỗ).
- `doc/erp/thu-mua/README.md`: thêm dòng mục lục cho tệp mới + kế hoạch. Chạy `KIEM_TAI_LIEU_ROOT=$PWD python backend/scripts/kiem_tai_lieu.py`.

## HDSD + RAG
- `backend/scripts/seed_help_gia_bao_bi.py`: bài "Tác động giá bao bì" (chọn mã, giá giả định, đọc KPI, ghi chú cảnh báo,
  báo giá, ngưỡng, nhập định mức). Có `--dry-run` thật (grep trước khi chạy — một số `seed_help_*` bỏ qua cờ).
- Nâng phiên bản skill cẩm nang thu mua (nếu có) ở `backend/app/modules/ai_skill/seed_handbook/`, chạy
  `backend/scripts/reindex_help_rag.py`.

## Sổ
- Giữ số CR ngay (dải chung — push ngay để không trùng), dòng ở change-log + mục `nhat-ky-task.md` câu tiếng Việt trọn ý,
  dòng cuối `Mã nguồn:` / `Commit:`; mã mục sổ duy nhất (lượt sau thêm hậu tố).

## Triển khai (dev rồi prod khi được lệnh)
1. Migration tự chạy lúc khởi động api.
2. `python scripts/backfill_product_price_ledger.py --dry-run` → đọc số đếm → `--apply` → `--check` exit 0.
3. Nhập `DATA_CHAI.xlsx` qua nút Nhập từ Excel (chạy thử, xác nhận).
4. Prod: `seed_prod.py` không ghi đè quyền → tick tay `packaging_cost` cho vai trò được chốt (Q4); ghi việc tick tay vào sổ.

## Kiểm xong
Cổng kiểm tài liệu exit 0; bài HDSD hiện ở Trung tâm trợ giúp; Trợ lý trả lời được "giá bao bì tăng ảnh hưởng sản phẩm nào".
