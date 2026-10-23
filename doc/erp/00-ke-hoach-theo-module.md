# KẾ HOẠCH CÒN LẠI THEO MODULE — DEGO ERP

**Bản 1.0 — 22/10/2026.** Thay toàn bộ các kế hoạch cũ đã xóa ngày 22/10/2026 (`01` ngắn hạn, `02` dài hạn, `04` danh mục chờ, `06` lộ trình nền tảng và HRM, `08` task củng cố, `10` báo cáo WorkHub, `11` đa pháp nhân, `13` đối chiếu màn v1↔v2, `19` việc còn lại). Mọi mục *chưa làm* trong các tệp đó đã được gom về đây, rồi **kiểm lại trong mã nguồn** trên nhánh `erp-v2`: mục nào mã đã có thì bỏ khỏi kế hoạch và ghi vào dòng *Đã có* của module.

Cách đọc:
- Mỗi module có ba phase: **Phase 1 — làm tiếp** (lỗ bảo mật, thứ đang chặn người dùng thật, nợ nhỏ rẻ), **Phase 2** (tính năng có giá trị rõ), **Phase 3 — khi cần** (tồn đọng, chờ nhu cầu).
- Mã việc: `<module><phase>-<số>`, ví dụ `HR1-2` là việc thứ hai của Phase 1 module Nhân sự. Cột **Nguồn** trỏ về tài liệu chi tiết; nguồn ghi *(bản cũ)* là tệp đã xóa, đọc lại trong lịch sử git.
- Mục ghi *(cần kiểm lại)* là chỗ mã chưa đủ để kết luận đã làm hay chưa.
- Kế hoạch này không đặt mốc ngày. Khi nhận việc vẫn cấp số CR như thường và ghi sổ nhật ký task.

Luật đã chốt, đừng mở lại: **không làm chấm công, không làm lương** (16/10/2026) · **bỏ tầng đa pháp nhân cho danh mục**, chia theo phòng ban (16/09/2026) · **bot Telegram đóng băng tính năng**, MCP là đường chính cho AI (17/10/2026) · **thu mua giữ nguyên luồng duyệt hiện tại** (22/10/2026).

---

## 0. Tổng quan

| # | Module | Phase 1 tập trung vào | Câu chặn lớn nhất |
|---|---|---|---|
| 1 | Nền tảng ERP v2 | Quyền xuất dữ liệu, CI tối thiểu, gắn công ty cho nhân sự, thử phục hồi sao lưu | Tắt `frontend/` cũ khi nào |
| 2 | Thu mua | Thông báo chờ duyệt ĐMH và YCTT không tới người duyệt | — |
| 3 | Nhập khẩu, hải quan | Nạp lại bài HDSD Tra cứu thị trường | Mở lại phân hệ Hồ sơ nhập khẩu khi nào |
| 4 | Bảo mật | BM-023, BM-021, BM-019, cập nhật sổ | 2FA cho HR và quản trị |
| 5 | Nhân sự (HRM) | Tick lại quyền Xuất khi deploy CR-660, luồng duyệt nghỉ phép cho công ty khác, nhập bù ngày vào làm | — |
| 6 | Văn thư và văn bản | Lớp mức mật văn bản | Chủ nghiệp vụ Pháp chế / Văn thư (C3) và 17 câu A1–C5 |
| 7 | Duyệt dấu, đặt xe, đồng bộ app cũ | Nạp lịch sử app đặt xe cũ | Ba quyết định A/B/C, ngày tắt app cũ |
| 8 | Công việc / dự án | Nối chuông, đóng mốc MVP | Đội nào dùng thử |
| 9 | Diễn đàn | Gán quản trị diễn đàn, đóng F6 | D-Q4…D-Q6 |
| 10 | Điểm cà phê / POS365 | Dọn cửa hàng, thí điểm 1 tháng | Mức điểm 4 cấp, âm điểm, thuế |
| 11 | AI | Đưa D1 lên prod, công cụ năng lực (A1), kế hoạch đề xuất (A2), khóa model riêng | Phòng thử đầu tiên |
| 12 | Sản xuất | Trả lời 15 câu, rà sổ kho, bảng sản phẩm cha | B1: chỉ số lượng hay làm cả giá thành |
| 13 | Kế toán | Khảo sát phần mềm kế toán đang dùng | Nối hay tự viết (C7) |
| 14 | Khác | — | CRM trước hay Kế toán trước |

## 0.1 Thứ tự ưu tiên toàn hệ — đợt làm tiếp theo

Gom từ Phase 1 của các module, xếp theo rủi ro trước, giá trị sau:

1. **Lỗ bảo mật đang có thật trên prod:** `AN1-1` (giải mã bí mật hỏng im lặng — sao lưu có thể chết không ai biết), `AN1-3` (`/api/uploads` không kiểm quyền), `HR1-1` + `NT1-1` (xuất CSV nhân sự và danh mục chỉ đòi quyền đọc), `AN1-2` (header bảo mật nginx).
2. **Người dùng thật đang vướng:** `TM1-1` (ĐMH, YCTT không báo người duyệt), `HR1-3` (công ty khác chưa có chuông duyệt nghỉ phép).
3. **Đợt prod tiếp theo:** `AI1-1` (D1 của anh Dược đang nằm trên dev), kèm các bản vá ở mục 1–2.
4. **AI chia việc:** `AI1-2`, `AI1-3` sau khi chốt phòng thử.
5. **Nền vận hành:** `NT1-2` (CI tối thiểu), `NT1-6` (thử phục hồi sao lưu), `NT1-3` (gắn công ty cho nhân sự).
6. Còn lại của Phase 1 các module, rồi mới sang Phase 2.

## 0.2 Câu chờ đại ca / ban lãnh đạo quyết (chặn nhiều việc nhất)

- **Sản xuất B1** — bản đầu chỉ quản lý số lượng hay làm cả giá thành (chặn cả module Sản xuất và một phần Kế toán).
- **Văn thư C3** — ai là chủ nghiệp vụ Pháp chế / Văn thư; thiếu người thì phase nạp dữ liệu thật đứng. Kèm 17 câu A1–C5.
- **AI** — phòng thử đầu tiên cho AI chia việc (đề nghị: Thu mua), khóa model riêng cho prod.
- **Duyệt dấu A/B/C** và ngày tắt app đặt xe cũ.
- **Điểm cà phê** — mức điểm 4 cấp, có cho âm điểm, xử lý thuế TNCN.
- **Nền tảng** — ngày tắt giao diện cũ `frontend/`; có dùng cây phòng ban (`parent`) hay giữ một cấp phẳng.

Chi tiết câu chờ của từng module nằm cuối mục module đó.

---

## 1. Nền tảng ERP v2

**Đã có:** Vỏ ERP v2 chạy dev/prod, trục phòng ban thay đa pháp nhân (bỏ 16/09), xóa mềm dùng chung (SoftDeleteMixin), nhật ký hệ thống P6 trên prod. Màn `/system/logs` đã gộp theo `request_id` (CR-312 P5). Nhập dữ liệu có luồng chạy thử rồi ghi thật từ đúng tệp đó (KT-3), adapter cho công ty, phòng ban, nhân sự, NCC, sản phẩm, ĐVT, nhóm hàng, kho, xe, tài xế, loại dấu. Năm màn Sản xuất đã có lọc nhanh và sắp xếp; `list_suppliers` không còn đè sắp xếp. Celery chạy prod với sao lưu R2 và các việc dọn dẹp theo lịch.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| NT1-1 | Đ-13c: thêm action `import`, đổi quyền xuất `read` sang `export`, áp `apply_scope` cho 3 export CSV viết tay (product, supplier, department; hiện `/export/csv` vẫn gác `read`) | Ma trận quyền có cột Nhập/Xuất; ai chỉ có `read` mất nút xuất; CSV chỉ ra dòng trong phạm vi | `doc/erp/nen-tang/16-quan-ly-import-export-v2.md` §9 |
| NT1-2 | CI tối thiểu: DB trống chạy đủ migration + chạy test mỗi lần đẩy (repo chưa có `.github/workflows`) | Mỗi lần đẩy `erp-v2` có kết quả xanh/đỏ | doc cũ 19 §6 |
| NT1-3 | Gắn công ty cho nhân sự (hầu hết `company_id=0`) để lọc công nợ, nhập kho theo công ty chạy đúng — việc vận hành | Lọc theo công ty ra đúng số trên dev và prod | doc cũ 13 |
| NT1-4 | Nợ nhỏ Thu mua phía backend: ghi *Tên trên hóa đơn* ĐMH lúc lưu; N-008 báo cáo mua hàng gom theo id phòng thay vì TÊN phòng | Đổi tên phòng không làm vỡ báo cáo; ĐMH lưu xong có sẵn tên hóa đơn | doc cũ 13 |
| NT1-5 | NF-20: gác quyền phía giao diện cho các route `/print/...` (mới có trang in theo NCC tự gác `supplier:read`) | Người không có quyền in mở thẳng đường dẫn thấy thông báo, không thấy trang trắng lỗi | doc cũ 13 §NF |
| NT1-6 | Thử phục hồi một bản sao lưu R2 định kỳ (đi cùng AN1-1) | Có biên bản phục hồi thành công ít nhất mỗi quý | doc cũ 19 §6 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| NT2-1 | Đ-13d/13e còn lại: adapter nhập hợp đồng, tồn/công nợ đầu kỳ; thêm hợp đồng, thương hiệu vào registry xuất; nút Nhập/Xuất trên `CrudListPage` theo `can('import'/'export')` (chưa có) | Màn danh mục hiện nút đúng quyền, dẫn về batch | `doc/erp/nen-tang/16-quan-ly-import-export-v2.md` §9.1, §9.2 |
| NT2-2 | **XONG mã, chờ rà — kh-NT2-2, 22/10** (nhánh agent3/kh-NT2-2, chưa lên erp-v2). Chip nhanh trên 4 màn Thu mua theo doc 14, A2 rà đạt | Bấm một chip ra đúng danh sách | `doc/erp/nen-tang/14-filter-sort-man-danh-sach-v2.md` |
| NT2-3 | Nhóm UI dùng chung: NF-01 thùng rác (màn khôi phục trên nền xóa mềm); NF-02 bộ lọc đã lưu (mới có ở Tra cứu thị trường, nhân rộng qua `user_preference`); NF-09 thao tác hàng loạt (xóa hàng loạt `core/bulk_delete.py` đã có ở 5 module, còn duyệt/gán/xuất hàng loạt — cần kiểm lại phạm vi); NF-03 tìm toàn cục | Mỗi NF có màn chạy trên dev, dùng chung cho mọi danh sách | doc cũ 13 §NF |
| NT2-4 | NF-07 khóa chứng từ Thu mua sau duyệt; NF-06 cấp số cấu hình được + DB9 gom đánh số (mã đang sinh rải ở `core/utils.py`, `survey_request`, `ticket`...) | Một bộ sinh số chung, cấu hình được tiền tố; phiếu đã duyệt không sửa được trừ khi mở lại có dấu vết | doc cũ 13 §NF, doc cũ 06 DB9 |
| NT2-5 | Celery phần còn lại: đẩy chuông/web push qua worker, cảnh báo nghiệp vụ theo lịch, NF-18 thư tổng hợp định kỳ, xuất nền (đã có: sao lưu, dọn dẹp, gửi thư, nhập nền) | Các việc trên chạy bằng beat, có nhật ký lỗi | doc cũ 11 |
| NT2-6 | Phạm vi đợt sau: `purchase_history` chưa `apply_scope` (đang cố ý: ai có `supplier.read` thấy hết), `report.compute` chưa nhận user, survey chỉ có chiều owner, contract thiếu chiều phòng; báo cáo tổng + hoàn thiện quyền P9 | Mỗi bảng có SCOPE_FIELDS đủ chiều; bài kiểm phạm vi xanh | `doc/erp/nen-tang/12-ke-hoach-erp-v2-da-phap-nhan.md` §3 |
| NT2-7 | Hạ tầng: giám sát + cảnh báo; deploy một lệnh (cần kiểm lại — script đang nằm ngoài repo ở `D:/vps_deploy`); đưa script đồng bộ môi trường vào repo | Máy chủ chết có cảnh báo; deploy dev/prod bằng một lệnh trong repo | doc cũ 19 §6 |
| NT2-8 | NF-17 màn lỗi/tác vụ nền; NF-22 biểu đồ cho dashboard Tồn kho | Quản trị thấy tác vụ hỏng; dashboard Tồn kho có biểu đồ | doc cũ 13 §NF |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| NT3-1 | Tắt `frontend/` cũ: đổi `FRONTEND_URL`, trỏ tên miền sang v2 (không còn chặn) | Người dùng chỉ vào v2; liên kết trong thư/chuông mở v2 | doc cũ 13 Đ-15, doc cũ 19 §6 |
| NT3-2 | Lớp dùng chung (`core/errors`, deps, repository, base_service, viết lại `make_crud_router`); bộ đệm quyền qua Redis (chưa có) | Module mới dùng lớp chung; đo được giảm truy vấn quyền | doc cũ 06 |
| NT3-3 | NF-08 tags, NF-16 trường tùy biến, NF-19 sửa mẫu in trên giao diện | Có người dùng thật yêu cầu | doc cũ 13 §NF |
| NT3-4 | Webhook ra/vào, khóa API, API `/v1`, tài liệu đối tác | Chờ C4 | doc cũ 19 |
| NT3-5 | DB6 bảng sản phẩm cha (nền BOM), DB7 từ điển dữ liệu tự sinh | Khi mở BOM Sản xuất | doc cũ 06 |
| NT3-6 | Rà truy vấn chậm, gộp migration, kiểm thử tải | Có số đo trước/sau | doc cũ 19 §6 |

**Câu chờ quyết:**
- Ngày tắt `frontend/` cũ — đại ca.
- C4 tích hợp ngoài nào làm đầu tiên — đại ca.
- C5 có quản lý vị trí kho, lô, hạn dùng không — đại ca + kho.
- Có dùng cây phòng ban (`parent`) cho phạm vi và báo cáo không — đại ca.
- `purchase_history` có cần lọc theo phạm vi không, hay giữ ai có quyền NCC thấy hết — Agent 1 đề xuất, đại ca chốt.

## 2. Thu mua

**Đã có:** Luồng YCBG, YCMH, ĐMH, YCTT, công nợ chạy prod; phòng tự mua bao-CR-414 trên prod, bộ AGC dùng phòng tự mua. Sổ tiền treo có cấn trừ (CR-268) và hoàn tiền. Cụm phương án YCMH bao-CR-310 đợt 2–4 đã có (màn Xử lý phương án, gom ĐMH từ phương án chốt, bản in theo NCC tự gác quyền, N-17), nằm sau công tắc `pr_options_enabled` mặc định tắt. Phiếu in ĐMH/YCMH lấy pháp nhân của chứng từ.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| TM1-1 | ĐMH và YCTT không thấy thông báo chờ duyệt (phát hiện 21/10). Mã đã có `po_submitted`/`pay_submitted` gửi người có quyền duyệt toàn hệ; cần tìm chỗ rơi (phòng tự mua, hộp *Việc chờ duyệt*?) (cần kiểm lại) | Người duyệt ĐMH/YCTT nhận chuông và thấy phiếu ở hộp chờ duyệt, kể cả phòng tự mua | ghi nhận 21/10 |
| TM1-2 | Phân công người mua theo phân loại cho phòng tự mua AGC — việc vận hành | Phiếu AGC tự về đúng người mua | `doc/erp/thu-mua/` (CR-414) |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| TM2-1 | Báo cáo thực hiện YCBG: **nhớ gấp/mở XONG mã, chờ rà — kh-TM2-1, 22/10** (nhánh agent3/kh-TM2-1); đính kèm tệp thật, nhắc hạn, quản lý mẫu chuyển sang kh-TM2-1-may-chu (anh Dược) | Bốn ý chạy trên dev, có HDSD | `doc/erp/thu-mua/18-bao-cao-thuc-hien-ycbg.md` |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| TM3-1 | Chuyển 5 luồng duyệt Thu mua sang bộ máy duyệt chung (tùy chọn; đại ca 22/10 dặn giữ nguyên) | Chỉ làm khi đại ca mở lại | doc cũ 13 |

**Câu chờ quyết:**
- Bật công tắc phương án YCMH trên prod khi nào — đại ca.
- Có chuyển luồng duyệt Thu mua sang bộ máy chung không — đại ca (hiện: giữ nguyên).

## 3. Nhập khẩu, hải quan, tra cứu thị trường

**Đã có:** Tra cứu thị trường HQ1–HQ5 và cụm yêu cầu chị Mi lên prod 01/10, có bộ lọc đã lưu. Chi phí thu mua và giá ba giai đoạn (Dự toán, Tạm tính, Quyết toán) trên ĐMH nhập khẩu (bao-CR-453) chạy prod. HQ6 P-01, P-03, P-04 (bảng ngưỡng NĐ 24, tra nghĩa vụ, thuế suất) đã có mã.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| NK1-1 | HQ5: chạy lại seed bài HDSD mục IX (`backend/scripts/seed_help_customs_prices.py`, bài đã viết lại theo A-05…A-08) rồi nạp lại chỉ mục RAG (cần kiểm lại trên dev/prod) | Bài mục IX trên Trung tâm trợ giúp khớp tool hiện tại | `doc/erp/hai-quan/03-lo-trinh-phase.md` HQ5 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| NK2-1 | HQ6 P-02 cảnh báo tồn kho chạm ngưỡng: dựng cầu nối vật tư (VTBB) với hoạt chất, mở lại ranh giới *không nối tồn kho* | Tồn kho chạm ngưỡng thì có cảnh báo kèm căn cứ pháp lý | `doc/erp/hai-quan/03-lo-trinh-phase.md` HQ6 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| NK3-1 | Phân hệ Hồ sơ và tiến độ nhập khẩu Đ1–Đ7 (đang PENDING); mở lại thì chạy checklist §14 | Đại ca mở lại | `doc/erp/nhap-khau/01-danh-sach-tinh-nang.md` §14 |

**Câu chờ quyết:**
- Q2 nạp bao lâu một lần, mỗi lần phủ khoảng nào — phòng Thu mua.
- Q4 có lấy được dữ liệu các năm trước không — phòng Thu mua.
- Q6 GTT02 có xuất kèm số tờ khai không — phòng Thu mua.
- Danh mục BVTV có được dùng và cập nhật định kỳ không; ai cập nhật bảng ngưỡng và biểu thuế hằng năm — đại ca chỉ định người.

## 4. Bảo mật

**Đã có:** Cụm tải tệp lên BM-025..031 (bao-CR-408) đã vào `main` ở 7086a4d0. BM-022 CORS đã đo sạch; BM-024 đã tách khóa dev khỏi prod. `nginx.erp.prod.conf` đã có X-Frame-Options và CSP `frame-ancestors`. Mật khẩu bỏ luật chữ+số (bao-CR-653).

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| AN1-1 | **XONG — bao-CR-655 (22/10/2026), chờ deploy.** BM-023 giải mã bí mật hỏng im lặng: `_decrypt` trong `core/app_settings.py` vẫn nuốt mọi lỗi trả chuỗi rỗng — nguy cơ sao lưu R2 chết không ai biết. ƯU TIÊN | Ba trạng thái (chưa có, đọc tốt, đọc hỏng) cho ba kết quả khác nhau; hỏng thì ghi lỗi và báo quản trị; bài `test_giai_ma_hong_thi_bao_thanh_tieng` xanh | `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md` BM-023 |
| AN1-2 | **XONG — bao-CR-655 (22/10/2026), chờ deploy.** BM-019 phần còn lại: thêm HSTS, `nosniff`, `Referrer-Policy` cho `nginx.erp.prod.conf`; `nginx.prod.conf` (thumua) chưa có header bảo mật nào | Đo header trên prod đủ bốn loại cho cả hai tên miền | `so-ghi-nhan-loi-bao-mat.md` BM-019 |
| AN1-3 | **XONG — bao-CR-655 (22/10/2026), chờ deploy.** BM-021: `/api/uploads` vẫn gắn `StaticFiles` không kiểm quyền (`backend/app/main.py:192`) — gỡ mount hoặc đặt sau kiểm quyền | Bài `test_uploads_khong_lo_tep_cho_nguoi_la` xanh | `so-ghi-nhan-loi-bao-mat.md` BM-021 |
| AN1-4 | **XONG — bao-CR-655 (22/10/2026), chờ deploy.** Cập nhật sổ: BM-025..031 còn ghi *chưa commit* trong khi đã lên `main` 7086a4d0; BM-013 ghi *chấp nhận* (lỗ đã đóng ở `tab_change_log`) | Sổ khớp trạng thái thật | `so-ghi-nhan-loi-bao-mat.md` |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| AN2-1 | BM-020 trần tần suất nghiệp vụ: đo số người dùng chung IP (NAT) trước, rồi bật `default_limits` | Bài `test_tran_tan_suat_co_hieu_luc` ra 429; không chặn nhầm văn phòng dùng chung IP | `so-ghi-nhan-loi-bao-mat.md` BM-020 |
| AN2-2 | BM-030(3) chốt dung lượng trước khi nhận hết thân request; vá nốt BM-003 (phiên phía máy chủ P3) và BM-006 | Tệp quá trần bị chặn sớm; BM-003, BM-006 chuyển *đã vá* | `so-ghi-nhan-loi-bao-mat.md` BM-003, BM-006, BM-030 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| AN3-1 | NFR: lưu nhật ký 5 năm; mã hóa tệp lưu trữ | Chính sách lưu trữ chạy, có đo dung lượng | doc cũ 19 NFR |

**Câu chờ quyết:**
- 2FA bắt buộc cho HR và quản trị không — mâu thuẫn với BM-017 đang chấp nhận rủi ro — đại ca.
- Ghi BM-013 thành *chấp nhận* chính thức — Agent 1 đề xuất, đại ca gật.

---

## 5. Nhân sự (HRM)

**Đã có:** Hồ sơ ~38 trường, nhóm nhạy cảm `employee_sensitive`, chức vụ, quá trình công tác, nhập Excel có hoàn tác, quyền mặc định theo chức vụ (duoc-CR-653), hồ sơ cách làm việc (duoc-CR-641..657). Hợp đồng lao động theo mẫu Word từng pháp nhân, nhân viên tự xem *Hợp đồng của tôi* (duoc-CR-606..652). Nghỉ phép đủ bộ (đính kèm, bàn giao, báo cáo, lịch làm việc 4 cấp); bộ máy duyệt nghỉ phép đã bật trên prod, AGC có luồng riêng từ 21/10. Cờ *Bắt buộc đính kèm* của loại nghỉ chặn lúc gửi duyệt (duoc-CR-661, HR1-2). Kiểm việc duyệt đang treo trước khi khóa tài khoản người nghỉ (duoc-CR-665, HR1-4). Bảng đối chiếu trước / sau kết sổ phép (duoc-CR-664, HR2-3). Sơ đồ tổ chức vẽ từ dữ liệu (duoc-CR-669, V2-6 của HR2-5). Tài liệu HĐLĐ, quyền theo chức vụ, nhập Excel ở `doc/erp/hrm/04-hop-dong-lao-dong.md` (duoc-CR-673, phần tài liệu của HR1-5). Xuất CSV / Excel nhân sự đòi quyền `export` thay cho `read`, cột nhạy cảm bị che theo `employee_sensitive.read` khi xuất, số truy vấn cố định khi xuất nhiều dòng (duoc-CR-660 + duoc-CR-675, HR1-1; khi deploy còn phải tick lại quyền Xuất cho vai trò trên prod vì seed không ghi đè quyền). *(Cập nhật 23/10/2026.)* Không làm chấm công, không làm lương (chốt 16/10/2026).

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| HR1-3 | Khai luồng duyệt nghỉ phép cho các pháp nhân đang dùng ngoài AGC (hiện chỉ AGC có chuông người duyệt, công ty khác đi đường cũ) | Mỗi pháp nhân có người dùng thật có luồng trên `/approval/flows`; đơn gửi đi có chuông tới đúng người duyệt | Dữ kiện prod 21/10 |
| HR1-5 | Nhập bù `hire_date` cho hồ sơ cũ (việc dữ liệu — phần tài liệu `04` đã xong ở duoc-CR-673). Thiếu ngày này thì thâm niên phép tính bằng 0, báo cáo biến động lấy ngày tạo hồ sơ. Đường nhập: ô trên hồ sơ hoặc cột «Ngày vào làm» của Nhập Excel | Không còn hồ sơ đang làm thiếu `hire_date`; nên xong trước khi cấp quỹ phép năm 2027 | `doc/erp/hrm/README.md` §5 · `doc/erp/hrm/04-hop-dong-lao-dong.md` §C.3 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| HR2-1 | Nhận việc / nghỉ việc có danh sách việc vào–ra, quyết định thôi việc có thẻ bàn giao, tài sản cấp phát (cấp, thu hồi, biên bản) — V2-1, V2-2, V2-3 | Người nghỉ có phiếu bàn giao và danh sách tài sản phải trả; tài sản tra được đang ở tay ai | `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md` §0.1 bước 1 |
| HR2-2 | Hồ sơ cho nhân viên: in *Phiếu thông tin nhân viên* theo mẫu BM00../QT01/NS (C5); nhân viên tự khai các nhóm hồ sơ còn lại (C6, mới mở nhóm Liên hệ) | In được phiếu đúng mẫu; nhân viên tự sửa được các nhóm đã chốt, HR thấy dấu vết | `doc/erp/hrm/01-ho-so-nhan-su.md` §7.9, §7.10 |
| HR2-4 | Tuyển dụng (V3-3): định biên, nhu cầu tuyển có duyệt, ứng viên, phỏng vấn, offer thành nhân viên | Ứng viên đạt chuyển thành hồ sơ qua sự kiện HIRE | `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md` §0.1 bước 2 |
| HR2-5 | Quyết định đầy đủ: phiếu nhiều người, tờ trình, duyệt (V1-8); khen thưởng / kỷ luật, đi làm lại, phụ lục HĐLĐ (V2-5) | Một phiếu áp được cho nhiều người sau duyệt | `doc/erp/hrm/01-ho-so-nhan-su.md` §4 · `10-de-xuat-ap-dung.md` §0.1 bước 4 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| HR3-1 | Đánh giá KPI / OKR (V3-2) | Công ty chốt cách đánh giá trước | `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md` §0.1 bước 3 |
| HR3-2 | Bảo hiểm xã hội (V3-4), đào tạo LMS, góp ý ẩn danh | Phòng Nhân sự xác nhận có nhu cầu thật | `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md` §0 |
| HR3-3 | Luồng duyệt đọc đủ mọi loại nghỉ của đơn nhiều loại (nay chỉ đọc loại chính) | Có phương án được chốt; đơn nhiều loại đi đúng luồng của từng loại | `doc/erp/hrm/02-nghi-phep.md` §7.1 |

**Câu chờ quyết:**
- Lấy *vị trí công việc* làm trung tâm của mô hình nhân sự hay giữ như nay — đại ca.
- Bật 2FA cho người có quyền HR — đại ca.
- V3-2 cách đánh giá; V3-4 tự khai hay thuê dịch vụ; đào tạo có cần không — phòng Nhân sự.
- Pháp nhân nào cần luồng duyệt nghỉ phép riêng, ai duyệt (HR1-3) — phòng Nhân sự từng pháp nhân.

## 6. Văn thư và văn bản

**Đã có:** Mã đi trọn yêu cầu → soạn → phiên bản → duyệt qua bộ máy chung → ban hành → clone xuống công ty con, có bản trích và đăng thông báo lên diễn đàn khi ban hành (F12). Bộ máy duyệt văn bản đã bật trên prod, AGC có luồng riêng từ 22/10. Prod hiện 0 văn bản.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| VT1-1 | P5 lớp kiểm mức mật: mức mật văn bản và người, chia sẻ đích danh có hạn, thu hồi, tra cứu qua kiểm quyền (kiểm mã: `document/controller.py` ghi rõ lớp `secrecy_level` CHƯA có). Chờ B3 | Đạt cả 8 bài kiểm (4 chỗ không lộ văn bản mật + 4 bài chia sẻ / thu hồi) | `doc/erp/van-thu/02-lo-trinh-phat-trien.md` §9 |
| VT1-2 | Pháp nhân nào bắt đầu dùng hoặc nhận bản clone thì khai luồng duyệt văn bản riêng (bộ máy đã bật, không có luồng là đi đường cũ) | Mỗi pháp nhân dùng thật có luồng trên `/approval/flows`, duyệt thử một văn bản ra đúng người | Dữ kiện prod 22/10 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| VT2-1 | P6 nạp dữ liệu thật: 32 loại văn bản, mã pháp nhân, văn bản đang hiệu lực; 10–15 người thử trên dev. Cần người Hành chính / Pháp chế | Người thật dùng trên dev với dữ liệu thật, có biên bản góp ý | `doc/erp/van-thu/02-lo-trinh-phat-trien.md` §10 |
| VT2-2 | P7 lên prod từng pháp nhân, kèm bài HDSD và buổi đào tạo | Pháp nhân đầu tiên ban hành văn bản thật trên prod | `doc/erp/van-thu/02-lo-trinh-phat-trien.md` §11 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| VT3-1 | P9 mở rộng: xác nhận đã đọc, sổ đi / đến, nhắc hết hiệu lực, AI báo trùng, tìm không dấu, ký số, dấu chìm, form web, so sánh phiên bản | Mỗi mục có người dùng thật yêu cầu và một dòng CR riêng | `doc/erp/van-thu/02-lo-trinh-phat-trien.md` §13 |

**Câu chờ quyết:**
- `doc/erp/van-thu/00-danh-gia-va-cau-hoi.md` §8: A1–A4, B1–B8, C1–C5. Chặn nhất: A1 (phạm vi bản đầu), B1 (form chuẩn), B2 (ai duyệt yêu cầu), B3 (mấy mức mật, ai cấp), B5 (clone có chạy lại luồng), B6 (mã pháp nhân / loại / phòng ban), B8 (ai ký cho 3 pháp nhân chưa có đại diện) — đại ca + Pháp chế.
- C3: ai là chủ nghiệp vụ phía Pháp chế / Văn thư — đại ca. Thiếu người này thì VT2-1 đứng.

## 7. Duyệt dấu và đặt xe, đồng bộ app đặt xe cũ

**Đã có:** Duyệt dấu pha 0–5 có mã, kể cả `SealApprovalPanel` và ẩn nút cổng 1 khi phiếu đang chạy luồng (kiểm mã: `seal-approval-panel.tsx`, `seal-workflow-actions.tsx`); prod chạy luồng chung trưởng bộ phận → pháp lý. Đặt xe pha 0–6 trên prod. Đồng bộ app cũ: P0 nền (sổ `tab_sync_log` chung, `legacy_id` chốt là index không unique, bảng tra thương hiệu → pháp nhân 11/11), P1 nạp 1 313 phiếu + lịch sử duyệt + tệp chạy xong ở local, P2 app cũ → ERP chạy, P3 ERP → app cũ đã viết mã nhưng công tắc tắt (bao-CR-596).

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| DX1-1 | P1 nạp lịch sử lên dev rồi prod: xuất CSV chỗ vướng, kiểm pháp nhân tra ra có tồn tại thật (có nhân sự mang `company_id = 15` không tồn tại), chạy thử / thật dev soi 20 phiếu, sao lưu DB prod, chạy prod. Phần suy phòng ban cho 367 phiếu xe + giao hàng đã chạy ở local *(cần kiểm lại trên dev)* | Dev và prod có đủ 1 313 phiếu, 0 phiếu mang pháp nhân / phòng ban chết | `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md` P1, mục chặn đường |
| DX1-2 | Nợ nhỏ: đại ca mở Luật Firebase cho nhánh `sync_logs` (mã xong 21/09, chưa mở thì sổ rỗng); bài kiểm trần độ dài ở tầng schema của P2 | Tab *Đồng bộ ERP* bên app cũ có dòng khi ERP sập thử; bài kiểm độ dài xanh | `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md` P0, P2 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| DX2-1 | E2E Playwright: luồng 2 cổng duyệt dấu + 6 bước đặt xe (kiểm mã: repo chưa có `playwright.config`) | Hai kịch bản chạy trên host với tài khoản demo 3 vai trò, xanh | `doc/duyet-dau/TIEN-DO.md` PHA 5 · `doc/dat-xe-duyet-dau/TIEN-DO.md` |
| DX2-2 | Điều kiện chuyển giai đoạn 2: rà ERP làm được mọi thao tác người dùng đang làm trên app cũ; rà hai danh sách người duyệt trùng | Có bảng đối chiếu thao tác, 0 dòng thiếu; danh sách người duyệt khớp | `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md` mục chặn đường |
| DX2-3 | Bật P3 ERP → app cũ: làm Bước 0 (chặn chiều nhận ghi đè kết quả ERP) trước, bật công tắc ở dev | Duyệt / điều phối trên ERP hiện bên app cũ, không bị ghi đè ngược | `doc/dong-bo-dat-xe-duyet-dau/p3-erp-sang-app-cu.md` |
| DX2-4 | P5 đối soát đêm: đếm hai bên theo tháng và trạng thái | Mỗi sáng có số lệch, lệch 0 trên dev một tuần | `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md` P5 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| DX3-1 | P7 phiếu dấu chiều ERP → app cũ; P8 tắt app cũ | Có ngày tắt được chốt; app cũ chỉ còn đọc rồi tắt | `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md` P7, P8 |
| DX3-2 | Duyệt dấu P4: tách khối *chứng từ chữ ký sống* với *ảnh ghi chú* (đang hoãn) | Khách xác nhận cần làm | `doc/duyet-dau/TIEN-DO.md` PHA 4 |

**Câu chờ quyết:**
- A: Giám đốc chỉ nhận báo hay thêm một cổng duyệt; B: Văn thư trả về thì gửi lại cho trưởng bộ phận hay thẳng Văn thư; C: chọn trưởng phòng thủ công hay tự động theo phòng ban — khách / đại ca (`doc/duyet-dau/README.md` §4).
- Phiếu dấu có làm chiều ERP → app cũ không; ngày tắt app cũ — đại ca.

## 8. Công việc / dự án

**Đã có:** W0–W1 xong; kanban kéo thẻ và kéo đổi thứ tự cột, khung danh sách, panel chi tiết, lọc điều kiện ở thanh công cụ (kiểm mã: `work-toolbar.tsx`, `task-filter-fields.ts`). Gantt + cột mốc + phụ thuộc, loại việc và đánh giá kết quả (duoc-CR-656), tab Hoạt động, màn Tổng quan dự án. Bình luận có @nhắc tên, đính kèm, xóa; xóa việc là xóa mềm.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| CV1-1 | W3 nối chuông: giao việc → chuông (F-01); việc Dự án vào tab *Việc cần làm*, giữ bất biến tập cha CR-215 (F-02); đổi trạng thái / bình luận báo người theo dõi (F-04). Kiểm mã: `modules/work` chưa gọi thông báo nào | Giao việc là chuông kêu; bài kiểm tập cha mở rộng xanh | `doc/erp/cong-viec/03-lo-trinh-phase.md` W3 |
| CV1-2 | Nợ nhỏ: sửa bình luận của mình (E-05, mới có xóa); thùng rác có màn và nút khôi phục (B-09, mới có `deleted_at`); ghim list hay dùng trên sidebar (A-05) | Ba thao tác chạy trên dev, có bài kiểm phần sửa | `doc/erp/cong-viec/03-lo-trinh-phase.md` W2, W3, W4 |
| CV1-3 | Đóng mốc MVP: một đội dùng thử trọn vòng trên dev (tạo nhóm → list → mời → giao nhiều PIC → nhãn → kéo cột → việc con → hoàn thành) | Có biên bản đội dùng thử | `doc/erp/cong-viec/03-lo-trinh-phase.md` W2 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| CV2-1 | Nhắc hạn bằng chuông ERP (F-03). Hiện chỉ có nhắc qua bot Telegram (`agent.work_due`, ai-CR-175), bot đã đóng băng và chỉ tới người có liên kết | Mỗi ngưỡng hạn bắn đúng một chuông, không lặp mỗi lượt beat | `doc/erp/cong-viec/03-lo-trinh-phase.md` W4 |
| CV2-2 | Màn *Việc của tôi* gom việc Dự án mọi list (G-03) *(cần kiểm lại: Trang cá nhân có tab Việc cần làm, chưa thấy gom việc Dự án)* | Một màn ra mọi việc mình là PIC, lọc theo hạn | `doc/erp/cong-viec/03-lo-trinh-phase.md` W4 |
| CV2-3 | Chuyển việc sang list khác (B-10) *(cần kiểm lại: `/tasks/{id}/move` mới đổi cột)*; mời thành viên theo phòng ban (A-06) | Chuyển được việc giữa hai list giữ bình luận, tệp; mời cả phòng một lần | `doc/erp/cong-viec/03-lo-trinh-phase.md` W4 |
| CV2-4 | Dashboard cấp list (D-06, mới có Tổng quan cấp phân hệ); gom nhóm kanban theo PIC / ưu tiên / hạn (D-08); list kiểu dự án (A-10) *(cần kiểm lại: phân hệ đã đổi tên Dự án)* | Tab Dashboard hiện trong list; đổi được tiêu chí gom nhóm | `doc/erp/cong-viec/03-lo-trinh-phase.md` W4 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| CV3-1 | Việc lặp (B-11), gắn chứng từ ERP (B-12) | Có người dùng thật yêu cầu và CR riêng | `doc/erp/cong-viec/03-lo-trinh-phase.md` W5 |
| CV3-2 | Gantt nâng cao: dời lịch dây chuyền theo `lag_days`, đường găng, baseline; trừ ngày nghỉ bằng lịch làm việc HRM (nền `work_schedule` đã có, gọi sang, không dựng bảng riêng) | Có người dùng thật yêu cầu | `doc/erp/cong-viec/03-lo-trinh-phase.md` W5 |

**Câu chờ quyết:**
- Đội nào dùng thử MVP (CV1-3) — đại ca.
- Nhắc hạn có cần cả email hay chỉ chuông — đại ca.

## 9. Diễn đàn

**Đã có:** F0–F5, ghim bài + tab Thông báo (F9a), tìm kiếm, bài tự động khi đổi ảnh đại diện (F10), clone thông báo từ Văn thư (F12), chuyên mục kiểu VOZ (F13a–c), tab Quản trị. Phân hệ bật (`enabled: true`) và đã lên prod cùng ERP v2.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| DD1-1 | Gán vai trò `forum_admin` cho người thật trên dev và prod (vai trò seed sẵn, chưa gán cho ai) | Có ít nhất một quản trị diễn đàn mỗi môi trường, ẩn / ghim được bài | `doc/tai-lieu-ky-thuat/ke-hoach-phat-hanh-erp-v2-len-prod.md` |
| DD1-2 | Đóng F6: nhóm nhỏ IT + HR dùng thử rồi thông báo toàn công ty *(cần kiểm lại: chưa rõ đã thông báo chưa)* | Nhóm thử đăng bài thật từ điện thoại; sao lưu R2 phủ bảng diễn đàn | `doc/erp/dien-dan/02-lo-trinh-phase.md` F6 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| DD2-1 | F9 sửa bài kèm nhãn *đã chỉnh sửa* (kiểm mã: chưa có PUT cho bài). Chờ D-Q4 | Tác giả sửa được bài của mình, bài hiện nhãn | `doc/erp/dien-dan/02-lo-trinh-phase.md` F9 |
| DD2-2 | Hai tool AI `forum_search`, `forum_post_read` ép quyền theo người hỏi, khai theo đường cổng MCP | Hỏi qua MCP ra đúng bài người đó được xem | `doc/erp/dien-dan/03-de-xuat-ai-doc-dien-dan.md` |
| DD2-3 | F7 Help Center thành tab *Hướng dẫn* | Tab đọc chung `help_article`, chốt đích chuyển hướng tên miền help cũ | `doc/erp/dien-dan/02-lo-trinh-phase.md` F7 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| DD3-1 | F8 duyệt bài trước theo box (cờ `require_approval`); F11 tự chọn bố cục ảnh | Sếp yêu cầu | `doc/erp/dien-dan/02-lo-trinh-phase.md` F8, F11 |
| DD3-2 | Đợt 3: theo dõi người, nhóm kín, bình chọn | Sếp muốn | `doc/erp/dien-dan/00-pham-vi-va-ke-hoach.md` |

**Câu chờ quyết:**
- D-Q4 người đăng được tự sửa / xóa bài hay chỉ ẩn; D-Q5 người thuộc holding thấy bài *Công ty* nào; D-Q6 like có sinh chuông không (mặc định không) — đại ca (`doc/erp/dien-dan/00-pham-vi-va-ke-hoach.md`).

## 10. Điểm cà phê / POS365

**Đã có:** CP0–CP3 xong 08/09: POC trên cửa hàng thật, tài khoản *TRU DIEM CAFE* Id 46714, sổ cái điểm, task kéo đơn, 5 màn, cấp phát kỳ có người duyệt. Bộ cấp chốt 5 cấp (cấp cao nhất vô hạn). Sổ đồng bộ đã gộp vào `tab_sync_log` chung.

Ghi chú mã phase: Phase 1 dưới đây là CP4 cũ (thí điểm), Phase 2 là CP5 cũ (mở rộng).

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| CP-P1-1 | Dọn cửa hàng POS365 trước thí điểm: *Xóa dữ liệu mẫu* (36 đơn, khách mẫu; cẩn thận 25 món mẫu), void 6 đơn thử, kiểm tài khoản 46714 còn sống (mất thì tạo lại qua API, sửa `.env`) | Sổ POS365 sạch, đơn trừ điểm thử mới vào đúng tài khoản 46714 | `doc/erp/diem-ca-phe/17-ke-hoach-trien-khai-pos365-diem-ca-phe.md` |
| CP-P1-2 | Nhập / xuất danh sách thành viên bằng xlsx (kiểm mã: `coffee_point` chưa có) | Nhập được danh sách gán cấp hàng loạt, xuất lại được | `doc/erp/diem-ca-phe/06-lo-trinh-phase.md` CP4 |
| CP-P1-3 | Thí điểm 1 tháng trên quán thật, sau khi chốt mức điểm 4 cấp thường + âm điểm + thuế bằng văn bản và khai vào màn Chính sách; đi trọn vòng bằng tay trên dev trước | Một tháng chạy thật, số dư ví khớp đơn POS365 | `doc/erp/diem-ca-phe/06-lo-trinh-phase.md` CP4 |

**Phase 2**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| CP-P2-1 | Soi gương số dư điểm lên POS365 (P5 `PartnerSave` ghi `Point`, chưa gọi thử) | Thu ngân thấy số dư trên POS365 khớp ERP | `doc/erp/diem-ca-phe/06-lo-trinh-phase.md` CP5 |
| CP-P2-2 | Báo cáo món / kỳ; bàn giao kế toán (E-02) theo đáp án thuế | Kế toán nhận được bảng kỳ đúng mẫu đã chốt | `doc/erp/diem-ca-phe/06-lo-trinh-phase.md` CP5 |

**Phase 3 — khi cần**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| CP-P3-1 | Nối cấp phúc lợi vào danh mục Chức vụ của HRM (đã có) thay gán tay | Đổi chức vụ là cấp cà phê tự đổi | `doc/erp/diem-ca-phe/06-lo-trinh-phase.md` CP5 |

**Câu chờ quyết:**
- Mức điểm / tháng của 4 cấp thường — đại ca + Nhân sự.
- C-05 cho âm điểm hay không — đại ca.
- E-02 thuế TNCN với điểm phúc lợi — kế toán.
- POS365 có cho ghi / soi số dư điểm không — chờ POS365 trả lời hoặc thử P5.

---

## 11. AI — trợ lý web, cổng MCP, kho skill, AI kế hoạch và phân việc, dịch vụ AI / bot

**Đã có:** Prod 19/10: kho skill P0–P8, cổng MCP có khóa và OAuth (ChatGPT, claude.ai), K7 bot và Trợ lý đọc chung kho, K9 quản trị bằng lời, dịch vụ AI tách chạy trên VPS prod, bot Telegram @degooo_bot đóng băng tính năng từ 17/10. Prod 20/10: A0 ai-CR-230 (`tab_ai_usage_daily`, `tab_audit_log.ai_channel`), D0 duoc-CR-654, hồ sơ cách làm việc duoc-CR-641, công tắc thu sự kiện giao diện đã bật. Soát mã 22/10: bài HDSD Kết nối AI riêng và Kho skill đã có (`backend/scripts/seed_help_ket_noi_ai_mcp.py`, bao-CR-631); `assistant/packs` đã gỡ nên màn quản lý nguồn tri thức (doc 03 P4) đã được Kho skill thay; nhắc hạn 3 mốc cho việc Dự án đã có (ai-CR-175); doc 21 §9 Q1–Q8 đã chốt hoặc đã làm theo đề nghị.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| AI1-1 | Đưa D1 lên prod: duoc-CR-655..657 (báo cáo mức dùng chức năng, chỉ số Dùng AI, năng lực theo loại việc, hàm gợi ý người nhận việc) | Chạy trên prod. Quản trị mở được báo cáo theo chức năng và nhóm 3.7, 3.8 | `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §7 |
| AI1-2 | A1: gắn công cụ `team_capacity` và `task_type_stats`. Hàm `suggest_assignees`, `get_capability` đã có ở `capability/ai_contract.py` nhưng chưa công cụ nào gọi | Có ở Trợ lý web và MCP. Gác quyền theo §6 (chỉ quản trị xem bảng số). Có nhật ký. Theo chuẩn §5.6 doc 21. Bài kiểm canh cửa xanh | `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §4, §7 |
| AI1-3 | A2: `plan_context`; `draft_work_plan` thêm `estimate_hours`, `task_type`, `assignee_reason`; bảng `tab_ai_plan_proposal` ghi đề xuất và phần người sửa (máy chủ XONG 445d2296); màn duyệt kế hoạch **XONG — kh-AI1-3-giao-dien, 23/10, đã lên erp-v2** | Lập được kế hoạch có ước lượng và lý do giao. Bản đề xuất và bản sau sửa đều lưu | `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §4, §5, §7 |
| AI1-4 | Vận hành sau đợt prod: khóa model riêng cho prod (đang dùng chung khóa dev); hỏi trạm modelapi.vn về khoảng 40k token dư mỗi lượt; thử claude.ai web và Claude Desktop với prod | Prod có khóa riêng. Có câu trả lời của trạm. Hai ứng dụng nối prod chạy được một lượt đọc và một lượt soạn nháp | `doc/agent-hub/20-loi-hoi-thoai-moi.md`; `doc/erp/tai-lieu-ai/21-kho-skill-ai-mcp.md` §7.2 P6 |

**Phase 2** (AI2-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| AI2-1 | A3 vòng học: đóng task thì so ước lượng với thực tế, hiệu chỉnh `task_type_stats`; tra kế hoạch tương tự | Sau mỗi task xong có dòng so sánh. Số thống kê tự cập nhật | `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §7 |
| AI2-2 | T1 thử với một phòng: soạn bộ skill phòng, trưởng phòng dùng 2–4 tuần, đo đề xuất đúng sai | Có số đo sau thời gian thử. Có danh sách sửa trước khi mở cả công ty | `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §7, §8 câu 2 |
| AI2-3 | P5 phủ công cụ cho Đặt xe, Duyệt dấu, Diễn đàn, Kho và giao nhận. Làm một phần: `erp_read` mới có phiếu nhận hàng | Mỗi phân hệ có ít nhất một công cụ đọc đúng quyền. Có skill hướng dẫn khi nào gọi | `doc/erp/tai-lieu-ai/03-lo-trinh-phase.md` Phase 5 |
| AI2-4 | Mở MCP `prompts` để ứng dụng ngoài tự xem cẩm nang trước khi trả lời (chưa có trong `agent_hub/mcp.py`) | Claude Desktop thấy danh sách prompt của công ty | `doc/erp/tai-lieu-ai/21-kho-skill-ai-mcp.md` §8 |
| AI2-5 | O-01: đếm lỗi 5xx và độ dài hàng đợi cho dịch vụ AI (cần kiểm lại) | Có số đếm theo giờ. Vượt ngưỡng thì báo | `doc/agent-hub/13-lo-trinh.md` §0 phase 7 |

**Phase 3 — khi cần** (AI3-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| AI3-1 | A4 hỏi chéo phòng: AI phòng A hỏi năng lực phòng B | Chỉ làm nếu T1 cần. Gác quyền hai phòng | `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §7 |
| AI3-2 | AI-2 RAG toàn hệ, lọc quyền từng bản ghi. Khoảng hở đã biết: RAG loại B chưa lọc quyền, an toàn vì corpus chỉ có HDSD công khai | Đóng khoảng hở trước khi nạp bất kỳ tài liệu không công khai nào | `doc/erp/tai-lieu-ai/03-lo-trinh-phase.md` mục Để sau |
| AI3-3 | Phase 8 lõi mở (M-09, N-06..N-08: MCP ngoài, A2A, ngân sách, sổ sự kiện) và dời dịch vụ AI sang VPS riêng (S-5, S-6) | Có VPS AI. Chạy runbook doc 14 §6 không mất dữ liệu | `doc/agent-hub/13-lo-trinh.md` §0, §3.3 |
| AI3-4 | N-01, N-05 bot riêng từng người: bảng `tab_agent_bot`, webhook, khóa mã hóa riêng | Một người tự dán token và có bot riêng chạy | `doc/agent-hub/13-lo-trinh.md` §7 |
| AI3-5 | Việc gắn bot đang đóng băng: G-2 tin cần để ý trong nhóm, G-3 tìm tin nhóm, G-4 đồng hồ chờ, bản tin cuối ngày (phần còn lại của T-14), M-07 khóa AI cá nhân cho Trợ lý web (web vẫn dùng khóa công ty) | Chỉ mở lại khi đại ca bỏ đóng băng bot | `doc/agent-hub/13-lo-trinh.md` §5; `doc/agent-hub/04-danh-sach-tinh-nang.md` M-07 |
| AI3-6 | Bật OTP cho thao tác prod qua bot (V-04, đang tạm bỏ qua theo lệnh đại ca; cần kiểm lại) | Lệnh prod từ máy sửa mã đòi OTP | `doc/agent-hub/08-van-hanh-vps.md`; `doc/agent-hub/13-lo-trinh.md` §6 |

**Câu chờ quyết:**
- 22 §8 câu 2: phòng thử đầu tiên. Agent 1 đề nghị Thu mua. Đại ca quyết.
- 22 §8 câu 3: ai khai danh mục loại việc cho từng phòng. Đề nghị trưởng phòng khai, quản trị duyệt. Đại ca quyết.
- 22 §8 câu 4: kênh thử trước. Đề nghị MCP và Trợ lý web. Đại ca quyết.
- Doc 03 điểm chốt: ký DPA không lưu giữ với Anthropic và Google; danh mục tài liệu tuyệt mật loại khỏi AI. Ban lãnh đạo quyết.
- Agent-hub 13 §7.1: ai được tạo bot riêng, có bot của phòng không. Đại ca quyết.
- Agent-hub 13 §3.4 S4: mua VPS AI riêng. Đại ca quyết.
- Khóa model riêng cho prod. Đại ca cấp.

## 12. Sản xuất (SX)

**Đã có:** Mới có tài liệu nghiên cứu nghiệp vụ `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` (21/10, căn cứ Thông tư 99/2025). Chưa có mã, bảng hay entity quyền nào. Dùng lại được `tab_product`, `tab_inventory` (bình quân di động), `tab_inventory_move`, Thu mua và công nợ phải trả.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| SX1-1 | Trả lời 15 câu ở §14 (A1–A5, B1–B4, C1–C6). Ưu tiên B1 và C2 (giá chuẩn hay giá thực tế, kỳ tính giá) | Có biên bản khảo sát nghiệp vụ được xác nhận. B1 và C2 có đáp án | `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §14; `doc/erp/san-xuat/README.md` |
| SX1-2 | Rà sổ kho: chặn âm kho, giá vốn, chốt kỳ | Có biên bản rà và danh sách việc sửa | `doc/erp/02-dai-han.md` §4 (bản cũ); `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §13 |
| SX1-3 | DB6 bảng sản phẩm cha, nền cho BOM. Không thêm bảng biến thể dưới `tab_product`, không đổi `product_code`, không đặt cột giá lên sản phẩm | Bảng mới đã dùng thật. `tab_product` không đổi dòng nào | `doc/erp/01-ngan-han-2026.md` DB6 (bản cũ); `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §13.3 |

**Phase 2** (SX2-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| SX2-1 | Viết tài liệu yêu cầu, rồi làm BOM (nhiều cấp, phiên bản, hiệu lực theo ngày) và lệnh sản xuất; thêm loại phiếu kho: xuất sản xuất, nhập thành phẩm, trả vật tư, xuất hủy; entity `production` | Trạng thái lưu `SMALLINT` có `IntEnum`. Entity khai đủ phạm vi. Bài kiểm canh xanh | `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §4, §13 |
| SX2-2 | Danh mục kho thật (thay chuỗi `warehouse_code`), giữ chỗ tồn kho; lô và hạn dùng nếu C5 chốt có | Có kho cách ly, kho gia công, kho dở dang. Số khả dụng đúng | `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §13.2 |
| SX2-3 | NF-23 dashboard Sản xuất có biểu đồ thật | Làm sau khi có module. Có số lệnh, sản lượng, hàng lỗi | `doc/erp/13-ke-hoach-man-con-lai-v2.md` NF-23 (bản cũ) |

**Phase 3 — khi cần** (SX3-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| SX3-1 | Giá thành nếu B1 chọn làm: đánh giá dở dang, phân bổ chi phí chung theo công suất bình thường, hàng lỗi, gia công ngoài | Phần vượt mức bình thường vào thẳng giá vốn, không nằm trong tồn kho | `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §5–§10 |
| SX3-2 | MRP tự động, Routing và công đoạn, chất lượng, bảo trì máy | Theo đáp án B2, B3 và khảo sát | `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §14 nhóm B; `doc/erp/02-dai-han.md` §3.3 (bản cũ) |

**Câu chờ quyết:**
- §14 B1: bản đầu chỉ quản lý số lượng hay làm cả giá thành. Đại ca quyết.
- §14 C2: giá thành chuẩn hay thực tế, kỳ tháng hay quý. Kế toán và ban lãnh đạo quyết.
- §14 A1: nhà máy nào, mặt hàng gì. Bộ phận sản xuất trả lời.
- C5 danh mục chờ: có làm vị trí kho, lô, hạn dùng không. Bộ phận sản xuất và kho quyết, trước khi viết BOM.
- C6 danh mục chờ: giá thành thuộc Sản xuất hay Kế toán. Ban lãnh đạo và kế toán quyết.

## 13. Kế toán (KT)

**Đã có:** ERP chưa có phân hệ kế toán. Đã có công nợ phải trả và yêu cầu thanh toán bên Thu mua, Tài chính, là một nửa nguồn bút toán. Đội phần mềm khuyến nghị nối phần mềm kế toán có sẵn, không tự viết. Thứ tự: sau HRM và Sản xuất.

**Phase 1 — làm tiếp**

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| KT1-1 | Hỏi kế toán đang dùng phần mềm nào và soát tên tài khoản sản xuất theo Thông tư 99 (chỉ khảo sát, chưa viết mã) | Có tên phần mềm và bảng tên tài khoản đã soát | `doc/erp/san-xuat/00-tong-quan-nghiep-vu.md` §14 C1, C3; `doc/erp/san-xuat/README.md` |

**Phase 2** (KT2-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| KT2-1 | Đầu nối xuất bút toán từ Thu mua (công nợ phải trả, yêu cầu thanh toán) sang phần mềm kế toán, kèm màn đối chiếu | Làm sau khi chốt C7. Kế toán nhận được bút toán một tháng thử và số khớp | `doc/erp/02-dai-han.md` §3.4, §5 (bản cũ) |

**Phase 3 — khi cần** (KT3-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| KT3-1 | Mở rộng đầu nối cho bút toán Sản xuất (giá thành) và CRM (công nợ phải thu) | Làm khi hai phân hệ đó đã chạy | `doc/erp/02-dai-han.md` §3.4 (bản cũ) |

**Câu chờ quyết:**
- C7 danh mục chờ: kế toán nối hay tự viết. Đề nghị nối. Ban lãnh đạo quyết, trước vòng 3.
- C11 danh mục chờ: CRM có đẩy lên trước Kế toán không. Ban lãnh đạo quyết.
- §14 C1, C3 (san-xuat/00): phần mềm kế toán đang dùng; pháp nhân có nhà máy theo chế độ doanh nghiệp hay doanh nghiệp nhỏ và vừa. Kế toán trả lời.

## 14. Khác — CRM, kênh Zalo, tách theo công ty cho khách ngoài (KH)

**Đã có:** Mã kênh Zalo đã xong trên dev: bot Zalo chính thức (ai-CR-111) và tài khoản Zalo công ty ghi lặng nhóm (ai-CR-122), đang chờ token và quét QR. Chưa có module CRM. Chưa tách dữ liệu theo công ty.

**Phase 1 — làm tiếp**

Không có việc Phase 1.

**Phase 2** (KH2-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| KH2-1 | Bật kênh Zalo cho thông báo và trao đổi nội bộ bằng mã đã có. Không thêm tính năng vì bot đang đóng băng | Có token bot Zalo và QR số Zalo công ty. Một người nhận được chuông ERP qua Zalo | `doc/agent-hub/13-lo-trinh.md` §0 phase 9, Z-3/Z-4, §6 |

**Phase 3 — khi cần** (KH3-x)

| Mã | Việc | Điều kiện xong | Nguồn |
|---|---|---|---|
| KH3-1 | CRM vòng 4: khách hàng, cơ hội, báo giá bán, đơn bán, giao hàng, công nợ phải thu, chăm sóc sau bán | Làm sau khi chốt C8. Dùng lại khuôn khảo sát giá và công nợ phải trả | `doc/erp/02-dai-han.md` §3.5 (bản cũ) |
| KH3-2 | Tách theo công ty (tenant) trên nút A và D của dịch vụ AI và kho tin nhắn khi có khách ngoài đầu tiên | Dữ liệu khách này không đọc được từ khách khác | `doc/agent-hub/13-lo-trinh.md` §4, §5 |

**Câu chờ quyết:**
- C8 danh mục chờ: mâu thuẫn mảng bán hàng ở `ke-hoach/02` mục 30.4. Ban lãnh đạo quyết, trước vòng 4.
- C9 danh mục chờ: phạm vi nhóm H, kế toán mua hàng. Ban lãnh đạo quyết.
- C15 danh mục chờ: ai làm lộ trình ERP, có tách khỏi luồng CR Thu mua không. Ban lãnh đạo quyết, trước khi chốt mốc thời gian.
- Agent-hub 13 §6: token bot Zalo và quét QR số Zalo công ty. Đại ca làm.