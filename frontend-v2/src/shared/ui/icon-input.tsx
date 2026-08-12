import type { LucideIcon } from 'lucide-react'
import type { ComponentProps } from 'react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

interface IconInputProps extends ComponentProps<'input'> {
  icon: LucideIcon
}

/**
 * Ô nhập có icon nằm trong, cao 48px — kiểu dùng ở các màn xác thực.
 * Icon đổi sang màu thương hiệu khi ô được focus (bắt bằng `group-focus-within`).
 */
export function IconInput({ icon: Icon, className, ...props }: IconInputProps) {
  return (
    <div className="group relative flex items-center">
      <Icon className="pointer-events-none absolute left-3.5 size-[18px] text-slate-400 transition-colors group-focus-within:text-primary" />
      <Input
        className={cn(
          'h-12 rounded-xl pl-[42px] text-[14.5px] shadow-none md:text-[14.5px]',
          'focus-visible:border-primary focus-visible:ring-[3px] focus-visible:ring-primary/15',
          className,
        )}
        {...props}
      />
    </div>
  )
}
