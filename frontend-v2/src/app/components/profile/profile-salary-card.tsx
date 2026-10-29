import { Eye, EyeOff, Wallet } from 'lucide-react'
import { useState } from 'react'

import type { Employee } from '@/modules/hr/types/employee'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'

interface ProfileSalaryCardProps {
  employee: Employee
}

const MASK = '••••'

/**
 * «Lương của tôi» ở Trang cá nhân (duoc-CR-693). Hai số đọc thẳng `/api/employees/me` — backend
 * chỉ trả số lương cho CHÍNH chủ, người khác (kể cả admin) không có đường nào xem.
 *
 * Mặc định CHE số: Trang cá nhân hay được mở khi đang chia sẻ màn hình (họp trực tuyến, nhờ
 * người khác xem giúp), hiện sẵn là lộ lương trước mặt người khác. Bấm con mắt mới hiện; trạng
 * thái không lưu lại, mở lại trang là che lại.
 */
export function ProfileSalaryCard({ employee }: ProfileSalaryCardProps) {
  const [shown, setShown] = useState(false)
  const salary = employee.salary_monthly ?? 0
  const allowance = employee.allowance_monthly ?? 0
  const hasSalary = salary > 0 || allowance > 0

  const rows = [
    { label: 'Lương', value: salary },
    { label: 'Phụ cấp', value: allowance },
    { label: 'Tổng', value: salary + allowance, strong: true },
  ]

  return (
    <FormCard
      title="Lương của tôi"
      icon={Wallet}
      iconClassName="text-muted-foreground"
      actions={
        hasSalary && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-pressed={shown}
            aria-label={shown ? 'Ẩn số lương' : 'Hiện số lương'}
            onClick={() => setShown((v) => !v)}
          >
            {shown ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            {shown ? 'Ẩn số' : 'Xem số'}
          </Button>
        )
      }
    >
      {hasSalary ? (
        <div className="divide-y rounded-md border">
          {rows.map((row) => (
            <div
              key={row.label}
              className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm"
            >
              <span className={cn('text-muted-foreground', row.strong && 'font-medium text-foreground')}>
                {row.label}
              </span>
              <span className="shrink-0 tabular-nums">
                <span className={cn(row.strong && 'font-semibold text-navy dark:text-foreground')}>
                  {shown ? formatMoney(row.value) : MASK}
                </span>
                <span className="text-muted-foreground"> đ/tháng</span>
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-2 text-sm text-muted-foreground">Phòng Nhân sự chưa nhập lương cho bạn.</p>
      )}
    </FormCard>
  )
}
