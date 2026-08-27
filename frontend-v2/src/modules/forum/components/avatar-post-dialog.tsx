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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'

import { uploadForumMedia } from '../api/forum-api'
import { useCreateForumPost } from '../hooks/use-create-forum-post'
import { FORUM_AUDIENCE_META, FORUM_POST_KIND } from '../types/forum-post'
import type { ForumAudience } from '../types/forum-post'
import { readLastAudience, saveLastAudience } from '../utils/last-audience'

interface AvatarPostDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Chính tệp ảnh vừa đặt làm avatar — đăng bài thì tải LẠI lên kho diễn đàn
   * (kho avatar và kho đính kèm là hai chỗ khác nhau, không mượn chéo được). */
  file: File | null
  /** Địa chỉ avatar MỚI backend vừa trả — dùng làm ảnh xem trước cho nhẹ. */
  previewUrl: string
}

/**
 * Hỏi "Đăng lên diễn đàn?" sau khi đổi ảnh đại diện thành công (F10) — hỏi chứ
 * KHÔNG ép: "Để sau" là xong chuyện, không đăng gì cả. Đồng ý thì thành một bài
 * `kind = AVATAR_UPDATE` bình thường trên feed, caption tùy thích, được phép
 * để trống (thẻ bài tự vẽ dòng "đã cập nhật ảnh đại diện").
 */
export function AvatarPostDialog({ open, onOpenChange, file, previewUrl }: AvatarPostDialogProps) {
  const create = useCreateForumPost()
  const [caption, setCaption] = useState('')
  const [audience, setAudience] = useState<ForumAudience>(() => readLastAudience())
  const [posting, setPosting] = useState(false)

  async function submit() {
    if (!file) return
    setPosting(true)
    try {
      const [uploaded] = await uploadForumMedia([file])
      await create.mutateAsync({
        body: caption.trim(),
        audience,
        file_ids: [uploaded.file_id],
        kind: FORUM_POST_KIND.avatarUpdate,
      })
      saveLastAudience(audience)
      setCaption('')
      onOpenChange(false)
      toast.success('Đã đăng lên diễn đàn')
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setPosting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Đăng lên diễn đàn?</DialogTitle>
          <DialogDescription>
            Chia sẻ ảnh đại diện mới với mọi người bằng một bài viết trên bảng tin.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="flex justify-center">
            <img
              src={previewUrl}
              alt="Ảnh đại diện mới"
              className="size-36 rounded-full border object-cover"
            />
          </div>

          <Textarea
            value={caption}
            onChange={(event) => setCaption(event.target.value)}
            placeholder="Viết vài lời cho ảnh mới... (không bắt buộc)"
            rows={3}
            className="max-h-40 text-base sm:text-base"
            autoFocus
          />

          <Select
            value={String(audience)}
            onValueChange={(value) => setAudience(Number(value) as ForumAudience)}
          >
            <SelectTrigger className="h-8 w-fit gap-1.5 text-xs" aria-label="Đối tượng xem">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {([3, 2, 1] as const).map((value) => {
                const meta = FORUM_AUDIENCE_META[value]
                const Icon = meta.icon
                return (
                  <SelectItem key={value} value={String(value)}>
                    <Icon className="size-3.5" aria-hidden />
                    {meta.label}
                  </SelectItem>
                )
              })}
            </SelectContent>
          </Select>
        </div>

        <DialogFooter className="flex-row justify-end gap-2">
          <Button
            type="button"
            variant="ghost"
            className="text-muted-foreground"
            disabled={posting}
            onClick={() => onOpenChange(false)}
          >
            Để sau
          </Button>
          <Button type="button" disabled={!file || posting} onClick={() => void submit()}>
            {posting && <Loader2 className="size-4 animate-spin" />}
            Đăng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
