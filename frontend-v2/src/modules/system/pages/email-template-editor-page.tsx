import { html as beautifyHtml } from 'js-beautify'
import { ArrowLeft, Loader2, RotateCcw, Save, Send, WandSparkles } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'

import { emailTemplateApi } from '../api/email-template-api'
import {
  useEmailTemplate,
  useResetEmailTemplate,
  useSaveEmailTemplate,
} from '../hooks/use-email-templates'
import type { EmailTemplate, EmailTemplatePreview } from '../types/email-template'

const BODY_TEXTAREA_ID = 'dx-email-body-editor'

/**
 * TRANG CON sửa một mẫu email theo bước (`/system/settings/email/:event`).
 * Trước là popup; tách thành trang riêng cho rộng rãi (soạn HTML + xem trước cạnh
 * nhau). Gác chung `setting.write` như trang Cấu hình.
 */
export function EmailTemplateEditorPage() {
  const navigate = useNavigate()
  const { event = '' } = useParams()
  const { data: template, isPending } = useEmailTemplate(event)

  return (
    <PageContainer>
      <PageHeader
        title={template ? `Mẫu email — ${template.label}` : 'Sửa mẫu email'}
        description="Sửa tiêu đề và nội dung HTML của email cho bước này. Người nhận do hệ thống quyết định theo vai trò."
        actions={
          <Button variant="ghost" onClick={() => navigate(appRoutes.system.settings)}>
            <ArrowLeft className="size-4" />
            Về Cấu hình
          </Button>
        }
      />

      {isPending || !template ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-10" />
          <Skeleton className="h-80" />
        </div>
      ) : (
        //  Dựng form CHỈ khi mẫu đã về → `useState` seed một lần từ prop, khỏi
        //  cần useEffect đồng bộ (tránh cảnh báo set-state-in-effect).
        <EditorForm event={event} template={template} />
      )}
    </PageContainer>
  )
}

function EditorForm({ event, template }: { event: string; template: EmailTemplate }) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can('setting', 'write')
  const save = useSaveEmailTemplate()
  const reset = useResetEmailTemplate()

  const [subject, setSubject] = useState(template.subject)
  const [body, setBody] = useState(template.body_html)
  const [preview, setPreview] = useState<EmailTemplatePreview | null>(null)
  const [busy, setBusy] = useState<'' | 'preview' | 'test'>('')

  //  "Prettify HTML" kiểu Sublime (HTML-CSS-JS Prettify dùng chính js-beautify).
  //  Thụt 2 space, KHÔNG tự bẻ dòng theo độ dài (email nhiều style dài, bẻ ra dễ vỡ).
  function prettifyHtml() {
    try {
      setBody(
        beautifyHtml(body, {
          indent_size: 2,
          preserve_newlines: true,
          max_preserve_newlines: 1,
          wrap_line_length: 0,
          indent_inner_html: true,
          end_with_newline: false,
        }),
      )
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  function insertVar(name: string) {
    const token = `{{ ${name} }}`
    const el = document.getElementById(BODY_TEXTAREA_ID) as HTMLTextAreaElement | null
    if (!el) {
      setBody((b) => b + token)
      return
    }
    const start = el.selectionStart ?? body.length
    const end = el.selectionEnd ?? body.length
    setBody(body.slice(0, start) + token + body.slice(end))
    requestAnimationFrame(() => {
      el.focus()
      const caret = start + token.length
      el.setSelectionRange(caret, caret)
    })
  }

  async function refreshPreview() {
    setBusy('preview')
    try {
      setPreview(await emailTemplateApi.preview(event, { subject, body_html: body }))
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setBusy('')
    }
  }

  async function doTestSend() {
    setBusy('test')
    try {
      const r = await emailTemplateApi.testSend(event)
      toast.success(`Đã gửi email thử tới ${r.to_email}`)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setBusy('')
    }
  }

  function doSave() {
    save.mutate(
      { event, enabled: template.enabled, subject, body_html: body },
      {
        onSuccess: () => {
          toast.success('Đã lưu mẫu email')
          navigate(appRoutes.system.settings)
        },
        onError: (error) => toast.error(extractErrorMessage(error)),
      },
    )
  }

  function doReset() {
    reset.mutate(event, {
      onSuccess: () => {
        toast.success('Đã khôi phục mẫu mặc định')
        navigate(appRoutes.system.settings)
      },
      onError: (error) => toast.error(extractErrorMessage(error)),
    })
  }

  return (
    <>
      <div className="grid gap-4 lg:grid-cols-2 lg:items-stretch">
        {/* Cột trái — soạn. Hàng đầu (Tiêu đề email) ngang với hàng đầu cột phải. */}
        <div className="flex h-full flex-col gap-3">
          <div className="grid gap-1.5">
            <Label htmlFor="dx-email-subject" className="flex h-6 items-center">
              Tiêu đề email
            </Label>
            <Input
              id="dx-email-subject"
              value={subject}
              readOnly={!canWrite}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>

          <div className="flex flex-1 flex-col gap-1.5">
            <div className="flex h-6 items-center justify-between">
              <Label htmlFor={BODY_TEXTAREA_ID}>Nội dung (HTML)</Label>
              {canWrite && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-6 px-2 text-xs"
                  onClick={prettifyHtml}
                  title="Định dạng lại HTML cho dễ đọc (Prettify)"
                >
                  <WandSparkles className="size-3.5" />
                  Định dạng HTML
                </Button>
              )}
            </div>
            <Textarea
              id={BODY_TEXTAREA_ID}
              value={body}
              readOnly={!canWrite}
              onChange={(e) => setBody(e.target.value)}
              className="min-h-[360px] flex-1 font-mono text-xs"
            />
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Chèn biến:</span>
            {template.variables.map((v) => (
              <button
                key={v}
                type="button"
                disabled={!canWrite}
                onClick={() => insertVar(v)}
                className={cn(
                  'rounded border px-1.5 py-0.5 font-mono text-[11px] hover:bg-accent',
                  !canWrite && 'cursor-not-allowed opacity-50',
                )}
              >
                {`{{ ${v} }}`}
              </button>
            ))}
          </div>
        </div>

        {/* Cột phải — xem trước. Cùng khuôn cột trái: hàng tiêu đề (h-6) + 1 control,
            rồi khung render chiếm phần còn lại → hai cột bằng chiều cao, canh đầu. */}
        <div className="flex h-full flex-col gap-3">
          <div className="grid gap-1.5">
            <div className="flex h-6 items-center justify-between">
              <Label>Xem trước (dữ liệu mẫu)</Label>
              <Button
                variant="outline"
                size="sm"
                className="h-6 px-2 text-xs"
                onClick={() => void refreshPreview()}
                disabled={busy === 'preview'}
              >
                {busy === 'preview' ? <Loader2 className="size-3.5 animate-spin" /> : null}
                Cập nhật
              </Button>
            </div>
            <div className="flex h-9 items-center truncate rounded-md border bg-muted px-3 text-xs">
              <span className="text-muted-foreground">Tiêu đề:&nbsp;</span>
              <span className="truncate">{preview?.subject ?? '—'}</span>
            </div>
          </div>

          <div className="flex flex-1 flex-col gap-1.5">
            <Label>Kết quả hiển thị</Label>
            <iframe
              title="Xem trước email"
              srcDoc={
                preview?.html ??
                '<p style="font-family:sans-serif;color:#64748b;padding:16px">Bấm “Cập nhật” để xem bản render.</p>'
              }
              className="min-h-[360px] w-full flex-1 rounded-md border bg-white"
            />
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          {canWrite && (
            <Button variant="outline" onClick={() => void doTestSend()} disabled={busy === 'test'}>
              {busy === 'test' ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              Gửi thử về email của tôi
            </Button>
          )}
          {canWrite && template.is_custom && (
            <Button variant="ghost" onClick={doReset} disabled={reset.isPending}>
              <RotateCcw className="size-4" />
              Khôi phục mặc định
            </Button>
          )}
        </div>
        {canWrite && (
          <Button onClick={doSave} disabled={save.isPending}>
            {save.isPending ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            Lưu
          </Button>
        )}
      </div>
    </>
  )
}
