# Bảng danh sách

Mọi màn danh sách dùng **`DataTable`** (`@/shared/data-table`). Không tự ghép
`<Table>`/`<TableRow>` của `shared/ui/table.tsx` ở tầng trang — những primitive
đó chỉ là vật liệu cho `DataTable`.

`DataTable` lo: ẩn/hiện cột, kéo giãn cột, nhớ bố cục, phân trang, trạng thái
đang tải / lỗi / rỗng. Trang gọi nó lo: gọi API, giữ state trang và bộ lọc.

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
| `key` | ✓ | Duy nhất trong bảng; là id khi ẩn cột và nhớ độ rộng |
| `header` | ✓ | **Luôn có chữ**, kể cả cột ảnh/hành động — mục không tên trong menu "Cột" là một dòng trống |
| `cell` | ✓ | `(row) => ReactNode` |
| `width` | | px, độ rộng ban đầu |
| `minWidth` | | Chặn dưới khi kéo, mặc định 64 |
| `align` | | `left` (mặc định) / `center` / `right` |
| `hideable` | | `false` = luôn hiện. Đặt cho cột định danh (tên/mã) và cột hành động |
| `defaultHidden` | | Ẩn sẵn lần đầu, người dùng bật lại được |

### Quy ước khác

- `columns` **phải** bọc `useMemo` — mảng dựng lại mỗi render sẽ làm bảng tính lại bố cục liên tục.
- `storageKey` theo dạng `<module>.<entity>` (`hr.employees`, `hr.companies`). Có nó thì cột ẩn + độ rộng được nhớ vào localStorage.
- Ô hành động: bọc `onClick={(e) => e.stopPropagation()}`, nếu không mỗi lần bấm nút sẽ mở luôn trang chi tiết vì `onRowClick` bắt được.
- Nội dung dài: thêm `truncate` trong `cell`. Bảng chạy `table-fixed` nên ô không tự nong ra.

---

## 2. Chiều cao & phân trang

Màn danh sách luôn **fit chiều cao**: bảng cao bằng khung, chỉ vùng dòng cuộn,
thanh phân trang dính đáy. Cần đủ **cả ba** mắt xích, thiếu một là hỏng:

```tsx
<PageContainer fill>                        {/* h-full + flex-col */}
  <PageHeader … />
  <Card className="flex min-h-0 flex-1 flex-col p-4">
    <DataTable fillHeight … />
  </Card>
</PageContainer>
```

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

## 3. Bộ lọc

Chia hai tầng — đừng nhồi hết vào thanh công cụ:

- **Thanh công cụ**: ô tìm kiếm + 1–3 select dùng hằng ngày.
- **"Bộ lọc" nâng cao** (`ConditionalFilter`): các trường còn lại, có đủ phép so
  sánh. Khai trong `modules/<m>/config/*-filter-fields.ts`.

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

### Ba cái bẫy

1. **`preserveParams` phải liệt kê đủ tên param của các select trên thanh công cụ.**
   `applyChanges` dựng lại query string từ đầu và chỉ giữ `searchParamName` +
   `preserveParams`. Thiếu tên nào là bấm "Áp dụng" xong mất luôn bộ lọc đó.
2. **`FILTER_CONFIG` để ở tầng module.** Object/mảng inline đổi identity mỗi
   render → `applyChanges` tái tạo vô ích.
3. **`name` của field phải nằm trong whitelist `FILTERABLE` của controller.**
   Sai tên thì backend im lặng bỏ qua, giao diện trông như bộ lọc hỏng.

### State bộ lọc nằm trên URL

| Loại | Hook | Ghi chú |
| --- | --- | --- |
| Ô gõ chữ | `useUrlSearchParam(name?)` | Có debounce, state cục bộ để gõ không giật |
| Ô chọn | `useUrlParamState(name, default)` | Đọc thẳng URL; trùng mặc định thì xóa param |
| Điều kiện nâng cao | `ConditionalFilter` tự lo | Dạng `<field>__<op>` |

`page` / `pageSize` KHÔNG lên URL.

### Cú pháp operator gửi backend

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

## 4. Trình bày — và vì sao lại thế

Kẻ ô đầy đủ, mọi dòng cùng chiều cao. Các con số nằm trong `data-table.tsx`:

| | Giá trị |
| --- | --- |
| Ô tiêu đề | `h-9`, `px-3`, `text-xs`, nền `bg-muted` |
| Ô dữ liệu | `h-10`, `px-3`, `py-0` |
| Ô báo trạng thái | `h-20`, căn giữa |
| Ảnh/avatar trong ô | `size-7` |

**Chiều cao đặt cứng kèm `py-0`, không dùng padding dọc.** Mỗi cột một loại nội
dung (chữ, huy hiệu, ảnh); để padding tự tính thì dòng có huy hiệu cao hơn hẳn
dòng chỉ có chữ.

### Bốn cái bẫy CSS đã vấp — đừng vấp lại

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

---

## 5. Sửa primitive dùng chung

`shared/ui/table.tsx` là component generated — mặc định **không sửa**. Cần đổi
diện mạo thì viết class ở `data-table.tsx` (lớp sơn đè), giống cách
`module-sidebar.tsx` làm với `sidebar.tsx`.

Ngoại lệ duy nhất tới giờ: thêm prop `containerClassName` cho `Table`. Khung
cuộn nằm bên trong `Table` và không có đường nào với tới, mà đó đúng là chỗ cần
`flex-1 overflow-auto` cho chế độ fit chiều cao. Thay đổi thuần cộng thêm, mặc
định không đổi. Nếu buộc phải sửa primitive lần nữa: chỉ cộng thêm, không đổi
hành vi mặc định, và ghi lý do vào đây.
