import {
  AlertCircle,
  Building2,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  List,
  Plus,
  SlidersHorizontal,
  Stamp,
} from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { BarList } from '@/shared/ui/bar-list'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ChartCard } from '@/shared/ui/chart'
import { ColumnChart } from '@/shared/ui/column-chart'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { DonutChart, type DonutSlice } from '@/shared/ui/donut-chart'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { cn } from '@/shared/utils/cn'
import { SealDirectoryGlanceCard } from '../components/seal-directory-glance-card'
import { SealQueueTable } from '../components/seal-queue-table'
import { useSealDashboard } from '../hooks/use-seal-dashboard'
import { SEAL_STATUS, SEAL_STATUS_LABELS } from '../types/seal-request'

/** Các khối bảng/biểu đồ có thể ẩn/hiện trên trang tổng quan. */
type BlockKey =
  | 'recent'
  | 'approve'
  | 'clerk'
  | 'director'
  | 'trend'
  | 'status'
  | 'company'
  | 'directory'

const BLOCK_LABELS: Record<BlockKey, string> = {
  recent: 'Phiếu gần đây của tôi',
  approve: 'Chờ phê duyệt',
  clerk: 'Chờ đóng dấu',
  director: 'Yêu cầu đã phê duyệt',
  trend: 'Số phiếu theo tháng',
  status: 'Theo trạng thái',
  company: 'Theo công ty',
  directory: 'Danh mục & Văn thư',
}

// Mặc định KHÔNG ẨN khối nào để trang đầy đủ thông tin và sống động ngay khi mở
const DEFAULT_HIDDEN: BlockKey[] = []

// Màu lát bánh "Theo trạng thái"
const STATUS_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-neutral)',
]

function toYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function defaultReportRange(): { from: string; to: string } {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - 29)
  return { from: toYmd(from), to: toYmd(to) }
}

/**
 * Tổng quan Duyệt dấu — Layout mới phong phú, đa chiều:
 *  1. Thanh công cụ & Bộ lọc thời gian chuẩn ERP
 *  2. Dải KPI metrics toàn diện theo vai trò và tổng thể
 *  3. Hàng đợi công việc (Chờ duyệt / Chờ đóng dấu / Phiếu gần đây) hiển thị mặc định
 *  4. Sơ đồ quy trình trình ký & đóng dấu 4 bước chuẩn hóa
 *  5. Thống kê xu hướng tháng, cơ cấu trạng thái, và phân bổ theo công ty
 *  6. Danh mục con dấu lưu hành & Đội ngũ văn thư phụ trách
 */
export function SealDashboardPage() {
  const { can } = usePermission()

  const [reportRange, setReportRange] = useState(defaultReportRange)
  const hasRange = Boolean(reportRange.from || reportRange.to)
  const { data, isLoading } = useSealDashboard({
    date_from: reportRange.from || undefined,
    date_to: reportRange.to || undefined,
  })

  const mine = data?.mine
  const approve = data?.approve
  const clerk = data?.clerk
  const director = data?.director
  const stats = data?.stats

  const mineByStatus = mine?.by_status ?? {}
  const mineTotal = Object.values(mineByStatus).reduce((sum, n) => sum + n, 0)

  // Tổng số phiếu trong kỳ tính từ stats
  const totalStatsCount = useMemo(() => {
    return (stats?.by_status ?? []).reduce((acc, curr) => acc + curr.value, 0)
  }, [stats])

  const completedStatsCount = useMemo(() => {
    const item = (stats?.by_status ?? []).find((s) => s.key === SEAL_STATUS.completed)
    return item?.value ?? 0
  }, [stats])

  const available = useMemo<Record<BlockKey, boolean>>(
    () => ({
      recent: Boolean(mine),
      approve: Boolean(approve),
      clerk: Boolean(clerk),
      director: Boolean(director),
      trend: Boolean(stats),
      status: Boolean(stats),
      company: Boolean(stats),
      directory: true,
    }),
    [mine, approve, clerk, director, stats],
  )

  const [hidden, setHidden] = useState<Set<BlockKey>>(() => new Set(DEFAULT_HIDDEN))
  const shows = (k: BlockKey) => available[k] && !hidden.has(k)
  const toggle = (k: BlockKey) =>
    setHidden((prev) => {
      const next = new Set(prev)
      if (next.has(k)) next.delete(k)
      else next.add(k)
      return next
    })
  const menuKeys = (Object.keys(BLOCK_LABELS) as BlockKey[]).filter((k) => available[k])

  const requestsRoute = appRoutes.approvalSeal.requests
  const withStatus = (status: number) => `${requestsRoute}?status=${status}`

  // Gom các thẻ hàng đợi công việc
  const queueCards: ReactNode[] = []
  if (shows('approve') && approve && approve.items.length > 0) {
    queueCards.push(
      <Card key="approve" className="h-full p-4 border-amber-500/20 shadow-xs">
        <SealQueueTable
          title="Chờ phê duyệt"
          description={`${approve.pending} phiếu đang chờ bạn thẩm định và duyệt`}
          rows={approve.items}
          hideStatusFilter
          isLoading={isLoading}
          emptyMessage="Không có phiếu chờ duyệt."
        />
      </Card>,
    )
  }

  if (shows('clerk') && clerk && clerk.queue.length > 0) {
    queueCards.push(
      <Card key="clerk" className="h-full p-4 border-blue-500/20 shadow-xs">
        <SealQueueTable
          title="Chờ đóng dấu"
          description={`${clerk.to_stamp} phiếu đã duyệt, sẵn sàng đóng dấu`}
          rows={clerk.queue}
          hideStatusFilter
          isLoading={isLoading}
          emptyMessage="Không có phiếu chờ đóng dấu."
        />
      </Card>,
    )
  }

  if (shows('director') && director && director.items.length > 0) {
    queueCards.push(
      <Card key="director" className="h-full p-4 border-border/80 shadow-xs">
        <SealQueueTable
          title="Yêu cầu đã phê duyệt"
          description={`${director.count} phiếu đã duyệt của công ty bạn`}
          rows={director.items}
          hideStatusFilter
          isLoading={isLoading}
          emptyMessage="Chưa có yêu cầu nào."
        />
      </Card>,
    )
  }

  if (shows('recent')) {
    queueCards.push(
      <Card key="recent" className="h-full p-4 border-border/80 shadow-xs">
        <SealQueueTable
          title="Phiếu gần đây của tôi"
          description={
            mineTotal > 0
              ? `${mineTotal} phiếu bạn đã lập trên hệ thống`
              : 'Các yêu cầu đóng dấu do bạn khởi tạo'
          }
          rows={mine?.recent ?? []}
          isLoading={isLoading}
          emptyMessage="Bạn chưa tạo yêu cầu đóng dấu nào."
        />
      </Card>,
    )
  }

  // Lát bánh biểu đồ trạng thái
  const statusSlices: DonutSlice[] = (stats?.by_status ?? [])
    .filter((s) => s.value > 0)
    .map((s, i) => ({
      label: s.label || SEAL_STATUS_LABELS[s.key ?? 0] || '—',
      value: s.value,
      color: STATUS_COLORS[i % STATUS_COLORS.length],
    }))

  return (
    <PageContainer>
      <PageHeader
        title="Tổng quan Duyệt dấu"
        description="Theo dõi tình trạng trình ký, tiến độ thẩm định và số lượng đóng dấu chứng từ toàn hệ thống."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <DateRangePicker
              from={reportRange.from}
              to={reportRange.to}
              placeholder="Khoảng thời gian…"
              onChange={(from, to) => setReportRange({ from, to })}
            />
            {menuKeys.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline">
                    <SlidersHorizontal className="mr-1.5 size-4" />
                    Hiển thị
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>Bố cục trang tổng quan</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {menuKeys.map((k) => (
                    <DropdownMenuCheckboxItem
                      key={k}
                      checked={!hidden.has(k)}
                      onSelect={(e) => e.preventDefault()}
                      onCheckedChange={() => toggle(k)}
                    >
                      {BLOCK_LABELS[k]}
                    </DropdownMenuCheckboxItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            <Button asChild variant="outline">
              <Link to={appRoutes.approvalSeal.requests}>
                <List className="mr-1.5 size-4" />
                Danh sách
              </Link>
            </Button>
            {can('seal_request', 'create') && (
              <Button asChild className="bg-primary hover:bg-primary/90">
                <Link to={appRoutes.approvalSeal.new}>
                  <Plus className="mr-1.5 size-4" />
                  Tạo yêu cầu
                </Link>
              </Button>
            )}
          </div>
        }
      />

      {/* ── 1. Dải thẻ KPI Metrics đa chiều ───────────────────────────────── */}
      <div className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
        {/* Phiếu của tôi */}
        <StatCard
          icon={Stamp}
          label="Phiếu của tôi"
          value={mineTotal}
          hint={`${mineByStatus[SEAL_STATUS.pending] ?? 0} chờ duyệt · ${mineByStatus[SEAL_STATUS.completed] ?? 0} đã đóng dấu`}
          loading={isLoading}
          to={requestsRoute}
        />

        {/* Chờ tôi duyệt (TBP) */}
        {approve && (
          <StatCard
            icon={ClipboardCheck}
            label="Chờ tôi duyệt"
            value={approve.pending}
            hint={approve.pending > 0 ? 'Hồ sơ cần thẩm định ngay' : 'Không có việc tồn'}
            tone={approve.pending > 0 ? 'warning' : undefined}
            loading={isLoading}
            to={withStatus(SEAL_STATUS.pending)}
          />
        )}

        {/* Chờ văn thư đóng dấu */}
        {clerk ? (
          <StatCard
            icon={Clock}
            label="Chờ đóng dấu"
            value={clerk.to_stamp}
            hint={clerk.to_stamp > 0 ? 'Đã duyệt, chờ dập dấu' : 'Không tồn đọng'}
            tone={clerk.to_stamp > 0 ? 'warning' : undefined}
            loading={isLoading}
            to={withStatus(SEAL_STATUS.approved)}
          />
        ) : (
          <StatCard
            icon={Clock}
            label="Chờ duyệt của tôi"
            value={mineByStatus[SEAL_STATUS.pending] ?? 0}
            hint="Đang chờ TBP phê duyệt"
            loading={isLoading}
            to={withStatus(SEAL_STATUS.pending)}
          />
        )}

        {/* Đã đóng dấu hoàn tất */}
        <StatCard
          icon={CheckCircle2}
          label="Đã hoàn thành"
          value={clerk ? clerk.completed : (mineByStatus[SEAL_STATUS.completed] ?? completedStatsCount)}
          hint={clerk ? 'Văn thư đã đóng dấu' : 'Đã đóng dấu bàn giao'}
          loading={isLoading}
          to={withStatus(SEAL_STATUS.completed)}
        />

        {/* Tổng hồ sơ trong kỳ hoặc Bị từ chối */}
        {(mineByStatus[SEAL_STATUS.rejected] ?? 0) > 0 ? (
          <StatCard
            icon={AlertCircle}
            label="Bị từ chối / Trả lại"
            value={(mineByStatus[SEAL_STATUS.rejected] ?? 0) + (mineByStatus[SEAL_STATUS.returned] ?? 0)}
            hint="Cần xem lý do & hiệu chỉnh"
            tone="danger"
            loading={isLoading}
            to={withStatus(SEAL_STATUS.rejected)}
          />
        ) : (
          <StatCard
            icon={Building2}
            label="Tổng lưu lượng"
            value={totalStatsCount || mineTotal}
            hint={hasRange ? 'Theo khoảng ngày đã chọn' : 'Toàn thời gian'}
            loading={isLoading}
            to={requestsRoute}
          />
        )}
      </div>

      {/* ── 2. Hàng đợi công việc & Danh sách gần đây ──────────────────────── */}
      {queueCards.length > 0 && (
        <div className={cn('mb-4 grid items-stretch gap-4', queueCards.length >= 2 && 'lg:grid-cols-2')}>
          {queueCards}
        </div>
      )}

      {/* ── 4. Thống kê phân tích: Xu hướng · Trạng thái · Công ty ────────── */}
      {(shows('trend') || shows('status') || shows('company')) && stats && (
        <div className="mb-4 flex flex-col gap-4">
          <div className="grid items-start gap-4 lg:grid-cols-3">
            {/* Biểu đồ số phiếu theo tháng */}
            {shows('trend') && (
              <ChartCard
                className={cn(shows('status') ? 'lg:col-span-2' : 'lg:col-span-3')}
                title="Xu hướng yêu cầu theo tháng"
                description={hasRange ? 'Khối lượng phiếu phát sinh theo khoảng thời gian đã chọn' : 'Khối lượng phát sinh 12 tháng gần nhất'}
                loading={isLoading}
                isEmpty={stats.trend.every((p) => p.value === 0)}
                emptyLabel="Chưa phát sinh phiếu trong khoảng thời gian này."
              >
                <ColumnChart data={stats.trend} formatValue={(v) => String(v)} />
              </ChartCard>
            )}

            {/* Biểu đồ phân bổ trạng thái */}
            {shows('status') && (
              <ChartCard
                title="Cơ cấu theo trạng thái"
                description={hasRange ? 'Tỷ lệ trạng thái trong khoảng đã chọn' : 'Tỷ lệ trạng thái toàn bộ yêu cầu'}
                loading={isLoading}
                isEmpty={statusSlices.length === 0}
                emptyLabel="Không có dữ liệu trạng thái."
              >
                <DonutChart data={statusSlices} centerLabel="phiếu" formatValue={(v) => String(v)} />
              </ChartCard>
            )}
          </div>

          {/* Phân bổ theo công ty */}
          {shows('company') && (
            <ChartCard
              title="Khối lượng đóng dấu theo Công ty / Pháp nhân"
              description={hasRange ? 'Số lượt đóng dấu cho từng pháp nhân trong khoảng đã chọn' : 'Số lượt đóng dấu cho từng pháp nhân trực thuộc tập đoàn'}
              loading={isLoading}
              isEmpty={stats.by_company.length === 0}
              emptyLabel="Chưa có dữ liệu theo công ty."
            >
              <BarList items={stats.by_company.map((c) => ({ label: c.name, value: c.value }))} />
            </ChartCard>
          )}
        </div>
      )}

      {/* ── 5. Danh mục con dấu & Văn thư phụ trách ───────────────────────── */}
      {shows('directory') && (
        <div className="mb-4">
          <SealDirectoryGlanceCard />
        </div>
      )}
    </PageContainer>
  )
}
