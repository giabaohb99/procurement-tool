import {
  CheckCircle2,
  CircleDashed,
  Clock,
  Loader,
  RotateCw,
  UserX,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { StatCard } from '@/shared/ui/stat-card'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import {
  SYNC_GRAIN,
  SYNC_STATUS,
  WARN_NO_EMPLOYEE,
  type SyncLogFilters,
  type SyncLogItem,
} from '../api/sync-log-api'
import { SyncLogDetailSheet } from '../components/sync-log-detail-sheet'
import { useSyncLogMeta, useSyncLogStats, useSyncLogs } from '../hooks/use-sync-logs'
import { runCountsText, shortMessage, syncStatusTone } from '../utils/sync-log-format'

/** Khoảng thời gian chọn được. Cố ý không có «tất cả»: sổ này là bảng dày nhất hệ. */
const DAY_OPTIONS = [
  { value: '1', label: '24 giờ qua' },
  { value: '7', label: '7 ngày qua' },
  { value: '30', label: '30 ngày qua' },
  { value: '90', label: '90 ngày qua' },
  { value: '365', label: '1 năm qua' },
]

const DEFAULT_DAYS = '7'

const STATUS_ICON = {
  [SYNC_STATUS.PENDING]: Clock,
  [SYNC_STATUS.RUNNING]: Loader,
  [SYNC_STATUS.SUCCESS]: CheckCircle2,
  [SYNC_STATUS.FAILED]: XCircle,
  [SYNC_STATUS.SKIPPED]: CircleDashed,
} as const

/**
 * SỔ ĐỒNG BỘ — `/system/sync-logs` (bao-CR-449, P4 của đồng bộ app đặt xe cũ).
 *
 * Một dòng = một bản ghi đi qua, hoặc một lượt chạy nền ôm lấy đám bản ghi đó.
 * Đây là màn duy nhất trả lời được câu "phiếu này bên app cũ đã sang ERP chưa,
 * chưa thì hỏng ở đâu" — và trả lời được bằng NGUYÊN VĂN câu lỗi của bên kia,
 * không phải bằng một câu diễn giải lại.
 *
 * Bốn tham số đi qua URL (`status` · `warning` · `source` · `run_id`) vì ba lối
 * vào màn này đều đi từ ngoài: chuông 08:00 trỏ `?status=4`, thẻ đếm đầu trang
 * là liên kết, và bấm một dòng LƯỢT CHẠY thì mở ra chính những bản ghi nó ghi
 * được (`?run_id=`). Các ô còn lại để ở state thường — chúng chỉ có nghĩa khi
 * người ta đang ngồi trước màn hình.
 */
export function SyncLogListPage() {
  const [searchParams] = useSearchParams()

  const [status, setStatus] = useUrlParamState('status', '')
  const [warning, setWarning] = useUrlParamState('warning', '')
  const [source, setSource] = useUrlParamState('source', '')
  const [runId, setRunId] = useUrlParamState('run_id', '')
  const [openedId, setOpenedId] = useUrlParamState('id', '')

  const [grain, setGrain] = useState('')
  const [entity, setEntity] = useState('')
  const [days, setDays] = useState(DEFAULT_DAYS)
  const [keyword, setKeyword] = useState('')
  const [legacyId, setLegacyId] = useState('')

  //  Hai ô gõ chữ phải hoãn: mỗi ký tự một lượt `LIKE '%…%'` trên bảng dày nhất.
  const keywordQuery = useDebouncedValue(keyword)
  const legacyIdQuery = useDebouncedValue(legacyId)

  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([
    status,
    warning,
    source,
    runId,
    grain,
    entity,
    days,
    keywordQuery,
    legacyIdQuery,
  ])

  const filters: SyncLogFilters = {
    source: source || undefined,
    status: status ? Number(status) : undefined,
    warning: warning || undefined,
    run_id: runId ? Number(runId) : undefined,
    grain: grain ? Number(grain) : undefined,
    entity: entity || undefined,
    legacy_id: legacyIdQuery || undefined,
    days: Number(days),
    q: keywordQuery || undefined,
  }

  const { data, isLoading, isError, refetch } = useSyncLogs({
    ...filters,
    page,
    page_size: pageSize,
  })
  //  Thẻ đếm dùng ĐÚNG khoảng ngày và đúng nguồn của bảng. Lệch một trong hai
  //  thì người ta cộng năm thẻ ra một số không khớp tổng bảng rồi đi báo lỗi.
  const stats = useSyncLogStats({ source: source || undefined, days: Number(days) })
  const meta = useSyncLogMeta()

  const hasFilter = Boolean(
    status || warning || source || runId || grain || entity || keywordQuery || legacyIdQuery,
  )

  /** Liên kết của một thẻ đếm: giữ nguyên bộ lọc đang xem, chỉ bật/tắt trạng thái. */
  const statusLink = (code: number) => {
    const next = new URLSearchParams(searchParams)
    if (String(code) === status) next.delete('status')
    else next.set('status', String(code))
    //  Bỏ `id`: mở một dòng rồi bấm thẻ đếm mà ngăn chi tiết vẫn treo dòng cũ
    //  thì người ta tưởng bảng chưa đổi.
    next.delete('id')
    const query = next.toString()
    return query ? `${appRoutes.system.syncLogs}?${query}` : appRoutes.system.syncLogs
  }

  const columns: DataTableColumn<SyncLogItem>[] = [
    {
      key: 'created_at',
      header: 'Lúc',
      width: 150,
      hideable: false,
      cell: (r) => <span className="tabular-nums">{formatDateTime(r.created_at) || '—'}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      width: 120,
      cell: (r) => (
        <Badge className={cn(TONE_CLASS[syncStatusTone(r.status)])}>{r.status_label}</Badge>
      ),
    },
    {
      key: 'source_label',
      header: 'Nguồn',
      width: 170,
      cell: (r) => <span className="truncate">{r.source_label}</span>,
    },
    {
      key: 'subject',
      header: 'Đối tượng',
      width: 220,
      hideable: false,
      cell: (r) => (
        <div className="min-w-0">
          <p className="truncate">
            {r.grain === SYNC_GRAIN.RUN ? r.job_label || '—' : r.entity_label || '—'}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {r.grain_label}
            {r.grain !== SYNC_GRAIN.RUN && r.action_label ? ` · ${r.action_label}` : ''}
          </p>
        </div>
      ),
    },
    {
      key: 'legacy_id',
      header: 'Mã bên app cũ',
      width: 150,
      cell: (r) => <span className="font-mono text-xs">{r.legacy_id || '—'}</span>,
    },
    {
      key: 'message',
      header: 'Nguyên văn bên kia trả về',
      width: 320,
      cell: (r) => (
        <span className="truncate" title={r.message}>
          {shortMessage(r.message) || '—'}
        </span>
      ),
    },
    {
      key: 'warning_labels',
      header: 'Cảnh báo',
      width: 200,
      cell: (r) =>
        r.warning_labels.length === 0 ? null : (
          //  Cờ sống được cả trên dòng THÀNH CÔNG — phiếu đã vào ERP nhưng có ô
          //  do máy suy ra. Hiện cái đầu tiên, phần còn lại đếm.
          <span className="truncate" title={r.warning_labels.join(', ')}>
            <Badge className={cn(TONE_CLASS.pending)}>{r.warning_labels[0]}</Badge>
            {r.warning_labels.length > 1 && (
              <span className="ml-1 text-xs text-muted-foreground">
                +{r.warning_labels.length - 1}
              </span>
            )}
          </span>
        ),
    },
    {
      key: 'counts',
      header: 'Kéo / ghi / bỏ',
      width: 160,
      cell: (r) =>
        r.grain === SYNC_GRAIN.RUN ? (
          <span className="tabular-nums">{runCountsText(r.fetched, r.written, r.skipped)}</span>
        ) : null,
    },
    {
      key: 'local_id',
      header: 'Mã bên ERP',
      width: 110,
      defaultHidden: true,
      cell: (r) => <span className="tabular-nums">{r.local_id || '—'}</span>,
    },
    {
      key: 'run_id',
      header: 'Thuộc lượt chạy',
      width: 130,
      defaultHidden: true,
      cell: (r) => (r.run_id ? `#${r.run_id}` : '—'),
    },
    {
      key: 'direction_label',
      header: 'Chiều',
      width: 100,
      defaultHidden: true,
      cell: (r) => r.direction_label || '—',
    },
    {
      key: 'attempt_count',
      header: 'Số lần thử',
      width: 100,
      defaultHidden: true,
      cell: (r) => <span className="tabular-nums">{r.attempt_count}</span>,
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Sổ đồng bộ"
        description="Mỗi dòng là một bản ghi hoặc một lượt chạy đi qua giữa ERP và hệ ngoài — giữ nguyên văn câu lỗi của bên kia"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} title="Nạp lại ngay">
            <RotateCw className="size-4 mr-1.5" /> Làm mới
          </Button>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {(stats.data?.by_status ?? []).map((row) => (
          <StatCard
            key={row.status}
            icon={STATUS_ICON[row.status as keyof typeof STATUS_ICON] ?? CircleDashed}
            label={row.label}
            value={row.count}
            tone={row.status === SYNC_STATUS.FAILED && row.count > 0 ? 'danger' : undefined}
            hint={String(row.status) === status ? 'Đang lọc theo thẻ này' : undefined}
            loading={stats.isLoading}
            to={statusLink(row.status)}
          />
        ))}
      </div>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          isLoading={isLoading}
          isError={isError}
          onRefresh={() => refetch()}
          onRowClick={(r) => setOpenedId(String(r.id))}
          emptyMessage={
            hasFilter
              ? 'Không có dòng sổ nào khớp bộ lọc.'
              : 'Chưa ghi được lượt đồng bộ nào trong khoảng thời gian này.'
          }
          storageKey="system.sync_logs"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng sổ',
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-3">
              <Select value={days} onValueChange={setDays}>
                <SelectTrigger size="sm" className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DAY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={source || 'all'} onValueChange={(v) => setSource(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-52">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi hệ nguồn</SelectItem>
                  {(meta.data?.sources ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={opt.code}>
                      {opt.label}
                      {opt.enabled === false ? ' (đang tắt)' : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status || 'all'} onValueChange={(v) => setStatus(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi trạng thái</SelectItem>
                  {(meta.data?.statuses ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={String(opt.code)}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={grain || 'all'} onValueChange={(v) => setGrain(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-36">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Cả hai hạt</SelectItem>
                  {(meta.data?.grains ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={String(opt.code)}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={entity || 'all'} onValueChange={(v) => setEntity(v === 'all' ? '' : v)}>
                <SelectTrigger size="sm" className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi đối tượng</SelectItem>
                  {(meta.data?.entities ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={opt.code}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={warning || 'all'}
                onValueChange={(v) => setWarning(v === 'all' ? '' : v)}
              >
                <SelectTrigger size="sm" className="w-56">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi cờ cảnh báo</SelectItem>
                  {(meta.data?.warnings ?? []).map((opt) => (
                    <SelectItem key={opt.code} value={opt.code}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Input
                value={legacyId}
                onChange={(e) => setLegacyId(e.target.value)}
                placeholder="Mã bên app cũ…"
                className="h-8 w-44"
              />

              <Input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Tìm trong câu lỗi…"
                className="h-8 w-56"
              />

              {/*  Ô lọc nhanh đặt riêng chứ không nằm trong danh sách cờ: «chưa
                   gắn được người» là hàng đợi soát THẬT SỰ có người đi xử —
                   phiếu đã vào ERP nhưng chưa biết của ai. Mấy cờ còn lại chỉ
                   là ghi chú dữ liệu. */}
              <Button
                type="button"
                size="sm"
                variant={warning === WARN_NO_EMPLOYEE ? 'default' : 'outline'}
                onClick={() => setWarning(warning === WARN_NO_EMPLOYEE ? '' : WARN_NO_EMPLOYEE)}
              >
                <UserX className="size-4 mr-1.5" />
                Chưa gắn được người
              </Button>

              {runId && (
                <Button type="button" size="sm" variant="ghost" onClick={() => setRunId('')}>
                  Bỏ lọc theo lượt chạy #{runId}
                </Button>
              )}
            </div>
          }
        />
      </Card>

      <SyncLogDetailSheet
        logId={openedId ? Number(openedId) : null}
        onClose={() => setOpenedId('')}
      />
    </PageContainer>
  )
}
