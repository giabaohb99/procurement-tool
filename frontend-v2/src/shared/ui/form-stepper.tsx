import { Check } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

export interface FormStep {
  title: string
  description?: string
}

interface FormStepperProps {
  /** `readonly` để nhận được cả mảng khai bằng `as const` ở chỗ gọi. */
  steps: readonly FormStep[]
  /** Bước đang đứng, đánh số từ 0. */
  current: number
  /**
   * Nhảy tới một bước ĐÃ QUA. Bỏ trống thì các bước chỉ để xem.
   *
   * Chỉ cho lùi, không cho nhảy tới bước sau: bước sau còn chờ bước trước nhập
   * xong mới kiểm được dữ liệu.
   */
  onGoTo?: (step: number) => void
  className?: string
}

/**
 * Dải bước của form nhiều bước: số thứ tự, tên bước, vạch nối.
 *
 * Bước đã qua hiện dấu tích và bấm được để quay lại — người dùng luôn nhìn ra
 * mình đang ở đâu và còn mấy bước nữa.
 */
export function FormStepper({ steps, current, onGoTo, className }: FormStepperProps) {
  return (
    <ol className={cn('flex items-center gap-2', className)}>
      {steps.map((step, index) => {
        const done = index < current
        const active = index === current
        const clickable = done && Boolean(onGoTo)

        return (
          <li key={step.title} className="flex flex-1 items-center gap-2">
            <button
              type="button"
              disabled={!clickable}
              onClick={() => onGoTo?.(index)}
              className={cn(
                'flex min-w-0 flex-1 items-center gap-3 rounded-lg border p-3 text-left transition-colors',
                active && 'border-primary bg-primary/5',
                done && 'border-primary/40',
                !active && !done && 'border-dashed text-muted-foreground',
                clickable && 'hover:bg-accent',
                !clickable && 'cursor-default',
              )}
            >
              <span
                className={cn(
                  'flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold',
                  (active || done) && 'border-primary bg-primary text-primary-foreground',
                )}
              >
                {done ? <Check className="size-4" /> : index + 1}
              </span>

              <span className="min-w-0">
                <span className="block truncate text-sm font-medium">{step.title}</span>
                {step.description && (
                  <span className="block truncate text-xs text-muted-foreground">
                    {step.description}
                  </span>
                )}
              </span>
            </button>

            {/* Vạch nối — bước cuối không có gì để nối tới. */}
            {index < steps.length - 1 && (
              <span
                aria-hidden
                className={cn('h-px w-6 shrink-0 bg-border', done && 'bg-primary')}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}
