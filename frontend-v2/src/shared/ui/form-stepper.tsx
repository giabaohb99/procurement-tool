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
 * Dải bước của form nhiều bước.
 *
 * Mỗi bước là một CHẤM TRÒN kèm nhãn, nối nhau bằng một đường liền chạy suốt
 * dải và **tô dần theo tiến độ** — nhìn một cái ra ngay đang ở đâu, còn mấy
 * bước. Cố ý bỏ khung hộp quanh từng bước: đóng khung làm dải này nặng ngang
 * các thẻ nội dung bên dưới, trong khi nó chỉ là thanh chỉ đường.
 *
 * Bước đã qua hiện dấu tích và bấm được để quay lại.
 */
export function FormStepper({ steps, current, onGoTo, className }: FormStepperProps) {
  const last = steps.length - 1

  return (
    <ol className={cn('flex items-start', className)}>
      {steps.map((step, index) => {
        const done = index < current
        const active = index === current
        const clickable = done && Boolean(onGoTo)

        return (
          <li
            key={step.title}
            // Bước cuối KHÔNG chiếm phần dư: cho nó co lại thì nhãn không bị
            // kéo giãn ra tận mép phải, dải bước gọn về bên trái như thanh
            // chỉ đường thật.
            className={cn('flex min-w-0 items-start', index < last && 'flex-1')}
          >
            <button
              type="button"
              disabled={!clickable}
              onClick={() => onGoTo?.(index)}
              aria-current={active ? 'step' : undefined}
              className={cn(
                'group flex min-w-0 items-center gap-3 rounded-lg text-left transition-opacity',
                'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none',
                clickable ? 'hover:opacity-70' : 'cursor-default',
              )}
            >
              <span
                className={cn(
                  'flex size-9 shrink-0 items-center justify-center rounded-full border text-sm font-semibold tabular-nums transition-colors',
                  (active || done) && 'border-primary bg-primary text-primary-foreground',
                  // Quầng sáng quanh bước ĐANG đứng — thứ duy nhất tách nó khỏi
                  // bước đã xong, vì cả hai cùng tô màu chính.
                  active && 'ring-4 ring-primary/15',
                  !active && !done && 'bg-background text-muted-foreground',
                )}
              >
                {done ? <Check className="size-4" /> : index + 1}
              </span>

              <span className="min-w-0">
                <span
                  className={cn(
                    'block truncate text-sm font-medium transition-colors',
                    active || done ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {step.title}
                </span>
                {step.description && (
                  <span className="hidden truncate text-xs text-muted-foreground sm:block">
                    {step.description}
                  </span>
                )}
              </span>
            </button>

            {/* Đường nối — bước cuối không có gì để nối tới.
                `mt-[17px]` = nửa chấm tròn (36px) trừ nửa bề dày đường (2px):
                đường cắt đúng tâm chấm chứ không lệch lên xuống. */}
            {index < last && (
              <span
                aria-hidden
                className="mx-3 mt-[17px] h-0.5 min-w-6 flex-1 overflow-hidden rounded-full bg-border"
              >
                <span
                  className="block h-full rounded-full bg-primary transition-[width] duration-300 ease-out"
                  style={{ width: done ? '100%' : '0%' }}
                />
              </span>
            )}
          </li>
        )
      })}
    </ol>
  )
}
