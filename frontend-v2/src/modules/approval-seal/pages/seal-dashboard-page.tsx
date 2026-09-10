import { CheckCircle2, ClipboardCheck, List, Plus, SlidersHorizontal, Stamp } from 'lucide-react'
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
import { SealQueueTable } from '../components/seal-queue-table'
import { useSealDashboard } from '../hooks/use-seal-dashboard'
import { SEAL_STATUS, SEAL_STATUS_LABELS } from '../types/seal-request'

/** Số cột KPI khớp đúng số thẻ hiện ra (Tailwind cần class tĩnh). */
const KPI_GRID_COLS: Record<number, string> = {
  1: 'xl:grid-cols-1',
  2: 'xl:grid-cols-2',
  3: 'xl:grid-cols-3',
  4: 'xl:grid-cols-4',
  5: 'xl:grid-cols-5',
}

/** Các khối bảng/biểu đồ có thể ẩn/hiện trên trang tổng quan. */
type BlockKey = 'recent' | 'approve' | 'clerk' | 'director' | 'trend' | 'status' | 'company'

const BLOCK_LABELS: Record<BlockKey, string> = {
  recent: 'Phiếu gần đây của tôi',
  approve: 'Chờ phê duyệt',
  clerk: 'Chờ đóng dấu',
  director: 'Yêu cầu đã phê duyệt',
  trend: 'Số phiếu theo tháng',
  status: 'Theo trạng thái',
  company: 'Theo công ty',
}

//  Ba bảng phiếu ẩn MẶC ĐỊNH (người dùng tự bật lại trong menu "Hiển thị").
const DEFAULT_HIDDEN: BlockKey[] = ['recent', 'approve', 'clerk']

//  Màu lát bánh "Theo trạng thái" — xoay vòng bộ màu biểu đồ đã chốt của theme.
const STATUS_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-neutral)',
]

/** Ngày local → 'yyyy-mm-dd'. */
function toYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Khoảng báo cáo mặc định: 30 ngày gần nhất (bao hôm nay). */
function defaultReportRange(): { from: string; to: string } {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - 29)
  return { from: toYmd(from), to: toYmd(to) }
}

/**
 * Tổng quan Duyệt dấu — thẻ KPI theo vai trò + bảng báo cáo:
 *  · Nhân sự thường: 1 bảng full-width "Phiếu gần đây của tôi".
 *  · Có vai trò (TBP/Giám đốc/Văn thư): 2 cột — cột 1 "Phiếu gần đây của tôi",
 *    cột 2 theo vai trò (Chờ phê duyệt / Yêu cầu đã phê duyệt / Chờ đóng dấu).
 *  · Mọi người: thống kê theo tháng / trạng thái / bộ phận theo PHẠM VI RIÊNG.
 */
export function SealDashboardPage() {
  const { can } = usePermission()

  //  Khoảng ngày áp cho MỌI khối báo cáo (theo tháng / trạng thái / công ty). Mặc
  //  định 30 ngày gần nhất; bấm X để bỏ lọc → lấy tất cả.
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

  const kpiCount =
    (mine ? 1 : 0) + (approve ? 1 : 0) + (clerk ? 2 : 0) + (director ? 1 : 0)

  //  Khối nào CÓ theo vai trò (chỉ liệt kê trong menu Hiển thị những khối này).
  const available = useMemo<Record<BlockKey, boolean>>(
    () => ({
      recent: Boolean(mine),
      approve: Boolean(approve),
      clerk: Boolean(clerk),
      director: Boolean(director),
      trend: Boolean(stats),
      status: Boolean(stats),
      company: Boolean(stats),
    }),
    [mine, approve, clerk, director, stats],
  )

  //  Khối bị ẩn — mặc định ẩn 3 bảng phiếu; người dùng bật/tắt trong menu "Hiển thị".
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

  //  Bấm thẻ KPI → sang danh sách đã lọc đúng nội dung thẻ. "Phiếu của tôi" không
  //  gắn với một trạng thái nên chỉ mở danh sách (phạm vi `own` tự lọc phiếu của mình).
  const requestsRoute = appRoutes.approvalSeal.requests
  const withStatus = (status: number) => `${requestsRoute}?status=${status}`

  //  Các thẻ bảng ĐANG BẬT, theo thứ tự cố định. `h-full` để khi xếp 2 cột các thẻ
  //  giãn bằng chiều cao hàng (items-stretch ở lưới cha).
  const tableCards: ReactNode[] = []
  if (shows('recent')) {
    tableCards.push(
      <Card key="recent" className="h-full p-4">
        <SealQueueTable
          title="Phiếu gần đây của tôi"
          description="Phiếu đóng dấu bạn đã tạo"
          rows={mine?.recent ?? []}
          isLoading={isLoading}
          emptyMessage="Bạn chưa tạo phiếu nào."
        />
      </Card>,
    )
  }
  if (shows('approve') && approve) {
    tableCards.push(
      <Card key="approve" className="h-full p-4">
        <SealQueueTable
          title="Chờ phê duyệt"
          description={`${approve.pending} phiếu đang chờ bạn duyệt`}
          rows={approve.items}
          hideStatusFilter
          isLoading={isLoading}
          emptyMessage="Không có phiếu chờ duyệt."
        />
      </Card>,
    )
  }
  if (shows('clerk') && clerk) {
    tableCards.push(
      <Card key="clerk" className="h-full p-4">
        <SealQueueTable
          title="Chờ đóng dấu"
          description={`${clerk.to_stamp} phiếu đã duyệt, chờ đóng dấu`}
          rows={clerk.queue}
          hideStatusFilter
          isLoading={isLoading}
          emptyMessage="Không có phiếu chờ đóng dấu."
        />
      </Card>,
    )
  }
  if (shows('director') && director) {
    tableCards.push(
      <Card key="director" className="h-full p-4">
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

  //  Lát bánh "Theo trạng thái" — bỏ lát 0 phiếu, tô màu xoay vòng theo bộ màu theme.
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
        title="Duyệt dấu"
        description="Bảng báo cáo yêu cầu đóng dấu theo vai trò của bạn."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {/*  Bộ lọc thời gian — áp cho MỌI khối báo cáo bên dưới (mặc định 30 ngày; X = tất cả). */}
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
                  <DropdownMenuLabel>Bảng hiển thị</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {menuKeys.map((k) => (
                    <DropdownMenuCheckboxItem
                      key={k}
                      checked={!hidden.has(k)}
                      //  Giữ menu MỞ khi tick nhiều khối (mặc định Radix đóng sau mỗi lần chọn).
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
              <Button asChild>
                <Link to={appRoutes.approvalSeal.new}>
                  <Plus className="mr-1.5 size-4" />
                  Tạo yêu cầu
                </Link>
              </Button>
            )}
          </div>
        }
      />

      {/* Thẻ KPI theo vai trò */}
      {kpiCount > 0 && (
        <div className={cn('mb-4 grid gap-4 sm:grid-cols-2', KPI_GRID_COLS[kpiCount] ?? 'xl:grid-cols-4')}>
          {mine && (
            <StatCard
              icon={Stamp}
              label="Phiếu của tôi"
              value={mineTotal}
              hint={`${mineByStatus[SEAL_STATUS.pending] ?? 0} chờ duyệt · ${mineByStatus[SEAL_STATUS.completed] ?? 0} đã đóng dấu`}
              loading={isLoading}
              to={requestsRoute}
            />
          )}
          {approve && (
            <StatCard
              icon={ClipboardCheck}
              label="Chờ tôi duyệt"
              value={approve.pending}
              hint={approve.pending ? 'Cần phê duyệt' : 'Không tồn đọng'}
              tone={approve.pending ? 'warning' : undefined}
              loading={isLoading}
              to={withStatus(SEAL_STATUS.pending)}
            />
          )}
          {clerk && (
            <>
              <StatCard
                icon={Stamp}
                label="Chờ đóng dấu"
                value={clerk.to_stamp}
                hint={clerk.to_stamp ? 'Đã duyệt, chờ văn thư' : 'Không tồn đọng'}
                tone={clerk.to_stamp ? 'warning' : undefined}
                loading={isLoading}
                to={withStatus(SEAL_STATUS.approved)}
              />
              <StatCard
                icon={CheckCircle2}
                label="Đã đóng dấu"
                value={clerk.completed}
                hint="Đã hoàn thành đóng dấu"
                loading={isLoading}
                to={withStatus(SEAL_STATUS.completed)}
              />
            </>
          )}
          {director && (
            <StatCard
              icon={CheckCircle2}
              label="Đã phê duyệt"
              value={director.count}
              hint="Của công ty bạn"
              loading={isLoading}
              to={withStatus(SEAL_STATUS.approved)}
            />
          )}
        </div>
      )}

      {/* Hàng bảng — chỉ dựng các khối được chọn; 1 khối thì full-width, ≥2 thì 2 cột. */}
      {tableCards.length > 0 && (
        <div className={cn('grid items-stretch gap-4', tableCards.length >= 2 && 'lg:grid-cols-2')}>
          {tableCards}
        </div>
      )}

      {/* Thống kê theo phạm vi riêng — mọi vai trò; bố cục co theo biểu đồ được chọn. */}
      {(shows('trend') || shows('status') || shows('company')) && stats && (
        <div className="mt-4 flex flex-col gap-4">
          {(shows('trend') || shows('status')) && (
            <div className={cn('grid items-start gap-4', shows('trend') && shows('status') && 'lg:grid-cols-3')}>
              {shows('trend') && (
                <ChartCard
                  className={cn(shows('status') && 'lg:col-span-2')}
                  title="Số phiếu theo tháng"
                  description={hasRange ? 'Theo khoảng đã chọn' : '12 tháng gần nhất, trong phạm vi của bạn'}
                  loading={isLoading}
                  isEmpty={stats.trend.every((p) => p.value === 0)}
                  emptyLabel="Chưa phát sinh phiếu."
                >
                  <ColumnChart data={stats.trend} formatValue={(v) => String(v)} />
                </ChartCard>
              )}
              {shows('status') && (
                <ChartCard
                  title="Theo trạng thái"
                  description={hasRange ? 'Số phiếu mỗi trạng thái (khoảng đã chọn)' : 'Số phiếu mỗi trạng thái (tất cả)'}
                  loading={isLoading}
                  isEmpty={statusSlices.length === 0}
                  emptyLabel="Không có phiếu trong khoảng đã chọn."
                >
                  <DonutChart data={statusSlices} centerLabel="phiếu" formatValue={(v) => String(v)} />
                </ChartCard>
              )}
            </div>
          )}
          {shows('company') && (
            <ChartCard
              title="Theo công ty"
              description={hasRange ? 'Số phiếu theo công ty (khoảng đã chọn)' : 'Số phiếu theo công ty'}
              loading={isLoading}
              isEmpty={stats.by_company.length === 0}
            >
              <BarList items={stats.by_company.map((c) => ({ label: c.name, value: c.value }))} />
            </ChartCard>
          )}
        </div>
      )}
    </PageContainer>
  )
}
