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
import { RichTextField } from '@/shared/ui/rich-text-editor/rich-text-field'
import type { RichTextFieldHandle } from '@/shared/ui/rich-text-editor/rich-text-field'

import { FORUM_PREFIX, labelOf } from '@/shared/constants/statuses'
import { Input } from '@/shared/ui/input'

import { uploadForumMedia } from '../api/forum-api'
import { useCreateForumPost } from '../hooks/use-create-forum-post'
import { FORUM_AUDIENCE_META, FORUM_BODY_FORMAT } from '../types/forum-post'
import type { ForumAudience, ForumUploadedFile } from '../types/forum-post'
import { readLastAudience, saveLastAudience } from '../utils/last-audience'
import { isVideoMedia, pickMediaFiles } from '../utils/pick-media-files'
import { isBlankRichBody } from '../utils/rich-body'
import { EmojiPickerButton } from './emoji-picker-button'
import { ThreadPrefixChip } from './thread-prefix-chip'

/**
 * Trần của một bài RICH (CR-261) — đo trên MARKUP, khớp `MAX_BODY_HTML` của
 * `forum/service.py`; thẻ mở/đóng ăn cỡ 3-4 lần chữ nhìn thấy nên 40k markup
 * xấp xỉ trần 10k chữ trơn cũ.
 */
const BODY_HTML_MAX = 40_000
/** Trần tiêu đề thread — khớp `MAX_TITLE` phía backend (F13a). */
const TITLE_MAX = 255

interface PostComposerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /**
   * Ngữ cảnh box (F13b): có `board` là hộp chuyển sang chế độ TẠO CHỦ ĐỀ —
   * thêm ô tiêu đề + chọn prefix, ẨN ô đối tượng xem (audience backend ép
   * theo box, QĐ-D7a). Không truyền = hộp đăng bài Bảng tin như cũ.
   */
  board?: { id: number; name: string }
}

/**
 * Hộp thoại đăng bài (F3): nội dung RICH TEXT (CR-261 — in đậm/nghiêng, đầu
 * mục, đánh số... như Facebook, cho CẢ Bảng tin lẫn chủ đề trong box) + ảnh/
 * video (chọn tệp / kéo thả / dán từ clipboard, khuôn tải-trước-gắn-sau) +
 * chọn đối tượng xem có nhớ lựa chọn lần trước. Đóng hộp KHÔNG xóa nháp —
 * lỡ tay bấm ra ngoài còn quay lại viết tiếp.
 */
export function PostComposerDialog({ open, onOpenChange, board }: PostComposerDialogProps) {
  const create = useCreateForumPost()
  //  `body` giữ HTML của RichTextField. Nháp sống ở đây: DialogContent unmount
  //  khi đóng, mở lại thì editor dựng mới với `defaultValue={body}`.
  const [body, setBody] = useState('')
  const [title, setTitle] = useState('')
  const [prefix, setPrefix] = useState(0)
  const [audience, setAudience] = useState<ForumAudience>(() => readLastAudience())
  const [images, setImages] = useState<ForumUploadedFile[]>([])
  const [uploading, setUploading] = useState(false)
  const pickRef = useRef<HTMLInputElement>(null)
  const richRef = useRef<RichTextFieldHandle>(null)

  /** Chèn emoji vào ĐÚNG chỗ con trỏ (F13c) — editor tự lo qua handle CR-261. */
  function insertEmoji(emoji: string) {
    richRef.current?.insertText(emoji)
  }

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
        // bài chỉ có ảnh: gửi chuỗi rỗng thay vì xác `<p></p>` của editor
        body: isBlankRichBody(body) ? '' : body,
        body_format: FORUM_BODY_FORMAT.richHtml,
        audience,
        file_ids: images.map((image) => image.file_id),
        ...(board && { board_id: board.id, title: title.trim(), prefix }),
      })
      if (!board) saveLastAudience(audience)
      setBody('')
      setTitle('')
      setPrefix(0)
      setImages([])
      onOpenChange(false)
      toast.success(board ? 'Đã đăng chủ đề' : 'Đã đăng bài')
    } catch (error) {
      // 400 "chưa gắn phòng ban/pháp nhân" của backend hiện nguyên văn ở đây.
      toast.error(extractErrorMessage(error))
    }
  }

  const empty = isBlankRichBody(body) && images.length === 0
  const missingTitle = Boolean(board) && !title.trim()
  const overLimit = body.length > BODY_HTML_MAX

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        //  bao-CR-272: bài hướng dẫn dài không review nổi trong hộp 512px —
        //  phóng gần hết màn hình (ngang 1024px, cao 92svh), phần giữa tự cuộn
        //  để hàng nút Đăng không bao giờ trôi khỏi tầm mắt.
        className="flex max-h-[92svh] flex-col sm:max-w-3xl lg:max-w-5xl"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault()
          void addFiles(Array.from(event.dataTransfer.files ?? []))
        }}
      >
        <DialogHeader>
          <DialogTitle>{board ? `Tạo chủ đề trong «${board.name}»` : 'Đăng bài viết'}</DialogTitle>
          <DialogDescription className="sr-only">
            Viết nội dung, đính ảnh/video và chọn đối tượng xem cho bài viết.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto">
          {board ? (
            // Ngữ cảnh box: prefix + tiêu đề thay cho ô đối tượng xem — audience
            // do backend ép theo box, hiện ô chọn ở đây chỉ gây hiểu lầm.
            <div className="flex items-center gap-2">
              <Select value={String(prefix)} onValueChange={(value) => setPrefix(Number(value))}>
                <SelectTrigger className="h-9 w-fit gap-1.5 text-xs" aria-label="Prefix chủ đề">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FORUM_PREFIX.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {Number(option.value) > 0 ? (
                        <ThreadPrefixChip prefix={Number(option.value)} />
                      ) : (
                        labelOf(FORUM_PREFIX, option.value)
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                maxLength={TITLE_MAX}
                placeholder="Tiêu đề chủ đề"
                aria-label="Tiêu đề chủ đề"
                autoFocus
              />
            </div>
          ) : (
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
          )}

          {/* Bọc CAPTURE để dán/thả TỆP vẫn đi đường tải-trước-gắn-sau: chặn
              ở tầng capture thì sự kiện không tới được ProseMirror (nó nghe
              native trên vùng gõ), khỏi bị editor nhét ảnh base64 vào body.
              Dán CHỮ có định dạng không dính files nên vẫn tới tay tiptap. */}
          <div
            onPasteCapture={(event) => {
              const files = Array.from(event.clipboardData?.files ?? [])
              if (!files.length) return
              event.preventDefault()
              event.stopPropagation()
              void addFiles(files)
            }}
            onDropCapture={(event) => {
              const files = Array.from(event.dataTransfer?.files ?? [])
              if (!files.length) return
              event.preventDefault()
              event.stopPropagation()
              void addFiles(files)
            }}
          >
            <RichTextField
              defaultValue={body}
              onChange={setBody}
              handleRef={richRef}
              placeholder={board ? 'Nội dung chủ đề' : 'Bạn đang nghĩ gì?'}
              toolbarPosition="bottom"
              autoFocus={!board}
              //  Nới vùng gõ theo hộp to (mặc định `.doc-rich-field` chỉ
              //  9-22rem cho các ô nhỏ lẫn trong form); chữ 15px thay 14px.
              //  PHẢI có `!`: luật gốc ở index.css nằm NGOÀI @layer nên đè
              //  mọi utility trong @layer utilities, kể cả selector sâu hơn.
              className="[&_.doc-rich-field]:min-h-[45svh]! [&_.doc-rich-field]:max-h-[58svh]! [&_.doc-rich-field]:text-[15px]!"
            />
          </div>

          {(body.length > BODY_HTML_MAX - 2_000 || overLimit) && (
            <p className={overLimit ? 'text-xs text-destructive' : 'text-xs text-muted-foreground'}>
              {body.length.toLocaleString('vi-VN')}/{BODY_HTML_MAX.toLocaleString('vi-VN')} ký tự
              (tính cả định dạng)
            </p>
          )}

          {images.length > 0 && (
            <div className="grid grid-cols-4 gap-1.5 sm:grid-cols-6 lg:grid-cols-8">
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
          <div className="flex items-center">
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
            <EmojiPickerButton onPick={insertEmoji} />
          </div>

          <Button
            type="button"
            disabled={empty || missingTitle || overLimit || uploading || create.isPending}
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
