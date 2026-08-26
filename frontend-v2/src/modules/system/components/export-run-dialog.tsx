import { Download, FileDown, Info, Loader2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'

import { EXPORT_FORMAT_OPTIONS, type ExportFormat } from '../config/export-meta'
import { useExportEntities, useRunExport } from '../hooks/use-exports'
import { ModuleTablePicker, type DataTableOption } from './module-table-picker'

interface ExportRunDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ExportRunDialog({ open, onOpenChange }: ExportRunDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="gap-0 overflow-hidden p-0 sm:max-w-[600px]"
        //  Chỉ đóng bằng nút Huỷ hoặc X — bấm ra vùng xám / nhấn Esc KHÔNG đóng.
        onInteractOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        {/* Component con để state khởi tạo lại mỗi lần mở (tránh set-state-in-effect). */}
        {open && <ExportRunForm onClose={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function ExportRunForm({ onClose }: { onClose: () => void }) {
  const { data: entities, isLoading } = useExportEntities()
  const [entity, setEntity] = useState<string>('')
  const [format, setFormat] = useState<ExportFormat>('xlsx')

  const runMutation = useRunExport()
  const busy = runMutation.isPending

  // Chọn sẵn bảng đầu tiên khi danh sách vừa nạp xong (không cần useEffect: đọc
  // trực tiếp lúc render, chốt giá trị hiệu lực).
  const effectiveEntity = entity || entities?.[0]?.entity || ''
  const selectedLabel = entities?.find((e) => e.entity === effectiveEntity)?.label ?? ''

  const exportTables: DataTableOption[] = (entities ?? []).map((e) => ({
    value: e.entity,
    label: e.label,
    moduleId: e.module,
  }))

  function handleRun() {
    if (!effectiveEntity) return
    runMutation.mutate(
      { entity: effectiveEntity, format, filename: `xuat-${effectiveEntity}.${format}` },
      { onSuccess: () => onClose() },
    )
  }

  const noEntity = !isLoading && (entities?.length ?? 0) === 0

  return (
    <>
      <DialogHeader className="flex-row items-center gap-3 border-b px-6 py-4 text-left">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500">
          <FileDown className="size-5 text-white" />
        </div>
        <div className="min-w-0">
          <DialogTitle className="text-base font-bold">Xuất dữ liệu</DialogTitle>
          <DialogDescription className="text-xs">
            Chọn bảng và định dạng để tải toàn bộ dữ liệu (theo phạm vi được phép).
          </DialogDescription>
        </div>
      </DialogHeader>

      <div className="space-y-4 px-6 py-5">
        {/* Chọn Phân hệ → Bảng dữ liệu (đồng nhất với hộp thoại Nhập) */}
        <ModuleTablePicker
          tables={exportTables}
          value={effectiveEntity}
          onChange={setEntity}
          disabled={busy || isLoading || noEntity}
        />

        {/* Định dạng */}
        <div className="space-y-1.5">
          <label className="text-sm font-semibold text-foreground">Định dạng</label>
          <div className="grid grid-cols-2 gap-2">
            {EXPORT_FORMAT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                disabled={busy}
                onClick={() => setFormat(opt.value)}
                className={cn(
                  'flex h-10 items-center justify-center rounded-lg text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
                  format === opt.value
                    ? 'border-2 border-emerald-500 bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40'
                    : 'border border-input bg-background text-muted-foreground hover:bg-accent',
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {noEntity ? (
          <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
            <Info className="mt-0.5 size-4 shrink-0" />
            <p>Bạn chưa được cấp quyền xuất bảng nào. Liên hệ quản trị để được cấp quyền «Xuất».</p>
          </div>
        ) : (
          <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50/70 p-3 text-xs text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-200">
            <Info className="mt-0.5 size-4 shrink-0" />
            <p>
              Tải toàn bộ <strong className="font-semibold">{selectedLabel}</strong> ra file{' '}
              <strong className="font-semibold uppercase">{format}</strong>. Lần xuất này sẽ được ghi
              vào nhật ký bên dưới.
            </p>
          </div>
        )}
      </div>

      <DialogFooter className="border-t px-6 py-4">
        <Button type="button" variant="ghost" disabled={busy} onClick={onClose}>
          Huỷ
        </Button>
        <Button type="button" className="gap-2" disabled={busy || noEntity || !effectiveEntity} onClick={handleRun}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
          Xuất dữ liệu
        </Button>
      </DialogFooter>
    </>
  )
}
