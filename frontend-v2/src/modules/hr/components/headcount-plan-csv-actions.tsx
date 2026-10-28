import { Download, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { exportHeadcountPlansCsv } from '../api/headcount-plan-api'

/** Tham số URL của màn được chép sang lời gọi xuất — đúng bộ lọc đang xem, bỏ phân trang. */
const EXPORT_PARAM_KEYS = ['year', 'period_type', 'company_id', 'department_id'] as const

/**
 * Nút «Xuất CSV» của danh sách Kế hoạch nhân sự (duoc-CR-690), gắn qua `renderToolbarExtra`. Gác
 * `headcount_plan.export`, theo đúng bốn ô lọc đang xem.
 *
 * Bộ NHẬP CSV kiểu cũ (một dòng = năm × pháp nhân × phòng, CR-689) đã bỏ: kế hoạch nay có dòng vị trí
 * và khoản chi phí, nên nhập CSV chuyển vào TRANG của từng kế hoạch (nhập dòng vị trí).
 */
export function HeadcountPlanCsvActions() {
  const { can } = usePermission()
  const [searchParams] = useSearchParams()
  const once = useSingleFlight()
  const [busy, setBusy] = useState(false)

  if (!can('headcount_plan', 'export')) return null

  const handleExport = () =>
    once(async () => {
      const params: Record<string, string> = {}
      for (const key of EXPORT_PARAM_KEYS) {
        const v = searchParams.get(key)
        //  `0` (toàn pháp nhân) là giá trị THẬT — chỉ bỏ ô trống và «tất cả».
        if (v && v !== 'all') params[key] = v
      }
      setBusy(true)
      try {
        await exportHeadcountPlansCsv(params)
      } catch (error) {
        toast.error(extractErrorMessage(error))
      } finally {
        setBusy(false)
      }
    })

  return (
    <Button type="button" variant="outline" size="sm" title="Xuất CSV" onClick={() => void handleExport()} disabled={busy}>
      {busy ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
      {/*  Khổ hẹp: chỉ còn biểu tượng — nút đầy chữ đẩy nút «Thêm» ra ngoài màn 390px. */}
      <span className="max-md:sr-only">Xuất CSV</span>
    </Button>
  )
}
