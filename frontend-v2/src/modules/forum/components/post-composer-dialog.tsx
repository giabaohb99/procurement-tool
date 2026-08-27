import { ImagePlus, Loader2, X } from 'lucide-react'
import { useRef, useState } from 'react'
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
import { FORUM_AUDIENCE_META } from '../types/forum-post'
import type { ForumAudience, ForumUploadedFile } from '../types/forum-post'
import { readLastAudience, saveLastAudience } from '../utils/last-audience'
import { isVideoMedia, pickMediaFiles } from '../utils/pick-media-files'

/** Trần chữ của một bài — khớp kiểm ở `forum/service.py` (hợp đồng API F1). */
const BODY_MAX = 10_000

interface PostComposerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Hộp thoại đăng bài (F3): chữ + ảnh/video (chọn tệp / kéo thả / dán từ
 * clipboard, khuôn tải-trước-gắn-sau) + chọn đối tượng xem có nhớ lựa chọn
 * lần trước. Đóng hộp KHÔNG xóa nháp — lỡ tay bấm ra ngoài còn quay lại viết tiếp.
 */
export function PostComposerDialog({ open, onOpenChange }: PostComposerDialogProps) {
  const create = useCreateForumPost()
  const [body, setBody] = useState('')
  const [audience, setAudience] = useState<ForumAudience>(() => readLastAudience())
  const [images, setImages] = useState<ForumUploadedFile[]>([])
  const [uploading, setUploading] = useState(false)
  const pickRef = useRef<HTMLInputElement>(null)

  async function addFiles(files: File[]) {
    const { accepted, errors } = pickMediaFiles(files, images.length)
    errors.forEach((message) => toast.error(message))
    if (!accepted.length) return
    setUploading(true)
    try {
      const uploaded = await uploadForumMedia(accepted)
      setImages((current) => [...current, ...uploaded])
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setUploading(false)
    }
  }

  async function submit() {
    try {
      await create.mutateAsync({
        body: body.trim(),
        audience,
        file_ids: images.map((image) => image.file_id),
      })
      saveLastAudience(audience)
      setBody('')
      setImages([])
      onOpenChange(false)
      toast.success('Đã đăng bài')
    } catch (error) {
      // 400 "chưa gắn phòng ban/pháp nhân" của backend hiện nguyên văn ở đây.
      toast.error(extractErrorMessage(error))
    }
  }

  const empty = !body.trim() && images.length === 0
  const overLimit = body.length > BODY_MAX

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="sm:max-w-lg"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault()
          void addFiles(Array.from(event.dataTransfer.files ?? []))
        }}
      >
        <DialogHeader>
          <DialogTitle>Đăng bài viết</DialogTitle>
          <DialogDescription className="sr-only">
            Viết nội dung, đính ảnh/video và chọn đối tượng xem cho bài viết.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
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

          <Textarea
            value={body}
            onChange={(event) => setBody(event.target.value)}
            onPaste={(event) => {
              const files = Array.from(event.clipboardData?.files ?? [])
              if (!files.length) return
              event.preventDefault()
              void addFiles(files)
            }}
            placeholder="Bạn đang nghĩ gì?"
            rows={5}
            className="max-h-72 border-0 p-1 text-base shadow-none focus-visible:ring-0 sm:text-base"
            autoFocus
          />

          {(body.length > BODY_MAX - 1_000 || overLimit) && (
            <p className={overLimit ? 'text-xs text-destructive' : 'text-xs text-muted-foreground'}>
              {body.length.toLocaleString('vi-VN')}/{BODY_MAX.toLocaleString('vi-VN')} ký tự
            </p>
          )}

          {images.length > 0 && (
            <div className="grid grid-cols-4 gap-1.5">
              {images.map((image) => (
                <div key={image.file_id} className="group relative aspect-square">
                  {isVideoMedia(image.filename, image.content_type) ? (
                    // Preview câm, không controls — ô vuông bé tí, bấm nút phát
                    // ở đây chẳng để làm gì; xem thật thì đăng xong xem trên thẻ bài.
                    <video
                      src={image.url}
                      muted
                      playsInline
                      className="size-full rounded-md bg-black object-cover"
                    />
                  ) : (
                    <img
                      src={image.thumb_url || image.url}
                      alt={image.filename}
                      className="size-full rounded-md object-cover"
                    />
                  )}
                  <button
                    type="button"
                    aria-label={`Bỏ tệp ${image.filename}`}
                    className="absolute right-1 top-1 rounded-full bg-black/60 p-1 text-white hover:bg-black/80"
                    onClick={() =>
                      setImages((current) => current.filter((f) => f.file_id !== image.file_id))
                    }
                  >
                    <X className="size-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <DialogFooter className="flex-row items-center justify-between sm:justify-between">
          <input
            ref={pickRef}
            type="file"
            multiple
            accept="image/*,video/mp4,video/webm"
            className="hidden"
            onChange={(event) => {
              void addFiles(Array.from(event.target.files ?? []))
              // Chọn lại đúng ảnh vừa bỏ thì `change` không bắn nếu không dọn giá trị.
              event.target.value = ''
            }}
          />
          <Button
            type="button"
            variant="ghost"
            className="text-muted-foreground"
            disabled={uploading}
            onClick={() => pickRef.current?.click()}
          >
            {uploading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <ImagePlus className="size-4 text-green-600" />
            )}
            Thêm ảnh/video
          </Button>

          <Button
            type="button"
            disabled={empty || overLimit || uploading || create.isPending}
            onClick={() => void submit()}
          >
            {create.isPending && <Loader2 className="size-4 animate-spin" />}
            Đăng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
