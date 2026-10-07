// bao-CR-470 — nạp tệp GTT02 (HQ1). Luôn CHẠY THỬ trước: mỗi tệp một lô, báo số dòng mới,
// khoảng ngày, số ngày bị đảo đã vá và số dòng sẽ BỎ QUA; người nạp xem rồi mới bấm Áp dụng.
//
// bao-CR-541 (đại ca chốt 01/10/2026): trùng thì BỎ QUA — dòng giống hệt một dòng đã có trong
// bảng giá hoặc lặp lại trong cùng tệp không được ghi; không xóa, không ghi đè dòng cũ nào nữa
// (bỏ luật «thay theo khoảng ngày» của bao-CR-470). Dòng mới trùng cột nhận diện mà khác giá
// thì vẫn thêm, chỉ đếm «nghi sửa giá» để người nạp rà ở Nhật ký lô.
//
// bao-CR-608 (đại ca 07/10/2026): tệp có thêm cột «ID» (tùy chọn) thì ID có thật → GHI ĐÈ đúng
// dòng đó; cột «Thao tác» = xóa → XÓA dòng có ID đó. Excel xuất ra từ màn này có sẵn cột ID đầu
// và cột «Thao tác» rỗng cuối. Bảng chạy thử có thêm hai cột Ghi đè / Xóa.
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
import {
  formatWrittenSummary,
  isBatchRunning,
  isBatchUsable,
  sumSkippedLines,
  sumWrittenLines,
} from '../../utils/customs'
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
  const skipped = sumSkippedLines(dry)
  //  Mọi lô chạy thử xong, không lô nào lỗi, mà không còn dòng mới: tệp đã nạp rồi — nói rõ
  //  thay vì câu «không tệp nào dùng được» (nghe như tệp hỏng).
  const nothingNew =
    dryDone && !usable.length && dry.every((batch) => batch.status === CUSTOMS_BATCH_STATUS.done)
  const appliedDone = applied.length > 0 && applied.every((batch) => !isBatchRunning(batch))

  //  Báo MỘT lần khi mọi lô ghi thật đã xong, rồi làm mới cả màn (danh sách, dải tháng,
  //  ô lọc). `notified` chặn báo lặp khi hộp thoại vẽ lại.
  useEffect(() => {
    if (!appliedDone || notified.current) return
    notified.current = true
    const failed = applied.filter((batch) => batch.status === CUSTOMS_BATCH_STATUS.failed)
    if (failed.length) toast.error(`${failed.length} tệp ghi lỗi — xem Lịch sử nạp`)
    else {
      const done = sumSkippedLines(applied)
      toast.success(formatWrittenSummary(sumWrittenLines(applied), done.existing + done.duplicate))
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
      //  Ghi LẦN LƯỢT từng lô: lô sau phải thấy dòng lô trước vừa ghi thì mới bỏ qua được
      //  phần hai tệp chồng nhau (backend cũng khóa, đây là để thứ tự đúng như danh sách).
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
              {/*  bao-CR-603 — năm cột tùy chọn: thiếu thì nạp như cũ, có thì ô có chữ mới thắng. */}
              <p className="text-xs text-muted-foreground">
                Tệp có thể thêm các cột tùy chọn <b>Hoạt chất</b>, <b>Hàm lượng / dạng</b>,{' '}
                <b>Đơn giá quy đổi VND (thuế NK 7%)</b>, <b>Đơn giá quy đổi VND (theo thuế suất XNK)</b>;
                cột <b>Nước nhận hàng</b> cũng không bắt buộc. Ô có giá trị thì lấy của tệp; ô trống hoặc
                thiếu cột thì hoạt chất / hàm lượng suy ra từ tên hàng và giá VND tính từ giá × tỷ giá như
                cũ. Tệp Excel xuất từ màn này nạp lại được.
              </p>
              {/*  bao-CR-608 — hai cột điều khiển: ghi đè / xóa đúng dòng theo ID. */}
              <p className="text-xs text-muted-foreground">
                Cột <b>ID</b> (tùy chọn): ô ghi ID của một dòng đang có thì dòng đó bị <b>ghi đè</b>{' '}
                toàn bộ bằng dữ liệu trong tệp; ID không có thì dòng được thêm mới như thường; ô trống
                thì như cũ. Cột <b>Thao tác</b> (tùy chọn, nhận cả tiêu đề «Action», «Hành động»): ghi{' '}
                <b>xóa</b> / <b>delete</b> thì <b>xóa</b> dòng có ID đó — dòng xóa chỉ cần ô ID. Excel
                xuất từ màn này có sẵn cột ID ở đầu và cột Thao tác trống ở cuối: xuất → sửa → nạp lại.
                Hoàn tác lô trả lại đủ dòng đã ghi đè / xóa.
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
                Dòng đã có trong bảng giá hoặc lặp lại trong cùng tệp sẽ được bỏ qua — nạp lại
                một tệp không làm nhân đôi dữ liệu. Dòng cũ chỉ bị ghi đè / xóa khi tệp chỉ ra đúng
                ID của nó.
              </p>
            </div>
          )}

          {stage !== 'pick' && (
            <div className="flex flex-col gap-3">
              <BatchTable rows={stage === 'apply' ? applied : dry} applying={stage === 'apply'} />
              {stage === 'dry' && !dryDone && (
                <p className="text-sm text-muted-foreground">Đang chạy thử…</p>
              )}
              {stage === 'dry' && dryDone && skipped.existing + skipped.duplicate > 0 && (
                <CustomsNotice tone="info">
                  Sẽ bỏ qua <b>{skipped.existing} dòng đã có</b> trong bảng giá
                  {skipped.duplicate > 0 && (
                    <>
                      {' '}
                      và <b>{skipped.duplicate} dòng trùng trong tệp</b>
                    </>
                  )}
                  .
                  {usable.length > 1 &&
                    ' Chạy thử tính riêng từng tệp — các tệp chồng ngày nhau thì lúc áp dụng sẽ bỏ qua thêm phần trùng giữa chúng.'}
                </CustomsNotice>
              )}
              {stage === 'dry' && dryDone && skipped.suspect > 0 && (
                <CustomsNotice tone="warning" icon={<TriangleAlert className="size-4" />}>
                  <b>{skipped.suspect} dòng mới</b> trùng ngày, doanh nghiệp, đối tác, mã HS, số thứ
                  tự và tên hàng với một dòng đã có nhưng khác giá hoặc lượng — vẫn được thêm (thường
                  là lô hàng khác). Nếu là nguồn sửa số liệu thì hoàn tác lô cũ rồi nạp lại; xem ghi
                  chú «nghi sửa giá» ở Nhật ký lô.
                </CustomsNotice>
              )}
              {stage === 'dry' && nothingNew && (
                <CustomsNotice tone="info">
                  Mọi dòng trong các tệp này đã có trong bảng giá — không có gì để thêm, ghi đè hay
                  xóa.
                </CustomsNotice>
              )}
              {stage === 'dry' && dryDone && !usable.length && !nothingNew && (
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
        header: applying ? 'Đã thêm' : 'Dòng mới',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (b) => (b.status === CUSTOMS_BATCH_STATUS.done ? b.created_count : '—'),
      },
      //  bao-CR-608 — ghi đè theo cột «ID», xóa theo cột «Thao tác».
      {
        key: 'updated_count',
        header: applying ? 'Đã ghi đè' : 'Ghi đè',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (b) => (b.status === CUSTOMS_BATCH_STATUS.done ? b.updated_count || 0 : '—'),
      },
      {
        key: 'deleted_count',
        header: applying ? 'Đã xóa' : 'Xóa',
        width: 70,
        align: 'right',
        hideable: false,
        cell: (b) => (b.status === CUSTOMS_BATCH_STATUS.done ? b.deleted_count || 0 : '—'),
      },
      {
        key: 'existing_rows',
        header: 'Đã có',
        width: 80,
        align: 'right',
        hideable: false,
        cell: (b) => (b.status === CUSTOMS_BATCH_STATUS.done ? b.existing_rows || 0 : '—'),
      },
      {
        key: 'duplicate_rows',
        header: 'Trùng trong tệp',
        width: 110,
        align: 'right',
        hideable: false,
        cell: (b) => (b.status === CUSTOMS_BATCH_STATUS.done ? b.duplicate_rows || 0 : '—'),
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
