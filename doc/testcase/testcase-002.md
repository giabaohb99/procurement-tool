# TESTCASE-002 — Khảo sát NCC & Sản phẩm (luồng + phân quyền)

> Bộ test cho **Khảo sát Nhà cung cấp** và **Khảo sát Sản phẩm**: tạo → gửi duyệt → quản lý duyệt từng dòng → trả lại → duyệt phiếu.
> URL Web: http://localhost:8080

---

## 1. Tài khoản test

| Vai trò | Username | Mật khẩu | Họ tên | Quyền `survey` |
|---|---|---|---|---|
| **Người khảo sát** | `NSU211` | `NSU211` | Võ Trọng Tín | read, create, write (KHÔNG duyệt) |
| **Quản lý duyệt** | `NSU215` | `NSU215` | Phạm Khánh Ngân | read, create, write, **approve** |
| Admin | `degoadmin` | (theo `.env`) | Quản trị viên | full |

---

## 2. Test cases (áp cho CẢ 2 loại: NCC & Sản phẩm)

| Mã | Nội dung | Tài khoản | Bước | Kết quả mong đợi |
|---|---|---|---|---|
| **TC-01** | Tạo phiếu khảo sát | NSU211 | Vào **Khảo sát NCC / SP → Tạo mới**, điền header (Phân loại, NSPT tự điền, Yêu cầu KT), thêm ≥1 dòng đủ trường → **Lưu** | Tạo thành công, sinh mã `KS…`, trạng thái **Nháp** |
| **TC-02** | Gửi duyệt (đủ trường) | NSU211 | Điền đủ mọi trường bắt buộc → **Gửi duyệt** | Trạng thái → **Chờ duyệt** |
| **TC-03** | Người khảo sát không duyệt dòng | NSU211 | Ở phiếu Chờ duyệt, thử sửa trường **Duyệt** của dòng | Không có quyền (nút/endpoint bị chặn — 403) |
| **TC-04** | Quản lý duyệt từng dòng | NSU215 | Mở popup từng dòng → chọn **Duyệt** (Đã duyệt / Không duyệt) + Ý kiến → **Lưu duyệt dòng** | Lưu đúng theo từng dòng; các trường khác **khóa** |
| **TC-05** | Trả lại để khảo sát lại | NSU215 → NSU211 | NSU215 bấm **Trả lại** (nhập lý do); NSU211 mở lại | Phiếu → **Từ chối**; NSU211 **sửa lại được** |
| **TC-06** | Gửi duyệt lại | NSU211 | Sửa xong → **Gửi duyệt** | Trạng thái → **Chờ duyệt** |
| **TC-07** | Duyệt cả phiếu | NSU215 | Bấm **Duyệt phiếu** | Trạng thái → **Đã duyệt** |
| **TC-08** *(thủ công/FE)* | Gửi duyệt khi thiếu trường | NSU211 | Bỏ trống 1 ô (VD Xuất xứ) → **Gửi duyệt** | Bị chặn, báo *"Dòng X: thiếu …"* (không gửi) |

> Ghi chú: các **trường file** và **trường của quản lý** (Duyệt/Ý kiến) KHÔNG bị bắt buộc khi gửi duyệt. Mã PYC là tùy chọn. Trường lấy mẫu chỉ bắt buộc khi tick "Mẫu sẵn".

---

## 3. Kết quả chạy tự động (API) — 2026-07-03

Chạy end-to-end qua API cho cả 2 loại (TC-01 → TC-07). TC-08 kiểm thủ công trên FE.

| Mã | Khảo sát NCC | Khảo sát Sản phẩm |
|---|:--:|:--:|
| TC-01 Tạo phiếu (draft) | ✅ 201 | ✅ 201 |
| TC-02 Gửi duyệt → Chờ duyệt | ✅ | ✅ |
| TC-03 Người khảo sát KHÔNG duyệt dòng (403) | ✅ | ✅ |
| TC-04 Quản lý duyệt từng dòng | ✅ (Đã duyệt / Không duyệt) | ✅ (Đã duyệt / Không duyệt) |
| TC-05 Trả lại → Từ chối + sửa lại được | ✅ | ✅ |
| TC-06 Gửi duyệt lại → Chờ duyệt | ✅ | ✅ |
| TC-07 Quản lý Duyệt phiếu → Đã duyệt | ✅ | ✅ |

**Tổng: 14/14 PASS.** TC-08 (validation FE khi thiếu trường): ☐ kiểm thủ công.
