import { Download, Filter, Search, X } from 'lucide-react'
import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlRangeParam } from '@/shared/hooks/use-url-range-param'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import type { StatusTone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import {
  formatMoney,
  formatPercent,
  formatQuantity,
  formatUnitPrice,
} from '@/shared/utils/format-money'
import { purchaseDocumentApi } from '../api/purchase-document-api'
import { LineApproveBadge, StatusBadge } from '../components/document-status-badge'
import { useSurveyReport } from '../hooks/use-purchase-documents'
import { usePurchaseRequestItemGroups } from '../hooks/use-purchase-request-support'
import { SURVEY_STATUS_LABELS, SURVEY_TYPE_LABELS } from '../types/purchase-document'
import {
  LINE_APPROVE_STATUSES,
  type SurveyReportLine,
} from '../types/survey-report'

const ALL = 'all'

const KIND_LABELS: Record<string, string> = { supplier: 'NCC', product: 'SP' }

/**
 * MỘT cột của báo cáo. `text` là bắt buộc vì nó phục vụ CẢ HAI đường ra: nội dung
 * ô trên bảng (khi cột không cần trang trí) và ô trong tệp CSV.
 */
interface ReportField {
  key: string
  header: string
  width?: number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  wrap?: boolean
  hideable?: boolean
  defaultHidden?: boolean
  defaultPinned?: boolean
  /** Giá trị dạng CHỮ — dùng cho ô bảng lẫn ô CSV. Trống thì trả chuỗi rỗng. */
  text: (line: SurveyReportLine) => string
  /** Chỉ khai khi ô cần trang trí (liên kết, huy hiệu); tệp CSV vẫn lấy theo `text`. */
  cell?: (line: SurveyReportLine) => ReactNode
}

/**
 * TOÀN BỘ cột của báo cáo — một nguồn duy nhất cho cả bảng lẫn tệp CSV. Bản trước
 * khai hai chỗ tách rời (11 cột ở bảng, 11 tiêu đề chép tay ở hàm xuất) nên thêm
 * cột vào bảng mà quên tệp xuất chỉ là chuyện sớm muộn.
 *
 * Báo cáo trộn dòng NCC với dòng SP, mà hai loại gần như không dùng chung trường
 * nào: cột giá/MOQ/mẫu chỉ có ở dòng SP, cột MST/liên hệ/chính sách chỉ có ở dòng
 * NCC, nên bật hết cùng lúc là nửa bảng bỏ trắng. Vì vậy chỉ khoảng hai chục cột
 * hiện sẵn, phần còn lại để `defaultHidden` — ai cần thì bật trong menu **Cột**,
 * bảng nhớ lựa chọn đó theo `storageKey`.
 */
const REPORT_FIELDS: ReportField[] = [
  // ── Định danh phiếu ──
  {
    key: 'survey_code',
    header: 'Mã phiếu',
    width: 160,
    sortable: true,
    hideable: false,
    defaultPinned: true,
    //  Mọi dòng in mã phiếu GIỐNG HỆT nhau. Bản trước làm mờ dòng nối tiếp
    //  và gắn nhãn đếm "N dòng" để tách nhóm cùng mã phiếu, nhưng nhìn vào
    //  không đoán ra nghĩa nếu không có người giải thích — khách yêu cầu bỏ.
    text: (line) => line.survey_code,
    cell: (line) => (
      <Link
        to={`/procurement/surveys/${line.survey_id}`}
        className="truncate font-medium text-primary hover:underline"
      >
        {line.survey_code}
      </Link>
    ),
  },
  {
    key: 'kind',
    header: 'Loại',
    width: 90,
    sortable: true,
    text: (line) => KIND_LABELS[line.kind] ?? line.kind,
    cell: (line) => <Badge variant="outline">{KIND_LABELS[line.kind] ?? line.kind}</Badge>,
  },
  {
    key: 'survey_type',
    header: 'Loại phiếu',
    width: 170,
    sortable: true,
    defaultHidden: true,
    text: (line) => SURVEY_TYPE_LABELS[line.survey_type] ?? line.survey_type,
  },
  {
    key: 'survey_status',
    header: 'Trạng thái phiếu',
    width: 150,
    sortable: true,
    defaultHidden: true,
    text: (line) => SURVEY_STATUS_LABELS[line.survey_status] ?? line.survey_status,
    cell: (line) => <StatusBadge status={line.survey_status} labels={SURVEY_STATUS_LABELS} />,
  },
  { key: 'sr_code', header: 'Mã YCBG', width: 150, sortable: true, defaultHidden: true, text: (line) => line.sr_code },
  { key: 'pr_code', header: 'Mã PYC', width: 150, sortable: true, defaultHidden: true, text: (line) => line.pr_code },

  // ── Nội dung dòng & nhà cung cấp ──
  //  `wrap` cho cột chữ: khách cần ĐỌC ĐỦ chứ không phải đoán qua dấu "…"
  //  (cùng lý do CR-243). Cột ngày, cột số và cột huy hiệu để nguyên một dòng
  //  cho hàng khỏi cao lệch nhau. Lưu ý: gắn `truncate` trong `cell` là vô hiệu
  //  hóa `wrap` — class ô con thắng lớp bọc của bảng.
  { key: 'content', header: 'Nội dung dòng', width: 260, sortable: true, wrap: true, text: (line) => line.content },
  { key: 'supplier_code', header: 'Mã NCC', width: 130, sortable: true, wrap: true, text: (line) => line.supplier_code },
  { key: 'supplier_name', header: 'Tên NCC', width: 220, sortable: true, wrap: true, defaultHidden: true, text: (line) => line.supplier_name },
  { key: 'tax_code', header: 'Mã số thuế', width: 130, sortable: true, defaultHidden: true, text: (line) => line.tax_code },
  { key: 'contact_person', header: 'Người liên hệ', width: 160, wrap: true, defaultHidden: true, text: (line) => line.contact_person },
  { key: 'contact_phone', header: 'Điện thoại', width: 130, defaultHidden: true, text: (line) => line.contact_phone },
  { key: 'supply_group', header: 'Nhóm hàng cung cấp', width: 220, wrap: true, defaultHidden: true, text: (line) => line.supply_group },
  { key: 'source_of_information', header: 'Nguồn thông tin', width: 180, wrap: true, defaultHidden: true, text: (line) => line.source_of_information },
  { key: 'production_time', header: 'Thời gian sản xuất', width: 160, wrap: true, defaultHidden: true, text: (line) => line.production_time },
  { key: 'nvkd_eval', header: 'Đánh giá NVKD', width: 160, wrap: true, defaultHidden: true, text: (line) => line.nvkd_eval },
  { key: 'invoice_policy', header: 'Chính sách hóa đơn', width: 200, wrap: true, defaultHidden: true, text: (line) => line.invoice_policy },
  { key: 'reliability', header: 'Độ tin cậy', width: 180, wrap: true, defaultHidden: true, text: (line) => line.reliability },
  { key: 'delivery_policy', header: 'Chính sách giao hàng', width: 200, wrap: true, defaultHidden: true, text: (line) => line.delivery_policy },
  { key: 'defect_return', header: 'Đổi trả hàng lỗi', width: 200, wrap: true, defaultHidden: true, text: (line) => line.defect_return },

  // ── Hàng hóa ──
  { key: 'item_group', header: 'Nhóm hàng', width: 140, sortable: true, wrap: true, text: (line) => line.item_group },
  { key: 'item_code', header: 'Mã hàng', width: 130, sortable: true, text: (line) => line.item_code },
  { key: 'item_name', header: 'Tên VTBB', width: 220, sortable: true, wrap: true, text: (line) => line.item_name },
  { key: 'uom', header: 'ĐVT', width: 90, sortable: true, text: (line) => line.uom },
  { key: 'internal_code', header: 'Mã SP theo NCC', width: 150, sortable: true, defaultHidden: true, text: (line) => line.internal_code },
  { key: 'invoice_name', header: 'Tên trên hóa đơn', width: 220, wrap: true, defaultHidden: true, text: (line) => line.invoice_name },
  { key: 'spec', header: 'Quy cách', width: 220, wrap: true, defaultHidden: true, text: (line) => line.spec },
  { key: 'active_ingredient', header: 'Hàm lượng hoạt chất', width: 180, wrap: true, defaultHidden: true, text: (line) => line.active_ingredient },
  { key: 'origin', header: 'Xuất xứ', width: 130, sortable: true, defaultHidden: true, text: (line) => line.origin },
  { key: 'main_content', header: 'Nội dung chính', width: 240, sortable: true, wrap: true, defaultHidden: true, text: (line) => line.main_content },
  { key: 'requirement_detail', header: 'Yêu cầu kỹ thuật', width: 260, wrap: true, defaultHidden: true, text: (line) => line.requirement_detail },

  // ── Giá & số lượng ──
  { key: 'request_qty', header: 'SL dự kiến', width: 110, align: 'right', sortable: true, text: (line) => formatQuantity(line.request_qty) },
  { key: 'quote_unit', header: 'ĐVT báo giá', width: 110, defaultHidden: true, text: (line) => line.quote_unit },
  { key: 'moq', header: 'MOQ', width: 110, align: 'right', sortable: true, defaultHidden: true, text: (line) => formatQuantity(line.moq) },
  { key: 'price_by_volume', header: 'Đơn giá', width: 130, align: 'right', sortable: true, text: (line) => formatUnitPrice(line.price_by_volume) },
  { key: 'volume_range', header: 'Khoảng sản lượng', width: 160, wrap: true, defaultHidden: true, text: (line) => line.volume_range },
  { key: 'vat', header: 'VAT', width: 90, align: 'right', sortable: true, text: (line) => formatPercent(line.vat) },
  { key: 'amount', header: 'Thành tiền', width: 140, align: 'right', sortable: true, text: (line) => formatMoney(line.amount) },
  { key: 'last_purchase_price', header: 'Giá mua gần nhất', width: 150, align: 'right', sortable: true, defaultHidden: true, text: (line) => formatUnitPrice(line.last_purchase_price) },
  { key: 'max_purchase_price', header: 'Giá mua cao nhất', width: 150, align: 'right', sortable: true, defaultHidden: true, text: (line) => formatUnitPrice(line.max_purchase_price) },
  { key: 'proposed_rate', header: 'Giá đề xuất', width: 130, align: 'right', sortable: true, defaultHidden: true, text: (line) => formatUnitPrice(line.proposed_rate) },
  { key: 'shipping_cost', header: 'Phí vận chuyển', width: 140, align: 'right', sortable: true, defaultHidden: true, text: (line) => formatMoney(line.shipping_cost) },
  { key: 'extra_shipping_cost', header: 'Phí giao tận kho', width: 150, align: 'right', sortable: true, defaultHidden: true, text: (line) => formatMoney(line.extra_shipping_cost) },
  { key: 'shipping_policy', header: 'Chính sách vận chuyển', width: 200, wrap: true, defaultHidden: true, text: (line) => line.shipping_policy },

  // ── Giao hàng & công nợ ──
  { key: 'delivery_time', header: 'Thời gian giao', width: 150, wrap: true, text: (line) => line.delivery_time },
  { key: 'delivery_place', header: 'Nơi giao hàng', width: 180, wrap: true, defaultHidden: true, text: (line) => line.delivery_place },
  { key: 'debt_policy', header: 'Ngày công nợ', width: 130, sortable: true, text: (line) => line.debt_policy },

  // ── Mẫu & kiểm nghiệm ──
  { key: 'sample_ready', header: 'Có mẫu', width: 100, defaultHidden: true, text: (line) => line.sample_ready },
  { key: 'sample_date', header: 'Ngày nhận mẫu', width: 130, sortable: true, defaultHidden: true, text: (line) => formatDate(line.sample_date) },
  { key: 'sample_qty', header: 'SL mẫu', width: 110, align: 'right', defaultHidden: true, text: (line) => formatQuantity(line.sample_qty) },
  { key: 'lab_result', header: 'Kết quả kiểm nghiệm', width: 200, wrap: true, defaultHidden: true, text: (line) => line.lab_result },

  // ── Mốc thời gian ──
  { key: 'date', header: 'Ngày', width: 110, sortable: true, text: (line) => formatDate(line.date) },
  { key: 'contact_date', header: 'Ngày liên hệ', width: 130, sortable: true, defaultHidden: true, text: (line) => formatDate(line.contact_date) },
  { key: 'reply_date', header: 'Ngày phản hồi', width: 130, sortable: true, defaultHidden: true, text: (line) => formatDate(line.reply_date) },
  { key: 'result_date', header: 'Ngày trả KQ', width: 130, sortable: true, defaultHidden: true, text: (line) => formatDate(line.result_date) },
  { key: 'received_date', header: 'Ngày tiếp nhận', width: 130, sortable: true, defaultHidden: true, text: (line) => formatDate(line.received_date) },
  { key: 'result_due_date', header: 'Hạn trả KQ', width: 130, sortable: true, defaultHidden: true, text: (line) => formatDate(line.result_due_date) },

  // ── Phụ trách, duyệt & ghi chú ──
  { key: 'nspt', header: 'NSPT', width: 150, sortable: true, wrap: true, text: (line) => line.nspt },
  {
    key: 'line_approve',
    header: 'Kết quả duyệt',
    width: 140,
    sortable: true,
    text: (line) => line.line_approve,
    cell: (line) => <LineApproveBadge status={line.line_approve} />,
  },
  {
    key: 'line_approve_note',
    header: 'Ghi chú duyệt',
    width: 200,
    defaultHidden: true,
    wrap: true,
    text: (line) => line.line_approve_note,
    cell: (line) => <span className="text-muted-foreground">{line.line_approve_note || ''}</span>,
  },
  { key: 'nspt_note', header: 'Ghi chú NSPT', width: 200, wrap: true, defaultHidden: true, text: (line) => line.nspt_note },
  { key: 'note', header: 'Ghi chú', width: 200, wrap: true, defaultHidden: true, text: (line) => line.note },
]

/**
 * Khóa của một dòng. `line_id` chỉ duy nhất TRONG một bảng dòng, mà báo cáo trộn
 * dòng NCC với dòng sản phẩm nên phải kèm cả phiếu và loại.
 */
function rowKey(line: SurveyReportLine) {
  return `${line.survey_id}-${line.kind}-${line.line_id}`
}

/** Sắc thái của từng kết quả duyệt — cùng bảng màu với `LineApproveBadge`. */
const STATUS_TONE: Record<string, StatusTone> = {
  'Chờ duyệt': 'pending',
  'Đã duyệt': 'done',
  'Không duyệt': 'danger',
  'Thiếu thông tin': 'progress',
}

/**
 * Bốn ô lọc phụ nằm trong hộp **Bộ lọc**.
 *
 * Backend khớp CHỨA-CHUỖI, không phân biệt hoa thường (`survey/controller.py`
 * hàm `keep`), nên gõ một mẩu là đủ. Riêng `item_group` khớp CHÍNH XÁC nên
 * không nằm trong danh sách này — nó có ô chọn riêng.
 */
const TEXT_FILTERS = [
  { param: 'supplier', label: 'Mã / tên NCC', placeholder: 'Vd: Phương Nam, NCCKS004' },
  { param: 'item_code', label: 'Mã hàng', placeholder: 'Vd: XOT0009' },
  { param: 'nspt', label: 'NSPT', placeholder: 'Người sản xuất phụ trách' },
  { param: 'main_content', label: 'Nội dung chính', placeholder: 'Nội dung chính của phiếu' },
] as const

/** Tên mọi tham số lọc phụ — dùng chung cho lúc đọc, lúc ghi và lúc đếm. */
const EXTRA_PARAMS = ['item_group', ...TEXT_FILTERS.map((item) => item.param)] as const

type ExtraFilters = Record<(typeof EXTRA_PARAMS)[number], string>

const EMPTY_EXTRA: ExtraFilters = {
  item_group: '',
  supplier: '',
  item_code: '',
  nspt: '',
  main_content: '',
}

/**
 * Báo cáo khảo sát — cắt theo DÒNG khảo sát (mỗi NCC được hỏi giá / mỗi sản
 * phẩm là một dòng), không phải theo phiếu.
 *
 * Dải chip đầu bảng vừa là số đếm vừa là bộ lọc kết quả duyệt: backend tính bốn
 * con số TRƯỚC khi lọc trạng thái nên bấm qua lại vẫn thấy đủ. Trước đây chỗ
 * này là bốn thẻ to chiếm trọn một băng ngang mà không có dấu hiệu nào cho biết
 * bấm được, lại còn dành cho "Thiếu thông tin: 0" đúng bằng diện tích của "Đã
 * duyệt: 5.117".
 */
export function SurveyReportPage() {
  const { can } = usePermission()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [kind, setKind] = useUrlParamState('kind', ALL)
  const [lineApprove, setLineApprove] = useUrlParamState('line_approve', ALL)
  //  ⚠️ Tên tham số phải là `date_from` / `date_to`. Bản trước gửi
  //  `from_date` / `to_date`, mà FastAPI lặng lẽ bỏ qua tham số lạ — lọc theo
  //  ngày không chạy suốt từ đó tới giờ và không ai thấy báo lỗi gì.
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  //  Bảng vốn đã gắn `sortable` cho tám cột nhưng chưa ai nối dây: bấm tiêu đề
  //  chỉ thấy mũi tên đổi chiều, dữ liệu đứng yên. Backend nhận sẵn
  //  `sort_by` / `sort_dir` với danh sách cột cho phép đúng bằng cột ở đây.
  const [sortBy, sortDir, setSort] = useUrlRangeParam('sort_by', 'sort_dir')
  const [searchParams, setSearchParams] = useSearchParams()
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [exporting, setExporting] = useState(false)

  const extra = useMemo<ExtraFilters>(() => {
    const value = { ...EMPTY_EXTRA }
    for (const param of EXTRA_PARAMS) value[param] = searchParams.get(param) ?? ''
    return value
  }, [searchParams])

  /**
   * Ghi CẢ NĂM ô lọc phụ trong MỘT lệnh `setSearchParams`. Gọi năm lần liên tiếp
   * thì lệnh sau dựng lại từ `searchParams` của lần vẽ hiện tại và nuốt mất bốn
   * lệnh trước — đúng cái bẫy đã ghi ở `useUrlRangeParam`.
   */
  const applyExtra = useCallback(
    (next: ExtraFilters) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current)
          for (const param of EXTRA_PARAMS) {
            if (next[param]) params.set(param, next[param])
            else params.delete(param)
          }
          return params
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  const extraCount = EXTRA_PARAMS.filter((param) => extra[param]).length

  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    kind,
    lineApprove,
    dateFrom,
    dateTo,
    ...EXTRA_PARAMS.map((param) => extra[param]),
  ])

  //  Tách riêng phần tham số lọc: bảng và nút Xuất CSV phải hỏi CÙNG một tập,
  //  xuất ra khác cái đang xem là lỗi ngầm không ai đối chiếu nổi.
  const filterParams = useMemo(() => {
    const params: ListParams = {}
    if (debouncedValue) {
      params.code = debouncedValue
      params.q = debouncedValue
    }
    if (kind !== ALL) params.kind = kind
    if (lineApprove !== ALL) params.line_approve = lineApprove
    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    for (const param of EXTRA_PARAMS) {
      if (extra[param]) params[param] = extra[param]
    }
    return params
  }, [debouncedValue, kind, lineApprove, dateFrom, dateTo, extra])

  const { data, isLoading, isError } = useSurveyReport({
    ...filterParams,
    ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir || 'asc' } : {}),
    page,
    page_size: pageSize,
  })
  const summary = data?.summary
  const summaryTotal = summary
    ? LINE_APPROVE_STATUSES.reduce((sum, status) => sum + (summary[status] ?? 0), 0)
    : 0

  /**
   * Nhịp thứ ba của tiêu đề cột (tăng → giảm → THÔI SẮP XẾP) trả về khóa cột
   * RỖNG. Lúc đó phải xóa luôn cả chiều sắp xếp, kẻo đường dẫn còn dính
   * `?sort_dir=asc` chẳng thuộc cột nào.
   */
  const handleSortChange = useCallback(
    (nextSortBy: string, nextSortDir: 'asc' | 'desc') => {
      setSort(nextSortBy, nextSortBy ? nextSortDir : '')
    },
    [setSort],
  )

  const handleExportCsv = async () => {
    if (!data?.total) return
    setExporting(true)
    try {
      //  Hỏi lại backend TRỌN BỘ dòng khớp bộ lọc. Bản trước dựng CSV từ
      //  `data.items` — tức đúng một trang: bấm Xuất trên báo cáo 5.198 dòng thì
      //  ra tệp 20 dòng, không một lời cảnh báo.
      const full = await purchaseDocumentApi.listSurveyReportLines({
        ...filterParams,
        ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir || 'asc' } : {}),
        page: 1,
        page_size: data.total,
      })
      downloadCsv(full.items)
    } finally {
      setExporting(false)
    }
  }

  const columns = useMemo<DataTableColumn<SurveyReportLine>[]>(
    () => REPORT_FIELDS.map(({ text, cell, ...column }) => ({ ...column, cell: cell ?? text })),
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Báo cáo khảo sát"
        description="Tổng hợp tiến độ và kết quả duyệt từng dòng khảo sát nhà cung cấp & sản phẩm."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            disabled={exporting || !data?.total}
          >
            <Download className="mr-1.5 size-4" />
            {exporting ? 'Đang xuất…' : 'Xuất CSV'}
          </Button>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        {summary && (
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <StatusChip
              label="Tất cả"
              value={summaryTotal}
              active={lineApprove === ALL}
              onClick={() => setLineApprove(ALL)}
            />
            {LINE_APPROVE_STATUSES.map((status) => (
              <StatusChip
                key={status}
                label={status}
                value={summary[status] ?? 0}
                tone={STATUS_TONE[status]}
                active={lineApprove === status}
                onClick={() => setLineApprove(lineApprove === status ? ALL : status)}
              />
            ))}
          </div>
        )}

        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={rowKey}
          sortBy={sortBy || undefined}
          sortDir={sortDir === 'desc' ? 'desc' : 'asc'}
          onSortChange={handleSortChange}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy dòng khảo sát nào."
          storageKey="procurement.survey-report"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="h-9 pl-9 text-xs"
                  placeholder="Tìm mã phiếu, mã YCBG/PYC, mã SP, tên SP, mã NCC, MST…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={kind} onValueChange={setKind}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Loại dòng" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại</SelectItem>
                  <SelectItem value="supplier">Dòng nhà cung cấp</SelectItem>
                  <SelectItem value="product">Dòng sản phẩm</SelectItem>
                </SelectContent>
              </Select>

              <DateRangePicker
                from={dateFrom}
                to={dateTo}
                onChange={setDateRange}
                placeholder="Khoảng ngày khảo sát"
              />

              <ExtraFilterPopover
                value={extra}
                count={extraCount}
                canReadItemGroups={can('item_group', 'read')}
                onApply={applyExtra}
              />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}

/** Chip vừa hiện số đếm vừa lọc theo kết quả duyệt; bấm lần nữa để bỏ lọc. */
function StatusChip({
  label,
  value,
  tone,
  active,
  onClick,
}: {
  label: string
  value: number
  tone?: StatusTone
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors',
        'hover:border-primary/50 hover:bg-accent/40',
        active ? 'border-primary bg-accent font-medium' : 'border-border bg-card',
      )}
    >
      {tone && <span className={cn('size-2 rounded-full', TONE_DOT[tone])} />}
      <span className={cn(!active && 'text-muted-foreground')}>{label}</span>
      <span className="font-semibold tabular-nums">{value.toLocaleString('vi-VN')}</span>
    </button>
  )
}

/**
 * Chấm màu của chip. Lấy đúng nền của `TONE_CLASS` nhưng bỏ phần chữ — chấm
 * không có chữ nên chỉ cần một màu đục, không dùng nền `/10` mờ như huy hiệu.
 */
const TONE_DOT: Record<StatusTone, string> = {
  neutral: 'bg-muted-foreground',
  pending: 'bg-warning',
  progress: 'bg-info',
  done: 'bg-success',
  danger: 'bg-destructive',
}

/**
 * Hộp **Bộ lọc** cho năm ô lọc phụ mà backend đã nhận sẵn nhưng màn hình chưa
 * hề bày ra — trước đây muốn dùng phải tự gõ tham số vào thanh địa chỉ.
 *
 * Giữ bản nháp trong state rồi ghi một lượt lúc bấm **Áp dụng**: gõ tới đâu ghi
 * URL tới đó thì mỗi ký tự là một lượt gọi API cho một báo cáo phải quét cả
 * mấy nghìn dòng.
 */
function ExtraFilterPopover({
  value,
  count,
  canReadItemGroups,
  onApply,
}: {
  value: ExtraFilters
  count: number
  canReadItemGroups: boolean
  onApply: (next: ExtraFilters) => void
}) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState<ExtraFilters>(value)

  //  Danh mục nhóm hàng nằm ở endpoint có `require("item_group","read")` riêng.
  //  Thiếu quyền mà vẫn gọi là ăn một toast 403 ngay lúc mở hộp lọc, nên chỉ
  //  hỏi khi mở hộp VÀ có quyền.
  const { data: itemGroups } = usePurchaseRequestItemGroups(open && canReadItemGroups)

  const openChange = (next: boolean) => {
    //  Mở lại thì lấy bộ lọc đang chạy làm bản nháp — bấm ra ngoài rồi mở lại
    //  mà vẫn thấy chữ đã gõ dở nhưng bảng chưa lọc thì không ai hiểu chuyện gì.
    if (next) setDraft(value)
    setOpen(next)
  }

  const apply = (next: ExtraFilters) => {
    onApply(next)
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={openChange}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 gap-1.5">
          <Filter className="size-3.5" />
          Bộ lọc
          {count > 0 && (
            <Badge variant="default" className="h-4 rounded-full px-1.5 text-[10px]">
              {count}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 space-y-3">
        {canReadItemGroups && (
          <div className="space-y-1.5">
            <Label className="text-xs">Nhóm hàng</Label>
            <Select
              value={draft.item_group || ALL}
              onValueChange={(next) =>
                setDraft((current) => ({ ...current, item_group: next === ALL ? '' : next }))
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Tất cả nhóm hàng" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả nhóm hàng</SelectItem>
                {(itemGroups?.items ?? []).map((group) => (
                  <SelectItem key={group.id} value={group.name}>
                    {group.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {TEXT_FILTERS.map((item) => (
          <div key={item.param} className="space-y-1.5">
            <Label className="text-xs" htmlFor={`filter-${item.param}`}>
              {item.label}
            </Label>
            <Input
              id={`filter-${item.param}`}
              className="h-9 text-xs"
              placeholder={item.placeholder}
              value={draft[item.param]}
              onChange={(e) => setDraft((current) => ({ ...current, [item.param]: e.target.value }))}
              onKeyDown={(e) => {
                if (e.key === 'Enter') apply(draft)
              }}
            />
          </div>
        ))}

        <div className="flex justify-end gap-2 border-t pt-3">
          <Button variant="ghost" size="sm" onClick={() => apply(EMPTY_EXTRA)}>
            <X className="mr-1 size-3.5" />
            Xóa lọc
          </Button>
          <Button size="sm" onClick={() => apply(draft)}>
            Áp dụng
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}

/**
 * Dựng tệp CSV rồi tải xuống. Kèm BOM để Excel đọc đúng tiếng Việt.
 *
 * Xuất **TOÀN BỘ** cột trong `REPORT_FIELDS`, kể cả cột đang ẩn trên bảng: người
 * xuất tệp là để mang đi đối chiếu chỗ khác, không phải để chụp lại đúng cái
 * đang nhìn. Bù lại, đây cũng là lý do danh sách cột phải khai một chỗ.
 */
function downloadCsv(rows: SurveyReportLine[]) {
  const quote = (text: string) => `"${(text || '').replace(/"/g, '""')}"`

  const csvContent = [
    REPORT_FIELDS.map((field) => quote(field.header)).join(','),
    ...rows.map((row) => REPORT_FIELDS.map((field) => quote(field.text(row))).join(',')),
  ].join('\n')

  const blob = new Blob(['﻿' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `Bao_cao_khao_sat_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
