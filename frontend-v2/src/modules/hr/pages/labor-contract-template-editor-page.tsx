// duoc-CR-606 (07/10/2026) — SOẠN NỘI DUNG mẫu hợp đồng ngay trên web: mở tệp .docx bằng trình
// soạn thảo của phân hệ Văn bản, chèn biến bằng nút (khung «Chèn biến»), lưu thì backend dựng lại
// .docx, kiểm biến y như lúc tải tệp lên rồi thay tệp. Bản Word gốc vẫn tải về được trước khi lưu.
import type { Editor } from '@tiptap/react'
import { ArrowLeft, Download, Loader2, Save, TriangleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { RichTextEditor, mmToPx, pxToMm, type PageMargins } from '@/shared/ui/rich-text-editor'
import { Skeleton } from '@/shared/ui/skeleton'
import { laborContractTemplateApi } from '../api/labor-contract-template-api'
import { LaborContractPlaceholderInsertPanel } from '../components/labor-contract-placeholder-insert-panel'
import {
  useLaborContractTemplate,
  useLaborContractTemplateContent,
  useSaveLaborContractTemplateContent,
} from '../hooks/use-labor-contract-templates'
import { extractUnknownPlaceholders } from '../utils/labor-contract-template-errors'

const FORMAT_WARNING =
  'Lưu trên web sẽ dựng lại tệp Word từ nội dung đang soạn: chữ, bảng, ảnh, căn lề và lề trái / phải được giữ; ' +
  'đầu trang / chân trang và một số định dạng riêng của Word có thể mất. Nên tải bản Word gốc về giữ trước khi lưu lần đầu.'

export function LaborContractTemplateEditorPage() {
  const { id } = useParams()
  const templateId = Number(id)
  const validId = Number.isInteger(templateId) && templateId > 0 ? templateId : 0
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can('labor_contract_template', 'write')

  const template = useLaborContractTemplate(validId)
  const content = useLaborContractTemplateContent(validId)
  const save = useSaveLaborContractTemplateContent()

  const [editor, setEditor] = useState<Editor | null>(null)
  const [dirty, setDirty] = useState(false)
  const [unknown, setUnknown] = useState<string[]>([])
  const htmlRef = useRef('')
  const marginsRef = useRef<{ left: number; right: number } | null>(null)
  //  `disabled={isPending}` không chặn nổi bấm đúp (state chỉ đổi ở lượt render sau).
  const savingRef = useRef(false)
  const warnedRef = useRef(false)

  //  Rời trang (đóng tab, F5) khi còn chữ chưa lưu thì trình duyệt hỏi lại.
  useEffect(() => {
    if (!dirty) return
    const onBeforeUnload = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirty])

  if (!validId) {
    return (
      <PageContainer>
        <PageHeader title="Soạn mẫu hợp đồng" description="Đường dẫn không đúng mẫu nào." />
      </PageContainer>
    )
  }

  const backToList = async () => {
    if (dirty && !(await confirm({ title: 'Bỏ thay đổi?', message: 'Nội dung đã sửa chưa được lưu sẽ mất.', confirmLabel: 'Bỏ thay đổi' }))) {
      return
    }
    navigate(appRoutes.hr.laborContractTemplates)
  }

  const insertToken = (token: string) => {
    //  Chèn dạng CHỮ THUẦN (không parse HTML) để biến nằm trọn một đoạn chữ — bị cắt thành nhiều
    //  mảnh thì lúc sinh hợp đồng biến không được thay.
    editor?.chain().focus().insertContent({ type: 'text', text: token }).run()
  }

  const handleSave = async () => {
    if (savingRef.current || !content.data) return
    if (!warnedRef.current) {
      const ok = await confirm({ title: 'Lưu nội dung mẫu', message: FORMAT_WARNING, confirmLabel: 'Lưu', tone: 'default' })
      if (!ok) return
      warnedRef.current = true
    }
    savingRef.current = true
    setUnknown([])
    const margins = marginsRef.current
    try {
      await save.mutateAsync({
        id: validId,
        payload: {
          html: htmlRef.current || content.data.html,
          margin_left_mm: margins ? Math.round(pxToMm(margins.left)) : content.data.margin_left_mm,
          margin_right_mm: margins ? Math.round(pxToMm(margins.right)) : content.data.margin_right_mm,
        },
      })
      setDirty(false)
    } catch (error) {
      //  Biến lạ hiện NGAY trên trang (toast tắt sau vài giây, người soạn cần danh sách để sửa).
      setUnknown(extractUnknownPlaceholders(error))
      toast.error(extractErrorMessage(error))
    } finally {
      savingRef.current = false
    }
  }

  const meta = template.data
  const description = meta
    ? `${meta.company_name}${meta.company_code ? ` (${meta.company_code})` : ''} · ${labelOf(LABOR_CONTRACT_TYPE, String(meta.contract_type)) || '—'}`
    : undefined

  return (
    <PageContainer fill className="flex flex-col gap-3">
      <PageHeader
        title={meta ? `Soạn mẫu «${meta.name}»` : 'Soạn mẫu hợp đồng'}
        description={description}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => void backToList()}>
              <ArrowLeft className="size-4" />
              Quay lại
            </Button>
            {meta && (
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  void laborContractTemplateApi.download(meta).catch((e: unknown) => toast.error(extractErrorMessage(e)))
                }
              >
                <Download className="size-4" />
                Tải bản Word
              </Button>
            )}
            {canWrite && (
              <Button type="button" disabled={!content.data || save.isPending} onClick={() => void handleSave()}>
                {save.isPending ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                Lưu
              </Button>
            )}
          </div>
        }
      />

      {unknown.length > 0 && (
        <div role="alert" className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          <span>
            Biến không có trong danh sách: {unknown.map((key) => `{{ ${key} }}`).join(', ')}. Xóa hoặc thay bằng biến ở
            khung «Chèn biến» rồi lưu lại.
          </span>
        </div>
      )}

      {content.isError ? (
        <p role="alert" className="text-sm text-destructive">{extractErrorMessage(content.error)}</p>
      ) : !content.data ? (
        <Skeleton className="h-[60vh] w-full" />
      ) : (
        <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <RichTextEditor
            key={validId}
            defaultContent={content.data.html}
            editable={canWrite}
            defaultMargins={{
              left: mmToPx(content.data.margin_left_mm),
              right: mmToPx(content.data.margin_right_mm),
            }}
            onMarginsChange={(margins: PageMargins) => {
              marginsRef.current = margins
              setDirty(true)
            }}
            onChange={(html) => {
              htmlRef.current = html
              setDirty(true)
            }}
            onEditorReady={setEditor}
          />
          {canWrite && (
            <LaborContractPlaceholderInsertPanel
              className="lg:max-h-[calc(100dvh-12rem)]"
              disabled={!editor}
              onInsert={insertToken}
            />
          )}
        </div>
      )}
    </PageContainer>
  )
}
