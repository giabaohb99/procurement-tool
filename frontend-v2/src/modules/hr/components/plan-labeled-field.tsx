import type { ReactNode } from 'react'

import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { cn } from '@/shared/utils/cn'

interface PlanLabeledFieldProps {
  label: string
  /** Gắn `<Label htmlFor>` vào ô — thiếu thì bấm nhãn không vào ô. */
  htmlFor?: string
  required?: boolean
  hint?: ReactNode
  fullWidth?: boolean
  children: ReactNode
  className?: string
}

/**
 * Ô có nhãn của trang Kế hoạch / Mẫu khoản chi phí — trang dùng bản nháp `useState` (không
 * react-hook-form) nên không dùng được `FormItem` của `shared/ui/form.tsx` (gắn với `useFormContext`).
 */
export function PlanLabeledField({
  label,
  htmlFor,
  required,
  hint,
  fullWidth,
  children,
  className,
}: PlanLabeledFieldProps) {
  return (
    <div className={cn('grid gap-1.5', fullWidth && 'sm:col-span-2', className)}>
      <Label htmlFor={htmlFor}>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}
