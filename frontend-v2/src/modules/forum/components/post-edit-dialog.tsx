import { Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api/response-envelope'
import { usePermission } from '@/core/authorization/use-permission'
import { FORUM_PREFIX, labelOf } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RichTextField } from '@/shared/ui/rich-text-editor/rich-text-field'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'

import { useForumBoards } from '../hooks/use-forum-boards'
import { useUpdateForumPost } from '../hooks/use-update-forum-post'
import { FORUM_BOARD_STATUS } from '../types/forum-board'
import { FORUM_BODY_FORMAT } from '../types/forum-post'
import type { ForumPost, ForumPostPatch } from '../types/forum-post'
import { listPrefixOptions } from '../utils/prefix-options'
import { isBlankRichBody } from '../utils/rich-body'
import { ThreadPrefixChip } from './thread-prefix-chip'

/** Khớp `MAX_TITLE` backend (F13a). */
const TITLE_MAX = 255

interface PostEditDialogProps {
  post: ForumPost
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Màn quản trị chỉ sửa tiêu đề / nhãn / box cho gọn — ẩn ô nội dung. */
  hideBody?: boolean
}

/**
 * Sửa bài (bao-CR-707). Tác giả sửa tiêu đề, nhãn, nội dung bài mình; quản trị
 * diễn đàn (`forum_post.write`) sửa mọi bài, chuyển box và gắn nhãn Thông báo.
 * Ảnh/video giữ nguyên — đợt này chưa sửa được tệp đính kèm.
 * Chỉ gửi trường THỰC SỰ đổi, để backend ghi nhật ký đúng thứ quản trị đã sửa.
 */
export function PostEditDialog({ post, open, onOpenChange, hideBody = false }: PostEditDialogProps) {
  const { can } = usePermission()
  const canManage = can('forum_post', 'write')
  const update = useUpdateForumPost()
  const boards = useForumBoards()
  const [title, setTitle] = useState(post.title)
  const [prefix, setPrefix] = useState(post.prefix)
  const [boardId, setBoardId] = useState(post.board_id)
  const [body, setBody] = useState(post.body)
  // why: `disabled={isPending}` chỉ có hiệu lực ở lượt render sau — bấm đúp vẫn ra hai request.
  const submitting = useRef(false)

  const rich = post.body_format === FORUM_BODY_FORMAT.richHtml
  const inBox = boardId > 0
  const boxes = (boards.data ?? []).map((group) => ({
    group,
    children: group.children.filter((box) => box.status === FORUM_BOARD_STATUS.active || box.id === post.board_id),
  }))

  function buildPatch(): ForumPostPatch {
    const patch: ForumPostPatch = {}
    if (canManage && boardId !== post.board_id) patch.board_id = boardId
    if (inBox && title.trim() !== post.title) patch.title = title.trim()
    if (inBox && prefix !== post.prefix) patch.prefix = prefix
    if (!hideBody && body !== post.body) {
      patch.body = body
      patch.body_format = post.body_format
    }
    return patch
  }

  async function save() {
    if (submitting.current) return
    if (inBox && !title.trim()) {
      toast.error('Chủ đề trong box phải có tiêu đề')
      return
    }
    if (!hideBody && post.images.length === 0 && (rich ? isBlankRichBody(body) : !body.trim())) {
      toast.error('Bài viết không được để trống')
      return
    }
    const patch = buildPatch()
    if (Object.keys(patch).length === 0) {
      onOpenChange(false)
      return
    }
    submitting.current = true
    try {
      await update.mutateAsync({ postId: post.id, patch })
      toast.success('Đã lưu bài viết')
      onOpenChange(false)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      submitting.current = false
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] flex-col sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Sửa bài viết</DialogTitle>
          <DialogDescription>
            {canManage
              ? 'Đổi tiêu đề, nhãn, chuyển sang box khác hoặc sửa nội dung. Ảnh và video giữ nguyên.'
              : 'Đổi tiêu đề, nhãn hoặc sửa nội dung bài của bạn. Ảnh và video giữ nguyên.'}
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto">
          {canManage && (
            <div className="space-y-1.5">
              <Label htmlFor="post-edit-board">Box</Label>
              <Select value={String(boardId)} onValueChange={(value) => setBoardId(Number(value))}>
                <SelectTrigger id="post-edit-board" className="w-full">
                  <SelectValue placeholder="Chọn box" />
                </SelectTrigger>
                <SelectContent>
                  {post.board_id === 0 && <SelectItem value="0">Bảng tin (không thuộc box nào)</SelectItem>}
                  {boxes.map(({ group, children }) =>
                    children.length ? (
                      <SelectGroup key={group.id}>
                        <SelectLabel>{group.name}</SelectLabel>
                        {children.map((box) => (
                          <SelectItem key={box.id} value={String(box.id)}>
                            {box.name}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    ) : null,
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

          {inBox && (
            <div className="flex items-end gap-2">
              <div className="space-y-1.5">
                <Label>Nhãn</Label>
                <Select value={String(prefix)} onValueChange={(value) => setPrefix(Number(value))}>
                  <SelectTrigger className="h-9 w-fit gap-1.5 text-xs" aria-label="Nhãn chủ đề">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {listPrefixOptions(canManage, post.prefix).map((option) => (
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
              </div>
              <div className="flex-1 space-y-1.5">
                <Label htmlFor="post-edit-title">Tiêu đề</Label>
                <Input
                  id="post-edit-title"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  maxLength={TITLE_MAX}
                />
              </div>
            </div>
          )}

          {!hideBody && (
            <div className="space-y-1.5">
              <Label>Nội dung</Label>
              {rich ? (
                <RichTextField defaultValue={post.body} onChange={setBody} placeholder="Nội dung bài viết" />
              ) : (
                <Textarea value={body} onChange={(event) => setBody(event.target.value)} rows={8} />
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" onClick={() => void save()} disabled={update.isPending}>
            {update.isPending && <Loader2 className="size-4 animate-spin" />}
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
