import { motion } from 'motion/react'
import { Monitor, Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useCallback, type MouseEvent } from 'react'
import { flushSync } from 'react-dom'

import { cn } from '@/shared/utils/cn'

const OPTIONS = [
  { value: 'system', icon: Monitor, label: 'Theo hệ thống' },
  { value: 'light', icon: Sun, label: 'Nền sáng' },
  { value: 'dark', icon: Moon, label: 'Nền tối' },
] as const

/**
 * Chọn giao diện: **Theo hệ thống · Sáng · Tối**.
 *
 * Ba lựa chọn chứ không phải một công tắc bật/tắt, vì "theo hệ thống" là một ý
 * định RIÊNG — người đặt máy tự sáng ban ngày tối ban đêm muốn ứng dụng đi theo,
 * chứ không phải chốt cứng một bên. Công tắc hai trạng thái không diễn tả được
 * ý đó.
 *
 * Đổi giao diện dùng **View Transitions API**: nền mới loang ra từ chính chỗ vừa
 * bấm thay vì đảo màu đột ngột cả màn hình (xem `@keyframes theme-reveal` trong
 * `index.css`).
 *
 * ⚠️ `flushSync` là bắt buộc quanh `setTheme`: `startViewTransition` chụp ảnh DOM
 * ngay sau callback, mà React gộp cập nhật theo lô — không ép ghi ngay thì nó
 * chụp phải khung hình CŨ, hiệu ứng loang ra rồi mà màu vẫn y nguyên.
 */
export function ThemeSwitch() {
  const { theme, setTheme } = useTheme()

  const pick = useCallback(
    (next: string, event: MouseEvent<HTMLButtonElement>) => {
      if (next === theme) return

      const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (!document.startViewTransition || reducedMotion) {
        setTheme(next)
        return
      }

      //  Tâm vòng loang = chỗ con trỏ vừa bấm; CSS đọc qua `--x` / `--y`.
      document.documentElement.style.setProperty('--x', `${event.clientX}px`)
      document.documentElement.style.setProperty('--y', `${event.clientY}px`)
      document.startViewTransition(() => {
        flushSync(() => setTheme(next))
      })
    },
    [theme, setTheme],
  )

  return (
    <div
      role="radiogroup"
      aria-label="Giao diện"
      className="flex items-center gap-0.5 rounded-full border bg-muted/50 p-[3px]"
    >
      {OPTIONS.map(({ value, icon: Icon, label }) => {
        const active = theme === value
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={label}
            title={label}
            onClick={(event) => pick(value, event)}
            className={cn(
              'relative grid size-6 place-items-center rounded-full transition-colors',
              active ? 'text-foreground' : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {/*  Viên nền TRƯỢT từ lựa chọn cũ sang lựa chọn mới thay vì tắt chỗ
                 này bật chỗ kia — `layoutId` để `motion` tự nối hai vị trí. Mắt
                 bám theo được là đỡ phải dò lại xem đang chọn cái nào. */}
            {active && (
              <motion.span
                layoutId="theme-switch-pill"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                className="absolute inset-0 rounded-full bg-card shadow-sm ring-1 ring-border"
              />
            )}
            <Icon className="relative size-3" />
          </button>
        )
      })}
    </div>
  )
}
