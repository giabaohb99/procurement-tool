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
| Gantt | Thanh thời gian | **XONG** — bản đầu 28/08/2026 (CR-219), dựng lại theo Lark 31/08/2026 (**CR-226** rồi **CR-230**): lưới trái CHÍNH LÀ khung nhìn Danh sách (ba cột cố định, ô sửa tại chỗ, kéo thả việc/việc con/cột, dòng «Việc mới») · thang Ngày/Tuần/Tháng + cụm _Hôm nay_ ‹ › · hàng NHÓM có thanh tổng · cột mốc hình thoi · **mũi tên phụ thuộc** (vẽ + kéo tạo + đổi kiểu + xóa). Tự dựng, không cài thư viện (GPLv2) | P2 → làm sớm theo yêu cầu | D-05 · B-14 · B-15 |
| Dashboard | Thống kê list | 4 khối recharts (§7) | P1 | D-06 |
| Activities | Dòng hoạt động cấp list | **XONG** 31/08/2026 (**CR-249**) — nhật ký gộp của cả list, cột ngày dính bên trái, lọc theo loại sự kiện + theo người, cuộn lấy thêm (§8) | P1 | D-09 |

Tab chưa làm thì **KHÔNG render** — không để tab "Sắp có" chết trên thanh công cụ.

Hiện có **bốn** tab: **Bảng (Kanban) · Danh sách · Gantt · Hoạt động**. Chỉ còn
**Dashboard** chưa render vì chưa làm (D-06 — P1).

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
  Cách dựng (chốt ở **CR-220**): **dnd-kit** + **`DragOverlay`** — thẻ đang kéo vẽ ở lớp
  nổi bám con trỏ, **không nghiêng**, thẻ gốc mờ tại chỗ. Kéo sang cột khác thì cột đích
  sáng lên và mở **khe chờ** nét đứt đúng chỗ thẻ sẽ rơi vào; trong cùng một cột thì để
  dnd-kit tự dãn khe. Hai cái bẫy đã vấp, đừng lặp lại: **cấm gắn lớp `transition` của
  Tailwind lên nút kéo được** (nó phủ cả `transform` nên thẻ lết theo sau con trỏ), và
  đừng suy cột đích từ `over` một cách ngây thơ — trỏ vào một THẺ thì `over` là thẻ đó
  chứ không phải cột, phải quy về cột của nó.
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

## 8. Activities (D-09) — ĐÃ LÀM (CR-249, 31/08/2026)

Dòng thời gian gộp audit của CẢ LIST, mới nhất trên cùng, cuộn lấy thêm. Lọc nhanh theo
loại sự kiện + theo người. Khác E-04: E-04 là nhật ký TRONG panel một task, đây là cấp list.

⚠️ **Phải dọn nền dữ liệu trước mới lọc được — đọc `backend/app/modules/work/audit_entity.py`.**
Cả phân hệ từng ghi chung `entity = "work_task"` cho ba loại đối tượng đánh số ĐỘC LẬP
(việc · list · nhóm), nên `(work_task, 5)` vừa có thể là việc #5 vừa có thể là list #5.
Nay tách năm tên (`work_task` · `work_list` · `work_list_member` · `work_group` ·
`work_group_member`), `entity_id` luôn là id của đúng đối tượng nêu trong tên; migration
`c3a91d47f2b8` đổi lại các dòng cũ theo mẫu câu. **`work_task` giữ nguyên tên** vì khối
E-04 đang gọi `/api/audit-logs?entity=work_task`.

⚠️ **Không gọi `/api/audit-logs` cho màn này.** Đường đó dùng chung cả hệ, chỉ đòi đăng
nhập và KHÔNG kiểm quyền theo entity, lại chỉ lọc được đúng một `entity_id`. Đường riêng
là `GET /api/work/lists/{id}/activities` (+ `/activity-actors`), đi qua `get_list_or_403`.

**Ba nguồn gộp lại:** việc trong list (kể cả việc đã xóa mềm — dòng "Xóa công việc" là
dòng người ta cần nhất) ∪ thành viên vào ra ∪ sửa chính list và cột. **Bình luận chưa có
mặt** vì E-01 chưa làm (`work_task` chưa nằm trong `COMMENT_POLICY`); thêm vào đây khi E-01 xong.

Sắp theo `id` giảm dần chứ không `created_at`: hai thao tác trong cùng một giây là chuyện
thường, sắp theo giờ thì cuộn xuống thấy dòng lặp hoặc dòng mất.

**Hình dáng một dòng** (khuôn Lark, TRẢI HẾT bề ngang — không bó cột hẹp):

```
Hôm nay   ──────────────────────────────────────────────────────
  31      14:05  (av)  ✔ Tên việc                ← chữ nhỏ, xám
                       Dego Admin đã sửa công việc ← câu kể, chữ đậm
```

Câu kể bỏ cái đuôi `: {tên việc}` vì tên việc đã đứng riêng dòng trên — so ĐÚNG cả đuôi
chứ không cắt ở dấu hai chấm cuối, vì `Thêm phụ thuộc: A → B` cắt là mất sạch nội dung.
Hàng lọc nằm NGOÀI khung cuộn; thanh công cụ của ba khung nhìn kia ẩn hẳn ở tab này.

## 9. Quy tắc chất liệu (nhắc lại, bắt buộc)

- shadcn/Radix + lucide, **không emoji** — cột/nhãn dùng chấm màu + chip màu token.
- Màu qua token Tailwind (`bg-…/text-…`), chip màu của tag/nhãn/cột lấy từ bảng màu
  định sẵn (10–12 màu đặt tên), KHÔNG cho nhập hex tự do — đỡ vỡ dark mode.
- Bảng = `DataTable`; lọc điều kiện = `@/shared/conditional-filter`; query key vào
  `shared/constants/query-keys.ts`; kéo thả dùng thư viện đã có trong repo nếu có,
  chưa có thì `@dnd-kit` (chuẩn hiện nay, hỗ trợ phím + cảm ứng) — chốt lúc làm W2.
- Ô chỉ xem theo luật `read-only-value`; mọi màn theo khuôn phân hệ `src/modules/work/`.

## 10. Khung nhìn Gantt (D-05 + B-14 + B-15) — ĐÃ LÀM

**Giấy phép — chốt một lần cho xong:** bản Standard (npm `dhtmlx-gantt`) là **GPLv2**, bản
Pro trả phí; ứng viên MIT là `frappe-gantt` / `gantt-task-react`. **Ta không cài cái nào**
(CR-219, giữ nguyên ở CR-226). Ba lý do theo thứ tự cân nhắc: ① rước một giấy phép lây lan
vào repo để đổi lấy một biểu đồ thanh ngang là không đáng; ② thư viện nào cũng mang CSS
riêng, không biết gì về token màu và chế độ nền của hệ — chỉnh cho khớp còn tốn hơn tự vẽ;
③ **lưới trái phải là CHÍNH các ô sửa được của khung nhìn Danh sách**, không thư viện nào
nhận vào chỗ đó một cây React của mình mà không phải vá. Bố cục và thao tác vẫn bám DHTMLX
+ Lark.

### 10.1 Bố cục — lưới trái CHÍNH LÀ khung nhìn Danh sách

Lưới trái (dính khi cuộn ngang) · **thanh chia kéo được** · trục thời gian. Cả hai bên nằm
CHUNG một khung cuộn nên không bao giờ lệch hàng — khỏi đồng bộ hai thanh cuộn dọc bằng tay.

**KHÔNG viền, không bo góc, không vạch trên, và nền TRÙNG nền trang** (`bg-canvas`, không
phải thẻ trắng `bg-card`) — chốt với khách 31/08/2026: Gantt là một mặt phẳng liền, thêm
một cái hộp hay một mảng trắng quanh nó là mắt tự tách lưới và trục thành hai vùng rời.
Đúng lối Lark. Ô nào phải ĐỤC vì có nội dung trượt bên dưới (ô tên ghim, tiêu đề nhóm ghim)
thì cũng lấy `bg-canvas` chứ không lấy trắng.

- Lưới trái dùng **chính `TaskGroupsBoard`** của khung nhìn Danh sách — nên có đủ: ô sửa
  tại chỗ, ô tick, bung việc con, **ba tầng kéo thả** (việc · việc con · cột), và dòng
  **«Việc mới»** cuối mỗi nhóm. Chép sang bản thứ hai thì hai bên lệch nhau ngay ở lần sửa
  kế tiếp, mà lệch ở đây là *kéo thả sai chỗ* chứ không phải sai màu.
- Lưới vẽ **ĐỦ cột** của bộ «Tùy chỉnh» y như Danh sách, nhưng ô chứa nó hẹp (mặc định vừa
  khoảng **ba cột**) nên nó **tự cuộn ngang**, và **ô TÊN ghim lại** ở mép trái
  (`stickyTitle` — cũng ghim cả tiêu đề nhóm và chữ «Việc mới»). Bề rộng cột nhớ RIÊNG cho
  Gantt (`erp.work.ganttcols.{listId}`), bề rộng ô lưới ở `erp.work.ganttpane.{listId}`.
- ⚠️ **Hai bên là HAI khung cuộn riêng** (Lark cũng vậy), không phải một khung chung: lưới
  phải tự cuộn ngang để xem hết cột, mà khung chung thì cuộn ngang là kéo luôn cả trục
  thời gian đi. Cái giá là chiều DỌC phải tự đồng bộ — trục thời gian là bên **chủ động**
  (có thanh cuộn dọc thật), lưới trái để `overflow-y-hidden` và được lái bằng `scrollTop`
  (gán được cả khi tràn bị ẩn), nên không có hai thanh cuộn dọc chạy song song trông rất
  rối. Lăn chuột khi con trỏ ở trên lưới thì chuyển thẳng deltaY sang bên kia, không thì
  rê vào vùng tên việc là lăn không ăn gì.
- Nhờ mỗi bên là một khung cuộn: hàng tiêu đề `sticky top-0` của CẢ HAI bên đều dính đúng
  (sticky bám khung cuộn gần nhất), nhãn tháng dính `left-0` của chính trục, và ô tên dính
  `left-0` của chính lưới — không cần tính bù trừ bề rộng nào.
- ⚠️ **Hai bên phải sinh ra ĐÚNG cùng một dãy hàng**: `TaskGroupsBoard` vẽ bên trái,
  `buildGanttRows` dựng lại y hệt cho bên phải (nhóm · việc · việc con đang bung · dòng
  «Việc mới»), và MỌI dòng cao đúng `ROW_HEIGHT`. Vì vậy state đổi số dòng (thu/mở nhóm ·
  bung việc con · **cột đang bị kéo** — lúc ấy nhóm thu lại còn mỗi tiêu đề) đều nằm ở
  chính `GanttView`, không giấu bên trong cụm nhóm. Sửa cấu trúc dòng ở
  `task-list-group.tsx` thì PHẢI sửa kèm `gantt-rows.ts` — có test ghim từng trường hợp.
- **Hàng NHÓM** = một cột kanban, cùng cách gom với Danh sách (`groupTasksBySection`) nên
  thu/mở nhớ chung một chỗ. Thanh nhóm trải từ ngày sớm nhất tới hạn muộn nhất của các
  việc CÓ NGÀY trong nhóm, tô phần trăm việc đã xong, không kéo được (ngày của nó là ngày
  tính ra — kéo thì không biết phải dời việc nào).
- **Cụm điều khiển trục** (mức phóng · _Hôm nay_ · ‹ ›) nằm ĐÈ lên góc phải dải tiêu đề,
  đúng chỗ Lark đặt. Đè bằng `absolute` ở NGOÀI khung cuộn chứ không nhét vào hàng tiêu
  đề: nhét vào thì nó là một ô của hàng, tức cộng thêm bề rộng vào trục và cuộn được quá
  cuối dải; còn để trong luồng cuộn thì nó trôi mất khi kéo sang tháng khác. Mức phóng dời
  khỏi hàng tab vì đứng cạnh ba tab khung nhìn thì nhìn như tab thứ tư. Nút _Hôm nay_
  không thừa dù biểu đồ tự cuộn tới hôm nay lúc mở: cuộn đi xem quý sau rồi muốn quay về
  thì ở mức Ngày phải kéo ngược cả nghìn pixel; ‹ › nhảy 80% bề rộng đang nhìn.

### 10.2 Thang thời gian (`utils/gantt-scale.ts`)

Ba mức: **Ngày** (ô ngày + thứ, gom tháng ở hàng trên) · **Tuần** (`T.37` theo tuần ISO,
gom NĂM ở hàng trên) · **Tháng** (`Th 9`, gom năm).

⚠️ **Nhãn hàng TRÊN dính khi cuộn ngang** (`sticky`, mốc là mép phải của lưới trái + thanh
chia): kéo sang giữa tháng 9 mà chữ "Tháng 9/2026" đã trôi khỏi màn hình thì người dùng
chỉ còn nhìn một dãy số 1…30 không biết của tháng nào. Sticky đặt trên CHÍNH ô của tháng
ấy nên nhãn chỉ trượt trong lòng tháng mình rồi nhường chỗ cho tháng kế — không bao giờ
có hai nhãn chồng nhau. Mức Tuần cố ý gom hàng trên theo NĂM
chứ không theo tháng: một tuần vắt qua hai tháng thì ô tuần bị cắt đôi và hai hàng tiêu đề
không còn thẳng mép nhau.

Dải được **bo về trọn tuần / trọn tháng** ở hai mức xa, nếu không thì ô đầu và ô cuối là
một tuần/tháng cụt, nhìn như lưới vỡ. Toàn bộ hàm THUẦN và làm việc trên chuỗi
`"YYYY-MM-DD"` — đổi qua `Date` để so sánh là dính lệch một ngày ở múi giờ +07.

### 10.3 Ba loại kéo, ba cơ chế khác nhau — cố ý

| Kéo gì | Bằng gì | Vì sao |
|---|---|---|
| **Ngày** (cả thanh / hai mép) | `dnd-kit`, vị trí tạm ở `DragOverlay` | Cùng bộ với kanban. Luật "đổi trường nào" nằm ở `utils/gantt-drag.ts`, có test — sửa hành vi kéo thì sửa ở đó, đừng nhét vào component |
| **Nối phụ thuộc** | `pointerdown` thô (`use-gantt-link-draft.ts`) | Cho nó đi chung `DndContext` thì `onDragEnd` phải đoán cú thả vừa rồi mang nghĩa gì — đoán nhầm là **ghi đè ngày của một việc thật** |
| **Giãn cột / thanh chia** | Ghi thẳng vào biến CSS | `setState` mỗi nhịp chuột là cả biểu đồ vẽ lại, kéo thành giật |

### 10.4 Cột mốc (B-14) và mũi tên phụ thuộc (B-15)

- **Cột mốc** vẽ hình thoi tại `due_date`, kéo dời được; bật/tắt bằng nút cạnh viên trạng
  thái trong panel chi tiết, hoặc tạo thẳng bằng mục **«Cột mốc mới»** trong mũi tên cạnh
  nút «Việc mới». Mốc tạo từ đó **có ngày ngay** (hôm nay) — mốc không ngày thì không có
  hình thoi nào trên biểu đồ, bấm xong tưởng hụt. Đổi việc → mốc thì service gộp ngày về
  một mốc.
- **Kiểu mũi tên suy ra từ hai đầu người dùng chạm vào**, đúng lối DHTMLX: rời ở cuối →
  vào đầu = `FS`; đầu→đầu = `SS`; cuối→cuối = `FF`; đầu→cuối = `SF`. Đích không cần trúng
  cái chấm nhỏ — thả vào NỬA nào của thanh đích thì tính là đầu ấy.
- ⚠️ Phép dò đích đi theo `data-task-id`, **không** theo phần tử thanh: hai mép kéo đổi
  ngày là anh em của thanh và nằm đè lên nó, mà thanh của một việc chỉ có hạn rộng đúng
  một ngày (16px ở mức Tuần) — hai mép 7px phủ gần kín. Dò theo thanh thì thả vào những
  việc như thế (phần lớn dữ liệu thật) luôn trượt, và trượt IM LẶNG.
- Mũi tên vẽ bằng **SVG** phủ vùng các hàng, `pointer-events-none` cho cả tấm rồi bật lại
  cho từng đường — để tấm phủ ăn chuột thì không thanh nào kéo được nữa, mà lỗi ấy nhìn
  hệt như "kéo thanh bị hỏng".
- Rê vào đường thì giữa thân mũi tên hiện **viên mã kiểu** (`FS`/`SS`/`FF`/`SF`) — vừa là
  nhãn vừa là nút: bấm ra menu **đổi kiểu** và **xóa**. Gộp hai việc vào một viên chứ
  không bày hai nút tròn: chỗ trống trên một đường gấp khúc chỉ đủ cho một thứ, mà hai nút
  18px sát nhau thì bấm nhầm «xóa» khi định «đổi kiểu» là chuyện sớm muộn. Đổi kiểu KHÔNG
  cần dò lại vòng lặp (chiều mũi tên giữ nguyên); đổi **hai đầu** thì máy chủ từ chối —
  xóa rồi nối lại để đi qua đúng bộ kiểm của `create_link`.
- **Luật chặn vòng lặp nằm ở backend**, không ở giao diện — xem `02-bang-du-lieu.md`
  §3 (`tab_work_task_link`).

### 10.5 Chốt: KHÔNG dời lịch dây chuyền

**Quyết định 31/08/2026 (CR-226).** Kéo một việc thì **chỉ đổi ngày của chính việc ấy** —
mũi tên phụ thuộc là thứ để ĐỌC quan hệ trước–sau, không phải bộ máy tự nắn lịch. Việc sau
không tự chạy theo, kể cả khi cú kéo làm nó vi phạm ràng buộc.

Hệ quả phải biết: **đồ thị phụ thuộc có thể mâu thuẫn với ngày thật** (việc sau bắt đầu
trước khi việc trước xong) và hệ **không cảnh báo gì**. Đó là chủ ý — người lập kế hoạch
tự nhìn biểu đồ mà chỉnh. Ai định "sửa" chỗ này về sau thì đọc dòng này trước: nó không
phải lỗ hổng bỏ quên.

`lag_days` vì thế mới chỉ LƯU và hiện trên mũi tên.

### 10.6 Chưa làm

Đường găng (critical path) — cần lịch dây chuyền nên hoãn theo §10.5 · baseline · đặt phụ
thuộc cho **việc con** (backend chặn thẳng, muốn có thì phải bàn lại luật C-05 trước).
