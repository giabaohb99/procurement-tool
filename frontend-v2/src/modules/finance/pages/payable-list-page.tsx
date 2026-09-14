import { Download, FilePlus2, Scale } from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { downloadFile } from '@/core/api/download-file'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlRangeParam } from '@/shared/hooks/use-url-range-param'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import { PayableAgingBadge, PayableStatusBadge } from '../components/payable-badges'
import { PayableCard } from '../components/payable-card'
import { PayableOffsetPrepayDialog } from '../components/payable-offset-prepay-dialog'
import { PAYABLE_FILTER_FIELDS } from '../config/payable-filter-fields'
import { usePayableSummary, usePayables } from '../hooks/use-payables'
import {
  AGING_BUCKETS,
  PAYABLE_SOURCE_LABELS,
  PAYABLE_STATUS_OPTIONS,
  agingLabel,
  type Payable,
} from '../types/payable'

const ALL = 'all'

/** Năm hiện tại — mặc định của ô "Năm", trùng mặc định của backend khi không gửi param. */
const THIS_YEAR = new Date().getFullYear()

/**
 * Khoảng ngày lọc theo MỐC nào. Hai mốc lệch nhau thật sự: hàng nhận tháng 7 mà
 * công nợ 30 ngày thì hạn trả rơi sang tháng 8.
 *
 * Mặc định là HẠN TRẢ — câu hỏi khách nêu 31/08/2026 là "cần thanh toán từ ngày
 * tới ngày cho một NCC", tức là kỳ chi tiền, không phải kỳ nhận hàng.
 */
const DATE_FIELDS = [
  { value: 'due', label: 'Theo hạn trả', from: 'due_from', to: 'due_to' },
  { value: 'incur', label: 'Theo ngày phát sinh', from: 'incur_from', to: 'incur_to' },
  // bao-CR-306: ngày HĐ có thể lệch ngày phát sinh (nhận 3/9, hóa đơn xuất 7/9) —
  // kế toán đối chiếu theo kỳ hóa đơn cần mốc riêng. Khoản chưa có số HĐ bị loại.
  { value: 'invoice', label: 'Theo ngày hóa đơn', from: 'invoice_from', to: 'invoice_to' },
] as const

const DEFAULT_DATE_FIELD = DATE_FIELDS[0].value

/**
 * Khóa cột trên bảng -> khóa cột file Excel (`COLS` trong
 * `backend/app/modules/payable/export.py`, bao-CR-275). Từ bao-CR-305 file có đủ
 * BA cột ngày tách bạch (hóa đơn / phát sinh / ghi nhận) nên bảng dịch là 1-1 —
 * bản map cũ `incur_date -> created_at` là di tích thời file chỉ có một cột ngày,
 * giữ lại là xuất nhầm giờ ghi sổ dưới nhãn "Ngày phát sinh". Cột không có trong
 * bảng dịch (tick chọn, cấn trừ, tiền trước VAT / VAT) vốn không nằm trong file.
 */
const EXPORT_COLUMN_KEYS: Record<string, string> = {
  supplier_name: 'supplier_name',
  supplier_code: 'supplier_code',
  source_type: 'source_type',
  company: 'company',
  po_code: 'po_code',
  invoice_no: 'invoice_no',
  invoice_date: 'invoice_date',
  incur_date: 'incur_date',
  created_at: 'created_at',
  due_date: 'due_date',
  aging: 'aging',
  total: 'total',
  paid_amount: 'paid_amount',
  remaining: 'remaining',
  status: 'status',
}

const FILTER_CONFIG = {
  fields: PAYABLE_FILTER_FIELDS,
  allowConjunctionToggle: true,
  // Mọi ô lọc trên thanh công cụ. Thiếu tên nào ở đây là bấm "Áp dụng" bộ lọc
  // nâng cao xong mất luôn ô đó.
  preserveParams: [
    'company_id',
    'status',
    'aging',
    'year',
    'date_field',
    'date_from',
    'date_to',
  ],
}

export function PayableListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PayableListContent />
    </FilterProvider>
  )
}

/**
 * Công nợ phải trả — bảng CHỈ ĐỌC. Mỗi dòng do backend sinh ngầm lúc nhận hàng
 * (`payable/service.upsert`), không ai nhập tay được.
 *
 * Khác bản v1 một chỗ, có chủ ý: v1 tải hết 1000 dòng rồi tự cắt trang ở trình
 * duyệt; ở đây phân trang do server làm, nên năm nợ nhiều nghìn dòng không còn
 * treo màn. Nhờ vậy cột tick CHỌN được BẮC QUA TRANG — `selected` giữ cả bản
 * ghi (không chỉ id), tick trang 1 rồi sang trang 2 tick tiếp, bấm "Tạo đề nghị"
 * vẫn gom đủ. Đổi bộ lọc thì xóa lựa chọn để không ôm theo khoản của bộ lọc cũ
 * đã biến khỏi bảng; chỉ SANG TRANG thì giữ nguyên.
 */
function PayableListContent() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [aging, setAging] = useUrlParamState('aging', ALL)
  const [year, setYear] = useUrlParamState('year', String(THIS_YEAR))
  const [dateField, setDateField] = useUrlParamState('date_field', DEFAULT_DATE_FIELD)
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  /** Cột đang hiện trên bảng — nút "Xuất Excel" bám theo để file khớp màn hình. */
  const [visibleColumnKeys, setVisibleColumnKeys] = useState<string[]>([])

  // Khoản đang tick để lên đề nghị thanh toán. Giữ CẢ BẢN GHI (không chỉ id) để
  // đếm được số NCC và truyền thẳng sang màn tạo phiếu, khỏi phải tải lại theo id.
  const [selected, setSelected] = useState<Record<number, Payable>>({})

  // CR-268: khoản nợ đang mở hộp cấn trừ tiền treo trả trước (null = đóng).
  const [offsetTarget, setOffsetTarget] = useState<Payable | null>(null)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  //  Bộ lọc nâng cao: ở khổ rộng mở bằng nút riêng + popover, ở khổ hẹp nhúng
  //  thẳng phần ruột vào tờ trượt. Cần `apply`/`reset`/`activeCount` cho tờ
  //  trượt nên phải lấy context, không chỉ query.
  const filter = useFilterContext()

  //  Mốc bóng đổ cho thanh công cụ ghim ở khổ hẹp — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  //  Chữ ký của TOÀN BỘ phần lọc — dùng chung cho "về trang 1" và "bỏ hết tick".
  //  KHÔNG có `page` trong này, nên chỉ sang trang thì lựa chọn được giữ nguyên.
  const filterSignature = [
    queryKey,
    debouncedValue,
    companyId,
    status,
    aging,
    year,
    dateField,
    dateFrom,
    dateTo,
  ]

  const [page, setPage] = usePageResetOnFilterChange(filterSignature)

  const filterChanged = useHasChanged(JSON.stringify(filterSignature))
  if (filterChanged) setSelected({})

  const hasDateRange = Boolean(dateFrom || dateTo)

  // Tách riêng phần LỌC khỏi phần phân trang: bốn ô tổng phải tính trên cả tập
  // kết quả chứ không phải trên 20 dòng đang hiện.
  //
  //  ⚠️ Có khoảng ngày thì ép `year=all`. Backend mặc định lọc theo NĂM HIỆN TẠI
  //  khi không nhận `year`, nên khoảng vắt qua giao thừa (12/2025 – 01/2026) sẽ
  //  lặng lẽ trả về rỗng — người dùng tưởng kỳ đó không có nợ nào.
  const filterParams: ListParams = { ...queryParams, year: hasDateRange ? ALL : year }
  if (debouncedValue) filterParams.po_code = debouncedValue
  if (companyId !== ALL) filterParams.company_id = Number(companyId)
  if (status !== ALL) filterParams.status = status
  if (aging !== ALL) filterParams.aging = aging
  if (hasDateRange) {
    const field = DATE_FIELDS.find((f) => f.value === dateField) ?? DATE_FIELDS[0]
    if (dateFrom) filterParams[field.from] = dateFrom
    if (dateTo) filterParams[field.to] = dateTo
  }

  const { data, isLoading, isError } = usePayables({ page, page_size: pageSize, ...filterParams })
  const { data: summary, isLoading: isSummaryLoading } = usePayableSummary(filterParams)

  // useCallback để đưa được vào deps của `columns` mà không phá memo.
  const companyName = useCallback(
    (id: number) => (companies?.items ?? []).find((company) => company.id === id)?.name ?? '—',
    [companies],
  )

  const canCreatePayment = can('payment_request', 'create')

  // CR-268: nút cấn trừ tiền treo cần `payable.write` (endpoint) và
  // `payment_request.read` (hộp thoại phải đọc được danh sách phiếu treo).
  const canOffsetPrepay = can('payable', 'write') && can('payment_request', 'read')

  // Chỉ tick được khoản CHƯA tất toán, CÒN nợ và ĐÃ có số hóa đơn — đúng ba điều
  // kiện backend cần để lên đề nghị thanh toán.
  const isPayable = useCallback(
    (p: Payable) => p.status !== 'paid' && p.remaining > 0 && p.invoice_no.trim() !== '',
    [],
  )

  const toggleRow = useCallback((row: Payable) => {
    setSelected((prev) => {
      const next = { ...prev }
      if (next[row.id]) delete next[row.id]
      else next[row.id] = row
      return next
    })
  }, [])

  //  Ô tick "chọn hết" chỉ tính TRÊN TRANG ĐANG XEM — không thể tick hộ những
  //  khoản chưa tải về, mà tự đi tải cả nghìn dòng để tick hộ thì đúng cái bẫy
  //  bản v1 đã dính. Dòng thiếu số hóa đơn vẫn bị loại y như tick từng dòng.
  const selectableRows = useMemo(
    () => (data?.items ?? []).filter(isPayable),
    [data?.items, isPayable],
  )
  const selectedOnPage = selectableRows.filter((p) => selected[p.id]).length
  const allOnPageSelected = selectableRows.length > 0 && selectedOnPage === selectableRows.length

  const toggleAllOnPage = useCallback(() => {
    setSelected((prev) => {
      const next = { ...prev }
      // Đang chọn đủ cả trang -> bỏ đúng trang này, giữ nguyên tick ở trang khác.
      const clearing = selectableRows.length > 0 && selectableRows.every((p) => prev[p.id])
      for (const row of selectableRows) {
        if (clearing) delete next[row.id]
        else next[row.id] = row
      }
      return next
    })
  }, [selectableRows])

  const columns = useMemo<DataTableColumn<Payable>[]>(() => {
    //  `wrap: true` ở các cột CHỮ: khách báo 31/08/2026 tên NCC dài bị cắt thành
    //  "Công ty TNHH Thương mại…" nên phải rê chuột từng dòng mới đọc nổi, trong
    //  khi đây là sổ để đối chiếu. Cột số / ngày / trạng thái giữ nguyên một dòng
    //  vì chúng vốn ngắn, cho xuống dòng chỉ làm hàng cao lệch nhau.
    const base: DataTableColumn<Payable>[] = [
      {
        key: 'supplier_name',
        header: 'Nhà cung cấp',
        width: 240,
        hideable: false,
        // Bảng 15 cột: ghim tên NCC để cuộn tới cột tiền vẫn biết đang xem nợ ai.
        defaultPinned: true,
        wrap: true,
        //  KHÔNG đặt `truncate` ở đây: class của ô con thắng lớp bọc `wrap` của
        //  DataTable, gắn vào là cờ `wrap` thành vô hiệu.
        cell: (p) => (
          <span className="font-medium">{p.supplier_name || p.supplier_code || '—'}</span>
        ),
      },
      {
        key: 'supplier_code',
        header: 'Mã NCC',
        width: 130,
        wrap: true,
        cell: (p) => <span className="text-muted-foreground">{p.supplier_code || '—'}</span>,
      },
      {
        key: 'source_type',
        header: 'Loại nợ',
        width: 120,
        cell: (p) => PAYABLE_SOURCE_LABELS[p.source_type] ?? p.source_type,
      },
      {
        key: 'company',
        header: 'Công ty',
        width: 200,
        wrap: true,
        cell: (p) => companyName(p.company_id),
      },
      { key: 'po_code', header: 'Mã ĐMH', width: 150, wrap: true, cell: (p) => p.po_code || '—' },
      {
        key: 'invoice_no',
        header: 'Số hóa đơn',
        width: 150,
        wrap: true,
        // Chưa có số HĐ = chưa lên được yêu cầu thanh toán, nên phải nhìn ra ngay
        // chứ không để trống như một ô rỗng bình thường.
        cell: (p) =>
          p.invoice_no || <span className="text-xs text-destructive">chưa có HĐ</span>,
      },
      {
        key: 'invoice_date',
        header: 'Ngày hóa đơn',
        width: 130,
        // bao-CR-306: giá trị dò từ phía ĐMH lúc đọc (đợt giao -> dòng -> incur_date),
        // không có bản lưu bên công nợ — sửa ngày HĐ trên ĐMH là cột này đổi theo ngay.
        cell: (p) => formatDate(p.invoice_date) || '—',
      },
      {
        key: 'incur_date',
        header: 'Ngày phát sinh',
        width: 130,
        // v1 hiện `created_at` ở cột này. Dùng `incur_date` mới đúng nghĩa: đó là
        // ngày NHẬN HÀNG, còn `created_at` chỉ là lúc dòng nợ được ghi vào sổ —
        // hai mốc lệch nhau khi nhập bù chứng từ cũ. Giữ `created_at` ở cột ẩn
        // bên dưới cho ai cần đối chiếu.
        cell: (p) => formatDate(p.incur_date) || '—',
      },
      {
        key: 'created_at',
        header: 'Ngày ghi sổ',
        width: 160,
        defaultHidden: true,
        cell: (p) => formatDateTime(p.created_at) || '—',
      },
      { key: 'due_date', header: 'Hạn trả', width: 120, cell: (p) => formatDate(p.due_date) || '—' },
      {
        key: 'aging',
        header: 'Tuổi nợ',
        width: 140,
        cell: (p) => <PayableAgingBadge aging={p.aging} />,
      },
      {
        key: 'amount',
        header: 'Tiền trước VAT',
        width: 150,
        align: 'right',
        defaultHidden: true,
        cell: (p) => <span className="tabular-nums">{formatMoney(p.amount)}</span>,
      },
      {
        key: 'vat',
        header: 'VAT',
        width: 130,
        align: 'right',
        defaultHidden: true,
        cell: (p) => <span className="tabular-nums">{formatMoney(p.vat)}</span>,
      },
      {
        key: 'total',
        header: 'Tổng nợ',
        width: 150,
        align: 'right',
        cell: (p) => <span className="tabular-nums">{formatMoney(p.total)}</span>,
      },
      {
        key: 'paid_amount',
        header: 'Đã trả',
        width: 150,
        align: 'right',
        cell: (p) => <span className="tabular-nums">{formatMoney(p.paid_amount)}</span>,
      },
      {
        key: 'remaining',
        header: 'Còn lại',
        width: 150,
        align: 'right',
        cell: (p) => (
          <span className="font-semibold tabular-nums">{formatMoney(p.remaining)}</span>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 170,
        cell: (p) => <PayableStatusBadge status={p.status} />,
      },
    ]

    // CR-268: cột cấn trừ tiền treo — kế toán trừ tiền TRẢ TRƯỚC CẤP NCC (phiếu
    // không gắn đơn) vào khoản nợ. Chỉ hiện với người đủ quyền, chỉ bấm được khi
    // khoản còn nợ. Có treo hay không thì hộp thoại tự tra và tự nói.
    if (canOffsetPrepay) {
      base.push({
        key: 'offset_prepay',
        header: 'Cấn trừ',
        width: 90,
        align: 'center',
        cell: (p) =>
          p.status !== 'paid' && p.remaining > 0.01 ? (
            <span className="flex items-center justify-center" onClick={(e) => e.stopPropagation()}>
              <Button
                variant="ghost"
                size="icon"
                className="size-7"
                title="Cấn trừ tiền treo trả trước của NCC vào khoản nợ này"
                aria-label="Cấn trừ tiền treo trả trước"
                onClick={() => setOffsetTarget(p)}
              >
                <Scale className="size-4" />
              </Button>
            </span>
          ) : null,
      })
    }

    // Không có quyền lập đề nghị thanh toán thì bỏ hẳn cột tick — người chỉ được
    // xem công nợ không cần chỗ chọn.
    if (!canCreatePayment) return base

    // Cột tick — lối CHÍNH để lên đề nghị thanh toán (nút phụ là form trắng ở màn
    // YCTT). Luôn hiện, ghim trái để cuộn tới cột tiền vẫn tick được.
    const selectColumn: DataTableColumn<Payable> = {
      key: 'select',
      header: 'Chọn',
      width: 56,
      minWidth: 44,
      align: 'center',
      hideable: false,
      defaultPinned: true,
      headerContent: (
        <Checkbox
          checked={
            allOnPageSelected ? true : selectedOnPage > 0 ? 'indeterminate' : false
          }
          disabled={selectableRows.length === 0}
          aria-label={
            allOnPageSelected ? 'Bỏ chọn mọi khoản trong trang' : 'Chọn mọi khoản trong trang'
          }
          title="Chọn / bỏ chọn mọi khoản đủ điều kiện trong trang này"
          onCheckedChange={toggleAllOnPage}
        />
      ),
      cell: (p) => (
        <span
          className="flex items-center justify-center"
          // Ô tick nằm trên hàng bấm-được (mở ĐMH) — chặn nổi bọt kẻo tick lại mở đơn.
          onClick={(e) => e.stopPropagation()}
        >
          <Checkbox
            checked={!!selected[p.id]}
            disabled={!isPayable(p)}
            aria-label="Chọn khoản nợ này để lên đề nghị thanh toán"
            onCheckedChange={() => toggleRow(p)}
          />
        </span>
      ),
    }
    return [selectColumn, ...base]
  }, [
    companyName,
    canCreatePayment,
    canOffsetPrepay,
    selected,
    isPayable,
    toggleRow,
    allOnPageSelected,
    selectedOnPage,
    selectableRows.length,
    toggleAllOnPage,
  ])

  const selectedRows = useMemo(() => Object.values(selected), [selected])
  const selectedSupplierCount = useMemo(
    () => new Set(selectedRows.map((r) => r.supplier_code)).size,
    [selectedRows],
  )

  // KHÔNG tạo phiếu ngay tại đây (tránh đẻ phiếu nháp): đẩy các khoản đã tick
  // sang màn tạo, chỉ khi bấm "Tạo phiếu" ở đó mới ghi DB. Kèm cả `rows` qua
  // state để màn tạo khỏi tải lại theo id; thiếu state nó vẫn tự fetch theo
  // `?payables=`. Nhiều NCC thì backend tự tách thành nhiều phiếu.
  function createRequest() {
    if (!selectedRows.length) return
    const ids = selectedRows.map((r) => r.id).join(',')
    navigate(`${appRoutes.finance.paymentRequestNew}?payables=${ids}`, {
      state: { rows: selectedRows },
    })
  }

  // Ticket #16 (bao-CR-275): xuất Excel đúng những gì đang thấy — bộ lọc + phạm
  // vi + cột đang hiện; có tick chọn thì CHỈ xuất các khoản đã tick (backend nhận
  // `ids` và tự bỏ giới hạn năm cho các khoản đó).
  const canExport = can('payable', 'export')

  const handleExportExcel = async () => {
    const cols = visibleColumnKeys
      .map((key) => EXPORT_COLUMN_KEYS[key])
      .filter(Boolean)
      .join(',')
    const ids = selectedRows.map((r) => r.id).join(',')
    await downloadFile('/api/payables/export/xlsx', 'cong-no-phai-tra.xlsx', {
      ...filterParams,
      ...(ids ? { ids } : {}),
      ...(cols ? { cols } : {}),
    })
  }

  // Bấm dòng thì mở ĐƠN MUA HÀNG sinh ra khoản nợ đó — đường tra ngược duy nhất
  // từ sổ nợ về chứng từ gốc. Không có quyền đọc ĐMH thì bỏ hẳn, kẻo bấm xong
  // rơi vào màn báo thiếu quyền.
  const canOpenOrder = can('purchase_order', 'read')

  //  Cùng một ô chọn dựng HAI lần (hàng ngang ở khổ rộng · tờ trượt ở khổ hẹp).
  //  State nằm ở đây nên hai bản luôn nói cùng một giá trị — đây là khuôn của
  //  `payment-request-list-page`, không phải trùng lặp cần dọn.
  //
  //  `max-md:w-full`: trong tờ trượt mỗi ô có trọn bề ngang màn hình; giữ bề
  //  rộng cứng `w-48` thì ô nép trái và chừa một khoảng trống dài bên phải.
  const companySelect = (
    <Select value={companyId} onValueChange={setCompanyId}>
      <SelectTrigger className="w-48 max-md:w-full" aria-label="Lọc theo công ty">
        <SelectValue placeholder="Công ty" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả công ty</SelectItem>
        {(companies?.items ?? []).map((company) => (
          <SelectItem key={company.id} value={String(company.id)}>
            {company.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-48 max-md:w-full" aria-label="Lọc theo trạng thái">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
        {PAYABLE_STATUS_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const agingSelect = (
    <Select value={aging} onValueChange={setAging}>
      <SelectTrigger className="w-44 max-md:w-full" aria-label="Lọc theo tuổi nợ">
        <SelectValue placeholder="Tuổi nợ" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Mọi tuổi nợ</SelectItem>
        {AGING_BUCKETS.map((bucket) => (
          <SelectItem key={bucket} value={bucket}>
            {agingLabel(bucket)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  //  Chọn MỐC trước, rồi tới khoảng ngày — đọc xuôi thành một câu "theo hạn
  //  trả, từ … tới …". Hai ô đứng liền nhau để không ai lọc nhầm mốc mà không
  //  để ý; trong tờ trượt chúng cũng phải giữ đúng thứ tự đó.
  const dateFieldSelect = (
    <Select value={dateField} onValueChange={setDateField}>
      <SelectTrigger className="w-44 max-md:w-full" aria-label="Lọc theo mốc ngày">
        <SelectValue placeholder="Mốc ngày" />
      </SelectTrigger>
      <SelectContent>
        {DATE_FIELDS.map((field) => (
          <SelectItem key={field.value} value={field.value}>
            {field.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const dateRangeInput = (
    <DateRangePicker
      from={dateFrom}
      to={dateTo}
      onChange={setDateRange}
      placeholder="Từ ngày – tới ngày"
      className="max-md:w-full"
    />
  )

  const yearSelect = (
    <Select value={hasDateRange ? ALL : year} onValueChange={setYear}>
      <SelectTrigger
        className="w-36 max-md:w-full"
        aria-label="Lọc theo năm"
        //  Khóa ô Năm khi đang lọc theo khoảng ngày: khoảng ngày đã ép
        //  `year=all` rồi, để ô này bấm được thì người dùng chọn 2026 mà bảng
        //  vẫn ra cả 2025 — nhìn như bộ lọc hỏng.
        disabled={hasDateRange}
        title={
          hasDateRange
            ? 'Đang lọc theo khoảng ngày nên tính trên mọi năm. Xóa khoảng ngày để chọn lại năm.'
            : undefined
        }
      >
        <SelectValue placeholder="Năm" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả các năm</SelectItem>
        {[THIS_YEAR, THIS_YEAR - 1, THIS_YEAR - 2].map((item) => (
          <SelectItem key={item} value={String(item)}>
            {item}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  //  Huy hiệu trên nút «Bộ lọc» của khổ hẹp phải đếm CẢ HAI tầng — ô lọc nhanh
  //  và điều kiện nâng cao — vì cả hai nay nằm sau đúng một nút đó. Đếm thiếu
  //  một tầng thì người dùng thấy nút không dấu gì mà danh sách vẫn đang bị
  //  lọc, rồi đi tìm lỗi ở dữ liệu.
  const quickFilterCount =
    (companyId !== ALL ? 1 : 0) +
    (status !== ALL ? 1 : 0) +
    (aging !== ALL ? 1 : 0) +
    (hasDateRange ? 1 : 0) +
    (year !== String(THIS_YEAR) ? 1 : 0) +
    filter.activeCount

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Đây cũng là thứ khiến
    //  câu ghi chú cuối trang ĐÈ LÊN thanh lọc ở khổ 390px: khung `h-full` ép
    //  mọi thứ vào đúng một màn hình rồi tràn ra ngoài. Cùng luật
    //  `payment-request-list-page` và `CrudListPage`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Công nợ phải trả"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  hai dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem. Cùng luật đã áp cho `payment-request-list-page`.
          <span className="max-md:hidden">
            Khoản phải trả nhà cung cấp và đơn vị vận chuyển, sinh tự động khi nhận hàng.
          </span>
        }
        //  Nút trải hết hàng ở khổ hẹp — không có lớp này thì chúng co theo chữ
        //  và dán mép phải sau một khoảng trống dài.
        //
        //  ⚠️ Nhắm vào `[&>div]` chứ không `[&>button]`: cụm nút ở đây bọc
        //  thêm một lớp `div` (hai nút, có khoảng cách), nên bộ chọn con TRỰC
        //  TIẾP không chạm tới nút nào và lớp này im lặng không làm gì cả.
        actionsClassName="max-md:[&>div]:w-full"
        actions={
          canExport || canCreatePayment ? (
            <div className="flex items-center gap-2">
              {canExport && (
                <Button
                  variant="outline"
                  //  Khổ hẹp nó là nút DUY NHẤT còn lại (nút tạo đề nghị đã ẩn)
                  //  nên cho trải hết hàng, đừng để một nút lẻ nép mép phải.
                  className="max-md:flex-1"
                  onClick={handleExportExcel}
                  title={
                    selectedRows.length > 0
                      ? `Chỉ xuất ${selectedRows.length} khoản đang tick chọn`
                      : 'Xuất mọi khoản khớp bộ lọc đang đặt'
                  }
                >
                  <Download className="size-4" />
                  Xuất Excel
                  {selectedRows.length > 0 && ` (${selectedRows.length} khoản đã tick)`}
                </Button>
              )}
              {canCreatePayment && (
                //  ⚠️ ẨN ở khổ hẹp, không phải quên. Chế độ thẻ bỏ ô tick chọn
                //  (thẻ đã là một nút mở ĐMH, lồng nút vào nút là HTML sai) nên
                //  `selectedRows` ở đó VĨNH VIỄN rỗng — để lại thì đây là một
                //  nút mờ không bao giờ bấm được, mời người dùng đi tìm xem
                //  mình còn thiếu thao tác nào. Lên đề nghị thanh toán là việc
                //  của khổ rộng.
                <Button
                  className="max-md:hidden"
                  disabled={selectedRows.length === 0}
                  onClick={createRequest}
                >
                  <FilePlus2 className="size-4" />
                  Tạo đề nghị thanh toán
                  {selectedRows.length > 0 &&
                    ` (${selectedRows.length} khoản · ${selectedSupplierCount} NCC)`}
                </Button>
              )}
            </div>
          ) : undefined
        }
      />

      {/*  ⚠️ **Hai cột ngay từ khổ nhỏ nhất**, không phải một. Bản cũ để mặc
           định `grid-cols-1` dưới `sm`, nên trên máy 390px bốn ô xếp DỌC thành
           một dải ~460px — cộng tiêu đề và thanh lọc thì danh sách nợ, thứ duy
           nhất người ta mở màn này để xem, bắt đầu từ dưới mép màn hình. Bốn số
           này đều ngắn (đã `formatMoney` làm tròn tới đồng) nên 2×2 vừa thoải
           mái. */}
      <div className="mb-4 grid shrink-0 grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
        <SummaryCard label="Tổng nợ" value={summary?.total} loading={isSummaryLoading} />
        <SummaryCard
          label="Đã trả"
          value={summary?.paid}
          loading={isSummaryLoading}
          className="text-success"
        />
        <SummaryCard
          label="Còn phải trả"
          value={summary?.remaining}
          loading={isSummaryLoading}
          className="text-info"
        />
        <SummaryCard
          label="Quá hạn"
          value={summary?.overdue}
          loading={isSummaryLoading}
          className="text-destructive"
        />
      </div>

      {/*  `group` + `data-scrolled`: mốc để thanh công cụ ghim biết đã có nội
           dung trôi bên dưới chưa (bóng đổ). Thiếu thì dải vẫn ghim, chỉ là
           không bao giờ đổ bóng — và lỗi đó im lặng. */}
      <Card
        ref={stickyRef}
        className="group flex min-h-0 flex-1 flex-col p-4"
        data-scrolled={scrolled ? '' : undefined}
      >
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(p) => p.id}
          onRowClick={
            canOpenOrder
              ? (p) => {
                  if (p.po_id > 0) navigate(appRoutes.procurement.purchaseOrderDetail(p.po_id))
                }
              : undefined
          }
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không có khoản công nợ nào khớp bộ lọc."
          //  Khổ hẹp: THẺ thay bảng — xem `PayableCard`.
          mobileCard={(p) => <PayableCard row={p} />}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="finance.payables"
          onVisibleColumnsChange={setVisibleColumnKeys}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'khoản',
          }}
          toolbar={
            //  ⚠️ **Khổ điện thoại: sáu ô lọc dọn vào TỜ TRƯỢT**, thanh công cụ
            //  còn một hàng. Sáu ô khai bề rộng cứng (`w-48`…`w-36`) cộng ô
            //  khoảng ngày, nên ở 390px mỗi ô rơi xuống một hàng riêng: **bảy
            //  hàng ≈ 330px** chắn trên đầu danh sách, mà thanh này còn được
            //  GHIM — mỗi pixel là một pixel che mất thẻ. Gom lại: một hàng
            //  52px, mở tờ trượt ra thì mỗi ô có trọn bề ngang kèm nhãn.
            <>
              {/*  Câu gợi ý RÚT GỌN ở khổ hẹp: sau khi chia chỗ cho nút «Bộ
                   lọc» và nút Tải lại, ô chỉ còn ~150px nên bản đầy đủ bị trình
                   duyệt xén thành «Tìm theo mã ĐMH.» — mất đúng phần đuôi, thứ
                   người đọc chưa đoán được. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm theo mã ĐMH…"
                placeholderShort="Tìm mã ĐMH…"
                aria-label="Tìm khoản công nợ theo mã đơn mua hàng"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  `QuickFilterSheet` tự mang `md:hidden`, khối bên dưới tự mang
                   `hidden md:flex` — hai vế loại trừ nhau nên không bao giờ có
                   hai bản ô lọc cùng lúc trong cây DOM. */}
              <QuickFilterSheet
                activeCount={quickFilterCount}
                onClearAll={() => {
                  setCompanyId(ALL)
                  setStatus(ALL)
                  setAging(ALL)
                  setDateField(DEFAULT_DATE_FIELD)
                  setDateRange('', '')
                  //  Năm trả về NĂM HIỆN TẠI chứ không về `all`: đó là mặc định
                  //  của cả màn lẫn backend. Xóa lọc mà ra "tất cả các năm" là
                  //  đổi phạm vi rộng hơn lúc mới mở màn — người dùng bấm "xóa
                  //  lọc" xong thấy thêm dữ liệu thì đọc ra như lỗi.
                  setYear(String(THIS_YEAR))
                  filter.reset()
                }}
                onApply={filter.apply}
              >
                <QuickFilterField label="Công ty">{companySelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                <QuickFilterField label="Tuổi nợ">{agingSelect}</QuickFilterField>
                <QuickFilterField label="Mốc ngày">{dateFieldSelect}</QuickFilterField>
                <QuickFilterField label="Khoảng ngày">{dateRangeInput}</QuickFilterField>
                <QuickFilterField label="Năm">{yearSelect}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>

              {/*  ⚠️ `md:contents`, KHÔNG `md:flex`. Thanh công cụ của
                   `DataTable` vốn là một hàng `flex-wrap gap-3`; bọc bảy ô vào
                   một `div` thì cả cụm thành MỘT phần tử flex và xuống hàng
                   nguyên khối — đo ở 1440px ra **bốn hàng** thay vì hai, với
                   nhóm nút *Tải lại · Cột* bị đẩy hẳn xuống một hàng trống.
                   `display: contents` gỡ lớp bọc khỏi bố cục nên bảy ô trở lại
                   làm con trực tiếp và tự xuống hàng theo chỗ còn trống. */}
              <div className="max-md:hidden md:contents">
                {companySelect}
                {statusSelect}
                {agingSelect}
                {dateFieldSelect}
                {dateRangeInput}
                {yearSelect}
                <ConditionalFilter />
              </div>
            </>
          }
        />
      </Card>

      <p className="mt-2 shrink-0 text-xs text-muted-foreground">
        Chỉ khoản nợ <b>đã có Số hóa đơn</b> mới lên được đề nghị thanh toán. Nợ hàng hóa nhập số
        HĐ ở chi tiết sản phẩm trên đơn mua hàng; nợ vận chuyển tự lấy theo Mã MISA + Mã SP.
      </p>

      {selectedSupplierCount > 1 && (
        <p className="mt-1 shrink-0 text-xs text-info">
          Đang chọn {selectedSupplierCount} nhà cung cấp — hệ thống sẽ tách thành{' '}
          {selectedSupplierCount} phiếu đề nghị thanh toán riêng.
        </p>
      )}

      {canOffsetPrepay && (
        <PayableOffsetPrepayDialog payable={offsetTarget} onClose={() => setOffsetTarget(null)} />
      )}
    </PageContainer>
  )
}

/** Ô tổng tiền ở đầu trang. Chỉ để ĐỌC — khác `SummaryCard` bấm được của Báo cáo khảo sát. */
function SummaryCard({
  label,
  value,
  loading,
  className,
}: {
  label: string
  value: number | undefined
  loading: boolean
  className?: string
}) {
  return (
    //  Khổ hẹp bóp đệm và cỡ chữ lại: bốn ô này là phần ĐỨNG TRÊN danh sách,
    //  mỗi pixel của chúng là một pixel đẩy khoản nợ đầu tiên xuống dưới.
    <div className="rounded-lg border bg-card px-3 py-2 sm:px-4 sm:py-3">
      <p className="text-xs text-muted-foreground sm:text-sm">{label}</p>
      {loading ? (
        <Skeleton className="mt-1.5 h-6 w-24 sm:h-7 sm:w-32" />
      ) : (
        <p
          className={cn(
            //  `tabular-nums` để bốn ô xếp cạnh nhau có chữ số thẳng cột —
            //  thiếu nó thì 2×2 nhìn ra so le dù cùng cỡ chữ.
            'mt-0.5 text-base font-semibold tabular-nums text-navy sm:text-xl dark:text-foreground',
            className,
          )}
        >
          {formatMoney(value ?? 0)}
        </p>
      )}
    </div>
  )
}
