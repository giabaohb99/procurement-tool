import { Download, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
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
import { cn } from '@/shared/utils/cn'
import { LineApproveBadge } from '../components/document-status-badge'
import { useSurveyReport } from '../hooks/use-purchase-documents'
import {
  LINE_APPROVE_STATUSES,
  type SurveyReportLine,
} from '../types/survey-report'

const ALL = 'all'

const KIND_LABELS: Record<string, string> = { supplier: 'NCC', product: 'SP' }

/**
 * Báo cáo khảo sát — cắt theo DÒNG khảo sát (mỗi NCC được hỏi giá / mỗi sản
 * phẩm là một dòng), không phải theo phiếu.
 *
 * Bốn ô đếm ở đầu trang bấm được để lọc nhanh theo kết quả duyệt; backend tính
 * số đếm TRƯỚC khi lọc trạng thái nên bấm qua lại vẫn thấy đủ bốn con số.
 */
export function SurveyReportPage() {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [kind, setKind] = useUrlParamState('kind', ALL)
  const [lineApprove, setLineApprove] = useUrlParamState('line_approve', ALL)
  const [fromDate] = useUrlParamState('from_date', '')
  const [toDate] = useUrlParamState('to_date', '')
  const [itemGroup] = useUrlParamState('item_group', '')
  const [supplierCode] = useUrlParamState('supplier', '')
  const [nspt] = useUrlParamState('nspt', '')
  const [itemCode] = useUrlParamState('item_code', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    kind,
    lineApprove,
    fromDate,
    toDate,
    itemGroup,
    supplierCode,
    nspt,
    itemCode,
  ])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedValue) {
    params.code = debouncedValue
    params.q = debouncedValue
  }
  if (kind !== ALL) params.kind = kind
  if (lineApprove !== ALL) params.line_approve = lineApprove
  if (fromDate) params.from_date = fromDate
  if (toDate) params.to_date = toDate
  if (itemGroup) params.item_group = itemGroup
  if (supplierCode) params.supplier = supplierCode
  if (nspt) params.nspt = nspt
  if (itemCode) params.item_code = itemCode

  const { data, isLoading, isError } = useSurveyReport(params)
  const summary = data?.summary

  const handleExportCsv = () => {
    const rows = data?.items ?? []
    if (!rows.length) return

    const headers = [
      'Mã phiếu',
      'Loại',
      'Nội dung dòng',
      'Mã NCC',
      'Nhóm hàng',
      'Mã hàng',
      'Nội dung chính',
      'NSPT',
      'Ngày',
      'Kết quả duyệt',
      'Ghi chú duyệt',
    ]

    const csvContent = [
      headers.join(','),
      ...rows.map((row) =>
        [
          `"${row.survey_code || ''}"`,
          `"${KIND_LABELS[row.kind] || row.kind || ''}"`,
          `"${(row.content || '').replace(/"/g, '""')}"`,
          `"${row.supplier_code || ''}"`,
          `"${row.item_group || ''}"`,
          `"${row.item_code || ''}"`,
          `"${(row.main_content || '').replace(/"/g, '""')}"`,
          `"${row.nspt || ''}"`,
          `"${formatDate(row.date) || ''}"`,
          `"${row.line_approve || ''}"`,
          `"${(row.line_approve_note || '').replace(/"/g, '""')}"`,
        ].join(','),
      ),
    ].join('\n')

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `Bao_cao_khao_sat_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const columns = useMemo<DataTableColumn<SurveyReportLine>[]>(
    () => [
      {
        key: 'survey_code',
        header: 'Mã phiếu',
        width: 150,
        sortable: true,
        hideable: false,
        defaultPinned: true,
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
        cell: (line) => <Badge variant="outline">{KIND_LABELS[line.kind] ?? line.kind}</Badge>,
      },
      {
        key: 'content',
        header: 'Nội dung dòng',
        width: 260,
        cell: (line) => (
          <span className="truncate" title={line.content}>
            {line.content || ''}
          </span>
        ),
      },
      {
        key: 'supplier_code',
        header: 'Mã NCC',
        width: 150,
        sortable: true,
        cell: (line) => line.supplier_code || '',
      },
      { key: 'item_group', header: 'Nhóm hàng', width: 160, sortable: true, cell: (line) => line.item_group || '' },
      { key: 'item_code', header: 'Mã hàng', width: 140, sortable: true, cell: (line) => line.item_code || '' },
      {
        key: 'main_content',
        header: 'Nội dung chính',
        width: 240,
        defaultHidden: true,
        cell: (line) => (
          <span className="truncate" title={line.main_content}>
            {line.main_content || ''}
          </span>
        ),
      },
      { key: 'nspt', header: 'NSPT', width: 150, sortable: true, cell: (line) => line.nspt || '' },
      { key: 'date', header: 'Ngày', width: 110, sortable: true, cell: (line) => formatDate(line.date) || '' },
      {
        key: 'line_approve',
        header: 'Kết quả duyệt',
        width: 140,
        sortable: true,
        cell: (line) => <LineApproveBadge status={line.line_approve} />,
      },
      {
        key: 'line_approve_note',
        header: 'Ghi chú duyệt',
        width: 200,
        defaultHidden: true,
        cell: (line) => (
          <span className="truncate text-muted-foreground" title={line.line_approve_note}>
            {line.line_approve_note || ''}
          </span>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Báo cáo khảo sát"
        description="Tổng hợp tiến độ và kết quả duyệt từng dòng khảo sát nhà cung cấp & sản phẩm."
        actions={
          <Button variant="outline" size="sm" onClick={handleExportCsv}>
            <Download className="mr-1.5 size-4" />
            Xuất CSV
          </Button>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        {summary && (
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <SummaryCard
              label="Chờ duyệt"
              value={summary['Chờ duyệt']}
              active={lineApprove === 'Chờ duyệt'}
              onClick={() => setLineApprove(lineApprove === 'Chờ duyệt' ? ALL : 'Chờ duyệt')}
            />
            <SummaryCard
              label="Đã duyệt"
              value={summary['Đã duyệt']}
              active={lineApprove === 'Đã duyệt'}
              onClick={() => setLineApprove(lineApprove === 'Đã duyệt' ? ALL : 'Đã duyệt')}
            />
            <SummaryCard
              label="Không duyệt"
              value={summary['Không duyệt']}
              active={lineApprove === 'Không duyệt'}
              onClick={() => setLineApprove(lineApprove === 'Không duyệt' ? ALL : 'Không duyệt')}
            />
            <SummaryCard
              label="Thiếu thông tin"
              value={summary['Thiếu thông tin']}
              active={lineApprove === 'Thiếu thông tin'}
              onClick={() =>
                setLineApprove(lineApprove === 'Thiếu thông tin' ? ALL : 'Thiếu thông tin')
              }
            />
          </div>
        )}

        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(line) => `${line.survey_id}-${line.kind}-${line.line_id}`}
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
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm mã phiếu, mã SP, tên SP, mã NCC, NSPT…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={kind} onValueChange={setKind}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Loại dòng" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại</SelectItem>
                  <SelectItem value="supplier">Dòng nhà cung cấp</SelectItem>
                  <SelectItem value="product">Dòng sản phẩm</SelectItem>
                </SelectContent>
              </Select>

              <Select value={lineApprove} onValueChange={setLineApprove}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Kết quả duyệt" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả kết quả</SelectItem>
                  {LINE_APPROVE_STATUSES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}

/** Ô đếm bấm được: bấm lần nữa để bỏ lọc. */
function SummaryCard({
  label,
  value,
  active,
  onClick,
}: {
  label: string
  value: number
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'rounded-lg border bg-card px-4 py-3 text-left transition-colors hover:border-primary/50 hover:bg-accent/40',
        active && 'border-primary/60 bg-accent',
      )}
    >
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-2xl font-semibold text-navy dark:text-foreground">
        {value.toLocaleString('vi-VN')}
      </p>
    </button>
  )
}
