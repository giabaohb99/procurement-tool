import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api/response-envelope'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Textarea } from '@/shared/ui/textarea'

import { useModerateForumPost } from '../hooks/use-moderate-forum-post'

interface ModeratePostDialogProps {
  postId: number
  /** Hộp này chỉ cho hai thao tác CẦN lý do — khôi phục đi thẳng, không qua đây. */
  action: 'hide' | 'remove'
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Gỡ bài xong ở trang chi tiết thì phải rời đi — bài không còn mở được nữa. */
  onRemoved?: () => void
}

const COPY = {
  hide: {
    title: 'Ẩn bài viết này?',
    description:
      'Bài sẽ biến khỏi bảng tin của mọi người; tác giả vẫn thấy bài ở trang cá nhân kèm lý do và nhận thông báo.',
    submit: 'Ẩn bài viết',
    done: 'Đã ẩn bài viết',
  },
  remove: {
    title: 'Gỡ bài viết này?',
    description:
      'Bài sẽ biến khỏi hệ thống với tất cả mọi người, kể cả tác giả — tác giả nhận thông báo kèm lý do. Thao tác này không hoàn tác được.',
    submit: 'Gỡ bài viết',
    done: 'Đã gỡ bài viết',
  },
} as const

/**
 * Hộp lý do kiểm duyệt (F5) — QĐ-D1: không ẩn lặng lẽ, lý do bắt buộc và được
 * gửi nguyên văn cho tác giả qua chuông. Nút gửi khóa tới khi có chữ.
 */
export function ModeratePostDialog({
  postId,
  action,
  open,
  onOpenChange,
  onRemoved,
}: ModeratePostDialogProps) {
  const moderate = useModerateForumPost()
  const [reason, setReason] = useState('')
  const copy = COPY[action]

  async function submit() {
    try {
      await moderate.mutateAsync({ postId, action, reason: reason.trim() })
      toast.success(copy.done)
      setReason('')
      onOpenChange(false)
      if (action === 'remove') onRemoved?.()
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{copy.title}</DialogTitle>
          <DialogDescription>{copy.description}</DialogDescription>
        </DialogHeader>

        <Textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          placeholder="Lý do (bắt buộc) — tác giả sẽ đọc được nguyên văn"
          rows={3}
          autoFocus
        />

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={!reason.trim() || moderate.isPending}
            onClick={() => void submit()}
          >
            {moderate.isPending && <Loader2 className="size-4 animate-spin" />}
            {copy.submit}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
