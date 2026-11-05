# Phase 06 — Tài liệu, HDSD, cẩm nang AI (duoc-CR-719)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | tai-lieu-kiem-thu | Hiệu lực | duoc-CR-719 |

Trạng thái: xong, chưa commit. Không sửa `frontend-v2/src` hay mã `backend/app` (trừ tệp md cẩm nang).

## Tệp
Sửa: `backend/scripts/seed_help_nghi_phep.py` (bản 8) · `backend/app/modules/ai_skill/seed_handbook/40-nghi-phep.md` ·
`doc/erp/hrm/02-nghi-phep.md` (bản 2.0, §16 mới; §3 · §5 · §9 · §10 · §11.1) · `doc/erp/hrm/README.md` ·
`doc/erp/thu-mua/chuc-nang/14-yeu-cau-thanh-toan.md` (§4 nguồn thứ tư) · `doc/erp/thu-mua/tai-lieu-ky-thuat/api.md` (§5) ·
`doc/erp/nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md` (dòng 179, 376) · `.claude/rules/hr-leave.md` (khối CR-719 +
2 đường `paths`) · `doc/tai-lieu-ky-thuat/quy-dinh/README.md` (dòng hr-leave) · `doc/tai-lieu-ky-thuat/change-log.md` (dòng
duoc-CR-719 → Xong — erp-v2) · `doc/tai-lieu-ky-thuat/nhat-ky-task.md` (mục `## duoc-CR-719` cuối sổ).
Tạo: `backend/scripts/seed_help_yctt_thanh_toan_nghi_phep.py` (cây Thu mua dựng tay, không có seed sở hữu → upsert một bài
dưới thẻ **Dành cho Kho & Kế toán** bằng `help_seed_common.run_article_upsert`).

## HDSD
- Bài mới **Thanh toán nghỉ phép** (tóm tắt 190 ký tự): ai lập / duyệt, các bước lập, hộp **Số ngày được thanh toán** + công
  thức + ví dụ (khớp số đã soát ở local: còn 11, giữ lại 2 → tối đa 9), cuối năm vs nghỉ việc, gửi duyệt / duyệt, sau duyệt
  (trừ quỹ, YCTT, khối Thanh toán, ai thấy số tiền), ma trận sửa / xóa / hủy, băng **Kế toán từ chối chi**, giữ kín lương,
  10 câu báo lỗi nguyên văn.
- Sửa: thẻ gốc (menu bảy mục, khái niệm phiếu TTP), **Hiểu số ngày phép còn lại** (công thức + dòng **Đã thanh toán ra
  tiền**), **Cấp và điều chỉnh quỹ phép** (cột ẩn sẵn **Đã thanh toán ra tiền**), **Loại nghỉ** (3 ô nhóm **Thanh toán nghỉ
  phép**, chặn xóa), **Phân quyền** (khóa thứ sáu, phạm vi, quyền Kế toán D-018).
- Bài kế toán **Yêu cầu thanh toán nghỉ phép: nhập số tiền và chi** (180 ký tự): tìm phiếu (chuông, lọc **Loại nợ**), khác
  YCTT NCC, từ chối, bản in STK (**kế toán tự điền**), ai thấy + cách tick quyền.
- Nhãn đối chiếu bằng đọc mã các tệp `hr/**/leave-encashment-*`, `leave-type-encashment-fields.ts`, `leave-balance-*`,
  `finance/**/payment-request-leave-encashment-*`, `payment-request-{print,list}-page.tsx`, câu lỗi ở `leave/encashment_*.py`,
  `leave_encashment_payout.py`, `notification/service.py`; và màn thật `localhost:8083/hr/leave-encashments/new` (một trang
  Chrome, admin local) — nhãn khớp.
- Seed local: `seed_help_nghi_phep.py` → 15 bài, không lỗi; `seed_help_yctt_thanh_toan_nghi_phep.py` chạy hai lần (thêm →
  cập nhật). Mọi `href` trỏ đúng slug có thật. **RAG tắt ở local → chưa reindex** (chạy `reindex_help_rag.py` trên dev khi deploy).

## Cẩm nang AI
Mục mới **Thanh toán nghỉ phép**: cấm nói số tiền, cách trả lời **tôi được thanh toán mấy ngày phép** (gọi
`my_leave_summary`, giải thích theo luật loại, nói dạng tối đa N ngày, con số chốt ở hộp trên form), đọc trạng thái chi,
kế toán từ chối, không có tool soạn nháp. Thêm khái niệm, công thức, đọc `encashed_days` / `encashments`, khóa thứ sáu,
bảng từ. Sửa đường dẫn menu cũ **Nhân sự ▸ Phân quyền tài khoản** → **Quản trị ▸ …** (khớp HDSD). Xuất bản local:
`nghi-phep` phiên bản 8.

## Kiểm
- `kiem_tai_lieu.py`: 7 lỗi, **0 mới** (exit 0). Không còn ngoặc góc trong các tệp đã sửa.
- `sync_task_journal.py`: không chạy được (thiếu `.task_sync.env` / tài khoản) — đã kiểm bằng `parse_journal`: mục
  `duoc-CR-719` đọc đúng (xong, 2026-11-03, NSU231, tag Được), không trùng key.

## Phát hiện (chưa sửa — ngoài khu)
1. **Lỗi nhỏ, backend (Agent 4):** câu 422 ở `leave/encashment_service.py:80` ghi `"Cho thanh toán ngày phép" ở Thiết lập nghỉ
   phép ▸ Loại nghỉ`, nhãn thật trên màn là **Cho phép thanh toán nghỉ phép** (Nghỉ phép ▸ Thiết lập ▸ Loại nghỉ). HDSD chỉ
   trích phần đầu câu để khỏi chép nhãn sai.
2. **Lỗi nhỏ, backend:** câu 409 trùng phiếu nói **Hủy hoặc hoàn tất phiếu đó trước**, nhưng phiếu Đã duyệt vẫn giữ
   `active_key` → **hoàn tất** không mở được phiếu mới. HDSD ghi rõ phiếu đã duyệt vẫn tính.
3. **Câu hỏi nghiệp vụ:** D4 + `active_key` giữ ở Đã duyệt → người đã nhận thanh toán **phép dư cuối năm** năm X rồi nghỉ
   việc trong cùng năm X không lập được phiếu **Nghỉ việc** cho loại đó/năm đó (409) trừ khi hủy phiếu cũ (mà đã chi thì
   không hủy được). Cần anh Được chốt có cho phiếu nghỉ việc vượt D4 không.
4. **Gợi ý (ai-mcp / backend):** mô tả skill `nghi-phep` trong `ai_skill/handbook_seed.py:45` chưa có chữ **thanh toán nghỉ
   phép** → trợ lý chọn skill theo mô tả có thể bỏ sót. Một dòng chuỗi, không thuộc khu được sửa.
5. `doc/erp/hrm/` vẫn thiếu `chuc-nang/01`, `02`, `tai-lieu-ky-thuat/api.md` (lỗi nền cũ, không do phase này); API
   `/api/leave-encashments` hiện ghi ở `02-nghi-phep.md` §16.3.

## Câu hỏi còn mở
- Mục 3 (phiếu nghỉ việc sau phiếu cuối năm cùng năm).
- Có sửa hai câu lỗi mục 1–2 trước commit không (giao Agent 4).

**Status:** DONE_WITH_CONCERNS
**Summary:** HDSD (bài mới + 5 bài sửa + bài kế toán), §16 tài liệu chức năng, tài liệu YCTT / nghiên cứu / luật, cẩm nang AI
phiên bản 8, change-log và sổ nhật ký đã xong; seed và xuất bản chạy sạch ở local, kiểm tài liệu 0 lỗi mới.
**Concerns/Blockers:** RAG chưa reindex (tắt ở local); hai câu lỗi backend lệch nhãn / gây hiểu nhầm; một câu hỏi nghiệp vụ D4.
