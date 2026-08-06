import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Eye, History, Save, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import { api } from '@/api/client'
import HelpAuditTimeline, { type HelpAuditLog } from '@/components/help-audit-timeline'
import HelpRichEditor from '@/components/help-rich-editor'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { createFaq, deleteFaq, fetchFaq, updateFaq, type Faq } from '@/lib/faq-api'

// /admin/faq/moi và /admin/faq/:faqId — soạn câu hỏi trên TRANG RIÊNG (không dùng hộp thoại),
// kèm khối lịch sử chỉnh sửa của chính câu hỏi đó.

export default function AdminFaqEditor() {
  const { faqId } = useParams()
  const nav = useNavigate()
  const isNew = !faqId

  const [faq, setFaq] = useState<Faq | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [saving, setSaving] = useState(false)
  // Quill chuẩn hóa lại HTML lúc mount nên chỉ tính là đã sửa khi onChange do người dùng
  const [answerTouched, setAnswerTouched] = useState(false)
  const [logs, setLogs] = useState<HelpAuditLog[]>([])

  const dirty = isNew
    ? !!question.trim()
    : !!faq && (question !== faq.question || answerTouched || isActive !== faq.is_active)

  const fetchLogs = useCallback(async () => {
    if (!faqId) return
    try {
      const res = await api.get('/api/audit-logs', { params: { entity: 'faq', entity_id: faqId } })
      setLogs(res.data.data)
    } catch {
      setLogs([])
    }
  }, [faqId])

  useEffect(() => {
    if (isNew) {
      setFaq(null)
      setQuestion('')
      setAnswer('')
      setIsActive(true)
      setAnswerTouched(false)
      return
    }
    let cancelled = false
    fetchFaq(parseInt(faqId!, 10))
      .then((data) => {
        if (cancelled) return
        setFaq(data)
        setQuestion(data.question)
        setAnswer(data.answer || '')
        setIsActive(data.is_active)
        setAnswerTouched(false)
      })
      .catch(() => { if (!cancelled) setNotFound(true) })
    fetchLogs()
    return () => { cancelled = true }
  }, [faqId, isNew, fetchLogs])

  const handleSave = async () => {
    if (!question.trim()) {
      toast.error('Câu hỏi không được để trống')
      return
    }
    setSaving(true)
    if (isNew) {
      const id = await createFaq({ question, answer, is_active: isActive, sort_order: 0 })
      setSaving(false)
      if (id) nav(`/admin/faq/${id}`, { replace: true })
      return
    }
    const ok = await updateFaq(faq!.id, { question, answer, is_active: isActive })
    setSaving(false)
    if (ok) {
      const fresh = await fetchFaq(faq!.id)
      setFaq(fresh)
      setAnswerTouched(false)
      fetchLogs()
    }
  }

  const handleDelete = async () => {
    if (!faq) return
    if (await deleteFaq(faq)) nav('/admin/faq')
  }

  if (notFound) {
    return (
      <div className="mx-auto max-w-3xl px-8 py-12 text-center text-muted-foreground">
        Câu hỏi này không tồn tại hoặc đã bị xóa.
      </div>
    )
  }

  if (!isNew && !faq) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-8 py-7">
        <Skeleton className="h-9 w-2/5" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl px-8 py-7 pb-16">
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => nav('/admin/faq')}>
          <ArrowLeft /> Danh sách
        </Button>

        <h1 className="min-w-0 flex-1 truncate text-lg font-bold text-navy">
          {isNew ? 'Thêm câu hỏi' : 'Sửa câu hỏi'}
        </h1>

        {dirty && <span className="text-xs font-medium text-amber-600">Chưa lưu</span>}

        <div className="flex shrink-0 items-center gap-2">
          <Button size="sm" disabled={!dirty || saving} onClick={handleSave}>
            <Save /> {saving ? 'Đang lưu…' : 'Lưu'}
          </Button>
          {!isNew && (
            <>
              <Button variant="outline" size="sm" onClick={() => nav('/cau-hoi-thuong-gap')}>
                <Eye /> Xem
              </Button>
              <Button
                variant="outline" size="icon" title="Xóa câu hỏi"
                className="size-8 border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive"
                onClick={handleDelete}
              >
                <Trash2 className="size-4" />
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="space-y-5">
        <Panel title="Câu hỏi">
          <Input
            autoFocus={isNew}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="VD: Quên mật khẩu thì làm thế nào?"
          />
          <label className="mt-3 flex items-center gap-2.5 text-sm text-navy">
            <Switch checked={isActive} onCheckedChange={setIsActive} />
            {isActive ? 'Đang hiển thị ở trang người dùng' : 'Đang ẩn khỏi trang người dùng'}
          </label>
        </Panel>

        <Panel title="Câu trả lời">
          <HelpRichEditor
            compact
            value={answer}
            onChange={(html, fromUser) => {
              setAnswer(html)
              if (fromUser) setAnswerTouched(true)
            }}
          />
        </Panel>

        {!isNew && (
          <Panel icon={History} title="Lịch sử chỉnh sửa">
            <HelpAuditTimeline logs={logs} hideHeading />
          </Panel>
        )}
      </div>
    </div>
  )
}

function Panel({
  icon: Icon, title, children,
}: {
  icon?: typeof History
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="overflow-hidden rounded-md border bg-card">
      <header className="flex items-center gap-2 border-b bg-secondary px-4 py-2.5">
        {Icon && <Icon className="size-4 text-primary" strokeWidth={1.75} />}
        <h2 className="text-sm font-semibold text-navy">{title}</h2>
      </header>
      <div className="p-4">{children}</div>
    </section>
  )
}
