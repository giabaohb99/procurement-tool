# Phase 05 — Tài liệu, bài kiểm, phát hành

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | planner | Nháp | duoc-CR-784, bao-CR-789 |
| 2 | 26/11/2026 | tài liệu và kiểm thử | **Tài liệu xong trên nhánh `duoc-cr784-p05-tai-lieu`** (chưa commit); seed HDSD + xuất bản cẩm nang + nạp lại chỉ mục chờ chạy trên dev; phát hành prod chờ duyệt | duoc-CR-784, bao-CR-789 |

Ưu tiên P2 · 2 giờ · cần 02–04, 06, 07 (đều đã lên dev 25/11/2026).

## Ma trận kiểm
| Tầng | Kiểm gì | Lệnh | Kết quả |
|---|---|---|---|
| Đơn vị + tích hợp (pytest, SQLite) | luật sổ giá mới, nguồn báo giá, hàm chuyển dữ liệu của migration, đếm truy vấn, đổi tên `fg_*`, xóa theo lô | `docker compose exec -T api python -m pytest test/backend -k cr784 -q --timeout=120` (chia nhóm nếu nặng) | xanh ở từng phase (ghi ở mục *Kết quả* của phase 02, 03, 04; phase 06 / 07 thêm `test_doi_ten_fg_cr784.py`, `test_xoa_theo_lo_nhap_cr784.py`) |
| Migration thật (MySQL) | `upgrade` → `downgrade -1` → `upgrade` trên bản sao DB dev nạp vào local | `alembic upgrade head` / `downgrade -1`; so số dòng, tổng `price`, tập khóa trước / sau | đã chạy cho `bompart784`, `srcmerge784`, `quotesrc784`, `cleanup784` (phase 01–04); `fgname784`, `bombatch784` chạy thật trên dev 25/11/2026 |
| Cổng | ruff `app`, `kiem_tai_lieu.py` (kèm `KIEM_TAI_LIEU_ROOT=$PWD`), typecheck + lint v2, vitest `src/modules/procurement` | như CLAUDE.md | cổng tài liệu 26/11/2026: không lỗi mới từ tệp của phase này (4 lỗi mới sẵn có ở `doc/erp/san-xuat/nghien-cuu`, không thuộc cụm); bài kiểm cẩm nang (`test_cam_nang_van_phong_cr235`, `test_tro_ly_doc_kho_skill_cr220`, `test_pham_vi_bo_may_duyet_xuyen_suot`) 60 qua |
| Tay (dev) | Lịch sử mua hàng v1 (devthumua) + v2 (deverp): dấu ĐMH đang mở, cột Nguồn; báo giá form + Excel, báo trùng; nút Xóa dữ liệu của lô này | soát bằng skill `soat-man-dev` | chưa soát lại sau phase 06 / 07 — làm cùng lúc mở bài HDSD trên devhelp |

## Tài liệu (26/11/2026)
- [x] Chức năng 21 bản 1.1: menu trong nhóm Mua hàng, ghi chú đơn vị, cột Nguồn của Lịch sử mua hàng (màn hình chỉ bày số ĐMH, Excel ghi chữ), nguồn và khóa duy nhất báo giá đã lên dev, mục 9 mới *Xóa dữ liệu theo lô nhập*, tên bài HDSD mới.
- [x] Tài liệu kỹ thuật mới [mo-hinh-du-lieu-gia-nvl-san-xuat.md](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-gia-nvl-san-xuat.md): bốn bảng, cột, khóa, chỉ mục, chuỗi migration (một chỗ cho cấu trúc; luật nguồn giá giữ ở chức năng 21 mục 1).
- [x] `api.md`: thêm hai dòng `/api/imports/{bid}/purge-preview`, `/purge` vào bảng mục 1; bỏ chữ *ngưỡng* ở dòng `price-list`; mục 2.1 hợp đồng hiện hành của cụm (tham số `fg_*`, `line_stage` / `is_open`, nguồn báo giá, không còn ngưỡng), mục 3 lỗi riêng (409 báo giá trùng, 400 / 403 / 404 xóa theo lô). Không chạy `dung_bang_api.py` ghi đè: chạy thử 26/11/2026 bằng ảnh `procurement-tool-api:latest` cho bảng lỗi (đường `/history`, `/fg-options`... mất tiền tố `/api/packaging-cost`, xóa chữ ghi tay của dòng `impact`), nên sửa tay đúng hai dòng mới và đã trả lại tệp.
- [x] `01-yeu-cau-chuc-nang.md` bản 0.5 (CN-TM-26, 27, 29 cập nhật; thêm CN-TM-31 Xóa theo lô), `02-yeu-cau-phi-chuc-nang.md` bản 0.3 (PCN-TM-13..16), README phân hệ.
- [x] `doc/agent-hub/06-cong-mcp.md` §3.7c và `doc/erp/tro-ly-ai/tai-lieu-ky-thuat/02-danh-sach-api-tool.md`: ghi đổi hợp đồng 25/11 (`fg_codes`, `fg_code` / `fg_name`, bỏ `floor_price` / `ceiling_price`).
- [x] Ghi chú đầu kế hoạch 261120 (`plan.md`, phase 01, phase 02): luật "nguồn 1 chỉ chèn / nguồn 2 xóa khi vào lịch sử" và bảng ngưỡng đã được thay bằng kế hoạch này; `hh_*` đã đổi thành `fg_*`.
- [x] Sổ: mục ngày 26/11/2026 dưới `duoc-CR-784` ở `nhat-ky-task.md`; hàng `duoc-CR-784-tac-dong-gia-bao-bi` ở `change-log.md` ghi thêm đợt tối ưu.

## HDSD và cẩm nang (26/11/2026)
- [x] `backend/scripts/seed_help_gia_bao_bi_cr784.py`: 10 nút (thẻ + 9 bài), thêm bài *Giá NVL sản xuất — Xóa dữ liệu đã nhập nhầm theo lô nhập Excel*; sửa đường menu (nhóm Mua hàng), bảng nguồn sổ giá (một dòng mỗi dòng ĐMH, đang mở rồi chốt), ghi chú đơn vị, VAT Misa trống, cột Nguồn của Lịch sử, báo giá trùng + cột Nguồn, thay mọi câu "chưa hoàn tác được" bằng xóa theo lô, phần quản trị hai đường nạp Misa. Slug các bài cũ giữ nguyên. Đã kiểm ngoài DB: tóm tắt <= 255 ký tự, không lọt chữ ngưỡng, mọi liên kết chéo trỏ đúng bài trong cây, thẻ HTML cân, `py_compile` qua.
- [x] Cẩm nang `backend/app/modules/ai_skill/seed_handbook/10-quy-trinh-thu-mua.md` mục *Giá nguyên vật liệu sản xuất* (đánh dấu *cập nhật 26/11/2026*): menu, nguồn giá, Lần, Giá trị mua, Tổng hợp lọc nâng cao, báo giá một khóa + cột Nguồn, không còn ngưỡng, xóa theo lô, tham số `fg_codes` của công cụ.
- [ ] Trên dev (chờ chạy sau commit): seed HDSD → xuất bản cẩm nang → nạp lại chỉ mục, rồi mở devhelp soát 10 nút.

```bash
# trên VPS dev, container api của dev (tên theo skill viet-hdsd: procurement-tool-dev-api-1)
docker exec procurement-tool-dev-api-1 python scripts/seed_help_gia_bao_bi_cr784.py --dry-run
docker exec procurement-tool-dev-api-1 python scripts/seed_help_gia_bao_bi_cr784.py
docker exec procurement-tool-dev-api-1 python scripts/publish_handbook_update.py --only quy-trinh-thu-mua --dry-run
docker exec procurement-tool-dev-api-1 python scripts/publish_handbook_update.py --only quy-trinh-thu-mua --note "Cập nhật mục Giá nguyên vật liệu sản xuất theo đợt tối ưu 25/11/2026 (duoc-CR-784)"
docker exec procurement-tool-dev-api-1 python scripts/reindex_help_rag.py --purge-orphans
```

Seed XÓA cả cây có tiêu đề gốc *Hướng dẫn sử dụng Giá nguyên vật liệu sản xuất* (và cây tên cũ *Hướng dẫn sử dụng Giá bao bì* nếu còn)
rồi dựng lại đúng vị trí cũ, nên id bài đổi — phải chạy `reindex_help_rag.py --purge-orphans` ngay sau để dọn đoạn của bài cũ.

## Phát hành prod (danh sách việc, chờ duyệt)
Chưa làm gì trên prod. Prod (`main`) chưa có bảng nào của cụm (có `mrg761a`, chưa có `pkgcost784`), nên không có bước chuyển dữ liệu:
mọi migration chạy trên bảng rỗng.

1. **Điều kiện trước.** Chủ dự án gật phát hành trong phiên. Thống nhất với người rà bao-CR-789: chuỗi CR-784 lên prod MỘT lần cùng
   sửa savepoint của bao-CR-789 (`purchase_history/service.py` gọi `record_history_row` trong savepoint — commit `e216d7ad9`); không
   lên lẻ phase. Quyết giao diện cũ: cụm có ở `frontend/` là ngoại lệ D-026, cần chốt có đưa lên `thumua.degoholding.vn` hay chỉ
   `erp.degoholding.vn`.
2. **Chuỗi migration** (một đầu, nối sau `mrg761a`): `pkgcost784` → `misa784` → `amt784` → `ppld784` → `bompart784` → `srcmerge784` →
   `quotesrc784` → `cleanup784` → `fgname784` → `bombatch784`. Trước khi gộp: `alembic heads` trên nhánh gộp chỉ ra một đầu.
3. **Sao lưu có kiểm** DB prod theo quy trình B ở `doc/tai-lieu-ky-thuat/van-hanh/quy-trinh-nhanh-va-deploy.md` §A.2 (diễn tập trên bản
   sao, sao lưu có kiểm, ngưỡng quay đầu).
4. **Câu đọc kiểm trước (chỉ đọc) trên prod:** `SELECT version_num FROM alembic_version` (phải là đầu của `main`, chuỗi có `mrg761a`);
   `SHOW TABLES LIKE 'tab_product_price%'` và `SHOW TABLES LIKE 'tab_packaging_bom%'` (phải rỗng). Các câu kiểm riêng từng phase chỉ cần
   khi bảng đã có dữ liệu — trên prod tất cả ra 0, chạy lại trên bản sao diễn tập để chắc:
   - `srcmerge784`: câu va chạm nguồn 1 / 2 và câu nguồn 1 sai dạng ở phase 02 mục *Việc phải làm trên dev* (kỳ vọng 0);
   - `quotesrc784`: ba câu ở phase 03 mục *Câu đọc kiểm trước khi lên dev* (nhóm trùng khóa phải 0, có thì migration DỪNG);
   - `cleanup784`: ba câu ở phase 04 mục *Câu đọc kiểm TRƯỚC khi lên dev* (số dòng ngưỡng phải 0);
   - `bombatch784`: không có lô module 4 trên prod nên không đánh dấu dòng nào (log `[bombatch784] ...`).
5. **Diễn tập** trên bản sao DB prod nạp vào local: `alembic upgrade head` → `alembic downgrade mrg761a` → `alembic upgrade head` sạch;
   đếm bảng mới, `SHOW CREATE TABLE` bốn bảng khớp [mô hình dữ liệu](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-gia-nvl-san-xuat.md).
6. **Deploy** bắt buộc `-f docker-compose.production.yml`; `start.prod.sh` tự chạy `alembic upgrade head` rồi `seed_prod`.
7. **Sau migration:** `docker compose exec -T api python -m scripts.backfill_product_price_ledger` (chạy thử, xem số) → `--apply` →
   `--check` phải thoát 0 (sổ giá dựng từ lịch sử mua + dòng ĐMH đã duyệt).
8. **Dữ liệu cụm:** sổ Misa nạp bằng nút *Nạp sổ Misa* (module 6) để còn xóa được theo lô — không dùng script HTML trên prod trừ khi
   chủ dự án chốt; định mức nạp tệp `DATA_CHAI.xlsx` thật bằng *Nhập từ Excel* (module 4). Không chép dữ liệu thử của dev (lô 98).
9. **Quyền:** `seed_prod` không ghi đè phân quyền đã sửa; kiểm admin thấy cụm, giao khóa *Giá bao bì* (`packaging_cost`) cho vai trò
   Thu mua cần dùng bằng tay ở màn Vai trò & quyền. Nhóm công cụ MCP `packaging` tắt mặc định, bật ở G7 khi cần.
10. **HDSD + cẩm nang + chỉ mục trên prod** (theo đợt đồng bộ Help Center của điều phối, không chạy lẻ): `seed_help_gia_bao_bi_cr784.py`,
    `publish_handbook_update.py --only quy-trinh-thu-mua --note "... (duoc-CR-784)"`, `reindex_help_rag.py --purge-orphans`.
11. **Giao diện cũ là ứng dụng cài được (PWA):** sau khi dựng lại `frontend/`, người dùng devthumua / thumua phải bấm *Tải lại* ở hộp
    *Đã có phiên bản mới* (hoặc đóng hết thẻ) mới thấy menu và nút mới; báo trước cho Thu mua.
12. **Kiểm sau phát hành:** mở sáu màn ở cả hai giao diện, tạo một báo giá tay rồi thử tạo trùng (phải báo 409), mở trang một lô chạy
    thử (không có nút xóa), gọi `/api/product-price-limits` (404).
13. **Quay lui:** `alembic downgrade mrg761a` (bỏ hẳn mọi bảng của cụm, prod chưa có dữ liệu nào trước đó) + revert commit gộp; sổ giá
    là dữ liệu dẫn xuất, lên lại thì `backfill --apply`.

## Việc cần làm
- [x] Ma trận kiểm xanh theo từng phase (02, 03, 04, 06, 07)
- [x] Tài liệu kỹ thuật + api.md + sổ (26/11/2026)
- [x] HDSD + cẩm nang sửa chữ (26/11/2026)
- [ ] Commit nhánh `duoc-cr784-p05-tai-lieu`, chạy seed + xuất bản cẩm nang + nạp lại chỉ mục trên dev, soát devhelp và màn dev
- [ ] Báo bao-CR-789 thứ tự migration và quyết lên prod một lần
- [ ] Phát hành prod theo danh sách trên (chờ duyệt)
