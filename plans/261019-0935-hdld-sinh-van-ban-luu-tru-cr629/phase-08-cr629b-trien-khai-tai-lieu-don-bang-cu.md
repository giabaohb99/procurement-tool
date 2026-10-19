# Phase 08 — CR-629b (bước B): hồi quy FE, tài liệu, diễn tập + deploy, dọn bảng cũ

**Sub-scope:** CR-629b bước B · **Ưu tiên:** P2 · **Trạng thái:** pending · **Effort:** 2.5h (+0.5h dọn bảng ở lần phát hành sau)
**Phụ thuộc:** 07 xanh (pytest + lên/xuống/lên trên MySQL local).

## Frontend — KHÔNG đổi mã
API giữ nguyên (Q4 phase 07) ⇒ `LaborContractTemplateCatalog`, trình soạn CR-606, hộp «Lập hợp đồng»/«Sinh tệp», `DocumentTemplateCatalog`, ô «Chọn mẫu» khi soạn văn bản không đổi. Thay đổi FE duy nhất là tệp sinh `frontend-v2/src/shared/constants/statuses.ts` (phase 07 sở hữu, `gen_status_ts`). Cổng:
```bash
docker compose exec -T erp npm run typecheck
docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/document src/modules/hr src/app/router
```
Không thêm bài vitest (không có hành vi FE mới). Kiểm tay trên `localhost:8083`: HR mở `/document/settings?tab=templates&kind=labor-contract` → tải lên / sửa / thay tệp / soạn trên web / ngừng dùng / xóa (đang dùng ⇒ 409); văn thư mở «Thư viện văn bản mẫu» và ô «Chọn mẫu» khi soạn ⇒ không thấy mẫu HĐLĐ.

## Tài liệu (sở hữu phase này)
- `doc/tai-lieu-ky-thuat/change-log.md`: dòng `duoc-CR-629b` — thêm «Bước B» (STI, giữ id HĐLĐ, dời id mẫu VB khi trùng, `lbrct03`, bảng bak, downgrade) hoặc dòng hậu tố riêng nếu dòng cũ đã «Xong (bước A)».
- `doc/tai-lieu-ky-thuat/nhat-ky-task.md`: mục MỚI, mã duy nhất (hậu tố `-buoc-b`), câu tiếng Việt trọn vẹn, `Mã nguồn:` dòng cuối.
- `doc/erp/hrm/01-ho-so-nhan-su.md` + `doc/tai-lieu-chuc-nang/14-van-thu-van-ban.md` §16: mẫu HĐLĐ nay nằm trong bảng `tab_document_template` (`template_kind=2`), quyền không đổi.
- `.claude/rules/hr-employee-profile.md` hoặc `document-folders-search.md`: 2 dòng «CẤM `query(TemplateRecord)`; thêm loại mẫu mới = thêm lớp con STI + mã `DocumentTemplateKind`».
- Comment bảng trong `labor_contract/model.py` (`template_id` FK mềm → `tab_document_template.id`, loại 2).

## Diễn tập trên bản sao prod (BẮT BUỘC — §A.2 `quy-trinh-nhanh-va-deploy.md`)
1. Đếm trên prod (chỉ đọc, qua adminer/`mysql` SELECT — không ghi tiếng Việt bằng tay):
   ```sql
   SELECT COUNT(*), MAX(id) FROM tab_labor_contract_template;
   SELECT COUNT(*), MAX(id) FROM tab_document_template;
   SELECT COUNT(*) FROM tab_labor_contract WHERE template_id > 0
     AND template_id NOT IN (SELECT id FROM tab_labor_contract_template);   -- orphan_truoc
   SELECT COUNT(DISTINCT template_id) FROM tab_labor_contract WHERE template_id > 0;
   ```
2. Dựng bản sao từ bản sao lưu mới nhất → `alembic upgrade head` → so: loại 2 = số dòng cũ; orphan bằng nhau; `SHOW CREATE TABLE tab_document_template` có unique/index mới và `AUTO_INCREMENT` > `MAX(id)`; mở 3 HĐ có mẫu: tên mẫu hiện, «Sinh tệp» chạy; tạo 1 mẫu VB mới ⇒ id không đụng id HĐLĐ.
3. `alembic downgrade lbrct02` → bảng cũ đủ dòng, đúng id → `upgrade head` lại sạch. Ghi thời gian chạy.

## Deploy
Theo kịch bản phát hành `erp-v2` → `main` (§A.2: diễn tập · sao lưu có kiểm · ngưỡng quay đầu). Dev (`erp-v2`, §C) trước, prod sau.
1. **Sao lưu có kiểm** TRƯỚC `up -d` (migration tự chạy lúc `api` khởi động — §B.5): dump toàn DB + dump riêng 3 bảng `tab_document_template tab_labor_contract_template tab_labor_contract`; `gunzip -t`. Ghi số đếm bước Diễn tập-1.
2. Dừng `api`, `celery-worker`, `celery-beat` cùng lúc (worker cũ còn model cũ sẽ đọc bảng đã đổi tên) → build/up theo §B.3–B.4 (`-f docker-compose.production.yml` ở prod).
3. Xác minh §D + `SELECT version_num FROM alembic_version` = `lbrct03`; chạy lại 4 câu đếm (đổi bảng nguồn sang `template_kind=2`).
4. **Ngưỡng quay đầu**: lệch số dòng / orphan, hoặc «Sinh tệp» lỗi «mẫu không tồn tại» ⇒ dừng `api`+celery, `alembic downgrade lbrct02`, deploy lại image trước; downgrade lỗi ⇒ khôi phục dump 3 bảng + `alembic stamp lbrct02`.
5. Ca biên downgrade (mọi mẫu HĐLĐ bị xóa sau khi lên): sau downgrade xóa dòng `tab_labor_contract_template` có `file_id` không còn trong `tab_file` — qua script Python, không `mysql -e`.

## Dọn bảng cũ — lần phát hành SAU (≥ 1 vòng chạy ổn)
- Migration `lbrct04_bo_bang_mau_hdld_bak.py`: `DROP TABLE tab_labor_contract_template_bak629` (gác tồn tại). **Không đụng `tab_file`** (file_id đang do bảng gộp dùng). Downgrade: tạo lại bảng bak rỗng đúng schema `lbrct01` để downgrade của `lbrct03` có chỗ đổ dữ liệu về.
- Trước khi chạy: so bak với loại 2 lần cuối (đếm theo id) cho chắc.
- Cho tới lúc đó, autogenerate sẽ đề xuất drop bảng bak — gọt tay như mọi lần.

## Tiêu chí xong
Ba cổng FE xanh; diễn tập lên/xuống/lên trên bản sao prod khớp số; prod ở `lbrct03`, số đếm khớp, sinh tệp HĐ cũ chạy; change-log + nhật ký ghi đủ; `lbrct04` có lịch ở lần phát hành sau.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Celery/api cũ chạy đúng lúc rename | TB × TB | Dừng cả 3 container trước `up -d` |
| Sao lưu hỏng đúng lúc cần | Thấp × Cao | `gunzip -t` + dump riêng 3 bảng |
| Dọn bak quá sớm, mất đường đối chiếu | Thấp × TB | `lbrct04` chỉ ở lần phát hành sau, có bước so |

## Rollback
Như mục Ngưỡng quay đầu. `lbrct04` revert = downgrade tạo lại bak rỗng (dữ liệu vẫn ở bảng gộp).
