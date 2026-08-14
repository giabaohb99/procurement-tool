# VĂN THƯ — PHASE 0→3 · KẾ HOẠCH TRIỂN KHAI

> Full-stack (backend `backend/app` + frontend `frontend-v2`) · nguồn: `van-thu/00`–`05`
> Phạm vi: **P0 vá nền · P1 danh mục+số hiệu · P2 yêu cầu+soạn thảo+phiên bản · P3 bộ máy phê duyệt**
> Ngoài phạm vi: P4 ban hành/clone, P5 quyền+tra cứu (chờ câu B3/B5/B6) — sẽ lên plan riêng.

## Tiến độ

| Phase | Tệp | Task | Trạng thái |
|---|---|---|---|
| 0 · Vá nền | [phase-00-va-nen.md](./phase-00-va-nen.md) | 13 | ☐ Chưa bắt đầu |
| 1 · Danh mục và số hiệu | [phase-01-danh-muc-va-so-hieu.md](./phase-01-danh-muc-va-so-hieu.md) | 14 | ☐ Chưa bắt đầu |
| 2 · Yêu cầu, soạn thảo, phiên bản | [phase-02-yeu-cau-soan-thao-phien-ban.md](./phase-02-yeu-cau-soan-thao-phien-ban.md) | 21 | ☐ Chưa bắt đầu |
| 3 · Bộ máy phê duyệt dùng chung | [phase-03-bo-may-phe-duyet.md](./phase-03-bo-may-phe-duyet.md) | 18 | ☐ Chưa bắt đầu |

**66 task.** Mã task: `P{phase}-T{nn}`. Cột **L** trong từng phase: `BE` backend · `FE` frontend-v2 · `DB` migration · `∞` cả hai.

## Phụ thuộc

```
P0 ──▶ P1 ──▶ P2 ──▶ P3 ──▶ (P4)
                └────────────▶ (P5, song song được với P3)
```

- **P0 không làm song song với phase nào khác** — đụng vào nền của hệ đang chạy thật (`02` mục 15).
- P0-T01 (kiểm thử 5 luồng duyệt Thu mua) **làm đầu tiên**, không chờ trả lời câu hỏi nào.
- P2 dùng **luồng duyệt một bước viết tay tạm thời**; P3-T17 mới chuyển sang bộ máy chung.
- P1–P3 **không bị chặn** bởi 17 câu hỏi ở `00` mục 8 (chỉ chặn P4 trở đi).

## Điều kiện chuyển phase

| Từ | Sang | Điều kiện |
|---|---|---|
| P0 | P1 | 5 kiểm thử luồng duyệt xanh · link tệp cũ dán vào tab ẩn danh **không mở được** · đổi tên phòng ban không mất quyền · loại trừ phòng ban có tác dụng thật · gọi API nhật ký không quyền bị từ chối · thu hồi vai trò mất quyền trong vài giây · bản vá đã chạy prod ổn định |
| P1 | P2 | **Bài kiểm 100 kết nối cấp số** ra đúng 100 số liên tiếp · hủy văn bản không trả số về · sang năm mới sổ theo năm reset, sổ mã bất biến không reset |
| P2 | P3 | Một người đi hết đường xin phép → soạn → phiên bản 2 trên dev · 5 phép thử ở `02` mục 6 đạt · ≥3 người ngoài đội phần mềm bấm thử |
| P3 | P4 | 6 bài kiểm ở `02` mục 7 đạt · **chạy lại 5 kiểm thử Thu mua vẫn xanh** |

## Quyết định đã chốt trong plan này

| # | Quyết định | Vì sao |
|---|---|---|
| 1 | `tab_file_access_log` tạo **sớm ở M1 (phase 0)** thay vì M10 | H03 "ghi nhật ký mọi lượt xem/tải" thuộc phase 0; không có bảng thì không ghi được |
| 2 | Backend đặt ở **3 module mới**: `doc_catalog`, `document`, `approval` | Theo `module pattern` của `CLAUDE.md`; không nhét vào module có sẵn |
| 3 | FE dựng trong `frontend-v2/src/modules/document` (đã có) + module mới `approval` | Tái dùng 4 danh mục + data-table + conditional-filter đã có |
| 4 | `store/local-collection.ts` **gỡ dần theo từng task**, không gỡ một lần | Mỗi màn nối API xong thì bỏ collection tương ứng; tránh một PR khổng lồ |
| 5 | Bộ máy duyệt **đứng cạnh** 5 luồng viết tay của Thu mua, bật bằng cờ `I26` | `00` mục 4.7 — đường lui trong một lần bấm |

## Rủi ro chặn cả plan

| Rủi ro | Giảm bằng |
|---|---|
| P0 làm gián đoạn Thu mua (~300 tài khoản) | P0-T01 trước tiên · mỗi task một lần deploy · dev trước prod ít nhất 1 tuần · cờ bật tắt |
| Cấp số trùng | 3 lớp: khóa dòng · UNIQUE tầng DB · cùng transaction. Bài kiểm 100 kết nối là điều kiện chuyển phase |
| Quên lọc `origin = 1` | Bộ lọc nằm ở hàm dựng truy vấn dùng chung + bài kiểm tự động (P2-T04) |
| Quên khai `SCOPE_FIELDS` cho bảng mới | Guard lúc khởi động (P0-T13): bảng có `company_id` mà chưa khai → chết ngay lúc chạy |
| Mô hình luồng duyệt không đủ mềm | **Khai thử 8 luồng ra giấy trước khi viết mã** (P3-T01) |

## Câu hỏi chưa trả lời (không chặn P0–P3)

1. **B1** — form chuẩn là mẫu Word (C02) hay form web (C09)? Plan này đi theo mẫu Word; form web để P9.
2. **B3** — 4 mức mật chốt tên gì? Plan dùng `1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật` theo `04` mục 5.2. FE hiện đang là Thường/Mật/Tối mật/Tuyệt mật → P1-T13 nắn lại.
3. **B12** — có làm loại thứ 33 *Trích lục* (C20) không? Plan chỉ làm bản trích nội bộ C19.
4. **B6** — 32 mã loại + 13 mã pháp nhân đã ai duyệt chưa? Cấp số rồi thì **không đổi mã được** (P1-T05 khóa cột).
5. `frontend-v2` đã chốt thay `frontend/` chưa? Cả bộ van-thu không nhắc tới nó — plan này giả định **có**.
