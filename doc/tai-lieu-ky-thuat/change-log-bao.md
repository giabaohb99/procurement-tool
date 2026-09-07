# NHẬT KÝ THAY ĐỔI — DẢI `bao`

Nhánh riêng của [`change-log.md`](change-log.md), tách ngày **07/09/2026**.

**Vì sao tách.** Luật tiền tố tên người (03/09) đã hết trùng SỐ, nhưng vẫn còn trùng CHỖ:
ai cũng chèn dòng mới vào **đúng dòng đầu bảng** của một tệp duy nhất, nên gần như lần
merge nào cũng dính xung đột ở đó — sửa tay không khó nhưng lặp lại mỗi ngày, và nguy hiểm
ở chỗ giải sai một phát là **nuốt mất dòng CR của người khác** mà không ai biết. Tách tệp
thì hai người ghi hai chỗ, git tự merge, không còn phải đụng tay.

**Tệp này chứa gì.** Mọi CR mang tiền tố `bao-` **từ bao-CR-310 trở đi**, và nhật ký deploy
của các CR đó.

**Tệp này KHÔNG chứa gì.** Ba thứ vẫn nằm ở `change-log.md` chung, cố ý:

- **CR cũ** (`CR-001`…`CR-271` và mọi `bao-CR-*` trước 310) — không dời sang đây. Dời là đẻ
  một diff khổng lồ, mà vẫn phải đọc hai tệp như cũ, chẳng được gì.
- **Việc còn nợ `N-xxx`** — đánh số KHÔNG tiền tố và được trích dẫn thẳng trong bình luận
  mã nguồn (`xem N-004`). Chẻ đôi là đẻ hai không gian số cho cùng một cái tên.
- **Quyết định `D-xxx` / `QĐ-x`** — cùng lý do, và cả đội đọc chung một danh sách.

Ba thứ đó hiếm khi thêm, nên xung đột không đáng kể.

---

## Luật ghi (giữ nguyên như tệp chung)

**Trạng thái:** `Đề xuất` → `Đã duyệt` → `Đang làm` → `Hoàn tất` (hoặc `Từ chối` / `Hoãn`).

**ID đầy đủ = `bao-CR-<số>-<slug>`**, slug kebab 3-5 chữ tóm tắt việc.

**ĐẶT CHỖ NGAY KHI NHẬN VIỆC** — cấp số xong là ghi ngay một dòng trạng thái `Đang làm`
(một câu là đủ) RỒI mới bắt tay code. Xong việc quay lại điền đủ; bỏ giữa chừng thì xóa
dòng đặt chỗ.

⚠️ **CẤP SỐ MỚI PHẢI GREP CẢ HAI TỆP.** Dải số là **chung cho cả đội**, không phải mỗi
người một dải — tách tệp chỉ để hết đụng chỗ ghi, không đổi cách đánh số:

```bash
grep -oh "CR-[0-9]\+" doc/tai-lieu-ky-thuat/change-log.md doc/tai-lieu-ky-thuat/change-log-bao.md | sort -t- -k2 -n | tail -3
```

Lỡ vẫn trùng số với người khác thì **kệ** — hai dòng cùng số khác slug là hợp lệ.

---

| CR | Ngày | Người đề xuất | Nội dung | Ảnh hưởng scope | Trạng thái | Tài liệu liên quan |
|---|---|---|---|---|---|---|
| **bao-CR-313-va-lo-hong-nhat-ky-va-tan-suat** | 2026-09-07 | Bảo | **ĐỀ XUẤT — GẤP, BM-001 đang mở trên hệ thật.** Vá ba lỗ hổng cùng vùng mã, ghi ở `so-ghi-nhan-loi-bao-mat.md`: (1) **BM-001** `/api/audit-logs` chỉ gác bằng `get_current_user` — không `require`, không `apply_scope`, `entity` do người gọi truyền thẳng và `entity_id` được phép bỏ trống, nên **bất kỳ tài khoản đăng nhập nào cũng đọc được nhật ký của mọi phân hệ**; đo trên prod 07/09: 18 entity, riêng `entity=auth` 341 dòng chứa IP nhà riêng + email tài khoản + lịch sử gõ sai mật khẩu. (2) **BM-003** `/api/auth/refresh` không ghi dấu vết và không lấy IP → refresh token bị cắp tự gia hạn im lặng suốt 7 ngày. (3) **BM-004** limiter khai `get_remote_address` mà uvicorn chạy không `--proxy-headers` sau nginx → mọi lượt gọi mang IP container, `LOGIN_RATE_LIMIT=10/minute` thành **10 lượt/phút cho cả công ty**: vừa yếu chống dò (14.400 lượt/ngày) vừa chặn nhầm người thật lúc cao điểm. Hai chỗ dễ vỡ: siết quyền đọc nhật ký làm dòng thời gian của lớp CRUD **im lặng trống** thay vì báo 403 (phải rà cả `frontend/` lẫn `frontend-v2/`); sửa limiter mà nginx cho client tự đặt `X-Forwarded-For` thì **tệ hơn hiện tại**. | main + erp-v2 | Đề xuất | `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md` |
| **bao-CR-312-nhat-ky-thay-doi-va-phien-dang-nhap** | 2026-09-07 | Bảo | **ĐỀ XUẤT — chưa làm, đang chờ chốt 6 câu hỏi.** Ghi nhật ký ở tầng dữ liệu thay vì tầng lời gọi: bảng `tab_change_log` (giá trị TRƯỚC / SAU dạng JSON, sinh tự động bằng sự kiện SQLAlchemy nên không phụ thuộc lập trình viên nhớ gọi `record`), bảng `tab_login_session` (mỗi lần đăng nhập một dòng: IP, user-agent, thiết bị/OS/trình duyệt, lần hoạt động cuối, thu hồi được), `jti` trong token để nối thao tác về đúng phiên, và ba cột `session_id`/`request_id`/`ip` trên `tab_audit_log`. Gốc rễ: ticket YCBG05092603 truy được thủ phạm nhưng phải đọc cột `created_by` trong database vì nhật ký phiếu trống — xem bao-CR-311. Chia 6 đợt P1..P6. Thiết kế + số đo + 6 câu hỏi chặn ở tài liệu bên cạnh. | erp-v2 | Đề xuất | `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` |
| **bao-CR-311-nhat-ky-gan-phuong-an-ycbg** | 2026-09-07 | Bảo | Ghi dấu vết khi **gắn / gỡ / chốt / bỏ chốt** phương án trên Yêu cầu báo giá — bốn hành động mới `add_option` · `del_option` · `choose_option` · `unchoose_option`, kèm nhãn tiếng Việt trong `ACTION_LABEL`. **Vì sao:** ticket YCBG05092603 (phiếu khảo sát Chai hiện kết quả Thùng) truy ra được thủ phạm, nhưng phải đọc cột `created_by` của chính dòng `tab_survey_request_option` trong database — ba thao tác này chạy từ ngày đầu mà **không ghi một dòng nhật ký nào**, người dùng mở lịch sử phiếu ra chỉ thấy trống. **Ba quyết định:** (1) **KHÔNG ghi tên NCC vào dấu vết** — nhật ký phiếu đọc bằng `survey_request.read` mà người YÊU CẦU có khóa đó, cả cơ chế phương án sinh ra là để giấu NCC với chính họ; chỉ ghi tên sản phẩm (vốn đã hiện trên thẻ phương án) + nhãn `Option N — ID x`. (2) Ghi kèm **phân loại của phiếu khảo sát nguồn** để soi lệch phân loại ngay trên dòng nhật ký — đúng thứ ticket cần mà không có. (3) Đường **đồng bộ tự động** truyền `audit=False` vì `sync_options_from_surveys` đã ghi một dòng `sync_options` tổng kết cả lượt; ghi thêm từng phương án là một thao tác hiện hai lần. Kèm theo: `delete_option` nhận thêm `user_id` (mặc định 0 = hệ thống) và luồng hủy duyệt phiếu khảo sát (`survey/service._purge_yc_options`) truyền người thao tác xuống, trước đây gỡ phương án hàng loạt mà không ai đứng tên. **Chỉ vá được từ nay về sau — thao tác cũ không dựng lại được.** Muốn lấp chỗ trống đó ở mức nền thì xem bao-CR-312. Test: `test_nhat_ky_phuong_an_cr311.py` (7 ca, có ca canh KHÔNG lộ tên NCC và ca canh không ghi đôi). | erp-v2 | Hoàn tất | — |
| **bao-CR-310-xu-ly-phuong-an-tren-ycmh** | 2026-09-07 | Khách | Cho XỬ LÝ KHẢO SÁT ngay trên Yêu cầu mua hàng: NSTM gắn phương án (NCC + giá) lên từng dòng YCMH, chốt rồi lên thẳng ĐMH — thay cho hướng gộp YCMH vào YCBG của cụm bao-CR-277..291 (đã khai tử, xem ghi chú ở tệp chung). YCBG giữ nguyên không đụng. **Chia 4 đợt, bảng đợt ở mục H.8 của tài liệu chức năng.** **Đợt 1 XONG** (nền + API): bảng `tab_purchase_request_item_option` (migration `6835fb9cfecd`) — bảng RIÊNG, cố ý không nhét chung `tab_survey_request_option` để khỏi đẻ cột nghĩa kép; snapshot giá tại thời điểm gắn nên phiếu khảo sát sửa giá sau đó không làm đổi phương án đã chốt; **không** thêm cột "đã chốt" lên dòng YCMH mà suy từ `is_chosen`. 6 API dưới `/{pid}/items/{item_id}/options` (liệt kê · gắn từ kho khảo sát · nhập tay · sửa · xóa · chốt), cổng mở khi phiếu ở `dispatched`/`processing`/`purchasing`/`purchased`. **Ba quyết định phân quyền:** (1) **NSTM gắn, NGƯỜI YÊU CẦU chốt** — NSTM chỉ biết giá bao nhiêu, người yêu cầu mới biết giá đó còn đáng mua không; (2) ai có `purchase_request.approve` (quản lý / admin thu mua) chốt thẳng được cho hàng gấp — khóa này chia đúng ranh giới sẵn có, `pur_staff` không có nên không cần khóa quyền mới; (3) nhập tay chỉ đòi `supplier.read` chứ KHÔNG đòi `supplier.write` — `pur_staff` không có `write`, đòi `write` là khóa chết đúng người dùng nó, mà `write` còn là quyền sửa cả danh mục NCC nên rộng quá mức. Vì thế `choose` gác bằng `read` (người yêu cầu thường chỉ có `read` sau khi phiếu đã duyệt) rồi để `ensure_can_choose` phân xử. Ẩn NCC bám luật cụm `pur` của Task 4. **Kèm theo: BỎ bắt buộc Mã hàng trên dòng YCMH** (`required-fields.ts`) — giống phiếu khảo sát vốn có cả loại có mã lẫn không mã, người yêu cầu phải mua được thứ chưa nằm trong danh mục mà không phải chờ mở mã. Đánh đổi phải biết: `sync_from_purchase_orders` nối ĐMH về YCMH bằng **chuỗi `product_code`** nên dòng KHÔNG MÃ không được cộng tiến độ `qty_ordered`/`qty_received` tự động, NSTM phải tự đặt `line_status` — muốn hết thì phải nối bằng khóa dòng, xem N-004. Luật cũ vẫn còn ở bản v1 (`PurchaseRequestDetail.tsx`) vì `frontend/` đóng băng, chờ khách quyết. Kịch bản nghiệm thu + dữ liệu demo: `backend/scripts/demo_cr310.py` (CHỈ local). Test: `test_ycmh_phuong_an_cr310.py` (21 ca) + `required-fields.test.ts`. **Còn lại: đợt 2** gom phương án đã chốt theo NCC → sinh N đơn mua hàng, **đợt 3** màn *Xử lý phương án* ở frontend-v2 (hiện chưa có một dòng giao diện nào — nên đợt 3 sẽ làm TRƯỚC đợt 2), **đợt 4** hai bản in (bản A cho người yêu cầu: dùng lại phiếu đề xuất mục F, in CHUNG MỘT BẢNG dù nhiều NCC, không cột NCC theo dòng; bản B cho thu mua: tick NCC → in nháp đơn, mỗi NCC một trang) + HDSD. | erp-v2 | Đang làm — xong đợt 1 | `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md` mục H |

---

## Nhật ký deploy môi trường thật

Chỉ ghi deploy của các CR trong tệp này. Deploy cũ nằm ở cuối `change-log.md`.

| Ngày | Môi trường | Nội dung | Ghi chú |
|---|---|---|---|
| 2026-09-07 | **prod** | **bao-CR-311** — dấu vết gắn / gỡ / chốt phương án YCBG. `main` 68595dca → **07ce3498** (cherry-pick từ `erp-v2` 2dbb0f1f), build lại `api` + `celery-worker` + `celery-beat`. | Không có migration mới. Xung đột ở `audit/controller.py`: `ACTION_LABEL` trên `main` chỉ có **9 nhãn**, bản `erp-v2` có ~40 (đợt vá 971 dòng ngày 05/09 **chưa hề lên prod**) — giải bằng cách giữ bản `main` và chỉ thêm 4 nhãn mới, không kéo cả đợt vá sang. Nghĩa là prod vẫn hiện mã Anh trần cho `login` · `assign` · `sync_options` …, **còn nợ một CR riêng**. Đã xác nhận chữ ký hàm + 4 nhãn trong container thật. |
