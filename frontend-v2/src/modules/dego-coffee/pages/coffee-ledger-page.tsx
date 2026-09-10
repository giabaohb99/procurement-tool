import { BookText, CalendarCheck, FileQuestion, History, PenLine, Play, Scale } from 'lucide-react'
import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'

import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { AdjustDialog } from '../components/adjust-dialog'
import { CoffeeBlock } from '../components/coffee-block'
import { ResetApproveDialog } from '../components/reset-approve-dialog'
import { ResolveOrderDialog } from '../components/resolve-order-dialog'
import {
  useCoffeeLedger,
  useCoffeeMeta,
  usePosOrders,
  useRunSync,
  useSyncRuns,
} from '../hooks/use-coffee'
import type { CoffeeLedgerRow, PosOrderRow, PosSyncRun } from '../types/coffee'
import { formatPoints, formatSignedPoints } from '../utils/format-points'

/** Kết quả đối chiếu D-04 nằm trong `detail` (JSON) của lần chạy RECONCILE gần nhất. */
interface ReconcileDetail {
  mismatches: { day: string; pos: number; ledger: number; diff: number }[]
  unmatched: number
}

const RECONCILE_KIND = 4
const SYNC_STATUS_VARIANT: Record<number, 'default' | 'outline' | 'destructive'> = {
  1: 'outline', // đang chạy
  2: 'default', // thành công
  3: 'destructive', // lỗi
  4: 'outline', // bỏ qua (HARD_OFF)
}

/** Sổ điểm & đối soát — 4 tab: Sổ cái · Đơn chưa khớp · Đối chiếu · Nhật ký đồng bộ. */
export function CoffeeLedgerPage() {
  const { can } = usePermission()
  const [adjusting, setAdjusting] = useState(false)
  const [approving, setApproving] = useState(false)
  const [resolving, setResolving] = useState<PosOrderRow | null>(null)

  return (
    <PageContainer fill className="gap-6">
      <PageHeader
        title="Sổ điểm & đối soát"
        description="Sổ cái chỉ ghi thêm — sửa sai bằng dòng điều chỉnh có lý do; lệch đối chiếu KHÔNG tự sửa."
        actions={
          <>
            {/*  A-06: cấp phát từng kỳ PHẢI có người chốt — beat ngày 1 chỉ nhắc. */}
            {can('coffee_ledger', 'approve') && (
              <Button variant="outline" onClick={() => setApproving(true)}>
                <CalendarCheck className="size-4" />
                Cấp phát kỳ
              </Button>
            )}
            {can('coffee_ledger', 'write') && (
              <Button onClick={() => setAdjusting(true)}>
                <PenLine className="size-4" />
                Điều chỉnh
              </Button>
            )}
          </>
        }
      />
      <Tabs defaultValue="ledger" className="flex min-h-0 flex-1 flex-col gap-3">
        <TabsList className="w-fit">
          <TabsTrigger value="ledger">Sổ cái</TabsTrigger>
          <TabsTrigger value="unmatched">Đơn chưa khớp</TabsTrigger>
          <TabsTrigger value="reconcile">Đối chiếu</TabsTrigger>
          <TabsTrigger value="sync">Nhật ký đồng bộ</TabsTrigger>
        </TabsList>
        <TabsContent value="ledger" className="min-h-0 flex-1">
          <LedgerTab />
        </TabsContent>
        <TabsContent value="unmatched" className="min-h-0 flex-1">
          <UnmatchedTab onResolve={setResolving} />
        </TabsContent>
        <TabsContent value="reconcile" className="min-h-0 flex-1">
          <ReconcileTab />
        </TabsContent>
        <TabsContent value="sync" className="min-h-0 flex-1">
          <SyncTab />
        </TabsContent>
      </Tabs>
      {adjusting && <AdjustDialog onClose={() => setAdjusting(false)} />}
      {approving && <ResetApproveDialog onClose={() => setApproving(false)} />}
      {resolving && <ResolveOrderDialog order={resolving} onClose={() => setResolving(null)} />}
    </PageContainer>
  )
}

function LedgerTab() {
  const { data, isLoading, isError } = useCoffeeLedger({ page_size: '200' })
  const columns = useMemo<DataTableColumn<CoffeeLedgerRow>[]>(
    () => [
      {
        key: 'created_at',
        header: 'Thời điểm',
        width: 150,
        cell: (row) => <span className="tabular-nums">{row.created_at.slice(0, 16)}</span>,
      },
      {
        key: 'employee_name',
        header: 'Nhân sự',
        width: 210,
        cell: (row) => (
          <div className="min-w-0">
            <span className="truncate">{row.employee_name}</span>
            <span className="ml-1.5 font-mono text-xs text-muted-foreground">
              {row.employee_code}
            </span>
          </div>
        ),
      },
      { key: 'period', header: 'Kỳ', width: 80, cell: (row) => row.period },
      {
        key: 'type',
        header: 'Loại',
        width: 140,
        cell: (row) => <Badge variant="outline">{row.type_label}</Badge>,
      },
      {
        key: 'points',
        header: 'Điểm',
        width: 110,
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
        width: 300,
        cell: (row) => (
          <div className="min-w-0">
            <span className="truncate">{row.reason}</span>
            {row.pos_code && (
              <span className="ml-1.5 font-mono text-xs text-muted-foreground">{row.pos_code}</span>
            )}
          </div>
        ),
      },
    ],
    [],
  )
  return (
    <CoffeeBlock icon={BookText} title="Sổ cái điểm" className="flex h-full min-h-0 flex-col">
      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        getRowId={(row) => row.id}
        storageKey="coffee.ledger"
        fillHeight
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Sổ chưa có dòng nào."
      />
    </CoffeeBlock>
  )
}

function UnmatchedTab({ onResolve }: { onResolve: (row: PosOrderRow) => void }) {
  const { can } = usePermission()
  //  match_status=2 = UNMATCHED (nhãn từ backend; số là hợp đồng API D-02).
  const { data, isLoading, isError } = usePosOrders({ match_status: '2', page_size: '200' })
  const columns = useMemo<DataTableColumn<PosOrderRow>[]>(
    () => [
      {
        key: 'purchase_date',
        header: 'Ngày bán',
        width: 150,
        cell: (row) => <span className="tabular-nums">{row.purchase_date.slice(0, 16)}</span>,
      },
      {
        key: 'pos_code',
        header: 'Mã bill',
        width: 150,
        cell: (row) => <span className="font-mono text-sm">{row.pos_code}</span>,
      },
      {
        key: 'pos_partner_id',
        header: 'Khách POS365',
        width: 140,
        cell: (row) =>
          row.pos_partner_id ? (
            <span className="tabular-nums">#{row.pos_partner_id}</span>
          ) : (
            <span className="text-muted-foreground">Không chọn khách</span>
          ),
      },
      {
        key: 'points_paid',
        header: 'Trả bằng điểm',
        width: 130,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{formatPoints(row.points_paid)}</span>,
      },
      {
        key: 'actions',
        header: '',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (row) =>
          can('coffee_ledger', 'write') ? (
            <Button variant="outline" size="sm" onClick={() => onResolve(row)}>
              Xử lý
            </Button>
          ) : null,
      },
    ],
    [can, onResolve],
  )
  return (
    <CoffeeBlock
      icon={FileQuestion}
      title="Đơn chưa khớp người"
      className="flex h-full min-h-0 flex-col"
    >
      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        getRowId={(row) => row.id}
        storageKey="coffee.unmatched"
        fillHeight
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Không có đơn nào chờ xử lý — mọi đơn trừ điểm đều đã khớp người."
      />
    </CoffeeBlock>
  )
}

function ReconcileTab() {
  const { data, isLoading } = useSyncRuns()
  const lastReconcile = (data?.items ?? []).find((r) => r.kind === RECONCILE_KIND && r.detail)
  let detail: ReconcileDetail | null = null
  if (lastReconcile?.detail) {
    try {
      detail = JSON.parse(lastReconcile.detail) as ReconcileDetail
    } catch {
      detail = null
    }
  }
  return (
    <CoffeeBlock
      icon={Scale}
      title="Đối chiếu sổ ↔ POS365"
      className="flex h-full min-h-0 flex-col gap-3 overflow-y-auto"
    >
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Đang tải…</p>
      ) : !lastReconcile ? (
        <p className="text-sm text-muted-foreground">
          Chưa có lần đối chiếu nào — task chạy 06:00 hằng ngày, hoặc bấm chạy tay ở tab Nhật ký.
        </p>
      ) : (
        <>
          <div className="text-sm text-muted-foreground">
            Lần đối chiếu gần nhất: <span className="tabular-nums">{lastReconcile.finished_at}</span>
          </div>
          {detail && detail.mismatches.length === 0 ? (
            <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
              Khớp — tổng tiêu trong sổ bằng tổng đơn «Trừ điểm» của 3 ngày gần nhất.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {(detail?.mismatches ?? []).map((m) => (
                <div
                  key={m.day}
                  className="flex items-center justify-between rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm"
                >
                  <span className="tabular-nums">{m.day}</span>
                  <span className="tabular-nums">
                    POS365: {formatPoints(m.pos)} · Sổ: {formatPoints(m.ledger)} · Chênh:{' '}
                    <span className="font-medium text-destructive">{formatPoints(m.diff)}</span>
                  </span>
                </div>
              ))}
              <p className="text-xs text-muted-foreground">
                Hệ KHÔNG tự sửa lệch — xử lý bằng dòng «Điều chỉnh» có lý do, sau khi đã hiểu vì
                sao lệch (đơn chưa khớp? đơn void chưa quét?).
              </p>
            </div>
          )}
          {detail && detail.unmatched > 0 && (
            <p className="text-sm text-amber-600 dark:text-amber-400">
              Đang còn {detail.unmatched} đơn chưa khớp người — xem tab «Đơn chưa khớp».
            </p>
          )}
        </>
      )}
    </CoffeeBlock>
  )
}

function SyncTab() {
  const { can } = usePermission()
  const { data: meta } = useCoffeeMeta()
  const { data, isLoading, isError } = useSyncRuns()
  const runSync = useRunSync()
  const [kind, setKind] = useState('1')

  const columns = useMemo<DataTableColumn<PosSyncRun>[]>(
    () => [
      {
        key: 'started_at',
        header: 'Lúc chạy',
        width: 150,
        cell: (row) => <span className="tabular-nums">{row.started_at}</span>,
      },
      { key: 'kind_label', header: 'Loại', width: 140, cell: (row) => row.kind_label },
      {
        key: 'status',
        header: 'Kết quả',
        width: 150,
        cell: (row) => (
          <Badge variant={SYNC_STATUS_VARIANT[row.status] ?? 'outline'}>{row.status_label}</Badge>
        ),
      },
      {
        key: 'fetched',
        header: 'Kéo / Ghi / Bỏ qua',
        width: 150,
        align: 'right',
        cell: (row) => (
          <span className="tabular-nums">
            {row.fetched} / {row.written} / {row.skipped}
          </span>
        ),
      },
      {
        key: 'error',
        header: 'Lỗi',
        width: 280,
        cell: (row) =>
          row.error ? (
            <span className="truncate text-sm text-destructive">{row.error}</span>
          ) : null,
      },
      {
        key: 'created_by',
        header: 'Người chạy',
        width: 110,
        defaultHidden: true,
        cell: (row) => (row.created_by ? `#${row.created_by}` : 'Tự động'),
      },
    ],
    [],
  )

  return (
    <CoffeeBlock icon={History} title="Nhật ký đồng bộ" className="flex h-full min-h-0 flex-col">
      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        getRowId={(row) => row.id}
        storageKey="coffee.sync-runs"
        fillHeight
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Chưa có lần đồng bộ nào."
        toolbar={
          can('pos_order', 'write') ? (
            <div className="flex items-center gap-2">
              <Select value={kind} onValueChange={setKind}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(meta?.sync_kinds ?? []).map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                disabled={runSync.isPending}
                onClick={() => runSync.mutate({ kind: Number(kind) })}
              >
                <Play className="size-4" />
                Chạy ngay
              </Button>
            </div>
          ) : undefined
        }
      />
    </CoffeeBlock>
  )
}
