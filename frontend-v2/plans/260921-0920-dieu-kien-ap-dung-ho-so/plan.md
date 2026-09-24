# Điều kiện áp dụng của hồ sơ

Khai trên từng tờ hồ sơ: *giấy này phải kèm theo chứng từ nào*. Chứng từ nào có
dòng hàng khớp điều kiện thì trang chi tiết của nó mọc ra thẻ **«Hồ sơ cần kèm»**.

## Chốt (đại ca, 21/09/2026)

| Hạng mục | Chốt |
|---|---|
| Màn áp dụng | YCMH · ĐMH · YCBG · Phiếu khảo sát |
| Chiều điều kiện | `product_code` (Sản phẩm) · `item_group` (Phân loại VTBB/NL) |
| Cách hiện | Thẻ «Hồ sơ cần kèm» cuối trang chi tiết, kèm **lý do khớp** |
| Khai ở đâu | Trên **từng hồ sơ** (không phải trên Loại hồ sơ) |

## Va chạm dữ liệu đã biết

**Dòng YCBG không có `product_code`.** `tab_survey_request_line` chỉ có
`item_group`; mã SP chỉ nằm ở `tab_survey_request_option.system_product_code`,
có sau khi khảo sát xong và **không bắt buộc**. Chốt: YCBG lấy mã SP của
**phương án ĐÃ CHỌN** (`is_chosen`), chưa chọn thì dòng đó không có SP để khớp.
Điều kiện theo sản phẩm vì vậy **im lặng không khớp** trên YCBG giai đoạn đầu —
giao diện phải nói ra, đừng để người khai tưởng mình khai sai.

**Phiếu khảo sát không có bảng dòng hàng.** `item_group` + `item_code` nằm ở
HEADER (`tab_survey`), nên bối cảnh khớp của nó là một "dòng" duy nhất.

## Nguồn mượn lại

`backend/app/modules/approval/condition_service.py` — DSL `[{field, op, value}]`
nối bằng VÀ, hỏng thì coi như không khai chứ không nổ. Dùng lại **hình dạng và
lý lẽ**, không import chéo (bộ máy duyệt đọc bối cảnh PHIẾU, cái này đọc DÒNG).

## Phase

| # | Việc | Trạng thái |
|---|---|---|
| 01 | Backend: 2 cột + `applicability.py` + API `/api/dossiers/applicable` + migration | ☐ |
| 02 | Giao diện khai điều kiện trong form hồ sơ | ☐ |
| 03 | Thẻ «Hồ sơ cần kèm» + gắn vào 4 trang chi tiết | ☐ |
| 04 | Bài kiểm + tài liệu | ☐ |

## Luật phải giữ

- **`apply_doc_kinds` rỗng = không bao giờ hiện.** Không khai thì hồ sơ đứng yên
  trong kho như trước, đúng hành vi của 100% hồ sơ đang có.
- **`apply_doc_kinds` có + `apply_conditions` rỗng = áp cho MỌI phiếu loại đó.**
  Đây là ca thật (giấy phép kinh doanh kèm mọi ĐMH) nhưng dễ bật nhầm — giao
  diện phải nói thành câu, đừng để suy ra từ một bảng trống.
- **Gác HAI cửa ở API.** `dossier.read` + `apply_scope` cho hồ sơ, **và**
  `get_scoped` trên chính chứng từ nguồn. Thiếu cửa thứ hai thì câu lý do
  («vì dòng 3 có SP-001») thành cửa dò nội dung đơn hàng của phòng khác.
- **Câu lý do dựng ở BACKEND** — cùng lối `approval/steps_service._summary`, vì
  sau này bản in cần đúng câu đó.
