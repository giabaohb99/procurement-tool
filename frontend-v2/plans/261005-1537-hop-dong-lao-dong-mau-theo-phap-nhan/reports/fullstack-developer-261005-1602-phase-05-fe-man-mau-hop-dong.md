# Phase 05 report - FE man Mau hop dong

Status: done. typecheck 0 loi; lint 0 loi (29 canh bao cu, 0 moi); vitest src/modules/hr + src/app/router + src/shared/constants = 82 file / 1017 test xanh (+ 3 test trang).

## Files
Created (frontend-v2/src/modules/hr/): types/labor-contract.ts, api/labor-contract-template-api.ts(+test), api/labor-contract-api.ts, hooks/use-labor-contract-templates.ts, config/labor-contract-template-columns.tsx(+test), pages/labor-contract-template-list-page.tsx(+test), components/labor-contract-template-upload-dialog.tsx(+test), components/labor-contract-template-file-picker.tsx, components/labor-contract-placeholder-guide-dialog.tsx(+test), utils/labor-contract-template-errors.ts(+test), utils/labor-contract-placeholder-groups.ts(+test).
Modified: shared/constants/query-keys.ts, shared/constants/app-routes.ts, modules/hr/routes.tsx, plan.md, phase-05 file.

## Notes for phase 06
- query keys: hr.laborContractTemplates(params), hr.laborContractPlaceholders(), hr.employeeLaborContracts(id), hr.employeeLaborContractTemplates(id, type). Duoi khoa ho so nen invalidate hr.all quet het.
- laborContractApi (listByEmployee, listTemplateOptions, create, update, remove, generate, transition, uploadSignedFile, downloadDocument, downloadSignedFile) + types LaborContract* da co. Hinh dang LaborContract/Transition la SUY RA tu phase-04 doc (doc chi noi "effective_status, can_edit, can_generate, transitions[]"): doi chieu voi serializer that khi phase 04 xong, sua o types/labor-contract.ts neu lech.
- Nav: muc «Mau hop dong» group Danh muc, entity labor_contract_template (khong manage), duoi «Chuc vu». Trang tu kiem can(read).
- 422 bien la: doc tu error.details.unknown (cung nhan error.unknown). Phase 03 controller phai tra details={"unknown":[...]} qua core.response.error.
- Cot «Cap nhat» doi thanh «Ngay tao» + nguoi tao vi BE khong tra updated_at.
- Bo loc q/company_id/contract_type/is_active dung URL params; khong gan ConditionalFilter (phase 03 khong khai FILTERABLE).

## Unresolved
- Dang ky route chua duoc kiem tren trinh duyet that (backend phase 03 chua xong); chua bam tay.
- Chua chay Prettier (ngoai cong).
