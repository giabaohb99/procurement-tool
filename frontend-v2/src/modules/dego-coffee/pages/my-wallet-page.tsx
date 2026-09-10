import { Coffee, History, TrendingDown, TrendingUp, Wallet } from 'lucide-react'
import { useMemo } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { cn } from '@/shared/utils/cn'
import { CoffeeBlock } from '../components/coffee-block'
import { useMyWallet } from '../hooks/use-coffee'
import type { CoffeeLedgerRow } from '../types/coffee'
import { formatPoints, formatSignedPoints } from '../utils/format-points'

/** Kỳ "YYYYMM" → "MM/YYYY" cho người đọc. */
function formatPeriod(period: string): string {
  return period.length === 6 ? `${period.slice(4)}/${period.slice(0, 4)}` : period
}

/**
 * Ví điểm của tôi (C-02) — số dư + được cấp/đã tiêu kỳ này + lịch sử.
 * Chỉ cần đăng nhập; backend tự lấy `employee_id` của người gọi.
 */
export function MyWalletPage() {
  const { data, isLoading, isError } = useMyWallet()

  const columns = useMemo<DataTableColumn<CoffeeLedgerRow>[]>(
    () => [
      {
        key: 'created_at',
        header: 'Thời điểm',
        width: 160,
        cell: (row) => <span className="tabular-nums">{row.created_at.slice(0, 16)}</span>,
      },
      {
        key: 'type',
        header: 'Loại',
        width: 150,
        cell: (row) => <Badge variant="outline">{row.type_label}</Badge>,
      },
      {
        key: 'points',
        header: 'Điểm',
        width: 120,
        align: 'right',
        cell: (row) => (
          <span
            className={cn(
              'font-medium tabular-nums',
              row.points < 0 ? 'text-destructive' : 'text-emerald-600 dark:text-emerald-400',
            )}
          >
            {formatSignedPoints(row.points)}
          </span>
        ),
      },
      {
        key: 'reason',
        header: 'Diễn giải',
        width: 320,
        cell: (row) => (
          <div className="min-w-0">
            <span className="truncate">{row.reason}</span>
            {row.pos_code && (
              <span className="ml-1.5 font-mono text-xs text-muted-foreground">{row.pos_code}</span>
            )}
          </div>
        ),
      },
      {
        key: 'period',
        header: 'Kỳ',
        width: 90,
        cell: (row) => <span className="tabular-nums">{formatPeriod(row.period)}</span>,
      },
    ],
    [],
  )

  //  Chưa được gán vào chương trình: nói rõ thay vì bày một bảng trống trơ.
  if (!isLoading && !isError && data && data.member === null) {
    return (
      <PageContainer>
        <PageHeader title="Ví điểm của tôi" />
        <Card className="flex flex-col items-center gap-3 p-10 text-center">
          <Coffee className="size-10 text-muted-foreground" />
          <div className="font-medium">Bạn chưa thuộc chương trình điểm cà phê</div>
          <p className="max-w-md text-sm text-muted-foreground">
            Liên hệ phòng Nhân sự để được gán cấp phúc lợi. Sau khi được gán, điểm sẽ tự cấp
            vào đầu mỗi tháng và bạn tiêu tại quầy bằng phương thức «Trừ điểm» trên POS365.
          </p>
        </Card>
      </PageContainer>
    )
  }

  return (
    //  gap-6: các block giãn nhau rõ ràng (yêu cầu 08/09 — trước đó thẻ dính sát).
    <PageContainer fill className="gap-6">
      <PageHeader
        title="Ví điểm của tôi"
        description={
          data?.period
            ? `Kỳ ${formatPeriod(data.period)} — điểm reset và cấp lại vào đầu mỗi tháng, không cộng dồn.`
            : undefined
        }
      />

      <div className="grid gap-5 sm:grid-cols-3">
        <Card className="flex items-center gap-4 p-5">
          <div className="rounded-md bg-amber-500/10 p-2.5 text-amber-600 dark:text-amber-400">
            <Wallet className="size-6" />
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Số dư hiện tại</div>
            <div
              className={cn(
                'text-3xl font-semibold tabular-nums',
                !data?.member?.unlimited && (data?.balance ?? 0) < 0 && 'text-destructive',
              )}
            >
              {/*  Cấp vô hạn (Chúa tể HĐQT): ký hiệu ∞ cùng cỡ với con số của
                  người thường — không cấp/không chặn, sổ vẫn ghi tiêu. */}
              {data?.member?.unlimited ? '∞' : formatPoints(data?.balance)}
            </div>
          </div>
        </Card>
        <Card className="flex items-center gap-4 p-5">
          <div className="rounded-md bg-emerald-500/10 p-2.5 text-emerald-600 dark:text-emerald-400">
            <TrendingUp className="size-6" />
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Được cấp kỳ này</div>
            <div className="text-2xl font-semibold tabular-nums">{formatPoints(data?.granted)}</div>
          </div>
        </Card>
        <Card className="flex items-center gap-4 p-5">
          <div className="rounded-md bg-rose-500/10 p-2.5 text-rose-600 dark:text-rose-400">
            <TrendingDown className="size-6" />
          </div>
          <div>
            <div className="text-sm text-muted-foreground">Đã tiêu kỳ này</div>
            <div className="text-2xl font-semibold tabular-nums">{formatPoints(data?.spent)}</div>
          </div>
        </Card>
      </div>

      <CoffeeBlock
        icon={History}
        title="Lịch sử giao dịch"
        className="flex min-h-0 flex-1 flex-col"
      >
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          getRowId={(row) => row.id}
          storageKey="coffee.my-wallet"
          fillHeight
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có giao dịch nào."
        />
      </CoffeeBlock>
    </PageContainer>
  )
}
