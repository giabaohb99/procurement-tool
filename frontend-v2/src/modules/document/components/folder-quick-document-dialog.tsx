import { zodResolver } from '@hookform/resolvers/zod'
import { FileStack, Loader2, Maximize2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { useAuth } from '@/core/auth/use-auth'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Form } from '@/shared/ui/form'
import { emptyDocumentForm, formToPayload } from '../helpers/document-form-defaults'
import { sendPendingAccessAndFiles } from '../helpers/send-pending-access-and-files'
import { useDocumentApprovalPreview } from '../hooks/use-document-approval-preview'
import { useSaveDocument } from '../hooks/use-documents'
import {
  documentRecordSchema,
  type DocumentRecordFormValues,
} from '../schemas/document-record-schema'
import { DOCUMENT_CONTENT_MODE } from '../types/document-record'
import { DocumentAccessFields, type PendingAccess } from './document-access-fields'
import { DocumentApproverPreviewLine } from './document-approver-preview-line'
import { DocumentPendingAttachments } from './document-pending-attachments'
import { FolderQuickDocumentFields } from './folder-quick-document-fields'

interface FolderQuickDocumentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Thư mục ĐANG XEM — văn bản tạo ra nằm luôn ở đây (thư mục chính). */
  folderId: number
  /** Pháp nhân của thư mục — `0` = thư mục tự do, rơi về pháp nhân của người đang đăng nhập. */
  folderCompanyId: number
  folderName?: string
}

/** Tên tệp bỏ đuôi — `Hop-dong-ABC.signed.pdf` → `Hop-dong-ABC.signed`. */
function titleFromFileName(name: string): string {
  const dot = name.lastIndexOf('.')
  return (dot > 0 ? name.slice(0, dot) : name).trim().slice(0, 500)
}

/**
 * «TẠO NHANH TỪ TỆP» ở trang Thư mục (yêu cầu 25/09/2026) — bản rút gọn của
 * trang tạo 3 bước, đi đúng nhánh «Tạo, không soạn thảo» của trang đó
 * (`content_mode = files`, `content_html` rỗng): tải tệp · năm ô bắt buộc ·
 * phân quyền · bấm Tạo. Phạm vi, sổ, hiệu lực, mức mật… không hỏi ở đây — mở
 * tab Thông tin của văn bản mà khai sau.
 *
 * Bắt buộc có ít nhất MỘT tệp: văn bản không soạn thảo lại không tệp là cái
 * vỏ rỗng — trang tạo đầy đủ còn hỏi lại cho qua, còn hộp «từ tệp» thì không
 * có lý do gì để tạo vỏ rỗng.
 */
export function FolderQuickDocumentDialog({
  open,
  onOpenChange,
  folderId,
  folderCompanyId,
  folderName,
}: FolderQuickDocumentDialogProps) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const save = useSaveDocument()
  const [files, setFiles] = useState<File[]>([])
  const [access, setAccess] = useState<PendingAccess[]>([])
  //  Chặn BẤM ĐÚP (bẫy thứ tư CR-317): `disabled={isPending}` chỉ đúng từ lượt
  //  render sau, nên chốt bằng ref đổi ngay trong tick.
  const creatingRef = useRef(false)
  const [creating, setCreating] = useState(false)

  const form = useForm<DocumentRecordFormValues>({
    resolver: zodResolver(documentRecordSchema),
    defaultValues: emptyDocumentForm({
      company_id: folderCompanyId || user?.company_id,
      department_id: user?.department_id,
      employee_id: user?.employee_id,
    }),
  })

  //  Cùng bộ tham số với trang tạo đầy đủ; ô nào hộp này không hỏi (độ khẩn,
  //  người ký…) thì lấy giá trị mặc định của form — đúng thứ sẽ được lưu.
  const approvalPreview = useDocumentApprovalPreview({
    doc_type_id: Number(form.watch('doc_type_id')) || 0,
    company_id: Number(form.watch('company_id')) || 0,
    department_id: Number(form.watch('department_id')) || 0,
    secrecy_level: Number(form.watch('secrecy_level')) || 0,
    urgency: Number(form.watch('urgency')) || 0,
    owner_employee_id: Number(form.watch('owner_employee_id')) || 0,
    drafter_employee_id: Number(form.watch('drafter_employee_id')) || 0,
    signer_employee_id: Number(form.watch('signer_employee_id')) || 0,
  })

  function handleOpenChange(next: boolean) {
    //  Đang gửi thì không cho đóng — đóng giữa chừng là văn bản ra đời mà
    //  quyền/tệp chưa kịp gửi, người dùng lại tưởng chưa tạo gì.
    //  Không tự dọn form ở đây: nơi gọi chỉ dựng hộp khi mở (`open && …`), nên
    //  mỗi lần mở là một form mới, mang đúng pháp nhân của thư mục lúc đó.
    if (!next && creatingRef.current) return
    onOpenChange(next)
  }

  function handleFilesChange(next: File[]) {
    //  Tự điền tên theo tệp đầu tiên — chỉ khi ô tên còn trống, không đè thứ
    //  người dùng đã gõ.
    if (next.length > 0 && !form.getValues('title').trim()) {
      form.setValue('title', titleFromFileName(next[0].name), { shouldValidate: true })
    }
    setFiles(next)
  }

  async function handleSubmit(values: DocumentRecordFormValues) {
    if (creatingRef.current) return
    if (files.length === 0) {
      toast.error('Chọn ít nhất một tệp — văn bản tạo nhanh không có phần soạn thảo.')
      return
    }
    creatingRef.current = true
    setCreating(true)
    try {
      const record = await save.mutateAsync({
        values: {
          ...formToPayload(values),
          folder_ids: [folderId],
          primary_folder_id: folderId,
          content_mode: DOCUMENT_CONTENT_MODE.files,
          content_html: '',
        },
      })
      await sendPendingAccessAndFiles(record.id, record.current_version_id ?? null, access, files)
      creatingRef.current = false
      setCreating(false)
      handleOpenChange(false)
    } catch (error) {
      toast.error(extractErrorMessage(error))
      creatingRef.current = false
      setCreating(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="flex max-h-[90dvh] flex-col overflow-hidden sm:max-w-4xl">
        {/*  `pr-8` chừa chỗ cho nút đóng (X) nằm tuyệt đối ở góc phải. */}
        <DialogHeader className="flex-row items-start justify-between gap-3 pr-8">
          <div className="space-y-1.5">
            <DialogTitle>Tạo nhanh từ tệp</DialogTitle>
            <DialogDescription>
              Văn bản không soạn thảo, lưu vào thư mục{' '}
              <span className="font-medium text-foreground">{folderName ?? `#${folderId}`}</span>.
              Các thông tin khác khai sau ở tab Thông tin.
            </DialogDescription>
          </div>
          {/*  «Mở rộng» = sang trang tạo đầy đủ 3 bước, giữ thư mục đích. Thứ
               đã nhập ở hộp này KHÔNG mang theo — trang kia tự điền lại bốn ô
               theo tài khoản, chỉ phải chọn lại loại + tệp. */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="shrink-0"
            disabled={creating}
            onClick={() => navigate(`${appRoutes.document.documentNew}?folder_id=${folderId}`)}
          >
            <Maximize2 className="size-4" />
            Mở rộng
          </Button>
        </DialogHeader>

        <Form {...form}>
          <form
            id="folder-quick-document-form"
            onSubmit={(event) => void form.handleSubmit(handleSubmit)(event)}
            className="-mx-6 min-h-0 flex-1 space-y-4 overflow-y-auto px-6"
          >
            <DocumentPendingAttachments bare files={files} onChange={handleFilesChange} />
            <FolderQuickDocumentFields form={form} />
            {/*  Người duyệt dự kiến (yêu cầu 25/09/2026) — ngay dưới Thông tin chính,
                 TRÊN Quyền truy cập: nó đọc từ các ô vừa chọn ngay phía trên. */}
            <DocumentApproverPreviewLine
              preview={approvalPreview.data}
              isLoading={approvalPreview.isLoading}
            />
            <DocumentAccessFields rows={access} onChange={setAccess} hasBookField={false} />
          </form>
        </Form>

        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            disabled={creating}
            onClick={() => handleOpenChange(false)}
          >
            Hủy
          </Button>
          <Button type="submit" form="folder-quick-document-form" disabled={creating}>
            {creating ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <FileStack className="size-4" />
            )}
            Tạo văn bản
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
