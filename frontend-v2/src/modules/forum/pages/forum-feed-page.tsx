import { useQueryClient } from '@tanstack/react-query'
import { ArrowUp, MessagesSquare, Pin, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'

import { FeedSkeleton } from '../components/feed-skeleton'
import { PostCard } from '../components/post-card'
import { PostComposer } from '../components/post-composer'
import { useForumFeed } from '../hooks/use-forum-feed'
import { useInfiniteSentinel } from '../hooks/use-infinite-sentinel'
import { useNewPostSignal } from '../hooks/use-new-post-signal'
import { usePinnedPosts } from '../hooks/use-pinned-posts'

/** Dải ghim chỉ chiếm chỗ này trên Bảng tin — còn lại xem ở tab «Thông báo». */
const MAX_PINNED_ON_FEED = 2

/**
 * Bảng tin: ô đăng bài trên cùng (F3), cuộn vô hạn bằng lính canh
 * IntersectionObserver ở đáy danh sách, kèm nút nổi «Có bài viết mới» khi máy
 * chủ đã có bài mới hơn màn hình.
 */
export function ForumFeedPage() {
  const queryClient = useQueryClient()
  const feed = useForumFeed()
  const { hasNextPage, isFetchingNextPage } = feed

  // Dải ghim (F9a): vài bài mới ghim nhất đứng đầu Bảng tin; bài nào đã lên
  // dải thì rút khỏi dòng thời gian bên dưới cho khỏi hiện hai lần liền nhau.
  const pinnedQuery = usePinnedPosts()
  const pinnedOnFeed = (pinnedQuery.data ?? []).slice(0, MAX_PINNED_ON_FEED)
  const pinnedOverflow = (pinnedQuery.data?.length ?? 0) > MAX_PINNED_ON_FEED

  const allPosts = feed.data?.pages.flatMap((page) => page.items) ?? []
  const posts = allPosts.filter((post) => !pinnedOnFeed.some((p) => p.id === post.id))
  const hasNewPosts = useNewPostSignal(allPosts[0]?.id)
  const sentinelRef = useInfiniteSentinel(feed)

  async function showNewPosts() {
    window.scrollTo({ top: 0 })
    // reset đưa useInfiniteQuery về đúng một trang đầu — các trang cũ bỏ đi để
    // con trỏ chạy lại từ bài mới nhất.
    await queryClient.resetQueries({ queryKey: queryKeys.forum.feed() })
  }

  if (feed.isPending) {
    return (
      <div className="space-y-3 pt-3">
        {[0, 1, 2].map((i) => (
          <FeedSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (feed.isError) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          Không tải được bảng tin. Kiểm tra kết nối rồi thử lại.
        </p>
        <Button variant="outline" onClick={() => void feed.refetch()}>
          <RefreshCw className="size-4" />
          Thử lại
        </Button>
      </div>
    )
  }

  return (
    <div className="relative">
      {hasNewPosts && (
        <div className="sticky top-16 z-10 flex justify-center py-1">
          <Button size="sm" className="rounded-full shadow-md" onClick={() => void showNewPosts()}>
            <ArrowUp className="size-4" />
            Có bài viết mới
          </Button>
        </div>
      )}

      <div className="space-y-3 pt-3">
        <PostComposer />

        {pinnedOnFeed.length > 0 && (
          <section aria-label="Thông báo đã ghim" className="space-y-3">
            <div className="flex items-center justify-between px-4 sm:px-1">
              <span className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase">
                <Pin className="size-3.5" aria-hidden />
                Thông báo
              </span>
              {pinnedOverflow && (
                <Link
                  to={appRoutes.forum.announcements}
                  className="text-xs font-medium text-blue-600 hover:underline"
                >
                  Xem tất cả
                </Link>
              )}
            </div>
            {pinnedOnFeed.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
            <div className="border-b border-border/70" aria-hidden />
          </section>
        )}

        {allPosts.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
            <MessagesSquare className="size-10 opacity-40" aria-hidden />
            <p className="text-sm">Chưa có bài viết nào. Hãy đăng bài đầu tiên.</p>
          </div>
        ) : (
          posts.map((post) => <PostCard key={post.id} post={post} />)
        )}
      </div>

      <div ref={sentinelRef} aria-hidden />
      {isFetchingNextPage && (
        <div className="space-y-3 pt-3">
          <FeedSkeleton />
        </div>
      )}
      {!hasNextPage && allPosts.length > 0 && (
        <p className="py-6 text-center text-xs text-muted-foreground">
          Bạn đã xem hết bảng tin.
        </p>
      )}
    </div>
  )
}
