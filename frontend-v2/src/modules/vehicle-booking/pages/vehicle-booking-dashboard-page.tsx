import {
  ClipboardCheck,
  Gauge,
  List,
  Plus,
  Route as RouteIcon,
  Send,
  SlidersHorizontal,
  Truck,
} from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { BarList } from '@/shared/ui/bar-list'
import { Button } from '@/shared/ui/button'
import { CHART_COLORS, CHART_NEUTRAL, ChartCard } from '@/shared/ui/chart'
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
import { BookingQueueTable } from '../components/booking-queue-table'
import { DriverStatsTable, VehicleStatsTable } from '../components/fleet-stats-table'
import { useVehicleBookingDashboard } from '../hooks/use-vehicle-booking-dashboard'
import { compactMoney } from '../utils/compact-money'
import { BOOKING_STATUS, BOOKING_STATUS_LABELS } from '../types/vehicle-booking'

/** Số cột KPI khớp đúng số thẻ hiện ra (Tailwind cần class tĩnh). */
const KPI_GRID_COLS: Record<number, string> = {
  1: 'xl:grid-cols-1',
  2: 'xl:grid-cols-2',
  3: 'xl:grid-cols-3',
  4: 'xl:grid-cols-4',
  5: 'xl:grid-cols-5',
}

/** Các khối bảng/biểu đồ có thể ẩn/hiện trên trang tổng quan. */
type BlockKey =
  | 'recent' | 'approve' | 'dispatch' | 'driver'
  | 'trend' | 'type' | 'status' | 'company'
  | 'vehicles' | 'drivers'

const BLOCK_LABELS: Record<BlockKey, string> = {
  recent: 'Phiếu gần đây của tôi',
  approve: 'Chờ tôi duyệt',
  dispatch: 'Chờ điều phối',
  driver: 'Chuyến của tôi',
  trend: 'Số phiếu theo tháng',
  type: 'Theo loại yêu cầu',
  status: 'Theo trạng thái',
  company: 'Theo công ty',
  vehicles: 'Thống kê theo xe',
  drivers: 'Thống kê theo tài xế',
}

//  Ẩn MẶC ĐỊNH ba bảng hàng-chờ (bật lại trong menu "Hiển thị").
const DEFAULT_HIDDEN: BlockKey[] = ['approve', 'dispatch', 'recent']

//  Màu lát bánh "Theo trạng thái" — xoay vòng bộ màu biểu đồ của theme.
const STATUS_COLORS = ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)', 'var(--chart-4)', 'var(--chart-neutral)']

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
 * Tổng quan Đặt xe — TỰ THÍCH ỨNG theo vai trò: backend chỉ trả khối mà quyền của
 * người xem mở khóa, trang chỉ vẽ khối nào có mặt. Cùng khuôn UX với Duyệt dấu:
 * thẻ KPI bấm được → danh sách đã lọc; bộ lọc thời gian cho các biểu đồ; menu
 * "Hiển thị" bật/tắt từng khối; bố cục co theo khối được chọn.
 */
export function VehicleBookingDashboardPage() {
  const { can } = usePermission()

  //  Khoảng ngày áp cho các BIỂU ĐỒ tổng hợp (mặc định 30 ngày; X = tất cả).
  const [reportRange, setReportRange] = useState(defaultReportRange)
  const hasRange = Boolean(reportRange.from || reportRange.to)
  const { data, isLoading } = useVehicleBookingDashboard({
    date_from: reportRange.from || undefined,
    date_to: reportRange.to || undefined,
  })

  const mine = data?.mine
  const approve = data?.approve
  const dispatch = data?.dispatch
  const driver = data?.driver
  const company = data?.company
  const fleet = data?.fleet

  const mineByStatus = mine?.by_status ?? {}
  const mineTotal = Object.values(mineByStatus).reduce((sum, n) => sum + n, 0)

  // Đếm số thẻ KPI để chia cột (mine:1 · approve:1 · dispatch:3 · driver:2).
  const kpiCount =
    (mine ? 1 : 0) + (approve ? 1 : 0) + (dispatch ? 3 : 0) + (driver ? 2 : 0)

  //  Bấm thẻ KPI → danh sách đã lọc đúng nội dung thẻ.
  const requestsRoute = appRoutes.vehicleBooking.requests
  const withStatus = (status: number) => `${requestsRoute}?status=${status}`
  const myTripsRoute = appRoutes.vehicleBooking.myTrips

  //  Khối nào CÓ theo vai trò (chỉ liệt kê trong menu Hiển thị những khối này).
  const available = useMemo<Record<BlockKey, boolean>>(
    () => ({
      recent: Boolean(mine),
      approve: Boolean(approve),
      dispatch: Boolean(dispatch),
      driver: Boolean(driver),
      trend: Boolean(company),
      type: Boolean(company),
      status: Boolean(company),
      company: Boolean(company),
      vehicles: Boolean(fleet),
      drivers: Boolean(fleet),
    }),
    [mine, approve, dispatch, driver, company, fleet],
  )

  //  Ẩn mặc định 3 bảng hàng-chờ; người dùng bật/tắt trong menu "Hiển thị".
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

  //  Các bảng hàng-chờ đang bật (theo thứ tự cố định).
  const queueCards: ReactNode[] = []
  if (shows('approve') && approve) {
    queueCards.push(
      <ChartCard key="approve" title="Chờ tôi duyệt" description={`${approve.pending} phiếu đang chờ`} loading={isLoading}>
        <BookingQueueTable rows={approve.items} hideStatusFilter emptyMessage="Không có phiếu chờ duyệt." />
      </ChartCard>,
    )
  }
  if (shows('dispatch') && dispatch) {
    queueCards.push(
      <ChartCard
        key="dispatch"
        title="Chờ điều phối"
        description={`${dispatch.to_dispatch} phiếu đã duyệt, chờ phân xe`}
        loading={isLoading}
      >
        <BookingQueueTable rows={dispatch.queue} hideStatusFilter emptyMessage="Không có phiếu chờ điều phối." />
      </ChartCard>,
    )
  }
  if (shows('driver') && driver) {
    queueCards.push(
      <ChartCard key="driver" title="Chuyến của tôi" description="Chuyến được phân cho bạn" loading={isLoading}>
        <BookingQueueTable rows={driver.trips} emptyMessage="Bạn chưa có chuyến nào." />
      </ChartCard>,
    )
  }
  if (shows('recent') && mine) {
    queueCards.push(
      <ChartCard key="recent" title="Phiếu gần đây của tôi" description="8 phiếu mới nhất" loading={isLoading}>
        <BookingQueueTable rows={mine.recent} emptyMessage="Bạn chưa tạo phiếu nào." />
      </ChartCard>,
    )
  }

  //  Lát bánh "Theo trạng thái" (bỏ lát 0, tô màu xoay vòng).
  const statusSlices: DonutSlice[] = (company?.by_status ?? [])
    .filter((s) => s.value > 0)
    .map((s, i) => ({
      label: s.label || BOOKING_STATUS_LABELS[s.key ?? 0] || '—',
      value: s.value,
      color: STATUS_COLORS[i % STATUS_COLORS.length],
    }))

  return (
    <PageContainer>
      <PageHeader
        title="Đặt xe"
        description="Tổng quan yêu cầu đặt xe theo vai trò của bạn."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {/*  Bộ lọc thời gian — áp cho các BIỂU ĐỒ tổng hợp (mặc định 30 ngày; X = tất cả). */}
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
              <Link to={appRoutes.vehicleBooking.requests}>
                <List className="mr-1.5 size-4" />
                Danh sách
              </Link>
            </Button>
            {can('vehicle_booking', 'create') && (
              <Button asChild>
                <Link to={appRoutes.vehicleBooking.new}>
                  <Plus className="mr-1.5 size-4" />
                  Tạo yêu cầu
                </Link>
              </Button>
            )}
          </div>
        }
      />

      {kpiCount > 0 && (
        <div className={cn('mb-4 grid gap-4 sm:grid-cols-2', KPI_GRID_COLS[kpiCount] ?? 'xl:grid-cols-5')}>
          {mine && (
            <StatCard
              icon={Truck}
              label="Phiếu của tôi"
              value={mineTotal}
              hint={`${mineByStatus[BOOKING_STATUS.pending] ?? 0} chờ duyệt · ${mineByStatus[BOOKING_STATUS.completed] ?? 0} hoàn thành`}
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
              to={withStatus(BOOKING_STATUS.pending)}
            />
          )}
          {dispatch && (
            <>
              <StatCard
                icon={Send}
                label="Chờ điều phối"
                value={dispatch.to_dispatch}
                hint={dispatch.to_dispatch ? 'Cần phân xe / tài xế' : 'Không tồn đọng'}
                tone={dispatch.to_dispatch ? 'warning' : undefined}
                loading={isLoading}
                to={withStatus(BOOKING_STATUS.approved)}
              />
              <StatCard
                icon={RouteIcon}
                label="Đang chạy"
                value={dispatch.ongoing}
                hint="Đã điều phối, đang thực hiện"
                loading={isLoading}
                to={withStatus(BOOKING_STATUS.dispatched)}
              />
              <StatCard
                icon={Gauge}
                label="Quãng đường"
                value={`${dispatch.distance_sum.toLocaleString('vi-VN')} km`}
                hint={`Chi phí ${compactMoney(dispatch.cost_sum)} đ`}
                loading={isLoading}
              />
            </>
          )}
          {driver && (
            <>
              <StatCard
                icon={ClipboardCheck}
                label="Chuyến chờ nhận"
                value={driver.waiting}
                hint={driver.waiting ? 'Cần bạn xác nhận' : 'Không có'}
                tone={driver.waiting ? 'warning' : undefined}
                loading={isLoading}
                to={myTripsRoute}
              />
              <StatCard
                icon={RouteIcon}
                label="Đang đi"
                value={driver.ongoing}
                hint={`${driver.completed} chuyến đã hoàn thành`}
                loading={isLoading}
                to={myTripsRoute}
              />
            </>
          )}
        </div>
      )}

      {/* Các khối hàng chờ theo vai trò — chỉ dựng khối được chọn; ≥2 thì 2 cột. */}
      {queueCards.length > 0 && (
        <div className={cn('grid items-start gap-4', queueCards.length >= 2 && 'lg:grid-cols-2')}>
          {queueCards}
        </div>
      )}

      {/* Khối tổng hợp (Giám đốc / phạm vi ≥ phòng) — lọc theo khoảng ngày, co theo lựa chọn.
          Bố cục 2×2: [Số phiếu theo tháng | Theo loại yêu cầu] · [Theo trạng thái | Theo công ty]. */}
      {(shows('trend') || shows('type') || shows('status') || shows('company')) && company && (
        <div className="mt-4 flex flex-col gap-4">
          {(shows('trend') || shows('type')) && (
            <div className="grid items-start gap-4 lg:grid-cols-2">
              {shows('trend') && (
                <ChartCard
                  title="Số phiếu theo tháng"
                  description={hasRange ? 'Theo khoảng đã chọn' : '12 tháng gần nhất, trong phạm vi bạn xem được'}
                  loading={isLoading}
                  isEmpty={company.trend.every((p) => p.value === 0)}
                  emptyLabel="Chưa phát sinh phiếu."
                >
                  <ColumnChart data={company.trend} formatValue={(v) => String(v)} />
                </ChartCard>
              )}
              {shows('type') && (
                <ChartCard title="Theo loại yêu cầu" description="Công tác vs Giao hàng" loading={isLoading}>
                  <DonutChart
                    centerLabel="phiếu"
                    data={[
                      { label: 'Công tác', value: company.by_type.car, color: CHART_COLORS[0] ?? CHART_NEUTRAL },
                      { label: 'Giao hàng', value: company.by_type.delivery, color: CHART_COLORS[1] ?? CHART_NEUTRAL },
                    ]}
                  />
                </ChartCard>
              )}
            </div>
          )}
          {(shows('status') || shows('company')) && (
            <div className="grid items-start gap-4 lg:grid-cols-2">
              {shows('status') && (
                <ChartCard
                  title="Theo trạng thái"
                  description="Số phiếu mỗi trạng thái"
                  loading={isLoading}
                  isEmpty={statusSlices.length === 0}
                >
                  <DonutChart data={statusSlices} centerLabel="phiếu" formatValue={(v) => String(v)} />
                </ChartCard>
              )}
              {shows('company') && (
                <ChartCard
                  title="Theo công ty"
                  description="Số phiếu theo công ty"
                  loading={isLoading}
                  isEmpty={company.by_company.length === 0}
                >
                  <BarList items={company.by_company.map((c) => ({ label: c.name, value: c.value }))} />
                </ChartCard>
              )}
            </div>
          )}
        </div>
      )}

      {/* Bảng đội xe (Điều phối viên / Giám đốc — quyền `approve`): theo xe & theo tài xế. */}
      {(shows('vehicles') || shows('drivers')) && fleet && (
        <div className="mt-4 grid items-start gap-4 lg:grid-cols-2">
          {shows('vehicles') && (
            <ChartCard title="Thống kê theo xe" description="Số phiếu · hoàn tất · km · chi phí" loading={isLoading}>
              <VehicleStatsTable rows={fleet.by_vehicle} />
            </ChartCard>
          )}
          {shows('drivers') && (
            <ChartCard title="Thống kê theo tài xế" description="Số phiếu · hoàn tất · km" loading={isLoading}>
              <DriverStatsTable rows={fleet.by_driver} />
            </ChartCard>
          )}
        </div>
      )}
    </PageContainer>
  )
}
