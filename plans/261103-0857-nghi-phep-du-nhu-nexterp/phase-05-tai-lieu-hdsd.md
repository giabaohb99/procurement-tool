# Phase 05 — Tài liệu, HDSD, cẩm nang AI, RAG

## Việc
1. `doc/erp/hrm/02-nghi-phep.md`: §3 (menu thêm «Phân bổ chính sách», thẻ «Chính sách nghỉ phép»), §5 «Cấp phát quỹ»
   (thứ tự hạn mức mới), mục mới **§15 Chính sách + phân bổ (duoc-CR-717)** (bảng, luật tháng-ngày-15, tính lại, hàng loạt,
   quyền), §9 (không khóa mới — chính sách theo `leave_type`, phân bổ theo `leave_balance`), §10 (gạch dòng đã có),
   §13.7 (chỉ số nghỉ bù, ma trận, báo cáo khóa 30). Ghi rõ «Kỳ nghỉ phép: không làm (anh Được bỏ 03/11/2026)».
2. `.claude/rules/hr-leave.md`: khối «duoc-CR-717» — `ensure_balance` đi qua `policy_allocation`; không phân bổ = số cũ;
   tên `leave_policy.py` là của CR-713; `plan_change` dùng chung preview/ghi; ma trận phải đăng ký trước `/{bid}`. Bổ sung
   các ghi chú CR-715 còn treo ở `plans/261102-1652-nghi-phep-kieu-erpnext/reports/review-fixes.md` §Unresolved.
3. `doc/erp/nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md`: bảng §6 «Cập nhật» + Phụ lục A.3 (Leave Policy /
   Assignment / Control Panel → Đã có (duoc-CR-717); Leave Period → Không làm; báo cáo thứ ba → Đã có).
4. HDSD: `backend/scripts/seed_help_nghi_phep.py` (bài «Chính sách nghỉ phép», «Phân bổ chính sách / hàng loạt», «Xem quỹ
   theo nhân sự», «Cấp quỹ có lọc») · `backend/scripts/seed_help_bao_cao_nhan_su.py` (bài báo cáo khóa 30).
5. Cẩm nang AI `ai_skill/seed_handbook/40-nghi-phep.md` + tăng phiên bản ở `handbook_seed.py` + chạy `reindex_help_rag`
   (memory: xong tính năng thì cập nhật HDSD + RAG).
6. Đối chiếu ba nơi (màn hình · bài HDSD · tài liệu) trên `localhost:8083`.
(Change-log + sổ nhật ký task do người điều phối ghi, không thuộc phase này.)

## Xong khi
Ba nơi khớp nhau; `seed_help_*` chạy lại được không lỗi; RAG trả lời đúng câu «phân bổ chính sách nghỉ phép ở đâu».
