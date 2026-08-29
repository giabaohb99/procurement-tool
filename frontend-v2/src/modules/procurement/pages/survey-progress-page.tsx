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
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
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

const FILTER_CONFIG = {
  fields: SURVEY_PROGRESS_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['state', 'late', 'sort_by', 'sort_dir'],
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
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([queryKey, debouncedValue, progressState, late])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
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
        cell: (r) => (
          <Link
            to={`/procurement/survey-requests/${r.sr_id}`}
            className="truncate font-semibold text-primary hover:underline"
          >
            {r.code}
          </Link>
        ),
      },
      { key: 'company', header: 'Công ty', width: 180, sortable: true, cell: (r) => r.company || '' },
      { key: 'department', header: 'Bộ phận', width: 140, sortable: true, cell: (r) => r.department || '' },
      { key: 'requester', header: 'Người yêu cầu', width: 150, sortable: true, cell: (r) => r.requester || '' },
      { key: 'purpose', header: 'Mục đích', width: 190, defaultHidden: true, cell: (r) => r.purpose || '' },
      { key: 'request_date', header: 'Ngày YC', width: 100, defaultHidden: true, cell: (r) => formatDate(r.request_date) || '' },
      { key: 'status', header: 'TT phiếu', width: 110, cell: (r) => r.status || '' },
      { key: 'internal_line_code', header: 'Mã dòng', width: 120, defaultHidden: true, supplierOnly: true, cell: (r) => r.internal_line_code || '' },
      { key: 'item_group', header: 'Phân loại', width: 130, sortable: true, cell: (r) => r.item_group || '' },
      { key: 'requirement_detail', header: 'Thông số kỹ thuật', width: 240, cell: (r) => <span className="truncate" title={r.requirement_detail}>{r.requirement_detail || ''}</span> },
      { key: 'other_requirement', header: 'Yêu cầu khác', width: 180, defaultHidden: true, cell: (r) => <span className="truncate" title={r.other_requirement}>{r.other_requirement || ''}</span> },
      { key: 'request_qty', header: 'SL dự kiến', width: 100, align: 'right', cell: (r) => <span className="tabular-nums">{formatQuantity(r.request_qty) || 0}</span> },
      { key: 'uom', header: 'ĐVT', width: 70, cell: (r) => r.uom || '' },
      { key: 'proposed_price', header: 'Giá đề xuất', width: 110, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatUnitPrice(r.proposed_price) || 0}</span> },
      { key: 'assignee_name', header: 'NSTM phụ trách', width: 180, cell: (r) => r.assignee_name || '' },
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
      { key: 'line_status', header: 'TT dòng', width: 130, defaultHidden: true, cell: (r) => r.line_status || '' },
      { key: 'option_count', header: 'Số PA', width: 80, align: 'right', cell: (r) => r.option_count ?? 0 },
      { key: 'opt_label', header: 'Phương án chốt', width: 130, defaultHidden: true, cell: (r) => r.opt_label || '' },
      { key: 'opt_supplier_code', header: 'Mã NCC', width: 120, defaultHidden: true, supplierOnly: true, cell: (r) => r.opt_supplier_code || '' },
      { key: 'opt_supplier_name', header: 'Nhà cung cấp', width: 220, supplierOnly: true, cell: (r) => <span className="truncate" title={r.opt_supplier_name}>{r.opt_supplier_name || ''}</span> },
      { key: 'opt_internal_code', header: 'Mã SP theo NCC', width: 140, defaultHidden: true, supplierOnly: true, cell: (r) => r.opt_internal_code || '' },
      { key: 'opt_product_code', header: 'Mã SP hệ thống', width: 140, defaultHidden: true, cell: (r) => r.opt_product_code || '' },
      { key: 'opt_product_name', header: 'Tên SP báo giá', width: 220, cell: (r) => <span className="truncate font-medium" title={r.opt_product_name}>{r.opt_product_name || ''}</span> },
      { key: 'opt_spec', header: 'Quy cách', width: 190, defaultHidden: true, cell: (r) => <span className="truncate" title={r.opt_spec}>{r.opt_spec || ''}</span> },
      { key: 'opt_origin', header: 'Xuất xứ', width: 110, defaultHidden: true, cell: (r) => r.opt_origin || '' },
      { key: 'opt_quote_unit', header: 'ĐVT báo giá', width: 100, defaultHidden: true, cell: (r) => r.opt_quote_unit || '' },
      { key: 'opt_moq', header: 'SL tối thiểu', width: 100, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatQuantity(r.opt_moq) || 0}</span> },
      { key: 'opt_price', header: 'Đơn giá báo', width: 120, align: 'right', cell: (r) => <span className="font-semibold tabular-nums">{formatUnitPrice(r.opt_price) || 0}</span> },
      { key: 'opt_volume_range', header: 'Khoảng SL áp giá', width: 140, defaultHidden: true, cell: (r) => r.opt_volume_range || '' },
      { key: 'opt_vat', header: 'VAT%', width: 70, align: 'right', defaultHidden: true, cell: (r) => r.opt_vat ?? 0 },
      { key: 'opt_delivery_time', header: 'Thời gian giao', width: 130, defaultHidden: true, cell: (r) => r.opt_delivery_time || '' },
      { key: 'opt_delivery_place', header: 'Nơi giao', width: 160, defaultHidden: true, cell: (r) => r.opt_delivery_place || '' },
      { key: 'opt_shipping_cost', header: 'Phí vận chuyển', width: 120, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatMoney(r.opt_shipping_cost) || 0}</span> },
      { key: 'opt_sample_ready', header: 'Có mẫu', width: 80, defaultHidden: true, cell: (r) => (r.opt_sample_ready ? 'Có' : '') },
      { key: 'opt_lab_result', header: 'KQ kiểm nghiệm', width: 130, defaultHidden: true, cell: (r) => r.opt_lab_result || '' },
      { key: 'opt_note', header: 'Ghi chú NSTM', width: 190, defaultHidden: true, supplierOnly: true, cell: (r) => <span className="truncate" title={r.opt_note}>{r.opt_note || ''}</span> },
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

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
