# Báo cáo bao-CR-712 — tổ chức lại tài liệu (P1–P4)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 03/11/2026 |
| Người phụ trách | Agent 4 |
| Trạng thái | Hiệu lực |
| CR liên quan | bao-CR-712 |

Trạng thái kế hoạch: **xong P1–P4** (P5 — đổi bài kiểm sang chế độ chặn — chờ dọn hết lỗi dưới đây).

## 1. Đã làm

- **P1:** `.claude/rules/chung-dat-ten-va-quy-uoc.md` (luôn nạp), `.claude/rules/chung-tai-lieu.md`, mục lục
  [`quy-dinh/README.md`](../../tai-lieu-ky-thuat/quy-dinh/README.md), luật ghi kế hoạch vào `doc/erp/<phan-he>/plans/`,
  bài kiểm `backend/scripts/kiem_tai_lieu.py` (chỉ báo).
- **P2:** tài liệu chung vào `tai-lieu-ky-thuat/kien-truc|phan-quyen|van-hanh/`, `doc/plans/`, V1 vào `doc/v1/`, thư mục tên
  tiếng Anh đổi tên Việt.
- **P3:** 14 nhóm dời về khuôn phân hệ; 18 phân hệ (trừ HRM) đủ 4 tài liệu bắt buộc trạng thái Nháp (api.md dựng từ
  `app.routes`); bản đồ `doc/README.md`, `doc/erp/README.md`, `doc/v1/README.md`; chỗ đọc tài liệu của bot
  (`agent_hub/memory.py`).
- **P4:** kế hoạch không thuộc HRM ở `plans/` gốc và `frontend-v2/plans/` về `plans/` của phân hệ (văn thư, công việc,
  hải quan, nền tảng, đặt xe) hoặc `doc/plans/`.

Bảng dời từng đợt: script `D:/tmp/cr712_move.py` + các tệp bảng (lưu ở máy Agent 4); lịch sử đủ trong `git log --follow`.

## 2. Để người phụ trách HRM (anh Dược) dời

- `doc/tai-lieu-chuc-nang/17-nghi-phep.md`, `18-dat-phong-hop.md`, `21-lich-lam-viec.md` → `doc/erp/hrm/chuc-nang/`
  (sau đó xóa `doc/tai-lieu-chuc-nang/`).
- `doc/erp/nghien-cuu/erpnext/` (03, 04, `ban-nhap-hrms/`, README) và `doc/erp/tham-khao-hrm/` → `doc/erp/hrm/nghien-cuu/`.
- `doc/erp/hrm/*.md` → `chuc-nang/` / `tai-lieu-ky-thuat/` theo khuôn + 3 tài liệu bắt buộc (01, 02, api.md — có thể
  sinh api.md bằng cách của bao-CR-712).
- Kế hoạch HRM còn ở `plans/`: `260903-0956-quan-ly-nghi-phep`, `260904-1144-dat-phong-hop`, `260907-1005-nhieu-loai-nghi-trong-mot-don`, `261019-0935-hdld-sinh-van-ban-luu-tru-cr629`, `261019-0935-nhap-excel-nhan-su-cr628`, `261019-1100-bien-mau-hdld-crud-cr630`, `261020-1545-hdld-cua-toi-cr652`, `261020-1545-quyen-mac-dinh-theo-chuc-vu-cr653`, `261022-1602-stress-test-cr661-670`, `261023-0935-stress-test-cr660-cr674`, `261023-1125-ep-tai-cr676`, `261023-1330-ep-tai-cr680`, `261026-1028-buoc-0-du-lieu-dev`, `261027-1045-kho-mau-bao-cao-nhan-su`, `261102-1652-nghi-phep-kieu-erpnext`, `261103-0857-nghi-phep-du-nhu-nexterp`.
- Ở `frontend-v2/plans/`: `261003-0837-qua-trinh-lam-viec-nhan-su`, `261005-0925-hr-lich-lam-viec`, `261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan`.
- Báo cáo lẻ còn ở `plans/reports/` (phần lớn của duoc-CR-653, 676, 680, 682, 686–688, 635): 30 tệp.

## 3. Chủ sở hữu chưa rõ — để nguyên, A1 phân

`plans/261022-1602-stress-test-cr661-670`, `261023-0935-stress-test-cr660-cr674`, `261023-1125-ep-tai-cr676`,
`261023-1330-ep-tai-cr680`, `261026-1028-buoc-0-du-lieu-dev` (thư mục có `scripts/`, đường chạy có thể đang được dùng).

## 4. Bộ nhớ agent còn trỏ đường cũ (A1 sửa)

- MEMORY.md: doc/erp/00-ke-hoach-theo-module.md
- ai-rag-tro-ly-tai-lieu.md: doc/erp/tai-lieu-ai/01-kien-truc-tro-ly-ai.md, doc/erp/tai-lieu-ai/02-danh-sach-api-tool.md, doc/erp/tai-lieu-ai/03-lo-trinh-phase.md
- chi-phi-thu-mua-gia-ba-giai-doan.md: doc/erp/nhap-khau/02-chi-phi-thu-mua.md
- cr-prefix-ten-nguoi.md: doc/erp/tai-lieu-ky-thuat/
- cr428-man-vai-tro-de-doc.md: doc/phan-quyen/Thiet_Ke_Phan_Quyen.md
- deploy-dev-1609-cr407-411.md: doc/dong-bo-dat-xe-duyet-dau/
- doc-process-adoption.md: doc/erp/tai-lieu-ky-thuat/, doc/testcase/
- dong-bo-app-dat-xe-cu.md: doc/dong-bo-dat-xe-duyet-dau/
- hai-quan-yeu-cau-chi-mi-cr493-496.md: doc/erp/hai-quan/06-doi-chieu-yeu-cau-fr-proc-2026-001.md
- kiem-log-tep-truoc-khi-ghi-lai.md: doc/erp/nghien-cuu/03-mau-thuan-san-xuat.xlsx
- may-het-ram-pagefile-wsl.md: doc/tai-lieu-ky-thuat/gioi-han-tai-nguyen-docker.md
- p3-dong-bo-erp-sang-app-cu.md: doc/dong-bo-dat-xe-duyet-dau/, doc/dong-bo-dat-xe-duyet-dau/p3-erp-sang-app-cu.md
- plan-ra-soat-api-hieu-nang.md: doc/tai-lieu-ky-thuat/ra-soat-api-hieu-nang.md
- prod-0211-dien-dan-nghi-phep.md: doc/erp/crm/00-ke-hoach-crm.md
- prod-2610-dot5-tron.md: doc/tai-lieu-ky-thuat/vps-dev-tai-khoan-ida.md
- prod-deploy-compose-file.md: doc/tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md
- so-ghi-nhan-loi-bao-mat.md: doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md
- survey-request-flow-phases.md: doc/yeu-cau/, doc/yeu-cau/Requirement_Task5_YeuCauKhaoSat.md
- viec-con-lai-uu-tien.md: doc/erp/00-ke-hoach-theo-module.md

## 5. Bài kiểm tài liệu sau P4 (chỉ báo)

```
## Liên kết hỏng — 39
- doc/tai-lieu-ky-thuat/change-log-bao.md → ../erp/12-ke-hoach-erp-v2-da-phap-nhan.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/12-ke-hoach-erp-v2-da-phap-nhan.md
- doc/tai-lieu-ky-thuat/change-log.md → ../../backend/app/modules/assistant/packs/50-dat-phong-hop.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/15-do-be-tong-nen-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/16-quan-ly-import-export-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/12-ke-hoach-erp-v2-da-phap-nhan.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/15-do-be-tong-nen-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/15-do-be-tong-nen-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/15-do-be-tong-nen-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/15-do-be-tong-nen-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/14-filter-sort-man-danh-sach-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/14-filter-sort-man-danh-sach-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/change-log.md → ../erp/13-ke-hoach-man-con-lai-v2.md
- doc/tai-lieu-ky-thuat/nhat-ky-task.md → /y

## Đường dẫn trong backtick không tồn tại — 3
- .claude/rules/document-folders-search.md → `frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/`
- .claude/rules/frontend-v2-migration-status.md → `doc/erp/12-`
- .claude/skills/them-cong-cu-mcp/SKILL.md → `doc/erp/21-kho-skill-ai-mcp.md`

## Tên sai luật (chữ thường, không dấu, gạch ngang) — 36
- doc/v1/chung/CHANGELOG.md
- doc/v1/chung/Deploy_VPS.md
- doc/v1/chung/FEATURE_CHECKLIST.md
- doc/v1/chung/Go_Live_Checklist.md
- doc/v1/chung/NAMING_CONVENTIONS.md
- doc/v1/chung/Plan_Celery_Worker.md
- doc/v1/chung/[Data Chuẩn] 3. THU MUA_MR TIÊN.xlsx
- doc/v1/thiet-ke/AI_Gen_Prompt.md
- doc/v1/thiet-ke/Dashboard_Spec_UXUI.md
- doc/v1/thiet-ke/Thiet_Ke_Giao_Dien.md
- doc/v1/yeu-cau/Mapping_Sheet06_TienDoMuaHang.md
- doc/v1/yeu-cau/Plan_CapNhat_Flow_KhaoSat_v2.md
- doc/v1/yeu-cau/Plan_CapNhat_ThuMua_2026_07.md
- doc/v1/yeu-cau/Requirement_BaoCao_MuaHang.md
- doc/v1/yeu-cau/Requirement_Email_Approval.md
- doc/v1/yeu-cau/Requirement_Features_Detail.md
- doc/v1/yeu-cau/Requirement_KhaoSat_NCC_SP.md
- doc/v1/yeu-cau/Requirement_KhaoSat_TruongChiTiet.md
- doc/v1/yeu-cau/Requirement_Mini_Tool_Thu_Mua.md
- doc/v1/yeu-cau/Requirement_Module_File.md
- doc/v1/yeu-cau/Requirement_Phase34_UX.md
- doc/v1/yeu-cau/Requirement_PO_Detail.md
- doc/v1/yeu-cau/Requirement_PO_GR_CongNo.md
- doc/v1/yeu-cau/Requirement_Task4_AutoAssign_PhanCong.md
- doc/v1/yeu-cau/Requirement_Task5_YeuCauKhaoSat.md
- doc/v1/yeu-cau/Requirement_Task7_GopKhaoSat.md
- doc/v1/yeu-cau/Requirement_Task8_BaoCao_ThieuThongTin.md
- doc/v1/yeu-cau/Requirement_Task9_Tab_NCC.md
- doc/v1/yeu-cau/Requirement_YeuCauMua_ChiTiet.md
- doc/v1/du-lieu/sheet/sheet_03_khao_sat_ncc.json
- doc/v1/du-lieu/sheet/sheet_04_khao_sat_sp.json
- doc/v1/du-lieu/sheet/sheet_06_tien_do_mua_hang.json
- doc/tai-lieu-ky-thuat/export/build_diagrams.py
- doc/tai-lieu-ky-thuat/export/build_doc_pdf.py
- doc/he-agent/nguoi-chu/NSU209.md
- doc/he-agent/so-quyet-dinh/NSU209.md

## Phân hệ thiếu README.md — 0

## Phân hệ thiếu tài liệu bắt buộc (01 / 02 / api.md) — 1
- doc/erp/hrm/: thiếu chuc-nang/01-yeu-cau-chuc-nang.md, chuc-nang/02-yeu-cau-phi-chuc-nang.md, tai-lieu-ky-thuat/api.md

## Tệp lẻ ở cấp doc/ — 0

## Skill / agent / luật chưa có trong mục lục quy định — 0

Tổng: 79 lỗi (chỉ báo).
```
