import { Eye, EyeOff, ExternalLink, Pencil, Pin, PinOff, Search, ShieldX } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api/response-envelope'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { FORUM_PREFIX, labelOf } from '@/shared/constants/statuses'
import { DataTable, RowLink } from '@/shared/data-table'
import type { DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'

import { useForumBoards } from '../hooks/use-forum-boards'
import { useForumSearch } from '../hooks/use-forum-search'
import { useModerateForumPost } from '../hooks/use-moderate-forum-post'
import { usePinForumPost } from '../hooks/use-pin-forum-post'
import { FORUM_POST_STATUS } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { ModeratePostDialog } from './moderate-post-dialog'
import { PostEditDialog } from './post-edit-dialog'
import { ThreadPrefixChip } from './thread-prefix-chip'

/** -1 = mọi giá trị (0 là giá trị thật: "không nhãn", "không thuộc box"). */
const ALL = '-1'

/** Nhãn cột "Bài viết": tiêu đề thread, không có thì trích nội dung đã bóc thẻ. */
function describePost(post: ForumPost): string {
  if (post.title) return post.title
  const text = post.body.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
  return text.slice(0, 120) || '(bài chỉ có ảnh/video)'
}

/**
 * Tab "Bài viết" của màn Quản trị diễn đàn (bao-CR-707): danh sách mọi bài (cả bài
 * đang ẩn) lọc theo box / nhãn / trạng thái / ghim + ô tìm; mỗi dòng sửa (tiêu đề,
 * nhãn, box), ghim, ẩn / khôi phục / gỡ, mở bài. Chạy trên `GET /posts/search`.
 */
export function ForumAdminPostsTab() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can('forum_post', 'write')
  const canDelete = can('forum_post', 'delete')
  const boards = useForumBoards()
  const pin = usePinForumPost()
  const moderate = useModerateForumPost()

  const [keyword, setKeyword] = useState('')
  const [boardId, setBoardId] = useState(ALL)
  const [prefix, setPrefix] = useState(ALL)
  const [status, setStatus] = useState('0')
  const [pinned, setPinned] = useState('0')
  const [pageSize, setPageSize] = useState(20)
  const debouncedKeyword = useDebouncedValue(keyword.trim())
  const [page, setPage] = usePageResetOnFilterChange([debouncedKeyword, boardId, prefix, status, pinned, pageSize])

  const [editing, setEditing] = useState<ForumPost | null>(null)
  const [moderating, setModerating] = useState<{ post: ForumPost; action: 'hide' | 'remove' } | null>(null)

  const search = useForumSearch(
    {
      q: debouncedKeyword,
      board_id: Number(boardId) > 0 ? Number(boardId) : undefined,
      prefix: Number(prefix),
      status: Number(status),
      pinned: Number(pinned),
      page,
      per_page: pageSize,
    },
    true,
  )
  const filtered = debouncedKeyword !== '' || boardId !== ALL || prefix !== ALL || status !== '0' || pinned !== '0'

  const pinAsync = pin.mutateAsync
  const moderateAsync = moderate.mutateAsync
  const pinPending = pin.isPending

  const columns = useMemo<DataTableColumn<ForumPost>[]>(() => {
    async function togglePin(post: ForumPost) {
      try {
        await pinAsync({ postId: post.id, pinned: post.pinned_at == null })
        toast.success(post.pinned_at == null ? 'Đã ghim bài viết' : 'Đã bỏ ghim bài viết')
      } catch (error) {
        toast.error(extractErrorMessage(error))
      }
    }

    async function restore(post: ForumPost) {
      try {
        await moderateAsync({ postId: post.id, action: 'restore' })
        toast.success('Đã khôi phục bài viết')
      } catch (error) {
        toast.error(extractErrorMessage(error))
      }
    }

    return [
      {
        key: 'title',
        header: 'Bài viết',
        width: 360,
        hideable: false,
        wrap: true,
        cell: (post) => (
          <div className="flex min-w-0 items-start gap-1.5">
            <ThreadPrefixChip prefix={post.prefix} className="mt-0.5" />
            <RowLink to={appRoutes.forum.postDetail(post.id)} className="min-w-0 font-medium">
              {describePost(post)}
            </RowLink>
          </div>
        ),
      },
      { key: 'board', header: 'Box', width: 180, cell: (post) => post.board_name || 'Bảng tin' },
      {
        key: 'prefix',
        header: 'Nhãn',
        width: 120,
        defaultHidden: true,
        cell: (post) => (post.prefix > 0 ? labelOf(FORUM_PREFIX, String(post.prefix)) : ''),
      },
      {
        key: 'author',
        header: 'Người đăng',
        width: 180,
        cell: (post) => post.author_name || `Tài khoản #${post.author_id}`,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 120,
        cell: (post) =>
          post.status === FORUM_POST_STATUS.hidden ? (
            <Badge className="border-transparent bg-amber-500/15 text-amber-700 dark:text-amber-400">Đang ẩn</Badge>
          ) : (
            <Badge className="border-transparent bg-emerald-500/15 text-emerald-700 dark:text-emerald-400">
              Đang hiện
            </Badge>
          ),
      },
      {
        key: 'pinned',
        header: 'Ghim',
        width: 80,
        align: 'center',
        cell: (post) => (post.pinned_at ? <Pin className="mx-auto size-4 text-primary" aria-label="Đang ghim" /> : ''),
      },
      { key: 'comments', header: 'Bình luận', width: 100, align: 'right', cell: (post) => post.comment_count },
      { key: 'created_at', header: 'Ngày đăng', width: 150, cell: (post) => formatDateTime(post.created_at) },
      {
        key: 'actions',
        header: 'Thao tác',
        width: 200,
        hideable: false,
        cell: (post) => {
          const hidden = post.status === FORUM_POST_STATUS.hidden
          return (
            <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
              {canWrite && (
                <Button type="button" size="icon" variant="ghost" title="Sửa" onClick={() => setEditing(post)}>
                  <Pencil className="size-4" />
                </Button>
              )}
              {canWrite && (post.pinned_at != null || !hidden) && (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  title={post.pinned_at ? 'Bỏ ghim' : 'Ghim'}
                  disabled={pinPending}
                  onClick={() => void togglePin(post)}
                >
                  {post.pinned_at ? <PinOff className="size-4" /> : <Pin className="size-4" />}
                </Button>
              )}
              {canWrite &&
                (hidden ? (
                  <Button type="button" size="icon" variant="ghost" title="Khôi phục" onClick={() => void restore(post)}>
                    <Eye className="size-4" />
                  </Button>
                ) : (
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    title="Ẩn"
                    onClick={() => setModerating({ post, action: 'hide' })}
                  >
                    <EyeOff className="size-4" />
                  </Button>
                ))}
              {canDelete && (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  title="Gỡ"
                  className="text-destructive"
                  onClick={() => setModerating({ post, action: 'remove' })}
                >
                  <ShieldX className="size-4" />
                </Button>
              )}
              <Button
                type="button"
                size="icon"
                variant="ghost"
                title="Mở bài"
                onClick={() => navigate(appRoutes.forum.postDetail(post.id))}
              >
                <ExternalLink className="size-4" />
              </Button>
            </div>
          )
        },
      },
    ]
  }, [canWrite, canDelete, pinPending, pinAsync, moderateAsync, navigate])

  return (
    <Card className="mt-3 flex min-h-[560px] flex-col p-4">
      <DataTable
        fillHeight
        columns={columns}
        rows={search.data?.items}
        getRowId={(post) => post.id}
        isLoading={search.isPending}
        isError={search.isError}
        emptyMessage={filtered ? 'Không có bài viết nào khớp bộ lọc.' : 'Diễn đàn chưa có bài viết nào.'}
        storageKey="forum.admin-posts"
        getRowHref={(post) => appRoutes.forum.postDetail(post.id)}
        onRowClick={(post) => navigate(appRoutes.forum.postDetail(post.id))}
        pagination={{
          page,
          pageSize,
          total: search.data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: setPageSize,
          unitLabel: 'bài viết',
        }}
        toolbar={
          <>
            <div className="relative w-full max-w-xs">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Tìm tiêu đề, nội dung..."
                value={keyword}
                maxLength={255}
                onChange={(event) => setKeyword(event.target.value)}
              />
            </div>
            <Select value={boardId} onValueChange={setBoardId}>
              <SelectTrigger className="w-48" aria-label="Box">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả box</SelectItem>
                {(boards.data ?? []).map((group) =>
                  group.children.length ? (
                    <SelectGroup key={group.id}>
                      <SelectLabel>{group.name}</SelectLabel>
                      {group.children.map((box) => (
                        <SelectItem key={box.id} value={String(box.id)}>
                          {box.name}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ) : null,
                )}
              </SelectContent>
            </Select>
            <Select value={prefix} onValueChange={setPrefix}>
              <SelectTrigger className="w-44" aria-label="Nhãn">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>Tất cả nhãn</SelectItem>
                {FORUM_PREFIX.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.value === '0' ? 'Không nhãn' : option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-40" aria-label="Trạng thái">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">Tất cả trạng thái</SelectItem>
                <SelectItem value={String(FORUM_POST_STATUS.published)}>Đang hiện</SelectItem>
                <SelectItem value={String(FORUM_POST_STATUS.hidden)}>Đang ẩn</SelectItem>
              </SelectContent>
            </Select>
            <Select value={pinned} onValueChange={setPinned}>
              <SelectTrigger className="w-36" aria-label="Ghim">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">Ghim: tất cả</SelectItem>
                <SelectItem value="1">Đang ghim</SelectItem>
                <SelectItem value="2">Không ghim</SelectItem>
              </SelectContent>
            </Select>
          </>
        }
      />

      {editing && (
        <PostEditDialog
          post={editing}
          open
          hideBody
          onOpenChange={(next) => {
            if (!next) setEditing(null)
          }}
        />
      )}
      {moderating && (
        <ModeratePostDialog
          postId={moderating.post.id}
          action={moderating.action}
          open
          onOpenChange={(next) => {
            if (!next) setModerating(null)
          }}
        />
      )}
    </Card>
  )
}
