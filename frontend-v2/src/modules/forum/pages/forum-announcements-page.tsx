import { Megaphone, RefreshCw } from 'lucide-react'

import { Button } from '@/shared/ui/button'

import { FeedSkeleton } from '../components/feed-skeleton'
import { PostCard } from '../components/post-card'
import { usePinnedPosts } from '../hooks/use-pinned-posts'

/**
 * Tab «Thông báo» (F9a/CR-199): mọi bài đang được quản trị viên ghim, mốc ghim
 * mới → cũ — chỗ nhìn MỘT PHÁT ra hết thông báo còn hiệu lực (nghỉ lễ, quy
 * định mới...), khỏi lướt ngược feed. Không phân trang: ghim chỉ vài bài.
 */
export function ForumAnnouncementsPage() {
  const pinned = usePinnedPosts()

  if (pinned.isPending) {
    return (
      <div className="space-y-3 pt-3">
        {[0, 1].map((i) => (
          <FeedSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (pinned.isError) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          Không tải được danh sách thông báo. Kiểm tra kết nối rồi thử lại.
        </p>
        <Button variant="outline" onClick={() => void pinned.refetch()}>
          <RefreshCw className="size-4" />
          Thử lại
        </Button>
      </div>
    )
  }

  const posts = pinned.data ?? []

  if (posts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
        <Megaphone className="size-10 opacity-40" aria-hidden />
        <p className="text-sm">Chưa có thông báo nào được ghim.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 pt-3">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  )
}
