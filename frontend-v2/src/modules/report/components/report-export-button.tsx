import { Download, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'

import type { PermissionEntity } from '@/core/authorization/permission-types'

import { reportAnalyticsApi } from '../api/report-analytics-api'

interface ReportExportButtonProps {
  endpoint: string
  entity: PermissionEntity
  params: Record<string, string>
  filename: string
}

/**
 * Nút "Xuất Excel" của trang báo cáo — chỉ hiện khi `can(entity, 'export')`
 * (quyền thật vẫn ở backend, đây chỉ để đỡ vướng mắt).
 *
 * Chặn bấm đúp bằng `useSingleFlight`: `disabled={isExporting}` một mình
 * KHÔNG đủ — đó là state React, chỉ có tác dụng SAU lần render kế tiếp, nên
 * vài cú bấm liên tiếp trong cùng một nhịp vẫn lọt qua và bắn nhiều lượt tải
 * (xem `use-single-flight.ts`).
 */
export function ReportExportButton({
  endpoint,
  entity,
  params,
  filename,
}: ReportExportButtonProps) {
  const { can } = usePermission()
  const [isExporting, setIsExporting] = useState(false)
  const runOnce = useSingleFlight()

  if (!can(entity, 'export')) return null

  const handleExport = () =>
    runOnce(async () => {
      setIsExporting(true)
      try {
        await reportAnalyticsApi.export(endpoint, params, filename)
      } catch {
        toast.error('Không xuất được báo cáo. Thử lọc bớt rồi xuất lại.')
      } finally {
        setIsExporting(false)
      }
    })

  return (
    <Button variant="outline" onClick={handleExport} disabled={isExporting}>
      {isExporting ? <Loader2 className="animate-spin" /> : <Download />}
      Xuất Excel
    </Button>
  )
}
