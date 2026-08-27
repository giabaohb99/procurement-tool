import { EyeOff, MessageCircle, ThumbsUp } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import { useTogglePostLike } from '../hooks/use-toggle-post-like'
import { FORUM_AUDIENCE_META, FORUM_POST_KIND, FORUM_POST_STATUS } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { authorInitials } from '../utils/author-initials'
import { PostActionsMenu } from './post-actions-menu'
import { PostBody } from './post-body'
import { PostComments } from './post-comments'
import { PostImageGrid } from './post-image-grid'
import { PostLikesDialog } from './post-likes-dialog'

interface PostCardProps {
  post: ForumPost
  /**
   * Đang đứng ở khung chi tiết (trang riêng hoặc popup): thời gian không cần
   * link về chính nó, và nút bình luận đứng yên thay vì dẫn đi đâu (khối bình
   * luận đã ở ngay dưới).
   */
  detail?: boolean
  /** Nằm trong popup chi tiết: bỏ viền/bóng của thẻ — khung dialog đã có sẵn. */
  flat?: boolean
}

/**
 * Một bài viết trên bảng tin: đầu bài (avatar · tên · thời gian · đối tượng
 * xem), nội dung, lưới ảnh, hàng đếm + hàng nút Thích / Bình luận (F4). Like
 * KHÔNG có chuông (D-Q6); bấm số đếm mở hộp "ai đã thích".
 */
export function PostCard({ post, detail = false, flat = false }: PostCardProps) {
  const audience = FORUM_AUDIENCE_META[post.audience]
  const AudienceIcon = audience.icon
  const time = formatRelativeTime(post.created_at)
  const toggleLike = useTogglePostLike()
  const [likesOpen, setLikesOpen] = useState(false)
  // Chi tiết mở dạng popup ngay trên feed (kiểu Facebook) — đóng lại là vẫn
  // đứng nguyên vị trí cuộn. Trang riêng /forum/posts/:id chỉ còn cho link
  // chia sẻ và thông báo.
  const [detailOpen, setDetailOpen] = useState(false)
  // Trang cá nhân mở tức thì nhờ mang sẵn tên/avatar theo state — khỏi chờ
  // trang đích tự suy ra tác giả từ trang feed đầu tiên của họ.
  const profileState = {
    name: post.author_name,
    code: post.author_code,
    avatar: post.author_avatar,
  }

  return (
    <article
      className={cn(
        'bg-card',
        !flat && 'border-y border-border shadow-sm sm:rounded-xl sm:border',
      )}
    >
      <header className="flex items-center gap-3 px-4 pt-3 pb-2">
        <Link
          to={appRoutes.forum.userProfile(post.author_id)}
          state={profileState}
          aria-label={`Trang cá nhân của ${post.author_name}`}
        >
          <Avatar className="size-10">
            <AvatarImage className="object-cover" src={post.author_avatar} alt={post.author_name} />
            <AvatarFallback className="bg-navy-solid text-sm font-semibold text-white">
              {authorInitials(post.author_name)}
            </AvatarFallback>
          </Avatar>
        </Link>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-semibold">
            <Link
              to={appRoutes.forum.userProfile(post.author_id)}
              state={profileState}
              className="hover:underline"
            >
              {post.author_name}
            </Link>
            {post.author_code && (
              <span className="ml-1.5 font-normal text-muted-foreground">
                {post.author_code}
              </span>
            )}
            {post.kind === FORUM_POST_KIND.avatarUpdate && (
              <span className="ml-1 font-normal">đã cập nhật ảnh đại diện</span>
            )}
          </div>
          <div
            className="flex items-center gap-1 text-xs text-muted-foreground"
            title={formatDateTime(post.created_at)}
          >
            {detail ? (
              <span>{time}</span>
            ) : (
              <button
                type="button"
                className="hover:underline"
                onClick={() => setDetailOpen(true)}
              >
                {time}
              </button>
            )}
            <span aria-hidden>·</span>
            <AudienceIcon className="size-3.5" aria-hidden />
            <span>{audience.label}</span>
          </div>
        </div>
        {(post.can_delete || post.can_moderate) && (
          // Trong popup (flat) xóa/gỡ xong KHÔNG điều hướng — bài biến khỏi
          // cache là thẻ ngoài feed unmount, popup tự đóng theo.
          <PostActionsMenu post={post} detail={detail && !flat} />
        )}
      </header>

      {post.status === FORUM_POST_STATUS.hidden && (
        <div className="mx-4 mb-1 flex items-start gap-2 rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
          <EyeOff className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          <span>
            Bài viết đã bị quản trị viên ẩn — chỉ tác giả và quản trị viên còn thấy.
            {post.hidden_reason && (
              <>
                {' '}
                Lý do: <span className="font-medium">{post.hidden_reason}</span>
              </>
            )}
          </span>
        </div>
      )}

      <PostBody body={post.body} />
      <PostImageGrid images={post.images} />

      <footer className="px-4 pb-1.5">
        {(post.like_count > 0 || post.comment_count > 0) && (
          <div className="flex items-center justify-between pt-2 text-xs text-muted-foreground">
            {post.like_count > 0 ? (
              <button
                type="button"
                className="flex items-center gap-1 hover:underline"
                onClick={() => setLikesOpen(true)}
              >
                <ThumbsUp className="size-3.5 fill-primary text-primary" aria-hidden />
                {post.like_count}
              </button>
            ) : (
              <span aria-hidden />
            )}
            {post.comment_count > 0 &&
              (detail ? (
                <span>{post.comment_count} bình luận</span>
              ) : (
                <button
                  type="button"
                  className="hover:underline"
                  onClick={() => setDetailOpen(true)}
                >
                  {post.comment_count} bình luận
                </button>
              ))}
          </div>
        )}
        <div className="mt-1.5 flex border-t border-border/70 pt-1 text-sm font-medium text-muted-foreground">
          <button
            type="button"
            disabled={toggleLike.isPending}
            onClick={() => toggleLike.mutate(post.id)}
            className={cn(
              'flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 hover:bg-muted',
              post.liked && 'text-primary',
            )}
          >
            <ThumbsUp className={cn('size-4', post.liked && 'fill-current')} aria-hidden />
            Thích
          </button>
          {detail ? (
            <span className="flex flex-1 items-center justify-center gap-1.5 py-1.5">
              <MessageCircle className="size-4" aria-hidden />
              Bình luận
            </span>
          ) : (
            <button
              type="button"
              className="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 hover:bg-muted"
              onClick={() => setDetailOpen(true)}
            >
              <MessageCircle className="size-4" aria-hidden />
              Bình luận
            </button>
          )}
        </div>
      </footer>

      <PostLikesDialog postId={post.id} open={likesOpen} onOpenChange={setLikesOpen} />
      {!detail && detailOpen && (
        <PostDetailDialog post={post} onClose={() => setDetailOpen(false)} />
      )}
    </article>
  )
}

/**
 * Popup chi tiết bài viết (kiểu Facebook): bài + toàn bộ bình luận trong một
 * dialog cuộn được, bấm ra ngoài là đóng. `post` truyền thẳng từ cache của
 * feed nên like/bình luận trong popup cập nhật ngược ra thẻ ngoài ngay.
 */
function PostDetailDialog({ post, onClose }: { post: ForumPost; onClose: () => void }) {
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        aria-describedby={undefined}
        className="flex max-h-[90svh] flex-col gap-0 overflow-hidden p-0 sm:max-w-2xl"
      >
        <DialogHeader className="border-b border-border px-4 py-3 text-center sm:text-center">
          <DialogTitle className="text-base">
            Bài viết của {post.author_name || 'thành viên'}
          </DialogTitle>
        </DialogHeader>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          <PostCard post={post} detail flat />
          <PostComments postId={post.id} flat />
        </div>
      </DialogContent>
    </Dialog>
  )
}
