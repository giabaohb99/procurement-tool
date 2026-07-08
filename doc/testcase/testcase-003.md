# TESTCASE-003 — Đồng bộ Sản phẩm (Mã HH) & Đơn hàng (tự gắn HH + chọn SP autocomplete)

> Bộ test cho phần triển khai ngày **2026-07-07**: đồng bộ 6.760 sản phẩm từ sheet *2. DATA NL, VTBB* (thêm **Mã HH / Tên SP HH**, chuẩn hóa phân loại), và **Đơn hàng** tự gắn Mã HH/Tên HH khi chọn SP + đổi ô chọn SP thành **autocomplete tìm kiếm**.
>
> URL Web: local `http://localhost:8080` · VPS `https://thumua.degoholding.vn`
> Đăng nhập bằng **Mã nhân viên** hoặc **Email** + mật khẩu.
> Cột **KQ**: ☐ chưa test · ✅ đạt · ❌ lỗi (ghi chú ở cột cuối).

---

## 1. Tài khoản test

| Vai trò | Username | Mật khẩu | Quyền liên quan |
|---|---|---|---|
| Admin | `degoadmin` | theo `.env` (`dego2026`) | product full, purchase_order full |
| Thu mua (tạo PO) | `NSU211` | `NSU211` | purchase_order read/create/write |
| Quản lý thu mua | `NSU215` | `NSU215` | purchase_order + approve |

> Ghi chú dữ liệu: **6.760 SP**, trong đó **6.082 có Mã HH**. Nhóm **ICARE (304 SP) KHÔNG có Mã HH** trong sheet gốc → dùng để test trường hợp "không tự điền".
> SP có HH để test nhanh: `THC0003`→HH0003, `THI0006`→HH0006, `CPT0001`→HH0001 (lưu ý HH0001 có mã nhưng trống tên HH).

---

## 2. Test cases — Đồng bộ Sản phẩm (màn **Danh mục → Sản phẩm**)

| Mã | Nội dung | TK | Bước | Kết quả mong đợi | KQ | Ghi chú |
|---|---|---|---|---|---|---|
| **SP-01** | Danh sách hiển thị cột HH | admin | Mở **Sản phẩm** | Có 2 cột **Mã HH** và **Tên SP (HH)**; tổng ~6.760 SP; phân trang mượt | ☐ | |
| **SP-02** | Lọc theo Phân loại (đã gộp) | admin | Lọc **Phân loại** = `Nhãn` | Chỉ ra SP nhóm Nhãn (~4.011); KHÔNG còn nhóm rác `[Nhãn]` | ☐ | |
| **SP-03** | Phân loại đã chuẩn hóa | admin | Mở dropdown lọc Phân loại | 21 nhóm sạch (Nhãn, Nhãn thùng, Thùng, NL, ICARE…); không có `HỘP`/`[HỘP]`/`Nguyên liệu` | ☐ | |
| **SP-04** | Tìm nhanh theo Mã HH | admin | Ô tìm gõ `HH0003` | Ra SP `THC0003` (tìm khớp cả Mã HH) | ☐ | |
| **SP-05** | Tìm nhanh theo Tên SP HH | admin | Ô tìm gõ 1 phần tên HH (VD `Thanh Long`) | Ra SP có tên HH khớp | ☐ | |
| **SP-06** | Xem/sửa 1 SP có HH | admin | Mở `THC0003` | Thấy Mã HH `HH0003` + Tên SP HH; sửa lưu được | ☐ | |
| **SP-07** | SP nhóm ICARE trống HH | admin | Mở 1 SP nhóm ICARE (VD `VT00013`) | Mã HH / Tên HH **trống** (đúng — sheet không có) | ☐ | |
| **SP-08** | Export CSV | admin | **Xuất CSV** danh sách | File có cột đúng thứ tự: Phân Loại, Mã VTBB/NL, Tên VTBB/NL, Tên HĐ, Tên pháp lý, ĐVT, **Mã HH**, **Tên SP (HH)** | ☐ | |
| **SP-09** | Re-import idempotent | admin | Import lại chính file vừa export (hoặc file sheet) | Báo "cập nhật …", **KHÔNG tạo trùng**; tổng SP không đổi | ☐ | ⚠️ quan trọng |
| **SP-10** | Import bỏ dòng test/#N/A | admin | (tham chiếu) import file sheet gốc | Bỏ dòng tên `#N/A`/trống; gộp mã trùng; báo "bỏ qua N dòng" | ☐ | |

---

## 3. Test cases — Đơn hàng (màn **Mua hàng → Đơn hàng**)

| Mã | Nội dung | TK | Bước | Kết quả mong đợi | KQ | Ghi chú |
|---|---|---|---|---|---|---|
| **PO-01** | Mở PO cũ vẫn đúng | NSU211 | Mở 1 PO đã tạo trước đây | Dòng hàng hiện đúng mã/tên SP; sửa được (không vỡ do đổi ô chọn) | ☐ | ⚠️ regression |
| **PO-02** | Chọn SP bằng autocomplete | NSU211 | Tạo PO mới → dòng hàng, ô **Mã hàng** gõ `THC` | Hiện danh sách gợi ý (mã · nhóm / tên / dòng HH); chọn được | ☐ | |
| **PO-03** | Tìm SP theo tên | NSU211 | Ô chọn SP gõ 1 phần **tên** (VD `Chai PET`) | Ra kết quả theo tên (không chỉ theo mã) | ☐ | |
| **PO-04** | Tự điền khi chọn SP có HH | NSU211 | Chọn `THC0003` | Tự điền: Tên hàng, Tên HĐ, ĐVT, Phân loại, **Mã HH=HH0003**, **Tên HH** | ☐ | |
| **PO-05** | SP không HH → HH trống | NSU211 | Chọn 1 SP nhóm ICARE | Các trường điền, **Mã HH/Tên HH trống** (đúng); nhập tay được | ☐ | |
| **PO-06** | Đổi SP trong popup chi tiết | NSU211 | Mở popup **Chi tiết dòng** → ô **Mã hàng** đổi sang SP khác | Đổi được (không còn khóa cứng); HH tự cập nhật theo SP mới | ☐ | ⚠️ bug đã sửa |
| **PO-07** | Lưu & mở lại giữ HH | NSU211 | Điền dòng có HH → **Lưu đơn** → thoát → mở lại | Mã HH + Tên HH còn nguyên | ☐ | |
| **PO-08** | Nhân bản dòng | NSU211 | Bấm **Nhân bản** 1 dòng có HH | Dòng mới mang theo Mã HH + Tên HH | ☐ | |
| **PO-09** | Nhận hàng → tồn/công nợ | NSU211/admin | Duyệt PO → popup giao hàng, nhận 1 lần | Sinh tồn kho + công nợ như cũ (field HH mới không phá luồng nhận) | ☐ | ⚠️ regression |
| **PO-10** | In PO | NSU211 | **In** PO vừa tạo | Bản in ra đúng, không lỗi | ☐ | |
| **PO-11** | ĐVT trống phải chọn tay | NSU211 | Chọn SP mới (ĐVT master trống) → xem ô ĐVT | ĐVT trống, chọn/tìm ĐVT tay được (đúng thiết kế) | ☐ | |

---

## 4. Liên đới — Yêu cầu mua / Khảo sát (autocomplete SP có sẵn)

| Mã | Nội dung | TK | Bước | Kết quả mong đợi | KQ | Ghi chú |
|---|---|---|---|---|---|---|
| **LK-01** | PR chọn SP autocomplete | NSU211 | Tạo **Yêu cầu mua** → chọn SP bằng ô tìm | Chọn được trong ~6.760 SP (đã dùng picker sẵn) | ☐ | |
| **LK-02** | Khảo sát chọn SP | NSU211 | Tạo **Phiếu khảo sát SP** → chọn SP | Chọn được; lọc theo phân loại (nhóm đã chuẩn hóa) khớp | ☐ | |

---

## 5. Trạng thái tổng

- Môi trường đã deploy: **local** ✅ · **VPS** ✅ (2026-07-07, migration `f7c2b4a9e1d3` + `a1d4f8b2c6e7`, import 6.760 SP)
- Đã tự kiểm (backend): search trả kèm Mã HH/Tên HH ✅ · import idempotent (local, cập nhật 6.759 không tạo trùng) ✅
- **Ưu tiên test tay:** PO-01, PO-06, PO-09, SP-09 (4 chỗ dễ vỡ nhất) trước khi coi là xong.

> Tick cột **KQ** khi test xong. Chỗ nào ❌ ghi chú lại để mình sửa.
