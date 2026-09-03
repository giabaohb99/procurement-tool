import { ArrowLeft, Lock } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

import { PostCard } from '../components/post-card'
import { PostComments } from '../components/post-comments'
import { useForumPost } from '../hooks/use-forum-post'

/**
 * Trang một bài viết — đích của link chia sẻ và thông báo. Ngoài đối tượng xem
 * (403) hay bài đã xóa (404) đều quy về một câu chung, không lộ bài có tồn tại
 * hay không.
 */
export function ForumPostPage() {
  const { id } = useParams()
  const postId = Number(id)
  const post = useForumPost(postId)
  // Thread trong box (F13b): breadcrumb dẫn VỀ BOX thay vì Bảng tin — tiêu đề
  // + chip prefix của thread do chính PostCard vẽ nên trang này chỉ lo đường về.
  const boardId = post.data?.board_id ?? 0

  return (
    <div className="pt-3">
      <div className="mb-2 px-4 sm:px-0">
        <Link
          to={boardId > 0 ? appRoutes.forum.boardDetail(boardId) : appRoutes.forum.feed}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          {boardId > 0 ? post.data?.board_name || 'Diễn đàn' : 'Bảng tin'}
        </Link>
      </div>

      {post.isPending && (
        <div className="border-y border-border bg-card p-4 shadow-sm sm:rounded-xl sm:border">
          <div className="flex items-center gap-3">
            <Skeleton className="size-10 rounded-full" />
            <div className="space-y-1.5">
              <Skeleton className="h-3.5 w-40" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <div className="mt-3 space-y-2">
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-2/3" />
          </div>
        </div>
      )}

      {post.isError && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <Lock className="size-10 text-muted-foreground opacity-40" aria-hidden />
          <p className="text-sm text-muted-foreground">
            Bài viết không tồn tại hoặc bạn không thuộc đối tượng xem của bài.
          </p>
          <Button asChild variant="outline">
            <Link to={appRoutes.forum.feed}>Về bảng tin</Link>
          </Button>
        </div>
      )}

      {post.data && (
        <>
          <PostCard post={post.data} detail />
          <PostComments postId={post.data.id} />
        </>
      )}
    </div>
  )
}
