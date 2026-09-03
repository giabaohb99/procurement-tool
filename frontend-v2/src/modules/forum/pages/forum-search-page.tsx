import { useState } from 'react'
import type { FormEvent } from 'react'
import { ChevronLeft, ChevronRight, RefreshCw, Search, SearchX } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'

import { FeedSkeleton } from '../components/feed-skeleton'
import { PostCard } from '../components/post-card'
import { useForumSearch } from '../hooks/use-forum-search'
import { useForumSearchFilters } from '../hooks/use-forum-search-filters'
import { FORUM_POST_STATUS } from '../types/forum-post'
import type { ForumSearchParams } from '../types/forum-post'

/**
 * Tìm bài viết (CR-263) — MỘT trang cho mọi người: từ khóa + người tạo +
 * công ty/phòng ban (ngữ cảnh đóng băng trên bài). Kết quả backend tự lọc
 * theo audience nên nhân viên thường không dò được bài ngoài phạm vi; riêng
 * quản trị viên có thêm ô trạng thái để soi cả bài đang ẩn.
 */
export function ForumSearchPage() {
  const { can } = usePermission()
  const isForumAdmin = can('forum_post', 'write')
  const filters = useForumSearchFilters()

  //  Bộ lọc NHÁP (đang gõ) tách khỏi bộ lọc ĐÃ GỬI — gõ từng phím không được
  //  phép bắn API, chỉ bấm Tìm mới chạy.
  const [draft, setDraft] = useState({
    q: '',
    authorQ: '',
    companyId: 0,
    deptId: 0,
    status: 0,
  })
  const [applied, setApplied] = useState<ForumSearchParams | null>(null)
  const [page, setPage] = useState(1)

  //  Ô tìm trên header (bao-CR-272) đưa người ta tới đây kèm `?q=` — nhận từ
  //  khóa đó rồi CHẠY LUÔN, không bắt gõ lại lần hai. Chỉnh state NGAY TRONG
  //  render (khuôn "adjusting state when a prop changes" của docs React) thay
  //  vì useEffect: đỡ một lượt vẽ thừa và không dính luật `set-state-in-effect`.
  const [searchParams] = useSearchParams()
  const urlQ = (searchParams.get('q') ?? '').trim()
  const [seenUrlQ, setSeenUrlQ] = useState('')
  if (urlQ && urlQ !== seenUrlQ) {
    setSeenUrlQ(urlQ)
    setDraft((d) => ({ ...d, q: urlQ }))
    setPage(1)
    setApplied((prev) => ({
      q: urlQ,
      author_q: prev?.author_q ?? '',
      company_id: prev?.company_id ?? 0,
      dept_id: prev?.dept_id ?? 0,
      status: prev?.status ?? 0,
    }))
  }

  const search = useForumSearch({ ...(applied ?? {}), page }, applied !== null)

  function submitSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setApplied({
      q: draft.q.trim(),
      author_q: draft.authorQ.trim(),
      company_id: draft.companyId,
      dept_id: draft.deptId,
      status: isForumAdmin ? draft.status : 0,
    })
  }

  const result = search.data
  const totalPages = result ? Math.max(1, Math.ceil(result.total / result.per_page)) : 1

  return (
    <div className="space-y-4 pt-4">
      <form
        onSubmit={submitSearch}
        className="space-y-3 rounded-lg border border-border bg-background p-4"
      >
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            value={draft.q}
            onChange={(e) => setDraft((d) => ({ ...d, q: e.target.value }))}
            placeholder="Từ khóa trong nội dung / tiêu đề..."
            maxLength={255}
            className="flex-1"
          />
          <Input
            value={draft.authorQ}
            onChange={(e) => setDraft((d) => ({ ...d, authorQ: e.target.value }))}
            placeholder="Người tạo (tên, mã NV, email)"
            maxLength={255}
            className="sm:w-64"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={String(draft.companyId)}
            onValueChange={(v) => setDraft((d) => ({ ...d, companyId: Number(v) }))}
          >
            <SelectTrigger className="w-full sm:w-52">
              <SelectValue placeholder="Công ty" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Mọi công ty</SelectItem>
              {(filters.data?.companies ?? []).map((c) => (
                <SelectItem key={c.id} value={String(c.id)}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={String(draft.deptId)}
            onValueChange={(v) => setDraft((d) => ({ ...d, deptId: Number(v) }))}
          >
            <SelectTrigger className="w-full sm:w-52">
              <SelectValue placeholder="Phòng ban" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Mọi phòng ban</SelectItem>
              {(filters.data?.departments ?? []).map((d) => (
                <SelectItem key={d.id} value={String(d.id)}>
                  {d.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {isForumAdmin ? (
            <Select
              value={String(draft.status)}
              onValueChange={(v) => setDraft((d) => ({ ...d, status: Number(v) }))}
            >
              <SelectTrigger className="w-full sm:w-40">
                <SelectValue placeholder="Trạng thái" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">Hiện + ẩn</SelectItem>
                <SelectItem value={String(FORUM_POST_STATUS.published)}>Đang hiện</SelectItem>
                <SelectItem value={String(FORUM_POST_STATUS.hidden)}>Đang ẩn</SelectItem>
              </SelectContent>
            </Select>
          ) : null}
          <Button type="submit" className="ml-auto" disabled={search.isFetching}>
            <Search className="size-4" />
            Tìm
          </Button>
        </div>
      </form>

      {applied === null ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
          <Search className="size-10 opacity-40" aria-hidden />
          <p className="text-sm">Nhập từ khóa hoặc chọn bộ lọc rồi bấm Tìm.</p>
        </div>
      ) : search.isPending ? (
        <div className="space-y-3">
          {[0, 1].map((i) => (
            <FeedSkeleton key={i} />
          ))}
        </div>
      ) : search.isError ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <p className="text-sm text-muted-foreground">
            Không tìm được. Kiểm tra kết nối rồi thử lại.
          </p>
          <Button variant="outline" onClick={() => void search.refetch()}>
            <RefreshCw className="size-4" />
            Thử lại
          </Button>
        </div>
      ) : result && result.items.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
          <SearchX className="size-10 opacity-40" aria-hidden />
          <p className="text-sm">Không có bài viết nào khớp bộ lọc.</p>
        </div>
      ) : result ? (
        <>
          <p className="px-1 text-sm text-muted-foreground">
            Tìm thấy {result.total} bài viết
          </p>
          <div className="space-y-3">
            {result.items.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
          {totalPages > 1 ? (
            <div className="flex items-center justify-center gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1 || search.isFetching}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="size-4" />
                Trước
              </Button>
              <span className="text-sm text-muted-foreground">
                Trang {result.page}/{totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={!result.has_more || search.isFetching}
                onClick={() => setPage((p) => p + 1)}
              >
                Sau
                <ChevronRight className="size-4" />
              </Button>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
