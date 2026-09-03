import { ArrowLeft, MessagesSquare } from 'lucide-react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'

import { FeedSkeleton } from '../components/feed-skeleton'
import { PostCard } from '../components/post-card'
import { PostComposer } from '../components/post-composer'
import { useInfiniteSentinel } from '../hooks/use-infinite-sentinel'
import { useUserPosts } from '../hooks/use-user-posts'
import { authorInitials } from '../utils/author-initials'

/** Tên/avatar `PostCard` gửi kèm theo `Link` để đầu trang hiện được ngay. */
interface ProfileLinkState {
  name?: string
  code?: string
  avatar?: string
}

/**
 * Trang cá nhân (QĐ-D3) — phục vụ cả `/forum/me` lẫn `/forum/users/:id`.
 * Trang CHÍNH MÌNH: có ô đăng bài, backend trả cả bài bị ẩn. Trang người
 * khác: chỉ những bài mình thuộc đối tượng xem; đầu trang lấy tên/avatar từ
 * state của link dẫn tới đây hoặc từ chính bài viết đầu tiên.
 */
export function ForumProfilePage() {
  const { user } = useAuth()
  const params = useParams()
  const location = useLocation()

  const routeId = params.id === undefined ? undefined : Number(params.id)
  const userId = routeId ?? user?.id
  const isSelf = userId !== undefined && userId === user?.id
  const invalidId = routeId !== undefined && (!Number.isInteger(routeId) || routeId <= 0)

  const feed = useUserPosts(invalidId ? undefined : userId)
  const posts = feed.data?.pages.flatMap((page) => page.items) ?? []
  const sentinelRef = useInfiniteSentinel(feed)

  if (invalidId) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <MessagesSquare className="size-10 text-muted-foreground opacity-40" aria-hidden />
        <p className="text-sm text-muted-foreground">Không tìm thấy người dùng này.</p>
        <Button asChild variant="outline">
          <Link to={appRoutes.forum.feed}>Về bảng tin</Link>
        </Button>
      </div>
    )
  }

  const linkState = (location.state ?? null) as ProfileLinkState | null
  const firstPost = posts[0]
  const name = isSelf
    ? (user?.full_name ?? '')
    : (firstPost?.author_name ?? linkState?.name ?? 'Thành viên diễn đàn')
  const code = isSelf ? user?.emp_code : (firstPost?.author_code ?? linkState?.code)
  const avatar = isSelf ? user?.avatar : (firstPost?.author_avatar ?? linkState?.avatar)
  // Phòng ban/pháp nhân chỉ chắc chắn với CHÍNH MÌNH (auth store); của người
  // khác PostOut không mang nên không đoán.
  const subtitle = isSelf
    ? [user?.position, user?.department_name, user?.company_name].filter(Boolean).join(' · ')
    : ''

  return (
    <div className="space-y-3 pt-3">
      <div className="px-4 sm:px-0">
        <Link
          to={appRoutes.forum.feed}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Bảng tin
        </Link>
      </div>

      <section className="flex items-center gap-4 border-y border-border bg-card p-4 shadow-sm sm:rounded-xl sm:border">
        <Avatar className="size-16">
          <AvatarImage className="object-cover" src={avatar} alt={name} />
          <AvatarFallback className="bg-navy-solid text-lg font-semibold text-white">
            {authorInitials(name)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold">
            {name}
            {code && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">{code}</span>
            )}
          </h1>
          {subtitle && <p className="truncate text-sm text-muted-foreground">{subtitle}</p>}
        </div>
      </section>

      {isSelf && <PostComposer />}

      {feed.isPending &&
        [0, 1].map((i) => <FeedSkeleton key={i} />)}

      {feed.isError && (
        <p className="py-10 text-center text-sm text-muted-foreground">
          Không tải được bài viết. Kiểm tra kết nối rồi thử lại.
        </p>
      )}

      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}

      {!feed.isPending && !feed.isError && posts.length === 0 && (
        <p className="py-10 text-center text-sm text-muted-foreground">
          {isSelf ? 'Bạn chưa đăng bài nào. Hãy đăng bài đầu tiên.' : 'Chưa có bài viết nào.'}
        </p>
      )}

      <div ref={sentinelRef} aria-hidden />
      {feed.isFetchingNextPage && <FeedSkeleton />}
      {!feed.hasNextPage && posts.length > 0 && (
        <p className="py-3 text-center text-xs text-muted-foreground">Đã xem hết bài viết.</p>
      )}
    </div>
  )
}
