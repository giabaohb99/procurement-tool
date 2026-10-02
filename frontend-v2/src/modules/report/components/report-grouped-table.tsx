import { useMemo, useState } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Card } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'

import {
  buildReportTableRows,
  REPORT_TOTAL_ROW_KEY,
  type ReportTableRow,
} from '../utils/build-report-table-rows'
import { orderVisibleReportMetrics } from '../utils/order-visible-report-metrics'
import type {
  ReportCompareMode,
  ReportGroupRow,
  ReportMeta,
  ReportMetricValues,
} from '../types/report-analytics'
import { ReportGroupBySelect } from './report-group-by-select'
import { ReportMetricValueCell } from './report-metric-value-cell'

interface ReportGroupedTableProps {
  meta: ReportMeta
  /** `ReportPageConfig.kpis` — đứng TRƯỚC trong bảng, đúng thứ tự, và là bộ cột HIỆN SẴN mặc định. */
  kpis: string[]
  totals: { current: ReportMetricValues; compare: ReportMetricValues | null }
  groups: ReportGroupRow[]
  compare: ReportCompareMode
  groupBy: string
  onGroupByChange: (key: string) => void
  isLoading: boolean
  isError: boolean
  /** `report.<slug>.v4` — nhớ bố cục cột riêng cho từng báo cáo (`docs/ui/table.md`). */
  storageKey: string
}

/**
 * Bảng "Xem theo" của trang báo cáo — dòng Tổng ghim đầu (`buildReportTableRows`),
 * MỖI CHỈ SỐ MỘT CỘT DUY NHẤT (`ReportMetricValueCell`). Mặc định chỉ hiện các
 * cột thuộc `kpis` của trang (đúng thứ tự); chỉ số khác vẫn bật được qua menu
 * "Cột" — tránh ép cuộn ngang ở khổ 1280px cho một báo cáo bảy tám chỉ số.
 *
 * Sắp xếp chạy Ở ĐÂY (state cục bộ), KHÔNG qua `sortBy/sortDir` như bảng
 * server-side thường: dữ liệu nhóm của một báo cáo tối đa vài trăm dòng, không
 * phân trang, gọi lại API chỉ để đổi hướng sắp là phí một lượt gọi.
 */
export function ReportGroupedTable({
  meta,
  kpis,
  totals,
  groups,
  compare,
  groupBy,
  onGroupByChange,
  isLoading,
  isError,
  storageKey,
}: ReportGroupedTableProps) {
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const rows = useMemo(
    () => buildReportTableRows(totals, groups, sortBy, sortDir),
    [totals, groups, sortBy, sortDir],
  )

  const visibleMetrics = useMemo(
    () => orderVisibleReportMetrics(meta.metrics, kpis),
    [meta.metrics, kpis],
  )
  const kpiKeys = useMemo(() => new Set(kpis), [kpis])
  const dimensionLabel = meta.dimensions.find((d) => d.key === groupBy)?.label ?? 'Nhóm'

  const columns = useMemo<DataTableColumn<ReportTableRow>[]>(() => {
    const cols: DataTableColumn<ReportTableRow>[] = [
      {
        key: 'label',
        header: dimensionLabel,
        width: 220,
        minWidth: 180,
        hideable: false,
        defaultPinned: true,
        wrap: true,
        cell: (row) => (
          <span
            className={cn(
              row.isTotal && 'font-semibold',
              !row.isTotal && row.isEmpty && 'text-muted-foreground',
            )}
          >
            {row.label}
          </span>
        ),
      },
    ]

    for (const metric of visibleMetrics) {
      cols.push({
        key: metric.key,
        header: metric.label,
        width: 168,
        minWidth: 150,
        align: 'right',
        sortable: true,
        //  Chỉ số KHÔNG nằm trong `kpis` của trang ẩn sẵn — vẫn bật lại được
        //  qua menu "Cột" (`docs/ui/table.md` §4: chỉ áp cho người CHƯA từng
        //  đụng menu đó, đúng ý "mặc định gọn, tùy chỉnh vẫn còn nguyên").
        defaultHidden: !kpiKeys.has(metric.key),
        cell: (row) => <ReportMetricValueCell row={row} metric={metric} compare={compare} />,
      })
    }

    return cols
  }, [visibleMetrics, kpiKeys, dimensionLabel, compare])

  return (
    <Card className="flex min-h-0 flex-1 flex-col p-4">
      <DataTable
        //  `useTableLayout` (bên trong `DataTable`) quyết định cột nào ẩn sẵn
        //  CHỈ Ở LẦN MOUNT ĐẦU (`useState` khởi tạo một lần) — trước khi có
        //  lượt gọi API đầu tiên, `meta.metrics` rỗng nên `columns` chỉ có
        //  đúng cột nhóm, không cột chỉ số nào để tính `defaultHidden`. Không
        //  đổi `key` thì lúc dữ liệu về, `columns` đổi nhưng state ẩn/hiện đã
        //  chốt cứng theo bộ cột RỖNG đó — mọi cột chỉ số hiện hết, kể cả cột
        //  không nằm trong `kpis`. Đổi `key` đúng MỘT LẦN khi có chỉ số thật
        //  buộc `DataTable` mount lại, tính `defaultHidden` trên bộ cột ĐÚNG.
        key={visibleMetrics.length > 0 ? 'loaded' : 'loading'}
        columns={columns}
        rows={rows}
        getRowId={(row) => row.key}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Kỳ này chưa có dữ liệu để gom nhóm."
        storageKey={storageKey}
        //  `bg-muted` ĐỤC (không alpha) — cột ghim (`label`) lấy `bg-inherit`
        //  từ hàng, nền trong suốt sẽ lộ nội dung đang cuộn ngang bên dưới nó
        //  (bẫy đã ghi ở `docs/ui/table.md` §5, "NỀN HÀNG PHẢI ĐỤC"). `border-b-2`
        //  tách hẳn dòng Tổng khỏi các dòng nhóm ngay dưới nó.
        rowClassName={(row) =>
          row.key === REPORT_TOTAL_ROW_KEY
            ? 'bg-muted font-semibold border-b-2 border-border'
            : undefined
        }
        sortBy={sortBy ?? ''}
        sortDir={sortDir}
        onSortChange={(nextSortBy, nextSortDir) => {
          setSortBy(nextSortBy || null)
          setSortDir(nextSortDir)
        }}
        //  Tiêu đề thẻ + "Xem theo" chèn vào CÙNG hàng với menu "Cột" (và Tải
        //  lại) của chính `DataTable` — một hàng công cụ duy nhất thay vì một
        //  hàng tiêu đề card riêng đứng trên hàng công cụ của bảng.
        toolbar={
          <>
            <h3 className="shrink-0 text-base font-semibold text-navy dark:text-foreground">
              Chi tiết theo {dimensionLabel}
            </h3>
            <ReportGroupBySelect
              dimensions={meta.dimensions}
              value={groupBy}
              onChange={onGroupByChange}
            />
          </>
        }
        //  `toolbar` khác rỗng thì `DataTable` tự vẽ nút "Xóa lọc" theo bộ lọc
        //  suy từ query string — mà query string của TRANG mang cả kỳ/so
        //  sánh/công ty, không phải bộ lọc CỦA riêng bảng này. Tắt hẳn, kẻo
        //  bấm nhầm là xóa sạch bộ lọc của cả trang chỉ vì đang đứng ở bảng.
        filtersActive={false}
      />
    </Card>
  )
}
