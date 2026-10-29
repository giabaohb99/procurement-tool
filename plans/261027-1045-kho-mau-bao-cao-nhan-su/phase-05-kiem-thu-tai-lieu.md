# Phase 05 — Kiểm thử chéo, rà mã, HDSD + RAG, tài liệu

**Trạng thái:** pending · **Chủ:** điều phối · **Phụ thuộc:** 02, 03, 04

## Việc
1. Chạy bài kiểm backend của phần vừa sửa + `test_pham_vi_luat_bat_bien.py` + `test_phan_quyen_bao_cao_gac_duong.py`; cổng frontend (typecheck, lint, vitest `src/modules/report`).
2. Rà mã độc lập (agent rà mã): phạm vi dữ liệu, rò trường nhạy cảm, số truy vấn, route bị nuốt.
3. Mở thử trên local (cổng 8083) 5 báo cáo Nhân sự: lọc phòng ban, ngăn danh sách, 2 trang mới.
4. Bài HDSD trên Trung tâm trợ giúp cho 2 báo cáo mới + phần lọc / danh sách; nạp lại chỉ mục RAG.
5. Tài liệu: `doc/erp/hrm/05-bao-cao-nhan-su.md` (B1, E1 → đã có; A1/C1/C2 gạch các mục đã bù), `doc/erp/hrm/README.md`, `doc/erp/00-ke-hoach-theo-module.md` (HR1-6 xong), `change-log.md` dòng duoc-CR-686, sổ nhật ký task.
6. Nhắc khi deploy: báo cáo 17, 18 mặc định chỉ admin — giao cho trưởng phòng Nhân sự / Ban Giám đốc ở tab «Báo cáo».
