import { Download, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { CALL_STATUS } from '../config/ai-skill-constants'
import { CallStatusBadge } from '../config/ai-skill-meta'
import { useMcpCalls } from '../hooks/use-ai-usage'
import type { McpCall, McpCallFilters } from '../types/ai-skill'
import { readCallDocument } from '../utils/ai-row-mappers'
import { formatResultChars } from '../utils/call-log-format'
import { buildCsv, downloadCsv, type CsvColumn } from '../utils/csv-export'

const ALL = 'all'
const STATUS_OPTIONS = [
  { value: CALL_STATUS.ok, label: 'Thành công' },
  { value: CALL_STATUS.denied, label: 'Bị từ chối' },
  { value: CALL_STATUS.error, label: 'Lỗi' },
]

const CSV_COLUMNS: CsvColumn<McpCall>[] = [
  { header: 'Thời gian', value: (c) => c.created_at ?? '' },
  { header: 'Người', value: (c) => c.user_label },
  { header: 'Ứng dụng AI', value: (c) => c.client_name },
  { header: 'Lệnh', value: (c) => c.method },
  { header: 'Công cụ', value: (c) => c.tool },
  { header: 'Chứng từ', value: (c) => readCallDocument(c)?.code ?? '' },
  { header: 'Trạng thái', value: (c) => c.status_label },
  { header: 'Lý do từ chối', value: (c) => c.deny_reason },
  { header: 'Thời gian chạy (ms)', value: (c) => c.duration_ms },
  //  0 / thiếu = lượt không đo (không phải tools/call, dòng trước ai-CR-228) — để ô trống như trên màn, không ghi 0
  { header: 'Số ký tự kết quả', value: (c) => (c.result_chars && c.result_chars > 0 ? c.result_chars : '') },
  { header: 'Mã khóa', value: (c) => c.key_id },
  { header: 'IP', value: (c) => c.ip },
]

/**
 * G6 — nhật ký lượt gọi từ AI riêng của nhân sự vào ERP (doc 21 §6.2, K3 ai-CR-209). Máy chủ tự giới hạn: người
 * thường chỉ thấy lượt của chính mình; xem cả công ty cần quyền quản lý bot AI (`agent_group.read`, tạm thời — Agent 4
 * sẽ đổi sang khóa riêng). Xuất CSV lấy đúng TRANG ĐANG XEM, nói rõ trên nút.
 *
 * bao-CR-696: ô tìm nhanh theo người HOẶC công cụ (tham số `q`, khớp một phần — thay `tool` khớp đúng tên) và cột
 * Chứng từ — mã phiếu của lượt GHI thật, đọc qua `readCallDocument`; lượt nháp / đề xuất / chỉ đọc thì gạch ngang.
 */
export function CallLogPage() {
  const { can } = usePermission()
  const canViewAll = can('agent_group', 'read')
  const { value: keyword, setValue: setKeyword, debouncedValue: q } = useUrlSearchParam('q')
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [dateFrom, setDateFrom] = useUrlParamState('from', '')
  const [dateTo, setDateTo] = useUrlParamState('to', '')
  //  Mặc định chỉ lượt gọi CÔNG CỤ: lượt khởi tạo / liệt kê / thông báo của ứng dụng AI chiếm phần lớn trang mà không nói
  //  gì về việc tra cứu (Agent 2 soi dev 19/10). Bỏ tick để xem đủ.
  const [allMethods, setAllMethods] = useUrlParamState('all', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([q, status, dateFrom, dateTo, allMethods])

  const filters: McpCallFilters = {
    page,
    size: pageSize,
    q: q.trim() || undefined,
    status: status === ALL ? undefined : Number(status),
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    kind: allMethods ? undefined : 'tools',
  }
  const { data, isLoading, isError } = useMcpCalls(filters)
  const rows = data?.items

  const columns = useMemo<DataTableColumn<McpCall>[]>(
    () => [
      {
        key: 'created_at',
        header: 'Thời gian',
        width: 160,
        hideable: false,
        cell: (c) => <span className="whitespace-nowrap">{formatDateTime(c.created_at)}</span>,
      },
      //  Lượt khóa sai không có người (user_id = 0) — máy chủ mới trả "(khóa sai)", bản cũ trả rỗng thì in gạch.
      { key: 'user', header: 'Người', width: 180, cell: (c) => c.user_label || (c.user_id ? `#${c.user_id}` : '—') },
      { key: 'client', header: 'Ứng dụng AI', width: 160, cell: (c) => c.client_name || '—' },
      {
        key: 'tool',
        header: 'Công cụ',
        width: 200,
        cell: (c) => <span className="font-mono text-xs">{c.tool || c.method}</span>,
      },
      {
        key: 'document',
        header: 'Chứng từ',
        width: 140,
        cell: (c) => {
          const doc = readCallDocument(c)
          //  Gạch thật bằng <span>: DataTable nuốt ô trả đúng chuỗi '—' (docs/ui/table.md §1).
          if (!doc) return <span className="text-muted-foreground">—</span>
          if (!doc.href) return <span className="font-medium">{doc.code}</span>
          return (
            <Link to={doc.href} className="font-medium text-primary hover:underline">
              {doc.code}
            </Link>
          )
        },
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 240,
        wrap: true,
        cell: (c) => (
          <div className="flex flex-wrap items-center gap-1">
            <CallStatusBadge status={c.status} label={c.status_label} />
            {c.deny_reason && <span className="text-xs text-muted-foreground">{c.deny_reason}</span>}
          </div>
        ),
      },
      { key: 'duration', header: 'Chạy (ms)', width: 100, align: 'right', cell: (c) => c.duration_ms },
      //  ai-CR-228: kết quả quá dài thì ứng dụng AI có thể bỏ qua — cột này cho thấy lượt nào trả nhiều chữ.
      {
        key: 'result_chars',
        header: 'Số ký tự kết quả',
        width: 130,
        align: 'right',
        cell: (c) => formatResultChars(c.result_chars),
      },
      { key: 'key_id', header: 'Mã khóa', width: 90, defaultHidden: true, cell: (c) => c.key_id || '—' },
      { key: 'ip', header: 'IP', width: 130, defaultHidden: true, cell: (c) => <span className="font-mono text-xs">{c.ip || '—'}</span> },
    ],
    [],
  )

  function exportPage() {
    if (!rows?.length) return
    downloadCsv(`nhat-ky-ai-trang-${page}.csv`, buildCsv(rows, CSV_COLUMNS))
  }

  const filtering = q.trim() !== '' || status !== ALL || dateFrom !== '' || dateTo !== ''

  return (
    <PageContainer fill>
      <PageHeader
        title="Nhật ký sử dụng"
        description={
          canViewAll
            ? 'Mọi lượt AI riêng của nhân sự tra cứu ERP: ai, lúc nào, dùng công cụ gì, có bị từ chối không.'
            : 'Các lượt AI riêng của bạn đã tra cứu ERP.'
        }
        actions={
          <Button variant="outline" onClick={exportPage} disabled={!rows?.length}>
            <Download className="size-4" />
            Xuất CSV (trang hiện tại)
          </Button>
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={rows}
          getRowId={(c) => c.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            filtering
              ? 'Không có lượt nào khớp bộ lọc.'
              : allMethods
                ? 'Chưa có lượt gọi nào.'
                : 'Chưa có lượt gọi công cụ nào — bỏ tick "Chỉ lượt gọi công cụ" để xem cả lượt khởi tạo kết nối.'
          }
          storageKey="ai-skill.calls"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'lượt',
          }}
          toolbar={
            <>
              <div className="relative min-w-48 flex-1 md:max-w-xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm người hoặc công cụ"
                  aria-label="Tìm theo người hoặc công cụ"
                  value={keyword}
                  maxLength={80}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
              <DateRangePicker
                from={dateFrom}
                to={dateTo}
                onChange={(from, to) => {
                  setDateFrom(from)
                  setDateTo(to)
                }}
                placeholder="Mọi ngày"
                className="w-56"
              />
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-40" aria-label="Lọc trạng thái">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
                  {STATUS_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={String(o.value)}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex items-center gap-2">
                <Checkbox
                  id="ai-calls-tools-only"
                  checked={!allMethods}
                  onCheckedChange={(checked) => setAllMethods(checked === true ? '' : '1')}
                />
                <Label htmlFor="ai-calls-tools-only" className="text-sm font-normal">
                  Chỉ lượt gọi công cụ
                </Label>
              </div>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
