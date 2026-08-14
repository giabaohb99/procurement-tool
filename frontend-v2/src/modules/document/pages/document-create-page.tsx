import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Activity, Info, Layers, PenLine } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Form } from '@/shared/ui/form'
import { FormCard } from '@/shared/ui/form-card'
import { FormStepper } from '@/shared/ui/form-stepper'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { DocumentAttachmentList } from '../components/document-attachment-list'
import { DocumentExtraInfoFields } from '../components/document-extra-info-fields'
import {
  DocumentMainInfoFields,
  MAIN_INFO_FIELDS,
} from '../components/document-main-info-fields'
import {
  DocumentProcessingFields,
  PROCESSING_FIELDS,
} from '../components/document-processing-fields'
import { emptyDocumentForm } from '../helpers/document-form-defaults'
import { useDocumentActions } from '../hooks/use-documents'
import {
  documentRecordSchema,
  type DocumentRecordFormValues,
} from '../schemas/document-record-schema'
import type { DocumentAttachment, DocumentDirection } from '../types/document-record'

/**
 * Ba bước của form tạo văn bản.
 *
 * `fields` là các ô được kiểm khi bấm "Tiếp tục" — chỉ kiểm bước đang đứng, vì
 * các bước sau còn chưa mở ra để nhập. Bước cuối không cần khai: bấm "Tạo" là
 * zod kiểm toàn bộ.
 */
const STEPS = [
  {
    title: 'Thông tin chính',
    description: 'Tên, số, loại, nơi nhận',
    fields: MAIN_INFO_FIELDS,
  },
  {
    title: 'Tình trạng xử lý',
    description: 'Khâu xử lý, người nhận, hạn',
    fields: PROCESSING_FIELDS,
  },
  {
    title: 'Thông tin bổ sung',
    description: 'Hình thức, vào sổ, mức mật, tệp đính kèm',
    fields: [],
  },
] as const

const LAST_STEP = STEPS.length - 1

/**
 * Trang TẠO VĂN BẢN, chia ba bước.
 *
 * Tách theo việc chứ không theo số lượng ô: bước 1 là những thứ bắt buộc để cấp
 * số và vào sổ, bước 2 là giao việc cho ai, bước 3 gom phần có thể bổ sung sau.
 * Tạo xong nhảy thẳng sang tab "Soạn thảo" của văn bản vừa lập — lập xong cái
 * vỏ thì việc kế tiếp luôn là gõ nội dung.
 */
export function DocumentCreatePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [step, setStep] = useState(0)

  const { save } = useDocumentActions()

  // Tạo mới từ tab đang xem: `?direction=outgoing` để khỏi phải chọn lại.
  const initialDirection = (searchParams.get('direction') ?? 'incoming') as DocumentDirection

  const form = useForm<DocumentRecordFormValues>({
    resolver: zodResolver(documentRecordSchema),
    defaultValues: { ...emptyDocumentForm(), direction: initialDirection },
  })

  const [attachments, setAttachments] = useState<DocumentAttachment[]>([])

  async function goNext() {
    const valid = await form.trigger([...STEPS[step].fields])
    if (!valid) {
      toast.error(`Còn ô bắt buộc chưa nhập ở bước ${STEPS[step].title}`)
      return
    }
    setStep(step + 1)
  }

  function handleSubmit(values: DocumentRecordFormValues) {
    const savedId = save({
      ...values,
      attachments,
      content: '',
      // Số vào sổ do hệ cấp lúc lưu; số văn bản (`code`) lấy theo ô người dùng
      // gõ, bỏ trống thì cũng do hệ ghép — xem `use-documents.ts`.
      book_no: 0,
      book_year: 0,
    })
    toast.success('Đã tạo và vào sổ văn bản')
    navigate(appRoutes.document.documentDetail(savedId), { replace: true })
  }

  return (
    <PageContainer className="space-y-5">
      <PageHeader
        title="Thêm văn bản"
        description="Số hiệu và số vào sổ sẽ được cấp tự động khi lưu."
        leading={
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={() => navigate(appRoutes.document.documents)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
      />

      <FormStepper steps={STEPS} current={step} onGoTo={setStep} className="max-w-5xl" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          {/* Giữ CẢ BA bước trong DOM, chỉ ẩn bước không xem: gỡ hẳn thì các ô
              của bước kia bị hủy đăng ký khỏi form và mất dữ liệu vừa nhập. */}
          <div className={step === 0 ? undefined : 'hidden'}>
            <FormCard title="Thông tin chính" icon={Info} iconClassName="text-primary">
              <DocumentMainInfoFields form={form} isEditing={false} />
            </FormCard>
          </div>

          <div className={step === 1 ? undefined : 'hidden'}>
            <FormCard
              title="Tình trạng xử lý"
              icon={Activity}
              iconClassName="text-violet-500"
            >
              <DocumentProcessingFields form={form} isEditing={false} />
            </FormCard>
          </div>

          <div className={step === 2 ? 'space-y-4' : 'hidden'}>
            <FormCard
              title="Thông tin bổ sung"
              icon={Layers}
              iconClassName="text-emerald-600"
            >
              <DocumentExtraInfoFields form={form} isEditing={false} />
            </FormCard>
            <DocumentAttachmentList attachments={attachments} onChange={setAttachments} />
          </div>

          <div className="flex items-center justify-between gap-3">
            <Button
              type="button"
              variant="outline"
              disabled={step === 0}
              onClick={() => setStep(step - 1)}
            >
              <ArrowLeft className="size-4" />
              Quay lại
            </Button>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate(appRoutes.document.documents)}
              >
                Hủy
              </Button>

              {step < LAST_STEP ? (
                <Button type="button" onClick={goNext}>
                  Tiếp tục
                  <ArrowRight className="size-4" />
                </Button>
              ) : (
                <Button type="submit">
                  <PenLine className="size-4" />
                  Tạo và soạn thảo
                </Button>
              )}
            </div>
          </div>
        </form>
      </Form>
    </PageContainer>
  )
}
