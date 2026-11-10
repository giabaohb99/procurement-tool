// bao-CR-470 — lịch sử các lần nạp dữ liệu hải quan (lô chạy thử + lô ghi thật), nhật ký
// dòng của từng lô và nút hoàn tác.
//
// bao-CR-493: từ hộp thoại thành MỘT THẺ trên trang (thẻ "Lịch sử nạp", yêu cầu F11 của phòng
// Thu mua) và thêm nút tải lại tệp GTT02 gốc — chỉ lô nạp qua màn hình mới có tệp (`has_file`),
// lô nạp bằng script thì nút ẩn.
//
// Không dùng lại màn `/system/imports`: màn đó gác bằng khóa `import` chung, còn lô hải
// quan gác bằng khóa RIÊNG `customs_price` (đại ca chốt 23/09/2026) — người thu mua có
// quyền nạp giá hải quan không nhất thiết có quyền xem mọi lô nạp của hệ thống.
//
// bao-CR-541: lô chỉ THÊM dòng chưa có (trùng thì bỏ qua) nên luôn hoàn tác được. Riêng lô CŨ
// nạp trước CR đã THAY dòng cũ (deleted_count > 0) thì không: dòng cũ đã xóa lúc ghi, hoàn tác
// chỉ để lại một khoảng ngày trống — nút bị khóa kèm lời giải thích.
//
// bao-CR-608: thêm cột "Ghi đè" / "Xóa" (tệp có cột "ID" + "Thao tác"). Lô ghi đè / xóa có bản
// chụp nên VẪN hoàn tác được: trả dòng ghi đè về bản cũ, dựng lại dòng đã xóa đúng id cũ.
import { useCallback, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import {
  useCustomsBatches,
  useCustomsBatchLogs,
  useCustomsPermissions,
  useRevertCustomsBatch,
} from '../../hooks/use-customs'
import {
  CUSTOMS_BATCH_MODE_LABELS,
  type CustomsBatchLog,
  type CustomsImportBatch,
} from '../../types/customs'
import { useLocalServerSort } from '../../hooks/use-local-server-sort'
import { formatRevertConfirm } from '../../utils/customs'
import { CustomsBatchHistoryActions } from './customs-batch-history-actions'
import { CustomsBatchLineCard } from './customs-batch-line-card'
import { CustomsBatchRowsPanel } from './customs-batch-rows-panel'
import { CustomsBatchStatusBadge } from './customs-batch-status-badge'
import { CustomsImportBatchCard } from './customs-import-batch-card'

const HISTORY_PAGE_SIZE = 20
const LOG_PAGE_SIZE = 50

/** Mức của một dòng nhật ký — khớp `ImportLogLevel` của backend. */
const LOG_LEVELS: Record<number, { label: string; tone: string }> = {
  0: { label: 'Thông tin', tone: TONE_CLASS.neutral },
  1: { label: 'Cảnh báo', tone: TONE_CLASS.pending },
  2: { label: 'Cần rà', tone: TONE_CLASS.progress },
  3: { label: 'Lỗi', tone: TONE_CLASS.danger },
}

/** Huy hiệu mức của một dòng nhật ký — chung cho cột "Mức" và thẻ khổ điện thoại. */
function renderLogLevelBadge(log: CustomsBatchLog) {
  const level = LOG_LEVELS[log.level]
  return (
    <Badge className={cn(level?.tone ?? TONE_CLASS.neutral)}>
      {level?.label ?? String(log.level)}
    </Badge>
  )
}

function formatRange(batch: CustomsImportBatch): string {
  return batch.date_from ? `${formatDate(batch.date_from)} → ${formatDate(batch.date_to)}` : '—'
}

export function CustomsHistoryPanel() {
  const { canRevert } = useCustomsPermissions()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(HISTORY_PAGE_SIZE)
  const [logsOf, setLogsOf] = useState<CustomsImportBatch | null>(null)
  const resetPage = useCallback(() => setPage(1), [])
  const sort = useLocalServerSort(resetPage)
  const { data, isLoading, isError } = useCustomsBatches({ page, page_size: pageSize, ...sort.params })
  const revert = useRevertCustomsBatch()
  const reverting = useRef(false)

  //  Cột "Thao tác" và thẻ khổ điện thoại dùng CHUNG một hàm vẽ nút — dựng cùng lượt với cột để
  //  `revertBatch` (đọc ref chặn bấm đúp + mutation) chỉ có một bản.
  const { columns, renderActions } = useMemo(() => {
    async function revertBatch(batch: CustomsImportBatch) {
      if (reverting.current) return
      const ok = await confirm({
        title: 'Hoàn tác lô nạp',
        message: formatRevertConfirm(batch),
        confirmLabel: 'Hoàn tác',
      })
      if (!ok || reverting.current) return
      reverting.current = true
      try {
        const result = await revert.mutateAsync(batch.id)
        toast.success(result.message || 'Đã hoàn tác')
      } catch {
        //  `httpClient` đã báo lỗi bằng toast.
      } finally {
        reverting.current = false
      }
    }

    const renderActions = (b: CustomsImportBatch) => (
      <CustomsBatchHistoryActions
        batch={b}
        canRevert={canRevert}
        revertPending={revert.isPending}
        onOpenLogs={setLogsOf}
        onRevert={(batch) => void revertBatch(batch)}
      />
    )

    const columns: DataTableColumn<CustomsImportBatch>[] = [
      {
        key: 'id',
        header: '#',
        width: 64,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => b.id,
      },
      {
        key: 'filename',
        header: 'Tệp',
        width: 220,
        sortable: true,
        hideable: false,
        wrap: true,
        cell: (b) => <span className="break-all">{b.filename}</span>,
      },
      {
        key: 'mode',
        header: 'Loại',
        width: 90,
        sortable: true,
        hideable: false,
        cell: (b) => CUSTOMS_BATCH_MODE_LABELS[b.mode],
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        sortable: true,
        hideable: false,
        cell: (b) => <CustomsBatchStatusBadge batch={b} />,
      },
      {
        key: 'created_count',
        header: 'Thêm mới',
        width: 90,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => b.created_count,
      },
      //  bao-CR-608 — ghi đè theo cột "ID", xóa theo cột "Thao tác". Lô cũ (trước bao-CR-541) có
      //  "Xóa" là số dòng cũ bị THAY — cột Thao tác khóa nút hoàn tác của lô đó.
      {
        key: 'updated_count',
        header: 'Ghi đè',
        width: 80,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => b.updated_count || 0,
      },
      {
        key: 'deleted_count',
        header: 'Xóa',
        width: 70,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => b.deleted_count || 0,
      },
      {
        key: 'range',
        header: 'Khoảng ngày',
        width: 190,
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: formatRange,
      },
      {
        key: 'date_fixed',
        header: 'Vá ngày',
        width: 80,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => b.date_fixed || 0,
      },
      {
        key: 'skipped_rows',
        header: 'Bỏ qua (trùng)',
        width: 110,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => (b.existing_rows || 0) + (b.duplicate_rows || 0),
      },
      {
        key: 'created_by_name',
        header: 'Người nạp',
        width: 150,
        sortable: true,
        hideable: false,
        wrap: true,
        cell: (b) => b.created_by_name || '—',
      },
      {
        key: 'finished_at',
        header: 'Lúc',
        width: 140,
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (b) => formatDateTime(b.finished_at || b.created_at) || '—',
      },
      {
        key: 'actions',
        header: 'Thao tác',
        width: 130,
        hideable: false,
        stickyRight: true,
        cell: renderActions,
      },
    ]
    return { columns, renderActions }
  }, [canRevert, revert])

  return (
    <Card className="gap-3 p-4">
      <div>
        <h2 className="text-base font-semibold">Lịch sử nạp dữ liệu hải quan</h2>
        <p className="text-sm text-muted-foreground">
          Mọi lô chạy thử và ghi thật, mới nhất lên đầu. Dòng trùng được bỏ qua khi nạp; hoàn tác
          một lô xóa dòng lô đó đã thêm và trả lại dòng lô đó đã ghi đè / xóa (theo cột ID / Thao
          tác). Lô nạp qua màn hình tải lại được tệp gốc.
        </p>
      </div>
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(b) => b.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Chưa nạp lần nào."
        //  Khổ điện thoại: thẻ dọc, nút thao tác nằm TRONG thẻ (bảng không có `onRowClick`).
        mobileCard={(b) => (
          <CustomsImportBatchCard batch={b} context="history" actions={renderActions(b)} />
        )}
        sortBy={sort.sortBy}
        sortDir={sort.sortDir}
        onSortChange={sort.onSortChange}
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
          unitLabel: 'lô',
        }}
      />
      {logsOf && <BatchLogsDialog batch={logsOf} onClose={() => setLogsOf(null)} />}
    </Card>
  )
}

function BatchLogsDialog({ batch, onClose }: { batch: CustomsImportBatch; onClose: () => void }) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(LOG_PAGE_SIZE)
  const resetPage = useCallback(() => setPage(1), [])
  const sort = useLocalServerSort(resetPage)
  const { data, isLoading, isError } = useCustomsBatchLogs(batch.id, {
    page,
    page_size: pageSize,
    ...sort.params,
  })

  const columns = useMemo<DataTableColumn<CustomsBatchLog>[]>(
    () => [
      {
        key: 'row_no',
        header: 'Dòng',
        width: 80,
        align: 'right',
        sortable: true,
        hideable: false,
        cell: (x) => x.row_no || '—',
      },
      {
        key: 'level',
        header: 'Mức',
        width: 110,
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: renderLogLevelBadge,
      },
      {
        key: 'message',
        header: 'Nội dung',
        width: 520,
        sortable: true,
        hideable: false,
        wrap: true,
        cell: (x) => x.message,
      },
    ],
    [],
  )

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="flex max-h-[92dvh] flex-col gap-4 sm:max-w-6xl">
        <DialogHeader>
          <DialogTitle>
            Nhật ký lô #{batch.id} — {batch.filename}
          </DialogTitle>
          {batch.error_summary && (
            <DialogDescription className="text-destructive">
              {batch.error_summary.split('\n')[0]}
            </DialogDescription>
          )}
        </DialogHeader>
        {/* bao-CR-496: hai thẻ chứ không xếp dọc hai bảng — hộp chỉ cao 88% màn hình, xếp dọc thì
             mỗi bảng còn thấy vài dòng. "Từng dòng" đứng trước: nó trả lời "lô này nạp ra sao";
             "Ghi chú" là cảnh báo / lỗi đọc tệp mức lô, y như trước 496. */}
        <Tabs defaultValue="rows" className="flex min-h-0 flex-1 flex-col gap-3">
          <TabsList className="self-start">
            <TabsTrigger value="rows">Kết quả từng dòng</TabsTrigger>
            <TabsTrigger value="notes">Ghi chú lỗi / cảnh báo</TabsTrigger>
          </TabsList>
          <TabsContent value="rows" className="flex min-h-0 flex-1 flex-col">
            <CustomsBatchRowsPanel batchId={batch.id} className="flex min-h-0 flex-1 flex-col gap-3" />
          </TabsContent>
          <TabsContent value="notes" className="flex min-h-0 flex-1 flex-col">
            {data?.pruned_note && (
              <p className="text-muted-foreground mb-2 text-xs">{data.pruned_note}</p>
            )}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <DataTable
                columns={columns}
                rows={data?.items}
                getRowId={(x) => x.id}
                isLoading={isLoading}
                isError={isError}
                emptyMessage="Không có ghi chú nào — mọi dòng đọc được bình thường."
                sortBy={sort.sortBy}
                sortDir={sort.sortDir}
                onSortChange={sort.onSortChange}
                mobileCard={(x) => (
                  <CustomsBatchLineCard
                    rowNo={x.row_no}
                    badge={renderLogLevelBadge(x)}
                    message={x.message}
                  />
                )}
                pagination={{
                  page,
                  pageSize,
                  total: data?.total ?? 0,
                  onPageChange: setPage,
                  onPageSizeChange: (size) => {
                    setPageSize(size)
                    setPage(1)
                  },
                  unitLabel: 'dòng nhật ký',
                }}
              />
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
