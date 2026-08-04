import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Eye, FileX2, History, Images, ListTree, Pencil, Save, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import HelpArticleToc from '@/components/help-article-toc'
import { HelpSlideGallery, HelpSlideManager, uploadHelpImage, type HelpSlide } from '@/components/help-article-slides'
import HelpAuditTimeline, { type HelpAuditLog } from '@/components/help-audit-timeline'
import HelpChildArticles from '@/components/help-child-articles'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useHeadingToc } from '@/hooks/use-heading-toc'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { deleteArticle, levelLabel, renameArticle } from '@/lib/help-article-actions'
import { findNode, findPath } from '@/lib/help-tree'

// /admin/:id — chi tiết 1 bài viết, chia tab: Nội dung · Bài viết con · Ảnh từng bước · Lịch sử.

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
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [auditLogs, setAuditLogs] = useState<HelpAuditLog[]>([])
  const [tab, setTab] = useState('content')

  const quillRef = useRef<ReactQuill>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const { items: toc, activeId } = useHeadingToc(
    contentRef, [article, isEditing, tab], !isEditing && tab === 'content' && !!article?.content,
  )

  const nodeId = id ? parseInt(id, 10) : null
  const node = nodeId ? findNode(tree, nodeId) : null
  const path = nodeId ? findPath(tree, nodeId) : null
  const depth = path ? path.length - 1 : 0
  const childCount = node?.children?.length || 0

  const fetchArticle = async () => {
    try {
      const res = await api.get(`/api/v1/help-center/${id}`)
      setArticle(res.data.data)
      setEditTitle(res.data.data.title)
      setEditContent(res.data.data.content || '')
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
    setIsEditing(false)
    setTab('content')
    fetchArticle()
    fetchLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const handleSave = async () => {
    if (!editTitle.trim()) {
      toast.error('Tiêu đề không được để trống')
      return
    }
    try {
      await api.put(`/api/v1/help-center/${id}`, { title: editTitle, content: editContent })
      toast.success('Đã lưu bài viết')
      setIsEditing(false)
      await Promise.all([fetchArticle(), fetchLogs(), loadTree()])
    } catch {
      // interceptor đã toast lỗi
    }
  }

  const handleDelete = async () => {
    if (!node) return
    if (await deleteArticle(node)) {
      await loadTree()
      nav(node.parent_id ? `/admin/${node.parent_id}` : '/admin')
    }
  }

  const handleRename = async () => {
    if (!node) return
    if (await renameArticle(node)) {
      await Promise.all([fetchArticle(), fetchLogs(), loadTree()])
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
      <div className="mx-auto max-w-5xl space-y-4 px-8 py-7">
        <Skeleton className="h-8 w-3/5" />
        <Skeleton className="h-9 w-72" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-8 py-7 pb-16">
      {/* Tiêu đề + hành động */}
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-1.5 flex items-center gap-2">
            <Badge variant="outline" className="font-normal text-muted-foreground">
              {levelLabel(depth)}
            </Badge>
            {childCount > 0 && (
              <span className="text-xs text-muted-foreground">{childCount} bài viết con</span>
            )}
          </div>
          <h1 className="text-2xl font-bold leading-tight text-navy">{article.title}</h1>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link to={`/${article.id}`} title="Xem như người dùng"><Eye /> Xem</Link>
          </Button>
          <Button variant="outline" size="sm" onClick={handleRename}>
            <Pencil /> Đổi tiêu đề
          </Button>
          {canDelete && (
            <Button
              variant="outline" size="sm"
              className="border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={handleDelete}
            >
              <Trash2 /> Xóa
            </Button>
          )}
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="content"><Pencil /> Nội dung</TabsTrigger>
          <TabsTrigger value="children">
            <ListTree /> Bài viết con {childCount > 0 && `(${childCount})`}
          </TabsTrigger>
          <TabsTrigger value="slides">
            <Images /> Ảnh từng bước {article.slides.length > 0 && `(${article.slides.length})`}
          </TabsTrigger>
          <TabsTrigger value="history"><History /> Lịch sử</TabsTrigger>
        </TabsList>

        {/* ---------- Nội dung ---------- */}
        <TabsContent value="content" className="mt-5">
          {isEditing ? (
            <>
              <div className="mb-4 flex items-center gap-2">
                <Input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder="Tiêu đề bài viết..."
                  className="h-9 flex-1 font-semibold"
                />
                <Button size="sm" onClick={handleSave}><Save /> Lưu lại</Button>
                <Button variant="outline" size="sm" onClick={() => {
                  setIsEditing(false)
                  setEditTitle(article.title)
                  setEditContent(article.content || '')
                }}>
                  <X /> Hủy
                </Button>
              </div>

              <div className="hc-editor">
                <ReactQuill ref={quillRef} theme="snow" value={editContent}
                            onChange={setEditContent} modules={modules} />
              </div>
            </>
          ) : (
            <div className="flex items-start gap-8">
              <div className="min-w-0 flex-1">
                <div className="mb-4">
                  <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                    <Pencil /> Sửa nội dung
                  </Button>
                </div>

                <div ref={contentRef} className="hc-content"
                     dangerouslySetInnerHTML={{ __html: article.content || '' }} />

                {!article.content && (
                  <div className="rounded-md border border-dashed px-6 py-10 text-center">
                    <Pencil className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
                    <strong className="block text-navy">Bài viết chưa có nội dung</strong>
                    <span className="text-sm text-muted-foreground">
                      Bấm "Sửa nội dung" để bắt đầu soạn.
                    </span>
                  </div>
                )}
              </div>

              {toc.length > 0 && (
                <aside className="sticky top-6 hidden w-60 shrink-0 xl:block">
                  <HelpArticleToc items={toc} activeId={activeId} title="Trong bài viết này" />
                </aside>
              )}
            </div>
          )}
        </TabsContent>

        {/* ---------- Bài viết con ---------- */}
        <TabsContent value="children" className="mt-5">
          {node && <HelpChildArticles parent={node} depth={depth} onChanged={loadTree} />}
        </TabsContent>

        {/* ---------- Ảnh từng bước ---------- */}
        <TabsContent value="slides" className="mt-5">
          <HelpSlideManager articleId={id!} slides={article.slides} onChange={fetchArticle} />
          <HelpSlideGallery slides={article.slides} />
        </TabsContent>

        {/* ---------- Lịch sử ---------- */}
        <TabsContent value="history" className="mt-5">
          <div className="rounded-md border bg-card p-5">
            <HelpAuditTimeline logs={auditLogs} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
