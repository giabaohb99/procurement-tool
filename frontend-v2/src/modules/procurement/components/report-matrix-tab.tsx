import { CalendarDays, Columns3, Rows3, Search, Sigma, X } from 'lucide-react'
import { useMemo, useState, type CSSProperties, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatPercent } from '@/shared/utils/format-money'
import { useReportRange } from '../hooks/use-purchase-report'
import {
  ALL_PERIOD,
  isWarnRow,
  metricValue,
  nextSort,
  RATE_METRIC,
  type MatrixRow,
  type ReportMetric,
  type ReportMonth,
  type ReportSort,
} from '../types/purchase-report'
import { ReportMetricTable } from './report-metric-table'

/**
 * Sáu tông xoay vòng cho các cụm cột tháng.
 *
 * Bảng "Ngang" rộng tới 12 tháng × 5 chỉ số; không chia cụm màu thì mắt trượt
 * sang cột tháng bên cạnh lúc nào không biết. Lấy đúng sáu tông của bảng màu tô
 * cột (`COLUMN_COLORS`) cho cả hệ cùng một gam, và pha bằng `color-mix` với nền
 * nguyên bản để ra màu ĐỤC — ô cột tên bị ghim, nền có alpha là lộ phần bảng
 * cuộn ngang phía dưới.
 */
const MONTH_TONES = ['#2563eb', '#16a34a', '#d97706', '#7c3aed', '#dc2626', '#0891b2']

function toneStyle(color: string, part: 'head' | 'cell'): CSSProperties {
  const [ratio, base] = part === 'head' ? ['20%', 'var(--muted)'] : ['8%', 'var(--card)']
  return { backgroundColor: `color-mix(in oklab, ${color} ${ratio}, ${base})` }
}

function monthStyle(index: number, part: 'head' | 'cell'): CSSProperties {
  return toneStyle(MONTH_TONES[index % MONTH_TONES.length], part)
}

/** Cụm "Tổng cả năm" — xám trung tính để tách hẳn khỏi dải màu tháng. */
const TOTAL_HEAD_STYLE: CSSProperties = { backgroundColor: 'var(--muted)' }
const TOTAL_CELL_STYLE: CSSProperties = {
  backgroundColor: 'color-mix(in oklab, var(--chart-neutral) 22%, var(--card))',
}

/** Nền đục cho ô cột tên bị ghim. */
const STICKY_HEAD_STYLE: CSSProperties = { backgroundColor: 'var(--muted)' }
const STICKY_CELL_STYLE: CSSProperties = { backgroundColor: 'var(--card)' }

interface ReportMatrixTabProps {
  rows: MatrixRow[]
  months: ReportMonth[]
  metrics: ReportMetric[]
  nameLabel: string
  title: string
  /** Chú thích ngưỡng cảnh báo, vd "đỏ = tỷ lệ trễ > 30%". Bỏ trống = bảng không tô cảnh báo. */
  warnHint?: string
  /** Nhãn kỳ đang xem, vd "Năm 2026" — dùng cho tiêu đề và bản in. */
  yearLabel: string
  /** Đường dẫn tính realtime theo khoảng ngày, vd `/api/reports/sup-range`. */
  rangeEndpoint: string
  /** Chỉ dùng cho báo cáo yêu cầu: `pyc` | `ycks`. */
  rangeKind?: string
  companyId?: string
  /** Bề rộng cột tên — tên NCC dài hơn tên bộ phận nhiều. */
  nameWidth?: number
  isLoading?: boolean
}

/**
 * Tab báo cáo ma trận (đối tượng × tháng), dùng chung cho NCC / phân loại / nhân
 * sự phụ trách / bộ phận / yêu cầu.
 *
 * Ba chế độ xem:
 *  - **Ngang** — pivot: mỗi đối tượng một dòng, mỗi tháng một cụm cột, cuối cùng
 *    là cụm "Tổng cả năm".
 *  - **Dọc** — khối tổng cả năm rồi lần lượt từng khối tháng (hợp để in / đọc
 *    trên màn hẹp).
 *  - **Khoảng ngày** — gọi backend tính lại theo đúng hai mốc ngày, trả về một
 *    bảng phẳng; lúc này hai chế độ trên tạm ẩn vì số liệu không còn cắt theo
 *    tháng nữa.
 *
 * Khác bản v1 hai chỗ: ô lọc theo tên là ô GÕ (v1 là dropdown chọn đúng một đối
 * tượng — v2 chưa có select tìm kiếm được, mà gõ để lọc còn rộng hơn: gõ vài
 * chữ là ra cả nhóm), và bản in dùng `print:` của Tailwind thay cho hai lớp
 * `screen-only` / `print-only` của v1.
 */
export function ReportMatrixTab({
  rows,
  months,
  metrics,
  nameLabel,
  title,
  warnHint,
  yearLabel,
  rangeEndpoint,
  rangeKind,
  companyId,
  nameWidth = 150,
  isLoading = false,
}: ReportMatrixTabProps) {
  const [view, setView] = useState<'ngang' | 'doc'>('ngang')
  const [rangeFrom, setRangeFrom] = useState('')
  const [rangeTo, setRangeTo] = useState('')
  /** Khoảng ngày ĐÃ bấm "Xem". `null` = đang xem cả năm theo tháng. */
  const [applied, setApplied] = useState<{ from: string; to: string } | null>(null)
  const [keyword, setKeyword] = useState('')
  const [sort, setSort] = useState<ReportSort | null>(null)
  /**
   * Tháng đang hiện. `null` = NGƯỜI DÙNG CHƯA CHỌN TAY, lấy mặc định suy từ
   * `months`. Không thể chốt mặc định một lần lúc dựng component như v1: ở đây
   * `months` về sau react-query nên lần dựng đầu nó còn rỗng, chốt lúc đó là ẩn
   * sạch mọi tháng.
   */
  const [visibleMonths, setVisibleMonths] = useState<Set<string> | null>(null)

  const rangeQuery = useReportRange(
    rangeEndpoint,
    {
      date_from: applied?.from ?? '',
      date_to: applied?.to ?? '',
      company_id: companyId,
      kind: rangeKind,
    },
    applied !== null,
  )

  // Bọc `useMemo` chứ không tính thẳng: `?? []` đẻ mảng mới mỗi lần render, làm
  // `shownRows` phía dưới tính lại liên tục dù dữ liệu không đổi.
  const baseRows = useMemo(
    () => (applied ? (rangeQuery.data ?? []) : rows),
    [applied, rangeQuery.data, rows],
  )
  const shownRows = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return baseRows
    return baseRows.filter((row) => row.key.toLowerCase().includes(needle))
  }, [baseRows, keyword])

  const defaultMonths = useMemo(() => defaultVisibleMonths(months), [months])
  const visible = visibleMonths ?? defaultMonths
  const shownMonths = months.filter((month) => visible.has(month.key))

  // Chỉ tô cảnh báo khi tab có khai ngưỡng — bảng đếm trạng thái yêu cầu không
  // có "tỷ lệ trễ" nào để mà vượt ngưỡng.
  const warnMetric = warnHint ? RATE_METRIC : undefined
  const canApply = !!rangeFrom && !!rangeTo && rangeFrom <= rangeTo

  function toggleMonth(key: string) {
    const next = new Set(visible)
    if (next.has(key)) next.delete(key)
    else next.add(key)
    setVisibleMonths(next)
  }

  function clearRange() {
    setApplied(null)
    setRangeFrom('')
    setRangeTo('')
  }

  function handleSort(key: string) {
    setSort((current) => nextSort(current, key))
  }

  const rangeLabel = applied ? `${formatDate(applied.from)} → ${formatDate(applied.to)}` : yearLabel

  return (
    <div className="flex flex-col gap-3">
      {/* ==== Thanh điều khiển ==== */}
      <div className="flex flex-wrap items-center gap-2 print:hidden">
        {!applied && (
          <div className="inline-flex overflow-hidden rounded-md border">
            <ViewButton
              active={view === 'ngang'}
              icon={<Columns3 className="size-4" />}
              label="Ngang"
              onClick={() => setView('ngang')}
            />
            <ViewButton
              active={view === 'doc'}
              icon={<Rows3 className="size-4" />}
              label="Dọc"
              onClick={() => setView('doc')}
            />
          </div>
        )}

        {!applied && months.length > 0 && (
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="gap-2">
                <CalendarDays className="size-4" />
                Tháng: {shownMonths.length}/{months.length}
              </Button>
            </PopoverTrigger>
            <PopoverContent align="start" className="w-56 p-2">
              <div className="mb-2 flex gap-2 border-b pb-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setVisibleMonths(new Set(months.map((month) => month.key)))}
                >
                  Tất cả
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setVisibleMonths(new Set())}>
                  Bỏ chọn
                </Button>
              </div>
              <div className="max-h-60 space-y-1 overflow-y-auto">
                {months.map((month) => (
                  <label
                    key={month.key}
                    className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-accent"
                  >
                    <Checkbox
                      checked={visible.has(month.key)}
                      onCheckedChange={() => toggleMonth(month.key)}
                    />
                    Tháng {month.label}
                  </label>
                ))}
              </div>
            </PopoverContent>
          </Popover>
        )}

        <div className="ml-auto flex flex-wrap items-center gap-2">
          <div className="relative min-w-48">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder={`Lọc theo ${nameLabel.toLowerCase()}…`}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>

          <DatePicker
            value={rangeFrom}
            onChange={setRangeFrom}
            placeholder="Từ ngày"
            className="w-40"
          />
          <DatePicker value={rangeTo} onChange={setRangeTo} placeholder="Đến ngày" className="w-40" />
          <Button
            variant="secondary"
            disabled={!canApply}
            onClick={() => setApplied({ from: rangeFrom, to: rangeTo })}
          >
            Xem
          </Button>
          {applied && (
            <Button variant="ghost" className="gap-2" onClick={clearRange}>
              <X className="size-4" />
              Xóa lọc
            </Button>
          )}
        </div>
      </div>

      {/* ==== Trên màn hình ==== */}
      <div className="print:hidden">
        {applied ? (
          <Card className="p-4">
            <SectionTitle title={`${title} — ${rangeLabel}`} />
            {rangeQuery.isLoading ? (
              <LoadingLine />
            ) : (
              <ReportMetricTable
                rows={shownRows}
                metrics={metrics}
                period={ALL_PERIOD}
                nameLabel={nameLabel}
                warnMetric={warnMetric}
                nameWidth={nameWidth}
                sort={sort}
                onSort={handleSort}
              />
            )}
          </Card>
        ) : view === 'doc' ? (
          <div className="flex flex-col gap-3">
            <Card className="p-4">
              <SectionTitle
                title={`Tổng cả năm — ${yearLabel}`}
                hint={warnHint}
                icon={<Sigma className="size-4 text-primary" />}
              />
              {isLoading ? (
                <LoadingLine />
              ) : (
                <ReportMetricTable
                  rows={shownRows}
                  metrics={metrics}
                  period={ALL_PERIOD}
                  nameLabel={nameLabel}
                  warnMetric={warnMetric}
                  nameWidth={nameWidth}
                  sort={sort}
                  onSort={handleSort}
                />
              )}
            </Card>

            {shownMonths.map((month, index) => (
              <Card
                key={month.key}
                className="gap-0 overflow-hidden p-0"
                style={{ borderLeft: `4px solid ${MONTH_TONES[index % MONTH_TONES.length]}` }}
              >
                <h3
                  className="px-4 py-3 text-sm font-semibold text-navy dark:text-foreground"
                  style={monthStyle(index, 'head')}
                >
                  Tháng {month.label}
                </h3>
                <div className="p-4">
                  <ReportMetricTable
                    // Tháng nào đối tượng không phát sinh thì bỏ hẳn khỏi khối,
                    // không liệt kê một loạt dòng toàn số 0.
                    rows={shownRows.filter((row) => row.m?.[month.key])}
                    metrics={metrics}
                    period={month.key}
                    nameLabel={nameLabel}
                    warnMetric={warnMetric}
                    nameWidth={nameWidth}
                    sort={sort}
                    onSort={handleSort}
                  />
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="p-4">
            <SectionTitle
              title={`${title} — ${yearLabel}`}
              hint={`phân cụm theo tháng · cuộn ngang · cụm xám = tổng cả năm${
                warnHint ? ` · ${warnHint}` : ''
              }`}
            />
            {isLoading ? (
              <LoadingLine />
            ) : (
              <PivotTable
                rows={shownRows}
                months={shownMonths}
                metrics={metrics}
                nameLabel={nameLabel}
                nameWidth={nameWidth}
                warnMetric={warnMetric}
              />
            )}
          </Card>
        )}
      </div>

      {/* ==== Khi IN: bản tổng hợp một dòng một đối tượng ==== */}
      <div className="hidden print:block">
        <SectionTitle title={`${title} — ${rangeLabel}`} hint="bản tổng hợp" />
        <ReportMetricTable
          rows={shownRows}
          metrics={metrics}
          period={ALL_PERIOD}
          nameLabel={nameLabel}
          warnMetric={warnMetric}
          nameWidth={nameWidth}
        />
      </div>
    </div>
  )
}

/** Pivot đối tượng (dòng) × tháng (cụm cột) + cụm "Tổng cả năm" ở cuối. */
function PivotTable({
  rows,
  months,
  metrics,
  nameLabel,
  nameWidth,
  warnMetric,
}: {
  rows: MatrixRow[]
  months: ReportMonth[]
  metrics: ReportMetric[]
  nameLabel: string
  nameWidth: number
  warnMetric?: string
}) {
  return (
    <Table className="min-w-[520px]">
      <TableHeader className="bg-muted">
        <TableRow className="hover:bg-muted">
          <TableHead
            rowSpan={2}
            className="sticky left-0 z-20 align-bottom"
            style={{ ...STICKY_HEAD_STYLE, width: nameWidth, minWidth: nameWidth }}
          >
            {nameLabel}
          </TableHead>
          {months.map((month, index) => (
            <TableHead
              key={month.key}
              colSpan={metrics.length}
              className="border-l text-center"
              style={monthStyle(index, 'head')}
            >
              Tháng {month.label}
            </TableHead>
          ))}
          <TableHead
            colSpan={metrics.length}
            className="border-l-2 text-center text-navy dark:text-foreground"
            style={TOTAL_HEAD_STYLE}
          >
            Tổng cả năm
          </TableHead>
        </TableRow>
        <TableRow className="hover:bg-muted">
          {months.map((month, index) =>
            metrics.map((metric, metricIndex) => (
              <TableHead
                key={`${month.key}-${metric.key}`}
                className={cn('text-right text-xs font-normal', metricIndex === 0 && 'border-l')}
                style={monthStyle(index, 'head')}
              >
                {metric.label}
              </TableHead>
            )),
          )}
          {metrics.map((metric, metricIndex) => (
            <TableHead
              key={`total-${metric.key}`}
              className={cn('text-right text-xs font-semibold', metricIndex === 0 && 'border-l-2')}
              style={TOTAL_HEAD_STYLE}
            >
              {metric.label}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>

      <TableBody>
        {rows.length === 0 && (
          <TableRow>
            <TableCell
              colSpan={1 + (months.length + 1) * metrics.length}
              className="h-20 text-center text-muted-foreground"
            >
              Không có dữ liệu
            </TableCell>
          </TableRow>
        )}

        {rows.map((row) => {
          const totalWarn = isWarnRow(row, ALL_PERIOD, warnMetric)
          return (
            <TableRow key={row.key}>
              <TableCell
                className="sticky left-0 z-10 truncate font-medium"
                style={{
                  ...STICKY_CELL_STYLE,
                  width: nameWidth,
                  minWidth: nameWidth,
                  maxWidth: nameWidth,
                }}
                title={row.key}
              >
                {row.key}
              </TableCell>

              {months.map((month, index) => {
                const hasData = !!row.m?.[month.key]
                const warn = isWarnRow(row, month.key, warnMetric)
                return metrics.map((metric, metricIndex) => (
                  <TableCell
                    key={`${month.key}-${metric.key}`}
                    className={cn(
                      'text-right tabular-nums',
                      metricIndex === 0 && 'border-l',
                      // Tháng không phát sinh vẫn ghi 0 nhưng làm mờ đi, để mắt
                      // phân biệt được "bằng 0" với "không có giao dịch nào".
                      !hasData && 'text-muted-foreground/50',
                      warn && metric.key === warnMetric && 'font-semibold text-destructive',
                    )}
                    style={monthStyle(index, 'cell')}
                  >
                    {formatCell(metric, metricValue(row, metric.key, month.key))}
                  </TableCell>
                ))
              })}

              {metrics.map((metric, metricIndex) => (
                <TableCell
                  key={`total-${metric.key}`}
                  className={cn(
                    'text-right font-semibold tabular-nums',
                    metricIndex === 0 && 'border-l-2',
                    totalWarn && metric.key === warnMetric && 'text-destructive',
                  )}
                  style={TOTAL_CELL_STYLE}
                >
                  {formatCell(metric, metricValue(row, metric.key, ALL_PERIOD))}
                </TableCell>
              ))}
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

function formatCell(metric: ReportMetric, value: number): string {
  return metric.pct ? formatPercent(value) : formatMoney(value)
}

function ViewButton({
  active,
  icon,
  label,
  onClick,
}: {
  active: boolean
  icon: ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'inline-flex h-9 items-center gap-1.5 px-3 text-sm font-medium transition-colors',
        active ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent',
      )}
    >
      {icon}
      {label}
    </button>
  )
}

function SectionTitle({
  title,
  hint,
  icon,
}: {
  title: string
  hint?: string
  icon?: ReactNode
}) {
  return (
    <h3 className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-navy dark:text-foreground">
      {icon}
      {title}
      {hint && <span className="font-normal text-muted-foreground">({hint})</span>}
    </h3>
  )
}

function LoadingLine() {
  return <p className="py-6 text-center text-sm text-muted-foreground">Đang tải…</p>
}

/**
 * Mặc định chỉ hiện các tháng TỚI tháng hiện tại — tháng sau chưa phát sinh, để
 * nguyên là bảng thừa mấy cụm cột rỗng. Người dùng vẫn tick lại được.
 */
function defaultVisibleMonths(months: ReportMonth[]): Set<string> {
  const now = new Date()
  const current = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  return new Set(months.filter((month) => month.key <= current).map((month) => month.key))
}
