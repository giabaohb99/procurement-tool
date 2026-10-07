# Phase 02 — Bộ máy docx + danh mục biến

## Context Links
- docxtpl 0.20.2 (PyPI 13/11/2025): `render(context, jinja_env=None, autoescape=False)`, `get_undeclared_template_variables(jinja_env=None, context=None)`; deps `python-docx`, `jinja2`, `lxml`
- FE `frontend-v2/src/shared/utils/number-to-vietnamese-words.ts` (66 dòng) — backend CHƯA có bản Python
- `backend/app/core/upload_guard.py` (`guard_upload`, sniff zip), `core/file_registry.py` (`DIRECT_FILE_POLICY`), `core/storage.py` (`download_bytes`), `core/vn_time.py`

## Overview
Priority P1. Status pending. Mọi thứ THUẦN (không DB, không HTTP) để test rẻ: danh mục biến, dựng ngữ cảnh, kiểm & render docx, đọc số thành chữ.

## Key Insights
- **SSTI**: Jinja mặc định cho chạy `{{ ''.__class__.__mro__[1].__subclasses__() }}` — mẫu do người dùng tải lên ⇒ BẮT BUỘC `jinja2.sandbox.SandboxedEnvironment`.
- **Ký tự `& < >`** trong tên/địa chỉ phá XML nếu không `autoescape=True`.
- **Word tách run** (`{{ ho_` + `ten }}` do soát chính tả/định dạng giữa chừng): docxtpl tự gộp phần lớn; ca còn sót → biến lạ/lỗi cú pháp ⇒ bắt ở bước kiểm lúc tải lên, hướng dẫn người dùng gõ lại biến một lần, không định dạng giữa chừng.
- Ngữ cảnh truyền **chuỗi đã định dạng sẵn** (ngày `dd/mm/yyyy`, tiền `15.000.000`, chữ) — không bắt người soạn mẫu biết filter (KISS, và RichText không hợp filter).
- Mẫu chỉ được dùng biến trong danh mục; biến lạ = 422 kèm danh sách (biến lạ render ra rỗng IM LẶNG nếu cho qua).

## Danh mục biến (nguồn DUY NHẤT: `placeholder_catalog.py`, FE đọc qua API)
Tên ASCII snake_case. Ngày `dd/mm/yyyy`, rỗng nếu NULL. Tiền dấu chấm ngăn nghìn.

| Nhóm | Biến | Nguồn |
|---|---|---|
| Người lao động | `ho_ten`, `ma_nhan_vien`, `gioi_tinh`, `ngay_sinh`, `noi_sinh`, `dan_toc`, `so_cccd`, `ngay_cap_cccd`, `noi_cap_cccd`, `dia_chi_thuong_tru`, `dia_chi_hien_tai`, `so_dien_thoai`, `email`, `ma_so_thue`, `so_bhxh`, `so_tai_khoan`, `ten_ngan_hang`, `chi_nhanh_ngan_hang`, `trinh_do`, `chuyen_nganh` | `Employee` (nhãn mã từ `employee/constants.py`; `email` = `personal_email` hoặc `email`) |
| Pháp nhân (bên A) | `ten_cong_ty`, `ten_viet_tat`, `ma_so_thue_cong_ty`, `dia_chi_cong_ty`, `nguoi_dai_dien`, `chuc_vu_nguoi_dai_dien` | `Company` + `legal_rep.full_name`, `legal_rep_title` |
| Hợp đồng | `so_hop_dong` (contract_no hoặc code), `loai_hop_dong`, `ngay_ky`, `ngay_ky_ngay`, `ngay_ky_thang`, `ngay_ky_nam`, `ngay_bat_dau`, `ngay_ket_thuc`, `thoi_han` («12 tháng» / «Không xác định thời hạn» / rỗng), `chuc_danh`, `phong_ban`, `dia_diem_lam_viec`, `ghi_chu` | `LaborContract` + `Department.name` |
| Lương | `luong_co_ban`, `luong_co_ban_bang_chu`, `luong_dong_bao_hiem`, `phu_cap`, `phu_cap_bang_chu`, `phu_cap_ghi_chu`, `tong_thu_nhap`, `tong_thu_nhap_bang_chu` | base/insurance/allowance; tổng = base + allowance |
| Hệ thống | `ngay_lap` (vn_today) | — |

Mỗi mục: `key, label, group, example` — `example` dùng cho render thử lúc tải lên và cho bảng hướng dẫn FE.

## Requirements
- `core/vn_number_words.py`: `read_amount_vi(n: int) -> str` («Mười lăm triệu đồng»), chép đúng luật bản TS (làm tròn đồng, ≤0 → «Không đồng»). Bộ ca test DÙNG CHUNG số liệu với `number-to-vietnamese-words.test.ts`.
- `labor_contract/placeholder_catalog.py`: `PLACEHOLDERS: tuple[Placeholder, ...]`, `KNOWN_KEYS: frozenset`, `sample_context() -> dict`.
- `labor_contract/context_builder.py`: `build_context(contract, employee, company, department, today) -> dict[str, str]`; assert `set(ctx) == KNOWN_KEYS` (test canh).
- `labor_contract/docx_engine.py`:
  - `inspect_template(data: bytes) -> list[str]` (biến dùng): zip hợp lệ; tổng giải nén ≤ 60MB & ≤ 2000 mục (chống zip bomb); có `word/document.xml`; KHÔNG có `vbaProject.bin` (macro); mở `DocxTemplate(BytesIO)`; `get_undeclared_template_variables(jinja_env=SANDBOX)`; biến lạ → `TemplateRejected(unknown=[...])`; render thử `sample_context()` → lỗi Jinja → `TemplateRejected(message)`.
  - `render(data: bytes, ctx: dict) -> bytes`: env Sandboxed, `autoescape=True`, trả bytes.
- `core/file_registry.py` `DIRECT_FILE_POLICY`: `"labor_contract_template": ({"docx"}, 10)`, `"labor_contract_docx": ({"docx"}, 20)`, `"labor_contract_signed": ({"pdf","jpg","jpeg","png"}, 50)`.
- `backend/requirements.txt`: `docxtpl==0.20.2` (kéo `Jinja2` — ghim luôn `Jinja2==3.1.x` bản đang có trên PyPI để build lặp lại được).

## Related Code Files
- Create: `backend/app/core/vn_number_words.py`, `backend/app/modules/labor_contract/placeholder_catalog.py`, `.../context_builder.py`, `.../docx_engine.py`, `test/backend/test_hdld_doc_so_thanh_chu.py`, `test/backend/test_hdld_bo_may_docx.py`
- Modify: `backend/requirements.txt`, `backend/app/core/file_registry.py`

## Implementation Steps
1. Thêm dep → `docker compose up --build api` (đổi requirements nên phải build).
2. Port số→chữ + test (0, 1, 5, 10, 15, 21, 25, 101, 105, 1_000, 1_000_001, 15_000_000, 10^12, âm).
3. Catalog + `sample_context`.
4. `context_builder` (dùng `vn_today()`, nhãn giới tính/học vấn từ `employee/constants.py`, trống thay vì `None`).
5. `docx_engine` + test dựng .docx NGAY trong test bằng `python-docx` (không commit tệp nhị phân).
6. Ca test bắt buộc: biến hợp lệ thay đúng · biến lạ → liệt kê · run bị tách bởi in đậm giữa biến · payload SSTI bị chặn (`SecurityError`) · tên có `&<>"` → docx mở lại được · zip bomb · tệp không phải zip · `.docx` có macro · `{% if %}` thiếu `endif` → thông báo rõ.

## Todo
- [ ] dep docxtpl · [ ] vn_number_words + test · [ ] catalog · [ ] context_builder · [ ] docx_engine · [ ] DIRECT_FILE_POLICY · [ ] test bộ máy

## Success Criteria
`pytest test/backend/test_hdld_doc_so_thanh_chu.py test/backend/test_hdld_bo_may_docx.py -q` xanh; render 1 mẫu ~3 trang < 1s.

## Risk Assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| SSTI qua mẫu | Trung×Rất cao | Sandbox + test payload |
| Run tách → biến lạ | Cao×Thấp | 422 nêu tên biến; hướng dẫn ở màn mẫu |
| Hai bản số→chữ lệch nhau | Trung×Trung | Chung bộ ca test, comment trỏ chéo 2 tệp |
| docxtpl đổi API | Thấp×Trung | Ghim phiên bản |

## Security
Sandbox, autoescape, chặn macro/zip bomb, chỉ `.docx`, trần 10MB, `guard_upload` sniff nội dung.

## Next
Phase 03.
