import { ChevronDown, ChevronUp, RotateCw } from 'lucide-react'
import { useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { Switch } from '@/shared/ui/switch'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import {
  ACTION_GROUP_LABEL,
  LOG_SOURCE_LABEL,
  LOG_STATUS,
  type LogStatus,
  type SystemLogFilters,
  type SystemLogItem,
} from '../api/system-log-api'
import { SystemLogDetailSheet } from '../components/system-log-detail-sheet'
import { SystemLogSummaryCharts } from '../components/system-log-summary-charts'
import { useSystemLogs, useSystemLogSummary } from '../hooks/use-system-logs'
import {
  changeSummaryText,
  defaultLogRange,
  formatDuration,
  httpStatusHint,
  httpStatusTone,
} from '../utils/system-log-format'

/**
 * NHẬT KÝ HỆ THỐNG — `/system/logs` (bao-CR-407, CR-312 P5).
 *
 * Một dòng = MỘT LƯỢT GỌI, gộp cả ba bảng nhật ký theo `request_id`. Khác màn
 * *Nhật ký nghiệp vụ* (`/system/audit-logs`) ở chỗ màn này lấy `tab_request_log`
 * làm xương sống, nên nó bày cả những lượt **không đẻ ra dấu vết nghiệp vụ nào**
 * — một `DELETE` ăn 403, một lượt 500 chết trước khi vào service. Đó đúng là hai
 * dòng cần nhìn nhất lúc đi truy sự cố.
 *
 * ⚠️ Dòng audit ghi TRƯỚC P1 (chưa có `request_id`) không lên màn này. Không
 * phải mất — chúng vẫn đọc được ở dòng thời gian của từng phiếu.
 */
export function SystemLogListPage() {
  const initialRange = useMemo(() => defaultLogRange(), [])

  const [from, setFrom] = useState(initialRange.from)
  const [to, setTo] = useState(initialRange.to)
  const [status, setStatus] = useState<LogStatus>(LOG_STATUS.ALL)
  const [actionGroup, setActionGroup] = useState('')
  const [source, setSource] = useState('')
  const [docCode, setDocCode] = useState('')
  const [route, setRoute] = useState('')
  const [ip, setIp] = useState('')
  const [table, setTable] = useState('')
  const [field, setField] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  //  Biểu đồ MẶC ĐỊNH ẨN. Người mở màn này gần như luôn đang đi tra một lượt gọi
  //  cụ thể, không phải đi xem hình dáng cả ngày — mà ba biểu đồ kia là ba câu
  //  `GROUP BY` trên bảng lớn nhất của cả hệ, trả tiền ngay ở lượt tải đầu cho
  //  thứ chưa ai hỏi. `enabled: showCharts` của `useSystemLogSummary` lo phần
  //  còn lại: ẩn thì không có truy vấn nào chạy.
  const [showCharts, setShowCharts] = useState(false)
  const [follow, setFollow] = useState(false)

  //  Ô gõ chữ phải hoãn: mỗi ký tự một lượt `GET /api/system-logs` là bốn năm
  //  truy vấn `GROUP BY` chồng nhau trên bảng lớn nhất của cả hệ.
  const docCodeQuery = useDebouncedValue(docCode)
  const routeQuery = useDebouncedValue(route)
  const ipQuery = useDebouncedValue(ip)
  const tableQuery = useDebouncedValue(table)
  const fieldQuery = useDebouncedValue(field)

  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([
    from,
    to,
    status,
    actionGroup,
    source,
    docCodeQuery,
    routeQuery,
    ipQuery,
    tableQuery,
    fieldQuery,
  ])

  //  `request_id` sống trên URL chứ không trong state: nút *Xem chi tiết* của
  //  dòng thời gian từng phiếu đi thẳng tới `/system/logs?request_id=…`, và một
  //  người đang truy sự cố phải gửi được đúng lượt gọi đó cho đồng nghiệp.
  const [openedRequestId, setOpenedRequestId] = useUrlParamState('request_id', '')

  const filters: SystemLogFilters = {
    from_time: from || undefined,
    to_time: to || undefined,
    status,
    action_group: actionGroup ? Number(actionGroup) : undefined,
    source: source ? Number(source) : undefined,
    doc_code: docCodeQuery || undefined,
    route: routeQuery || undefined,
    ip: ipQuery || undefined,
    table: tableQuery || undefined,
    field: fieldQuery || undefined,
  }

  const { data, isLoading, isError, refetch } = useSystemLogs(
    { ...filters, page, page_size: pageSize },
    { follow },
  )
  const summary = useSystemLogSummary(filters, { enabled: showCharts, follow })

  const hasFilter =
    status !== LOG_STATUS.ALL ||
    Boolean(actionGroup || source || docCodeQuery || routeQuery || ipQuery || tableQuery || fieldQuery)

  const columns: DataTableColumn<SystemLogItem>[] = [
    {
      key: 'at',
      header: 'Lúc',
      width: 150,
      cell: (r) => <span className="tabular-nums">{formatDateTime(r.at) || '—'}</span>,
    },
    {
      key: 'user_name',
      header: 'Ai',
      width: 170,
      cell: (r) => <span className="truncate">{r.user_name || '—'}</span>,
    },
    {
      key: 'summary',
      header: 'Lần bấm',
      width: 320,
      cell: (r) => (
        <div className="min-w-0">
          <p className="truncate" title={r.summary}>
            {r.summary || '—'}
          </p>
          <p className="truncate font-mono text-xs text-muted-foreground" title={r.path}>
            {r.method} {r.path}
          </p>
        </div>
      ),
    },
    {
      key: 'doc_code',
      header: 'Chứng từ',
      width: 120,
      cell: (r) => <span className="font-mono text-xs">{r.doc_code || '—'}</span>,
    },
    {
      key: 'http_status',
      header: 'Kết quả',
      width: 110,
      cell: (r) => (
        <Badge
          className={cn(TONE_CLASS[httpStatusTone(r.http_status)])}
          title={httpStatusHint(r.http_status)}
        >
          {r.http_status || '—'}
        </Badge>
      ),
    },
    {
      key: 'duration_ms',
      header: 'Mất',
      width: 90,
      cell: (r) => <span className="tabular-nums">{formatDuration(r.duration_ms)}</span>,
    },
    {
      key: 'change_count',
      header: 'Đổi',
      width: 120,
      cell: (r) => (
        <span className={cn('tabular-nums', !r.change_count && 'text-muted-foreground')}>
          {changeSummaryText(r.change_count, r.change_table_count)}
        </span>
      ),
    },
    {
      key: 'device',
      header: 'Thiết bị',
      width: 180,
      defaultHidden: true,
      cell: (r) => <span className="truncate">{r.device || '—'}</span>,
    },
    {
      key: 'ip',
      header: 'IP',
      width: 130,
      defaultHidden: true,
      cell: (r) => <span className="font-mono text-xs">{r.ip || '—'}</span>,
    },
    {
      key: 'route',
      header: 'Đường (đã gom)',
      width: 240,
      defaultHidden: true,
      cell: (r) => <span className="font-mono text-xs">{r.route || '—'}</span>,
    },
    {
      key: 'source_label',
      header: 'Nguồn',
      width: 110,
      defaultHidden: true,
      cell: (r) => r.source_label || '—',
    },
    {
      key: 'error_code',
      header: 'Mã lỗi',
      width: 140,
      defaultHidden: true,
      cell: (r) => <span className="font-mono text-xs">{r.error_code || '—'}</span>,
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Nhật ký hệ thống"
        description="Mỗi dòng là một lượt gọi — kể cả lượt bị chặn hay lượt hỏng giữa chừng, thứ không để lại dấu vết nghiệp vụ nào"
        actions={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Switch id="logs-follow" checked={follow} onCheckedChange={setFollow} />
              <Label htmlFor="logs-follow" className="text-sm">
                Theo dõi trực tiếp
              </Label>
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()} title="Nạp lại ngay">
              <RotateCw className="size-4 mr-1.5" /> Làm mới
            </Button>
          </div>
        }
      />

      {showCharts && (
        <SystemLogSummaryCharts
          summary={summary.data}
          loading={summary.isLoading}
          from={from}
          to={to}
        />
      )}

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.request_id}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          onRowClick={(r) => setOpenedRequestId(r.request_id)}
          emptyMessage={
            hasFilter
              ? 'Không có lượt gọi nào khớp bộ lọc.'
              : 'Chưa ghi được lượt gọi nào trong khoảng thời gian này.'
          }
          storageKey="system.system_logs"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'lượt gọi',
          }}
          toolbar={
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <DateRangePicker
                  from={from}
                  to={to}
                  onChange={(nextFrom, nextTo) => {
                    setFrom(nextFrom)
                    setTo(nextTo)
                  }}
                  placeholder="Chọn khoảng thời gian"
                  className="w-64"
                />

                <Select value={status} onValueChange={(v) => setStatus(v as LogStatus)}>
                  <SelectTrigger size="sm" className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={LOG_STATUS.ALL}>Mọi kết quả</SelectItem>
                    {/*  «Bị chặn» tách khỏi «Lỗi» vì 403 là hệ thống làm ĐÚNG
                         việc của nó; trộn chung thì câu hỏi "hôm nay hỏng gì"
                         luôn bị vùi dưới hàng trăm lượt thiếu quyền. */}
                    <SelectItem value={LOG_STATUS.ERROR}>Chỉ lỗi (5xx, 4xx)</SelectItem>
                    <SelectItem value={LOG_STATUS.BLOCKED}>Chỉ bị chặn (401, 403)</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={actionGroup || 'all'}
                  onValueChange={(v) => setActionGroup(v === 'all' ? '' : v)}
                >
                  <SelectTrigger size="sm" className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Mọi nhóm hành động</SelectItem>
                    {Object.entries(ACTION_GROUP_LABEL).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Input
                  value={docCode}
                  onChange={(e) => setDocCode(e.target.value)}
                  placeholder="Mã chứng từ…"
                  className="h-8 w-44"
                />

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAdvanced((v) => !v)}
                >
                  Lọc nâng cao
                  {showAdvanced ? (
                    <ChevronUp className="size-4 ml-1" />
                  ) : (
                    <ChevronDown className="size-4 ml-1" />
                  )}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowCharts((v) => !v)}
                >
                  {showCharts ? 'Ẩn biểu đồ' : 'Hiện biểu đồ'}
                </Button>
              </div>

              {showAdvanced && (
                <div className="flex flex-wrap items-center gap-3 border-t pt-3">
                  <Input
                    value={route}
                    onChange={(e) => setRoute(e.target.value)}
                    placeholder="Đường API, vd /api/purchase-orders"
                    className="h-8 w-64"
                  />
                  <Input
                    value={ip}
                    onChange={(e) => setIp(e.target.value)}
                    placeholder="Địa chỉ IP…"
                    className="h-8 w-40"
                  />
                  <Select value={source || 'all'} onValueChange={(v) => setSource(v === 'all' ? '' : v)}>
                    <SelectTrigger size="sm" className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Mọi nguồn</SelectItem>
                      {Object.entries(LOG_SOURCE_LABEL).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {/*  Hai ô dưới lọc theo BẢNG / TRƯỜNG đã bị sửa — đường duy
                       nhất trả lời "ai đổi đơn giá của phiếu này". */}
                  <Input
                    value={table}
                    onChange={(e) => setTable(e.target.value)}
                    placeholder="Bảng bị sửa, vd purchase_order"
                    className="h-8 w-56"
                  />
                  <Input
                    value={field}
                    onChange={(e) => setField(e.target.value)}
                    placeholder="Trường bị sửa, vd unit_price"
                    className="h-8 w-52"
                  />
                </div>
              )}
            </div>
          }
        />
      </Card>

      <SystemLogDetailSheet
        requestId={openedRequestId || null}
        onClose={() => setOpenedRequestId('')}
      />
    </PageContainer>
  )
}
