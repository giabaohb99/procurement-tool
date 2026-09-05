# PHA 2 — Luồng duyệt 2 cổng (TBP + Văn thư)

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **CHƯA LÀM**.
> ⚠️ Đây là luồng **chuyển trạng thái trực tiếp theo quyền** (như Đặt xe PHA 3). Bản nối engine
> đa-bước ở [phase-5-runtime-duyet-va-test.md](phase-5-runtime-duyet-va-test.md).

## Mục tiêu
Cho phiếu chạy hết vòng đời qua **2 cổng**: **Trưởng bộ phận** (Duyệt / Yêu cầu chỉnh sửa / Từ chối)
→ **Văn thư** (Hoàn thành sau khi đóng dấu / Yêu cầu chỉnh sửa / Từ chối). Chốt chặn thật ở backend,
không chỉ ẩn nút.

## Phạm vi & việc cụ thể
- [ ] **Cổng 1 — TBP** (`approve`): `approve_seal` (Chờ duyệt→Đã duyệt) · `return_seal` (→Yêu cầu chỉnh sửa, +lý do) · `reject_seal` (→Từ chối, +lý do).
- [ ] **Cổng 2 — Văn thư** (`write`, phạm vi `company`): `complete_seal` (Đã duyệt→Hoàn thành; nhập **số bản đã đóng** + ghi chú) · `return_seal` (Đã duyệt→Yêu cầu chỉnh sửa) · `reject_seal` (Đã duyệt→Từ chối).
- [ ] Ghi lý do có nhãn vào `note` (`_append_note`): *"{Tên} - Yêu cầu chỉnh sửa - Lý do: …"*, *"{Tên} - Từ chối - …"*, *"{Tên} - Đã đóng dấu {n} bản"*.
- [ ] Kiểm **trạng thái nguồn** mỗi chuyển (chỉ Duyệt được *Chờ duyệt*; chỉ Hoàn thành được *Đã duyệt*).
- [ ] `submit` lại sau *Yêu cầu chỉnh sửa* → về *Chờ duyệt* (mặc định — quyết định còn mở B).
- [ ] FE: `SealWorkflowActions` bày **cụm nút theo vai trò + trạng thái**; dialog **nhập lý do** + dialog **Hoàn thành** (số bản/ghi chú) là **popup** (C-01).

## Thiết kế kỹ thuật
| Chuyển | Endpoint | Hàm service | Nguồn hợp lệ |
|---|---|---|---|
| Duyệt | `POST /api/seal-requests/{id}/approve` | `approve_seal` | Chờ duyệt |
| Yêu cầu chỉnh sửa | `.../{id}/return` (+ `ReasonIn`) | `return_seal` | Chờ duyệt · Đã duyệt |
| Từ chối | `.../{id}/reject` (+ `ReasonIn`) | `reject_seal` | Chờ duyệt · Đã duyệt |
| Hoàn thành (đóng dấu) | `.../{id}/complete` (+ `CompleteSealIn`) | `complete_seal` | Đã duyệt |

- `CompleteSealIn`: `copies_done: int` (mặc định = `copies`), `note: str` (ghi chú đóng dấu). Ghi audit + `_append_note`.
- Chốt chặn quyền: `require("seal_request","approve")` cho cổng 1; `require("seal_request","write")` cho cổng 2. Lấy phiếu qua `get_scoped` (Văn thư phạm vi `company` → chỉ thấy phiếu công ty mình).
- Cụm nút FE (`SealWorkflowActions`) bày theo `can(entity, action)` **và** trạng thái phiếu — nhưng backend là chốt thật.
- Nút **In phiếu** (đặt ở PHA 4) chỉ hiện khi *Hoàn thành* (tùy chọn).

## Cấu hình / migration
- Không thêm cột/ENV — dùng cột đã có (status, copies, note).
- Seed dữ liệu mẫu đủ trạng thái: `scripts/seed_duyetdau_demo.py` (Nháp/Chờ duyệt/Đã duyệt/Hoàn thành/Từ chối/YCCS).

## Chống trùng / Idempotent
- Mỗi chuyển kiểm **trạng thái nguồn** → bấm lại không nhảy sai (Duyệt phiếu đã duyệt → 400).
- `complete_seal` chấm audit "đóng dấu", phiếu sang *Hoàn thành* — không lặp.

## Kiểm thử & tiêu chí
- End-to-end 2 cổng qua tài khoản khác vai trò: NS tạo+gửi → TBP duyệt → Văn thư hoàn thành → *Hoàn thành*.
- Nhánh: TBP Yêu cầu chỉnh sửa → NS sửa → gửi lại → Chờ duyệt; TBP Từ chối → khóa; Văn thư Yêu cầu chỉnh sửa (chụp lại chữ ký) → NS sửa → lại Chờ duyệt.
- Văn thư công ty A **không** hoàn thành được phiếu công ty B (phạm vi `company`).
- Lý do Trả/Từ chối + "Đóng dấu n bản" hiện đúng trong `note` / `AuditTimeline`.

## Rủi ro & lưu ý
- **Hai cổng dùng chung `/return` `/reject`** nhưng nguồn khác nhau — kiểm nguồn kỹ để cổng 2 không "duyệt lại".
- Quyết định còn mở **B** (Văn thư trả → về TBP hay thẳng Văn thư): mặc định về TBP; nếu khách muốn bỏ qua TBP thì thêm nhánh `submit` → *Đã duyệt*.
- Chưa gắn thông báo ở phase này (để PHA 3) — chuyển trạng thái xong chưa ai được báo; đừng quên nối ở PHA 3.
