# TRACKING NGƯỜI DÙNG — HỒ SƠ CÁCH LÀM VIỆC CỦA TỪNG NGƯỜI

**Bản:** 1.1 — 19/10/2026 · **CR:** duoc-CR-626 (thiết kế) → duoc-CR-641 (làm) · **Trạng thái: pha 1–3 ĐÃ LÀM (backend + màn admin). Pha 4 (AI đọc hồ sơ) chưa làm.**
**Liên quan:** [`nhat-ky-va-phien-dang-nhap.md`](nhat-ky-va-phien-dang-nhap.md) (thiết kế các bảng nhật ký mà tài liệu này đọc lại).

---

## 1. Mục tiêu

Mở hồ sơ của **một người** là thấy được người đó **làm việc trên hệ thống như thế nào**:

- hay vào **trang nào**, ở lâu ở đâu, đi theo đường nào;
- **làm task ra sao**: lập phiếu một lèo hay sửa đi sửa lại, xử lý ngay hay để dồn, duyệt nhanh hay chậm;
- làm vào **giờ nào**, trên **thiết bị gì**;
- **thạo** tới đâu, đang **vướng** ở chỗ nào;
- tài khoản có gì **bất thường** không.

Từ đó nhận diện được **kiểu làm việc** của người đó (mục 4) để hỗ trợ, đào tạo, phân việc cho hợp, và sửa hệ thống chỗ người ta hay vướng.

---

## 2. Dữ liệu đang có và còn thiếu

| Bảng có sẵn | Ghi gì | Dùng cho hồ sơ |
|---|---|---|
| `tab_login_session` | phiên đăng nhập, IP, thiết bị/OS/trình duyệt, `last_seen_at` | nhịp làm việc, thiết bị, an toàn tài khoản |
| `tab_request_log` | **mọi** lượt gọi API (kể cả GET từ 10/09/2026): `route`, `http_status`, `error_code`, `duration_ms`, `session_id` | phân hệ hay dùng (ước lượng), lỗi gặp phải. GET giữ 90 ngày, lượt ghi giữ 16 tháng |
| `tab_audit_log` | thao tác nghiệp vụ: `action`, `action_group`, `on_behalf_of`, `changed_fields`, `doc_code` | cách làm task: tạo/gửi/sửa/duyệt/xóa, bấm hộ |
| `tab_export_log` | xuất file: thực thể, số dòng, bộ lọc | thói quen xuất Excel |
| `tab_notification.is_read` | đã đọc chưa | phản hồi thông báo (chưa có giờ đọc) |
| `tab_comment`, `tab_comment_mention` | bình luận, nhắc tên | phối hợp |
| `tab_agent_message`, `tab_agent_run`, `tab_assistant_change` | hỏi trợ lý AI, chi phí, việc AI làm thay | cách dùng AI |
| `tab_user_preference` | bộ lọc lưu, tùy chỉnh cột | mức thành thạo |
| `tab_import_batch`, `tab_import_log` | nhập file | nhập tay hay nhập file |
| `tab_work_task` | việc dự án | đúng hạn / quá hạn |

**Còn thiếu — chặn đúng câu hỏi "vào trang nào nhiều":**

- Giao diện chưa ghi gì: `frontend-v2/src/core/telemetry/logger.ts` chỉ in ra console.
- Một màn gọi nhiều đường API nên từ `tab_request_log` chỉ **ước lượng** được phân hệ, **không đếm được lượt xem màn** và **không biết ở lại bao lâu**.
- Không biết mở form rồi bỏ ngang, tìm kiếm không ra kết quả, lỗi JS phía trình duyệt.
- Thông báo không có `read_at`.

→ Muốn có phần "trang nào, bao lâu, đi đường nào" chính xác thì phải làm **bảng sự kiện giao diện** ở mục 6.

---

## 3. Hồ sơ cá nhân — các phần và chỉ số

Ký hiệu nguồn: ✅ đo được ngay · 🆕 cần bảng sự kiện giao diện (mục 6) · ⚠️ bảng có sẵn, phải kiểm cột trước.

### 3.1 Nhịp làm việc

| Chỉ số | Nguồn | Đọc ra được gì |
|---|---|---|
| Giờ vào đầu tiên / thao tác cuối cùng mỗi ngày | ✅ | khung giờ làm việc thực tế |
| Bản đồ nhiệt giờ × thứ | ✅ | làm dồn buổi nào, ngày nào |
| Số ngày có vào / số ngày làm việc (trừ ngày nghỉ phép) | ✅ + phân hệ `leave` | dùng đều hay thỉnh thoảng |
| Số phiên/ngày, thời lượng phiên | ✅ | mở một lần làm cả ngày hay vào ra nhiều lần |
| Thao tác ngoài giờ, cuối tuần | ✅ | quá tải hoặc làm bù |
| Tỷ lệ điện thoại / máy tính, theo từng loại thao tác | ✅ | duyệt trên điện thoại, lập phiếu trên máy tính… |

### 3.2 Trang truy cập

| Chỉ số | Nguồn | Đọc ra được gì |
|---|---|---|
| Top 10 màn vào nhiều nhất | 🆕 (✅ ước lượng theo phân hệ) | công việc chính của người đó |
| % thời gian theo phân hệ | 🆕 | thời gian dồn vào đâu |
| Thời gian ở lại trung bình từng màn | 🆕 | màn nào phải loay hoay lâu |
| Màn mở đầu tiên mỗi ngày | 🆕 | điểm xuất phát (Trang chủ, thông báo, hay vào thẳng danh sách) |
| Đường đi hay gặp (màn A → màn B → màn C) | 🆕 | quy trình thực tế người đó đi, có vòng lặp/đi lạc không |
| Số màn khác nhau đã dùng trong 30 ngày | 🆕 | dùng rộng hay chỉ quanh vài màn |
| Báo cáo hay mở, bao lâu một lần | ✅ `/summary` | theo dõi số liệu đều đặn hay không |
| Màn vào được nhưng bị chặn quyền (403) | ✅ | đi lạc, hoặc thiếu quyền thật |

### 3.3 Cách làm task (phiếu và việc)

Tính **riêng theo từng loại phiếu** (YCMH, YCBG, ĐMH, nhận hàng, đề nghị thanh toán, văn bản, nghỉ phép, đặt xe…).

| Chỉ số | Nguồn | Đọc ra được gì |
|---|---|---|
| Số phiếu lập / gửi / duyệt / từ chối trong kỳ | ✅ | khối lượng việc trên hệ thống |
| Thời gian lập một phiếu (mở form → lưu) | 🆕 | nhanh hay chậm so với người cùng vai trò |
| Lập một lèo hay lưu nháp quay lại nhiều lần | ✅ số lần `update` trước `submit` | chuẩn bị đủ thông tin trước hay vừa làm vừa tìm |
| Sửa sau khi đã gửi | ✅ | hay bị thiếu/sai sau khi gửi |
| Tỷ lệ bị trả về / từ chối | ✅ | chất lượng phiếu lập |
| Mở form rồi bỏ ngang | 🆕 | form khó, hoặc thiếu thông tin để điền |
| Tới lượt mình → xử lý mất bao lâu (trung vị, p90) | ✅ mốc gửi → mốc duyệt | xử lý ngay hay để tồn |
| Xử lý từng phiếu hay dồn lô (nhiều phiếu trong vài phút) | ✅ | thói quen dồn việc |
| Phiếu tạo trong 3 ngày cuối tháng | ✅ | nhập dồn, có thể đang làm ngoài hệ thống rồi nhập bù |
| Bấm hộ người khác / được người khác bấm hộ | ✅ `on_behalf_of` | ai tự làm, ai nhờ hành chính |
| Nhập tay hay nhập file, tỷ lệ dòng lỗi khi nhập | ✅ | thạo nhập hàng loạt hay không |
| Việc dự án đúng hạn / quá hạn, cập nhật tiến độ đều không | ✅ `tab_work_task` | cách theo dõi việc của chính mình |

### 3.4 Phản hồi và phối hợp

| Chỉ số | Nguồn | Đọc ra được gì |
|---|---|---|
| Thông báo: tỷ lệ đọc | ✅ | có theo dõi thông báo không |
| Thông báo: gửi → đọc mất bao lâu | 🆕 cần `read_at` | kênh thông báo có tới được người này không |
| Bị nhắc tên → trả lời mất bao lâu | ✅ | phản hồi trong hệ thống hay ngoài (Zalo) |
| Số bình luận trên phiếu của mình / của người khác | ✅ | trao đổi qua hệ thống nhiều hay ít |
| Hỏi trợ lý AI: số câu, chủ đề hay hỏi, việc AI làm thay | ✅ | dựa vào AI cho việc gì, có chỗ nào nên làm thành nút riêng |

### 3.5 Mức thành thạo

| Chỉ số | Nguồn | Đọc ra được gì |
|---|---|---|
| Lưu bộ lọc, tùy chỉnh cột | ✅ | người dùng thạo |
| Lỗi nhập bị chặn khi lưu (422) trên 100 lần lưu | ✅ | hay nhập sai ở form nào |
| Tìm kiếm không ra kết quả | 🆕 | không biết tìm thế nào, hoặc dữ liệu thiếu |
| Xem bài hướng dẫn / FAQ, gửi yêu cầu hỗ trợ | 🆕 / ⚠️ `ticket` | đang tự học hay cần người kèm |
| Xuất Excel so với xem trên màn | ✅ | đang xử lý số liệu ngoài hệ thống |
| Xu hướng các chỉ số trên qua 4–8 tuần | ✅ | đang tiến bộ hay đứng yên |

### 3.6 An toàn tài khoản

| Chỉ số | Nguồn | Đọc ra được gì |
|---|---|---|
| Đăng nhập từ IP / thiết bị chưa từng thấy | ✅ | có thể bị lộ mật khẩu |
| Nhiều phiên song song, nhiều nơi cùng lúc | ✅ | tài khoản dùng chung |
| Xuất số dòng vượt xa mức thường của chính người đó | ✅ | rủi ro mang dữ liệu ra ngoài |
| Xóa hàng loạt trong thời gian ngắn | ✅ | thao tác nhầm hoặc cố ý |
| Quyền được cấp nhưng 90 ngày không dùng | ✅ | quyền thừa, nên thu lại |
| Đã nghỉ việc mà tài khoản vẫn hoạt động | ⚠️ trạng thái nhân sự × `user` | lỗ hổng khi nhân viên nghỉ |

---

## 4. Nhận diện kiểu làm việc

Ghép các chỉ số ở mục 3 thành **kiểu** dễ hiểu. Một người có thể thuộc nhiều kiểu. Luôn **so với người cùng vai trò**, không so chung toàn công ty.

| Kiểu | Dấu hiệu | Gợi ý xử lý |
|---|---|---|
| **Làm dồn** | phiếu dồn cuối tháng, xử lý theo lô, bản đồ nhiệt có vài cột rất đậm | nhắc định kỳ, kiểm có đang làm ngoài hệ thống rồi nhập bù không |
| **Nút thắt duyệt** | tới lượt mình → xử lý chậm hơn hẳn trung vị nhóm, nhiều phiếu đang chờ | nhắc tự động, ủy quyền duyệt, duyệt trên điện thoại |
| **Dùng Excel song song** | xuất Excel nhiều, cùng một bộ lọc xuất hằng tuần, ít xem trên màn | làm báo cáo đó ngay trong hệ thống |
| **Người mới đang vướng** | tỷ lệ lỗi nhập cao, bỏ ngang form, nhiều 403, xem nhiều hướng dẫn, ít ngày dùng | kèm 1–1, chỉ đúng màn/bài cần xem |
| **Người thạo** | lưu bộ lọc, ít lỗi, lập phiếu nhanh, dùng rộng nhiều màn | mời làm người hướng dẫn cho phòng, hỏi ý kiến khi sửa màn |
| **Hay đi lạc** | nhiều 403, đường đi vòng vèo, màn mở đầu thay đổi liên tục | rà lại menu và quyền, ẩn mục không có quyền |
| **Làm trên điện thoại** | phần lớn thao tác từ điện thoại | ưu tiên kiểm màn của người đó trên khổ điện thoại |
| **Phiếu kém chất lượng** | bị trả về nhiều, sửa sau khi gửi nhiều, thiếu đính kèm | đào tạo lại bước lập phiếu, thêm kiểm tra khi nhập |
| **Nhờ làm hộ** | phần lớn phiếu do người khác bấm hộ | xem có cần tài khoản không, hoặc cần đào tạo |
| **Ít dùng** | ít ngày có vào **sau khi đã trừ ngày nghỉ và phần được bấm hộ** | hỏi lý do: công việc không cần, hay đang làm ngoài hệ thống |

---

## 5. Ví dụ một hồ sơ

```
NGUYỄN VĂN A · Nhân viên mua hàng · Phòng Thu mua · dùng hệ thống 120 ngày · kỳ: tuần 42/2026

NHỊP LÀM VIỆC     vào 5/5 ngày làm việc · thường 8:10–17:30 · 2 phiên/ngày · 85% máy tính
TRANG HAY VÀO     1. Danh sách ĐMH (34%)  2. YCBG (22%)  3. Báo cáo tiến độ mua (11%)  4. Thông báo (8%)
                  màn mở đầu ngày: Thông báo · ở lâu nhất: form ĐMH (TB 6 phút 40 giây, nhóm 4 phút)
CÁCH LÀM TASK     lập 14 ĐMH · lưu nháp TB 3 lần trước khi gửi (nhóm 1) · 2/14 bị trả về
                  xử lý YCBG được giao: trung vị 4 giờ (nhóm 1 ngày) · 40% phiếu tạo thứ Sáu chiều
PHẢN HỒI          đọc thông báo sau TB 25 phút · trả lời nhắc tên sau TB 2 giờ
THÀNH THẠO        lỗi nhập 18/100 lần lưu (nhóm 6), chủ yếu ở trường «Ngày giao» · chưa lưu bộ lọc nào
AN TOÀN           không có gì bất thường

KIỂU              Xử lý nhanh khi được giao · Đang vướng ở form ĐMH · Làm dồn chiều thứ Sáu
GỢI Ý             chỉ cách chọn «Ngày giao» · xem bài «Lập ĐMH từ YCBG» · rà lại trường Ngày giao trên form
```

---

## 6. Ghi thêm sự kiện giao diện

Không có phần này thì mục 3.2 chỉ dừng ở mức phân hệ. Đề xuất:

- **Bảng `tab_ui_event`**: `user_id`, `session_id`, `event_type` (**SMALLINT + IntEnum** theo luật R2: xem màn, rời màn, mở form, lưu form, bỏ form, tìm kiếm, lỗi giao diện), `route_pattern` (dạng `/purchase-orders/:id`, **không chứa id thật**), `module`, `duration_ms`, `meta` JSON nhỏ có giới hạn kích thước, `created_at`.
- **Giao diện**: một hook ở router ghi xem màn/rời màn (thời gian ở lại tính theo lúc tab đang hiển thị); `logger.error` gửi lỗi giao diện. Đệm trong bộ nhớ, gửi **theo lô** mỗi 30 giây và lúc rời trang (`navigator.sendBeacon`).
- **Đường API nhận sự kiện không ghi vào `tab_request_log`** — nếu không mỗi lô lại đẻ thêm một dòng nhật ký. Phải thêm ngoại lệ trong `core/logging_policy.py`, vì `SKIP_GET_PREFIXES` hiện chỉ áp cho GET.
- Thêm `tab_notification.read_at`.
- **Gom theo ngày** vào `tab_usage_daily` (người × ngày × phân hệ) bằng Celery chạy đêm; sự kiện thô giữ 90 ngày, số gom giữ lâu hơn để xem xu hướng.
- Tìm kiếm: chỉ ghi "có tìm, ra bao nhiêu kết quả", **không ghi từ khóa** trừ khi được chốt (từ khóa có thể chứa tên người, số tiền).

---

## 7. Cho AI đọc hồ sơ để nhận xét

1. **AI không đọc nhật ký thô.** `tab_request_log` khoảng 7.400 lượt GET/ngày: đưa vào là tốn tiền, AI **đếm sai** mà vẫn nói rất chắc, lại lộ dữ liệu. Máy tính số, AI chỉ diễn giải.
2. **Luồng:** `tab_usage_daily` → job tuần dựng `tab_user_usage_snapshot` (1 dòng/người/kỳ: JSON chỉ số mục 3 + trung vị nhóm cùng vai trò + xu hướng 4 kỳ + kiểu ở mục 4) → công cụ AI `usage_profile(user_id, ky)` khai qua `tool_defs` / `run_tool` của `agent_hub`, gác quyền → AI viết nhận xét → lưu `tab_user_usage_review` kèm `snapshot_id` đã dùng.
3. **Mỗi chỉ số đưa AI phải kèm ngữ cảnh:** trung vị nhóm cùng vai trò, xu hướng, ý nghĩa ngắn, **số ngày nghỉ phép**, **số phiếu được bấm hộ**, và **chỉ số nào chưa đo được** — thiếu mấy thứ này AI sẽ kết luận "ít dùng" với người đang nghỉ phép.
4. **Chỉ đưa số và mã**, không đưa văn bản tự do (bình luận, từ khóa) → tránh lộ dữ liệu và tránh câu lệnh lừa AI nằm trong dữ liệu.
5. **Kết quả bắt buộc:** mỗi nhận định ghi rõ chỉ số làm bằng chứng + mức tin cậy + phần "không đủ dữ liệu". Sau khi AI viết, một hàm đối chiếu mọi con số trong nhận xét với snapshot; số nào không có trong snapshot thì bỏ nhận định đó.
6. **Nhóm quá nhỏ** (vai trò < 5 người): so với toàn công ty và ghi rõ là đang so như vậy.
7. Chạy theo tuần, mỗi snapshot cho AI đọc một lần rồi lưu kết quả, không gọi lại mỗi lần mở màn.
8. Bộ mẫu kiểm (`agent_hub/core_eval.py` đã có khung): vài snapshot giả có đáp án đúng, để kiểm AI không kết luận sai trước khi bật thật.

---

## 8. Ai được xem và minh bạch (ĐÃ CHỐT — duoc-CR-641)

| Người xem | Thấy gì |
|---|---|
| Admin hệ thống (và người admin chủ động giao thêm) | hồ sơ của MỌI người |
| Chính người đó · quản lý trực tiếp · đồng nghiệp | **không thấy** — không có đường «hồ sơ của tôi» |

- **Gác quyền theo mẫu báo cáo chuẩn:** `ReportKey.USAGE_PROFILE = 14` («Hồ sơ cách làm việc», nhóm «Quản trị») + `require_report` trên CẢ 4 đường
  (`/summary`, `/summary/export`, `/cohorts`, `/{user_id}`), kèm `require("setting", "read"|"export")`. Chưa gán = ĐÓNG; vai trò `admin` /
  `ADMINISTRATOR` được gán sẵn bởi `ensure_report_access_defaults` mỗi lần khởi động. Admin giao thêm cho người khác ở Phân quyền → tab «Báo cáo»
  (người đó vẫn phải có `setting.read`). Không lọc phạm vi theo phòng ban.
- **Mục đích sử dụng (chủ sản phẩm chốt):** hồ sơ **có thể được dùng làm một căn cứ tham khảo khi đánh giá hiệu quả làm việc**. Vì vậy văn bản
  thông báo cho nhân viên (mục 12) phải nói rõ điều này, và hồ sơ luôn hiện kèm bằng chứng, nhóm đang so sánh, ngữ cảnh nghỉ phép / bấm hộ, và
  danh sách chỉ số «chưa đo được». Khuyến nghị đọc theo **kết quả** (thời gian xử lý, bị trả về, lỗi nhập) hơn là theo số lượt có mặt; 4 tuần đầu coi nhãn
  là thử nghiệm.
- **Dấu vết xem:** mỗi lần admin mở hồ sơ để lại một dòng `tab_request_log` (GET không bị loại); xuất Excel còn ghi `tab_export_log` (entity `usage_profile`).
- **Công tắc thu thập sự kiện giao diện** `usage_tracking_enabled` (Cấu hình hệ thống → Hệ thống), **mặc định BẬT**. Tắt: `POST /api/telemetry/ui-events`
  nhận rồi bỏ (HTTP 204), không ghi gì; FE ngừng gửi (cờ `usage_tracking` ở `/api/auth/me`). Gom số từ nhật ký sẵn có (pha 1) luôn chạy.
- **Giữ bao lâu:** `tab_ui_event` 90 ngày; `tab_usage_daily`, `tab_user_usage_snapshot`, `tab_user_usage_label` **3 năm** (việc dọn `usage.cleanup_ui_events` 04:20).
- **Không ghi:** từ khóa tìm kiếm (chỉ màn + số kết quả), nội dung nhập vào biểu mẫu, id trong đường dẫn (route mẫu `/…/:id`), `query_string`/`request_body`/`response_body`.
- **Hai ứng dụng gửi (bao-CR-649):** app cũ thumua (`frontend/`) có bộ thu riêng `frontend/src/telemetry/` cùng hợp đồng, thân lô kèm `"app": 2`
  (ERP v2 không khai = 1). Cột `tab_ui_event.app` giữ nguồn; route thumua của YCMH / YCBG / ĐMH được máy chủ quy về route v2
  (`/purchase-orders/:id` → `/procurement/purchase-orders/:id`, `canonical_route`) để báo cáo không tách đôi một màn. Số gom ngày cộng cả hai app;
  `GET /api/usage-profiles/by-app` trả số sự kiện tách theo app trong kỳ (90 ngày dữ liệu thô). Thumua chỉ đo biểu mẫu TẠO MỚI ba phiếu đó,
  không đo tìm kiếm; trang in `/print/...` nằm ngoài bố cục chung nên không đo.
- Người đó có chỗ phản hồi «nhận xét này sai vì…»: **chưa làm** (gắn với pha 4 / quy trình HR).

---

## 9. Lộ trình đề xuất

| Pha | Việc | Được gì |
|---|---|---|
| 1 | Gom `tab_usage_daily` từ dữ liệu có sẵn + màn hồ sơ cá nhân bản đầu | 3.1, 3.3 (trừ thời gian lập/bỏ form), 3.4 (trừ giờ đọc), 3.5 phần ✅, 3.6; trang truy cập ở mức phân hệ |
| 2 | Bảng `tab_ui_event` + hook giao diện + `read_at` | 3.2 đầy đủ (màn, thời gian ở lại, đường đi), thời gian lập phiếu, bỏ form, tìm kiếm |
| 3 | Nhận diện kiểu (mục 4) chạy tự động theo tuần | danh sách kiểu trên hồ sơ |
| 4 | Snapshot + công cụ AI + nhận xét có kiểm | AI viết nhận xét từng người |

---

## 10. Câu hỏi đã chốt / còn mở

1. ~~Quản lý trực tiếp xem được hồ sơ người trong phòng?~~ **Chốt: không.** Chỉ admin (và người admin giao thêm).
2. ~~Người dùng xem hồ sơ về chính mình?~~ **Chốt: không** (không có đường «của tôi»). Minh bạch bằng văn bản thông báo (mục 12).
3. ~~Hồ sơ làm căn cứ KPI / đánh giá?~~ **Chốt: CÓ THỂ dùng làm căn cứ tham khảo khi đánh giá** — phải nói rõ trong thông báo.
4. **CÒN MỞ — cần pháp chế / nhân sự duyệt** văn bản thông báo (mục 12) và hình thức xác nhận của nhân viên **trước khi** để công tắc BẬT trên prod
   (mặc định hiện là BẬT — xem rủi ro ở mục 13).
5. ~~Ghi từ khóa tìm kiếm?~~ **Chốt: không.**
6. SLA xử lý từng loại phiếu: **CÒN MỞ**. Tạm dùng «≥ 2× trung vị nhóm VÀ ≥ 8 giờ» cho nhãn Nút thắt duyệt (`label_thresholds.py`).
7. ~~Giờ hành chính / T7?~~ **Chốt:** «ngoài giờ» theo **Lịch làm việc từng người** (mặc định hệ thống T2–T7 08:00–17:00), trừ ngày lễ; ngày nghỉ phép đã duyệt không tính vào mẫu số ngày làm việc.
8. ~~Pha 1 trước hay Pha 2?~~ **Chốt:** làm cả pha 1–3 trong một CR.
9. Model AI / ngân sách (pha 4): **CÒN MỞ**, ngoài phạm vi CR này.
10. Thời hạn giữ số gom: **Chốt 3 năm** (`tab_usage_daily`, snapshot, nhãn).

---

## 11. Lệch so với thiết kế gốc (duoc-CR-641)

| Thiết kế gốc | Bản làm | Lý do |
|---|---|---|
| Gửi lô bằng `navigator.sendBeacon` | `fetch(..., {keepalive: true})` kèm `Authorization: Bearer` | FE không dùng cookie phiên; `sendBeacon` không mang được header |
| «Số phiên/ngày» theo phiên đăng nhập | **Phiên làm việc** = chuỗi lượt (request ∪ sự kiện giao diện) ngắt khi nghỉ > 30 phút | phiên đăng nhập sống 7 ngày nên không phản ánh «vào / ra» |
| Bấm hộ theo `audit.on_behalf_of` | Phiếu có người đề nghị ≠ người tạo (nghỉ phép / YCMH / đóng dấu) + `tab_approval_action.on_behalf_of_id` | `audit.on_behalf_of` hiện không lời gọi nào điền (luôn 0) |
| Mốc «tới lượt» = lúc tạo việc duyệt | Bước **lần lượt**: lúc người liền trước quyết định (đọc `flow_snapshot`) | việc lần lượt được tạo sẵn ở trạng thái chờ |
| Giữ số gom «lâu dài» | 3 năm | chủ sản phẩm chốt |
| Thu thập mặc định TẮT | mặc định **BẬT** (có công tắc) | chủ sản phẩm chốt |
| Đường đi A→B→C trên toàn cửa sổ | chỉ **tuần cuối** của cửa sổ, từ sự kiện thô (còn trong 90 ngày) | giới hạn bộ nhớ job (~30k dòng/tuần) |
| Chỉ số HOÃN / BỎ | xem `plans/261019-1450-tracking-ho-so-lam-viec-cr641/metric-definitions.md` và `metric_catalog.DEFERRED_METRICS`: duyệt YCMH/ĐMH ngoài bộ máy duyệt · tách bình luận mình/người khác · lỗi 422 theo trường · quyền 90 ngày không dùng · chủ đề hay hỏi trợ lý AI | thiếu nguồn tin cậy hoặc trái nguyên tắc §7.4 |

Công thức và nguồn từng chỉ số: bảng ở `plans/261019-1450-tracking-ho-so-lam-viec-cr641/metric-definitions.md`; mã: `backend/app/modules/usage_profile/` (`metric_catalog.py` là danh mục khóa cố định).

---

## 12. Văn bản thông báo cho nhân viên (BẢN NHÁP — HR / pháp chế duyệt trước khi gửi)

> **Thông báo về việc ghi nhận cách sử dụng hệ thống ERP**
>
> Từ ngày …/…/…, hệ thống ERP của DEGO Holding ghi nhận **cách sử dụng hệ thống** của từng tài khoản nhằm cải tiến màn hình, hỗ trợ đào tạo
> và **làm một căn cứ tham khảo khi đánh giá hiệu quả làm việc**.
>
> **Những gì được ghi:** màn hình đã mở và thời gian ở lại; số lần mở, lưu, bỏ dở biểu mẫu; số lần tìm kiếm và số kết quả tìm thấy
> (**không ghi nội dung tìm kiếm**); lỗi hiển thị; giờ thao tác (trong / ngoài giờ làm việc theo lịch của bạn); loại thiết bị; số phiếu lập, gửi, duyệt, bị trả về;
> thời gian xử lý các việc duyệt; số lần xuất dữ liệu. Hệ thống **không ghi nội dung bạn nhập vào biểu mẫu** và không ghi số hiệu chứng từ trong đường dẫn.
>
> **Ai xem được:** chỉ **quản trị hệ thống** và những người được quản trị hệ thống giao quyền xem báo cáo «Hồ sơ cách làm việc». Quản lý trực tiếp và đồng nghiệp
> không tự xem được. Mỗi lần mở hồ sơ đều để lại dấu vết.
>
> **Dùng để làm gì:** (1) cải tiến phần mềm và hướng dẫn sử dụng; (2) hỗ trợ, đào tạo người dùng; (3) **tham khảo, cùng với kết quả công việc thực tế và đánh giá của quản lý,
> khi xem xét hiệu quả làm việc**. Số liệu không phải căn cứ duy nhất để kết luận về cá nhân; ngày nghỉ phép đã duyệt được loại khỏi phần tính, và hệ thống
> ghi rõ chỉ số nào chưa đo được.
>
> **Thời gian lưu:** dữ liệu chi tiết tự xóa sau **90 ngày**; số liệu tổng hợp theo ngày và theo tuần được giữ **3 năm** để xem xu hướng.
>
> **Quyền của bạn:** nếu thấy số liệu về mình chưa đúng, liên hệ phòng Nhân sự để được xem xét. Thắc mắc khác liên hệ phòng Nhân sự / bộ phận phụ trách hệ thống.

**Khuyến nghị:** pháp chế và Nhân sự rà văn bản này (căn cứ pháp lý về dữ liệu cá nhân của người lao động, hình thức thông báo / xác nhận đã đọc, quy chế nội bộ) **trước khi** bật thu thập trên môi trường thật.
Câu «làm một căn cứ tham khảo khi đánh giá» là ý chủ sản phẩm đã chốt; nên đối chiếu với nội quy lao động và quy chế đánh giá hiện hành.

---

## 13. Vận hành

- **Việc nền (Celery, giờ VN):** `usage.cleanup_ui_events` 04:20 · `usage.aggregate_daily` 04:30 (gom HÔM QUA) · `usage.build_weekly_snapshots` thứ Hai 05:15 (tuần vừa kết thúc; tự gom bù ngày còn thiếu).
- **Gom bù lịch sử:** `docker compose exec api python -m app.modules.usage_profile.backfill --days 90` (tuần tự, ngủ 0,2 giây giữa các ngày, lỗi một ngày không chặn ngày khác). Chỉ lùi được ≤ 90 ngày vì dòng GET của `tab_request_log` bị dọn sau 90 ngày.
- **Dựng snapshot tay:** `celery call usage.build_weekly_snapshots --args '["2026-10-12"]'` (thứ Hai của tuần cần dựng).
- **Migration:** `usgprof01` (4 bảng + `tab_notification.read_at` + 4 chỉ mục: `tab_notification.created_at`, `tab_audit_log.created_at`, `tab_export_log.created_at`, `tab_approval_task.decided_at`). `ADD INDEX` trên `tab_audit_log` (bảng phân vùng) chạy online, nên chạy giờ thấp điểm.
- **Tắt khẩn cấp:** Cấu hình hệ thống → «Thu thập cách dùng giao diện» → TẮT (có hiệu lực ≤ 30 giây do bộ nhớ đệm cấu hình).
- **Rủi ro cần biết:** công tắc mặc định BẬT — môi trường mới tạo sẽ thu thập ngay từ lần khởi động đầu. Muốn tắt sẵn cho prod trước khi HR gửi thông báo thì đặt `USAGE_TRACKING_ENABLED=false` ở `.env` hoặc tắt ở màn Cấu hình ngay sau khi deploy.
- **Danh sách khóa API và hình dạng JSON:** xem `backend/app/modules/usage_profile/controller.py` và các tệp `list_service.py`, `profile_service.py`, `cohort_service.py` (có bài kiểm khóa từng trường ở `test/backend/test_ho_so_lam_viec_api_cr641.py`).
