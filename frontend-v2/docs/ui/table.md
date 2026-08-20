# Bảng danh sách

Mọi màn danh sách dùng **`DataTable`** (`@/shared/data-table`). Không tự ghép
`<Table>`/`<TableRow>` của `shared/ui/table.tsx` ở tầng trang — những primitive
đó chỉ là vật liệu cho `DataTable`.

`DataTable` lo: ẩn/hiện cột, kéo giãn cột, **kéo thả đổi thứ tự cột**, **ghim
cột**, tô màu cột, **nút tải lại**, nhớ bố cục, phân trang, trạng thái đang tải /
lỗi / rỗng. Trang gọi nó lo: gọi API, giữ state trang và bộ lọc.

---

## 1. Khung tối thiểu

```tsx
const columns = useMemo<DataTableColumn<Employee>[]>(() => [
  { key: 'code', header: 'Mã NV', width: 140, cell: (e) => e.code },
  { key: 'full_name', header: 'Họ tên', width: 260, hideable: false,
    cell: (e) => <span className="truncate">{e.full_name}</span> },
  { key: 'status', header: 'Tình trạng', width: 140,
    cell: (e) => <Badge>{e.status}</Badge> },
], [])

<DataTable
  fillHeight
  columns={columns}
  rows={data?.items}
  getRowId={(e) => e.id}
  isLoading={isLoading}
  isError={isError}
  emptyMessage="Không tìm thấy nhân sự nào."
  storageKey="hr.employees"
  onRowClick={(e) => navigate(appRoutes.hr.employeeDetail(e.id))}
  pagination={{ page, pageSize, total: data?.total ?? 0,
                onPageChange: setPage, onPageSizeChange: setPageSize,
                unitLabel: 'nhân sự' }}
  toolbar={<>…</>}
/>
```

### `DataTableColumn`

| Field | Bắt buộc | Ghi chú |
| --- | --- | --- |
| `key` | ✓ | Duy nhất trong bảng; là id khi ẩn cột, nhớ độ rộng, thứ tự, màu |
| `header` | ✓ | **Luôn có chữ**, kể cả cột ảnh/hành động — mục không tên trong menu "Cột" là một dòng trống. Cột bắt buộc nhập thì thêm đuôi `" *"` (xem *Cột bắt buộc* bên dưới) |
| `cell` | ✓ | `(row) => ReactNode` |
| `width` | | px, độ rộng ban đầu |
| `minWidth` | | Chặn dưới khi kéo, mặc định 64 |
| `align` | | `left` (mặc định) / `center` / `right` |
| `hideable` | | `false` = luôn hiện. Đặt cho cột định danh (tên/mã) và cột hành động |
| `defaultHidden` | | Ẩn sẵn lần đầu, người dùng bật lại được |
| `defaultPinned` | | Ghim trái sẵn. Chỉ đặt cho cột định danh của bảng **nhiều cột** |

### Prop của `DataTable`

| Prop | Ghi chú |
| --- | --- |
| `rows` | `undefined` = chưa có dữ liệu; `[]` = rỗng → hiện `emptyMessage` |
| `getRowId` | Bắt buộc, dùng làm `key` của dòng |
| `isLoading` / `isError` | Hiện khung xương / dòng báo lỗi (`errorMessage`) |
| `onRowClick` | Bấm dòng; ô hành động phải `stopPropagation` |
| `onRefresh` | Việc chạy khi bấm **Tải lại**. Bỏ trống = tự `invalidateQueries({ type: 'active' })` |
| `toolbar` | Nội dung chèn bên TRÁI cụm nút phải (xem mục 3) |
| `storageKey` | Có thì nhớ bố cục vào localStorage |
| `pagination` | Phân trang server-side |
| `fillHeight` | Bảng cao bằng khung chứa, chỉ vùng dòng cuộn |

### Quy ước khác

- `columns` **phải** bọc `useMemo` — mảng dựng lại mỗi render sẽ làm bảng tính lại bố cục liên tục.
- `storageKey` theo dạng `<module>.<entity>` (`hr.employees`, `document.records`).
- Ô hành động: bọc `onClick={(e) => e.stopPropagation()}`, nếu không mỗi lần bấm nút sẽ mở luôn trang chi tiết vì `onRowClick` bắt được.
- Nội dung dài: thêm `truncate` trong `cell`. Bảng chạy `table-fixed` nên ô không tự nong ra.

### Cột bắt buộc — khai bằng đuôi `" *"`

Cột nào **bắt buộc nhập** thì viết tiêu đề kết thúc bằng dấu cách rồi dấu sao:

```ts
{ key: 'warehouse_code', header: 'Kho nhận *', width: 120 }
```

`shared/data-table/required-header.ts` tách đuôi đó ra, ô tiêu đề vẽ chữ bình thường
cộng một dấu sao `text-destructive` kèm lời nhắc *"Bắt buộc trước khi gửi duyệt"*.

- **Đừng đổi `header` thành `ReactNode` để nhét JSX vào.** Chuỗi tiêu đề còn được
  dùng làm nhãn khối kéo thả (`startDrag`), tên cột trong menu **Cột** và số đo bề
  rộng tự động — cho JSX vào là gãy cả ba chỗ. Ba nơi đó gọi `columnLabel(header)`
  nên tên cột hiện ra không dính dấu sao.
- Quy ước là **dấu cách rồi mới tới sao**. `'SL*'` viết liền bị coi là tiêu đề thường,
  cố ý vậy để tiêu đề có `*` sẵn (ví dụ `'VAT%*'` gõ thiếu dấu cách) không bị cắt cụt.
- Dấu sao chỉ để **báo**; phần **chặn** nằm ở validator của phân hệ. Với ba chứng từ
  mua hàng, bộ trường bắt buộc khai một chỗ duy nhất tại
  `modules/procurement/utils/required-fields.ts` (xem **CR-107**) — sửa dấu sao mà
  quên sửa validator là hai thứ trôi khỏi nhau.
- Ô nhập trong biểu mẫu / popup thì dùng `shared/ui/required-mark.tsx`
  (`<RequiredMark />`, đổi lời nhắc bằng prop `hint`), đừng gõ `*` thẳng vào chuỗi nhãn.

---

## 2. Bọc `Card` — BẮT BUỘC

Bảng luôn nằm trong `Card`, không đặt trần lên nền trang:

```tsx
<PageContainer fill>                        {/* h-full + flex-col */}
  <PageHeader … />
  <Card className="flex min-h-0 flex-1 flex-col p-4">
    <DataTable fillHeight … />
  </Card>
</PageContainer>
```

Không phải chuyện thẩm mỹ: nền của `Card` là `bg-card` (trắng đục) — cùng màu với
hàng dữ liệu, còn hàng tiêu đề `bg-muted` xám hơn một bậc. Bỏ `Card` thì bảng
ngồi trên nền trang `bg-secondary`, tương phản tiêu đề / thân bảng đổi hẳn và màn
đó **nhìn lệch tông so với mọi phân hệ khác**.

Ba mắt xích của chế độ fit chiều cao (`PageContainer fill` → `Card flex min-h-0
flex-1 flex-col` → `DataTable fillHeight`) phải đủ cả ba, thiếu một là hỏng.

Trang **chi tiết** thì KHÔNG dùng `fill` — để nội dung dài ra và cuộn cả trang.

Phân trang là **server-side**. `page` / `pageSize` giữ ở state của trang, gửi
lên API; `total` lấy từ response. Chân bảng: trái = chọn số dòng (10/20/50/100)
+ tổng bản ghi, phải = dãy số trang + lùi/tiến.

**Luôn reset về trang 1 khi bất kỳ điều kiện lọc nào đổi**, nếu không người dùng
đứng ở trang 7 mà kết quả mới chỉ có 2 trang thì thấy bảng trống:

```tsx
useEffect(() => setPage(1), [queryKey, debouncedValue, departmentId, status])
```

---

## 3. Thanh công cụ: tìm kiếm → select chính → Bộ lọc

Một hàng duy nhất, thứ tự cố định để mọi màn nhìn như một:

```
[ 🔍 ô tìm kiếm ] [ select chính 1 ] [ select chính 2 ] [ Bộ lọc ]  ……  [ ⟳ ] [ Cột ]
└──────────────────── prop `toolbar` ────────────────────┘        └ DataTable tự vẽ ┘
```

- **Ô tìm kiếm** — `w-full max-w-xs`, icon `Search` đặt tuyệt đối bên trái, input `pl-9`.
- **Select chính** — 1–3 ô CHỌN dùng hằng ngày (pháp nhân, trạng thái, loại…), `w-44` (rộng hơn thì `w-48`). Mỗi ô luôn có mục "Tất cả …" làm mặc định.
- **`<ConditionalFilter />`** — bộ lọc nâng cao, đứng cuối cụm trái.
- **Tải lại + Cột** — `DataTable` tự render, dính mép phải (`ml-auto`). Trang không phải khai gì.

```tsx
toolbar={
  <>
    <div className="relative w-full max-w-xs">
      <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input className="pl-9" placeholder="Tìm theo mã…" value={keyword}
             onChange={(e) => setKeyword(e.target.value)} />
    </div>

    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-44"><SelectValue /></SelectTrigger>
      <SelectContent>
        <SelectItem value="all">Tất cả trạng thái</SelectItem>
        …
      </SelectContent>
    </Select>

    <ConditionalFilter />
  </>
}
```

Tab (vd luồng văn bản đến / đi / nội bộ) thì đặt **ngoài** `DataTable`, giữa
`PageHeader` và `Card` — nó chia tập dữ liệu chứ không phải một ô lọc.

### Nút Tải lại

Mặc định làm mới MỌI query đang hoạt động của trang
(`invalidateQueries({ type: 'active' })`) chứ không chỉ query của bảng: màn danh
sách nào cũng kèm query phụ (danh mục công ty, trạng thái…), làm mới cả cụm mới
ra số khớp nhau. Cần việc khác thì truyền `onRefresh` (nhận cả hàm async) — bảng
chờ promise xong mới tắt vòng xoay. Cờ quay do chính nút giữ, không đọc
`isFetching`: dữ liệu về tức thì vẫn phải thấy một nhịp phản hồi.

### Bộ lọc nâng cao

Khai trường trong `modules/<m>/config/*-filter-fields.ts`, bọc trang bằng provider:

```tsx
const FILTER_CONFIG = {                        // hằng số tầng module, KHÔNG inline
  fields: EMPLOYEE_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['department_id', 'status'],
}

export function EmployeeListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <EmployeeListContent />                  {/* useFilterQuery() phải ở TRONG provider */}
    </FilterProvider>
  )
}
```

#### Ba cái bẫy

1. **`preserveParams` phải liệt kê đủ tên param của các select trên thanh công cụ.**
   `applyChanges` dựng lại query string từ đầu và chỉ giữ `searchParamName` +
   `preserveParams`. Thiếu tên nào là bấm "Áp dụng" xong mất luôn bộ lọc đó.
2. **`FILTER_CONFIG` để ở tầng module.** Object/mảng inline đổi identity mỗi
   render → `applyChanges` tái tạo vô ích.
3. **`name` của field phải nằm trong whitelist `FILTERABLE` của controller.**
   Sai tên thì backend im lặng bỏ qua, giao diện trông như bộ lọc hỏng.

#### State bộ lọc nằm trên URL

| Loại | Hook | Ghi chú |
| --- | --- | --- |
| Ô gõ chữ | `useUrlSearchParam(name?)` | Có debounce, state cục bộ để gõ không giật |
| Ô chọn | `useUrlParamState(name, default)` | Đọc thẳng URL; trùng mặc định thì xóa param |
| Điều kiện nâng cao | `ConditionalFilter` tự lo | Dạng `<field>__<op>` |

`page` / `pageSize` KHÔNG lên URL.

#### Cú pháp operator gửi backend

Hậu tố của dự án **khác** FilterCN gốc — bảng ánh xạ nằm ở
`shared/conditional-filter/helpers/operators.ts`, phải khớp `OPERATORS` trong
`backend/app/core/filter_operators.py`:

```
is → __eq        is_not → __ne        contains → __contains
between → __between      is_empty/is_not_empty → __isnull=true/false
```

Endpoint không chạy qua `apply_filters` (vd `/api/users`) thì **không** gắn
`ConditionalFilter` — cú pháp `__op` vô tác dụng ở đó.

---

## 4. Tùy biến cột (menu "Cột")

Người dùng tự chỉnh, bảng nhớ vào localStorage theo `storageKey`:

| Việc | Cách làm | Ghi ở |
| --- | --- | --- |
| Ẩn / hiện | Bấm tên cột trong menu | `hiddenColumns` |
| Đổi độ rộng | Kéo vạch mép phải ô tiêu đề; **nháy đúp** = vừa nội dung | `columnWidths` |
| Đổi thứ tự | Kéo ô tiêu đề, **hoặc** kéo tay nắm ⠿ trong menu | `columnOrder` |
| Ghim trái | Icon ghim trong menu | `pinnedColumns` |
| Tô màu cột | Bảng màu trong menu | `columnColors` |
| Vừa nội dung tất cả | Mục cuối menu | `columnWidths` |

Hai chỉ báo khi kéo thả, cùng một ngôn ngữ hình ảnh:
- Kéo trên hàng tiêu đề → vạch dọc có chóp mũi tên ngay khe sẽ chèn
  (`column-drop-indicator.tsx`).
- Kéo trong menu → vạch ngang + "viên" nhãn bám con trỏ (portal ra `body`, vì
  khung menu và `overflow-y-auto` của danh sách sẽ xén mất).

Thứ tự luôn tính trên danh sách ĐẦY ĐỦ (kể cả cột đang ẩn) — sắp lại chỉ trên cột
đang hiện thì cột ẩn bị dồn xuống cuối lúc bật lại.

---

## 5. Màu sắc & kích thước — và vì sao lại thế

Kẻ ô đầy đủ, mọi dòng cùng chiều cao. Các con số nằm trong `data-table.tsx`:

| | Class | Màu thực tế (light) |
| --- | --- | --- |
| Khung ngoài | `Card` `p-4` | `bg-card` → `#fff` |
| Hàng tiêu đề | `h-9 px-3 text-xs`, `bg-muted` | `rgb(246,248,251)` |
| Hàng dữ liệu | `h-10 px-3 py-0`, `bg-card` | `#fff`, hover `bg-muted` |
| Dòng đang chọn | `data-[state=selected]:bg-muted` | như hover |
| Ô báo trạng thái | `h-20`, căn giữa | — |
| Ảnh/avatar trong ô | `size-7` | — |

**Nền hàng phải ĐỤC, cấm biến thể alpha** (`bg-muted/50`, `bg-card/60`…): ô của
cột ghim lấy `bg-inherit` từ hàng để che phần bảng đang cuộn ngang phía dưới; nền
trong suốt là nội dung lộ xuyên qua cột dính. Cũng vì vậy `TableRow` mặc định của
shadcn (`hover:bg-muted/50`) bị ghi đè ở hàng tiêu đề.

**Chiều cao đặt cứng kèm `py-0`, không dùng padding dọc.** Mỗi cột một loại nội
dung (chữ, huy hiệu, ảnh); để padding tự tính thì dòng có huy hiệu cao hơn hẳn
dòng chỉ có chữ.

### Sáu cái bẫy CSS đã vấp — đừng vấp lại

1. **`sticky` thead làm mất viền.** Tailwind preflight đặt
   `border-collapse: collapse`; ở chế độ đó viền thuộc về *bảng* chứ không thuộc
   *ô*, nên hàng tiêu đề sticky bị bỏ viền. → Viền ô tiêu đề vẽ bằng
   `inset box-shadow`, không dùng `border`.
2. **Dòng cuối hở đáy.** `TableBody` của shadcn có `[&_tr:last-child]:border-0`.
   Đúng khi bảng kết thúc sát viền khung, nhưng ở chế độ `fillHeight` còn khoảng
   trống bên dưới → chỉ khi đó mới bật lại `border-b`.
3. **`space-y-*` cộng dồn với `gap` của Card.** `Card` là `flex flex-col` đã có
   sẵn `gap-6`; thêm `space-y-4` thành 40px chứ không phải 16px. → Ghi đè thẳng
   `gap-4`, đừng dùng `space-y`.
4. **Thiếu `min-w-0` là bảng nong vỡ trang.** Item flex / ô grid mặc định không
   co dưới min-content. Bảng rộng sẽ đẩy cả trang trôi ngang thay vì tự cuộn.
   Đã xử ở `module-layout.tsx` (`SidebarInset`, `main`); ô grid nào chứa bảng
   cũng phải tự thêm.
5. **`line-clamp` bị `block` ghi đè.** `line-clamp-2` cần `display: -webkit-box`;
   viết kèm `block` trong cùng `cn(...)` là mất tác dụng, chữ tràn 3–4 dòng.
6. **Hàng có nút bung dính nền ALPHA.** `TableRow` của shadcn có sẵn
   `has-aria-expanded:bg-muted/50` — đặt `aria-expanded` lên một nút trong hàng
   (nút bung nhánh con) là cả hàng nhận nền nửa trong suốt, và ô cột ghim
   `bg-inherit` lộ nguyên phần bảng đang cuộn ngang phía sau. → Đã sửa thành
   `has-aria-expanded:bg-muted` (đục) trong `shared/ui/table.tsx`.
   **Cùng một luật với bẫy nền alpha ở trên** — chỗ này chỉ là một cửa nữa dẫn
   tới nó, mở ra bằng thuộc tính a11y chứ không phải bằng class.

---

## 6. Sửa primitive dùng chung

`shared/ui/table.tsx` là component generated — mặc định **không sửa**. Cần đổi
diện mạo thì viết class ở `data-table.tsx` (lớp sơn đè), giống cách
`module-sidebar.tsx` làm với `sidebar.tsx`.

Hai ngoại lệ tới giờ:

**(1)** thêm prop `containerClassName` cho `Table`. Khung
cuộn nằm bên trong `Table` và không có đường nào với tới, mà đó đúng là chỗ cần
`flex-1 overflow-auto` cho chế độ fit chiều cao. Thay đổi thuần cộng thêm, mặc
định không đổi.

**(2)** đổi `has-aria-expanded:bg-muted/50` thành `has-aria-expanded:bg-muted`
(bẫy số 6). Đây là sửa một mặc định của shadcn chứ không phải cộng thêm, nên ghi
rõ lý do: nền hàng có alpha làm hỏng cột ghim, mà luật này bật lên bởi một
thuộc tính a11y (`aria-expanded`) nên không lường trước được từ tầng gọi. Nếu buộc phải sửa primitive lần nữa: chỉ cộng thêm, không đổi
hành vi mặc định, và ghi lý do vào đây.
