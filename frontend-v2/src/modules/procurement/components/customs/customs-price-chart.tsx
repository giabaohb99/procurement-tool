// bao-CR-470 — thẻ «Biểu đồ» của màn Tra cứu giá hải quan (bản v2, recharts).
//
// Bốn luật lấy từ số liệu thật của ATRAZINE (doc/erp/hai-quan/04-giao-dien.md §4) —
// đừng "làm cho đẹp" mà bỏ:
//   1. Tách theo đơn vị — kg và lít không vẽ chung (hàng chip đơn vị).
//   2. Kỳ không có dòng nào để TRỐNG: không vẽ 0, không nối đường qua
//      (`connectNulls={false}`, giá kỳ trống là `null`).
//   3. Kỳ dưới `min_lines_for_best` dòng vẽ điểm RỖNG và không được gắn nhãn "tốt nhất"
//      (backend đã loại chúng khỏi `best_period`).
//   4. Dải tô nhạt là KHOẢNG GIÁ PHỔ BIẾN p25–p75 (nửa số dòng ở giữa), KHÔNG phải thấp–cao:
//      vài dòng giá lạ (250 USD/lít giữa đám 2–4 USD/lít) kéo trục lên trần và ép đường bình
//      quân dẹp sát đáy — lỗi thật ở bản v1. Trục giá cũng tính theo p25/p75 + bình quân
//      (`buildPriceAxis`); thấp / cao vẫn hiện trong bảng và ô rê chuột.
//
// Hai biểu đồ (giá · lượng) chung `syncId`, chung lề và chung bề rộng trục Y để nhãn kỳ
// thẳng cột với nhau; rê chuột ở biểu đồ nào cũng hiện ô số liệu đầy đủ của kỳ đó ở biểu
// đồ giá. Cỡ chữ cố định (recharts vẽ theo điểm ảnh thật, không co giãn `viewBox`).
import { Boxes, ListOrdered, Scale, TrendingDown, TrendingUp } from 'lucide-react'
import { useMemo, useState } from 'react'
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { StatCard } from '@/shared/ui/stat-card'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'

import { useCustomsStats } from '../../hooks/use-customs'
import type {
  CustomsFilters,
  CustomsPeriod,
  CustomsPriceMode,
  CustomsSeriesPoint,
} from '../../types/customs'
import {
  buildCustomsParams,
  buildPriceAxis,
  CUSTOMS_PERIOD_OPTIONS,
  formatCompactQuantity,
  formatCustomsUnit,
  formatUsd,
  type PriceAxis,
} from '../../utils/customs'
import { CustomsNotice, CustomsSegmentedChoice, CustomsUnitChips } from './customs-controls'


const PRICE_COLOR = 'var(--chart-1)'
const BEST_COLOR = 'var(--success)'
const QTY_COLOR = 'var(--chart-neutral)'
const AXIS_TICK = { fill: 'var(--muted-foreground)', fontSize: 12 }
/**
 * Lề + bề rộng trục Y DÙNG CHUNG cho hai biểu đồ: lệch nhau một chút là nhãn kỳ của biểu
 * đồ lượng không còn thẳng cột với nhãn kỳ của biểu đồ giá. Lề phải đủ rộng để nhãn kỳ
 * cuối không bị xén nửa chữ.
 */
const CHART_MARGIN = { top: 8, right: 28, bottom: 0, left: 4 }
const Y_AXIS_WIDTH = 60
const SYNC_ID = 'customs-price-chart'

/** Một điểm trên trục — giữ nguyên kỳ gốc + dải `[p25, p75]` cho vùng tô. */
interface ChartPoint extends CustomsSeriesPoint {
  band: [number, number] | null
  isBest: boolean
}

interface CustomsPriceChartProps {
  filters: CustomsFilters
}

export function CustomsPriceChart({ filters }: CustomsPriceChartProps) {
  const [period, setPeriod] = useState<CustomsPeriod>('month')
  //  bao-CR-493: đại ca chốt bỏ hẳn nút chọn giá — biểu đồ luôn vẽ GIÁ ĐIỀU CHỈNH (giá hải quan
  //  áp lại để tính thuế); ai cần giá khai báo thì thẻ Danh sách vẫn có đủ hai cột.
  const priceMode: CustomsPriceMode = 'adjusted'
  const [chartUnit, setChartUnit] = useState('')

  //  Đổi bộ lọc thì đơn vị cũ có thể không còn trong tập mới — trả về để backend tự
  //  chọn đơn vị nhiều dòng nhất.
  const filtersChanged = useHasChanged(JSON.stringify(filters))
  if (filtersChanged && chartUnit) setChartUnit('')

  const params = {
    ...buildCustomsParams(filters),
    period,
    price_mode: priceMode,
    ...(chartUnit ? { chart_unit: chartUnit } : {}),
  }
  const { data, isLoading, isError, error } = useCustomsStats(params, true)

  const points = useMemo<ChartPoint[]>(
    () =>
      (data?.series ?? []).map((point) => ({
        ...point,
        band:
          typeof point.p25 === 'number' && typeof point.p75 === 'number'
            ? [point.p25, point.p75]
            : null,
        isBest: point.period === data?.best_period,
      })),
    [data],
  )
  const priceAxis = useMemo(() => buildPriceAxis(data?.series ?? []), [data])

  const unit = formatCustomsUnit(data?.unit)
  const minLines = data?.min_lines_for_best ?? 5

  const tableColumns = useMemo<DataTableColumn<ChartPoint>[]>(
    () => [
      { key: 'label', header: 'Kỳ', width: 110, hideable: false, cell: (p) => p.label },
      {
        key: 'count',
        header: 'Số dòng',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (p) => <span className="tabular-nums">{p.count}</span>,
      },
      {
        key: 'qty',
        header: `Tổng lượng (${unit})`,
        width: 140,
        align: 'right',
        hideable: false,
        cell: (p) => <span className="tabular-nums">{p.count ? formatQuantity(p.qty) : '—'}</span>,
      },
      {
        key: 'min',
        header: 'Thấp nhất',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (p) => <span className="tabular-nums">{formatUsd(p.min)}</span>,
      },
      {
        key: 'common_range',
        header: 'Khoảng phổ biến (25–75%)',
        width: 180,
        align: 'right',
        hideable: false,
        cell: (p) => <span className="tabular-nums">{formatCommonRange(p)}</span>,
      },
      {
        key: 'wavg',
        header: 'Bình quân gia quyền',
        width: 150,
        align: 'right',
        hideable: false,
        cell: (p) => <span className="font-semibold tabular-nums">{formatUsd(p.wavg)}</span>,
      },
      {
        key: 'max',
        header: 'Cao nhất',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (p) => <span className="tabular-nums">{formatUsd(p.max)}</span>,
      },
      {
        key: 'note',
        header: 'Ghi chú',
        width: 220,
        hideable: false,
        wrap: true,
        cell: (p) => (
          <span className={cn('text-xs', p.isBest ? 'font-medium text-success' : 'text-muted-foreground')}>
            {p.count === 0
              ? 'Không có dữ liệu'
              : p.isBest
                ? 'Giá tốt nhất (đủ dữ liệu)'
                : p.low_data
                  ? `Ít dữ liệu (< ${minLines} dòng)`
                  : ''}
          </span>
        ),
      },
    ],
    [unit, minLines],
  )

  if (isError) {
    return (
      <Card className="p-6 text-sm text-muted-foreground">
        {extractErrorMessage(error) || 'Không tải được biểu đồ.'}
      </Card>
    )
  }

  if (isLoading || !data) {
    return (
      <Card className="gap-3 p-6">
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </Card>
    )
  }

  const { kpi, coverage } = data
  const priceUnit = unit ? `USD/${unit}` : 'USD'
  const outliers = kpi.outliers ?? 0

  return (
    <div className="flex flex-col gap-3">
      {/* bao-CR-493: Kỳ và Đơn vị nằm chung MỘT thẻ (đề xuất đại ca 25/09) — hai hàng nút rời
          nhau nhìn như hai việc khác nhau, thật ra đều là cách cắt cùng một biểu đồ. */}
      <Card className="gap-3 p-4">
        <CustomsSegmentedChoice
          label="Kỳ"
          value={period}
          options={CUSTOMS_PERIOD_OPTIONS}
          onChange={setPeriod}
        />
        <CustomsUnitChips units={data.units} value={data.unit} onChange={setChartUnit} />
      </Card>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <StatCard icon={TrendingDown} label="Thấp nhất" value={formatUsd(kpi.min)} hint={priceUnit} />
        <StatCard
          icon={Scale}
          label="Bình quân gia quyền"
          value={formatUsd(kpi.wavg)}
          hint={
            typeof kpi.p25 === 'number' && typeof kpi.p75 === 'number'
              ? `${priceUnit} · phổ biến ${formatUsd(kpi.p25)} – ${formatUsd(kpi.p75)}`
              : priceUnit
          }
        />
        <StatCard icon={TrendingUp} label="Cao nhất" value={formatUsd(kpi.max)} hint={priceUnit} />
        <StatCard icon={Boxes} label="Tổng lượng" value={formatQuantity(kpi.qty) || '0'} hint={unit} />
        <StatCard
          icon={ListOrdered}
          label="Số dòng hàng"
          value={String(kpi.count ?? 0)}
          hint="không phải số tờ khai"
        />
      </div>

      <CustomsNotice tone="warning">
        Dựa trên {coverage.lines} dòng hàng trong {coverage.months} tháng (
        {formatDate(coverage.date_from) || '—'} → {formatDate(coverage.date_to) || '—'}).
        {coverage.empty_periods.length > 0 && (
          <> Không có dữ liệu ở: {coverage.empty_periods.join(', ')}.</>
        )}
        {coverage.years < 2 ? (
          <>
            {' '}
            Mới có dữ liệu <b>{coverage.years} năm</b> — chỉ thấy xu hướng trong năm, chưa đủ để
            kết luận theo mùa vụ.
          </>
        ) : (
          <> Có dữ liệu {coverage.years} năm.</>
        )}{' '}
        Kỳ dưới {minLines} dòng vẽ điểm rỗng và không được chọn làm kỳ giá tốt nhất.
        {outliers > 0 && (
          <>
            {' '}
            <b>{outliers} dòng giá bất thường</b> (ngoài khoảng phổ biến) — xem cột Thấp nhất /
            Cao nhất.
          </>
        )}
      </CustomsNotice>

      <Card className="min-w-0 gap-3 p-4">
        <ChartLegend />
        {priceAxis ? (
          <PriceChart points={points} axis={priceAxis} priceUnit={priceUnit} unit={unit} />
        ) : (
          <p className="py-8 text-center text-sm text-muted-foreground">Không có giá để vẽ.</p>
        )}
        <p className="text-xs text-muted-foreground">Lượng nhập ({unit || 'đơn vị'})</p>
        <QuantityChart points={points} />
      </Card>

      <Card className="p-4">
        <DataTable
          columns={tableColumns}
          rows={points}
          getRowId={(point) => point.period}
          //  Nền ĐỤC (luật bảng: cấm nền hàng có alpha) — khai lại đúng cặp odd/even để
          //  đè sọc mặc định của `DataTable`.
          rowClassName={(point) =>
            point.isBest
              ? 'odd:bg-emerald-50 even:bg-emerald-50 dark:odd:bg-emerald-950 dark:even:bg-emerald-950'
              : undefined
          }
          emptyMessage="Không có kỳ nào để hiện."
        />
      </Card>
    </div>
  )
}

function ChartLegend() {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="h-0.5 w-3.5" style={{ backgroundColor: PRICE_COLOR }} />
        Bình quân gia quyền
      </li>
      <li className="flex items-center gap-1.5">
        <span
          aria-hidden
          className="h-2.5 w-3 rounded-sm opacity-20"
          style={{ backgroundColor: PRICE_COLOR }}
        />
        Khoảng giá phổ biến (50% số dòng ở giữa)
      </li>
      <li className="flex items-center gap-1.5">
        <span
          aria-hidden
          className="size-2.5 rounded-full border-2 bg-card"
          style={{ borderColor: PRICE_COLOR }}
        />
        Ít dữ liệu
      </li>
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="size-2.5 rounded-full" style={{ backgroundColor: BEST_COLOR }} />
        Kỳ giá tốt nhất (đủ dữ liệu)
      </li>
    </ul>
  )
}

/** Điểm của đường bình quân: rỗng khi ít dữ liệu, xanh lá to hơn ở kỳ tốt nhất. */
function renderPriceDot(props: {
  cx?: number | string
  cy?: number | string
  index: number
  payload?: unknown
}) {
  const point = props.payload as ChartPoint | undefined
  const cx = Number(props.cx)
  const cy = Number(props.cy)
  if (!point || point.wavg === null || !Number.isFinite(cx) || !Number.isFinite(cy)) {
    return <g key={`dot-${props.index}`} />
  }
  const color = point.isBest ? BEST_COLOR : PRICE_COLOR
  return (
    <circle
      key={`dot-${props.index}`}
      cx={cx}
      cy={cy}
      r={point.isBest ? 6 : 4.5}
      stroke={color}
      strokeWidth={2}
      fill={point.isBest ? BEST_COLOR : point.low_data ? 'var(--card)' : PRICE_COLOR}
    />
  )
}

interface PriceChartProps {
  points: ChartPoint[]
  axis: PriceAxis
  priceUnit: string
  unit: string
}

function PriceChart({ points, axis, priceUnit, unit }: PriceChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={points} margin={CHART_MARGIN} syncId={SYNC_ID}>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tick={AXIS_TICK}
          interval="preserveStartEnd"
        />
        <YAxis
          width={Y_AXIS_WIDTH}
          tickLine={false}
          axisLine={false}
          tick={AXIS_TICK}
          domain={axis.domain}
          ticks={axis.ticks}
          //  Dải p25–p75 có thể vượt trục (trục chỉ ôm p25/p75 + bình quân, có nới) — cắt
          //  gọn trong khung thay vì để recharts tự nới trục theo giá trị ngoài cùng.
          allowDataOverflow
          tickFormatter={(value: number) => formatUnitPrice(value)}
        />
        <Tooltip
          wrapperStyle={{ outline: 'none' }}
          cursor={{ stroke: 'var(--border)' }}
          content={<PeriodTooltip priceUnit={priceUnit} unit={unit} />}
        />
        <Area
          dataKey="band"
          stroke="none"
          fill={PRICE_COLOR}
          fillOpacity={0.15}
          connectNulls={false}
          isAnimationActive={false}
          activeDot={false}
        />
        <Line
          dataKey="wavg"
          stroke={PRICE_COLOR}
          strokeWidth={2}
          connectNulls={false}
          isAnimationActive={false}
          dot={(props) => renderPriceDot(props)}
          activeDot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

function QuantityChart({ points }: { points: ChartPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={150}>
      <BarChart data={points} margin={CHART_MARGIN} syncId={SYNC_ID}>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tick={AXIS_TICK}
          interval="preserveStartEnd"
        />
        <YAxis
          width={Y_AXIS_WIDTH}
          tickLine={false}
          axisLine={false}
          tick={AXIS_TICK}
          tickFormatter={(value: number) => formatCompactQuantity(value)}
        />
        {/*  Ô số liệu đầy đủ hiện ở biểu đồ GIÁ (hai biểu đồ chung `syncId`) — ở đây chỉ
             tô vệt kỳ đang trỏ, không bật thêm ô thứ hai trùng nội dung. */}
        <Tooltip
          wrapperStyle={{ outline: 'none' }}
          cursor={{ fill: 'var(--row-hover)' }}
          content={() => null}
        />
        <Bar dataKey="qty" radius={[3, 3, 0, 0]} maxBarSize={28} isAnimationActive={false}>
          {points.map((point) => (
            <Cell key={point.period} fill={point.isBest ? BEST_COLOR : QTY_COLOR} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/** "p25 – p75", hoặc gạch ngang khi kỳ không có giá. */
function formatCommonRange(point: Pick<ChartPoint, 'p25' | 'p75'>): string {
  if (typeof point.p25 !== 'number' || typeof point.p75 !== 'number') return '—'
  return `${formatUsd(point.p25)} – ${formatUsd(point.p75)}`
}

interface PeriodTooltipProps {
  active?: boolean
  payload?: { payload?: unknown }[]
  priceUnit: string
  unit: string
}

/** Ô rê chuột: đủ số liệu của MỘT kỳ — kỳ, bình quân, khoảng phổ biến, thấp, cao, số dòng, lượng. */
function PeriodTooltip({ active, payload, priceUnit, unit }: PeriodTooltipProps) {
  const point = payload?.[0]?.payload as ChartPoint | undefined
  if (!active || !point) return null
  return (
    <div className="min-w-52 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      <p className="mb-1 text-sm font-semibold">
        {point.label}
        {point.isBest && <span className="ml-1.5 font-normal text-success">· kỳ giá tốt nhất</span>}
      </p>
      {point.count === 0 ? (
        <p className="text-muted-foreground">Không có dữ liệu</p>
      ) : (
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 tabular-nums">
          <dt className="text-muted-foreground">BQ gia quyền</dt>
          <dd className="text-right font-semibold">
            {formatUsd(point.wavg)} {priceUnit}
          </dd>
          <dt className="text-muted-foreground">Khoảng phổ biến</dt>
          <dd className="text-right">{formatCommonRange(point)}</dd>
          <dt className="text-muted-foreground">Thấp nhất</dt>
          <dd className="text-right">{formatUsd(point.min)}</dd>
          <dt className="text-muted-foreground">Cao nhất</dt>
          <dd className="text-right">{formatUsd(point.max)}</dd>
          <dt className="text-muted-foreground">Số dòng</dt>
          <dd className="text-right">
            {point.count}
            {point.low_data ? ' (ít dữ liệu)' : ''}
          </dd>
          <dt className="text-muted-foreground">Lượng</dt>
          <dd className="text-right">
            {formatQuantity(point.qty) || '0'} {unit}
          </dd>
        </dl>
      )}
    </div>
  )
}
