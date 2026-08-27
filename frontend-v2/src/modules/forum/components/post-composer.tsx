import { ImagePlus } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'

import { authorInitials } from '../utils/author-initials'
import { PostComposerDialog } from './post-composer-dialog'

/**
 * Thẻ mồi đăng bài ở đầu bảng tin — bấm vào đâu cũng mở hộp thoại đăng bài
 * (kiểu «Bạn đang nghĩ gì?» quen mắt của mạng xã hội).
 */
export function PostComposer() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <>
      <div className="flex items-center gap-3 border-y border-border bg-card p-3 shadow-sm sm:rounded-xl sm:border">
        <Avatar className="size-10">
          <AvatarImage className="object-cover" src={user?.avatar} alt={user?.full_name ?? ''} />
          <AvatarFallback className="bg-navy-solid text-sm font-semibold text-white">
            {authorInitials(user?.full_name ?? '')}
          </AvatarFallback>
        </Avatar>
        <button
          type="button"
          className="flex-1 rounded-full bg-muted px-4 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:bg-accent"
          onClick={() => setOpen(true)}
        >
          Bạn đang nghĩ gì?
        </button>
        <button
          type="button"
          aria-label="Đăng bài kèm ảnh"
          className="rounded-full p-2 text-green-600 transition-colors hover:bg-accent"
          onClick={() => setOpen(true)}
        >
          <ImagePlus className="size-5" />
        </button>
      </div>

      <PostComposerDialog open={open} onOpenChange={setOpen} />
    </>
  )
}
