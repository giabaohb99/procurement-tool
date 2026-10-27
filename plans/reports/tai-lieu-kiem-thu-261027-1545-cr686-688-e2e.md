# Kiểm thử E2E 11 báo cáo Nhân sự (duoc-CR-686/687/688) — LOCAL

Ngày 27/10/2026 · Agent 2 (tài liệu và kiểm thử) · nhánh `erp-v2` @ `ec40a667` · chỉ local (8083 + 8000), không đụng dev/prod, không sửa mã, không commit.
Cách làm: skill `soat-man-dev` áp cho local. chrome-devtools MCP đang bận (hồ sơ trình duyệt bị phiên khác giữ) nên dùng Playwright headless với Chrome của máy. Khổ điện thoại dùng `is_mobile` 390x844 (emulate), không dùng resize.
Ảnh: `plans/reports/e2e-261027-shots/` (tên tệp `<vai>-<màn>.png`). Tệp Excel tải về nằm ở `/tmp/e2e/xlsx/` (dữ liệu demo local, không đưa vào repo).

## Kết luận
**Không có lỗi chặn.** Có 3 lỗi Nên sửa: một lỗi số liệu ở danh sách, một lỗi danh sách không khớp thẻ, một công tắc gây hỏng cả trang với người thiếu quyền. Thêm khoảng 20 lỗi nhỏ về nhãn, bố cục trên điện thoại, Excel và bài HDSD. Phân quyền đều đúng ở cả 3 vai: không lộ lương, tuổi hay CCCD ngoài thiết kế. Tệp 01/PLI đúng 27 cột, đúng tiêu đề 3 tầng.

## Vai thử
| Vai | Tài khoản | Quyền | Khóa báo cáo |
|---|---|---|---|
| A | `admin` | tất cả | 1–24 |
| B | `test_hr_sens@test.local` (vai trò `TEST_HR_SENS`) | employee read/export, employee_sensitive read, labor_contract read/export, leave_request + leave_balance read/export, department/company read | 6–8, 17–24 |
| C | `test_no_sens@test.local` (vai trò `TEST_NO_SENS`) | employee read, labor_contract read, department/company read; KHÔNG có nhạy cảm, KHÔNG có nghỉ phép, KHÔNG có quyền xuất | 6, 19–24 |

## Bảng phủ (11 màn × 3 vai)
| Báo cáo | A | B | C |
|---|---|---|---|
| Biến động nhân sự (+ Nhóm tuổi/Trình độ/Địa điểm/Nhóm vị trí) | ✔ số khớp danh sách; lọc phòng ban OK (Kế toán = 25) | ✔ | ✔ nhóm tuổi bị che «—», che thêm nhóm bù; danh sách theo nhóm tuổi trả 403 bằng câu tiếng Việt; không có nút Xuất |
| Tình hình nghỉ phép | ✔ (lỗi N1) | ✔ | 403 (đúng, chưa giao khóa 7) |
| Quỹ phép năm | ✔ | ✔ | 403 (đúng) |
| Hợp đồng lao động | ✔ | ✔ | 403 (đúng) |
| Hồ sơ & tài khoản còn thiếu | ✔ có nhóm tài khoản | ✔ ẩn nhóm tài khoản (đúng) | 403 (đúng) |
| Sổ quản lý lao động | ✔ + Excel | ✔ + Excel có lọc phòng ban | chặn bằng câu dễ hiểu (lỗi nhỏ M14) |
| 01/PLI | ✔ + Excel | ✔ + Excel | chặn bằng câu dễ hiểu |
| Quỹ lương theo pháp nhân | ✔ che nhóm < 3 người «—», Excel để trống ô bị che | ✔ | thấy lương (đúng thiết kế: có `labor_contract.read` và được giao khóa 21) |
| Phúc lợi & sự kiện | ✔ 7 dịp có sẵn; kinh phí = NV×mức + QL×mức; Xuất danh sách ký nhận | ✔ | lọc tuổi, 1/6, Trung thu, Sinh nhật tháng bị khóa; ép tham số qua URL thì nhận 403 tiếng Việt (lỗi N3) |
| Cơ cấu quản lý | ✔ | ✔ | ✔ |
| Điều chuyển & bổ nhiệm | ✔ (lỗi N2) | ✔ | ✔ |

Ngoài bảng trên đã kiểm thêm:
- API đối chiếu thẻ số với tổng danh sách (`/summary/rows`) cho mọi chỉ số có danh sách, và cho 6 nhóm đầu của mọi chiều «Xem theo»: chỉ sai ở N1 và N2.
- Biểu đồ linh hoạt: Vẽ theo, Cột ngang / Cột / Vành khuyên, Top 5/10/20/Tất cả. Nhóm thừa gộp thành «Khác (n nhóm)» và tổng khớp. Cột «Khác» không bấm được. Bấm cột hoặc lát vành khuyên ra đúng danh sách. Vành khuyên bị mờ khi có hơn 6 nhóm. Tải ảnh PNG ra tệp `bieu-do-hr-headcount-….png` (30 KB). Tải lại trang vẫn giữ lựa chọn trên đường dẫn.
- Khổ 390px: không màn nào tràn ngang (scrollWidth = 390). Ngăn danh sách hiện dạng thẻ. Nút PNG chỉ còn biểu tượng.

## Lỗi — Nên sửa
**N1. «Đơn chờ duyệt quá 3 ngày»: danh sách liệt kê mọi đơn đang chờ, không lọc mốc 3 ngày.** Vai A/B. Tháng này thẻ ghi 0 nhưng danh sách ra 1 đơn (NP003, gửi 26/10). Cả năm thẻ ghi 1 nhưng danh sách ra 2 đơn.
Nguyên nhân: `backend/app/modules/leave/report_drill_rows.py:90`, phần `- timedelta(hours=PENDING_OVERDUE_HOURS)` bị viết lọt vào sau dấu `#` của chú thích:
```python
cutoff = datetime.now()  # cùng đồng hồ với `submitted_at`, xem report_sql_metrics - timedelta(hours=PENDING_OVERDUE_HOURS)
```
Sinh ra ở commit 31fb3bf4 (CR-686). Chủ: backend. Nên thêm bài kiểm «thẻ = tổng danh sách» cho chỉ số này.

**N2. «Số người có biến động»: danh sách ra số LƯỢT, thẻ ghi số NGƯỜI.** Vai A/B/C, kỳ «Năm nay»: thẻ ghi 1, danh sách ra 3 dòng (MKT_TP: bổ nhiệm, kiêm nhiệm, điều chuyển). Bài HDSD dòng 669 ghi rõ «một người chuyển hai lần vẫn đếm một».
Kỳ vọng: danh sách gom mỗi người một dòng, hoặc đổi tên danh sách cho khỏi lệch. Chủ: `backend/app/modules/employee/work_move_report_service.py` (`build_rows`, chỉ số `people_moved`).

**N3. Phúc lợi: công tắc «Tính người đang nghỉ» vẫn bấm được với người không có `leave_request.read`.** Vai C tắt công tắc thì cả trang báo «Không tải được báo cáo» (403 LEAVE_MSG). Ảnh: `C-benefit-toggle-onleave.png`.
Kỳ vọng: công tắc bị khóa kèm dòng giải thích, giống ô tuổi. Chủ: `frontend-v2/src/modules/report/components/benefit-audience-filters.tsx` (khoảng dòng 137–143).

## Lỗi nhỏ
| # | Màn / vai | Thực tế | Kỳ vọng / gợi ý | Chủ tệp |
|---|---|---|---|---|
| M1 | Biến động, nút «Xem» ở dòng (mọi vai) | Ngăn mở theo chỉ số của biểu đồ (mặc định «Vào mới»). Dòng 35–44 có Định biên 103 mà ngăn báo «Vào mới · 0 dòng · Không có ai». Ảnh `A-headcount-drill-age.png` | Mặc định theo cột đầu của bảng (Định biên cuối kỳ) | `hooks/use-report-drilldown-state.ts` / `utils/report-drilldown-metrics` |
| M2 | Biến động, vai C, Xem theo Nhóm tuổi | Nút «Xem» của nhóm không bị che vẫn bấm được, ra lỗi kèm nút «Thử lại» (thử lại vô ích). HDSD có ghi hành vi này | Ẩn hoặc khóa nút khi thiếu quyền nhạy cảm; bỏ «Thử lại» khi lỗi 403 | `report-grouped-table.tsx`, `report-drilldown-sheet.tsx` |
| M3 | Biến động, vai C, Vẽ theo Nhóm tuổi chỉ số «Vào mới» | Báo «Mọi nhóm đều bị che» trong khi 2 nhóm không bị che, chỉ là bằng 0 | Câu báo tách hai trường hợp bị che và bằng 0 | `report-flexible-chart.tsx` |
| M4 | Biến động, khối «Theo trạng thái» | Dòng phụ ghi «Theo vào mới» nhưng số là định biên (267/1) | Ghi «Theo định biên cuối kỳ» (lỗi cũ, không phải của CR này) | `report-breakdown-charts.tsx` / `rank_by` |
| M5 | Biến động, thẻ «Tỷ lệ nghỉ việc» | Ghi «Số dư hiện tại — bấm để vẽ theo nhóm» | Tỷ lệ của kỳ, không phải số dư | `kpi-trend-card.tsx` / cờ `snapshot` |
| M6 | Biến động, mô tả trang | Không nhắc 4 chiều mới (nhóm tuổi, trình độ, địa điểm, nhóm vị trí) | Bổ sung mô tả | `report-catalog-hr.ts` / trang |
| M7 | Điện thoại 390px, mọi màn báo cáo | Ô Phòng ban và Công ty co lại còn biểu tượng + 1 ký tự (`montage2-hr-headcount.png`). Bảng «Chi tiết theo» giấu cột số ra ngoài mép phải nên nhìn như ô trống (`montage-A-mobile-benefit-audience.png`) | Cho bộ lọc xuống dòng hoặc chiếm cả hàng; ghim cột số, hoặc dùng thẻ trên điện thoại | `report-filters-bar.tsx`, `report-grouped-table.tsx` |
| M8 | Quỹ lương, khi chỉ có 1 nhóm hoặc mọi nhóm bị che | Bảng chỉ còn dòng Tổng. Lý do nằm trong «Cách tính số liệu» đang gập | Hiện một dòng giải thích ngay trên bảng | `payroll-fund-report-page.tsx` |
| M9 | Quỹ lương | HĐ có lương cơ bản 0 (MKT_YC) vẫn tính vào «Số người hưởng lương». Bình quân bị kéo xuống, «Lương cơ bản thấp nhất» = 0 | Loại HĐ chưa ghi lương, hoặc đếm riêng | `labor_contract/payroll_report_data.py` |
| M10 | Phúc lợi, chưa nhập mức quà | Bảng xếp theo Tổng kinh phí (đều 0) nên thứ tự lộn xộn (`C-benefit-8-3.png`) | Kinh phí bằng nhau thì xếp theo Số người | `employee/benefit_report_service.py:49` |
| M11 | Phúc lợi, dịp Tết / Trung thu / Kỷ niệm | Giữ nguyên ngày của dịp bấm trước (ví dụ 01/06/2027), không nhắc người dùng chọn ngày | Nhắc «chọn ngày dịp», hoặc xóa ngày cũ | `benefit-occasion-preset-chips.tsx` |
| M12 | Phúc lợi | Các dịp có sẵn đặt `compare=none`, trên màn không có chỗ chọn so sánh. Tài liệu `05-bao-cao-nhan-su.md` mục H1 lại ghi «So với cùng dịp năm trước ✅» | Làm thêm, hoặc sửa tài liệu thành ⏳ | FE + `doc/erp/hrm/05` |
| M13 | 01/PLI, nhãn chỉ số `ct_other` | «HĐ khác (thử việc, khoán, CTV, chưa có HĐ)» trong khi khoán / CTV bị loại khỏi mẫu | Bỏ «khoán, CTV» khỏi nhãn | `labor_register/report_service.py:74` |
| M14 | Sổ / 01-PLI, vai C | Trang chặn vẫn hiện nút «Đặt lại bộ lọc» (không giúp được gì). Kỳ hiện «01/01–31/12/2026», trong khi vai A thấy «–27/10». Menu vẫn hiện 2 báo cáo C không bao giờ mở được | Ẩn nút khi lỗi 403; cân nhắc ẩn mục menu khi thiếu `employee_sensitive.read` | `report-analytics-page.tsx`, `report-catalog-hr.ts` |
| M15 | Quỹ phép năm | «Tỷ lệ sử dụng» dòng Tổng làm tròn 1%, dòng nhóm 0,8% | Cùng 1 chữ số lẻ | định dạng % |
| M16 | Excel 01/PLI và Sổ, tên sheet | Cắt 31 ký tự nên khó phân biệt: «CÔNG TY TNHH XUẤT NHẬP KHẨU» và «CÔNG TY TNHH XUẤT NHẬP KHẨ 2» | Dùng tên ngắn / mã pháp nhân, hoặc bỏ «CÔNG TY TNHH» | `labor_register/export_common.py:63` |
| M17 | Excel 01/PLI, cột 26 | «Thời điểm đơn vị kết thúc BHXH». Cột 25 có chữ «đóng», cột 26 thì không | Đối chiếu PDF mẫu gốc (nhiều khả năng là «…kết thúc đóng BHXH») | `labor_register/form_01_pli_layout.py:36` |
| M18 | Excel Biến động (và mọi báo cáo có chỉ số «tại thời điểm») | Cột Định biên đầu/cuối kỳ, Thay đổi ròng, Tỷ lệ nghỉ việc ghi dạng CHỮ ('266'), không cộng được. Ở Biến động nay có cả số theo nhóm | Ghi số thật (lối cũ CR-482, `_snap_text`) | `core/report_export.py` |
| M19 | Tên tệp xuất | Ký nhận luôn là `danh-sach-ky-nhan-phuc-loi.xlsx` (không có dịp / ngày). Sổ / 01-PLI thiếu hậu tố ngày xuất mà các tệp khác có | Thêm dịp + ngày vào tên | `benefit_report_export.py`, `labor_register/*_export.py` |
| M20 | Excel, chống công thức | Ô mở đầu bằng `= + - @` được thêm dấu `'` vào CHÍNH giá trị (`'=1+2 …`), nên Excel hiện cả dấu nháy. An toàn nhưng xấu | Dùng `quotePrefix` của ô thay vì chèn ký tự | `core/export_xlsx` / `export_common` |
| M21 | API `/summary/export` khi thiếu quyền xuất | Câu «Không có quyền: export employee» lộ mã quyền. Giao diện đã ẩn nút nên chỉ gặp khi gọi thẳng API (lỗi cũ, dùng chung `require`) | Câu tiếng Việt thường | `core/auth.py` |
| M22 | Bài HDSD «Đọc báo cáo Biến động nhân sự» (dòng 183) | Ghi «kỳ không có ai vào, nghỉ → báo *Kỳ này chưa có dữ liệu*, ẩn bảng, nút *Xem cả năm nay*». Thực tế (Tháng trước) bảng vẫn hiện, chỉ biểu đồ ghi «Kỳ này chưa có phát sinh.» (`A-hr-headcount-lastmonth-tall.png`) | Sửa bài HDSD (khu của Agent 2, làm ở lượt sau) | `backend/scripts/seed_help_bao_cao_nhan_su.py` |

## Tệp Excel (openpyxl)
- **01/PLI** (vai A, Năm nay):
  - 13 sheet, mỗi pháp nhân một sheet, tên sheet hợp lệ.
  - 27 cột A–AA, đầu bảng 3 tầng gộp ô đúng nhãn: «Họ tên», «Mã số BHXH», «Ngày tháng năm sinh», «Giới tính», «Số CCCD/CMND/Hộ chiếu», «Cấp bậc, chức vụ, chức danh nghề, nơi làm việc», «Vị trí việc làm (2)» (4 cột con), «Tiền lương» → «Hệ số/ Mức lương» + «Phụ cấp» (Chức vụ / Thâm niên VK (%) / Thâm niên nghề (%) / Phụ cấp lương / Các khoản bổ sung), «Ngành/nghề nặng nhọc, độc hại» (Ngày bắt đầu / Ngày kết thúc), «Loại và hiệu lực hợp đồng lao động» (5 cột), 2 cột BHXH (xem M17), «Ghi chú».
  - Hàng đánh số 1…27; dòng «Tổng (145 lao động)»; chỗ ký «ĐẠI DIỆN DOANH NGHIỆP, CƠ QUAN, TỔ CHỨC»; chú thích (2).
  - Không có số 0 ở ô thiếu dữ liệu (HĐ lương 0 để trống). Ngày là kiểu ngày thật, định dạng `dd/mm/yyyy`. Tổng người của các sheet = 268 = KPI.
  - Kỳ không có ai: tệp có 1 sheet «Không có dữ liệu».
- **Sổ quản lý lao động**: 13 sheet, 25 cột. Dòng thiếu thông tin tô vàng (`FFF2CC`) ở cột STT và Họ và tên, khớp HDSD. Ghim cột ở D8. Ngày là kiểu ngày thật.
  - Hỏi: «Thiếu thông tin bắt buộc» không tính Số BHXH (xem câu hỏi mở 2).
- **Danh sách ký nhận** (8/3, NV 300.000, QL 500.000): mỗi pháp nhân một sheet. «Tổng tiền» từng sheet bằng tổng cột Mức quà. Tổng các sheet 18,1 tr = API = công thức NV×mức + QL×mức. Không có ngày sinh, không có người thân.
- **Quỹ lương**: nhóm bị che để trống ô (không ghi 0). Dòng Tổng đủ số.
- **Biến động, Hợp đồng lao động, Cơ cấu quản lý, Điều chuyển**: mở được, cột đúng `meta` (xem M18).
- **Chống công thức**: đặt tên / địa chỉ thử mở đầu bằng `=`, `@`, `+` → không ô nào thành công thức (xem M20). Đã trả tên về như cũ.
- Tải qua giao diện (vai B): tệp tải về giữ đúng `department_id` (01/PLI Kế toán ra 25 người, 1 sheet).

## Không phải lỗi (dữ liệu local)
- 30/31 đơn nghỉ đã duyệt (mã `E2E-NP*`) không có dòng `tab_leave_request_line`. Vì vậy «Ngày nghỉ đã duyệt» = 0 và cột ngày nghỉ của Sổ = 0. Migration `cbb45a57ada1` đã bù dòng cho dữ liệu thật; bộ E2E này được chèn sau và thiếu dòng. Nên sửa script tạo bộ E2E.
- Local không có CCCD, mã số thuế, BHXH, ngân hàng, trình độ, nơi làm việc → «Tỷ lệ hồ sơ đủ» 0%, Trình độ và Địa điểm đều «(Chưa gắn)».
- «Chưa được cấp quỹ −95%» là do năm 2025 không có quỹ phép.
- Quỹ lương vai C thấy số lương: đúng thiết kế (lớp chặn là khóa 21).

## Dữ liệu thử đã tạo trên LOCAL — chủ dự án xóa giúp
| Loại | Định danh |
|---|---|
| Vai trò | id 137 `TEST_HR_SENS`, id 138 `TEST_NO_SENS` |
| Tài khoản | id 1462 `test_hr_sens@test.local`, id 1463 `test_no_sens@test.local` |
| Nhân sự | id 1483 `TEST_HR_SENS`, 1484 `TEST_NO_SENS`, 1485 `TEST_PAYROLL_C2` (pháp nhân 2) |
| HĐLĐ đã ký | id 38/39/40 (HDLD013–015, số HĐ `TEST-E2E-*`) — tạo để thử che nhóm < 3 ở Quỹ lương |
| Giao quyền báo cáo | vai trò 137: khóa 6, 7, 8, 17–24; vai trò 138: khóa 6, 19–24 (lý do «e2e kiểm thử 27/10 — xóa sau») |

Lưu ý: 3 nhân sự + 3 HĐ này làm số local đổi (định biên 266 → 269, HĐ đang hiệu lực 2 → 5). Xóa thứ tự: thu hồi quyền báo cáo → tài khoản → HĐ → nhân sự → vai trò.

## Việc kế đề nghị
1. Backend sửa N1 + N2 (kèm bài kiểm thẻ = tổng danh sách); giao diện sửa N3, M1, M2, M7.
2. Agent 2 sửa bài HDSD (M22) rồi chạy lại seed + reindex trên dev.
3. Đối chiếu nhãn cột 26 của 01/PLI với PDF mẫu (M17) trước hạn nộp 05/12.

## Câu hỏi còn mở
1. Phúc lợi: có làm «so với cùng dịp năm trước» (M12) không, hay sửa tài liệu?
2. Sổ quản lý lao động: «Số BHXH» có tính là thông tin bắt buộc không?
3. Có ẩn mục menu Sổ / 01-PLI khỏi người được giao khóa nhưng thiếu quyền nhạy cảm không (M14)?

**Status:** DONE_WITH_CONCERNS
**Summary:** Đã kiểm 11 báo cáo Nhân sự × 3 vai trên local (giao diện, API, Excel, khổ 390px). Không có lỗi chặn; có 3 lỗi Nên sửa (N1 danh sách «đơn chờ quá 3 ngày» không lọc mốc, N2 «Số người có biến động» liệt kê lượt, N3 công tắc «Tính người đang nghỉ» làm hỏng trang với người thiếu quyền) và 22 lỗi nhỏ.
**Concerns/Blockers:** Dữ liệu thử (2 vai trò, 2 tài khoản, 3 nhân sự, 3 HĐ, các quyền báo cáo) còn trên local, chờ xóa. chrome-devtools MCP bận nên dùng Playwright headless. Bài HDSD M22 chưa sửa vì lượt này được giao không sửa.
