import { useQueryClient } from '@tanstack/react-query'
import { Download, FileUp, Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { getCrudRootKey } from '@/shared/crud'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import {
  exportHeadcountPlansCsv,
  HEADCOUNT_PLAN_API_PATH,
  importHeadcountPlansCsv,
} from '../api/headcount-plan-api'
import { splitImportErrorMessage } from '../utils/headcount-plan-options'

/** Tham số URL của màn được chép sang lời gọi xuất — đúng bộ lọc đang xem, bỏ phân trang. */
const EXPORT_PARAM_KEYS = ['year', 'company_id', 'department_id'] as const

/**
 * Nút «Xuất CSV» + «Nhập CSV» của màn Kế hoạch nhân sự (duoc-CR-689), gắn qua
 * `renderToolbarExtra`. Cột tệp: `year, company_code, department_code, planned_headcount,
 * planned_payroll_monthly, note` — phòng để trống = toàn pháp nhân.
 *
 * - Xuất: gác `headcount_plan.export`, theo đúng ba ô lọc đang xem.
 * - Nhập: gác CẢ `create` LẪN `write` — backend đòi đủ hai (nhập vừa tạo vừa cập nhật). NGUYÊN KHỐI — một dòng
 *   lỗi là không ghi gì — nên lỗi bày đủ từng dòng trong hộp thoại, không cụt thành một toast.
 */
export function HeadcountPlanCsvActions() {
  const { can } = usePermission()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const once = useSingleFlight()
  const [busy, setBusy] = useState<'export' | 'import' | null>(null)
  const [errors, setErrors] = useState<string[]>([])

  const canExport = can('headcount_plan', 'export')
  const canImport = can('headcount_plan', 'create') && can('headcount_plan', 'write')
  if (!canExport && !canImport) return null

  const handleExport = () =>
    once(async () => {
      const params: Record<string, string> = {}
      for (const key of EXPORT_PARAM_KEYS) {
        const v = searchParams.get(key)
        if (v && v !== 'all') params[key] = v
      }
      setBusy('export')
      try {
        await exportHeadcountPlansCsv(params)
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
        const res = await importHeadcountPlansCsv(file)
        toast.success(`Đã nhập kế hoạch: ${res.created} dòng mới, ${res.updated} dòng cập nhật`)
        void queryClient.invalidateQueries({ queryKey: getCrudRootKey(HEADCOUNT_PLAN_API_PATH) })
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
        <Button
          type="button"
          variant="outline"
          size="sm"
          title="Xuất CSV"
          onClick={() => void handleExport()}
          disabled={busy !== null}
        >
          {busy === 'export' ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
          {/*  Khổ hẹp: chỉ còn biểu tượng — ba nút đầy chữ một hàng đẩy nút «Thêm» ra ngoài màn 390px. */}
          <span className="max-md:sr-only">Xuất CSV</span>
        </Button>
      )}
      {canImport && (
        <>
          <Button
            type="button"
            variant="outline"
            size="sm"
            title="Nhập CSV"
            onClick={() => inputRef.current?.click()}
            disabled={busy !== null}
          >
            {busy === 'import' ? <Loader2 className="size-4 animate-spin" /> : <FileUp className="size-4" />}
            <span className="max-md:sr-only">Nhập CSV</span>
          </Button>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            aria-label="Chọn tệp CSV kế hoạch nhân sự"
            onChange={(e) => void handleFile(e.target.files?.[0])}
          />
        </>
      )}
      <Dialog open={errors.length > 0} onOpenChange={(open) => !open && setErrors([])}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Chưa nhập được tệp</DialogTitle>
            <DialogDescription>
              Không dòng nào được ghi. Sửa các dòng dưới đây trong tệp rồi nhập lại.
            </DialogDescription>
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
