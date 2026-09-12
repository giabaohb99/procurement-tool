import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import { useMemo, type CSSProperties } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney, formatPercent } from '@/shared/utils/format-money'
import {
  isWarnRow,
  metricValue,
  NAME_SORT_KEY,
  type MatrixRow,
  type ReportMetric,
  type ReportSort,
} from '../types/purchase-report'

/**
 * Nền dòng cảnh báo.
 *
 * Pha bằng `color-mix` chứ không dùng `bg-destructive/5`: hai ô đầu dòng được
 * GHIM, phần bảng cuộn ngang chạy ở dưới chúng — nền có alpha là lộ chữ xuyên
 * qua. Pha với `--card` nên tự đúng cả ở giao diện tối.
 */
const WARN_ROW_STYLE: CSSProperties = {
  backgroundColor: 'color-mix(in oklab, var(--destructive) 8%, var(--card))',
}

interface ReportMetricTableProps {
  rows: MatrixRow[]
  metrics: ReportMetric[]
  /** `'all'` = tổng cả năm, `'YYYY-MM'` = riêng tháng đó. */
  period: string
  nameLabel: string
  /** Chỉ số quyết định dòng có bị tô đỏ hay không — thường là `rate`. */
  warnMetric?: string
  /** Bề rộng cột tên: tên NCC dài hơn tên bộ phận nhiều. */
  nameWidth?: number
  /** Bỏ trống cả hai = bảng không sắp xếp được (bản in). */
  sort?: ReportSort | null
  onSort?: (key: string) => void
  className?: string
}

/**
 * Bảng báo cáo gọn: dòng = đối tượng, cột = chỉ số.
 *
 * Không dùng `DataTable` được: cột ở đây do dữ liệu quyết (mỗi tab một bộ chỉ
 * số), lại cần sắp xếp tại chỗ trên toàn bộ dòng đã tải — `DataTable` chưa có
 * sắp xếp và cũng không phân trang bộ số liệu này (báo cáo trả trọn một lần).
 *
 * Trạng thái sắp xếp nằm ở component CHA để chế độ xem "Dọc" (12 khối tháng)
 * sắp cùng một kiểu ở mọi khối, thay vì mỗi bảng một kiểu.
 */
export function ReportMetricTable({
  rows,
  metrics,
  period,
  nameLabel,
  warnMetric,
  nameWidth = 160,
  sort = null,
  onSort,
  className,
}: ReportMetricTableProps) {
  const isMobile = useIsMobile()
  const sorted = useMemo(() => {
    if (!sort) return rows
    const direction = sort.dir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      if (sort.key === NAME_SORT_KEY) {
        return direction * String(a.key).localeCompare(String(b.key), 'vi')
      }
      return direction * (metricValue(a, sort.key, period) - metricValue(b, sort.key, period))
    })
  }, [rows, sort, period])

  //  ⚠️ **Khổ điện thoại bày THẺ, không bày bảng thu nhỏ.** Ở chế độ «Dọc» màn
  //  này dựng tới MƯỜI bảng (một tổng năm + chín tháng), mỗi bảng lặp lại đúng
  //  hàng tiêu đề «# · Nhà cung cấp · Số lần giao dịch» và một thanh cuộn ngang
  //  riêng, còn cột tên thì bị bóp tới mức ba dòng «CÔNG TY TNHH …» xếp chồng.
  //  Đọc ra là một bức tường chữ lặp, mà vẫn phải kéo ngang mới thấy hai chỉ số
  //  còn lại. Thẻ thì bày ĐỦ tên trên một dòng chảy và mọi chỉ số nằm ngay dưới
  //  — hết cuộn ngang, hết cắt tên, hết chín hàng tiêu đề.
  //
  //  Sắp xếp không mất theo: `ReportMatrixTab` dựng MỘT dải nút sắp xếp cho cả
  //  tab (xem `MobileSortBar`), thay cho chín hàng tiêu đề bấm được.
  if (isMobile) {
    return (
      <MetricCardList rows={sorted} metrics={metrics} period={period} warnMetric={warnMetric} />
    )
  }

  return (
    <Table className={cn('min-w-[480px]', className)}>
      <TableHeader className="bg-muted">
        <TableRow className="bg-muted hover:bg-muted">
          <TableHead className="sticky left-0 z-20 w-12 bg-inherit">#</TableHead>
          <TableHead
            className="sticky left-12 z-20 bg-inherit"
            style={{ width: nameWidth, minWidth: nameWidth }}
          >
            <SortButton
              label={nameLabel}
              sortKey={NAME_SORT_KEY}
              sort={sort}
              onSort={onSort}
            />
          </TableHead>
          {metrics.map((metric) => (
            <TableHead key={metric.key} className="text-right">
              <SortButton
                label={metric.label}
                sortKey={metric.key}
                sort={sort}
                onSort={onSort}
                align="right"
              />
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>

      <TableBody>
        {sorted.length === 0 && (
          <TableRow>
            <TableCell
              colSpan={2 + metrics.length}
              className="h-20 text-center text-muted-foreground"
            >
              Không có dữ liệu
            </TableCell>
          </TableRow>
        )}

        {sorted.map((row, index) => {
          const warn = isWarnRow(row, period, warnMetric)
          return (
            <TableRow
              key={row.key || index}
              className={cn('bg-card hover:bg-muted', warn && 'hover:bg-inherit')}
              style={warn ? WARN_ROW_STYLE : undefined}
            >
              <TableCell className="sticky left-0 z-10 w-12 bg-inherit text-muted-foreground">
                {index + 1}
              </TableCell>
              {/*  Nhánh bảng này chỉ chạy từ `md` trở lên (dưới đó đã rẽ sang
                   thẻ), nên cắt một dòng là đủ — cột rộng 160–260px ở đó. */}
              <TableCell
                className="sticky left-12 z-10 truncate bg-inherit font-medium"
                style={{ width: nameWidth, minWidth: nameWidth, maxWidth: nameWidth }}
                title={row.key}
              >
                {row.key}
              </TableCell>
              {metrics.map((metric) => {
                const value = metricValue(row, metric.key, period)
                const isWarnCell = warn && metric.key === warnMetric
                return (
                  <TableCell
                    key={metric.key}
                    className={cn(
                      'text-right tabular-nums',
                      isWarnCell && 'font-semibold text-destructive',
                    )}
                  >
                    {metric.pct ? formatPercent(value) : formatMoney(value)}
                  </TableCell>
                )
              })}
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

/**
 * Danh sách THẺ thay cho bảng ở khổ điện thoại — xem ghi chú ở
 * `ReportMetricTable`.
 *
 * ⚠️ **Mọi dòng đều `px-2`, KHÔNG phải chỉ dòng cảnh báo, và tuyệt đối không
 * bù bằng lề âm.** Nền cảnh báo cần chỗ thở hai bên, nhưng nếu chỉ dòng đó có
 * đệm thì chữ của nó lệch 8px so với các dòng khác — nhìn ra ngay khi cuộn qua.
 * Còn `-mx-2` để tràn ra mép thẻ thì đẩy `scrollWidth` của `<ul>` vượt
 * `clientWidth` 8px, tức đẻ ra một vùng cuộn ngang tí hon ở mỗi khối tháng
 * (đo 12/09/2026: 332 / 324). Cho tất cả cùng thụt vào là xong cả hai.
 */
function MetricCardList({
  rows,
  metrics,
  period,
  warnMetric,
}: {
  rows: MatrixRow[]
  metrics: ReportMetric[]
  period: string
  warnMetric?: string
}) {
  if (rows.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">Không có dữ liệu</p>
  }

  return (
    <ul className="divide-y">
      {rows.map((row, index) => {
        const warn = isWarnRow(row, period, warnMetric)
        return (
          <li
            key={row.key || index}
            className={cn('px-2 py-2.5 first:pt-0', warn && 'rounded-md')}
            style={warn ? WARN_ROW_STYLE : undefined}
          >
            <div className="flex items-start gap-2">
              <span className="w-5 shrink-0 pt-px text-xs tabular-nums text-muted-foreground">
                {index + 1}
              </span>

              <div className="min-w-0 flex-1 space-y-1">
                {/*  Tên KHÔNG cắt: đây là chỗ duy nhất nói dòng này là của ai,
                     mà tên doanh nghiệp Việt Nam phân biệt nhau ở phần đuôi. */}
                <span className="block text-sm font-medium text-foreground">{row.key}</span>

                <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                  {metrics.map((metric) => {
                    const value = metricValue(row, metric.key, period)
                    const isWarnCell = warn && metric.key === warnMetric
                    return (
                      <span key={metric.key}>
                        {metric.label}{' '}
                        <b
                          className={cn(
                            'tabular-nums text-foreground',
                            isWarnCell && 'text-destructive',
                          )}
                        >
                          {metric.pct ? formatPercent(value) : formatMoney(value)}
                        </b>
                      </span>
                    )
                  })}
                </div>
              </div>
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function SortButton({
  label,
  sortKey,
  sort,
  onSort,
  align = 'left',
}: {
  label: string
  sortKey: string
  sort: ReportSort | null
  onSort?: (key: string) => void
  align?: 'left' | 'right'
}) {
  if (!onSort) return <span>{label}</span>

  const active = sort?.key === sortKey
  // Cột nào cũng có icon (mờ) để thấy là bấm được; cột đang sắp thì mũi tên rõ.
  const Icon = !active ? ArrowUpDown : sort?.dir === 'asc' ? ArrowUp : ArrowDown

  return (
    <button
      type="button"
      onClick={() => onSort(sortKey)}
      className={cn(
        'inline-flex w-full items-center gap-1 whitespace-nowrap',
        align === 'right' ? 'justify-end' : 'justify-start',
        active ? 'text-foreground' : 'hover:text-foreground',
      )}
    >
      {label}
      <Icon className={cn('size-3.5 shrink-0', !active && 'opacity-40')} />
    </button>
  )
}
