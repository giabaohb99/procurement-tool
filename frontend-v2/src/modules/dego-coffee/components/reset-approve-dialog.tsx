import { useState } from 'react'
import { toast } from 'sonner'

import { Badge } from '@/shared/ui/badge'
import { useResetExecute, useResetPreview } from '../hooks/use-coffee'
import { formatPoints, formatSignedPoints } from '../utils/format-points'
import { CoffeeDialogShell } from './coffee-dialog-shell'

interface ResetApproveDialogProps {
  onClose: () => void
}

/**
 * CẤP PHÁT KỲ (A-06 — chốt 08/09/2026: từng kỳ PHẢI có người duyệt): xem bảng
 * DỰ KIẾN (thu cuối kỳ + cấp mới từng người) rồi mới CHỐT. Beat ngày 1 chỉ nhắc.
 */
export function ResetApproveDialog({ onClose }: ResetApproveDialogProps) {
  const { data, isLoading, isError } = useResetPreview()
  const execute = useResetExecute()
  const [done, setDone] = useState(false)

  const rows = data?.preview ?? []
  const pending = rows.filter((r) => !r.already_granted)
  const totalGrant = pending.reduce((s, r) => s + r.grant, 0)

  function handleConfirm() {
    if (!data || pending.length === 0) {
      onClose()
      return
    }
    execute.mutate(data.period, {
      onSuccess: () => {
        toast.success(`Đã chốt cấp phát kỳ ${data.period} — cấp ${pending.length} người, tổng ${formatPoints(totalGrant)} điểm`)
        setDone(true)
        onClose()
      },
    })
  }

  return (
    <CoffeeDialogShell
      title={`Cấp phát kỳ ${data?.period ?? ''}`}
      description="Bảng dự kiến — chưa ghi gì cho tới khi bấm Chốt. Chốt lại cùng kỳ không nhân đôi điểm."
      dirty={false}
      pending={execute.isPending || done}
      confirmLabel={
        pending.length === 0 ? 'Đóng' : `Chốt cấp phát (${pending.length} người)`
      }
      onConfirm={handleConfirm}
      onClose={onClose}
      widthClass="sm:max-w-[640px]"
    >
      {isLoading && <p className="text-sm text-muted-foreground">Đang tính bảng dự kiến…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          Không tải được bảng dự kiến — kiểm tra quyền «Duyệt» trên Sổ điểm.
        </p>
      )}
      {rows.length > 0 && (
        <div className="max-h-72 overflow-y-auto rounded-md border">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-muted/80 text-left text-xs text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Nhân sự</th>
                <th className="px-3 py-2 font-medium">Cấp</th>
                <th className="px-3 py-2 text-right font-medium">Thu cuối kỳ</th>
                <th className="px-3 py-2 text-right font-medium">Cấp mới</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.employee_id} className="border-t">
                  <td className="px-3 py-1.5">
                    <span className="font-medium">{r.employee_name}</span>
                    <span className="ml-1.5 font-mono text-xs text-muted-foreground">
                      {r.employee_code}
                    </span>
                  </td>
                  <td className="px-3 py-1.5">{r.level_label}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums">
                    {r.already_granted ? '—' : r.expire ? formatSignedPoints(r.expire) : '0'}
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums">
                    {r.already_granted ? (
                      <Badge variant="outline">Đã cấp</Badge>
                    ) : (
                      <span className="font-medium">{formatPoints(r.grant)}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && data.no_policy.length > 0 && (
        <p className="text-sm text-amber-600 dark:text-amber-400">
          {data.no_policy.length} người có cấp CHƯA khai mức điểm — không nằm trong bảng, khai ở
          «Chính sách cấp điểm» rồi mở lại.
        </p>
      )}
      {rows.length > 0 && pending.length > 0 && (
        <p className="text-sm">
          Tổng cấp kỳ này:{' '}
          <span className="font-semibold tabular-nums">{formatPoints(totalGrant)}</span> điểm cho{' '}
          {pending.length} người.
        </p>
      )}
      {rows.length === 0 && !isLoading && !isError && (
        <p className="text-sm text-muted-foreground">
          Không có ai chờ cấp — chưa có thành viên thuộc cấp có mức, hoặc tất cả đã cấp kỳ này.
        </p>
      )}
    </CoffeeDialogShell>
  )
}
