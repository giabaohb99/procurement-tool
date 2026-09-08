import { Download, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { usePermission } from '@/core/authorization/use-permission'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlRangeParam } from '@/shared/hooks/use-url-range-param'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { downloadFile } from '@/core/api/download-file'
import { SURVEY_PROGRESS_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { useSurveyProgress } from '../hooks/use-purchase-documents'
import type { SurveyProgressItem } from '../types/survey-progress-types'

const ALL = 'all'

const PROGRESS_COLORS: Record<string, string> = {
  'Chưa tiếp nhận': '#94a3b8',
  'Đã tiếp nhận': '#64748b',
  'Đang khảo sát': '#d97706',
  'Đã trả kết quả': '#00AEEF',
  'Chốt rỗng': '#a855f7',
  'Đã chọn phương án': '#0d9488',
  'Cần khảo sát lại': '#dc2626',
  'Đã tạo YCMH': '#7c3aed',
  'Hoàn thành': '#16a34a',
}

function ProgressStateBadge({ state }: { state: string }) {
  if (!state) return null
  const color = PROGRESS_COLORS[state] || '#64748b'
  return (
    <span
      className="inline-block whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: `${color}22`, color }}
    >
      {state}
    </span>
  )
}

/**
 * Khoảng ngày lọc theo MỐC nào. Ba mốc của một dòng khảo sát lệch nhau cả tuần:
 * tiếp nhận đầu tháng, hạn trả giữa tháng, trả kết quả thật thì có khi sang
 * tháng sau — hỏi nhầm mốc là ra tập khác hẳn chứ không lệch vài dòng.
 *
 * Mặc định là NGÀY TIẾP NHẬN, trùng mốc mà bộ lọc `month` của backend vẫn dùng.
 * Cả ba cặp đều đã có sẵn ở `survey_progress/controller.py`.
 */
const DATE_FIELDS = [
  { value: 'received', label: 'Theo ngày tiếp nhận', from: 'received_date_from', to: 'received_date_to' },
  { value: 'result_due', label: 'Theo hạn trả KQ', from: 'result_due_date_from', to: 'result_due_date_to' },
  { value: 'result', label: 'Theo ngày trả KQ', from: 'result_date_from', to: 'result_date_to' },
] as const

const DEFAULT_DATE_FIELD = DATE_FIELDS[0].value

const FILTER_CONFIG = {
  fields: SURVEY_PROGRESS_FILTER_FIELDS,
  allowConjunctionToggle: true,
  //  Mọi ô lọc trên thanh công cụ. Thiếu tên nào ở đây là bấm "Áp dụng" bộ lọc
  //  nâng cao xong mất luôn ô đó.
  preserveParams: [
    'state',
    'late',
    'date_field',
    'date_from',
    'date_to',
    'sort_by',
    'sort_dir',
  ],
}

export function SurveyProgressPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyProgressContent />
    </FilterProvider>
  )
}

function SurveyProgressContent() {
  const { can } = usePermission()
  const canReadSupplier = can('supplier', 'read')
  const canExport = can('survey_request', 'export')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [progressState, setProgressState] = useUrlParamState('state', ALL)
  const [late, setLate] = useUrlParamState('late', ALL)
  const [dateField, setDateField] = useUrlParamState('date_field', DEFAULT_DATE_FIELD)
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    progressState,
    late,
    dateField,
    dateFrom,
    dateTo,
  ])

  //  Cặp tham số ngày đã đổi tên theo mốc đang chọn. Tách riêng vì bảng và nút
  //  Xuất Excel phải hỏi CÙNG một tập — xuất ra khác cái đang xem là lỗi ngầm.
  const dateParams: Record<string, string> = {}
  if (dateFrom || dateTo) {
    const field = DATE_FIELDS.find((item) => item.value === dateField) ?? DATE_FIELDS[0]
    if (dateFrom) dateParams[field.from] = dateFrom
    if (dateTo) dateParams[field.to] = dateTo
  }

  const params: ListParams = { page, page_size: pageSize, ...queryParams, ...dateParams }
  if (debouncedValue) params.q = debouncedValue
  if (progressState !== ALL) params.state = progressState
  if (late !== ALL) params.late = late

  const { data, isLoading, isError } = useSurveyProgress(params)
  const items = data?.items ?? []
  const showSupplier = data?.show_supplier ?? canReadSupplier

  const handleExportExcel = async () => {
    const query = new URLSearchParams()
    if (debouncedValue) query.set('q', debouncedValue)
    if (progressState !== ALL) query.set('state', progressState)
    if (late !== ALL) query.set('late', late)
    for (const [key, value] of Object.entries(dateParams)) query.set(key, value)
    const queryString = query.toString() ? `?${query.toString()}` : ''
    await downloadFile(`/api/survey-progress/export/xlsx${queryString}`, 'tien-do-bao-gia.xlsx')
  }

  const columns = useMemo<DataTableColumn<SurveyProgressItem>[]>(() => {
    const allCols: (DataTableColumn<SurveyProgressItem> & { supplierOnly?: boolean })[] = [
      {
        key: 'code',
        header: 'Mã YCBG',
        width: 150,
        sortable: true,
        defaultPinned: true,
        //  `wrap` cho cột chữ: khách cần ĐỌC ĐỦ, không phải đoán qua dấu "…"
        //  (khách nêu 31/08/2026). Cột số và cột ngày để nguyên một dòng, kẻo
        //  hàng cao lệch nhau nhìn rối. Lưu ý: gắn `truncate` trong `cell` là
        //  vô hiệu hóa `wrap` — class ô con thắng lớp bọc của bảng.
        wrap: true,
        cell: (r) => (
          <Link
            to={`/procurement/survey-requests/${r.sr_id}`}
            className="font-semibold text-primary hover:underline"
          >
            {r.code}
          </Link>
        ),
      },
      { key: 'company', header: 'Công ty', width: 180, sortable: true, wrap: true, cell: (r) => r.company || '' },
      { key: 'department', header: 'Bộ phận', width: 140, sortable: true, wrap: true, cell: (r) => r.department || '' },
      { key: 'requester', header: 'Người yêu cầu', width: 150, sortable: true, wrap: true, cell: (r) => r.requester || '' },
      { key: 'purpose', header: 'Mục đích', width: 190, defaultHidden: true, wrap: true, cell: (r) => r.purpose || '' },
      { key: 'request_date', header: 'Ngày YC', width: 100, defaultHidden: true, cell: (r) => formatDate(r.request_date) || '' },
      { key: 'status', header: 'TT phiếu', width: 110, wrap: true, cell: (r) => r.status || '' },
      { key: 'internal_line_code', header: 'Mã dòng', width: 120, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.internal_line_code || '' },
      { key: 'item_group', header: 'Phân loại', width: 130, sortable: true, wrap: true, cell: (r) => r.item_group || '' },
      { key: 'requirement_detail', header: 'Thông số kỹ thuật', width: 240, wrap: true, cell: (r) => r.requirement_detail || '' },
      { key: 'other_requirement', header: 'Yêu cầu khác', width: 180, defaultHidden: true, wrap: true, cell: (r) => r.other_requirement || '' },
      { key: 'request_qty', header: 'SL dự kiến', width: 100, align: 'right', cell: (r) => <span className="tabular-nums">{formatQuantity(r.request_qty) || 0}</span> },
      { key: 'uom', header: 'ĐVT', width: 70, cell: (r) => r.uom || '' },
      { key: 'proposed_price', header: 'Giá đề xuất', width: 110, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatUnitPrice(r.proposed_price) || 0}</span> },
      { key: 'assignee_name', header: 'NSTM phụ trách', width: 180, wrap: true, cell: (r) => r.assignee_name || '' },
      { key: 'received_date', header: 'Ngày tiếp nhận', width: 120, cell: (r) => formatDate(r.received_date) || '' },
      { key: 'result_due_date', header: 'Hạn trả KQ', width: 110, cell: (r) => formatDate(r.result_due_date) || '' },
      { key: 'result_date', header: 'Ngày trả KQ', width: 110, cell: (r) => formatDate(r.result_date) || '' },
      {
        key: 'days_late',
        header: 'Trễ (ngày)',
        width: 100,
        align: 'right',
        cell: (r) => (r.days_late && r.days_late > 0 ? <span className="font-semibold text-destructive">{r.days_late}</span> : ''),
      },
      { key: 'handling_days', header: 'Số ngày xử lý', width: 110, align: 'right', cell: (r) => r.handling_days ?? '' },
      { key: 'progress_state', header: 'Tiến độ dòng', width: 160, cell: (r) => <ProgressStateBadge state={r.progress_state} /> },
      { key: 'line_status', header: 'TT dòng', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.line_status || '' },
      { key: 'option_count', header: 'Số PA', width: 80, align: 'right', cell: (r) => r.option_count ?? 0 },
      { key: 'opt_label', header: 'Phương án chốt', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.opt_label || '' },
      { key: 'opt_supplier_code', header: 'Mã NCC', width: 120, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.opt_supplier_code || '' },
      { key: 'opt_supplier_name', header: 'Nhà cung cấp', width: 220, supplierOnly: true, wrap: true, cell: (r) => r.opt_supplier_name || '' },
      { key: 'opt_internal_code', header: 'Mã SP theo NCC', width: 140, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.opt_internal_code || '' },
      { key: 'opt_product_code', header: 'Mã SP hệ thống', width: 140, defaultHidden: true, wrap: true, cell: (r) => r.opt_product_code || '' },
      { key: 'opt_product_name', header: 'Tên SP báo giá', width: 220, wrap: true, cell: (r) => <span className="font-medium">{r.opt_product_name || ''}</span> },
      { key: 'opt_spec', header: 'Quy cách', width: 190, defaultHidden: true, wrap: true, cell: (r) => r.opt_spec || '' },
      { key: 'opt_origin', header: 'Xuất xứ', width: 110, defaultHidden: true, wrap: true, cell: (r) => r.opt_origin || '' },
      { key: 'opt_quote_unit', header: 'ĐVT báo giá', width: 100, defaultHidden: true, wrap: true, cell: (r) => r.opt_quote_unit || '' },
      { key: 'opt_moq', header: 'SL tối thiểu', width: 100, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatQuantity(r.opt_moq) || 0}</span> },
      { key: 'opt_price', header: 'Đơn giá báo', width: 120, align: 'right', cell: (r) => <span className="font-semibold tabular-nums">{formatUnitPrice(r.opt_price) || 0}</span> },
      { key: 'opt_volume_range', header: 'Khoảng SL áp giá', width: 140, defaultHidden: true, wrap: true, cell: (r) => r.opt_volume_range || '' },
      { key: 'opt_vat', header: 'VAT%', width: 70, align: 'right', defaultHidden: true, cell: (r) => r.opt_vat ?? 0 },
      { key: 'opt_delivery_time', header: 'Thời gian giao', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.opt_delivery_time || '' },
      { key: 'opt_delivery_place', header: 'Nơi giao', width: 160, defaultHidden: true, wrap: true, cell: (r) => r.opt_delivery_place || '' },
      { key: 'opt_shipping_cost', header: 'Phí vận chuyển', width: 120, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatMoney(r.opt_shipping_cost) || 0}</span> },
      { key: 'opt_sample_ready', header: 'Có mẫu', width: 80, defaultHidden: true, cell: (r) => (r.opt_sample_ready ? 'Có' : '') },
      { key: 'opt_lab_result', header: 'KQ kiểm nghiệm', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.opt_lab_result || '' },
      { key: 'opt_note', header: 'Ghi chú NSTM', width: 190, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.opt_note || '' },
    ]

    return allCols.filter((col) => !col.supplierOnly || showSupplier)
  }, [showSupplier])

  return (
    <PageContainer fill>
      <PageHeader
        title="Tiến độ báo giá"
        description="Theo dõi tiến độ xử lý từng dòng yêu cầu báo giá."
        actions={
          canExport ? (
            <Button variant="outline" size="sm" onClick={handleExportExcel}>
              <Download className="mr-1.5 size-4" />
              Xuất Excel
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={items}
          getRowId={(row) => `${row.sr_id}-${row.code}-${row.stt || 0}`}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy dữ liệu tiến độ báo giá."
          storageKey="procurement.survey-progress"
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
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm mã YCBG, SP, NCC, NSTM…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={progressState} onValueChange={setProgressState}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Tiến độ dòng" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả tiến độ</SelectItem>
                  {Object.keys(PROGRESS_COLORS).map((st) => (
                    <SelectItem key={st} value={st}>
                      {st}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={late} onValueChange={setLate}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Trễ hạn" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả</SelectItem>
                  <SelectItem value="1">Trễ hạn</SelectItem>
                  <SelectItem value="0">Đúng hạn</SelectItem>
                </SelectContent>
              </Select>

              {/*  Chọn MỐC trước, rồi tới khoảng ngày — đọc xuôi thành một câu
                   "theo hạn trả KQ, từ … tới …". Hai ô đứng liền nhau để không ai
                   lọc nhầm mốc mà không để ý. */}
              <Select value={dateField} onValueChange={setDateField}>
                <SelectTrigger className="w-48">
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

              <DateRangePicker
                from={dateFrom}
                to={dateTo}
                onChange={setDateRange}
                placeholder="Từ ngày – tới ngày"
              />

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
