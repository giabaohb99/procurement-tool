# QUY TRÌNH & LOGIC TÀI LIỆU DỰ ÁN
## Từ "khách nói muốn gì" → đến "bàn giao xong" (cho team nhỏ)

| | |
|---|---|
| **Phiên bản** | v1.0 |
| **Ngày** | 2026-07-08 |
| **Mục đích** | Giải thích có những loại tài liệu nào, ra đời theo thứ tự/vòng nào, ai làm–ai duyệt, và cách chốt để khách không đổi ý liên tục mà không có ràng buộc |

---

## 1. Bức tranh tổng thể — chuỗi tài liệu

Mỗi tài liệu trả lời **một câu hỏi khác nhau**. Đi từ *nghiệp vụ* → *sản phẩm* → *kỹ thuật* → *bàn giao*.

```
 Khách nói muốn gì
        │  (làm rõ qua vài vòng hỏi–đáp)
        ▼
①  BRD   — "Nghiệp vụ CẦN GÌ và TẠI SAO?"      (ngôn ngữ kinh doanh)
        │  chốt/ký
        ▼
②  PRD   — "SẢN PHẨM LÀM GÌ để đáp ứng?"        (tính năng, màn hình, luật)
        │  chốt/ký
        ▼
③  TDD   — "XÂY BẰNG CÁCH NÀO?"                 (kiến trúc, DB, API, phân quyền)
        │
        ▼
④  Test cases / QA — "LÀM SAO BIẾT ĐÚNG?"
        │
        ▼
⑤  Tài liệu bàn giao — "DÙNG & VẬN HÀNH RA SAO?"
        
   (xuyên suốt)  ⑥ Change Log / CR — "AI ĐỔI GÌ, KHI NÀO, ẢNH HƯỞNG?"
```

> **Nguyên tắc vàng:** càng về sau càng đắt khi sửa. Đổi ở BRD = sửa 1 câu; đổi ở TDD/khi đã code = sửa cả tuần. → Nên **chốt BRD/PRD trước khi code**.

---

## 2. Từng loại tài liệu — là gì, ai làm, gồm gì

| Tài liệu | Trả lời câu hỏi | Ai viết | Ai duyệt/ký | Ngôn ngữ | Khi nào "đóng băng" |
|---|---|---|---|---|---|
| **Yêu cầu thô** (Intake) | Khách muốn gì (chưa rõ) | Ai nhận việc | — | Tự do | Không (là nguyên liệu) |
| **BRD** (Business Requirements) | Nghiệp vụ cần gì & tại sao | BA / Product | **Khách (phòng TM)** | Kinh doanh | Sau khi khách ký |
| **PRD** (Product Requirements) | Sản phẩm làm gì | Product | Khách + Tech lead | Bán kỹ thuật | Trước khi code |
| **TDD** (Technical Design) | Xây bằng cách nào | Tech lead / Dev | Nội bộ kỹ thuật | Kỹ thuật | Trước khi code phần đó |
| **Test cases** | Kiểm thế nào là đúng | QA / Dev | Product | Kỹ thuật | Trước khi test |
| **Tài liệu bàn giao** | Dùng & vận hành ra sao | Dev | Khách nhận | Người dùng | Khi release |
| **Change Log / CR** | Ai đổi gì, ảnh hưởng gì | Product | Khách (nếu ảnh hưởng scope) | Hỗn hợp | Cập nhật liên tục |

### Chi tiết từng cái

**① BRD — Business Requirements Document** *(cái quan trọng nhất để "chốt bản vẽ")*
- Mục tiêu kinh doanh, bối cảnh, vấn đề đang giải quyết
- Các bên liên quan (stakeholders) & vai trò
- **Phạm vi:** làm gì / KHÔNG làm gì (out of scope — chỗ này chống "đẻ thêm việc")
- Quy trình nghiệp vụ mong muốn (sơ đồ luồng)
- Quy tắc nghiệp vụ (business rules)
- Tiêu chí thành công / nghiệm thu
- → **Khách ký vào đây = chốt bản vẽ.** Đổi sau đó = phụ lục (CR).

**② PRD — Product Requirements Document**
- Danh sách tính năng (feature list) + độ ưu tiên (Must/Should/Could)
- User story: *"Là [vai trò], tôi muốn [làm gì] để [mục đích]"*
- Luồng màn hình (wireframe/screen flow)
- Tiêu chí chấp nhận (acceptance criteria) cho từng tính năng
- → Là cầu nối giữa BRD (nghiệp vụ) và TDD (kỹ thuật)

**③ TDD — Technical Design Document**
- Kiến trúc, stack, mô hình dữ liệu, API, phân quyền, quyết định kỹ thuật
- → Đã có: [technical-design.md](technical-design.md)

**④ Test cases / QA plan**
- Bảng: mã · nội dung · bước · kết quả mong đợi · trạng thái
- → Đã có: `doc/testcase/testcase-001…003.md`

**⑤ Tài liệu bàn giao (Handover / Release)**
- Hướng dẫn sử dụng (User manual) theo vai trò
- Hướng dẫn quản trị (tạo user, phân quyền, cấu hình)
- Hướng dẫn triển khai/vận hành (deploy, backup, khôi phục)
- Danh sách chức năng đã bàn giao + phiên bản
- Vấn đề đã biết (known issues) + việc còn lại

**⑥ Change Log / Change Request (CR)** *(cái "phụ lục hợp đồng")*
- Mỗi thay đổi so với bản đã chốt = 1 dòng CR
- Cột: Mã CR · Ngày · Mô tả · Lý do · **Ảnh hưởng (công/thời gian)** · Người duyệt · Version
- → CR chính là thứ bảo vệ team: "cái này ngoài bản đã chốt, cần phụ lục"

---

## 3. "Các vòng" để ra được một tài liệu

Mỗi tài liệu (BRD, PRD…) không ra ngay — đi qua **3 vòng** giống nhau:

```
  DRAFT  ──►  REVIEW  ──►  APPROVE (baseline)
 (viết nháp)  (khách/team    (khách ký → đóng băng
              góp ý, sửa)     thành v1.0)
      ▲___________│
       lặp tới khi đồng thuận
```

- **Vòng làm rõ (trước BRD):** 2–3 buổi hỏi–đáp với phòng TM để hiểu đúng nhu cầu → mới viết BRD được. *(Đừng viết BRD khi còn mơ hồ.)*
- **Vòng review:** gửi bản nháp, họp 30–60 phút, ghi phản hồi, sửa.
- **Vòng duyệt:** khách xác nhận "OK bản này" → **ký/đóng băng** → thành baseline.

> Sau khi baseline: muốn đổi → **không sửa thẳng vào baseline**. Mở **CR mới**, ước lượng ảnh hưởng, khách duyệt CR → cập nhật tài liệu và **tăng version** (v1.0 → v1.1).

---

## 4. Quản lý phiên bản & kiểm soát thay đổi (Change Control)

Đây là câu trả lời trực tiếp cho vấn đề "khách đổi ý liên tục":

1. **Baseline:** chốt bản v1.0, khách ký (Sign-off) — 1 trang xác nhận là đủ.
2. **Khách đòi đổi →** ghi 1 dòng CR: đổi gì, tại sao, **ảnh hưởng bao nhiêu công/ngày**.
3. **Khách duyệt CR** (đồng ý trả thêm thời gian/chi phí) → mới làm.
4. **Tăng version** tài liệu + ghi vào Change Log.

Kết quả: mọi thay đổi đều **có dấu vết + có người chịu trách nhiệm**. Bạn không còn ở thế bị động "làm free vì khách đổi ý".

---

## 5. Bản RÚT GỌN cho team nhỏ ✂️

Team nhỏ không cần đủ 6 loại nặng nề. Gộp lại còn **3 tài liệu sống + 1 sổ thay đổi**:

| Bắt buộc | Gộp từ | Ghi chú |
|---|---|---|
| **1. Spec** (1 file) | BRD + PRD gộp | Mục tiêu + phạm vi + luồng + danh sách tính năng + luật nghiệp vụ + tiêu chí nghiệm thu. **Khách ký cái này.** |
| **2. TDD** | TDD | Kỹ thuật — nội bộ dùng. *(đã có)* |
| **3. Test cases** | QA | Bảng test tay + tự động. *(đã có)* |
| **+ Change Log** | CR | 1 file, mỗi đổi 1 dòng. **Sống mãi.** |
| Bàn giao | Handover | Làm khi release; có thể chỉ là 1 file hướng dẫn sử dụng + deploy. |

> Với dự án này, nếu ngại tách BRD/PRD riêng: dùng **1 file "Spec"** (bản vẽ nghiệp vụ để khách ký) + **TDD** (kỹ thuật) + **testcase** + **change-log**. Bốn thứ là đủ chặt.

---

## 6. Áp vào dự án hiện tại — đang ở đâu, thiếu gì

| Tài liệu | Hiện trạng | Việc cần làm |
|---|---|---|
| BRD/PRD (Spec nghiệp vụ) | ❌ **Chưa có** | ⭐ Cần dựng — để phòng TM ký chốt bản vẽ |
| TDD | ✅ Vừa tạo `technical-design.md` | Rà + chốt v1.0 |
| Test cases | ✅ testcase-001/002/003 | Bổ sung testcase-004 (Yêu cầu khảo sát) |
| Tài liệu bàn giao | ❌ Chưa có | Làm khi release chính thức |
| Change Log | ❌ Chưa có | ⭐ Cần dựng ngay — ghi CR-001 (PYC→YCKS) |

**Đề xuất thứ tự làm tiếp:**
1. Dựng **change-log.md** (ghi ngay CR-001) — rẻ, chặn ngay việc đổi ý không kiểm soát.
2. Dựng **Spec nghiệp vụ** (BRD+PRD gộp) từ hệ thống thực tế → đưa phòng TM **ký chốt v1.0**.
3. Từ đó, mọi yêu cầu mới đi qua CR.

---

## 7. Mẫu nhanh (copy dùng ngay)

**Mẫu 1 dòng Change Log:**
```
| CR-00X | 2026-07-xx | <đổi gì> | <lý do> | <+X ngày, thêm Y màn> | <người duyệt> | v1.x→v1.y |
```

**Khung Spec nghiệp vụ (BRD+PRD gộp) — các mục tối thiểu:**
1. Mục tiêu & bối cảnh
2. Các bên liên quan + vai trò
3. Phạm vi: trong / **ngoài** phạm vi
4. Luồng nghiệp vụ (sơ đồ)
5. Danh sách tính năng + ưu tiên (Must/Should/Could)
6. Quy tắc nghiệp vụ
7. Tiêu chí nghiệm thu
8. Ô ký chốt (khách + team) + version

**Biên bản Sign-off (1 trang):**
> *"Phòng Thu mua xác nhận đồng ý bản Spec/TDD phiên bản v1.0 ngày ___. Mọi thay đổi sau ngày này được xử lý qua Change Request."* — Ký: ___ (khách) / ___ (team).

---

*Hết. Tài liệu kỹ thuật hệ thống xem [technical-design.md](technical-design.md).*
