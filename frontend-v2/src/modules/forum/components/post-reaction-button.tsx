import { ThumbsUp } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { cn } from '@/shared/utils/cn'

import { useTogglePostReaction } from '../hooks/use-toggle-post-reaction'
import { FORUM_REACTION_KINDS, FORUM_REACTION_META } from '../types/forum-post'
import type { ForumPost, ForumReactionKind } from '../types/forum-post'

const OPEN_DELAY_MS = 350 // rê chuột qua nút bao lâu thì khay hiện — khớp cảm giác Facebook
const CLOSE_DELAY_MS = 250 // trễ khi rời để kịp đưa chuột lên khay, không tắt phũ
const LONG_PRESS_MS = 450 // màn cảm ứng: giữ lâu mở khay, chạm nhanh vẫn là Thích

interface PostReactionButtonProps {
  post: ForumPost
}

/**
 * Nút cảm xúc kiểu Facebook (CR-206): bấm nhanh = Thích (hoặc bỏ cảm xúc đang
 * có), rê chuột / giữ lâu = mở khay 6 cảm xúc. Khay tự vẽ bằng div absolute
 * thay vì Popover của Radix — Popover mở theo CLICK, không có chế độ hover,
 * mà cú click ở đây đã dành cho toggle nhanh.
 */
export function PostReactionButton({ post }: PostReactionButtonProps) {
  const toggleReaction = useTogglePostReaction()
  const [pickerOpen, setPickerOpen] = useState(false)
  const openTimer = useRef<number | undefined>(undefined)
  const closeTimer = useRef<number | undefined>(undefined)
  const longPressTimer = useRef<number | undefined>(undefined)
  // Cờ chặn cú click sinh ra SAU khi long-press đã mở khay — không chặn thì
  // vừa mở khay xong bài đã bị Thích luôn một nhịp.
  const longPressed = useRef(false)

  useEffect(
    () => () => {
      window.clearTimeout(openTimer.current)
      window.clearTimeout(closeTimer.current)
      window.clearTimeout(longPressTimer.current)
    },
    [],
  )

  const current =
    post.my_reaction > 0
      ? FORUM_REACTION_META[post.my_reaction as ForumReactionKind]
      : undefined
  const CurrentIcon = current?.icon ?? ThumbsUp

  const react = (kind: number) => {
    toggleReaction.mutate({ postId: post.id, kind })
    setPickerOpen(false)
  }

  const handlePointerEnter = (e: React.PointerEvent) => {
    if (e.pointerType !== 'mouse') return
    window.clearTimeout(closeTimer.current)
    openTimer.current = window.setTimeout(() => setPickerOpen(true), OPEN_DELAY_MS)
  }
  const handlePointerLeave = (e: React.PointerEvent) => {
    if (e.pointerType !== 'mouse') return
    window.clearTimeout(openTimer.current)
    closeTimer.current = window.setTimeout(() => setPickerOpen(false), CLOSE_DELAY_MS)
  }
  const handlePointerDown = (e: React.PointerEvent) => {
    if (e.pointerType === 'mouse') return
    longPressed.current = false
    longPressTimer.current = window.setTimeout(() => {
      longPressed.current = true
      setPickerOpen(true)
    }, LONG_PRESS_MS)
  }
  const clearLongPress = () => window.clearTimeout(longPressTimer.current)
  const handleClick = () => {
    if (longPressed.current) {
      longPressed.current = false
      return
    }
    // Bấm nhanh: đang có cảm xúc thì bỏ đúng cảm xúc đó, chưa có thì Thích.
    react(post.my_reaction > 0 ? post.my_reaction : 1)
  }

  return (
    <div
      className="relative flex flex-1"
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
    >
      {pickerOpen && (
        <div
          role="menu"
          aria-label="Chọn cảm xúc"
          className="absolute bottom-full left-1/2 z-20 mb-1 flex -translate-x-1/2 items-center gap-0.5 rounded-full border border-border bg-popover px-1.5 py-1 shadow-lg"
        >
          {FORUM_REACTION_KINDS.map((kind) => {
            const meta = FORUM_REACTION_META[kind]
            const Icon = meta.icon
            return (
              <button
                key={kind}
                type="button"
                role="menuitem"
                aria-label={meta.label}
                title={meta.label}
                onClick={() => react(kind)}
                className={cn(
                  'rounded-full p-1.5 transition-transform hover:scale-125 hover:bg-muted',
                  meta.className,
                  post.my_reaction === kind && 'bg-muted',
                )}
              >
                <Icon className={cn('size-5', meta.fill && 'fill-current')} aria-hidden />
              </button>
            )
          })}
        </div>
      )}
      <button
        type="button"
        disabled={toggleReaction.isPending}
        onClick={handleClick}
        onPointerDown={handlePointerDown}
        onPointerUp={clearLongPress}
        onPointerCancel={clearLongPress}
        // Giữ lâu trên mobile hay làm trình duyệt bung menu ngữ cảnh đè lên khay.
        onContextMenu={(e) => longPressed.current && e.preventDefault()}
        className={cn(
          'flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 hover:bg-muted',
          current?.className,
        )}
      >
        <CurrentIcon
          className={cn('size-4', current != null && current.fill && 'fill-current')}
          aria-hidden
        />
        {current?.label ?? 'Thích'}
      </button>
    </div>
  )
}
