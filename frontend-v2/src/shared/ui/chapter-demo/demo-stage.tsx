import { AnimatePresence, motion } from 'motion/react'
import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Khối dựng cảnh cho kịch bản demo (ai-CR-214): khung cửa sổ ứng dụng, hộp thoại nổi trên
 * nền mờ, thông báo góc dưới. Chỉ là vỏ trình bày — nội dung bên trong là component v2
 * thật (Card, Badge, Button…) với dữ liệu giả.
 */

interface DemoWindowProps {
  title: string
  /** Dòng phụ bên phải thanh tiêu đề (vd đường dẫn màn). */
  hint?: string
  children: ReactNode
  className?: string
}

export function DemoWindow({ title, hint, children, className }: DemoWindowProps) {
  return (
    <div className={cn('flex h-full flex-col overflow-hidden rounded-lg border bg-background shadow-sm', className)}>
      <div className="flex items-center gap-2 border-b bg-muted/50 px-3 py-2 text-xs">
        <span className="flex gap-1" aria-hidden>
          <span className="size-2 rounded-full bg-muted-foreground/40" />
          <span className="size-2 rounded-full bg-muted-foreground/40" />
          <span className="size-2 rounded-full bg-muted-foreground/40" />
        </span>
        <span className="font-medium">{title}</span>
        {hint && <span className="ml-auto truncate text-muted-foreground">{hint}</span>}
      </div>
      <div className="min-h-0 flex-1 overflow-hidden p-3">{children}</div>
    </div>
  )
}

interface DemoDialogProps {
  open: boolean
  title: string
  children: ReactNode
  /** Tắt chuyển động (giảm chuyển động / ảnh tĩnh). */
  still?: boolean
  className?: string
}

/** Hộp thoại đang thao tác: nền phía sau mờ đi, hộp nổi lên giữa khung. */
export function DemoDialog({ open, title, children, still = false, className }: DemoDialogProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="dialog"
          className="absolute inset-0 z-10 flex items-center justify-center bg-background/60 backdrop-blur-[2px]"
          initial={still ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            role="dialog"
            aria-label={title}
            className={cn('w-[min(90%,26rem)] rounded-lg border bg-background p-4 shadow-lg', className)}
            initial={still ? false : { opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.25 }}
          >
            <p className="mb-3 text-sm font-semibold">{title}</p>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

interface DemoToastProps {
  open: boolean
  children: ReactNode
  still?: boolean
}

export function DemoToast({ open, children, still = false }: DemoToastProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="toast"
          role="status"
          className="absolute right-3 bottom-3 z-20 max-w-[70%] rounded-md border bg-background px-3 py-2 text-xs shadow-md"
          initial={still ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/** Ô chữ giả đang được gõ — hiện vạch nháy khi còn gõ dở. */
export function DemoTypedField({ value, full, label }: { value: string; full: string; label: string }) {
  const typing = value.length > 0 && value.length < full.length
  return (
    <div className="space-y-1">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <div className="min-h-8 rounded-md border bg-background px-2 py-1.5 text-xs">
        {value}
        {typing && <span className="ml-px inline-block h-3 w-px animate-pulse bg-foreground align-middle" aria-hidden />}
      </div>
    </div>
  )
}
