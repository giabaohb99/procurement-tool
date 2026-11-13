# Phase 04 — Tài liệu, HDSD, cẩm nang, luật, RAG

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 13/11/2026 | tai-lieu-kiem-thu | Nháp | duoc-CR-756 (sửa tài liệu duoc-CR-755) |

## Context links
- [plan.md](plan.md); phase 01-03 (hành vi cuối + câu chữ giao diện).
- Luật: `.claude/rules/chung-tai-lieu.md`, `.claude/rules/chung-dat-ten-va-quy-uoc.md` §4; bộ nhớ dự án "Xong tính năng thì cập nhật HDSD + RAG".

## Overview
Ưu tiên P2. Thay mô hình cặp (phòng, công ty) bằng hai loại dòng ở MỌI nơi đã ghi CR-755; không để hai mô tả đứng cạnh nhau.

## Key insights
- CR-755 ghi mô hình cặp ở 9 chỗ: `doc/erp/hrm/01-ho-so-nhan-su.md` §7.18 (+ §4, §7.10, §7.11 nhắc), `doc/erp/hrm/tai-lieu-ky-thuat/api.md`,
  `doc/erp/hrm/chuc-nang/01-yeu-cau-chuc-nang.md`, `02-yeu-cau-phi-chuc-nang.md`, `doc/tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md`
  §4c, `.claude/rules/hr-employee-profile.md` mục KIÊM NHIỆM, `backend/scripts/seed_help_nhan_su.py` (bài `CONCURRENT`, dòng 71/96/158),
  `backend/app/modules/ai_skill/seed_handbook/60-nhan-su-ho-so.md`, `doc/agent-hub/06-cong-mcp.md` (mô tả `employee_lookup`).
- Kế hoạch CR-755 giữ chỗ (luật 8) nhưng ghi dòng *Mô hình cặp đã thay bằng duoc-CR-756* ở đầu `plan.md` của nó.
- `seed_help_*` có thể không có `--dry-run` — grep `dry` trước khi chạy (bộ nhớ dự án).

## Requirements
1. §7.18: hai loại dòng, luật phạm vi theo bậc (bảng bậc × loại), Q1/Q3/Q4 mới, L2 theo loại, migration `kn756a`. Bảng phiên bản đầu tệp.
2. §4c phân quyền: thay bảng "đường thấy / không thấy cặp" bằng bảng "bậc → công ty kiêm nhiệm cộng gì" (company / dept / dept_proc /
   own / all) + chủ thể công ty B + `company_reach`.
3. `api.md`: dòng `GET /api/employee-concurrents` (tham số mới), POST/PATCH (ô theo loại), PATCH hồ sơ (`keep_old_company_concurrent`);
   chạy `scripts/dung_bang_api.py --repo /repo` (bảng mục 1 dựng bằng máy) rồi sửa tay cột *Phạm vi* / *Ai gọi*.
4. `01`/`02` chức năng: sửa mục CN / PCN kiêm nhiệm (trạng thái *có*).
5. Luật `.claude/rules/hr-employee-profile.md` mục KIÊM NHIỆM viết lại 9 điểm theo mô hình mới (giữ ngắn; chi tiết trỏ §7.18), thêm bẫy:
   loại 1 lưu `company_id` = công ty chính; `dept_proc` không ràng công ty nên công ty kiêm nhiệm không cộng; `own` rơi về `company` chỉ
   công ty chính; L2 loại 2 chỉ bậc toàn công ty.
6. HDSD bài **Nhân sự — Khai kiêm nhiệm** (đổi tiêu đề thành *Khai kiêm nhiệm phòng ban hoặc công ty khác*; sửa `ref()` nơi trỏ tới):
   hai loại, ví dụ *anh A kiêm nhiệm phòng ban A và công ty B*, ai thấy gì theo bậc, hộp đổi pháp nhân một câu hỏi.
7. Cẩm nang `60-nhan-su-ho-so.md` cùng nội dung rút gọn + tăng phiên bản skill; mô tả công cụ ở `06-cong-mcp.md`.
8. `doc/erp/hrm/README.md` dòng kế hoạch CR-756 (đã thêm lúc lập kế hoạch) → cập nhật trạng thái khi xong.
9. Sổ: dòng `duoc-CR-756` ở `doc/tai-lieu-ky-thuat/change-log.md` (đã đặt chỗ) → nội dung + *Xong — erp-v2*; dòng CR-755 thêm câu *mô hình
   cặp đã thay bằng duoc-CR-756*; mục `doc/tai-lieu-ky-thuat/nhat-ky-task.md` câu tiếng Việt trọn vẹn, mã mục duy nhất.

## Architecture
Một sự thật một chỗ: luật chi tiết ở §7.18 + §4c; luật cho người viết mã ở `.claude/rules/hr-employee-profile.md`; HDSD + cẩm nang cho
người dùng / AI, không chép bảng kỹ thuật.

## Related code files
Sửa: các tệp ở Key insights + `doc/erp/hrm/plans/261112-kiem-nhiem-khac-cong-ty-duoc-cr-755/plan.md` (một dòng), `doc/erp/hrm/README.md`,
`doc/tai-lieu-ky-thuat/change-log.md`, `doc/tai-lieu-ky-thuat/nhat-ky-task.md`. Không sửa mã nguồn.

## Implementation steps
1. Đọc báo cáo phase 01-03 (câu chữ, tham số cuối). 2. Sửa tài liệu kỹ thuật (yêu cầu 1-5). 3. HDSD + cẩm nang (6-7). 4. Sổ (8-9).
5. `KIEM_TAI_LIEU_ROOT=$PWD python backend/scripts/kiem_tai_lieu.py` exit 0; `test_kiem_tai_lieu_cr712.py` xanh.
6. Local: chạy `seed_help_nhan_su.py` (sau khi grep `dry`), seed cẩm nang; RAG `reindex_help_rag` trên dev do điều phối làm khi deploy.

## Todo
- [x] §7.18 · [x] §4c · [x] api.md · [x] 01/02 · [x] luật · [x] HDSD · [x] cẩm nang + phiên bản · [x] MCP doc · [x] sổ · [x] cổng kiểm tài liệu

## Success criteria
`grep -rn "concurrent_pairs\|theo CẶP (phòng, công ty)" doc .claude backend/scripts backend/app/modules/ai_skill` chỉ còn trong kế hoạch
CR-755 + sổ change-log; `kiem_tai_lieu.py` exit 0; HDSD hiện đúng trên `localhost:8082` (hoặc Trung tâm trợ giúp v2).

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Đổi tiêu đề bài HDSD làm gãy `ref()` / liên kết RAG | Trung × Trung | Grep `CONCURRENT` + tiêu đề cũ; reindex sau deploy |
| Câu chữ lệch giao diện | Trung × Thấp | Lấy nhãn từ báo cáo phase 03 |

## Security
Không ghi tên người thật / số QĐ thật vào ví dụ. Không chép giá trị nhạy cảm.

## Next
Điều phối: rà mã độc lập (code-reviewer) toàn CR → cổng kiểm (ruff, pytest theo tệp, typecheck, lint, vitest theo khu) → commit một lượt
`duoc-CR-756 ...` → deploy dev cùng `kn755a` → `reindex_help_rag`.
