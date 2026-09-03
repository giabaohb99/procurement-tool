import {
  Book,
  Briefcase,
  Camera,
  Code,
  Coffee,
  Cpu,
  Gamepad2,
  Heart,
  HelpCircle,
  Image,
  Lightbulb,
  Megaphone,
  MessageCircle,
  MessagesSquare,
  Music,
  Newspaper,
  ShoppingCart,
  Star,
  Trophy,
  Users,
  Wrench,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

// why: cột `icon` của box là TÊN icon lucide (kebab-case) hoặc 1 emoji do admin
// gõ tay. Import cả bộ `icons` của lucide để tra động thì phá tree-shaking
// (cả nghìn icon vào bundle), nên khoanh một bộ tên hay dùng; tên lạ mà ngắn
// (emoji) vẽ thẳng chữ, còn lại rơi về icon mặc định.
const BOARD_ICONS: Record<string, LucideIcon> = {
  book: Book,
  briefcase: Briefcase,
  camera: Camera,
  code: Code,
  coffee: Coffee,
  cpu: Cpu,
  'gamepad-2': Gamepad2,
  heart: Heart,
  'help-circle': HelpCircle,
  image: Image,
  lightbulb: Lightbulb,
  megaphone: Megaphone,
  'message-circle': MessageCircle,
  'messages-square': MessagesSquare,
  music: Music,
  newspaper: Newspaper,
  'shopping-cart': ShoppingCart,
  star: Star,
  trophy: Trophy,
  users: Users,
  wrench: Wrench,
}

interface BoardIconProps {
  /** Giá trị cột `icon` của box — tên lucide, emoji, hoặc rỗng. */
  icon: string
  className?: string
}

/** Ô icon vuông bo góc đứng đầu dòng box — khuôn chung cho mọi màn F13b. */
export function BoardIcon({ icon, className }: BoardIconProps) {
  const name = icon.trim().toLowerCase()
  const Icon = BOARD_ICONS[name]
  return (
    <span
      className={cn(
        'flex size-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400',
        className,
      )}
      aria-hidden
    >
      {Icon ? (
        <Icon className="size-5" />
      ) : icon.trim() && icon.trim().length <= 4 ? (
        // emoji (hoặc 1-2 ký tự bất kỳ) — vẽ thẳng chữ, không qua lucide
        <span className="text-lg leading-none">{icon.trim()}</span>
      ) : (
        <MessagesSquare className="size-5" />
      )}
    </span>
  )
}
