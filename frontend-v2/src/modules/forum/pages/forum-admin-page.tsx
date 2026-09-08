import { useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  Pencil,
  PinOff,
  Plus,
  Trash2,
} from 'lucide-react'
import { Link, Navigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api/response-envelope'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import { BoardFormDialog } from '../components/board-form-dialog'
import { BoardIcon } from '../components/board-icon'
import { useDeleteForumBoard } from '../hooks/use-delete-forum-board'
import { useForumBoards } from '../hooks/use-forum-boards'
import { useModerationLogs } from '../hooks/use-moderation-logs'
import { usePinForumPost } from '../hooks/use-pin-forum-post'
import { usePinnedPosts } from '../hooks/use-pinned-posts'
import { FORUM_MODERATION_ACTION } from '../types/forum-admin'
import { FORUM_BOARD_STATUS } from '../types/forum-board'
import type { ForumBoardNode } from '../types/forum-board'
import { FORUM_BODY_FORMAT, FORUM_POST_STATUS } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { stripRichBodyText } from '../utils/rich-body'

/**
 * Tab «Quản trị» diễn đàn (CR-263): Chuyên mục (dựng cây nhóm-box) · Bài ghim
 * (bỏ ghim tại chỗ) · Nhật ký kiểm duyệt (bảng ghi từ F5, giờ mới có chỗ đọc).
 * `can()` chỉ để ẩn/hiện — chốt chặn thật là `require()` trên từng API.
 */
export function ForumAdminPage() {
  const { can } = usePermission()
  const canBoard = can('forum_board', 'write')
  const canModerate = can('forum_post', 'read')

  if (!canBoard && !canModerate) {
    return <Navigate to={appRoutes.forum.boards} replace />
  }

  return (
    <div className="space-y-4 pt-4">
      <Tabs defaultValue={canBoard ? 'boards' : 'pinned'}>
        <TabsList>
          {canBoard ? <TabsTrigger value="boards">Chuyên mục</TabsTrigger> : null}
          {canModerate ? (
            <>
              <TabsTrigger value="pinned">Bài ghim</TabsTrigger>
              <TabsTrigger value="logs">Nhật ký kiểm duyệt</TabsTrigger>
            </>
          ) : null}
        </TabsList>

        {canBoard ? (
          <TabsContent value="boards">
            <BoardsTab />
          </TabsContent>
        ) : null}
        {canModerate ? (
          <>
            <TabsContent value="pinned">
              <PinnedTab />
            </TabsContent>
            <TabsContent value="logs">
              <ModerationLogsTab />
            </TabsContent>
          </>
        ) : null}
      </Tabs>
    </div>
  )
}

// ── Tab Chuyên mục ────────────────────────────────────────────────────────────

function BoardsTab() {
  const boards = useForumBoards()
  const deleteBoard = useDeleteForumBoard()
  //  bao-CR-272: ô lọc tại chỗ — danh mục vài chục nhóm/box, lọc client là đủ,
  //  khỏi tốn một API. Nhóm khớp từ khóa thì giữ nguyên cả cây con của nó.
  const [filter, setFilter] = useState('')
  const [dialog, setDialog] = useState<{
    open: boolean
    board: ForumBoardNode | null
    defaultParentId: number
  }>({ open: false, board: null, defaultParentId: 0 })

  const groups = (boards.data ?? []).map((g) => ({ id: g.id, name: g.name }))
  const kw = filter.trim().toLowerCase()
  const matchBox = (box: ForumBoardNode) =>
    box.name.toLowerCase().includes(kw) ||
    (box.description ?? '').toLowerCase().includes(kw)
  const visibleGroups = (boards.data ?? [])
    .map((group) =>
      !kw || group.name.toLowerCase().includes(kw)
        ? group
        : { ...group, children: group.children.filter(matchBox) },
    )
    .filter(
      (group) =>
        !kw || group.name.toLowerCase().includes(kw) || group.children.length > 0,
    )

  async function confirmDelete(node: ForumBoardNode) {
    try {
      await deleteBoard.mutateAsync(node.id)
      toast.success('Đã xóa nhóm/box')
    } catch (error) {
      // Hay gặp nhất: box còn thread / nhóm còn box — backend chặn 400 kèm lý do.
      toast.error(extractErrorMessage(error))
    }
  }

  if (boards.isPending) {
    return (
      <div className="space-y-3 pt-3">
        {[0, 1].map((i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-3 pt-3">
      <div className="flex items-center gap-2">
        <Input
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="Lọc theo tên nhóm / box..."
          className="w-full sm:max-w-xs"
        />
        <Button
          className="ml-auto shrink-0"
          onClick={() => setDialog({ open: true, board: null, defaultParentId: 0 })}
        >
          <Plus className="size-4" />
          Thêm nhóm
        </Button>
      </div>

      {(boards.data ?? []).length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          Chưa có nhóm nào — bấm «Thêm nhóm» để dựng chuyên mục đầu tiên.
        </p>
      ) : visibleGroups.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          Không có nhóm / box nào khớp từ khóa.
        </p>
      ) : null}

      {visibleGroups.map((group) => (
        <div key={group.id} className="rounded-lg border border-border bg-background">
          <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
            <span className="font-semibold">{group.name}</span>
            {group.status === FORUM_BOARD_STATUS.hidden ? (
              <Badge variant="secondary">Đang ẩn</Badge>
            ) : null}
            <div className="ml-auto flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  setDialog({ open: true, board: null, defaultParentId: group.id })
                }
              >
                <Plus className="size-4" />
                Thêm box
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                title="Sửa nhóm"
                aria-label="Sửa nhóm"
                onClick={() =>
                  setDialog({ open: true, board: group, defaultParentId: 0 })
                }
              >
                <Pencil />
              </Button>
              <ConfirmIconButton
                icon={Trash2}
                title="Xóa nhóm"
                confirmTitle={`Xóa nhóm "${group.name}"?`}
                confirmDescription="Chỉ xóa được nhóm RỖNG — còn box bên trong thì hệ thống sẽ chặn."
                confirmLabel="Xóa"
                destructive
                disabled={deleteBoard.isPending}
                onConfirm={() => void confirmDelete(group)}
              />
            </div>
          </div>

          {group.children.length === 0 ? (
            <p className="px-4 py-3 text-sm text-muted-foreground">
              Nhóm chưa có box nào.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {group.children.map((box) => (
                <li key={box.id} className="flex items-center gap-3 px-4 py-2.5">
                  <BoardIcon icon={box.icon} className="size-9" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">{box.name}</span>
                      {box.status === FORUM_BOARD_STATUS.hidden ? (
                        <Badge variant="secondary">Đang ẩn</Badge>
                      ) : null}
                    </div>
                    <p className="truncate text-sm text-muted-foreground">
                      {box.description || `${box.thread_count} thread`}
                    </p>
                  </div>
                  <span className="hidden shrink-0 text-sm text-muted-foreground sm:inline">
                    {box.thread_count} thread
                  </span>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    title="Sửa box"
                    aria-label="Sửa box"
                    onClick={() =>
                      setDialog({ open: true, board: box, defaultParentId: group.id })
                    }
                  >
                    <Pencil />
                  </Button>
                  <ConfirmIconButton
                    icon={Trash2}
                    title="Xóa box"
                    confirmTitle={`Xóa box "${box.name}"?`}
                    confirmDescription="Chỉ xóa được box RỖNG — còn thread thì hệ thống sẽ chặn. Muốn cất box đang dùng thì chuyển trạng thái Đang ẩn."
                    confirmLabel="Xóa"
                    destructive
                    disabled={deleteBoard.isPending}
                    onConfirm={() => void confirmDelete(box)}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}

      <BoardFormDialog
        open={dialog.open}
        onOpenChange={(open) => setDialog((d) => ({ ...d, open }))}
        board={dialog.board}
        groups={groups}
        defaultParentId={dialog.defaultParentId}
      />
    </div>
  )
}

// ── Tab Bài ghim ──────────────────────────────────────────────────────────────

/** Nhãn một dòng cho bài — tiêu đề thread, không có thì trích nội dung. */
function labelPost(post: ForumPost): string {
  if (post.title) return post.title
  const text =
    post.body_format === FORUM_BODY_FORMAT.richHtml
      ? stripRichBodyText(post.body)
      : post.body
  return text.trim() || '(bài chỉ có ảnh/video)'
}

function PinnedTab() {
  const pinned = usePinnedPosts()
  const pin = usePinForumPost()
  //  bao-CR-272: lọc tại chỗ theo nhãn bài / người đăng — bài ghim ít, khỏi API.
  const [filter, setFilter] = useState('')

  async function unpin(postId: number) {
    try {
      await pin.mutateAsync({ postId, pinned: false })
      toast.success('Đã bỏ ghim')
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  if (pinned.isPending) {
    return (
      <div className="space-y-2 pt-3">
        {[0, 1].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  const all = pinned.data ?? []

  if (all.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        Không có bài nào đang ghim. Ghim bài từ menu ba chấm trên chính bài viết.
      </p>
    )
  }

  const kw = filter.trim().toLowerCase()
  const posts = all.filter(
    (post) =>
      !kw ||
      labelPost(post).toLowerCase().includes(kw) ||
      (post.author_name ?? '').toLowerCase().includes(kw),
  )

  return (
    <div className="space-y-3 pt-3">
      <Input
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        placeholder="Lọc theo tiêu đề / người đăng..."
        className="w-full sm:max-w-xs"
      />
      {posts.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          Không có bài ghim nào khớp từ khóa.
        </p>
      ) : (
        <ul className="divide-y divide-border rounded-lg border border-border bg-background">
          {posts.map((post) => (
        <li key={post.id} className="flex items-center gap-3 px-4 py-2.5">
          <div className="min-w-0 flex-1">
            <Link
              to={appRoutes.forum.postDetail(post.id)}
              className="line-clamp-1 font-medium hover:underline"
            >
              {labelPost(post)}
            </Link>
            <p className="text-sm text-muted-foreground">
              {post.author_name}
              {post.pinned_at ? ` · ghim lúc ${formatDateTime(post.pinned_at)}` : ''}
            </p>
          </div>
          <ConfirmIconButton
            icon={PinOff}
            title="Bỏ ghim"
            confirmTitle="Bỏ ghim bài này?"
            confirmDescription="Bài rời dải Thông báo nhưng vẫn nằm nguyên trên bảng tin."
            confirmLabel="Bỏ ghim"
            disabled={pin.isPending}
            onConfirm={() => void unpin(post.id)}
          />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Tab Nhật ký kiểm duyệt ────────────────────────────────────────────────────

const ACTION_META: Record<number, { label: string; className: string }> = {
  [FORUM_MODERATION_ACTION.hide]: {
    label: 'Ẩn',
    className: 'bg-amber-500/15 text-amber-700 dark:text-amber-400',
  },
  [FORUM_MODERATION_ACTION.remove]: {
    label: 'Gỡ',
    className: 'bg-destructive/15 text-destructive',
  },
  [FORUM_MODERATION_ACTION.restore]: {
    label: 'Khôi phục',
    className: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400',
  },
}

function ModerationLogsTab() {
  const [page, setPage] = useState(1)
  //  bao-CR-272: bộ lọc đầu tiên của tab này — loại thao tác áp NGAY khi chọn,
  //  từ khóa (lý do / tiêu đề / nội dung bài) chỉ bắn API lúc bấm Lọc.
  const [action, setAction] = useState(0)
  const [qDraft, setQDraft] = useState('')
  const [q, setQ] = useState('')
  const logs = useModerationLogs(page, action, q)

  const data = logs.data
  const filtered = action !== 0 || q !== ''
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.per_page)) : 1

  return (
    <div className="space-y-3 pt-3">
      <form
        onSubmit={(event) => {
          event.preventDefault()
          setPage(1)
          setQ(qDraft.trim())
        }}
        className="flex flex-wrap items-center gap-2"
      >
        <Input
          value={qDraft}
          onChange={(event) => setQDraft(event.target.value)}
          placeholder="Từ khóa trong lý do / bài viết..."
          maxLength={255}
          className="w-full sm:max-w-xs"
        />
        <Select
          value={String(action)}
          onValueChange={(value) => {
            setAction(Number(value))
            setPage(1)
          }}
        >
          <SelectTrigger className="w-40" aria-label="Loại thao tác">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">Mọi thao tác</SelectItem>
            <SelectItem value={String(FORUM_MODERATION_ACTION.hide)}>Ẩn</SelectItem>
            <SelectItem value={String(FORUM_MODERATION_ACTION.remove)}>Gỡ</SelectItem>
            <SelectItem value={String(FORUM_MODERATION_ACTION.restore)}>
              Khôi phục
            </SelectItem>
          </SelectContent>
        </Select>
        <Button type="submit" variant="outline" disabled={logs.isFetching}>
          Lọc
        </Button>
      </form>

      {logs.isPending ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-12 w-full rounded-lg" />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <p className="py-10 text-center text-sm text-muted-foreground">
          {filtered
            ? 'Không có dòng nào khớp bộ lọc.'
            : 'Chưa có thao tác kiểm duyệt nào.'}
        </p>
      ) : (
        <>
      <ul className="divide-y divide-border rounded-lg border border-border bg-background">
        {data.items.map((entry) => {
          const meta = ACTION_META[entry.action]
          //  Bài đã GỠ (removed) không mở được nữa — chỉ link khi còn hiện/ẩn.
          const linkable =
            entry.post_status === FORUM_POST_STATUS.published ||
            entry.post_status === FORUM_POST_STATUS.hidden
          return (
            <li key={entry.id} className="space-y-1 px-4 py-2.5">
              <div className="flex flex-wrap items-center gap-2">
                {meta ? (
                  <Badge className={cn('border-transparent', meta.className)}>
                    {meta.label}
                  </Badge>
                ) : null}
                {linkable ? (
                  <Link
                    to={appRoutes.forum.postDetail(entry.post_id)}
                    className="line-clamp-1 min-w-0 flex-1 font-medium hover:underline"
                  >
                    {entry.post_label || `Bài #${entry.post_id}`}
                  </Link>
                ) : (
                  <span className="line-clamp-1 min-w-0 flex-1 font-medium text-muted-foreground">
                    {entry.post_label || `Bài #${entry.post_id}`}
                  </span>
                )}
                <span className="shrink-0 text-sm text-muted-foreground">
                  {formatDateTime(entry.created_at)}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                {entry.actor_name || `Tài khoản #${entry.actor_id}`}
                {entry.reason ? ` — lý do: ${entry.reason}` : ''}
              </p>
            </li>
          )
        })}
      </ul>

      {totalPages > 1 ? (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1 || logs.isFetching}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            <ChevronLeft className="size-4" />
            Trước
          </Button>
          <span className="text-sm text-muted-foreground">
            Trang {data.page}/{totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!data.has_more || logs.isFetching}
            onClick={() => setPage((p) => p + 1)}
          >
            Sau
            <ChevronRight className="size-4" />
          </Button>
        </div>
      ) : null}
        </>
      )}
    </div>
  )
}
