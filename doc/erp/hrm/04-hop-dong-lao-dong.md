# Hợp đồng lao động, quyền mặc định theo chức vụ, nhập Excel nhân sự

| | |
|---|---|
| Bản | 1.0 — 23/10/2026 (duoc-CR-673: gom tài liệu đang rải ở `01`, sổ thay đổi và các kế hoạch về một tệp) |
| Giao diện | Chỉ có trên `frontend-v2/` (cổng 8083), menu *Nhân sự* |
| Mã nguồn backend | `modules/labor_contract/` (HĐLĐ) · `modules/employee/position_role_*.py` (quyền theo chức vụ) · `modules/import_tool/employee_import*.py` (nhập Excel) |
| Luật cho trợ lý AI | `.claude/rules/hr-labor-contract-variables.md` · `.claude/rules/hr-employee-profile.md` (hai mục cuối) |
| CR gốc | HĐLĐ: duoc-CR-606, 620, 629, 629b, 630, 632, 633, 640, 643, 652, 659 · Quyền theo chức vụ: duoc-CR-653 · Nhập Excel: duoc-CR-628 |

Tệp này nói **chức năng làm gì và luật nào đã chốt**. Chi tiết từng lượt sửa nằm ở dòng CR tương ứng trong `doc/tai-lieu-ky-thuat/change-log.md`; bẫy khi sửa mã nằm ở tệp luật cho trợ lý AI.

---

## Phần A. Hợp đồng lao động

### A.1. Chức năng này để làm gì

Phòng Nhân sự lập hợp đồng lao động ngay trong hồ sơ của từng người, sinh tệp Word từ **mẫu riêng của từng pháp nhân**, lưu bản đã ký, và được nhắc khi hợp đồng sắp hết hạn. Người lao động tự xem lại hợp đồng của mình ở Trang cá nhân.

### A.2. Màn hình

| Màn | Đường dẫn | Ghi chú |
|---|---|---|
| Tab «Hợp đồng» trong hồ sơ nhân sự | `/hr/employees/:id?tab=labor-contracts` | Lập / sửa / sinh tệp / tải bản ký / đổi trạng thái. Cột Thao tác là một nút «⋯» mở menu chia nhóm Xem · Soạn · Trạng thái · Xóa (duoc-CR-633) |
| Mẫu hợp đồng | `/hr/labor-contract-templates` | Mở ngay trong Nhân sự (duoc-CR-643). Cùng bảng cũng hiện ở *Văn bản ▸ Thiết lập ▸ Thư viện văn bản mẫu* (`/document/settings?tab=templates&kind=labor-contract`) |
| Soạn nội dung mẫu trên web | `/hr/labor-contract-templates/:id/edit` | Trình soạn của phân hệ Văn bản, có khung «Chèn biến» |
| Danh sách biến | `/hr/labor-contract-templates/variables` | Biến hệ thống + biến tùy chỉnh (§A.6) |
| Thẻ «Hợp đồng lao động sắp hết hạn» | Tổng quan Nhân sự | Chỉ dựng khi có `labor_contract.read` |
| «Hợp đồng của tôi» | `/me`, nhóm Hồ sơ | Chỉ hiện khi tài khoản gắn với một hồ sơ nhân sự (§A.8) |

### A.3. Loại hợp đồng và trạng thái

Cả hai là mã số (`core/labor_contract_codes.py`, luật R2). Số đã cấp không đổi, không tái dùng.

| Loại | Mã | Ngày kết thúc |
|---|---|---|
| Thử việc | 1 | Bắt buộc |
| Xác định thời hạn | 2 | Bắt buộc. Trên 36 tháng chỉ **cảnh báo**, không chặn |
| Không xác định thời hạn | 3 | **Cấm** có |
| Khoán việc / dịch vụ | 4 | Bắt buộc |
| Cộng tác viên | 5 | Bắt buộc |
| Khác | 9 | Tùy |

Nút chọn nhanh thời hạn: 12 · 24 · 36 tháng, thử việc 30 · 60 ngày.

| Từ → Đến | Điều kiện |
|---|---|
| Nháp → Đã ký | Bắt buộc ngày ký. **Không** đòi tệp bản ký (đại ca chốt 05/10/2026). Biến bắt buộc còn trống thì chặn (§A.6) |
| Nháp → Đã hủy | Bắt buộc lý do |
| Đã ký → Đã chấm dứt / thanh lý | Ngày chấm dứt ≥ ngày bắt đầu, bắt buộc lý do |
| Còn lại | 409 |

**«Hết hạn» (mã 3) không ghi vào DB.** Đó là trạng thái suy ra = Đã ký + ngày kết thúc < hôm nay (giờ Việt Nam). Luật chuyển trạng thái nằm ở `labor_contract/rules.py`; giao diện chỉ hiển thị `effective_status` / `transitions` do backend trả.

### A.4. Lập hợp đồng và sinh tệp

- Lúc lập, hệ thống **chụp** pháp nhân và phòng ban của người lao động vào hợp đồng. Người đó đổi phòng sau này thì hợp đồng cũ không đổi.
- Trong hộp Lập / Sửa có ô chọn sẵn tệp bản ký (PDF · JPG · PNG ≤ 50 MB, không bắt buộc). Tệp chỉ được tải lên sau khi lưu xong, đi đúng đường `PUT /signed-file` (duoc-CR-632).
- **Sinh tệp** chỉ lấy mẫu của **đúng pháp nhân và đúng loại** của hợp đồng, chạy `docxtpl` trong sandbox. Tải bản sinh đòi quyền `print`.
- Sửa nội dung hợp đồng nháp (lương, ngày, giá trị biến…) thì **tệp đã sinh bị xóa**, phải sinh lại.
- Không ai tự lập hợp đồng cho chính mình.

### A.5. Mẫu hợp đồng

- Mỗi mẫu là một tệp `.docx` có biến dạng `{{ ten_bien }}`, gắn **một pháp nhân + một loại hợp đồng**. Ô chọn và bảng hiện kèm mã pháp nhân vì có pháp nhân trùng tên.
- Lúc tải lên (hoặc lưu từ trình soạn web) mẫu bị kiểm kỹ: biến lạ → 422 kèm tên biến. **Chỉ cho biến đơn**: mọi `{% %}`, bộ lọc, gọi hàm, thuộc tính đều bị chặn (chống treo máy bằng vòng lặp lồng). Cũng chặn macro, liên kết ngoài, đối tượng nhúng, phần XML > 5 MB, quá ~1000 biến.
- Soạn trên web (duoc-CR-606 ②b): giữ lề trái / phải của bản gốc; đầu / chân trang có thể mất (có cảnh báo một lần).
- **Dữ liệu** (duoc-CR-629b bước B, migration `lbrct03`): mẫu HĐLĐ nằm chung bảng `tab_document_template` với `template_kind = 2` (lớp `LaborContractTemplate`). `id` mẫu giữ nguyên nên `tab_labor_contract.template_id` không đổi. Người chỉ có quyền văn bản mẫu (`doc_template`) **không bao giờ thấy** mẫu HĐLĐ. Bảng cũ còn tên `tab_labor_contract_template_bak629`, sẽ bị migration `lbrct04` của lần phát hành sau xóa.
- Quyền: `labor_contract_template`, phạm vi theo pháp nhân.

### A.6. Danh sách biến của mẫu hợp đồng (duoc-CR-630)

API `/api/labor-contract-variables`, bảng `tab_labor_contract_variable`, migration `lbvar01`. Biến dùng chung **toàn hệ thống**, mọi pháp nhân.

- **Hai loại biến.** *Hệ thống* (48 biến mã cứng ở `placeholder_catalog.py`): giá trị lấy từ hồ sơ; chỉ sửa được tên hiển thị, mô tả và «Ẩn khỏi danh sách hướng dẫn» (biến ẩn vẫn dùng được trong mẫu); mã bất biến, không xóa. *Tùy chỉnh*: HR tự thêm, **nhập tay theo từng hợp đồng** ở ô «Thông tin bổ sung cho mẫu» trong hộp Lập / Sửa.
- **Kiểu giá trị** của biến tùy chỉnh: Chữ · Chữ nhiều dòng (xuống dòng thành ngắt dòng Word) · Số (không âm, tối đa 2 số lẻ, in `1.234,5`) · Ngày (in `dd/mm/yyyy`) · Tiền (đồng nguyên 0..10^12, in `15.000.000`; tự có thêm biến `{{ <mã>_bang_chu }}` đọc số thành chữ).
- **Mã biến** `^[a-z][a-z0-9_]{1,39}$`, không `__`, không đuôi `_` hoặc `_bang_chu`, không trùng từ khóa bộ máy mẫu hay biến hệ thống. Tối đa 100 biến tùy chỉnh; mỗi hợp đồng tối đa 100 khóa / 20 000 ký tự giá trị.
- **Mặc định được SAO vào hợp đồng lúc lập** (hộp Lập điền sẵn). Đổi mặc định sau đó KHÔNG đổi hợp đồng đã lập.
- **Bắt buộc** chặn *Sinh tệp* (chỉ biến mà mẫu thật sự dùng) và việc chuyển sang *Đã ký* (422 nêu NHÃN còn thiếu); lưu nháp không bao giờ bị chặn. Khi ký, hợp đồng còn mẫu thì xét biến của mẫu đó; không còn mẫu (chưa sinh, sửa sau khi sinh, ký bằng bản scan) thì xét biến của các mẫu đang dùng của CHÍNH pháp nhân hợp đồng (ưu tiên cùng loại hợp đồng, không có thì mọi loại; không mẫu nào thì không ép). Số 0 là giá trị thật cho kiểu Số / Tiền; chỉ ô để trống mới là «chưa nhập».
- **Ngừng dùng** ≠ xóa. Ngừng dùng: biến mất ở ô nhập và khung «Chèn biến», mẫu mới không nhận được; mẫu cũ đã chứa nó vẫn sửa / sinh được, giá trị đã lưu vẫn in và hiện CHỈ ĐỌC ở hộp Sửa hợp đồng. **Xóa** chỉ được khi không mẫu nào chứa và không hợp đồng nào (kể cả xóa mềm) giữ giá trị → 409 nêu số mẫu / hợp đồng (chỉ liệt kê tên mẫu người xem thấy theo phạm vi + số mẫu còn lại). Biến đang dùng cũng bị khóa mã và kiểu.
- **Quyền.** Xem = `labor_contract_template.read` (ô nhập trong hộp hợp đồng còn mở cho `labor_contract.create/write`). Thêm / sửa (cả nhãn biến hệ thống) = `write`, xóa = `delete`, **và phải có phạm vi «tất cả pháp nhân»** (`variable_access.is_unrestricted`); HR một pháp nhân chỉ xem và dùng.
- **Dữ liệu nhạy cảm.** `custom_values` che khỏi nhật ký request và nhật ký thay đổi như lương; tiêu đề / tóm tắt bản lưu trữ ở Văn bản không chứa giá trị biến.

### A.7. Bản lưu trữ ở phân hệ Văn bản (duoc-CR-629, 640, 659)

Mỗi hợp đồng (`tab_labor_contract`) có cột `document_id` trỏ tới một văn bản loại `HDLD` ở phân hệ Văn bản (0 = chưa có). Cầu nối `labor_contract/document_archive_sync.archive_sync` chạy sau khi lập / sửa / sinh tệp / tải bản ký / chuyển trạng thái / xóa; lỗi chỉ ghi nhật ký, hợp đồng vẫn đi bình thường, sự kiện sau tự lành.

- **Trạng thái:** Nháp → Nháp · Đã ký → Có hiệu lực · Đã chấm dứt → Hết hiệu lực (ngày hết = ngày chấm dứt) · Đã hủy / HĐ xóa mềm → Lưu trữ · hồ sơ nhân sự xóa cứng → văn bản xóa mềm.
- **Tệp:** văn bản giữ BẢN SAO (chép byte sang `tab_file` riêng, so `sha256`) của .docx đã sinh và bản đã ký; sinh lại / thay bản ký thì bản sao cũ bị gỡ. Văn bản là **gương** của hợp đồng, không lưu lịch sử mọi bản ký. Bản sao do đồng bộ tạo mang dấu `tab_file_link.doc_type='hdld_sync'`; đồng bộ **chỉ** đụng các bản sao đó, tệp người dùng tự tải thêm không bị xóa (duoc-CR-640).
- **Tiêu đề / tóm tắt** chỉ có số hợp đồng + tên người + loại + ngày + trạng thái — KHÔNG lương, phụ cấp, CCCD, tài khoản.
- **Quyền đọc** chỉ theo `labor_contract.read` trong phạm vi (xem `.claude/rules/document-folders-search.md`). Vai trò `hr_profile` được seed thêm `document.read` + `document.write` phạm vi «Của tôi» để mở danh sách / tải tệp (hệ đang chạy phải tick tay hoặc `SEED_FORCE_SYNC` một lần).
- **Sửa được** (duoc-CR-640) với người có `labor_contract.write` phủ hợp đồng: thông tin chung, nội dung bản nháp, phiên bản, tệp mềm, thư mục. Trường do đồng bộ sở hữu (tên, tóm tắt, ngày hiệu lực, loại, sổ, pháp nhân, phòng, chủ) → 409. Vẫn chặn 409 mọi thao tác đẩy văn bản tới người khác: chia sẻ, sao chép, trích, quan hệ, gửi duyệt, ban hành, cấp số, ký, vào sổ.
- **«Ban hành» (duoc-CR-659):** khi hợp đồng còn Nháp, trang văn bản lưu trữ chỉ có MỘT nút «Ban hành» = **ký hợp đồng gốc** (qua `/api/labor-contracts/{id}/transition`, Nháp → Đã ký, ngày ký = hôm nay); đồng bộ sau đó đưa văn bản sang «Có hiệu lực». Nút hiện khi `/permissions` trả `can_issue_archive` (HĐ chưa xóa, đang Nháp, người xem ghi được HĐ). Văn bản vẫn không có trạng thái riêng.
- **Bù dữ liệu cũ:** `docker compose exec -T api python scripts/backfill_hdld_van_ban_luu_tru.py --dry-run` rồi chạy thật (idempotent); rollback: `--soft-delete-all`.

### A.8. Cảnh báo sắp hết hạn (duoc-CR-620)

Một nguồn `labor_contract/expiry_service.find_expiring` cho ba chỗ: **chuông** (`/api/alerts`), **tab Việc cần làm** (chỗ duy nhất ẩn được dòng chuông) và **thẻ trên Tổng quan Nhân sự** (`GET /api/labor-contracts/expiring`).

- Báo khi hợp đồng **Đã ký**, có ngày kết thúc, chưa xóa mềm, trong phạm vi người xem, và hết hạn trong **30 ngày** tới hoặc **đã quá hạn** (người vẫn đi làm mà hết hợp đồng thì báo tới khi xử lý).
- **Đỏ** khi còn ≤ **15 ngày** (mốc báo trước của Điều 45 BLLĐ 2019) hoặc đã quá hạn; còn lại vàng. Mức vàng đã ẩn sẽ nổi lại khi sang đỏ.
- **Không báo** khi người đó đã có hợp đồng **nối tiếp** bắt đầu sau (Đã ký: luôn che; Nháp: chỉ che khi hợp đồng cũ CHƯA hết hạn) hoặc đã nghỉ việc.
- Tính tại chỗ lúc mở, không có job chạy nền, không gửi email. Không trả lương.

### A.9. Hợp đồng của tôi (duoc-CR-652)

Ở Trang cá nhân `/me`, người lao động thấy bảng chỉ xem các hợp đồng **của chính mình** ở trạng thái Đã ký / Đã chấm dứt (kể cả Hết hạn): số HĐ, loại, hiệu lực, chức danh, trạng thái, lương cơ bản; tải bản mềm (.docx) hoặc bản đã ký nếu có.

- API `GET /api/me/labor-contracts`, `/{id}/document`, `/{id}/signed-file`. Hồ sơ nhân sự lấy **từ token**, không nhận id từ ngoài; HĐ của người khác / nháp / đã hủy → 404.
- Không trả `custom_values`, ghi chú, id tệp; che lương trong nhật ký. Không có khóa quyền mới.
- Ở phân hệ Văn bản, chủ hợp đồng **đọc được** bản lưu trữ khi HĐ đã ký / chấm dứt (không sửa, xóa, chia sẻ). Mở bản lưu trữ ở đó còn cần `document.read` của vai trò; tải tệp ở Trang cá nhân thì không cần.

### A.10. Quyền

| Khóa | Dùng cho | Phạm vi lọc theo |
|---|---|---|
| `labor_contract` | Hợp đồng: `read` xem / tải bản ký · `create` lập · `write` sửa, sinh tệp, tải bản ký, chuyển trạng thái · `delete` xóa mềm · `print` tải bản sinh .docx | pháp nhân · phòng ban · chính mình (`SCOPE_FIELDS`). Cố ý **không** có `owner`: có nó thì phạm vi «own» lập được HĐ cho nhân sự công ty khác rồi tải CCCD + số tài khoản |
| `labor_contract_template` | Mẫu hợp đồng và danh sách biến | pháp nhân. Ghi danh sách biến đòi thêm phạm vi «tất cả pháp nhân» |

Cả hai khóa nằm trong `_SYS_ENTITIES` và được seed cho vai trò `hr_profile`. Lương và `custom_values` bị che ở nhật ký thay đổi và nhật ký request.

---

## Phần B. Quyền mặc định theo chức vụ (duoc-CR-653)

### B.1. Chức năng này để làm gì

Người mới vào công ty có tài khoản là **làm việc được ngay**, không phải chờ quản trị gán từng vai trò. Mỗi chức vụ khai sẵn một **gói vai trò**; tài khoản của người giữ chức vụ đó được hệ thống tự cấp gói, đổi chức vụ thì gói tự đổi theo.

### B.2. Cách dùng

- Màn: *Nhân sự ▸ Danh mục ▸ Chức vụ* → mở một chức vụ → tab **«Quyền mặc định»** (`/hr/job-positions/:id`). Chọn các vai trò của gói rồi lưu.
- **Lưu gói không đổi quyền của ai.** Muốn áp cho những người đang giữ chức vụ thì bấm **«Áp lại cho người đang giữ chức vụ»** (có hộp xác nhận kèm số người).
- Từ lúc đó, hệ thống tự cấp gói khi: cấp tài khoản cho nhân sự, đổi chức vụ ở hồ sơ, nhập Excel, hoàn tác lô nhập, áp quá trình công tác, mở khóa tài khoản. Tài khoản bị khóa hoặc hồ sơ nghỉ việc thì bỏ qua.
- Ở *Quản trị ▸ Phân quyền tài khoản*, vai trò được cấp theo gói hiện nhãn **«Theo chức vụ: …»**.

### B.3. Luật đã chốt

- **Gói chỉ là danh sách vai trò, không có bậc phạm vi.** Bậc own / dept / company / all nằm ở cấu hình của từng vai trò. Muốn «Trưởng phòng xem cả phòng» thì chọn vai trò đã cấu hình bậc đó.
- **Đổi chức vụ X → Y chỉ gỡ những vai trò hệ thống cấp theo X.** Vai trò quản trị gán tay giữ nguyên. Dấu nằm ở `tab_user_role.granted_by_position_id` (0 = gán tay, > 0 = cấp theo chức vụ đó).
- **Cấm tự cấp cho chính mình.** Người không phải quản trị đổi chức vụ của chính mình thì không được nhận gói (chặn đường «HR tự nâng quyền»). Thu hồi vẫn chạy.
- **Không leo thang.** Người không phải quản trị chỉ cấp được vai trò mà mình có đủ quyền; vai trò còn lại bị bỏ qua và ghi nhật ký.
- **Vai trò cấm vào gói:** quản trị (`admin`) và vai trò có quyền ghi / tạo / xóa Vai trò hoặc Tài khoản. Người đang giữ một chức vụ không được thêm vai trò vào gói của chính chức vụ đó.
- Sửa gói cần `role.write` (không phải `job_position.write`). Xóa một vai trò đang nằm trong gói bị chặn.

### B.4. Hạn chế đã biết

- **Bỏ một vai trò của gói cho riêng một người** thì phải sửa gói hoặc đổi chức vụ của họ. Bỏ tick ở Phân quyền tài khoản sẽ bị «Áp lại» hoặc lần đổi chức vụ sau cấp lại.
- **Cache quyền 60 giây theo từng tiến trình.** Vai trò vừa thu hồi có thể còn tác dụng tối đa một phút ở worker khác.

### B.5. Đưa lên hệ đang chạy

1. Kiểm dòng trùng `tab_user_role` trước khi chạy migration `jobposrole01` (migration dọn trùng, giữ dòng gán tay).
2. Chạy script đề xuất gói từ dữ liệu hiện có: `backend/scripts/de_xuat_quyen_theo_chuc_vu.py` (mặc định chỉ xem; chức vụ ≥ 3 người giữ, ngưỡng 60%). Duyệt kết quả, rồi `--apply --yes` — script chỉ **thêm gói**, không cấp cho ai.
3. Vào từng chức vụ bấm «Áp lại».

---

## Phần C. Nhập Excel nhân sự (duoc-CR-628)

### C.1. Chức năng này để làm gì

Phòng Nhân sự tạo mới hoặc cập nhật hàng loạt hồ sơ bằng một tệp Excel, **xem trước kết quả trước khi ghi**, và **hoàn tác** được cả lô nếu nhập sai. Thay cho Import CSV cũ (nay trả 410).

### C.2. Cách dùng

1. Ở *Nhân sự ▸ Danh sách* (`/hr/employees`) bấm **«Nhập Excel»**, tải tệp mẫu (có ghi chú từng cột).
2. Điền tệp, tải lên → **chạy thử**: hệ thống báo từng dòng sẽ tạo / sửa / lỗi, chưa ghi gì.
3. Bấm **ghi thật**. Mỗi bản chạy thử chỉ ghi thật được **một lần** (409 nếu đã có lô ghi thật cùng tệp).
4. Sai thì mở chi tiết lô → **hoàn tác**.

Đi qua khung chung `import_tool` (adapter `EMPLOYEE`). Khung hook: `doc/erp/nen-tang/16-quan-ly-import-export-v2.md` §9.3.

### C.3. Luật của tệp

- Khoảng **38 cột**, kể cả nhóm nhạy cảm. Tham chiếu (pháp nhân, phòng ban, chức vụ…) ghi theo **mã**.
- **Ô trống = giữ nguyên.** Muốn xóa giá trị thì ghi `__/empty_value/__` (không xóa được Họ tên, Trạng thái, Đang dùng).
- Giá trị lạ ở ô mã số / trạng thái / ngày là **lỗi dòng**, hệ thống không đoán.
- Thiếu Mã NV thì hệ thống tự sinh. Một Mã NV chỉ được xuất hiện **một lần** trong tệp (không phân biệt hoa / thường).
- Tối đa **2000 dòng**. **Không xóa** nhân sự qua tệp.
- Cột «Ngày vào làm» (`hire_date`) có trong tệp — đây là cách nhanh nhất để nhập bù ngày vào làm cho hồ sơ cũ (xem `02-nghi-phep.md` §10: thiếu ngày này thì thâm niên phép tính bằng 0).

### C.4. Quyền và dữ liệu nhạy cảm

- Gác kép: `import` × `employee`. Tạo lô / ghi thật cần `import.create` + `employee.create` / `write`; hoàn tác lô có tạo mới cần thêm `employee.delete`.
- **Cột nhạy cảm cần `employee_sensitive.write`.** Thiếu quyền thì cả cột bị bỏ qua kèm một cảnh báo, các cột khác vẫn ghi.
- Tệp gốc của lô và bản chụp hoàn tác chứa CCCD / số tài khoản **bản rõ** → tải tệp gốc đòi `employee_sensitive.read`. Nhật ký và thông báo lỗi không bao giờ chứa giá trị cột nhạy cảm.
- Mỗi dòng đi qua chốt phạm vi trước và sau khi ghi: không đưa được người ra khỏi tầm của mình, không tự đổi phòng của chính mình.
- Vai trò cũ phải **tick tay** `import.read/create` + `employee.create/write` + `employee_sensitive.write` (seed không tự đổi trên hệ đang chạy). Lưu ý `import.read` là quyền toàn cục: ai có nó thấy cả danh sách lô của Thu mua, Kho.

### C.5. Hoàn tác

- Bản chụp chỉ giữ các cột đã đổi `[cũ, mới]` (kèm tập phòng ban trước / sau). Cột nào đã bị sửa tiếp sau lô thì **từ chối cả lượt hoàn tác**, nêu mã + tên cột.
- Ai đủ quyền trong phạm vi cũng hoàn tác được, không riêng người tạo lô.
- Hồ sơ **mới** của lô chỉ bị xóa khi chưa có dữ liệu con (liên hệ, người thân, quá trình công tác, HĐLĐ, kiêm nhiệm) và chưa bị sửa sau lô.
- Hoàn tác về trạng thái «nghỉ việc» thì khóa lại tài khoản; hoàn tác **không** mở lại tài khoản đã khóa vì nghỉ việc.

### C.6. Hạn chế đã biết

- **Bản chụp hoàn tác giữ vĩnh viễn**, chưa có việc dọn sau N ngày (chủ dự án chốt hoãn) — đây là chỗ CCCD / số tài khoản bản rõ còn nằm lại.
- Ghi thật giữ khóa sinh mã NV tới hết lô: trong lúc lô chạy, người khác tạo nhân sự bằng tay sẽ phải chờ. Muốn nhẹ hơn thì điền sẵn Mã NV trong tệp.
- Người bị đổi phạm vi bởi lô nhập có thể còn thấy phạm vi cũ tối đa 60 giây (cache quyền).
