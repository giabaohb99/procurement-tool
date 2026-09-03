import { EyeOff, MessageCircle, Pin } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { cn } from '@/shared/utils/cn'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import {
  FORUM_AUDIENCE_META,
  FORUM_POST_KIND,
  FORUM_POST_STATUS,
  FORUM_REACTION_META,
} from '../types/forum-post'
import type { ForumPost, ForumReactionKind } from '../types/forum-post'
import { authorInitials } from '../utils/author-initials'
import { PostActionsMenu } from './post-actions-menu'
import { PostBody } from './post-body'
import { ThreadPrefixChip } from './thread-prefix-chip'
import { PostComments } from './post-comments'
import { PostImageGrid } from './post-image-grid'
import { PostLikesDialog } from './post-likes-dialog'
import { PostReactionButton } from './post-reaction-button'

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
 * Ba cảm xúc ĐÔNG NHẤT của bài, nhiều → ít — cụm icon nhỏ cạnh số đếm (kiểu
 * Facebook). Cache cũ chưa có `reactions` (dữ liệu trước CR-206) thì rơi về
 * icon Thích cho khỏi trống chỗ.
 */
function topReactionKinds(post: ForumPost): ForumReactionKind[] {
  const kinds = Object.entries(post.reactions ?? {})
    .filter(([, n]) => n > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([kind]) => Number(kind) as ForumReactionKind)
  return kinds.length > 0 ? kinds : [1]
}

/**
 * Một bài viết trên bảng tin: đầu bài (avatar · tên · thời gian · đối tượng
 * xem), nội dung, lưới ảnh, hàng đếm + hàng nút cảm xúc / Bình luận (F4).
 * Cảm xúc KHÔNG có chuông (D-Q6); bấm số đếm mở hộp "ai đã bày tỏ cảm xúc".
 */
export function PostCard({ post, detail = false, flat = false }: PostCardProps) {
  const audience = FORUM_AUDIENCE_META[post.audience]
  const AudienceIcon = audience.icon
  const time = formatRelativeTime(post.created_at)
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
            {post.pinned_at != null && (
              <>
                <span aria-hidden>·</span>
                <Pin className="size-3.5 text-blue-600" aria-hidden />
                <span className="text-blue-600">Đã ghim</span>
              </>
            )}
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

      {post.board_id > 0 && post.title && (
        // Thread trong box (F13b): chip tên box + tiêu đề đậm đứng trên nội
        // dung; ngoài feed bấm tiêu đề là mở thread, trong chi tiết đứng yên.
        <div className="px-4 pb-0.5">
          <div className="flex flex-wrap items-center gap-1.5">
            {post.board_name && (
              <Link
                to={appRoutes.forum.boardDetail(post.board_id)}
                className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
              >
                {post.board_name}
              </Link>
            )}
            <ThreadPrefixChip prefix={post.prefix} />
          </div>
          {detail ? (
            // Khung đọc bài: tiêu đề phải ra dáng tiêu đề, 15px lẫn vào nội dung.
            <h2 className="mt-1 text-xl font-semibold">{post.title}</h2>
          ) : (
            <Link
              to={appRoutes.forum.postDetail(post.id)}
              className="mt-1 block text-base font-semibold hover:underline"
            >
              {post.title}
            </Link>
          )}
        </div>
      )}

      <PostBody body={post.body} format={post.body_format} detail={detail} />
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
                <span className="flex items-center gap-0.5">
                  {topReactionKinds(post).map((kind) => {
                    const meta = FORUM_REACTION_META[kind]
                    const Icon = meta.icon
                    return (
                      <Icon
                        key={kind}
                        className={cn('size-3.5', meta.className, meta.fill && 'fill-current')}
                        aria-hidden
                      />
                    )
                  })}
                </span>
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
          <PostReactionButton post={post} />
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
        className="flex max-h-[92svh] flex-col gap-0 overflow-hidden p-0 sm:max-w-3xl"
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
