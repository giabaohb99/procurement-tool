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
| **bao-CR-310-xu-ly-phuong-an-tren-ycmh** | 2026-09-07 | Khách | Cho XỬ LÝ KHẢO SÁT ngay trên Yêu cầu mua hàng: NSTM gắn phương án (NCC + giá) lên từng dòng YCMH, chốt rồi lên thẳng ĐMH — thay cho hướng gộp YCMH vào YCBG của cụm bao-CR-277..291 (đã khai tử, xem ghi chú ở tệp chung). YCBG giữ nguyên không đụng. **Chia 4 đợt, bảng đợt ở mục H.8 của tài liệu chức năng.** **Đợt 1 XONG** (nền + API): bảng `tab_purchase_request_item_option` (migration `6835fb9cfecd`) — bảng RIÊNG, cố ý không nhét chung `tab_survey_request_option` để khỏi đẻ cột nghĩa kép; snapshot giá tại thời điểm gắn nên phiếu khảo sát sửa giá sau đó không làm đổi phương án đã chốt; **không** thêm cột "đã chốt" lên dòng YCMH mà suy từ `is_chosen`. 6 API dưới `/{pid}/items/{item_id}/options` (liệt kê · gắn từ kho khảo sát · nhập tay · sửa · xóa · chốt), cổng mở khi phiếu ở `dispatched`/`processing`/`purchasing`/`purchased`. **Ba quyết định phân quyền:** (1) **NSTM gắn, NGƯỜI YÊU CẦU chốt** — NSTM chỉ biết giá bao nhiêu, người yêu cầu mới biết giá đó còn đáng mua không; (2) ai có `purchase_request.approve` (quản lý / admin thu mua) chốt thẳng được cho hàng gấp — khóa này chia đúng ranh giới sẵn có, `pur_staff` không có nên không cần khóa quyền mới; (3) nhập tay chỉ đòi `supplier.read` chứ KHÔNG đòi `supplier.write` — `pur_staff` không có `write`, đòi `write` là khóa chết đúng người dùng nó, mà `write` còn là quyền sửa cả danh mục NCC nên rộng quá mức. Vì thế `choose` gác bằng `read` (người yêu cầu thường chỉ có `read` sau khi phiếu đã duyệt) rồi để `ensure_can_choose` phân xử. Ẩn NCC bám luật cụm `pur` của Task 4. **Kèm theo: BỎ bắt buộc Mã hàng trên dòng YCMH** (`required-fields.ts`) — giống phiếu khảo sát vốn có cả loại có mã lẫn không mã, người yêu cầu phải mua được thứ chưa nằm trong danh mục mà không phải chờ mở mã. Đánh đổi phải biết: `sync_from_purchase_orders` nối ĐMH về YCMH bằng **chuỗi `product_code`** nên dòng KHÔNG MÃ không được cộng tiến độ `qty_ordered`/`qty_received` tự động, NSTM phải tự đặt `line_status` — muốn hết thì phải nối bằng khóa dòng, xem N-004. Luật cũ vẫn còn ở bản v1 (`PurchaseRequestDetail.tsx`) vì `frontend/` đóng băng, chờ khách quyết. Kịch bản nghiệm thu + dữ liệu demo: `backend/scripts/demo_cr310.py` (CHỈ local). Test: `test_ycmh_phuong_an_cr310.py` (21 ca) + `required-fields.test.ts`. **Còn lại: đợt 2** gom phương án đã chốt theo NCC → sinh N đơn mua hàng, **đợt 3** màn *Xử lý phương án* ở frontend-v2 (hiện chưa có một dòng giao diện nào — nên đợt 3 sẽ làm TRƯỚC đợt 2), **đợt 4** hai bản in (bản A cho người yêu cầu: dùng lại phiếu đề xuất mục F, in CHUNG MỘT BẢNG dù nhiều NCC, không cột NCC theo dòng; bản B cho thu mua: tick NCC → in nháp đơn, mỗi NCC một trang) + HDSD. | erp-v2 | Đang làm — xong đợt 1 | `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md` mục H |

---

## Nhật ký deploy môi trường thật

Chỉ ghi deploy của các CR trong tệp này. Deploy cũ nằm ở cuối `change-log.md`.

| Ngày | Môi trường | Nội dung | Ghi chú |
|---|---|---|---|
| — | — | *(chưa có)* | — |
