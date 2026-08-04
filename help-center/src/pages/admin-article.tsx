import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Eye, FileX2, FolderInput, History, Images, ListTree, MoreHorizontal, Save, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import { HelpSlideManager, uploadHelpImage, type HelpSlide } from '@/components/help-article-slides'
import HelpAuditTimeline, { type HelpAuditLog } from '@/components/help-audit-timeline'
import HelpChildArticles from '@/components/help-child-articles'
import MoveArticleDialog from '@/components/move-article-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { deleteArticle, levelLabel } from '@/lib/help-article-actions'
import { findNode, findPath } from '@/lib/help-tree'

// /admin/:id — soạn bài viết trên MỘT trang, không dùng tab:
//   cột trái  : tiêu đề (sửa inline) · trình soạn thảo luôn mở · ảnh từng bước
//   cột phải  : bài viết con · lịch sử chỉnh sửa
// Tiêu đề + nội dung lưu chung bằng 1 nút (bật khi có thay đổi, hoặc Ctrl/Cmd+S).

interface HelpArticleData {
  id: number
  title: string
  content: string
  parent_id: number | null
  sort_order: number
  slides: HelpSlide[]
}

export default function AdminArticle() {
  const { id } = useParams()
  const nav = useNavigate()
  const { can } = useAuth()
  const { tree, loadTree } = useOutletContext<AdminOutletContext>()
  const canDelete = can('help_article', 'delete')

  const [article, setArticle] = useState<HelpArticleData | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  // Quill chuẩn hóa lại HTML ngay khi mount (thêm <p><br></p>...) nên KHÔNG so sánh chuỗi
  // để biết đã sửa hay chưa — chỉ đánh dấu khi onChange đến từ thao tác của người dùng.
  const [contentTouched, setContentTouched] = useState(false)
  const [auditLogs, setAuditLogs] = useState<HelpAuditLog[]>([])
  const [moveOpen, setMoveOpen] = useState(false)

  const quillRef = useRef<ReactQuill>(null)

  const nodeId = id ? parseInt(id, 10) : null
  const node = nodeId ? findNode(tree, nodeId) : null
  const depth = nodeId ? (findPath(tree, nodeId)?.length ?? 1) - 1 : 0
  const childCount = node?.children?.length || 0

  const dirty = !!article && (title !== article.title || contentTouched)

  const fetchArticle = async () => {
    try {
      const res = await api.get(`/api/v1/help-center/${id}`)
      setArticle(res.data.data)
      setTitle(res.data.data.title)
      setContent(res.data.data.content || '')
      setContentTouched(false)
      setNotFound(false)
    } catch {
      setArticle(null)
      setNotFound(true)
    }
  }

  const fetchLogs = async () => {
    try {
      const res = await api.get('/api/audit-logs', {
        params: { entity: 'help_article', entity_id: id },
      })
      setAuditLogs(res.data.data)
    } catch {
      setAuditLogs([])
    }
  }

  useEffect(() => {
    if (!id) return
    fetchArticle()
    fetchLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const handleSave = useCallback(async () => {
    if (!title.trim()) {
      toast.error('Tiêu đề không được để trống')
      return
    }
    setSaving(true)
    try {
      await api.put(`/api/v1/help-center/${id}`, { title, content })
      toast.success('Đã lưu bài viết')
      await Promise.all([fetchArticle(), fetchLogs(), loadTree()])
    } catch {
      // interceptor đã toast lỗi
    } finally {
      setSaving(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, title, content, loadTree])

  // Ctrl/Cmd + S để lưu nhanh khi đang soạn
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        e.preventDefault()
        if (dirty && !saving) handleSave()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [dirty, saving, handleSave])

  // Cảnh báo khi đóng tab lúc còn thay đổi chưa lưu
  useEffect(() => {
    if (!dirty) return
    const onLeave = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', onLeave)
    return () => window.removeEventListener('beforeunload', onLeave)
  }, [dirty])

  const handleDelete = async () => {
    if (!node) return
    if (await deleteArticle(node)) {
      await loadTree()
      nav(node.parent_id ? `/admin/${node.parent_id}` : '/admin')
    }
  }

  // Chèn ảnh vào trình soạn thảo — thay handler mặc định của Quill (base64 phình DB)
  const imageHandler = async () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) return
      try {
        const url = await uploadHelpImage(file)
        const quill = quillRef.current?.getEditor()
        if (!quill) return
        const range = quill.getSelection(true)
        quill.insertEmbed(range.index, 'image', url)
        quill.setSelection(range.index + 1, 0)
      } catch {
        // interceptor đã toast lỗi
      }
    }
    input.click()
  }

  const modules = useMemo(() => ({
    toolbar: {
      container: [
        [{ header: [1, 2, 3, 4, 5, 6, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ color: [] }, { background: [] }],
        [{ list: 'ordered' }, { list: 'bullet' }],
        [{ align: [] }],
        ['link', 'image', 'video'],
        ['clean'],
      ],
      handlers: { image: imageHandler },
    },
  }), [])

  if (notFound) {
    return (
      <div className="mx-auto max-w-3xl px-8 py-12 text-center text-muted-foreground">
        <FileX2 className="mx-auto mb-3 size-12" strokeWidth={1.5} />
        Bài viết này không tồn tại hoặc đã bị xóa.
      </div>
    )
  }

  if (!article) {
    return (
      <div className="mx-auto max-w-6xl space-y-4 px-8 py-6">
        <Skeleton className="h-10 w-3/5" />
        <Skeleton className="h-72 w-full" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[86rem] px-6 py-5 pb-16">
      {/* Thanh tiêu đề + hành động — gói trên MỘT hàng, dính khi cuộn để nút Lưu luôn trong tầm tay */}
      <div className="sticky top-0 z-10 -mx-6 mb-5 flex flex-wrap items-center gap-2 border-b bg-background/95 px-6 py-2.5 backdrop-blur">
        <Badge variant="outline" className="shrink-0 font-normal text-muted-foreground">
          {levelLabel(depth)}
        </Badge>

        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Tiêu đề bài viết..."
          className="h-9 min-w-[12rem] flex-1 border-transparent bg-transparent px-2 text-lg font-bold text-navy shadow-none hover:border-input focus-visible:border-input md:text-lg"
        />

        {dirty && (
          <span className="shrink-0 text-xs font-medium text-amber-600">Chưa lưu</span>
        )}

        <div className="flex shrink-0 items-center gap-2">
          <Button size="sm" disabled={!dirty || saving} onClick={handleSave}>
            <Save /> {saving ? 'Đang lưu…' : 'Lưu'}
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link to={`/${article.id}`} title="Xem như người dùng"><Eye /> Xem</Link>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="size-8" title="Thao tác khác">
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuItem onClick={() => setMoveOpen(true)}>
                <FolderInput /> Chuyển sang mục khác
              </DropdownMenuItem>
              {canDelete && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem variant="destructive" onClick={handleDelete}>
                    <Trash2 /> Xóa bài viết
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {node && (
        <MoveArticleDialog
          tree={tree}
          node={node}
          open={moveOpen}
          onOpenChange={setMoveOpen}
          onMoved={async () => { await Promise.all([fetchArticle(), fetchLogs(), loadTree()]) }}
        />
      )}

      <div className="flex flex-col items-start gap-5 xl:flex-row">
        {/* Cột trái: soạn nội dung + ảnh từng bước */}
        <div className="min-w-0 flex-1 space-y-5">
          <Panel title="Nội dung bài viết" hint="Ctrl/⌘ + S để lưu nhanh">
            <div className="hc-editor">
              <ReactQuill
                ref={quillRef}
                theme="snow"
                value={content}
                onChange={(value, _delta, source) => {
                  setContent(value)
                  if (source === 'user') setContentTouched(true)
                }}
                modules={modules}
              />
            </div>
          </Panel>

          <Panel
            icon={Images}
            title="Ảnh hướng dẫn từng bước"
            hint={article.slides.length ? `${article.slides.length} ảnh` : 'Chưa có ảnh'}
          >
            <HelpSlideManager articleId={id!} slides={article.slides} onChange={fetchArticle} />
          </Panel>
        </div>

        {/* Cột phải: bài con + lịch sử */}
        <aside className="w-full shrink-0 space-y-5 xl:sticky xl:top-28 xl:w-[22rem]">
          <Panel icon={ListTree} title="Bài viết con" hint={childCount ? `${childCount} bài` : undefined}>
            {node && <HelpChildArticles parent={node} depth={depth} onChanged={loadTree} compact />}
          </Panel>

          <Panel icon={History} title="Lịch sử chỉnh sửa">
            <div className="max-h-[26rem] overflow-y-auto">
              <HelpAuditTimeline logs={auditLogs} hideHeading />
            </div>
          </Panel>
        </aside>
      </div>
    </div>
  )
}

/** Khối nội dung có tiêu đề — thay cho tab, mọi phần đều thấy ngay trên 1 trang. */
function Panel({
  icon: Icon, title, hint, children,
}: {
  icon?: typeof Images
  title: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <section className="overflow-hidden rounded-md border bg-card">
      <header className="flex items-center gap-2 border-b bg-secondary px-4 py-2.5">
        {Icon && <Icon className="size-4 text-primary" strokeWidth={1.75} />}
        <h2 className="text-sm font-semibold text-navy">{title}</h2>
        {hint && <span className="ml-auto text-xs text-muted-foreground">{hint}</span>}
      </header>
      <div className="p-4">{children}</div>
    </section>
  )
}
