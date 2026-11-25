import { Loader2 } from 'lucide-react'
import { useState } from 'react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Checkbox } from '@/shared/ui/checkbox'

import { useImportPurgePreview, usePurgeImport } from '../hooks/use-imports'

interface ImportBatchPurgeDialogProps {
  batchId: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Hộp thoại "Xóa dữ liệu của lô này" (duoc-CR-784 phase 07) cho lô Định mức bao bì / Báo giá VTBB / Sổ Misa: xem trước số dòng
 * sẽ xóa, dòng đã sửa tay sau khi nhập tách riêng (mặc định giữ lại), rồi mới xóa.
 */
export function ImportBatchPurgeDialog({ batchId, open, onOpenChange }: ImportBatchPurgeDialogProps) {
  const [includeEdited, setIncludeEdited] = useState(false)
  const preview = useImportPurgePreview(batchId, open)
  const purge = usePurgeImport()
  const data = preview.data

  const willDelete = data ? data.untouched + (includeEdited ? data.edited : 0) : 0

  function handleOpenChange(next: boolean) {
    if (!next) setIncludeEdited(false)
    onOpenChange(next)
  }

  return (
    <AlertDialog open={open} onOpenChange={handleOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Xóa dữ liệu của lô này?</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm">
              {preview.isLoading && (
                <p className="flex items-center gap-2">
                  <Loader2 className="size-4 animate-spin" /> Đang đếm số dòng…
                </p>
              )}
              {preview.isError && <p className="text-destructive">Không xem trước được số dòng của lô.</p>}
              {data && data.total === 0 && <p>Lô này không còn dòng dữ liệu nào để xóa.</p>}
              {data && data.total > 0 && (
                <>
                  <p>
                    Sẽ xóa <strong>{data.untouched}</strong> {data.target_label} do lô này nhập.
                  </p>
                  {data.edited > 0 && (
                    <div className="rounded-md border border-amber-300 bg-amber-50 p-2 dark:bg-amber-950/30">
                      <p>
                        Có <strong>{data.edited}</strong> dòng đã được sửa tay sau khi nhập — mặc định được{' '}
                        <strong>giữ lại</strong>.
                      </p>
                      <label className="mt-2 flex cursor-pointer items-center gap-2">
                        <Checkbox
                          checked={includeEdited}
                          onCheckedChange={(v) => setIncludeEdited(v === true)}
                          aria-label="Xóa luôn dòng đã sửa tay"
                        />
                        <span>Xóa luôn {data.edited} dòng đã sửa tay</span>
                      </label>
                    </div>
                  )}
                  {data.recomputes_cutoff && <p>Mốc sổ Misa sẽ được tính lại theo các dòng còn lại.</p>}
                  <p>Hành động này không thể đảo ngược.</p>
                </>
              )}
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={purge.isPending}>Hủy</AlertDialogCancel>
          <AlertDialogAction
            className="bg-rose-600 text-white hover:bg-rose-700"
            disabled={purge.isPending || willDelete === 0}
            onClick={(e) => {
              e.preventDefault()
              purge.mutate({ id: batchId, includeEdited }, { onSuccess: () => handleOpenChange(false) })
            }}
          >
            {purge.isPending && <Loader2 className="mr-1.5 size-4 animate-spin" />}
            {willDelete > 0 ? `Xóa ${willDelete} dòng` : 'Xóa'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
