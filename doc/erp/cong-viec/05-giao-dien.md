# PHÂN HỆ CÔNG VIỆC — ĐẶC TẢ GIAO DIỆN (CLONE LARK TASKS)

**Bản:** 1.0 — 28/08/2026 · **CR:** CR-216 · Nguồn: ba ảnh Lark của người dùng (kanban,
panel chi tiết task, thanh công cụ khung nhìn). Nguyên tắc: **bố cục và thao tác bám
Lark**, còn chất liệu là bộ sẵn có của `frontend-v2` (shadcn/Radix, lucide, DataTable,
conditional-filter, token màu Tailwind) — không chế khung mới khi đã có khuôn.

---

## 1. Bố cục tổng thể

```
┌─────────────┬──────────────────────────────────────────────────────┐
│ SIDEBAR     │ Tên list + mô tả + avatar thành viên + nút Mời       │
│ - Việc của  ├──────────────────────────────────────────────────────┤
│   tôi       │ [List] [Kanban] [Gantt] [Dashboard] [Activities]     │  <- hàng tab khung nhìn
│ - Ghim      ├──────────────────────────────────────────────────────┤
│ - Nhóm A    │ [+ Việc mới v] [Tất cả v] [Lọc] [Sắp xếp] [Gom nhóm] │  <- thanh công cụ
│    - List 1 │                                     [Tùy chỉnh]      │
│    - List 2 │ ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│ - Nhóm B    │ │ Cột 1    2 │ │ Cột 2    0 │ │ Cột 3    2 │         │  <- nội dung khung nhìn
│    - Nhóm B1│ │ [thẻ]      │ │            │ │ [thẻ]      │         │
│ - List lẻ   │ │ [thẻ]  [+] │ │        [+] │ │ [thẻ]  [+] │         │
└─────────────┴──────────────────────────────────────────────────────┘
```

- **Sidebar trái:** mục cố định "Việc của tôi" (G-03) + list ghim + cây nhóm → nhóm con →
  list (tối đa 2 cấp nhóm, A-08). Mỗi list một chấm màu (`color`). Nút "+" tạo nhanh
  nhóm/list. Sidebar của PHÂN HỆ, nằm trong khung vỏ ERP chung.
- **Đầu trang list:** tên + mô tả, chồng avatar thành viên (bấm mở dialog thành viên
  A-02/A-03), nút "Mời".
- Trạng thái khung nhìn (tab đang chọn, bộ lọc, sắp xếp, tùy chỉnh thẻ) **lưu
  `localStorage` theo (người dùng × list × khung nhìn)** — đúng khuôn `LinesTable` đang
  nhớ cấu hình cột. Không lưu server ở bản đầu.

## 2. Hàng tab khung nhìn (clone đúng thứ tự Lark)

| Tab | Lark | Ta làm | Phase | Mã |
|---|---|---|---|---|
| List | Bảng phẳng | `DataTable` dùng chung, gom theo cột (section) thu/mở được | P0 | D-02 |
| Kanban | Bảng cột kéo thả | Khung nhìn chính | P0 | D-01 |
| Gantt | Thanh thời gian | ĐỂ SAU | P2 | D-05 |
| Dashboard | Thống kê list | 4 khối recharts (§7) | P1 | D-06 |
| Activities | Dòng hoạt động cấp list | Nhật ký audit của cả list (§8) | P1 | D-09 |

Tab chưa làm thì **KHÔNG render** — không để tab "Sắp có" chết trên thanh công cụ.

## 3. Thanh công cụ — từng nút là gì và ta clone thế nào

Đây là hàng nút trong ảnh: `+ New Task | All Tasks | Filter | Sort by | Group by | Customize`.

### 3.1 `+ Việc mới` (New Task) — P0

Nút chính tạo nhanh: mở ô nhập tiêu đề ngay đầu cột đầu tiên, Enter là có task (như Lark).
Mũi tên xuống bên cạnh: "Tạo với biểu mẫu đầy đủ" — mở panel chi tiết trống để điền hết
trường trước khi lưu. Cuối mỗi cột kanban cũng có nút `+` thêm thẳng vào cột đó.

### 3.2 `Tất cả` (All Tasks) — bộ lọc PHẠM VI nhanh — P0

Dropdown một-chọn, đổi nhanh lát cắt dữ liệu mà không đụng bộ lọc điều kiện:
**Tất cả việc** (mặc định, chưa xong) · **Việc của tôi** (mình là PIC) · **Tôi tạo** ·
**Đã hoàn thành** · **Đã hủy**. Đây là cái Lark để ngay cạnh nút tạo vì dùng nhiều nhất.

### 3.3 `Lọc` (Filter) — bộ lọc ĐIỀU KIỆN — P0

Là gì bên Lark: bấm ra popover thêm từng điều kiện dạng "trường — phép so — giá trị",
nhiều điều kiện AND với nhau; nút hiện số điều kiện đang áp (ví dụ "Lọc · 2").

Ta clone bằng khung **`@/shared/conditional-filter` sẵn có** (đang chạy ở các màn danh
sách lớn), bộ trường: PIC · người tạo · tag · độ ưu tiên · cột (section) · trạng thái ·
hạn chót (trước/sau/khoảng/quá hạn) · **từng nhãn tùy biến của list** (B-08 — trường
động nạp theo list). Bộ lọc áp cho MỌI khung nhìn (List/Kanban/Dashboard cùng lát cắt).
Lưu bộ lọc hay dùng = G-04 (P2).

### 3.4 `Sắp xếp` (Sort by) — P0

Dropdown: **Tay (Custom)** (mặc định — theo `sort_order` kéo thả) · Hạn chót · Độ ưu
tiên · Ngày tạo · Tiêu đề. Trong kanban, sắp xếp áp TRONG TỪNG CỘT. Quy tắc phải giữ:
đang sort khác "Tay" thì kéo thả ĐỔI VỊ TRÍ trong cột bị khóa (kéo sang cột khác vẫn
được) — không thì thả xong danh sách tự nhảy lại, người dùng tưởng lỗi.

### 3.5 `Gom nhóm` (Group by) — P0 một phần

Là gì bên Lark: đổi TIÊU CHÍ chia cột kanban mà không đổi dữ liệu. "Custom Group" =
chia theo cột tự đặt (section).

| Gom theo | Phase | Ghi chú |
|---|---|---|
| Cột tự đặt (Custom Group) | P0 | Mặc định — chính là section, kéo thả đổi cột như thường |
| PIC | P1 | Mỗi người một cột; kéo thẻ = đổi người phụ trách |
| Độ ưu tiên | P1 | Kéo thẻ = đổi ưu tiên |
| Hạn | P1 | Cột cứng: Quá hạn · Hôm nay · Tuần này · Sau này · Chưa đặt (kéo thả tắt) |
| Tag / nhãn tùy biến | P2 | |

Mã tính năng mới: **D-08** (gom theo trường khác ngoài section).

### 3.6 `Tùy chỉnh` (Customize) — P0 phần thẻ

Là gì bên Lark: chỉnh CÁCH HIỂN THỊ của khung nhìn hiện tại (không đụng dữ liệu).
Ta clone thành popover ba phần:

1. **Trường hiện trên thẻ kanban** — bật/tắt: PIC · hạn · tag · độ ưu tiên · từng nhãn
   tùy biến · tiến độ việc con · số bình luận. (Tiêu đề luôn hiện.)
2. **Hiện/ẩn việc đã hoàn thành** trong cột (mặc định ẩn, xem qua "Tất cả" §3.2 cũng được).
3. **Với List view:** chọn cột bảng + thứ tự — chính là năng lực có sẵn của `DataTable`.

Lưu theo (người dùng × list × khung nhìn) như §1. Mã tính năng mới: **D-07** (thanh công
cụ khung nhìn: All/Lọc/Sắp xếp/Gom nhóm/Tùy chỉnh).

## 4. Kanban — giải phẫu

- **Cột:** tiêu đề + chấm màu + SỐ ĐẾM task (như "Documentation 2") + menu cột (đổi tên,
  đổi màu, xóa — xóa bắt dồn task sang cột khác) + nút `+` cuối cột. Kéo ngang đổi thứ
  tự cột. Lark gắn emoji cho cột — ta **thay bằng chấm màu** (luật cấm emoji, `icons.md`).
- **Thẻ:** tiêu đề (tối đa 2 dòng, cắt `…`) · hàng chip: độ ưu tiên (P1 đỏ/P2 vàng… như
  Lark) + tag + giá trị nhãn tùy biến (mỗi chip mang màu của option) · hàng chân: avatar
  PIC (nhiều người chồng nhau, tối đa 3 + "+n") · hạn (chữ đỏ khi quá hạn, cam khi hôm
  nay) · `n/m` việc con kèm icon nhánh · icon bình luận + số. Trường nào tắt ở Tùy chỉnh
  thì không vẽ.
- **Kéo thả:** thẻ trong cột (đổi `sort_order`), thẻ sang cột khác (đổi `section_id`),
  luật khóa khi sort khác Tay (§3.4). Optimistic update — thả là nằm yên, gọi API sau,
  lỗi thì bật lại và toast.
- Bấm thẻ mở **panel chi tiết** trượt từ phải (Sheet), không rời bảng.

## 5. List view

`DataTable` dùng chung, mỗi section một nhóm dòng thu/mở được (header nhóm = tên cột +
đếm). Cột bảng: ô tick tròn hoàn thành (như Lark) · tiêu đề · PIC · hạn · độ ưu tiên ·
tag · nhãn tùy biến · cập nhật cuối. Tick tròn đổi `status` ngay tại chỗ. Việc con KHÔNG
hiện thành dòng riêng (C-05).

## 6. Panel chi tiết task (clone ảnh 2)

Thứ tự hàng đúng như Lark: tiêu đề (sửa tại chỗ) → PIC + nút thêm người / người theo
dõi → hạn: nút nhanh **Hôm nay / Ngày mai / Khác** (mở date-picker, kèm ngày bắt đầu)
→ dòng "thuộc: [list] · [cột v]" đổi được ngay tại đó (B-10 chuyển list là P1) → các
hàng nhãn: Tag · Độ ưu tiên · từng nhãn tùy biến (chip màu, bấm mở chọn) → mô tả →
khối việc con: thanh tiến độ `n/m` + danh sách tick + ô "Thêm việc con" → bình luận
(khuôn CR-033) → cuối panel: `AuditTimeline` (E-04). Góc panel: menu xóa (thùng rác),
sao chép link task.

## 7. Dashboard (D-06 — P1)

Bốn khối trên recharts (đã có sẵn wrapper chart trong `shared/ui/`):

1. **Thẻ số tổng quan:** đang mở · hoàn thành 7 ngày · quá hạn · đến hạn tuần này.
2. **Phân bố theo cột** — bar ngang (thấy nghẽn ở cột nào).
3. **Theo PIC** — bar: mỗi người đang ôm bao nhiêu việc mở, phần quá hạn tô đỏ.
4. **Theo độ ưu tiên** — donut P1–P4.

Tôn trọng bộ lọc đang áp (§3.3). Không làm burndown/tiến độ thời gian ở bản đầu.

## 8. Activities (D-09 — P1)

Dòng thời gian gộp audit của CẢ LIST (tạo/sửa/kéo cột/đổi PIC/bình luận/thành viên
vào-ra), mới nhất trên cùng, phân trang cuộn. Lọc nhanh theo loại sự kiện + theo người.
Khác E-04: E-04 là nhật ký TRONG panel một task, đây là cấp list.

## 9. Quy tắc chất liệu (nhắc lại, bắt buộc)

- shadcn/Radix + lucide, **không emoji** — cột/nhãn dùng chấm màu + chip màu token.
- Màu qua token Tailwind (`bg-…/text-…`), chip màu của tag/nhãn/cột lấy từ bảng màu
  định sẵn (10–12 màu đặt tên), KHÔNG cho nhập hex tự do — đỡ vỡ dark mode.
- Bảng = `DataTable`; lọc điều kiện = `@/shared/conditional-filter`; query key vào
  `shared/constants/query-keys.ts`; kéo thả dùng thư viện đã có trong repo nếu có,
  chưa có thì `@dnd-kit` (chuẩn hiện nay, hỗ trợ phím + cảm ứng) — chốt lúc làm W2.
- Ô chỉ xem theo luật `read-only-value`; mọi màn theo khuôn phân hệ `src/modules/work/`.

## 10. Tham khảo cho Gantt (D-05 — P2, ghi sẵn để khỏi tìm lại)

Người dùng chỉ định tham khảo **DHTMLX Gantt** (dhtmlx.com) về logic và giao diện:

- Bố cục chuẩn của nó: lưới cột bên trái (tên việc, người, ngày) + trục thời gian bên
  phải; kéo hai mép thanh đổi ngày bắt đầu/kết thúc, kéo cả thanh dời lịch, vẽ mũi tên
  nối phụ thuộc việc trước-sau, zoom ngày/tuần/tháng, đường "hôm nay". Dữ liệu ta đã đủ
  nuôi nó: `start_date`/`due_date` + cha-con 2 cấp; PHỤ THUỘC việc (link) thì CHƯA có
  bảng — làm Gantt thật mới thêm `tab_work_task_link`, đừng thêm trước.
- **Giấy phép phải soát lúc quyết:** bản Standard (npm `dhtmlx-gantt`) là **GPLv2**,
  bản Pro trả phí. Dùng nội bộ không phân phối thì GPL không kích hoạt nghĩa vụ mở mã,
  nhưng vẫn phải ghi nhận quyết định này một dòng CR khi làm.
- Ứng viên thay thế giấy phép dễ hơn (MIT): `frappe-gantt` (nhẹ, đủ kéo thả cơ bản),
  `gantt-task-react` (React thuần). Chốt thư viện ở W5, theo đúng nguyên tắc
  "P2 chỉ làm khi có người đòi" — tài liệu này chỉ giữ địa chỉ tham khảo.
