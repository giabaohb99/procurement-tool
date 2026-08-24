import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Copy, Info, Layers, PenLine, Target } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { purchaseRequestSupportApi } from '@/modules/procurement/api/purchase-request-support-api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Form } from '@/shared/ui/form'
import { FormCard } from '@/shared/ui/form-card'
import { FormStepper } from '@/shared/ui/form-stepper'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { documentCloneApi } from '../api/document-clone-api'
import { documentScopeApi } from '../api/document-scope-api'
import { documentAccessApi } from '../api/document-api'
import { DocumentAccessFields, type PendingAccess } from '../components/document-access-fields'
import { DocumentClonePlanFields } from '../components/document-clone-plan-fields'
import { DocumentExtraInfoFields } from '../components/document-extra-info-fields'
import { DocumentMainInfoFields, MAIN_INFO_FIELDS } from '../components/document-main-info-fields'
import { DocumentPendingAttachments } from '../components/document-pending-attachments'
import { DocumentPrerequisiteDialog } from '../components/document-prerequisite-dialog'
import { DocumentScopeFields, type PendingScope } from '../components/document-scope-fields'
import { cloneTargetsFromScopes } from '../helpers/clone-targets-from-scopes'
import { emptyDocumentForm, formToPayload } from '../helpers/document-form-defaults'
import { useDocumentBooks } from '../hooks/use-document-books'
import { useActiveDocumentTypes } from '../hooks/use-document-types'
import { useDocumentPrerequisites, useSaveDocument } from '../hooks/use-documents'
import { useDocumentTemplate } from '../hooks/use-document-templates'
import {
  documentRecordSchema,
  type DocumentRecordFormValues,
} from '../schemas/document-record-schema'
import type { DocumentClonePlanInput } from '../types/document-clone'

/**
 * Hai bước của form tạo văn bản.
 *
 * `fields` là các ô được kiểm khi bấm "Tiếp tục" — chỉ kiểm bước đang đứng, vì
 * bước sau còn chưa mở ra để nhập.
 */
const STEPS = [
  {
    title: 'Thông tin chính',
    description: 'Tên, loại, pháp nhân, quyền truy cập',
    fields: MAIN_INFO_FIELDS,
  },
  {
    title: 'Phạm vi áp dụng',
    description: 'Áp cho ai, có tách bản riêng không',
    fields: [],
  },
  {
    title: 'Thông tin bổ sung',
    description: 'Mức mật, hiệu lực, từ khóa, tệp đính kèm',
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
  const [templateId, setTemplateId] = useState<number | null>(null)
  //  Quyền khai ở khối cuối thẻ thông tin chính phải chờ có id văn bản mới gửi
  //  được, nên giữ tạm ở đây.
  const [pendingAccess, setPendingAccess] = useState<PendingAccess[]>([])
  //  Phạm vi và kế hoạch clone cũng phải chờ có id văn bản, nên xếp hàng y hệt.
  const [pendingScopes, setPendingScopes] = useState<PendingScope[]>([])
  //  `company_ids` KHÔNG giữ ở đây: nơi nhận bản riêng suy thẳng từ các dòng
  //  phạm vi (xem `cloneTargetsFromScopes`). Giữ thêm một bản thứ hai là lại có
  //  hai danh sách lệch nhau — đúng thứ vừa bỏ đi.
  const [clonePlan, setClonePlan] = useState<Omit<DocumentClonePlanInput, 'company_ids'>>({
    due_date: '',
    note: '',
  })
  //  Tệp đính kèm cũng xếp hàng: chúng treo vào PHIÊN BẢN, mà phiên bản 1.0 chỉ
  //  ra đời cùng lúc với văn bản.
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  //  Bộ giá trị đang chờ người dùng trả lời hộp cảnh báo thiếu văn bản tiên
  //  quyết. Khác `null` = hộp đang mở. Giữ luôn cả `values` để lúc bấm "Vẫn
  //  tạo" không phải đọc lại form (người dùng không sửa được gì khi hộp đang mở,
  //  nhưng đọc lại là thêm một đường dữ liệu thứ hai cho cùng một việc).
  const [choXacNhan, setChoXacNhan] = useState<DocumentRecordFormValues | null>(null)
  const save = useSaveDocument()
  const selectedTemplate = useDocumentTemplate(templateId)
  const { items: books } = useDocumentBooks()
  const documentTypes = useActiveDocumentTypes()

  const form = useForm<DocumentRecordFormValues>({
    resolver: zodResolver(documentRecordSchema),
    defaultValues: emptyDocumentForm(),
  })

  //  Pháp nhân nhận bản riêng = các pháp nhân khai ở khối phạm vi, trừ nơi ban
  //  hành. Suy tại chỗ chứ không giữ state riêng: sửa một dòng phạm vi là danh
  //  sách clone đổi theo ngay, không có nhịp nào hai bên nói khác nhau.
  const cloneCompanyIds = cloneTargetsFromScopes(
    pendingScopes.map((row) => row.values),
    Number(form.watch('company_id')) || 0,
  )

  const docTypeId = Number(form.watch('doc_type_id')) || 0
  //  Hỏi ngay khi chọn loại dù hộp cảnh báo chỉ hiện lúc bấm Tạo — hỏi đúng
  //  nhịp bấm thì người dùng phải chờ một vòng mạng ở đúng nhịp sốt ruột nhất.
  const { data: thieuTienQuyet } = useDocumentPrerequisites(docTypeId)

  async function goNext() {
    const valid = await form.trigger([...STEPS[step].fields])
    if (!valid) {
      toast.error(`Còn ô bắt buộc chưa nhập ở bước ${STEPS[step].title}`)
      return
    }
    setStep(step + 1)
  }

  /**
   * Gửi ba thứ xếp hàng chờ — quyền, phạm vi, kế hoạch clone — ngay sau khi văn
   * bản có id.
   *
   * Tuần tự để dòng nào hỏng thì báo đúng dòng đó. Hỏng cũng **vẫn vào trang
   * soạn thảo**: văn bản đã tồn tại rồi, giữ người dùng ở lại form trắng tay
   * còn tệ hơn — mỗi phần đều có chỗ khai lại ở trang chi tiết, và câu báo lỗi
   * nói rõ phải mở tab nào.
   */
  async function guiPhanXepHang(documentId: number, versionId: number | null) {
    const hongQuyen: string[] = []
    for (const row of pendingAccess) {
      try {
        await documentAccessApi.grant(documentId, row.values)
      } catch {
        hongQuyen.push(row.subjectLabel || 'một đối tượng')
      }
    }
    if (hongQuyen.length > 0) {
      toast.error(
        `Chưa chia được quyền cho ${hongQuyen.join(', ')} — mở tab Thông tin để khai lại.`,
      )
    }

    const hongPhamVi: string[] = []
    for (const row of pendingScopes) {
      try {
        await documentScopeApi.create(documentId, row.values)
      } catch {
        hongPhamVi.push(row.label || 'một dòng')
      }
    }
    if (hongPhamVi.length > 0) {
      toast.error(
        `Chưa lưu được phạm vi cho ${hongPhamVi.join(', ')} — mở tab Phạm vi để khai lại.`,
      )
    }

    if (cloneCompanyIds.length > 0) {
      try {
        await documentCloneApi.savePlan(documentId, {
          ...clonePlan,
          company_ids: cloneCompanyIds,
        })
      } catch {
        toast.error('Chưa ghi được kế hoạch clone — khai lại ở thẻ «Bản clone ở pháp nhân con».')
      }
    }

    //  Tệp gửi MỘT LƯỢT chứ không từng tệp một: API nhận nhiều tệp trong một
    //  lần gọi, và người dùng chỉ cần biết "đính kèm được hay không".
    if (pendingFiles.length > 0 && versionId) {
      try {
        await purchaseRequestSupportApi.uploadAttachments(
          'document_version',
          versionId,
          pendingFiles,
        )
        toast.success(`Đã đính kèm ${pendingFiles.length} tệp`)
      } catch (error) {
        //  Nói nguyên câu của backend: gần như luôn là "tệp quá lớn" hoặc "đuôi
        //  tệp không cho phép" — người dùng cần biết tệp nào phải đổi.
        toast.error(`Chưa tải được tệp đính kèm — ${extractErrorMessage(error)}`)
      }
    }
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

    if (templateId && !selectedTemplate.data) {
      toast.error('Văn bản mẫu chưa tải xong. Vui lòng thử lại.')
      return
    }

    //  E04b — loại này bắt buộc trỏ tới loại khác mà kho chưa có cái nào để
    //  trỏ vào: hỏi lại một nhịp rồi vẫn cho tạo nếu họ chọn tiếp tục.
    if (thieuTienQuyet?.length) {
      setChoXacNhan(values)
      return
    }

    taoVanBan(values)
  }

  function taoVanBan(values: DocumentRecordFormValues) {
    save.mutate(
      {
        values: {
          ...formToPayload(values),
          content_html: selectedTemplate.data?.content_html ?? '',
        },
      },
      {
        onSuccess: async (record) => {
          //  `current_version_id` do chính lượt tạo đặt (`service.create` dựng
          //  phiên bản 1.0 rồi trỏ vào nó) nên đây là id có thật, không phải
          //  đoán.
          await guiPhanXepHang(record.id, record.current_version_id)
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
            onClick={() => navigate(appRoutes.document.documentsTab('outgoing'))}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
      />

      {/*  `max-w-5xl` chứ không phải `3xl`: bề rộng cũ đặt từ hồi form còn hai
           bước. Thêm bước thứ ba là mỗi bước mất một phần ba chỗ, và dòng mô tả
           bị cắt cụt ("Áp cho ai, có tách bản riêng kh…"). */}
      <FormStepper steps={STEPS} current={step} onGoTo={setStep} className="max-w-5xl" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          {/* Giữ CẢ BA bước trong DOM, chỉ ẩn bước không xem: gỡ hẳn thì các ô
              của bước kia bị hủy đăng ký khỏi form và mất dữ liệu vừa nhập. */}
          <div className={step === 0 ? undefined : 'hidden'}>
            <FormCard title="Thông tin chính" icon={Info} iconClassName="text-primary">
              <DocumentMainInfoFields
                form={form}
                isNumbered={false}
                templateId={templateId}
                onTemplateChange={setTemplateId}
              />

              {/* Quyền truy cập nằm CUỐI chính thẻ này, không tách thẻ riêng và
                  càng không tách bước riêng: khai xong ai được xem ngay lúc lập
                  văn bản thì không còn khoảng hở "đã tạo nhưng chưa chặn ai",
                  mà form cũng không dài thêm vì mặc định nó chỉ là một dòng. */}
              <DocumentAccessFields
                rows={pendingAccess}
                onChange={setPendingAccess}
                bookName={books.find((book) => book.id === Number(form.watch('book_id')))?.name}
              />
            </FormCard>
          </div>

          <div className={step === 1 ? undefined : 'hidden'}>
            <div className="space-y-4">
              <FormCard title="Phạm vi áp dụng" icon={Target} iconClassName="text-sky-600">
                <DocumentScopeFields rows={pendingScopes} onChange={setPendingScopes} />
              </FormCard>

              {/*  Thẻ này chỉ hiện khi phạm vi đã có pháp nhân ngoài nơi ban
                   hành. Nơi nhận bản riêng nay SUY từ phạm vi, nên lúc chưa
                   khai gì nó chẳng hỏi được câu nào — bày ra một thẻ chỉ để nói
                   "chưa có gì" là bắt người dùng đọc rồi bỏ qua.

                   Đứng SAU phạm vi, không song song: hai khối trả lời hai câu
                   nối tiếp nhau — "áp cho ai" rồi mới tới "mỗi nơi dùng chung
                   một bản hay tách bản riêng". */}
              {cloneCompanyIds.length > 0 && (
              <FormCard
                title="Bản clone ở pháp nhân con"
                icon={Copy}
                iconClassName="text-violet-600"
              >
                <DocumentClonePlanFields
                  value={{ ...clonePlan, company_ids: cloneCompanyIds }}
                  onChange={({ due_date, note }) => setClonePlan({ due_date, note })}
                  companyIds={cloneCompanyIds}
                />
              </FormCard>
              )}
            </div>
          </div>

          <div className={step === 2 ? 'space-y-5' : 'hidden'}>
            <FormCard title="Thông tin bổ sung" icon={Layers} iconClassName="text-emerald-600">
              <DocumentExtraInfoFields form={form} />
            </FormCard>

            {/*  Đính kèm ở BƯỚC CUỐI, ngay trên nút Tạo: tệp là thứ người soạn
                 cầm sẵn trong tay lúc lập văn bản, chứ không phải thông tin phải
                 nghĩ như tên hay phạm vi. */}
            <DocumentPendingAttachments files={pendingFiles} onChange={setPendingFiles} />
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
                onClick={() => navigate(appRoutes.document.documentsTab('outgoing'))}
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
                <Button
                  key="submit"
                  type="submit"
                  disabled={save.isPending || selectedTemplate.isFetching}
                >
                  <PenLine className="size-4" />
                  Tạo và soạn thảo
                </Button>
              )}
            </div>
          </div>
        </form>
      </Form>

      <DocumentPrerequisiteDialog
        open={choXacNhan !== null}
        onOpenChange={(open) => {
          if (!open) setChoXacNhan(null)
        }}
        docTypeName={documentTypes.find((type) => type.id === docTypeId)?.name ?? 'này'}
        items={thieuTienQuyet ?? []}
        onConfirm={() => {
          const values = choXacNhan
          setChoXacNhan(null)
          if (values) taoVanBan(values)
        }}
      />
    </PageContainer>
  )
}
