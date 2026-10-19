# TRACKING NGƯỜI DÙNG — HỒ SƠ CÁCH LÀM VIỆC CỦA TỪNG NGƯỜI

**Bản:** 1.0 — 19/10/2026 · **CR:** duoc-CR-626 · **Trạng thái: ĐỀ XUẤT, chưa gõ mã.**
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

## 8. Ai được xem và minh bạch

| Người xem | Thấy gì |
|---|---|
| Chính người đó | toàn bộ hồ sơ của mình + gợi ý (nên mở cho xem trước tiên) |
| Quản lý trực tiếp | hồ sơ người trong phòng mình |
| Admin hệ thống | phần an toàn tài khoản của mọi người |

- Gác bằng một `ReportKey` mới + `require_report` (luật duoc-CR-562) và phạm vi theo phòng ban.
- **Thông báo cho nhân viên** là hệ thống có ghi lại cách dùng và ai xem được — đây là dữ liệu cá nhân.
- Người đó có chỗ phản hồi "nhận xét này sai vì…".
- Lưu ý khi dùng: biết bị đo theo số lượt vào thì người ta sẽ bấm cho có, chỉ số mất nghĩa. Nên đọc hồ sơ theo **kết quả** (thời gian xử lý, bị trả về, lỗi nhập) hơn là theo số lượt có mặt.

---

## 9. Lộ trình đề xuất

| Pha | Việc | Được gì |
|---|---|---|
| 1 | Gom `tab_usage_daily` từ dữ liệu có sẵn + màn hồ sơ cá nhân bản đầu | 3.1, 3.3 (trừ thời gian lập/bỏ form), 3.4 (trừ giờ đọc), 3.5 phần ✅, 3.6; trang truy cập ở mức phân hệ |
| 2 | Bảng `tab_ui_event` + hook giao diện + `read_at` | 3.2 đầy đủ (màn, thời gian ở lại, đường đi), thời gian lập phiếu, bỏ form, tìm kiếm |
| 3 | Nhận diện kiểu (mục 4) chạy tự động theo tuần | danh sách kiểu trên hồ sơ |
| 4 | Snapshot + công cụ AI + nhận xét có kiểm | AI viết nhận xét từng người |

---

## 10. Câu hỏi chưa chốt

1. Quản lý trực tiếp xem được hồ sơ người trong phòng, hay chỉ ban lãnh đạo/admin?
2. Người dùng có được xem hồ sơ và nhận xét AI về chính mình không? (đề xuất: có)
3. Hồ sơ có được dùng làm căn cứ đánh giá KPI/nhân sự không?
4. Có cần thông báo bằng văn bản / xin đồng ý của nhân viên trước khi bật Pha 2 không? (hỏi pháp chế, nhân sự)
5. Có ghi từ khóa tìm kiếm không?
6. SLA xử lý cho từng loại phiếu là bao lâu? (để so "xử lý chậm")
7. Giờ hành chính chuẩn, có tính thứ Bảy không? (để tính "ngoài giờ")
8. Làm Pha 1 trước để có số ngay, hay làm luôn Pha 2?
9. Dùng model AI nào, ngân sách AI mỗi tháng?
