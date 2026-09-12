import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { PR_LINE_STATUS } from '@/shared/constants/statuses'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { STICKY_TOOLBAR_BASE } from '@/shared/ui/sticky-toolbar'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { usePrLines } from '../hooks/use-purchase-report'
import { ProgressStatusBadge, StatusBadge } from './document-status-badge'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import type { PrLineRow } from '../types/purchase-report'

const ALL = 'all'

/**
 * Bộ lọc TIẾN ĐỘ dòng hàng: `chua_dat` là giá trị GỘP (backend hiểu = no_po +
 * not_ordered) — đúng mục tiêu báo cáo: soi mã chưa được đặt để khỏi đặt sót đơn.
 */
const LINE_STATUS_OPTIONS = [
  { value: 'chua_dat', label: 'Chưa được đặt hàng (gộp)' },
  ...PR_LINE_STATUS.map((option) => ({ value: option.value, label: option.label })),
]

/**
 * Thanh công cụ ghim DƯỚI dải điều khiển của trang.
 *
 * Cả hai chỗ nhúng — tab trong *Báo cáo mua hàng* và trang riêng
 * `/procurement/pr-lines-report` — đều ghim một dải điều khiển (ô công ty · năm
 * · nút lệnh) cao **53px** ở `top-0`, nên hằng này dùng chung.
 *
 * ⚠️ 53px là chiều cao THẬT của dải đó: đệm `pt-2` 8 + ô chọn `h-9` 36 + `pb-2`
 * 8 + `border-b` 1. Sửa đệm hay cỡ ô ở một trong hai trang thì **phải đo lại
 * bằng `getBoundingClientRect` và sửa luôn số này** — nhỏ hơn thì thanh công cụ
 * chui lên dưới dải kia, lớn hơn thì hở một khe cho thẻ trôi qua giữa hai dải.
 * Cả hai chỉ lộ ra khi cuộn, không lộ lúc dựng màn.
 *
 * Chỗ nhúng nào KHÔNG có dải điều khiển phía trên thì khai một hằng mới với
 * `max-md:top-0` — đừng mượn mốc này, nó sẽ chừa một khe 53px trống.
 */
export const PR_LINES_TOOLBAR_STICKY_UNDER_CONTROLS = `${STICKY_TOOLBAR_BASE} max-md:top-[53px]`

interface ReportPrLinesTabProps {
  year: string
  companyId?: string
  /**
   * Lớp GHIM cho thanh công cụ ở khổ điện thoại — truyền một trong hai hằng
   * `PR_LINES_TOOLBAR_STICKY_*` ở trên. Mốc `top` khác nhau tùy chỗ nhúng nên
   * component không tự chọn được.
   *
   * ⚠️ Bóng đổ đòi tổ tiên mang `group` + `data-scrolled`; thiếu thì dải vẫn
   * ghim, chỉ là không bao giờ đổ bóng — và lỗi đó im lặng.
   */
  toolbarStickyClassName?: string
}

/**
 * Báo cáo "Chi tiết YC mua hàng" theo DÒNG hàng (bao-CR-295/299) — dùng chung
 * cho tab trong Báo cáo mua hàng và trang riêng (bao-CR-296).
 *
 * Một YCMH 3 mã hàng / 3 NCC phải ra 3 ĐMH — báo cáo này để NSTM soi mã nào
 * chưa lên đơn, tránh đặt sót. Phân trang phía SERVER như tab Chi phí vận
 * chuyển: một năm vài nghìn dòng, tải hết về trình duyệt là treo trang.
 */
export function ReportPrLinesTab({
  year,
  companyId,
  toolbarStickyClassName,
}: ReportPrLinesTabProps) {
  const [status, setStatus] = useState(ALL)
  const [lineStatus, setLineStatus] = useState(ALL)
  const [assignee, setAssignee] = useState(ALL)
  //  Ô tìm kiếm chỉ áp khi Enter / rời ô (như bản v1): áp theo từng phím gõ là
  //  mỗi ký tự một lượt gọi API phân trang server. `searchDraft` là chữ đang gõ,
  //  `search` mới là giá trị đã áp vào bộ lọc.
  const [searchDraft, setSearchDraft] = useState('')
  const [search, setSearch] = useState('')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([
    status,
    lineStatus,
    assignee,
    search,
    year,
    companyId,
  ])

  const { data, isLoading, isError } = usePrLines(
    {
      year,
      company_id: companyId,
      status: status === ALL ? undefined : status,
      line_status: lineStatus === ALL ? undefined : lineStatus,
      assignee: assignee === ALL ? undefined : assignee,
      search: search || undefined,
      page,
      page_size: pageSize,
    },
    true,
  )

  const filtersActive = status !== ALL || lineStatus !== ALL || assignee !== ALL || search !== ''

  function commitSearch() {
    const trimmed = searchDraft.trim()
    if (trimmed !== search) setSearch(trimmed)
  }

  //  Ba ô lọc khai MỘT LẦN rồi dùng cho cả hai khổ màn — khổ rộng xếp thẳng
  //  hàng trên thanh công cụ, khổ hẹp nằm trong tờ trượt. Chép hai bản là hai
  //  khổ màn lọc ra hai kết quả khác nhau mà không chỗ nào báo.
  const lineStatusSelect = (
    <Select value={lineStatus} onValueChange={setLineStatus}>
      <SelectTrigger className="w-52 max-md:w-full">
        <SelectValue placeholder="Tiến độ" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả tiến độ</SelectItem>
        {LINE_STATUS_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-44 max-md:w-full">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
        {Object.entries(PR_STATUS_LABELS).map(([value, label]) => (
          <SelectItem key={value} value={value}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const assigneeSelect = (
    <Select value={assignee} onValueChange={setAssignee}>
      <SelectTrigger className="w-48 max-md:w-full">
        <SelectValue placeholder="NSTM" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả NSTM</SelectItem>
        {(data?.assignees ?? []).map((item) => (
          <SelectItem key={item.code} value={item.code}>
            {item.name ? `${item.name} (${item.code})` : item.code}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const columns = useMemo<DataTableColumn<PrLineRow>[]>(
    () => [
      { key: 'id', header: 'ID', width: 70, cell: (row) => row.id },
      {
        key: 'pr_code',
        header: 'Mã PYC',
        width: 130,
        hideable: false,
        // Bảng 18 cột: ghim mã phiếu để cuộn tới cột tiến độ vẫn biết dòng của phiếu nào.
        defaultPinned: true,
        cell: (row) => (
          <Link
            to={appRoutes.procurement.purchaseRequestDetail(row.pr_id)}
            className="font-medium text-primary hover:underline"
          >
            {row.pr_code || '—'}
          </Link>
        ),
      },
      {
        key: 'created_date',
        header: 'Ngày tạo',
        width: 110,
        cell: (row) => (
          <span className="whitespace-nowrap">{formatDate(row.created_date) || '—'}</span>
        ),
      },
      { key: 'requester', header: 'Người yêu cầu', width: 150, cell: (row) => row.requester || '—' },
      { key: 'department', header: 'Bộ phận', width: 140, cell: (row) => row.department || '—' },
      { key: 'product_code', header: 'Mã hàng', width: 120, cell: (row) => row.product_code || '—' },
      {
        key: 'product_name',
        header: 'Tên sản phẩm',
        width: 220,
        cell: (row) => (
          <span className="truncate" title={row.product_name}>
            {row.product_name || '—'}
          </span>
        ),
      },
      { key: 'warehouse', header: 'Kho nhận', width: 130, cell: (row) => row.warehouse || '—' },
      { key: 'item_group', header: 'Phân loại', width: 140, cell: (row) => row.item_group || '—' },
      { key: 'gram', header: 'Gram', width: 100, cell: (row) => row.gram || '—' },
      {
        key: 'qty',
        header: 'SL',
        width: 90,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatQuantity(row.qty)}</span>,
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 120,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatUnitPrice(row.price)}</span>,
      },
      {
        key: 'vat_pct',
        header: 'VAT',
        width: 80,
        align: 'right',
        cell: (row) =>
          row.vat_pct ? <span className="tabular-nums">{formatQuantity(row.vat_pct)}%</span> : '',
      },
      {
        key: 'amount',
        header: 'Thành tiền',
        width: 140,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatMoney(row.amount)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        cell: (row) => <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />,
      },
      {
        key: 'line_status',
        header: 'Tiến độ',
        width: 160,
        cell: (row) => <ProgressStatusBadge status={row.line_status} />,
      },
      {
        key: 'expected_date',
        header: 'Ngày dự kiến có hàng',
        width: 160,
        cell: (row) => (
          <span className="whitespace-nowrap">{formatDate(row.expected_date) || '—'}</span>
        ),
      },
      {
        key: 'assignee',
        header: 'NSTM phụ trách',
        width: 160,
        cell: (row) => row.assignee_name || row.assignee || '—',
      },
    ],
    [],
  )

  return (
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <h3 className="mb-3 text-sm font-semibold text-navy dark:text-foreground">
        Chi tiết Yêu cầu mua hàng theo dòng hàng{' '}
        <span className="font-normal text-muted-foreground">
          (soi mã hàng chưa được đặt để không đặt sót đơn)
        </span>
      </h3>
      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        getRowId={(row) => String(row.id)}
        isLoading={isLoading}
        isError={isError}
        emptyMessage={filtersActive ? 'Không có dòng khớp bộ lọc.' : 'Chưa có dữ liệu.'}
        //  Khổ hẹp: THẺ thay bảng — xem `PrLineCard`.
        mobileCard={(row) => <PrLineCard row={row} />}
        toolbarClassName={toolbarStickyClassName}
        storageKey="procurement.purchase-report.pr-lines"
        //  Bộ lọc của BẢNG này nằm ở state cục bộ chứ không lên URL. Năm / công
        //  ty là bộ lọc của cả trang (đầu trang hoặc trang riêng), không khai ở đây.
        filtersActive={filtersActive}
        onResetFilters={() => {
          setStatus(ALL)
          setLineStatus(ALL)
          setAssignee(ALL)
          setSearchDraft('')
          setSearch('')
        }}
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'dòng',
        }}
        toolbar={
          //  ⚠️ **Khổ điện thoại: ba ô lọc dọn vào TỜ TRƯỢT, thanh công cụ còn
          //  MỘT hàng** — cùng khuôn với Đơn nghỉ phép / Văn thư. Bản trước để
          //  chúng nằm thẳng trên thanh: bề rộng cứng (`w-52`/`w-44`/`w-48`)
          //  nên ô hẹp nhất cũng đã 176px trên 358px dùng được, xếp ra **ba
          //  hàng** (ô tìm trọn hàng, hai ô ghép đôi, ô lẻ + nút Tải lại) ≈
          //  124px chắn trên đầu danh sách — mà thanh này còn được GHIM, tức
          //  mỗi pixel là một pixel che mất thẻ. Gom vào tờ trượt: một hàng
          //  52px, và lúc mở ra mỗi ô có trọn bề ngang màn hình kèm nhãn.
          <>
            <Input
              className="w-52 max-md:min-w-0 max-md:flex-1"
              placeholder="Mã hàng / tên SP / mã PYC"
              value={searchDraft}
              onChange={(event) => setSearchDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') commitSearch()
              }}
              onBlur={commitSearch}
            />

            {/*  `QuickFilterSheet` tự mang `md:hidden`, còn khối bên dưới tự
                 mang `hidden md:flex` — hai vế loại trừ nhau nên không bao giờ
                 có hai bản ô chọn cùng lúc trong cây DOM. */}
            <QuickFilterSheet
              activeCount={
                (lineStatus !== ALL ? 1 : 0) + (status !== ALL ? 1 : 0) + (assignee !== ALL ? 1 : 0)
              }
              onClearAll={() => {
                setLineStatus(ALL)
                setStatus(ALL)
                setAssignee(ALL)
              }}
            >
              <QuickFilterField label="Tiến độ dòng hàng">{lineStatusSelect}</QuickFilterField>
              <QuickFilterField label="Trạng thái phiếu">{statusSelect}</QuickFilterField>
              <QuickFilterField label="NSTM phụ trách">{assigneeSelect}</QuickFilterField>
            </QuickFilterSheet>

            <div className="hidden items-center gap-3 md:flex md:flex-wrap">
              {lineStatusSelect}
              {statusSelect}
              {assigneeSelect}
            </div>
          </>
        }
      />
    </Card>
  )
}

/**
 * Một DÒNG HÀNG ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **18 cột**, bề rộng tự nhiên **2350px** trong khung 322px (đo
 * 12/09/2026 ở 390px): phần nhìn thấy được là *Mã PYC · ID · Ngày tạo* — ba cột
 * hành chính — còn **tên sản phẩm, số lượng, tiến độ** thì nằm ngoài mép phải.
 * Tức đúng ba thứ mà báo cáo này sinh ra để trả lời («mã nào chưa được đặt»)
 * lại là ba thứ không thấy.
 *
 * ⚠️ **TÊN SẢN PHẨM lên dòng đầu.** Đây là báo cáo theo DÒNG HÀNG, không phải
 * theo phiếu: một phiếu đẻ ra nhiều dòng nên cột *Mã PYC* in ra `PYCDEMO01`
 * hai ba lần liền nhau — dòng định danh mà không định danh được dòng nào.
 *
 * ⚠️ **Giữ đủ cặp huy hiệu *Trạng thái phiếu* + *Tiến độ dòng*.** Hai thứ khác
 * nhau và đều cần: phiếu «Đã duyệt» mà dòng «Chưa được đặt hàng» chính là ca
 * mà người dùng mở màn này ra để tìm. Bỏ một cái là mất luôn câu hỏi.
 *
 * Bảy cột còn lại (bộ phận · kho · phân loại · gram · VAT · người yêu cầu ·
 * NSTM) cố ý KHÔNG lên thẻ: nhồi đủ mười tám trường vào một thẻ thì thẻ dài
 * hơn cả màn hình, mà chúng là dữ liệu để đối chiếu khi ngồi máy tính — bên đó
 * bảng vẫn còn nguyên cả mười tám cột.
 */
function PrLineCard({ row }: { row: PrLineRow }) {
  return (
    <div className="space-y-1.5">
      <span className="block font-medium text-foreground">{row.product_name || '—'}</span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        {row.product_code && <span className="font-mono">{row.product_code}</span>}
        <Link
          to={appRoutes.procurement.purchaseRequestDetail(row.pr_id)}
          className="font-medium text-primary hover:underline"
        >
          <span aria-hidden="true">· </span>
          {row.pr_code || '—'}
        </Link>
        {row.created_date && (
          <span>
            <span aria-hidden="true">· </span>
            {formatDate(row.created_date)}
          </span>
        )}
      </span>

      {/*  ⚠️ **Hai huy hiệu phải có NHÃN đi kèm.** Ở bảng, tiêu đề cột nói cái
           nào là *Trạng thái* (của phiếu) và cái nào là *Tiến độ* (của dòng);
           trên thẻ thì không còn tiêu đề, mà hai huy hiệu hoàn toàn có thể in
           ra chữ y hệt nhau — «Hoàn thành» cạnh «Hoàn thành» — thành hai nhãn
           giống nhau không biết cái nào nói gì. Dùng đúng hai từ của tiêu đề
           cột để bảng và thẻ nói cùng một thứ tiếng. */}
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          Trạng thái
          <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />
        </span>
        <span className="inline-flex items-center gap-1">
          Tiến độ
          <ProgressStatusBadge status={row.line_status} />
        </span>
      </div>

      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
        <span>
          SL <b className="tabular-nums text-foreground">{formatQuantity(row.qty)}</b>
        </span>
        <span>
          Đơn giá <b className="tabular-nums text-foreground">{formatUnitPrice(row.price)}</b>
        </span>
        <span>
          Thành tiền <b className="tabular-nums text-foreground">{formatMoney(row.amount)} đ</b>
        </span>
        {/*  Ngày dự kiến chỉ hiện khi CÓ: dòng chưa được đặt thì chưa có mốc
             nào, in ra một dấu gạch ngang là thêm một thứ để mắt phải bỏ qua. */}
        {row.expected_date && (
          <span>
            Dự kiến{' '}
            <b className="tabular-nums text-foreground">{formatDate(row.expected_date)}</b>
          </span>
        )}
      </div>
    </div>
  )
}
