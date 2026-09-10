import {
  Banknote,
  ChartColumn,
  Coffee,
  CreditCard,
  ExternalLink,
  PlugZap,
  ReceiptText,
  RefreshCw,
} from 'lucide-react'
import { useMemo } from 'react'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ColumnChart } from '@/shared/ui/column-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import { CoffeeBlock } from '../components/coffee-block'
import { usePosDashboard } from '../hooks/use-coffee'
import type { PosDashboard } from '../types/coffee'

/** Trục Y biểu đồ: rút gọn 1.210.000 → "1,2 tr", 535.000 → "535k". */
function shortMoney(value: number): string {
  if (value >= 1_000_000) {
    const tr = value / 1_000_000
    return `${(Math.round(tr * 10) / 10).toLocaleString('vi-VN')} tr`
  }
  if (value >= 1_000) return `${Math.round(value / 1_000)}k`
  return String(value)
}

/**
 * Quản lý POS (chỉ-ĐỌC, doc 09 §12): số của quầy đọc TRỰC TIẾP từ POS365 lúc mở
 * màn — không ghi gì, không đụng sổ điểm. Sổ điểm/đối soát nằm ở màn riêng.
 */
export function PosDashboardPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = usePosDashboard()

  const columns = useMemo<DataTableColumn<PosDashboard['recent'][number]>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã bill',
        width: 150,
        hideable: false,
        cell: (row) => (
          <span className={cn('font-mono text-sm', row.is_voided && 'line-through opacity-60')}>
            {row.code}
          </span>
        ),
      },
      {
        key: 'time',
        header: 'Thời gian',
        width: 150,
        cell: (row) => <span className="tabular-nums">{row.time.slice(0, 16)}</span>,
      },
      {
        key: 'partner_name',
        header: 'Khách',
        width: 200,
        cell: (row) => row.partner_name || <span className="text-muted-foreground">—</span>,
      },
      {
        key: 'method',
        header: 'Phương thức',
        width: 150,
        cell: (row) => (
          <Badge variant={row.is_points ? 'default' : 'outline'}>{row.method}</Badge>
        ),
      },
      {
        key: 'total',
        header: 'Tổng tiền',
        width: 130,
        align: 'right',
        cell: (row) => (
          <span className={cn('font-medium tabular-nums', row.is_voided && 'line-through opacity-60')}>
            {formatMoney(row.total)}
          </span>
        ),
      },
      {
        key: 'is_voided',
        header: 'Trạng thái',
        width: 110,
        cell: (row) =>
          row.is_voided ? (
            <Badge variant="destructive">Đã hủy</Badge>
          ) : (
            <Badge variant="outline">Hoàn tất</Badge>
          ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill className="gap-6">
      <PageHeader
        title="Quản lý POS"
        description="Số liệu quầy đọc trực tiếp từ POS365 — chỉ xem; sổ điểm và đối soát nằm ở màn «Sổ điểm & đối soát»."
        actions={
          <>
            <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
              <RefreshCw className={cn('size-4', isFetching && 'animate-spin')} />
              Làm mới
            </Button>
            {data?.store_url && (
              <Button asChild>
                {/*  Mở trang quản lý gốc của POS365 — việc SỬA (menu, giá, nhân
                    viên quầy) làm bên đó, màn này cố ý không ôm. */}
                <a href={data.store_url} target="_blank" rel="noreferrer">
                  <ExternalLink className="size-4" />
                  Mở POS365
                </a>
              </Button>
            )}
          </>
        }
      />

      {isError ? (
        <Card className="flex flex-col items-center gap-3 p-10 text-center">
          <PlugZap className="size-10 text-muted-foreground" />
          <div className="font-medium">Không đọc được từ POS365</div>
          <p className="max-w-md text-sm text-muted-foreground">{extractErrorMessage(error)}</p>
        </Card>
      ) : (
        <>
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              icon={ReceiptText}
              label="Đơn hôm nay"
              value={data?.today.orders ?? 0}
              hint={data?.today.voided ? `${data.today.voided} đơn đã hủy` : undefined}
              tone={data?.today.voided ? 'warning' : undefined}
              loading={isLoading}
            />
            <StatCard
              icon={Banknote}
              label="Doanh thu hôm nay"
              value={formatMoney(data?.today.revenue ?? 0)}
              hint={`Tiền mặt ${formatMoney(data?.today.cash ?? 0)}`}
              loading={isLoading}
            />
            <StatCard
              icon={Coffee}
              label="Trừ điểm hôm nay"
              value={formatMoney(data?.today.points ?? 0)}
              hint="Đơn nhân viên trả bằng điểm"
              loading={isLoading}
            />
            <StatCard
              icon={CreditCard}
              label="Tài khoản khác hôm nay"
              value={formatMoney(data?.today.account ?? 0)}
              hint="Chuyển khoản / ví điện tử"
              loading={isLoading}
            />
          </div>

          <CoffeeBlock icon={ChartColumn} title="Doanh thu 7 ngày gần nhất">
            <ColumnChart data={data?.by_day ?? []} height={240} unit="đ" formatValue={shortMoney} />
          </CoffeeBlock>

          <CoffeeBlock
            icon={ReceiptText}
            title="Đơn gần đây"
            className="flex min-h-0 flex-1 flex-col"
          >
            <DataTable
              columns={columns}
              rows={data?.recent ?? []}
              getRowId={(row) => row.pos_order_id}
              storageKey="coffee.pos-dashboard"
              fillHeight
              isLoading={isLoading}
              emptyMessage="Chưa có đơn nào trong 7 ngày gần nhất."
            />
          </CoffeeBlock>
        </>
      )}
    </PageContainer>
  )
}
