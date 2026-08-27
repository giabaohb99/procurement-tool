import { Eye, EyeOff, MoreHorizontal, ShieldX, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api/response-envelope'
import { appRoutes } from '@/shared/constants/app-routes'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { buttonVariants } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'

import { useDeleteForumPost } from '../hooks/use-delete-forum-post'
import { useModerateForumPost } from '../hooks/use-moderate-forum-post'
import { FORUM_POST_STATUS } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { ModeratePostDialog } from './moderate-post-dialog'

interface PostActionsMenuProps {
  post: ForumPost
  /** Đang đứng ở trang chi tiết — xóa/gỡ xong phải rời khỏi bài vừa biến mất. */
  detail: boolean
}

/**
 * Nút «...» góc bài viết. Tác giả có «Xóa bài» (F3); quản trị viên (F5,
 * `post.can_moderate`) có Ẩn / Khôi phục / Gỡ theo trạng thái bài — hai đường
 * ẩn/gỡ bắt buộc lý do và báo chuông cho tác giả (QĐ-D1).
 */
export function PostActionsMenu({ post, detail }: PostActionsMenuProps) {
  const navigate = useNavigate()
  const remove = useDeleteForumPost()
  const moderate = useModerateForumPost()
  const [confirming, setConfirming] = useState(false)
  const [moderating, setModerating] = useState<'hide' | 'remove' | null>(null)

  const hidden = post.status === FORUM_POST_STATUS.hidden

  async function confirmDelete() {
    try {
      await remove.mutateAsync(post.id)
      toast.success('Đã xóa bài viết')
      if (detail) navigate(appRoutes.forum.root)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  async function restore() {
    try {
      await moderate.mutateAsync({ postId: post.id, action: 'restore' })
      toast.success('Đã khôi phục bài viết')
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="Thao tác với bài viết"
          className="rounded-full p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <MoreHorizontal className="size-5" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {post.can_delete && (
            <DropdownMenuItem variant="destructive" onSelect={() => setConfirming(true)}>
              <Trash2 className="size-4" />
              Xóa bài
            </DropdownMenuItem>
          )}
          {post.can_moderate && (
            <>
              {hidden ? (
                <DropdownMenuItem onSelect={() => void restore()}>
                  <Eye className="size-4" />
                  Khôi phục bài viết
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onSelect={() => setModerating('hide')}>
                  <EyeOff className="size-4" />
                  Ẩn bài viết
                </DropdownMenuItem>
              )}
              <DropdownMenuItem variant="destructive" onSelect={() => setModerating('remove')}>
                <ShieldX className="size-4" />
                Gỡ bài viết
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xóa bài viết này?</AlertDialogTitle>
            <AlertDialogDescription>
              Bài viết cùng toàn bộ ảnh, lượt thích và bình luận sẽ mất — không hoàn tác được.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className={cn(buttonVariants({ variant: 'destructive' }))}
              onClick={() => void confirmDelete()}
            >
              Xóa
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {moderating && (
        <ModeratePostDialog
          postId={post.id}
          action={moderating}
          open
          onOpenChange={(next) => !next && setModerating(null)}
          onRemoved={detail ? () => navigate(appRoutes.forum.root) : undefined}
        />
      )}
    </>
  )
}
