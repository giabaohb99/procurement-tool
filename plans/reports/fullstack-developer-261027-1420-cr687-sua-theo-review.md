# CR-687 sua theo review

Test: `-k "cr687 or gac_duong or assistant_report_summary or bao_cao_nhan_su or bien_dong or cr686"` -> 259 passed.

## Done
1. A2 che nhom tuoi (`employee/report_headcount_privacy.py`)
   - So cap: che nhom neu BAT KY so dem (start/end/new_hires/departures, ky nay hoac so sanh) = 1 hoac 2.
   - Thu cap: nhom bi che (bo nhom toan 0) chi 1, hoac tong headcount_end < 3 -> che them nhom hien nho nhat con nguoi, lap toi khi >= 2 nhom va tong >= 3 hoac het nhom. Tong giu nguyen. Nhom bi che co co `suppressed=True`; them note giai thich.
   - Excel: `core/report_export.py` xoa o so cua nhom `suppressed` sau khi dung (hau xu ly bang openpyxl) -> o TRONG, khong phai 0. Bao cao khac khong co co nay nen khong doi.
   - Test (co_cau): tong - nhom hien khong lo nhom 61 tuoi; start 1 / new_hires 2 bi che; ky so sanh = 1 bi che; xuat Excel o trong; co `employee_sensitive.read` thay het.
2. Xuat tep theo scope `export` (`report_inputs.py`, 2 controller): `apply_scope(..., "export")` cho Employee + LaborContract; route export doi `labor_contract.export`. Test: employee read=all, export=own chi xuat dong cua minh; thieu labor_contract.export -> 403.
3. `leave_days.py`: nhan `leave_q` da qua `apply_scope(..., "leave_request")`. Khong co `leave_request.read` -> `leave_q=None`, 2 cot nghi de trong + ghi chu o A6 sheet. Test ca hai nhanh.
4. `people_data.py`: `created_at` UTC so voi can ky gio VN (tru `VN_OFFSET`), doi sang ngay bang `to_local_date`. Test bien 23:30 vs 00:30 VN.
5. `left_in_period` chi tinh `resign_date <= as_of`; nguoi nghi sau `as_of` van "dang lam". Test.
6. 01/PLI loai SERVICE / COLLABORATOR khoi summary, rows, export (`is_civil_contract`); ghi chu so nguoi bi loai (summary notes, A4 moi sheet, sheet trong). So quan ly (B2) giu ho. Test.
7. Nits: cot nghi "trong ky"; `text_cell` dung `_FORMULA_TRIGGER_CHARS`; `unique_sheet_name` bo dau nhay dau/cuoi; phap nhan khong co trong bang xep cuoi; xoa `date_cell`, `department_names` (dung `load_group_names(always=True)`), `AGE_BAND_LABELS`, comment cu; nhan "Noi cu tru"; ghi chu so nguoi lay ngay tao ho so thay ngay vao lam (summary notes + A6 Excel).
8. Theo yeu cau them: cau 403 thanh tieng Viet khong kem ma ky thuat («Ban can quyen xem thong tin nhay cam cua nhan su de mo bao cao nay — nho quan tri cap o Phan quyen.»); test cap nhat.

## Files
backend: `employee/report_headcount_privacy.py`, `employee/report_headcount_dims.py`, `labor_register/{export_common,form_01_pli_export,labor_book_export,leave_days,people_data,register_controller,usage_report_controller,report_inputs,report_service}.py`, `core/report_export.py`.
tests: `test_bao_cao_co_cau_cr687.py`, `test_bao_cao_so_lao_dong_cr687.py`, `test_bao_cao_mau_01_pli_cr687.py`. Tat ca file < 200 dong. So truy van van co dinh (test dem truy van xanh).

## Luu y
- Thu cap chi xet tong headcount_end ky nay (dung quyet dinh); tong ky so sanh - nhom hien ky so sanh khong duoc kiem rieng.
- `export_common` import `_FORMULA_TRIGGER_CHARS` (ten private) tu `core/export_xlsx`.
- Nhom 01/PLI chi co nguoi khoan viec/CTV khong con sheet rieng (chi duoc dem trong ghi chu).
- Chua cap nhat `seed_help_bao_cao_nhan_su.py` (agent khac); HDSD can ghi: che them nhom ke tiep, 01/PLI loai khoan viec/CTV, xuat can labor_contract.export.

**Status:** DONE
**Summary:** Du 7 nhom sua + cau 403 tieng Viet; 259 test xanh.
**Concerns/Blockers:** khong.
