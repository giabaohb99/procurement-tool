# Phase 06 — Tài liệu, HDSD, cẩm nang trợ lý, RAG

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | tai-lieu-kiem-thu | Nháp | duoc-CR-755 |

## Context links
- [plan.md](plan.md) và năm phase trước (mục Key insights, Security).
- `doc/erp/hrm/01-ho-so-nhan-su.md` §4 (dòng ~145), §7.10 (~615), §7.11 (~661, dòng ~687 lệch mã loại sự kiện), §7.12 sơ đồ.
- `.claude/rules/hr-employee-profile.md` mục QTCT luật 1, 5 và Nhập Excel luật 12 (đang nói `set_extra_departments`,
  `tab_employee_department`, `_depts` — hết đúng sau CR này).
- `backend/scripts/seed_help_nhan_su.py`; cẩm nang trợ lý ở `backend/app/modules/ai_skill/seed_handbook/` (nâng phiên bản);
  `reindex_help_rag`. Memory: `seed_help_*` có thể không có `--dry-run` — grep `dry` trước khi chạy.
- Sổ: `doc/tai-lieu-ky-thuat/change-log.md` (dòng duoc-CR-755 đã đặt chỗ), `doc/tai-lieu-ky-thuat/nhat-ky-task.md`.

## Overview
P3. Rút quyết định + bẫy vào tài liệu phân hệ và luật cho người viết mã; viết bài HDSD tab Kiêm nhiệm; cập nhật cẩm nang trợ
lý Nhân sự; nạp lại RAG; ghi sổ.

## Requirements
- `01-ho-so-nhan-su.md`: mục mới §7.18 **Kiêm nhiệm khác công ty (duoc-CR-755)** — bảng dữ liệu, luật hiệu lực, phạm vi theo
  cặp (đường nào thấy / không thấy), ai được gán, đổi pháp nhân, Áp QTCT, hiển thị phòng B, báo cáo không đếm trùng, sáu
  quyết định Q1–Q6 đã chốt 12/11; sửa §4 + §7.10 + §7.11 cho khớp (kể cả dòng 687 lệch mã).
- `doc/erp/hrm/README.md` thêm dòng kế hoạch; `doc/erp/hrm` tài liệu bắt buộc (`chuc-nang/01..`, `02..`,
  `tai-lieu-ky-thuat/api.md`) — nếu đã có thì thêm CN / PCN / đường API mới; nếu chưa có, KHÔNG dựng ở CR này, ghi vào câu hỏi.
  Bảng API dựng bằng `scripts/dung_bang_api.py`.
- `.claude/rules/hr-employee-profile.md`: mục mới **KIÊM NHIỆM KHÁC CÔNG TY** (bảng mới là nguồn duy nhất; `dept_ids` chỉ cùng
  công ty; cặp khác công ty chỉ vào nhánh có ràng công ty; không cộng vào ACL; L2 theo cặp; không xóa-chèn; đổi pháp nhân chỉ
  kết thúc dòng công ty cũ); sửa luật 1, 5 QTCT và luật 12 Nhập Excel.
- HDSD (`seed_help_nhan_su.py`): bài **Kiêm nhiệm** — thêm dòng, công tắc phạm vi, tự hết hạn, tệp QĐ, đổi pháp nhân, trưởng
  phòng B thấy ở đâu. Không markdown trong chữ trơn, không ngoặc kép góc, không emoji.
- Cẩm nang trợ lý Nhân sự: một đoạn kiêm nhiệm + trường `concurrent_roles`; nâng phiên bản skill.
- RAG: `reindex_help_rag` (nếu hết hạn mức Gemini thì ghi rõ trạng thái chờ ở sổ).
- Sổ: cập nhật dòng change-log (trạng thái Xong — erp-v2), một mục `nhat-ky-task.md` câu tiếng Việt trọn vẹn, mã mục duy nhất.
- Đổi `plan.md` sang *Trạng thái kế hoạch: xong*.

## Related code files
Sửa (phase sở hữu): `doc/erp/hrm/01-ho-so-nhan-su.md`, `doc/erp/hrm/README.md`, tài liệu bắt buộc của `doc/erp/hrm` nếu có,
`.claude/rules/hr-employee-profile.md`, `backend/scripts/seed_help_nhan_su.py`, tệp cẩm nang Nhân sự trong
`backend/app/modules/ai_skill/seed_handbook/`, `doc/tai-lieu-ky-thuat/change-log.md`, `doc/tai-lieu-ky-thuat/nhat-ky-task.md`,
`plan.md` của thư mục này.

## Implementation steps
1. Đọc diff thật của phase 01–05 (không chép từ kế hoạch nếu mã đã khác).
2. Viết tài liệu + luật; chạy `KIEM_TAI_LIEU_ROOT=$PWD python backend/scripts/kiem_tai_lieu.py` (0 lỗi mới).
3. HDSD + cẩm nang; chạy seed trên local; soát màn bằng trình duyệt (khổ máy tính + emulate điện thoại).
4. Nạp lại RAG; ghi sổ.

## Todo
- [x] `01-ho-so-nhan-su.md` §7.18 + sửa §4, §7.10, §7.11 (+ §7.12 khối người kiêm nhiệm)
- [x] Luật `hr-employee-profile.md`
- [x] README phân hệ, bảng API (`tai-lieu-ky-thuat/api.md` dựng mới cả phân hệ + `chuc-nang/01`, `02` dạng Nháp để cổng kiểm
  tài liệu không báo lỗi mới khi commit); `doc/agent-hub/06-cong-mcp.md` §3.6
- [x] HDSD (seed local hai lần) + cẩm nang (xuất bản local phiên bản 8)
- [ ] RAG `reindex_help_rag` (điều phối làm)
- [ ] Change-log + nhật ký task; plan.md xong (điều phối làm)

## Success criteria
- `kiem_tai_lieu.py` không lỗi mới; `test_kiem_tai_lieu_cr712.py` xanh.
- Bài HDSD hiện ở Trung tâm trợ giúp local; trợ lý trả lời đúng câu *Kiêm nhiệm ở công ty khác có thấy dữ liệu công ty đó
  không?* (đúng cặp, chỉ khi bật công tắc).
- Ba nơi khớp nhau: màn hình, bài HDSD, tài liệu.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Seed HDSD xóa dựng lại cây thật | Trung × Trung | grep `dry` trước, chạy local trước |
| Tài liệu lệch mã vì phase sửa sau review | Trung × Thấp | Viết từ diff cuối, phase này chạy sau cùng |

## Security
Không đưa dữ liệu thật (tên, mã nhân sự) vào ví dụ HDSD.

## Next steps
Gom đợt deploy theo quy trình chung (việc duoc-CR chỉ cần lên erp-v2).
