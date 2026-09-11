import { Fragment, useMemo, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { ConditionalFilter, useOptionalFilterContext } from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Card } from '@/shared/ui/card'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

const ALL = 'all'

interface CatalogTableProps<T extends { id: number; is_active: boolean }> {
  /** Khóa nhớ layout bảng (ẩn/hiện, độ rộng, thứ tự cột). */
  storageKey: string
  items: T[]
  columns: DataTableColumn<T>[]
  /** Các trường được ô tìm kiếm quét qua. */
  searchFields: (row: T) => string[]
  searchPlaceholder: string
  /**
   * Câu gợi ý rút gọn cho khổ điện thoại, nơi ô tìm chia hàng với cụm nút — xem
   * `SearchFieldProps.placeholderShort`. Bỏ trống thì dùng câu đủ ở mọi khổ, và
   * trình duyệt sẽ xén đuôi nếu không vừa.
   */
  searchPlaceholderShort?: string
  /** Bỏ trống = danh mục chỉ đọc, bấm dòng không đi đâu cả. */
  detailPath?: (id: number) => string
  emptyMessage?: string
  /** Lọc thêm sau ô tìm kiếm và select trạng thái (vd bộ lọc nâng cao). */
  filterRows?: (rows: T[]) => T[]
  /**
   * Bày BỘ LỌC NÂNG CAO (điều kiện tự ghép) cho danh mục này.
   *
   * Màn rộng: nút riêng + popover (`ConditionalFilter`). Khổ hẹp: nhúng thẳng
   * phần ruột vào tờ trượt lọc (`AdvancedFilterSection`) — popover neo vào một
   * nút trên thanh công cụ đã chật, bung ra ở 390px thì che gần hết màn mà vẫn
   * không đủ ngang cho một hàng điều kiện.
   *
   * ⚠️ Đòi danh mục phải nằm trong một `FilterProvider`; không có thì
   * `CatalogTable` tự bỏ qua chứ không nổ (đọc bằng `useOptionalFilterContext`).
   */
  advancedFilter?: boolean
  /**
   * Ô lọc riêng CÓ NHÃN của từng danh mục.
   *
   * Khai ở đây thay vì `extraToolbar` thì `CatalogTable` dựng chúng ở **hai
   * chỗ**: xếp thẳng hàng trên thanh công cụ từ `md` trở lên, và xếp dọc có nhãn
   * trong tờ trượt lọc ở khổ hẹp.
   *
   * ⚠️ **Truyền cùng MỘT phần tử cho cả hai chỗ, đừng dựng hai bản.** React vẽ
   * cùng một mô tả ra hai instance, mà cả hai cùng đọc/ghi một khóa trên URL nên
   * chúng luôn khớp nhau. Chép thành hai bản khai khác nhau thì hai khổ màn lọc
   * ra hai kết quả khác nhau mà không chỗ nào báo.
   */
  filters?: { label: string; node: ReactNode }[]
  /**
   * Nội dung MỘT THẺ ở khổ hẹp — xem `DataTableProps.mobileCard`. Bỏ trống thì
   * danh mục đó vẫn ra bảng cuộn ngang như cũ.
   */
  mobileCard?: (row: T) => ReactNode
  /** Lớp gắn vào thanh công cụ, dùng để ghim nó khi cuộn (xem `list-sticky.ts`). */
  toolbarClassName?: string
  /**
   * Bày ô lọc *Đang dùng / Ngừng*. Tắt cho danh mục mà mọi dòng luôn `is_active`
   * — ô lọc trên một cột không bao giờ đổi giá trị thì chọn "Ngừng" chỉ làm
   * trắng bảng, còn "Đang dùng" thì y hệt "Tất cả": bày ra là hứa một thứ danh
   * mục đó không có.
   */
  showStatusFilter?: boolean
  /**
   * Khóa nhận dạng một dòng. Mặc định là `id`, nhưng danh mục nào gộp nhiều
   * thang vào một bảng thì `id` KHÔNG còn duy nhất — xem `SecurityLevelCatalog`.
   */
  getRowId?: (row: T) => string | number
  /**
   * Param tab của trang chứa bảng, để nút *Xóa lọc* không quét mất nó. Màn Sổ
   * văn bản chia tab bằng `kind` chứ không phải `tab`.
   */
  keepFilterParams?: string[]
}

/**
 * Bảng chung cho MỘT danh mục nền của phân hệ Văn bản.
 *
 * Bốn danh mục (loại văn bản, mức mật/khẩn, đối tác, trường động) đều cần đúng
 * một bộ: tìm theo từ khóa, lọc đang dùng / ngừng, bấm dòng vào chi tiết. Chỉ
 * cột và ô lọc riêng là khác nhau nên chúng đi vào props.
 *
 * KHÔNG tự vẽ tiêu đề trang: cả bốn nằm chung trang "Thiết lập văn bản", tiêu
 * đề và nút Thêm mới do trang đó lo (xem `pages/document-settings-page.tsx`).
 */
export function CatalogTable<T extends { id: number; is_active: boolean }>({
  storageKey,
  items,
  columns,
  searchFields,
  searchPlaceholder,
  searchPlaceholderShort,
  detailPath,
  emptyMessage = 'Không có bản ghi nào khớp điều kiện đang lọc.',
  filterRows,
  advancedFilter = false,
  filters,
  mobileCard,
  toolbarClassName,
  showStatusFilter = true,
  getRowId = (row) => row.id,
  keepFilterParams,
}: CatalogTableProps<T>) {
  const navigate = useNavigate()
  //  `useOptional…` chứ không `useFilterContext`: bảy danh mục dùng chung khung
  //  này, chỉ một cái bọc `FilterProvider`. Bản bắt buộc sẽ ném lỗi ở sáu cái kia.
  const filter = useOptionalFilterContext()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)

  const rows = useMemo(() => {
    const needle = debouncedValue.trim().toLowerCase()
    const found = items.filter((item) => {
      //  Ô lọc bị tắt mà URL vẫn còn `?status=inactive` (dán lại link cũ) thì
      //  bảng trắng trơn và không còn ô nào để gỡ điều kiện ra.
      if (showStatusFilter && status !== ALL && item.is_active !== (status === 'active'))
        return false
      if (!needle) return true
      return searchFields(item).some((field) => (field ?? '').toLowerCase().includes(needle))
    })
    return filterRows ? filterRows(found) : found
  }, [items, status, showStatusFilter, debouncedValue, searchFields, filterRows])

  //  Dựng MỘT LẦN rồi dùng cho cả hàng ngang (màn rộng) lẫn tờ trượt (màn hẹp) —
  //  xem ghi chú ở `CatalogTableProps.filters`.
  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-44">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
        <SelectItem value="active">Đang dùng</SelectItem>
        <SelectItem value="inactive">Ngừng</SelectItem>
      </SelectContent>
    </Select>
  )

  //  Đếm ô lọc ĐANG KHÁC MẶC ĐỊNH để báo lên nút «Bộ lọc» ở khổ hẹp. Chỉ đếm
  //  được ô trạng thái vì nó là ô duy nhất `CatalogTable` tự giữ state; ô của
  //  `filters` do trang ngoài giữ nên không đọc được từ đây.
  //  ⚠️ Cộng CẢ điều kiện nâng cao: dưới 768px hai tầng lọc nằm sau đúng một
  //  nút, đếm thiếu một tầng thì người dùng thấy nút trơn mà danh sách vẫn
  //  đang bị cắt bớt, rồi đi tìm lỗi ở dữ liệu.
  const quickFilterCount =
    (showStatusFilter && status !== ALL ? 1 : 0) + (advancedFilter ? (filter?.activeCount ?? 0) : 0)

  return (
    // Bọc `Card` giống mọi màn danh sách khác (Nhân sự, Thu mua) — bảng đặt
    // trần lên nền trang thì màu hàng tiêu đề và thân bảng lệch hẳn.
    //
    //  ⚠️ `p-3` ở khổ hẹp vì lề âm của dải thanh công cụ ghim tính theo đúng đệm
    //  đó; `min-w-0` vì ô flex mặc định `min-width:auto` nên thẻ không co xuống
    //  dưới bề rộng tự nhiên của bảng bên trong — thiếu nó thì CẢ TRANG trượt
    //  ngang ở khổ hẹp.
    <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={getRowId}
        storageKey={storageKey}
        keepFilterParams={keepFilterParams}
        fillHeight
        toolbarClassName={toolbarClassName}
        //  Ô tìm và cụm nút đứng chung một hàng ở khổ hẹp, nên `ml-auto` mặc
        //  định sẽ xé hàng thành hai mẩu cách nhau một quãng trống.
        toolbarActionsClassName="max-md:ml-0"
        mobileCard={mobileCard}
        onRowClick={detailPath ? (row) => navigate(detailPath(row.id)) : undefined}
        emptyMessage={emptyMessage}
        toolbar={
          <>
            {/*  ⚠️ **`max-md:min-w-40` là SÀN chống bẹp, không phải chuyện thẩm
                 mỹ.** `SearchField` khai `flex-1 min-w-0`, tức nó nhường chỗ cho
                 tới khi còn 0. Thanh công cụ của danh mục có thể lên tới NĂM
                 khối (tìm · lọc nhanh · lọc nâng cao · Tải lại · Cột): đo ở 393px
                 trên màn Thiết lập văn bản, ô tìm bị ép còn **55px**, phần gõ
                 chữ còn **5px** — một ô nhập không nhập được.

                 Có sàn thì khi không đủ chỗ, `flex-wrap` đẩy khối THỪA xuống
                 hàng dưới thay vì bóp ô tìm; màn nào chỉ ba khối (như Sổ văn bản)
                 vẫn gọn một hàng vì ô tìm tự giãn quá sàn. */}
            <SearchField
              value={keyword}
              onChange={setKeyword}
              placeholder={searchPlaceholder}
              placeholderShort={searchPlaceholderShort}
              className="max-md:min-w-40 md:min-w-56 md:max-w-xs"
            />

            {/*  Khổ hẹp: mọi ô lọc gom sau MỘT nút biểu tượng, để ô tìm và cụm
                 nút vừa một hàng. Nút tự ẩn từ `md` trở lên. */}
            {(showStatusFilter || filters?.length || advancedFilter) && (
              <QuickFilterSheet
                iconOnly
                activeCount={quickFilterCount}
                //  Bộ lọc nâng cao giữ điều kiện ở dạng NHÁP tới khi ai đó gọi
                //  `apply()`. Không nối vào thì người dùng gõ xong ba điều kiện,
                //  bấm nút duy nhất trong tầm mắt, tờ trượt đóng lại và danh
                //  sách không đổi gì — nhìn ra y như hệ thống nuốt mất thao tác.
                onApply={advancedFilter ? filter?.apply : undefined}
              >
                {showStatusFilter && (
                  <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                )}
                {filters?.map((item) => (
                  <QuickFilterField key={item.label} label={item.label}>
                    {item.node}
                  </QuickFilterField>
                ))}
                {advancedFilter && filter && <AdvancedFilterSection />}
              </QuickFilterSheet>
            )}

            {/*  `md:contents` chứ không `md:flex`: bọc cụm lọc trong một thẻ flex
                 riêng thì cả cụm là MỘT ô của thanh công cụ — không đủ chỗ là nó
                 rớt nguyên khối xuống dòng dưới, chừa một khoảng trống dài bên
                 phải ô tìm. */}
            <div className="hidden md:contents">
              {showStatusFilter && statusSelect}
              {filters?.map((item) => <Fragment key={item.label}>{item.node}</Fragment>)}
              {advancedFilter && filter && <ConditionalFilter />}
            </div>
          </>
        }
      />
    </Card>
  )
}
