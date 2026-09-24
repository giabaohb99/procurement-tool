// bao-CR-470 — nạp tệp GTT02 (HQ1). Luôn CHẠY THỬ trước: mỗi tệp một lô, báo số dòng,
// khoảng ngày, số ngày bị đảo đã vá và số dòng cũ SẼ BỊ THAY; người nạp xem rồi mới bấm
// Áp dụng.
//
// Luật thay dữ liệu: lô mới xóa mọi dòng cũ nằm trong khoảng ngày của nó rồi ghi lại — tệp
// GTT02 không có khóa duy nhất (806 dòng trùng khít trong 5 tệp mẫu), nên nạp chồng theo
// khoảng ngày là cách duy nhất không đếm đôi. Lô đã thay dòng cũ thì KHÔNG hoàn tác được.
//
// Hai nút Chạy thử / Áp dụng chặn bấm đúp bằng `useRef` ngay trong lượt bấm — `disabled`
// chỉ đổi ở lượt vẽ sau, bấm liền tay vẫn lọt hai lệnh.
import { Check, FileSpreadsheet, Play, TriangleAlert, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { formatDate } from '@/shared/utils/format-date'
import { formatFileSize } from '@/shared/utils/format-file-size'

import {
  useCommitCustomsBatch,
  useCustomsBatchPolling,
  useInvalidateCustoms,
  useUploadCustomsFiles,
} from '../../hooks/use-customs'
import { CUSTOMS_BATCH_STATUS, type CustomsImportBatch } from '../../types/customs'
import { isBatchRunning, isBatchUsable, sumReplacedLines } from '../../utils/customs'
import { CustomsBatchStatusBadge } from './customs-batch-status-badge'
import { CustomsNotice } from './customs-controls'

const ACCEPTED = '.xls,.xlsx'

interface CustomsImportDialogProps {
  onClose: () => void
}

export function CustomsImportDialog({ onClose }: CustomsImportDialogProps) {
  const [files, setFiles] = useState<File[]>([])
  const [dryBatches, setDryBatches] = useState<CustomsImportBatch[]>([])
  const [applyBatches, setApplyBatches] = useState<CustomsImportBatch[]>([])
  const [applying, setApplying] = useState(false)
  const busy = useRef(false)
  const notified = useRef(false)

  const upload = useUploadCustomsFiles()
  const commit = useCommitCustomsBatch()
  const invalidate = useInvalidateCustoms()

  const dry = useCustomsBatchPolling(dryBatches)
  const applied = useCustomsBatchPolling(applyBatches)

  const stage = applyBatches.length ? 'apply' : dryBatches.length ? 'dry' : 'pick'
  const dryDone = dry.length > 0 && dry.every((batch) => !isBatchRunning(batch))
  const usable = dry.filter(isBatchUsable)
  const willReplace = sumReplacedLines(dry)
  const appliedDone = applied.length > 0 && applied.every((batch) => !isBatchRunning(batch))

  //  Báo MỘT lần khi mọi lô ghi thật đã xong, rồi làm mới cả màn (danh sách, dải tháng,
  //  ô lọc). `notified` chặn báo lặp khi hộp thoại vẽ lại.
  useEffect(() => {
    if (!appliedDone || notified.current) return
    notified.current = true
    const failed = applied.filter((batch) => batch.status === CUSTOMS_BATCH_STATUS.failed)
    if (failed.length) toast.error(`${failed.length} tệp ghi lỗi — xem Lịch sử nạp`)
    else {
      const total = applied.reduce((sum, batch) => sum + (batch.created_count || 0), 0)
      toast.success(`Đã nạp ${total} dòng hàng`)
    }
    void invalidate()
  }, [appliedDone, applied, invalidate])

  async function runDryRun() {
    if (busy.current || !files.length) return
    busy.current = true
    try {
      const batches = await upload.mutateAsync(files)
      setDryBatches(batches)
    } catch {
      //  `httpClient` đã báo lỗi (tệp sai định dạng, thiếu cột…) bằng toast.
    } finally {
      busy.current = false
    }
  }

  async function applyAll() {
    if (busy.current || !usable.length) return
    busy.current = true
    setApplying(true)
    try {
      const created: CustomsImportBatch[] = []
      //  Ghi LẦN LƯỢT từng lô: hai lô cùng thay một khoảng ngày mà chạy song song thì
      //  lô nào xóa trước lô nào ghi trước là chuyện may rủi.
      for (const batch of usable) {
        created.push(await commit.mutateAsync(batch.id))
      }
      setApplyBatches(created)
    } catch {
      //  `httpClient` đã báo lỗi bằng toast.
    } finally {
      busy.current = false
      setApplying(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="flex max-h-[92dvh] flex-col gap-4 sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Nạp dữ liệu hải quan (tệp GTT02)</DialogTitle>
          <DialogDescription>
            Mỗi tệp chạy thử riêng; chưa có gì ghi vào dữ liệu cho tới khi bấm Áp dụng.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {stage === 'pick' && (
            <div className="flex flex-col gap-3">
              <p className="text-sm">
                Chọn một hoặc nhiều tệp <b>.xls / .xlsx</b> xuất từ hệ thống hải quan (mẫu GTT02 —
                đủ 32 cột).
              </p>
              <FileDropzone
                accept={ACCEPTED}
                busy={upload.isPending}
                hint="Kéo thả tệp GTT02 vào đây hoặc bấm để chọn (chọn được nhiều tệp)"
                onFiles={(picked) => setFiles((current) => mergeFiles(current, picked))}
              />
              {files.length > 0 && (
                <ul className="space-y-1 text-sm">
                  {files.map((file) => (
                    <li key={`${file.name}-${file.size}`} className="flex items-center gap-2">
                      <FileSpreadsheet className="size-4 shrink-0 text-muted-foreground" />
                      <span className="min-w-0 flex-1 truncate">{file.name}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-xs"
                        aria-label={`Bỏ tệp ${file.name}`}
                        onClick={() => setFiles((current) => current.filter((item) => item !== file))}
                      >
                        <X />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
              <p className="text-xs text-muted-foreground">
                Lưu ý: nạp tệp có khoảng ngày trùng dữ liệu đã có thì các dòng cũ trong khoảng đó
                được THAY bằng tệp mới (tệp hải quan không có mã dòng để đối chiếu từng dòng).
              </p>
            </div>
          )}

          {stage !== 'pick' && (
            <div className="flex flex-col gap-3">
              <BatchTable rows={stage === 'apply' ? applied : dry} applying={stage === 'apply'} />
              {stage === 'dry' && !dryDone && (
                <p className="text-sm text-muted-foreground">Đang chạy thử…</p>
              )}
              {stage === 'dry' && dryDone && willReplace > 0 && (
                <CustomsNotice tone="warning" icon={<TriangleAlert className="size-4" />}>
                  Áp dụng sẽ <b>thay {willReplace} dòng cũ</b> nằm trong khoảng ngày của các tệp
                  này. Lô đã thay dữ liệu cũ thì KHÔNG hoàn tác được.
                </CustomsNotice>
              )}
              {stage === 'dry' && dryDone && !usable.length && (
                <CustomsNotice tone="danger" icon={<TriangleAlert className="size-4" />}>
                  Không tệp nào dùng được — xem cột Trạng thái và dòng lỗi bên dưới bảng.
                </CustomsNotice>
              )}
              {stage === 'apply' && !appliedDone && (
                <p className="text-sm text-muted-foreground">Đang ghi dữ liệu…</p>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            {appliedDone ? 'Đóng' : 'Hủy'}
          </Button>
          {stage === 'pick' && (
            <Button type="button" disabled={!files.length || upload.isPending} onClick={runDryRun}>
              <Play className="size-4" />
              {upload.isPending ? 'Đang tải lên…' : 'Chạy thử'}
            </Button>
          )}
          {stage === 'dry' && (
            <Button type="button" disabled={!dryDone || !usable.length || applying} onClick={applyAll}>
              <Check className="size-4" />
              {applying ? 'Đang áp dụng…' : `Áp dụng ${usable.length} tệp`}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Gộp tệp mới chọn vào danh sách, bỏ tệp trùng tên + dung lượng (chọn lại cùng tệp). */
function mergeFiles(current: File[], picked: File[]): File[] {
  const seen = new Set(current.map((file) => `${file.name}|${file.size}`))
  return [...current, ...picked.filter((file) => !seen.has(`${file.name}|${file.size}`))]
}

function formatRange(batch: CustomsImportBatch): string {
  return batch.date_from
    ? `${formatDate(batch.date_from)} → ${formatDate(batch.date_to)}`
    : '—'
}

function BatchTable({ rows, applying }: { rows: CustomsImportBatch[]; applying: boolean }) {
  const columns = useMemo<DataTableColumn<CustomsImportBatch>[]>(
    () => [
      {
        key: 'filename',
        header: 'Tệp',
        width: 240,
        hideable: false,
        wrap: true,
        cell: (b) => <span className="break-all">{b.filename}</span>,
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
        width: 100,
        align: 'right',
        hideable: false,
        cell: (b) => (b.status === CUSTOMS_BATCH_STATUS.done ? b.created_count : '—'),
      },
      { key: 'range', header: 'Khoảng ngày', width: 200, hideable: false, cell: formatRange },
      {
        key: 'date_fixed',
        header: 'Đã vá ngày',
        width: 100,
        align: 'right',
        hideable: false,
        cell: (b) => b.date_fixed || 0,
      },
      {
        key: 'deleted_count',
        header: applying ? 'Đã thay' : 'Sẽ thay',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (b) => (
          <span className={b.deleted_count > 0 ? 'font-semibold text-warning' : undefined}>
            {b.deleted_count || 0}
          </span>
        ),
      },
      {
        key: 'warning_count',
        header: 'Cảnh báo',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (b) => b.warning_count || 0,
      },
    ],
    [applying],
  )

  const failed = rows.filter((batch) => batch.status === CUSTOMS_BATCH_STATUS.failed)

  return (
    <div className="flex flex-col gap-2">
      <DataTable columns={columns} rows={rows} getRowId={(b) => b.id} />
      {failed.length > 0 && (
        <ul className="space-y-0.5 text-xs text-destructive">
          {failed.map((batch) => (
            <li key={batch.id}>
              {batch.filename}: {(batch.error_summary || '').split('\n')[0]}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
