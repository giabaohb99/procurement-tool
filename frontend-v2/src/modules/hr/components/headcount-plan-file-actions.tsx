import { FileSpreadsheet, FileUp, Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { headcountPlanApi } from '../api/headcount-plan-api'
import { useImportHeadcountPlanLines } from '../hooks/use-headcount-plans'
import { splitImportErrorMessage } from '../utils/headcount-plan-options'

interface HeadcountPlanFileActionsProps {
  planId: number
  /** Tên tệp xuất, vd `ke-hoach-nhan-su-Q3-2026.xlsx`. */
  exportName: string
  /** Sau khi nhập xong — trang nạp lại bản nháp từ máy chủ (dòng vị trí vừa thay). */
  onImported: () => void
}

/**
 * «Xuất Excel» một kế hoạch (dòng vị trí + bảng tính) và «Nhập CSV dòng vị trí» vào CHÍNH kế hoạch
 * này (`position_code, hc_1..hc_n, <mã khoản>…`). Chỉ có ở kế hoạch ĐÃ LƯU — chưa có id thì không có
 * chỗ nhập vào. Nhập là NGUYÊN KHỐI: một dòng lỗi thì không ghi gì, nên lỗi bày đủ từng dòng.
 */
export function HeadcountPlanFileActions({ planId, exportName, onImported }: HeadcountPlanFileActionsProps) {
  const { can } = usePermission()
  const inputRef = useRef<HTMLInputElement>(null)
  const once = useSingleFlight()
  const importLines = useImportHeadcountPlanLines(planId)
  const [busy, setBusy] = useState<'export' | 'import' | null>(null)
  const [errors, setErrors] = useState<string[]>([])

  const canExport = can('headcount_plan', 'export')
  const canImport = can('headcount_plan', 'write')
  if (planId <= 0 || (!canExport && !canImport)) return null

  const handleExport = () =>
    once(async () => {
      setBusy('export')
      try {
        await headcountPlanApi.exportXlsx(planId, exportName)
      } catch (error) {
        toast.error(extractErrorMessage(error))
      } finally {
        setBusy(null)
      }
    })

  const handleFile = (file: File | undefined) =>
    once(async () => {
      if (!file) return
      setBusy('import')
      try {
        await importLines.mutateAsync(file)
        toast.success('Đã nhập dòng vị trí từ tệp CSV')
        onImported()
      } catch (error) {
        setErrors(splitImportErrorMessage(extractErrorMessage(error)))
      } finally {
        setBusy(null)
        //  Cho chọn lại CÙNG tệp sau khi sửa: input giữ tên cũ thì `change` không bắn lần hai.
        if (inputRef.current) inputRef.current.value = ''
      }
    })

  return (
    <>
      {canExport && (
        <Button type="button" variant="outline" size="sm" onClick={() => void handleExport()} disabled={busy !== null}>
          {busy === 'export' ? <Loader2 className="size-4 animate-spin" /> : <FileSpreadsheet className="size-4" />}
          Xuất Excel
        </Button>
      )}
      {canImport && (
        <>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => inputRef.current?.click()}
            disabled={busy !== null}
            title="Thay dòng vị trí bằng tệp CSV — cột position_code, hc_1..hc_n, mã các khoản nhập theo vị trí"
          >
            {busy === 'import' ? <Loader2 className="size-4 animate-spin" /> : <FileUp className="size-4" />}
            Nhập CSV dòng vị trí
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            aria-label="Chọn tệp CSV dòng vị trí"
            onChange={(e) => void handleFile(e.target.files?.[0])}
          />
        </>
      )}
      <Dialog open={errors.length > 0} onOpenChange={(open) => !open && setErrors([])}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Chưa nhập được tệp</DialogTitle>
            <DialogDescription>Không dòng nào được ghi. Sửa các dòng dưới đây trong tệp rồi nhập lại.</DialogDescription>
          </DialogHeader>
          <ul className="max-h-80 list-disc space-y-1 overflow-y-auto pl-5 text-sm">
            {errors.map((line, i) => (
              <li key={`${i}-${line}`}>{line}</li>
            ))}
          </ul>
        </DialogContent>
      </Dialog>
    </>
  )
}
