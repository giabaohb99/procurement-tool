import { useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Card } from '@/shared/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatPercent, formatQuantity } from '@/shared/utils/format-money'
import { useShippingDetail } from '../hooks/use-purchase-report'
import { ReportMetricTable } from './report-metric-table'
import {
  nextSort,
  SHIPPING_METRICS,
  type MatrixRow,
  type ReportSort,
  type ShippingDetailRow,
} from '../types/purchase-report'

const ALL = 'all'

/** Dòng chi tiết không có id — ghép khóa từ số trang + vị trí để `DataTable` phân biệt. */
type DetailRow = ShippingDetailRow & { rowKey: string }

interface ReportShippingTabProps {
  rows: MatrixRow[]
  /** `'all'` = tổng cả năm, `'YYYY-MM'` = riêng tháng đó. */
  period: string
  periodLabel: string
  year: string
  companyId?: string
  isLoading?: boolean
}

/**
 * Tab Chi phí vận chuyển: bảng theo ĐƠN VỊ VẬN CHUYỂN (từ ma trận có sẵn) rồi
 * bảng CHI TIẾT theo từng dòng nhận hàng.
 *
 * Bảng chi tiết phân trang phía SERVER: một năm có thể vài nghìn dòng nhận
 * hàng, tải hết về rồi cắt ở trình duyệt là treo trang.
 */
export function ReportShippingTab({
  rows,
  period,
  periodLabel,
  year,
  companyId,
  isLoading = false,
}: ReportShippingTabProps) {
  const [sort, setSort] = useState<ReportSort | null>(null)
  const [carrier, setCarrier] = useState(ALL)
  const [month, setMonth] = useState(ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([carrier, month, year, companyId])

  const { data, isLoading: isDetailLoading, isError } = useShippingDetail(
    {
      year,
      company_id: companyId,
      carrier: carrier === ALL ? undefined : carrier,
      month: month === ALL ? undefined : month,
      page,
      page_size: pageSize,
    },
    true,
  )

  const detailRows = useMemo<DetailRow[]>(
    () => (data?.items ?? []).map((row, index) => ({ ...row, rowKey: `${page}-${index}` })),
    [data?.items, page],
  )

  const columns = useMemo<DataTableColumn<DetailRow>[]>(
    () => [
      {
        key: 'carrier',
        header: 'Đơn vị vận chuyển',
        width: 200,
        hideable: false,
        // Bảng 11 cột: ghim tên đơn vị vận chuyển để cuộn tới cột tiền vẫn biết
        // đang xem chi phí của ai.
        defaultPinned: true,
        cell: (row) => (
          <span className="truncate font-medium" title={row.carrier}>
            {row.carrier || '—'}
          </span>
        ),
      },
      { key: 'month', header: 'Tháng', width: 100, cell: (row) => row.month || '—' },
      {
        key: 'product_code',
        header: 'Mã vật tư bao bì / nguyên liệu',
        width: 180,
        cell: (row) => row.product_code || '—',
      },
      { key: 'misa_code', header: 'Mã MISA', width: 140, cell: (row) => row.misa_code || '—' },
      { key: 'invoice_no', header: 'Số hóa đơn', width: 150, cell: (row) => row.invoice_no || '—' },
      {
        key: 'received_date',
        header: 'Ngày nhận',
        width: 120,
        cell: (row) => formatDate(row.received_date) || '—',
      },
      {
        key: 'qty_order',
        header: 'Số lượng đặt',
        width: 130,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatQuantity(row.qty_order)}</span>,
      },
      {
        key: 'qty_received',
        header: 'Số lượng nhận',
        width: 130,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatQuantity(row.qty_received)}</span>,
      },
      {
        key: 'order_amount',
        header: 'Thành tiền đơn hàng',
        width: 170,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatMoney(row.order_amount)}</span>,
      },
      {
        key: 'ship_amount',
        header: 'Thành tiền vận chuyển',
        width: 180,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatMoney(row.ship_amount)}</span>,
      },
      {
        key: 'rate',
        header: 'Tỷ lệ',
        width: 100,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatPercent(row.rate)}</span>,
      },
    ],
    [],
  )

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-4">
        <h3 className="mb-3 text-sm font-semibold text-navy dark:text-foreground">
          Chi phí vận chuyển theo đơn vị vận chuyển — {periodLabel}{' '}
          <span className="font-normal text-muted-foreground">
            (Tỷ lệ = Chi phí vận chuyển / Giá trị đơn hàng)
          </span>
        </h3>
        {isLoading ? (
          <p className="py-6 text-center text-sm text-muted-foreground">Đang tải…</p>
        ) : (
          <ReportMetricTable
            rows={rows}
            metrics={SHIPPING_METRICS}
            period={period}
            nameLabel="Đơn vị vận chuyển"
            nameWidth={200}
            sort={sort}
            onSort={(key) => setSort((current) => nextSort(current, key))}
          />
        )}
      </Card>

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <h3 className="mb-3 text-sm font-semibold text-navy dark:text-foreground">
          Chi tiết theo đơn hàng
        </h3>
        <DataTable
          columns={columns}
          rows={detailRows}
          getRowId={(row) => row.rowKey}
          isLoading={isDetailLoading}
          isError={isError}
          emptyMessage={
            carrier !== ALL || month !== ALL
              ? 'Không có dòng khớp bộ lọc.'
              : 'Chưa có chi phí vận chuyển.'
          }
          storageKey="procurement.purchase-report.shipping"
          //  Bộ lọc của BẢNG này nằm ở state cục bộ chứ không lên URL, nên phải
          //  tự khai. Cố ý không đụng tới pháp nhân / kỳ / năm: đó là bộ lọc của
          //  cả trang báo cáo, nằm ở đầu trang chứ không thuộc bảng này.
          filtersActive={carrier !== ALL || month !== ALL}
          onResetFilters={() => {
            setCarrier(ALL)
            setMonth(ALL)
          }}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng',
          }}
          toolbar={
            <>
              <Select value={carrier} onValueChange={setCarrier}>
                <SelectTrigger className="w-56">
                  <SelectValue placeholder="Đơn vị vận chuyển" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả đơn vị vận chuyển</SelectItem>
                  {(data?.carriers ?? []).map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={month} onValueChange={setMonth}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Tháng" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả tháng</SelectItem>
                  {(data?.months ?? []).map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </div>
  )
}
