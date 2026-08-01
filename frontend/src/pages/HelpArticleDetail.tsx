import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useOutletContext, useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import 'react-quill/dist/quill.snow.css'

import { api } from '../api/client'
import { askConfirm } from '../components/confirm'
import HelpAuditTimeline, { type HelpAuditLog } from '../components/HelpAuditTimeline'
import { HelpSlideGallery, HelpSlideManager, uploadHelpImage, type HelpSlide } from '../components/HelpArticleSlides'
import { toast } from '../components/toast'
import type { HelpOutletContext } from '../layouts/HelpLayout'

interface HelpArticle {
  id: number
  title: string
  content: string
  parent_id: number | null
  sort_order: number
  slides: HelpSlide[]
}

interface TocItem {
  id: string
  text: string
  level: number
}

export default function HelpArticleDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { loadTree, canEdit } = useOutletContext<HelpOutletContext>()

  const [article, setArticle] = useState<HelpArticle | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [toc, setToc] = useState<TocItem[]>([])
  const [auditLogs, setAuditLogs] = useState<HelpAuditLog[]>([])

  const quillRef = useRef<ReactQuill>(null)
  const contentRef = useRef<HTMLDivElement>(null)

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
    setToc([])
    fetchArticle()
    fetchLogs()
  }, [id])

  // Sinh mục lục từ các heading trong nội dung đã render
  useEffect(() => {
    if (isEditing || !article?.content || !contentRef.current) {
      setToc([])
      return
    }
    const headings = Array.from(contentRef.current.querySelectorAll('h1, h2, h3'))
    setToc(headings.map((heading, index) => {
      if (!heading.id) heading.id = `hc-heading-${index}`
      return {
        id: heading.id,
        text: heading.textContent || '',
        level: parseInt(heading.tagName.substring(1), 10),
      }
    }))
  }, [article, isEditing])

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
      nav('/hdsd')
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
      <div style={{ padding: 48, textAlign: 'center', color: 'var(--muted)' }}>
        <i className="ti ti-file-off" style={{ fontSize: 48, display: 'block', marginBottom: 12 }} />
        Bài viết này không tồn tại hoặc đã bị xóa.
      </div>
    )
  }
  if (!article) return <div style={{ padding: 32, color: 'var(--muted)' }}>Đang tải...</div>

  return (
    <div className="hc-article-body">
      <div style={{ flex: 1, minWidth: 0 }}>
        {isEditing ? (
          <>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16 }}>
              <input
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="Tiêu đề bài viết..."
                style={{ flex: 1, fontSize: 16, fontWeight: 600 }}
              />
              <button className="btn" onClick={handleSave}>
                <i className="ti ti-device-floppy" /> Lưu lại
              </button>
              <button className="btn secondary" onClick={() => {
                setIsEditing(false)
                setEditTitle(article.title)
                setEditContent(article.content || '')
              }}>
                <i className="ti ti-x" /> Hủy
              </button>
            </div>

            <div className="hc-editor">
              <ReactQuill ref={quillRef} theme="snow" value={editContent}
                          onChange={setEditContent} modules={modules} />
            </div>

            <HelpSlideManager articleId={id!} slides={article.slides} onChange={fetchArticle} />
          </>
        ) : (
          <>
            <h1 style={{ fontSize: 30, fontWeight: 700, lineHeight: 1.35, marginTop: 0, marginBottom: 20,
                         color: 'var(--navy)' }}>
              {article.title}
            </h1>

            <div ref={contentRef} className="hc-content"
                 dangerouslySetInnerHTML={{ __html: article.content || '' }} />

            {article.content
              ? null
              : <p style={{ color: 'var(--muted)' }}>Bài viết chưa có nội dung.</p>}

            <HelpSlideGallery slides={article.slides} />

            <div style={{ marginTop: 64, padding: 20, borderRadius: 12, background: '#f8fafc',
                          border: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 24 }}>
              {canEdit && (
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <button className="btn secondary" onClick={() => setIsEditing(true)}>
                    <i className="ti ti-edit" /> Sửa bài viết
                  </button>
                  <button className="btn err" onClick={handleDelete}>
                    <i className="ti ti-trash" /> Xóa bài viết
                  </button>
                </div>
              )}
              <HelpAuditTimeline logs={auditLogs} />
            </div>
          </>
        )}
      </div>

      {!isEditing && toc.length > 0 && (
        <aside className="hc-toc">
          <div className="hc-toc-inner">
            <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--navy)', marginTop: 0, marginBottom: 14,
                         textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Trong bài viết này
            </h4>
            <ul>
              {toc.map((item) => (
                <li key={item.id} style={{ marginBottom: 8 }}>
                  <a
                    href={`#${item.id}`}
                    style={{ paddingLeft: (item.level - 1) * 12 + 12 }}
                    onClick={(e) => {
                      e.preventDefault()
                      const el = document.getElementById(item.id)
                      el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                    }}
                  >
                    {item.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      )}
    </div>
  )
}
