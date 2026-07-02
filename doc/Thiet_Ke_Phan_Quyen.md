# Thiết kế Phân quyền (RBAC + Phạm vi dữ liệu)

> Viết cho người không chuyên. Chốt cách phân quyền cho ~20 người dùng nội bộ DEGO.
> Ý tưởng gốc của anh: *khi cấp tài khoản, chọn phạm vi — admin = tất cả công ty; phòng thu mua =
> vài công ty; nhân sự = một phòng ban*. Tài liệu này biến ý đó thành thiết kế cụ thể.

---

## 1. Có 2 lớp quyền (tách riêng, đừng trộn)

**Lớp A — Quyền HÀNH ĐỘNG (theo VAI TRÒ):** vai trò được *làm gì* trên từng chức năng.
Ví dụ vai trò "Nhân viên thu mua": Xem + Tạo + Sửa trên Yêu cầu mua & Đơn mua hàng; KHÔNG được Duyệt.
→ Đây là **ma trận quyền** (giống ảnh Frappe anh gửi).

**Lớp B — PHẠM VI dữ liệu (theo NGƯỜI DÙNG):** người đó được *thấy dữ liệu của ai*.
Ví dụ: cùng vai trò "Nhân viên thu mua" nhưng anh A phụ trách **Công ty 1 & 2**, anh B chỉ **Phòng Sản xuất**.
→ Đây là cái anh mô tả: lúc cấp tài khoản thì tick công ty/phòng ban được phụ trách.

> Nguyên tắc: **Hành động gắn vào VAI TRÒ. Phạm vi gắn vào NGƯỜI DÙNG.**
> Vì 2 người cùng vai trò nhưng phạm vi khác nhau.

---

## 2. Bộ hành động (rút gọn — không bê 16 cột của Frappe)

Giữ gọn, đủ dùng cho nội bộ:

| Cờ | Nghĩa |
|---|---|
| Xem | đọc/danh sách |
| Tạo | thêm mới |
| Sửa | chỉnh sửa |
| Xóa | xóa |
| Duyệt | gửi duyệt / phê duyệt / từ chối |
| Hủy | hủy chứng từ (cancel) |
| In | in chứng từ |
| Xuất | xuất Excel/CSV |

→ Tổng **8 hành động**: Xem · Tạo · Sửa · Xóa · Duyệt · Hủy · In · Xuất.

Bỏ các cột thừa của Frappe: Select, Amend, Share, Email, và **Level (phân quyền theo từng ô/field)** — quá phức tạp, không cần.
Giữ khái niệm **"Chỉ của mình" (own)** như một lựa chọn phạm vi (xem mục 4).

---

## 3. Mô hình dữ liệu

### Đã có sẵn (Lớp A)
- `Role` (vai trò): mã, tên, mô tả — **tạo/sửa/xóa được**.
- `Permission`: theo (vai trò × chức năng) với các cờ `can_read/create/write/delete/approve/print/export`.
- `User` ↔ `UserRole` ↔ `Role`: 1 người có thể nhiều vai trò.

### Thêm mới (Lớp B) — PHẠM VI GẮN VÀO TỪNG "DÒNG PHÂN QUYỀN" (grant)

Thay vì 1 phạm vi chung cho cả người, **mỗi người có NHIỀU dòng phân quyền**, mỗi dòng =
**1 vai trò + phạm vi riêng của dòng đó**. (Mở rộng bảng `UserRole` hiện có thành "grant".)

| Cột (mỗi dòng grant) | Ý nghĩa |
|---|---|
| user_id | người dùng |
| role_id | vai trò của dòng này |
| company_ids | công ty áp cho dòng này (trống = tất cả) |
| department_codes | phòng ban áp cho dòng này (trống = tất cả) |
| own | chỉ bản ghi do chính mình tạo |

**Vì sao tách theo dòng:** để cấp *quyền khác nhau trên phạm vi khác nhau* cho cùng 1 người.
Đây chính là tình huống: "xử lý yêu cầu của phòng **Sản xuất**, nhưng còn được **duyệt** cho phòng **IT**".

Quy ước:
- Trống cả company & department ở 1 dòng = dòng đó không giới hạn phạm vi.
- Quyền hiệu lực = **HỢP (OR) của mọi dòng**: được làm hành động X trên bản ghi R nếu **tồn tại ≥1 dòng**
  mà (vai trò của dòng có quyền X trên chức năng đó) **và** (phạm vi dòng đó chứa R).
- Admin: 1 dòng vai trò Admin, để trống phạm vi ⇒ full.

---

## 4. Cách hệ thống thực thi (enforcement)

1. **Chặn hành động (Lớp A):** mọi API đã đi qua `require(entity, action)` — nếu vai trò không có cờ → chặn (đang chạy).
2. **Lọc phạm vi (Lớp B):** hàm `scope_query(query, entity, action, user)` áp vào **danh sách + chi tiết**:
   - Lấy các **dòng grant** của user mà vai trò có quyền `action` trên entity này.
   - Với mỗi grant, dựng điều kiện phạm vi (company_ids / department_codes / own) theo cột entity có.
   - Kết quả = **OR các điều kiện đó** (hợp các dòng). Không grant nào phù hợp → không thấy gì.
3. **Chặn ghi ngoài phạm vi:** khi tạo/sửa, không cho gán company/department ngoài phạm vi được cấp.

### Chức năng nào lọc theo chiều nào
| Chức năng | company_id | department | own |
|---|---|---|---|
| Đơn mua hàng (PO) | ✓ | ✓ | ✓ |
| Yêu cầu mua (PYC) | ✓ | ✓ | ✓ |
| Công nợ / Thanh toán | ✓ | – | – |
| Tồn kho | ✓ | – | – |
| Nhà cung cấp, Sản phẩm, Danh mục | (dùng chung, thường không giới hạn) | – | – |
| Báo cáo / Dashboard | ✓ (số liệu chỉ trong phạm vi) | ✓ | – |

> Ghi chú: Danh mục dùng chung (NCC, sản phẩm, kho…) **không lọc theo phạm vi**; nhưng vẫn theo quyền Xem (mục dưới).

### Ẩn/hiện menu theo quyền (theo ý anh: "được xem ở đâu thì hiện ra đó")
- **Mục menu sidebar chỉ hiện nếu user có quyền Xem** entity đó. Không có quyền Xem → ẩn khỏi menu.
- Cụm menu (Mua hàng / Kho & Công nợ / Danh mục…) tự ẩn nếu không còn mục con nào.
- Ngoài ẩn menu, backend vẫn chặn truy cập trực tiếp bằng `require()` (an toàn 2 lớp).

---

## 5. Giao diện — một màn "Phân quyền" riêng (3 tab)

### Tab 1 — Vai trò
- Danh sách vai trò + nút **Thêm vai trò**. Mỗi dòng: tên, mô tả, số người dùng, nút sửa/xóa.

### Tab 2 — Ma trận quyền (chọn 1 vai trò)
- Bảng: **hàng = chức năng** (gom cụm: Mua hàng / Kho & Công nợ / Danh mục / Hệ thống), **cột = hành động** (Xem/Tạo/Sửa/Xóa/Duyệt/Hủy/In/Xuất) — ô tick.
- Tiện ích: tick cả dòng ("cấp mọi quyền chức năng này"), tick cả cột, nút Lưu.
- (Giống ảnh Frappe nhưng ít cột, gom nhóm cho dễ nhìn.)

### Tab 3 — Người dùng & phạm vi (Ma trận + chỉnh phạm vi từng dòng)
Chọn 1 người → màn gồm:
1. **Phạm vi tổng (mặc định):** Công ty [chip] + Phòng ban [chip]. Trống = tất cả. Áp cho **mọi chức năng** trừ dòng nào chỉnh riêng.
2. **Ma trận quyền theo chức năng:** hàng = chức năng, cột = 8 hành động (tick). Cuối mỗi dòng có cột **Phạm vi**:
   - Nhãn **Mặc định** (kế thừa phạm vi tổng) hoặc **Tùy chỉnh**, kèm nút **✏️**.
   - Bấm ✏️ → **popup có tiêu đề = tên quyền** (vd "Quyền: Yêu cầu mua hàng"):
     - Chọn **Dùng phạm vi tổng** *hoặc* **Tùy chỉnh riêng**.
     - Nếu tùy chỉnh, chọn **nhiều** ở từng cấp: **Công ty** → **Phòng ban** → **Nhân sự**, và **Loại trừ** (công ty / phòng ban / nhân sự).
     - Phạm vi này áp **CHUNG cho mọi hành động** của chức năng đó (bản này).
     - Lưu.
- Đa số dòng để **Mặc định**; chỉ dòng ngoại lệ mới ✏️.
- *Phiên bản sau:* tách phạm vi **theo từng hành động** (xem ở đâu · tạo ở đâu · duyệt ở đâu khác nhau).

> Đúng ý anh: cài phạm vi tổng 1 lần; chức năng nào cần khác thì ✏️ chỉnh riêng (bao gồm + loại trừ),
> không đụng thì tự lấy theo phạm vi tổng.

---

## 5b. Luồng thao tác (mô phỏng) — làm sao cho GỌN

Bí quyết để dễ: **cài quyền hành động 1 lần theo vai trò**, sau đó **cấp người dùng chỉ còn 3 cú chọn**.

### (A) Cài 1 lần cho mỗi vai trò — người quản trị làm lúc đầu
1. Menu **Phân quyền → tab Vai trò → "Thêm vai trò"** → gõ tên (vd "Nhân viên thu mua") → Lưu.
2. Sang **tab Ma trận quyền → chọn vai trò đó** → tick quyền. Có nút **tick cả dòng** nên rất nhanh:
   - Yêu cầu mua: Xem, Tạo, Sửa
   - Đơn mua hàng: Xem, Tạo, Sửa
   (không tick Duyệt vì nhân viên không được duyệt) → **Lưu**.
   → Mỗi vai trò làm ~30 giây, chỉ 1 lần.

> Hệ thống seed sẵn vài vai trò mẫu (Admin, Trưởng phòng thu mua, Nhân viên thu mua, Thủ kho,
> Kế toán công nợ) để dùng ngay, đỡ phải tạo từ đầu.

### (B) Cấp tài khoản hằng ngày — 1 dòng, 3 bước
Vào **tab Người dùng & phạm vi → chọn người** (hoặc Thêm) → ở **dòng phân quyền**:
1. **Chọn vai trò** (vd "Nhân viên thu mua") — quyền hành động tự áp theo vai trò.
2. **Chọn phạm vi** bằng chip: Công ty = [Cty 1, Cty 2] *hoặc* Phòng ban = [Sản xuất]. (Trống = tất cả.)
3. **Lưu**. Xong.

### (C) Cấp thêm quyền ngoại lệ — thêm 1 dòng
VD: bạn trên **còn được duyệt** phiếu yêu cầu của **phòng IT**:
- Bấm **＋ Thêm dòng phân quyền** → chọn vai trò có quyền **Duyệt** (vd "Người duyệt PYC")
  + Phòng ban = **IT** → Lưu.
- Kết quả: dòng 1 cho làm việc ở Sản xuất, dòng 2 cho duyệt ở IT. Hệ thống lấy **hợp** cả hai.

### Hình dung nhanh (tab Người dùng & phạm vi — dạng dòng)
```
Nguyễn Văn A                                              [ Lưu ]
──────────────────────────────────────────────────────────────
Dòng 1  Vai trò [ Nhân viên thu mua ▾ ]  Phòng ban [ Sản xuất ✕ ]  ☐ Của mình   🗑
Dòng 2  Vai trò [ Người duyệt PYC   ▾ ]  Phòng ban [ IT ✕ ]        ☐ Của mình   🗑
                                                          ＋ Thêm dòng phân quyền
(Công ty để trống = tất cả công ty)
```

---

## 6. Ví dụ tình huống (kiểm chứng thiết kế)

| Người | Vai trò (Lớp A) | Phạm vi (Lớp B) | Kết quả |
|---|---|---|---|
| Giám đốc / Admin | Admin (mọi quyền) | (trống) | Thấy & làm mọi thứ, mọi công ty |
| Trưởng phòng thu mua | Thu mua + Duyệt | Công ty 1, 2 | Duyệt PO/PYC nhưng chỉ của Cty 1 & 2 |
| Nhân viên thu mua | Thu mua (không Duyệt) | Phòng Sản xuất | Tạo/sửa PYC-PO của phòng Sản xuất, không duyệt |
| **NV thu mua (2 dòng)** | Dòng 1: Thu mua · Dòng 2: Người duyệt PYC | Dòng 1: Sản xuất · Dòng 2: IT | Làm việc ở Sản xuất **+ duyệt PYC của IT** (hợp 2 dòng) |
| Thủ kho | Kho (Xem/Sửa tồn) | Công ty 1 | Chỉ thao tác tồn kho Cty 1 |
| Kế toán công nợ | Công nợ + Thanh toán | (trống) | Xem công nợ mọi công ty |

---

## 7. Lộ trình triển khai

- **Bước 1:** Tab Vai trò + Tab Ma trận quyền (Lớp A). Backend đã sẵn — chủ yếu dựng giao diện. → phân quyền hành động dùng được ngay.
- **Bước 2:** Mở rộng `UserRole` thành **grant** (company_ids/department_codes/own) + Tab Người dùng & phạm vi (nhiều dòng) + hàm `scope_query`; áp cho PO, PYC, công nợ, tồn kho, báo cáo.
- **Bước 3:** Chặn ghi ngoài phạm vi + ẩn mục menu theo quyền + mở rộng chiều (kho, NCC) nếu cần.

---

## 8. Đã chốt
1. ✅ Phạm vi giai đoạn đầu: **Công ty + Phòng ban** (Kho/NCC mở rộng sau).
2. ✅ Hành động: **8 cờ** — Xem/Tạo/Sửa/Xóa/Duyệt/**Hủy**/In/Xuất.
3. ✅ **Menu/danh mục hiện theo quyền Xem** — có quyền xem cái nào thì hiện cái đó (mục 4).
4. ✅ Làm theo lộ trình 3 bước, **Bước 1 trước**; thao tác cấp quyền theo luồng mục 5b (gọn, 3 bước/người).

---

## 9. Kiến trúc kiểm quyền & hiệu năng

**Kiểm quyền = dependency trên route, không phải middleware toàn cục.** `require(entity, action)`
gắn vào từng API (đã có). Middleware chỉ giải mã token → gắn user.

**Token chỉ chứa `user_id` (+ hạn).** Không nhét quyền vào token (đổi quyền là token cũ sai; token phình).
Quyền tra ở server theo user_id.

**Luồng mỗi request:** token → user_id → lấy *hồ sơ quyền* `{actions_by_entity, scope}` →
`require()` cho/chặn → `scope_query()` lọc dữ liệu.

**Cache (~100 user):** cache **hồ sơ quyền đã gộp** của user để khỏi tính lại mỗi request.
- Kích thước bảng vài ngàn dòng là **nhỏ** với MySQL — query `WHERE user_id=?` (có index) ~1–3ms;
  không phải lý do cần Redis. Lý do cache là **tránh gộp roles→ma trận+scope lặp lại**.
- Hồ sơ quyền mỗi user ~vài KB → 100 user ~vài trăm KB → **cache in-process** (dict/LRU) thoải mái,
  có thể nạp sẵn lúc khởi động. In-process **nhanh hơn Redis** (không qua mạng) khi chỉ 1 tiến trình.
- **Bọc sau interface** `perm_cache.get/set/clear`: bản đầu in-process; đổi sang **Redis khi chạy
  nhiều worker/instance** (không sửa chỗ gọi). Redis cũng dùng cho worker Phase 3.
- Lưu ý multi-worker: mỗi worker cache riêng → đổi quyền lệch tối đa 1 TTL; TTL 30–60s + xóa khi lưu là đủ.

**Invalidation:** khi lưu Vai trò/Ma trận/Phạm vi → xóa cache user liên quan (hoặc bump `perm_version`);
hoặc để TTL tự hết sau ≤1 phút.

**FE:** `GET /api/auth/me` trả hồ sơ quyền rút gọn để **ẩn menu/nút**. Nhưng **chốt chặn thật ở backend** —
ẩn ở FE chỉ là UX, không phải bảo mật.

### Việc cần code (tóm tắt)
- `get_perm_profile(user_id)` + cache in-process + invalidate khi lưu quyền.
- `require()` / `scope_query()` đọc từ profile.
- `/api/auth/me` trả quyền cho FE; FE ẩn menu/nút theo `read`.
