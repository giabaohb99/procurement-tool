// bao-CR-470 — lịch sử các lần nạp dữ liệu hải quan (lô chạy thử + lô ghi thật), nhật ký
// dòng của từng lô và nút hoàn tác.
//
// bao-CR-493: từ hộp thoại thành MỘT THẺ trên trang (thẻ «Lịch sử nạp», yêu cầu F11 của phòng
// Thu mua) và thêm nút tải lại tệp GTT02 gốc — chỉ lô nạp qua màn hình mới có tệp (`has_file`),
// lô nạp bằng script thì nút ẩn.
//
// Không dùng lại màn `/system/imports`: màn đó gác bằng khóa `import` chung, còn lô hải
// quan gác bằng khóa RIÊNG `customs_price` (đại ca chốt 23/09/2026) — người thu mua có
// quyền nạp giá hải quan không nhất thiết có quyền xem mọi lô nạp của hệ thống.
//
// Lô đã THAY dòng cũ (deleted_count > 0) không hoàn tác được: dòng cũ đã xóa lúc ghi, hoàn
// tác chỉ xóa được dòng mới và để lại một khoảng ngày trống — nút bị khóa kèm lời giải thích.
import { Download, ListTree, Undo2 } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import { downloadCustomsBatchFile } from '../../api/customs-api'
import {
  useCustomsBatches,
  useCustomsBatchLogs,
  useCustomsPermissions,
  useRevertCustomsBatch,
} from '../../hooks/use-customs'
import {
  CUSTOMS_BATCH_MODE,
  type CustomsBatchLog,
  type CustomsImportBatch,
} from '../../types/customs'
import { resolveRevertState } from '../../utils/customs'
import { CustomsBatchRowsPanel } from './customs-batch-rows-panel'
import { CustomsBatchStatusBadge } from './customs-batch-status-badge'

const HISTORY_PAGE_SIZE = 20
const LOG_PAGE_SIZE = 50

/** Mức của một dòng nhật ký — khớp `ImportLogLevel` của backend. */
const LOG_LEVELS: Record<number, { label: string; tone: string }> = {
  0: { label: 'Thông tin', tone: TONE_CLASS.neutral },
  1: { label: 'Cảnh báo', tone: TONE_CLASS.pending },
  2: { label: 'Cần rà', tone: TONE_CLASS.progress },
  3: { label: 'Lỗi', tone: TONE_CLASS.danger },
}

function formatRange(batch: CustomsImportBatch): string {
  return batch.date_from ? `${formatDate(batch.date_from)} → ${formatDate(batch.date_to)}` : '—'
}

export function CustomsHistoryPanel() {
  const { canRevert } = useCustomsPermissions()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(HISTORY_PAGE_SIZE)
  const [logsOf, setLogsOf] = useState<CustomsImportBatch | null>(null)
  const { data, isLoading, isError } = useCustomsBatches({ page, page_size: pageSize })
  const revert = useRevertCustomsBatch()
  const reverting = useRef(false)

  const columns = useMemo<DataTableColumn<CustomsImportBatch>[]>(() => {
    async function revertBatch(batch: CustomsImportBatch) {
      if (reverting.current) return
      const ok = await confirm({
        title: 'Hoàn tác lô nạp',
        message: `Xóa ${batch.created_count} dòng hàng của tệp «${batch.filename}»? Dữ liệu khoảng ${formatRange(batch)} sẽ trống.`,
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

    return [
      { key: 'id', header: '#', width: 64, align: 'right', hideable: false, cell: (b) => b.id },
      {
        key: 'filename',
        header: 'Tệp',
        width: 220,
        hideable: false,
        wrap: true,
        cell: (b) => <span className="break-all">{b.filename}</span>,
      },
      {
        key: 'mode',
        header: 'Loại',
        width: 90,
        hideable: false,
        cell: (b) => (b.mode === CUSTOMS_BATCH_MODE.dryRun ? 'Chạy thử' : 'Ghi thật'),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        hideable: false,
        cell: (b) => <CustomsBatchStatusBadge batch={b} />,
      },
      {
        key: 'created_count',
        header: 'Dòng hàng',
        width: 95,
        align: 'right',
        hideable: false,
        cell: (b) => b.created_count,
      },
      { key: 'range', header: 'Khoảng ngày', width: 190, hideable: false, cell: formatRange },
      {
        key: 'date_fixed',
        header: 'Vá ngày',
        width: 80,
        align: 'right',
        hideable: false,
        cell: (b) => b.date_fixed || 0,
      },
      {
        key: 'deleted_count',
        header: 'Thay dòng cũ',
        width: 105,
        align: 'right',
        hideable: false,
        cell: (b) => b.deleted_count || 0,
      },
      {
        key: 'created_by_name',
        header: 'Người nạp',
        width: 150,
        hideable: false,
        wrap: true,
        cell: (b) => b.created_by_name || '—',
      },
      {
        key: 'finished_at',
        header: 'Lúc',
        width: 140,
        hideable: false,
        cell: (b) => formatDateTime(b.finished_at || b.created_at) || '—',
      },
      {
        key: 'actions',
        header: 'Thao tác',
        width: 130,
        hideable: false,
        stickyRight: true,
        cell: (b) => {
          const revertState = canRevert ? resolveRevertState(b) : 'hidden'
          return (
            <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
              {b.has_file && (
                <IconTooltip label="Tải lại tệp gốc đã nạp">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    aria-label="Tải lại tệp gốc đã nạp"
                    onClick={() =>
                      downloadCustomsBatchFile(b.id, b.filename).catch((error: Error) =>
                        toast.error(error.message),
                      )
                    }
                  >
                    <Download className="size-4" />
                  </Button>
                </IconTooltip>
              )}
              <IconTooltip label="Nhật ký dòng lỗi / cảnh báo">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label="Nhật ký dòng lỗi / cảnh báo"
                  onClick={() => setLogsOf(b)}
                >
                  <ListTree className="size-4" />
                </Button>
              </IconTooltip>
              {revertState !== 'hidden' && (
                <IconTooltip
                  label={
                    revertState === 'blocked'
                      ? `Lô này đã thay ${b.deleted_count} dòng cũ nên không hoàn tác được — nạp lại tệp đúng để sửa.`
                      : 'Hoàn tác: xóa các dòng lô này đã ghi'
                  }
                >
                  {/*  Bọc `span`: nút `disabled` không nhận sự kiện chuột nên tooltip
                       giải thích VÌ SAO bị khóa sẽ không bao giờ hiện nếu gắn thẳng. */}
                  <span className="inline-flex">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label="Hoàn tác lô nạp"
                      disabled={revertState === 'blocked' || revert.isPending}
                      onClick={() => void revertBatch(b)}
                    >
                      <Undo2 className="size-4" />
                    </Button>
                  </span>
                </IconTooltip>
              )}
            </div>
          )
        },
      },
    ]
  }, [canRevert, revert])

  return (
    <Card className="gap-3 p-4">
      <div>
        <h2 className="text-base font-semibold">Lịch sử nạp dữ liệu hải quan</h2>
        <p className="text-sm text-muted-foreground">
          Mọi lô chạy thử và ghi thật, mới nhất lên đầu. Lô đã thay dòng cũ thì không hoàn tác
          được; lô nạp qua màn hình tải lại được tệp gốc.
        </p>
      </div>
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(b) => b.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Chưa nạp lần nào."
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
  const { data, isLoading, isError } = useCustomsBatchLogs(batch.id, {
    page,
    page_size: pageSize,
  })

  const columns = useMemo<DataTableColumn<CustomsBatchLog>[]>(
    () => [
      {
        key: 'row_no',
        header: 'Dòng',
        width: 80,
        align: 'right',
        hideable: false,
        cell: (x) => x.row_no || '—',
      },
      {
        key: 'level',
        header: 'Mức',
        width: 110,
        hideable: false,
        cell: (x) => {
          const level = LOG_LEVELS[x.level]
          return (
            <Badge className={cn(level?.tone ?? TONE_CLASS.neutral)}>
              {level?.label ?? String(x.level)}
            </Badge>
          )
        },
      },
      { key: 'message', header: 'Nội dung', width: 520, hideable: false, wrap: true, cell: (x) => x.message },
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
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto">
          {/* bao-CR-496 — kết cục TỪNG DÒNG của tệp (Thêm mới / Lỗi / Trùng trong lô), đủ mọi dòng. */}
          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Từng dòng của tệp</h3>
            <CustomsBatchRowsPanel batchId={batch.id} />
          </section>
          <h3 className="text-sm font-semibold">Ghi chú khi đọc tệp</h3>
          <DataTable
            columns={columns}
            rows={data?.items}
            getRowId={(x) => x.id}
            isLoading={isLoading}
            isError={isError}
            emptyMessage="Không có ghi chú nào — mọi dòng đọc được bình thường."
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
      </DialogContent>
    </Dialog>
  )
}
