import { useQueryClient } from '@tanstack/react-query'
import { ArrowUp, MessagesSquare, RefreshCw } from 'lucide-react'

import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'

import { FeedSkeleton } from '../components/feed-skeleton'
import { PostCard } from '../components/post-card'
import { PostComposer } from '../components/post-composer'
import { useForumFeed } from '../hooks/use-forum-feed'
import { useInfiniteSentinel } from '../hooks/use-infinite-sentinel'
import { useNewPostSignal } from '../hooks/use-new-post-signal'

/**
 * Bảng tin: ô đăng bài trên cùng (F3), cuộn vô hạn bằng lính canh
 * IntersectionObserver ở đáy danh sách, kèm nút nổi «Có bài viết mới» khi máy
 * chủ đã có bài mới hơn màn hình.
 */
export function ForumFeedPage() {
  const queryClient = useQueryClient()
  const feed = useForumFeed()
  const { hasNextPage, isFetchingNextPage } = feed

  const posts = feed.data?.pages.flatMap((page) => page.items) ?? []
  const hasNewPosts = useNewPostSignal(posts[0]?.id)
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

        {posts.length === 0 ? (
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
      {!hasNextPage && posts.length > 0 && (
        <p className="py-6 text-center text-xs text-muted-foreground">
          Bạn đã xem hết bảng tin.
        </p>
      )}
    </div>
  )
}
