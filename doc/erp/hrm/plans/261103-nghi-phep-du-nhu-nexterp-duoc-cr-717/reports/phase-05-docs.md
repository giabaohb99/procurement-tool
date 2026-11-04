# Phase 05 — Tài liệu, HDSD, cẩm nang AI, công cụ AI (duoc-CR-717)

Status: DONE_WITH_CONCERNS. Không commit / push. Không đụng dev / prod.

## Đã làm
1. **HDSD** — `backend/scripts/seed_help_nghi_phep.py` (bản 7): 2 bài mới **Nhân sự — Chính sách nghỉ phép**, **Nhân sự — Phân bổ
   chính sách nghỉ phép cho từng người và hàng loạt**; bài Quỹ phép của Nhân sự viết lại phần đọc bảng (thẻ Theo dòng quỹ /
   Theo nhân sự, 5 cột hiện + cột ẩn sẵn), hộp Cấp quỹ có lọc, dòng **Chính sách đang áp**, ngoại lệ tính lại; thứ tự hạn mức mới
   ở bài Hiểu số ngày phép còn lại / Loại nghỉ / Phân quyền; thẻ gốc **Sáu mục**, Thiết lập **bốn thẻ**. Thêm `check_unique_titles`
   (slug trùng + tóm tắt > 255). `seed_help_bao_cao_nhan_su.py`: bài mới **Báo cáo Nhân sự — Xem ai đi làm vào ngày lễ, ngày nghỉ
   và ngày nghỉ bù được duyệt** (khóa 30, nhắc đăng nhập lại), cột **Nghỉ bù cộng thêm** ở bài Quỹ phép năm, dòng khóa 30 ở bài
   giao quyền, 15 → 16 báo cáo, `EXPECTED_ARTICLES` 21. Seed local chạy 2 lần sạch: cây Nghỉ phép 14 bài, Báo cáo Nhân sự 21
   bài, 0 liên kết chéo gãy, icon dùng bộ có sẵn của help-center.
   Nhãn đối chiếu bằng đọc mã màn + trình duyệt localhost:8083 (menu **Phân bổ chính sách**, nút **Phân bổ hàng loạt** / **Phân bổ**,
   lọc **Mọi chính sách** / **Mọi phân bổ** / **Mọi pháp nhân**, cột, **Kết thúc** / **Xóa** — khớp).
   **RAG reindex bỏ qua** (local tắt `AI_RAG_ENABLED`) — chạy trên dev lúc deploy.
2. **Tài liệu** — `doc/erp/hrm/02-nghi-phep.md` bản 1.9: §15 mới (15.1 mô hình · 15.2 API chính sách · 15.3 API phân bổ + chốt
   ghi, khóa REPEATABLE READ, hàng loạt không savepoint · 15.4 thứ tự / tháng-ngày-15 / phân bổ từ ngày vào làm áp cả năm / tính
   lại · 15.5 giao diện · 15.6 ma trận · 15.7 cấp quỹ có lọc · 15.8 báo cáo khóa 30 · 15.9 AI · 15.10 bài kiểm); sửa §3 (chín
   màn), §5 Cấp phát quỹ, §9, §10 (gạch dòng đã có + Kỳ nghỉ phép **Không làm**), §13.7. `doc/erp/nghien-cuu/erpnext/04-...md`:
   §6 + bảng cập nhật + Phụ lục A.3 (Policy / Assignment / Control Panel / 2 báo cáo → Đã có (duoc-CR-717); Leave Period → Không
   làm (anh Được bỏ 03/11/2026)). `.claude/rules/hr-leave.md`: khối CR-717 (ghi quỹ chỉ qua `ensure_balance` →
   `policy_allocation`; không phân bổ = số cũ; đọc có khóa; phạm vi employee read ∩ leave_balance write; D5; ma trận trước `/{bid}`;
   ReportKey 30; Leave Period không làm). Ghi chú treo của CR-715 (review-fixes §Unresolved) đã có sẵn trong khối CR-715.
3. **AI** — cẩm nang `40-nghi-phep.md`: mục Chính sách + phân bổ, Quỹ theo nhân sự + cấp quỹ có lọc, Báo cáo khóa 30
   (`report_summary` `report_key = holiday_work`), trường `policy` của tool, bảng khóa quyền, bảng từ. Xuất bản local
   `publish_handbook_update.py --only nghi-phep` → **phiên bản 7**; chạy lại = **đã mới nhất**.
   `assistant/tools/leave_tool.py` `my_leave_summary`: thêm `policy` (tên, mã, từ, đến của phân bổ phủ mốc = hôm nay kẹp vào năm
   hỏi) + `policy_name` / `policy_annual_days` mỗi dòng quỹ + mục glossary; chỉ đọc qua `policy_allocation.load_assignments` /
   `load_lines`, ≤ 3 truy vấn. Bài kiểm mới `test/backend/test_assistant_nghi_phep_chinh_sach_cr717.py` (4 bài).
4. **Sổ** — `change-log.md` hàng duoc-CR-717 → mô tả đủ + **Xong — erp-v2** (kèm sửa `shared/ui/dialog.tsx`). `nhat-ky-task.md` mục
   **## duoc-CR-717 | …** cuối sổ (Bối cảnh / Đã làm / Kết quả / Còn lại, `Mã nguồn:` cuối). Bóc sổ offline: 687 mục, không trùng
   khóa. **Chưa chạy `sync_task_journal.py`**: local không có tài khoản `WORK_SYNC_*` (không tự gõ mật khẩu).

## Kiểm
- 6 tệp CR-717: **182 xanh**. `test_assistant_nghi_phep_erpnext_cr715`, `test_assistant_leave_tool`, `test_assistant_pham_vi_doc`,
  `test_nghi_nhieu_khoang_ngay_cr683`, `test_agent_hub_cau_hinh_mcp_cr216`, `test_pham_vi_luat_bat_bien`, `test_pham_vi_duong_vong`,
  6 tệp đọc cẩm nang (cr220/228/183/192/693/draft): xanh hết.

## Concerns
- **Dữ liệu mồ côi trên DB local**: 22 dòng `tab_leave_policy_assignment` trỏ tới 12 nhân sự + 12 chính sách (id 3–14) KHÔNG còn tồn
  tại → màn Phân bổ hiện **#1495** / **#11** thay tên. Có lẽ do lượt thử của agent khác ghi thẳng MySQL rồi dọn thiếu. Không xóa (không
  phải khu của em). Gợi ý: người chạy thử dọn bằng SQLAlchemy; cân nhắc chặn xóa cứng nhân sự / chính sách còn phân bổ.
- Danh sách phân bổ có cột **ID** tự chèn (idColumn mặc định của DataTable) — bài HDSD không nhắc; lỗi nhỏ cho giao-dien-v2 nếu muốn tắt.
- `leave_tool.py` 326 dòng (> 200, trước đó 284) — chưa tách.

## Câu hỏi còn mở
- Ai dọn 22 dòng phân bổ mồ côi trên local?
