import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Info, Layers, PenLine } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Form } from '@/shared/ui/form'
import { FormCard } from '@/shared/ui/form-card'
import { FormStepper } from '@/shared/ui/form-stepper'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { DocumentExtraInfoFields } from '../components/document-extra-info-fields'
import {
  DocumentMainInfoFields,
  MAIN_INFO_FIELDS,
} from '../components/document-main-info-fields'
import { emptyDocumentForm, formToPayload } from '../helpers/document-form-defaults'
import { useSaveDocument } from '../hooks/use-documents'
import {
  documentRecordSchema,
  type DocumentRecordFormValues,
} from '../schemas/document-record-schema'

/**
 * Hai bước của form tạo văn bản.
 *
 * `fields` là các ô được kiểm khi bấm "Tiếp tục" — chỉ kiểm bước đang đứng, vì
 * bước sau còn chưa mở ra để nhập.
 */
const STEPS = [
  {
    title: 'Thông tin chính',
    description: 'Loại, pháp nhân, phòng, tên văn bản',
    fields: MAIN_INFO_FIELDS,
  },
  {
    title: 'Thông tin bổ sung',
    description: 'Mức mật, hiệu lực, từ khóa',
    fields: [],
  },
] as const

const LAST_STEP = STEPS.length - 1

/**
 * Trang TẠO VĂN BẢN.
 *
 * **Không có bước xin phép** — ai có quyền `document.create` thì tạo thẳng
 * (chốt 14/08/2026, quyết định 7 của plan). Bù lại, khối gợi ý ngay dưới ô tên
 * hiện luôn văn bản cùng loại cùng phòng đang hiệu lực để người soạn thấy trước
 * khi ngồi gõ bản thứ hai cho cùng một việc.
 *
 * Tạo xong nhảy thẳng sang tab "Soạn thảo": lập xong cái vỏ thì việc kế tiếp
 * luôn là gõ nội dung.
 */
export function DocumentCreatePage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const save = useSaveDocument()

  const form = useForm<DocumentRecordFormValues>({
    resolver: zodResolver(documentRecordSchema),
    defaultValues: emptyDocumentForm(),
  })

  async function goNext() {
    const valid = await form.trigger([...STEPS[step].fields])
    if (!valid) {
      toast.error(`Còn ô bắt buộc chưa nhập ở bước ${STEPS[step].title}`)
      return
    }
    setStep(step + 1)
  }

  function handleSubmit(values: DocumentRecordFormValues) {
    //  Gõ Enter trong một ô nhập cũng gửi form (implicit submission của trình
    //  duyệt). Ở bước chưa cuối, ý người dùng là "sang bước tiếp" chứ không
    //  phải "tạo văn bản" — nếu không chặn thì gõ xong tên văn bản, bấm Enter
    //  là văn bản ra đời với bộ trường bổ sung còn trống trơn.
    if (step < LAST_STEP) {
      setStep(step + 1)
      return
    }

    save.mutate(
      { values: { ...formToPayload(values), content_html: '' } },
      {
        onSuccess: (record) => {
          navigate(appRoutes.document.documentDetail(record.id), { replace: true })
        },
      },
    )
  }

  return (
    <PageContainer className="space-y-5">
      <PageHeader
        title="Tạo văn bản"
        description="Số hiệu do hệ cấp — khi lưu bản nháp hoặc khi được duyệt, tùy loại văn bản."
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

      <FormStepper steps={STEPS} current={step} onGoTo={setStep} className="max-w-3xl" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          {/* Giữ CẢ HAI bước trong DOM, chỉ ẩn bước không xem: gỡ hẳn thì các ô
              của bước kia bị hủy đăng ký khỏi form và mất dữ liệu vừa nhập. */}
          <div className={step === 0 ? undefined : 'hidden'}>
            <FormCard title="Thông tin chính" icon={Info} iconClassName="text-primary">
              <DocumentMainInfoFields form={form} isNumbered={false} />
            </FormCard>
          </div>

          <div className={step === 1 ? undefined : 'hidden'}>
            <FormCard
              title="Thông tin bổ sung"
              icon={Layers}
              iconClassName="text-emerald-600"
            >
              <DocumentExtraInfoFields form={form} />
            </FormCard>
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

              {/* ⚠️ `key` KHÁC NHAU là bắt buộc, không phải cho đẹp.
                  Cùng key thì React giữ NGUYÊN nút DOM cũ và chỉ đổi thuộc tính
                  `type`. Bấm chuột thật: click bắn ra → `goNext` chạy → await
                  xong trong microtask → React render lại ngay trong nhịp đó →
                  nút đang bấm biến thành `type="submit"` → trình duyệt mới xử
                  lý hành vi kích hoạt, đọc `type` MỚI và gửi form luôn. Kết quả
                  là bấm "Tiếp tục" ở bước 1 tạo thẳng văn bản, bỏ qua bước 2.
                  Key khác nhau → React thay hẳn nút, nút cũ rời khỏi DOM trước
                  khi tới bước kích hoạt nên không gửi form được. */}
              {step < LAST_STEP ? (
                <Button key="next" type="button" onClick={goNext}>
                  Tiếp tục
                  <ArrowRight className="size-4" />
                </Button>
              ) : (
                <Button key="submit" type="submit" disabled={save.isPending}>
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
