import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'
import { Eye, FileX2, Pencil, Save, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import { useAuth } from '@/auth/auth-context'
import { askConfirm } from '@/components/confirm-dialog'
import HelpArticleToc from '@/components/help-article-toc'
import { HelpSlideGallery, HelpSlideManager, uploadHelpImage, type HelpSlide } from '@/components/help-article-slides'
import HelpAuditTimeline, { type HelpAuditLog } from '@/components/help-audit-timeline'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useHeadingToc } from '@/hooks/use-heading-toc'
import type { AdminOutletContext } from '@/layouts/admin-layout'

// Bài viết ở khu QUẢN TRỊ — xem, sửa nội dung, quản lý slide, xem lịch sử chỉnh sửa.

interface HelpArticle {
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
  const { loadTree } = useOutletContext<AdminOutletContext>()
  const canDelete = can('help_article', 'delete')

  const [article, setArticle] = useState<HelpArticle | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [auditLogs, setAuditLogs] = useState<HelpAuditLog[]>([])

  const quillRef = useRef<ReactQuill>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const { items: toc, activeId } = useHeadingToc(
    contentRef, [article, isEditing], !isEditing && !!article?.content,
  )

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
    const ok = await askConfirm({
      title: 'Xóa bài viết',
      message: `Xóa "${article?.title}"? Thao tác này không thể hoàn tác.`,
      confirmText: 'Xóa',
    })
    if (!ok) return
    try {
      await api.delete(`/api/v1/help-center/${id}`)
      toast.success('Đã xóa bài viết')
      await loadTree()
      nav('/admin')
    } catch {
      // interceptor đã toast lỗi (vd thư mục còn bài con)
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
        <FileX2 className="mx-auto mb-3 size-12" />
        Bài viết này không tồn tại hoặc đã bị xóa.
      </div>
    )
  }

  if (!article) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-8 py-8">
        <Skeleton className="h-9 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    )
  }

  return (
    <div className="flex items-start gap-8 px-8 py-6 pb-16">
      <div className="min-w-0 flex-1">
        {isEditing ? (
          <>
            <div className="mb-4 flex items-center gap-2">
              <Input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="Tiêu đề bài viết..."
                className="h-10 flex-1 font-semibold"
              />
              <Button onClick={handleSave}><Save /> Lưu lại</Button>
              <Button variant="outline" onClick={() => {
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

            <HelpSlideManager articleId={id!} slides={article.slides} onChange={fetchArticle} />
          </>
        ) : (
          <>
            <div className="mb-5 flex items-center gap-3">
              <h1 className="flex-1 text-[1.8rem] font-bold leading-tight text-navy">{article.title}</h1>
              <Button variant="outline" size="sm" asChild>
                <Link to={`/${article.id}`} title="Xem như người dùng"><Eye /> Xem</Link>
              </Button>
            </div>

            <div ref={contentRef} className="hc-content"
                 dangerouslySetInnerHTML={{ __html: article.content || '' }} />

            {!article.content && <p className="text-muted-foreground">Bài viết chưa có nội dung.</p>}

            <HelpSlideGallery slides={article.slides} />

            <Card className="mt-16 gap-6 bg-muted/50 py-5">
              <CardContent className="space-y-6 px-5">
                <div className="flex flex-wrap gap-3">
                  <Button variant="outline" onClick={() => setIsEditing(true)}>
                    <Pencil /> Sửa bài viết
                  </Button>
                  {canDelete && (
                    <Button variant="outline" onClick={handleDelete}
                            className="border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive">
                      <Trash2 /> Xóa bài viết
                    </Button>
                  )}
                </div>
                <HelpAuditTimeline logs={auditLogs} />
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {!isEditing && toc.length > 0 && (
        <aside className="sticky top-6 hidden w-64 shrink-0 xl:block">
          <HelpArticleToc items={toc} activeId={activeId} title="Trong bài viết này" />
        </aside>
      )}
    </div>
  )
}
