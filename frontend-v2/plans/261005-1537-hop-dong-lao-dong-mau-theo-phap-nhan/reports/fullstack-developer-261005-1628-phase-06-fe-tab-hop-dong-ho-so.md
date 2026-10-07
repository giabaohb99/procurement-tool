# Phase 06 - FE tab «Hop dong» trong ho so (kem doi chieu phase 05 voi backend that)

Status: done (chua bam tay tren trinh duyet). typecheck 0 loi; lint 0 loi, 29 canh bao = cu, 0 moi; vitest src/modules/hr + src/shared/constants + src/app/router = 89 file / 1106 test xanh.

## Buoc 1 - doi chieu voi serializer that (sua o frontend-v2/src/modules/hr)
- types/labor-contract.ts: viet lai LaborContract theo LaborContractOut: them code, template_name, generated_at, can_delete, can_print, can_upload_signed; doi allowance_amount -> allowance, has_document -> has_generated_file; transitions la number[] (bo kieu LaborContractTransition doan sai). Them LaborContractSaveResult {item, warnings}, LaborContractUpdatePayload. Payload tao: job_title/work_location nullable (null = backend lay tu ho so), bo trung.
- api/labor-contract-api.ts: create/update tra LaborContractSaveResult.
- Template list {total,items} (da dung PaginatedResult), 422 error.details.unknown (da doc dung) - khong phai sua. Copy dialog tai len / huong dan bien da kiem: khong goi y {% if %}, chi {{ bien }}.
- Test moi api/labor-contract-api.test.ts (5).

## Buoc 2 - tab Hop dong
Created (src/modules/hr/): utils/labor-contract-rules(+test), schemas/labor-contract-schema(+test), hooks/use-employee-labor-contracts.ts, config/employee-labor-contract-columns.tsx, components/{labor-contract-status-badge, labor-contract-row-actions(+test), labor-contract-form-dialog(+test), labor-contract-form-dialog-fields, labor-contract-generate-dialog, labor-contract-transition-dialog, employee-tab-labor-contracts(+test), labor-contract-fixture}.
Modified: pages/employee-detail-page.tsx (tab «Hop dong» icon FileSignature, chi dung khi can('labor_contract','read'); ?tab=labor-contracts ma khong quyen -> ve tab Chung), api/labor-contract-api.ts, types/labor-contract.ts, plan.md, phase-06 file.

Hanh vi:
- Nut/hanh dong hien theo co backend (can_edit/can_generate/can_print/can_upload_signed/can_delete, transitions[]), khong tu ghep can(). Tai .docx chi khi can_print. EXPIRED hien tu effective_status.
- Ky (DRAFT->SIGNED) chi hoi ngay ky, khong dong tep. Huy: ly do. Cham dut: ngay (>= start) + ly do. Hop thoai chuyen trang thai KHONG dung <form> long.
- Form: phap nhan chi doc (ReadOnlyValue), loai HD -> an o ngay ket thuc khi INDEFINITE (doi sang loai cam thi xoa ngay cu), tien dung NumberInput decimals=false, chuc danh/dia diem dien san tu ho so, stopPropagation o onSubmit + chan bam dup bang useRef. Loai co 0 mau -> cau «Phap nhan X chua co mau cho loai nay» + link man Mau neu co quyen.
- warnings (>36 thang) -> toast.warning, khong phai loi. Sinh tep: dialog chon mau (loc theo loai, chon san neu chi 1 mau hoac mau cu).
- Tai ban ky len: input file an, kiem duoi pdf/jpg/png <= 50MB truoc khi gui.
- Xoa: confirm() truoc.

## Test dang chu y
Mutation check: bo stopPropagation -> test «Luu khong submit form cha» do (da hoan lai). Phu: schema (end_date theo loai, end<start, tien am/le/NaN/chuoi/tran 10^12, do dai 50/100/255/500), rules (bo ma khop statuses sinh tu BE), row-actions theo co, tab (rong, can_create, EXPIRED, Ky khong tep, Huy thieu ly do, khong co mau, 1 mau, xoa tu choi, tai loi).

## Chua lam / luu y
- Chua smoke-test tren trinh duyet (can tai khoan co labor_contract* da tick quyen / SEED_FORCE_SYNC va docxtpl trong container api).
- Khong co test cap trang cho «tab an khi thieu quyen» (employee-detail-page qua nang de mock); logic la 1 bien can() + goi dieu kien — nen bam tay o phase 07.
- Hang so loai HD (3 = khong xac dinh; 1,2,4,5 bat buoc ngay ket thuc) va ma trang thai bi chep sang utils/labor-contract-rules.ts vi generator khong sinh tap «can end_date»; test doi chieu voi LABOR_CONTRACT_TYPE/STATUS se do neu BE them ma.
- PATCH: backend bo qua job_title/work_location = null, nen xoa trang chuc danh khi SUA khong xoa duoc o BE (chi lay tu ho so khi tao). Khong phai bug, chi la hanh vi can biet.
- Backend (khong sua): GET /employees/{eid}/labor-contract-templates chua chan theo pham vi tung hang (da ghi o report phase 03/04).
- Prettier chua chay (ngoai cong).

**Status:** DONE_WITH_CONCERNS
**Summary:** Da dong bo type/api FE voi serializer that va xong tab «Hop dong»; 3 cong xanh.
**Concerns/Blockers:** Chua bam tay tren trinh duyet; thieu test cap trang cho viec an tab.
