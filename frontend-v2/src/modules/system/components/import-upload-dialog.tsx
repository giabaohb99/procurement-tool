import {
  AlertCircle,
  Download,
  FileSpreadsheet,
  FileUp,
  Info,
  Loader2,
  Upload,
  X,
} from 'lucide-react'
import { type ReactNode, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
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
import { cn } from '@/shared/utils/cn'
import { formatFileSize } from '@/shared/utils/format-file-size'

import { importApi } from '../api/import-api'
import {
  IMPORT_MODE_APPLY,
  IMPORT_MODE_DRY_RUN,
  IMPORT_MODULE_LABELS,
  IMPORT_MODULE_OPTIONS,
} from '../config/import-meta'
import { useUploadImport } from '../hooks/use-imports'
import { ModuleTablePicker, type DataTableOption } from './module-table-picker'

/** Đối tượng mặc định = mục đầu tiên trong danh sách (danh mục nền của Đ-13d). */
const DEFAULT_MODULE = IMPORT_MODULE_OPTIONS[0]?.value ?? 1

/** Bảng cho picker: chuyển IMPORT_MODULE_OPTIONS sang dạng {value chuỗi, moduleId}. */
const IMPORT_TABLES: DataTableOption[] = IMPORT_MODULE_OPTIONS.map((o) => ({
  value: String(o.value),
  label: o.label,
  moduleId: o.moduleId,
}))

interface ImportUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Khóa cứng đối tượng (khi mở từ nút Nhập của một màn danh mục cụ thể). */
  lockedModule?: number
  /** Điều hướng sang trang chi tiết batch vừa tạo. */
  onCreated?: (batchId: number) => void
}

export function ImportUploadDialog({
  open,
  onOpenChange,
  lockedModule,
  onCreated,
}: ImportUploadDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="gap-0 overflow-hidden p-0 sm:max-w-[600px]"
        //  Chỉ đóng bằng nút Huỷ hoặc X — bấm ra vùng xám / nhấn Esc KHÔNG đóng,
        //  tránh mất tệp và lựa chọn đang dở.
        onInteractOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        {/* Nội dung là component con — Radix unmount khi đóng nên mỗi lần mở là
            state khởi tạo lại từ đầu, không cần useEffect reset (tránh cảnh báo
            set-state-in-effect). */}
        {open && (
          <ImportUploadForm
            lockedModule={lockedModule}
            onClose={() => onOpenChange(false)}
            onCreated={onCreated}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

interface ImportUploadFormProps {
  lockedModule?: number
  onClose: () => void
  onCreated?: (batchId: number) => void
}

/** Nút chọn chế độ (Chạy thử / Ghi) — kiểu ô bấm bo góc, tô màu khi được chọn. */
function ModeTile({
  active,
  tone,
  disabled,
  onClick,
  children,
}: {
  active: boolean
  tone: 'blue' | 'amber'
  disabled?: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex h-10 items-center justify-center rounded-lg text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
        !active && 'border border-input bg-background text-muted-foreground hover:bg-accent',
        active &&
          tone === 'blue' &&
          'border-2 border-blue-500 bg-blue-50 text-blue-600 dark:bg-blue-950/40',
        active &&
          tone === 'amber' &&
          'border-2 border-amber-500 bg-amber-50 text-amber-600 dark:bg-amber-950/40',
      )}
    >
      {children}
    </button>
  )
}

function ImportUploadForm({ lockedModule, onClose, onCreated }: ImportUploadFormProps) {
  const [module, setModule] = useState<number>(lockedModule ?? DEFAULT_MODULE)
  const [mode, setMode] = useState<number>(IMPORT_MODE_DRY_RUN)
  const [file, setFile] = useState<File | null>(null)
  const [downloading, setDownloading] = useState(false)

  const uploadMutation = useUploadImport()
  const busy = uploadMutation.isPending
  // Lỗi từ bước upload (vd sai file cho bảng) — hiện ngay trong hộp thoại.
  const uploadError = uploadMutation.isError ? extractErrorMessage(uploadMutation.error) : null

  const selected = IMPORT_MODULE_OPTIONS.find((o) => o.value === module)
  const hasTemplate = !!selected?.hasTemplate

  async function handleTemplate() {
    setDownloading(true)
    try {
      await importApi.downloadTemplate(module, `mau_import_${IMPORT_MODULE_LABELS[module] || module}.xlsx`)
    } catch {
      toast.error('Không tải được file mẫu')
    } finally {
      setDownloading(false)
    }
  }

  function handleFiles(files: File[]) {
    const picked = files[0]
    if (!picked) return
    const name = picked.name.toLowerCase()
    if (!name.endsWith('.xlsx') && !name.endsWith('.csv')) {
      toast.error('Chỉ nhận file .xlsx hoặc .csv')
      return
    }
    setFile(picked)
    uploadMutation.reset()
  }

  function handleSubmit() {
    if (!file) {
      toast.error('Vui lòng chọn tệp .xlsx')
      return
    }
    uploadMutation.mutate(
      { module, mode, file },
      {
        onSuccess: (batch) => {
          onClose()
          onCreated?.(batch.id)
        },
      },
    )
  }

  return (
    <>
      {/* Header — icon nền gradient + tiêu đề + mô tả */}
      <DialogHeader className="flex-row items-center gap-3 border-b px-6 py-4 text-left">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-cyan-500">
          <FileUp className="size-5 text-white" />
        </div>
        <div className="min-w-0">
          <DialogTitle className="text-base font-bold">Nhập dữ liệu</DialogTitle>
          <DialogDescription className="text-xs">
            Chọn file để nhập dữ liệu vào hệ thống
          </DialogDescription>
        </div>
      </DialogHeader>

      {/* Body */}
      <div className="space-y-4 px-6 py-5">
        {/* Chọn Phân hệ → Bảng dữ liệu (đồng nhất với hộp thoại Xuất) */}
        <ModuleTablePicker
          tables={IMPORT_TABLES}
          value={String(module)}
          onChange={(v) => {
            setModule(Number(v))
            uploadMutation.reset()
          }}
          disabled={busy || lockedModule != null}
        />

        {/* Chế độ — hai ô bấm */}
        <div className="space-y-1.5">
          <label className="text-sm font-semibold text-foreground">Chế độ</label>
          <div className="grid grid-cols-2 gap-2">
            <ModeTile
              active={mode === IMPORT_MODE_DRY_RUN}
              tone="blue"
              disabled={busy}
              onClick={() => setMode(IMPORT_MODE_DRY_RUN)}
            >
              Chạy thử
            </ModeTile>
            <ModeTile
              active={mode === IMPORT_MODE_APPLY}
              tone="amber"
              disabled={busy}
              onClick={() => setMode(IMPORT_MODE_APPLY)}
            >
              Ghi
            </ModeTile>
          </div>
        </div>

        {/* Nhãn file + tải mẫu */}
        <div>
          <div className="mb-1.5 flex items-center justify-between gap-2">
            <label className="text-sm font-semibold text-foreground">File nhập dữ liệu</label>
            {hasTemplate && (
              <Button
                type="button"
                variant="ghost"
                size="xs"
                className="h-auto gap-1 py-0.5 text-xs text-primary hover:text-primary"
                disabled={downloading}
                onClick={handleTemplate}
              >
                {downloading ? <Loader2 className="size-3.5 animate-spin" /> : <Download className="size-3.5" />}
                Tải file mẫu
              </Button>
            )}
          </div>

          {file ? (
            <div className="flex items-center gap-3 rounded-xl border bg-muted/30 p-3">
              <FileSpreadsheet className="size-8 shrink-0 text-emerald-600" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground" title={file.name}>
                  {file.name}
                </p>
                <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                title="Bỏ tệp đã chọn"
                disabled={busy}
                onClick={() => setFile(null)}
              >
                <X className="size-4" />
              </Button>
            </div>
          ) : (
            <FileDropzone
              className="rounded-xl py-7"
              hint="Kéo thả file .xlsx hoặc .csv vào đây, hoặc bấm để chọn"
              accept=".xlsx,.csv"
              disabled={busy}
              onFiles={handleFiles}
            >
              <span className="text-xs text-muted-foreground">Nhận file Excel (.xlsx) hoặc CSV (.csv)</span>
            </FileDropzone>
          )}
        </div>

        {/* Ghi chú theo chế độ */}
        <div
          className={cn(
            'flex items-start gap-2 rounded-xl border p-3 text-xs',
            mode === IMPORT_MODE_DRY_RUN
              ? 'border-blue-200 bg-blue-50/70 text-blue-900 dark:border-blue-900/50 dark:bg-blue-950/30 dark:text-blue-200'
              : 'border-amber-200 bg-amber-50/70 text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200',
          )}
        >
          <Info className="mt-0.5 size-4 shrink-0" />
          {mode === IMPORT_MODE_DRY_RUN ? (
            <p>
              <strong className="font-semibold">Chạy thử (Dry-run):</strong> Hệ thống sẽ kiểm tra toàn
              bộ dữ liệu trong file nhưng <strong className="font-semibold">chưa ghi vào CSDL</strong>.
              Bạn có thể xem báo cáo cảnh báo/lỗi trước khi quyết định ghi thật.
            </p>
          ) : (
            <p>
              <strong className="font-semibold">Chế độ Ghi:</strong> dữ liệu sẽ được{' '}
              <strong className="font-semibold">ghi thực tế</strong> vào hệ thống. Có thể hoàn tác sau
              khi import.
            </p>
          )}
        </div>

        {/* Lỗi upload (vd sai file cho bảng) — báo ngay tại đây, không tạo lần import */}
        {uploadError && (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <p>{uploadError}</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <DialogFooter className="border-t px-6 py-4">
        <Button type="button" variant="ghost" disabled={busy} onClick={onClose}>
          Huỷ
        </Button>
        <Button type="button" disabled={busy || !file} onClick={handleSubmit} className="gap-2">
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
          Bắt đầu import
        </Button>
      </DialogFooter>
    </>
  )
}
