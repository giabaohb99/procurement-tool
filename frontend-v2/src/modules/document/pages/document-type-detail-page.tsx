import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { DocumentTypeForm } from '../components/document-type-form'
import { RecordHistoryCard } from '../components/record-history-card'
import {
  useDocumentType,
  useDocumentTypeActions,
  useDocumentTypeHistory,
} from '../hooks/use-document-types'

/**
 * Trang THÊM MỚI / SỬA một loại văn bản.
 *
 * Là trang riêng chứ không phải hộp thoại: bên dưới form còn khối "Lịch sử thao
 * tác", và sau này còn danh sách văn bản thuộc loại đó — nhét hết vào popup thì
 * không đủ chỗ, cũng không gửi link cho nhau được.
 *
 * Một route dùng cho cả hai việc: `/document/types/new` → id không phải số →
 * form rỗng.
 */
/** Nối nút Lưu trên header với thẻ `<form>` nằm trong `DocumentTypeForm`. */
const FORM_ID = 'document-type-form'

export function DocumentTypeDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  const documentTypeId = Number(id)
  const isCreating = !Number.isFinite(documentTypeId)

  const documentType = useDocumentType(isCreating ? undefined : documentTypeId)
  const history = useDocumentTypeHistory(isCreating ? undefined : documentTypeId)
  const { save, remove, isCodeTaken } = useDocumentTypeActions()

  function backToList() {
    navigate(appRoutes.document.types)
  }

  // Id có trong URL nhưng không có bản ghi: link cũ của bản ghi đã bị xóa.
  if (!isCreating && !documentType) {
    return (
      <ErrorState
        code="404"
        title="Không tìm thấy loại văn bản"
        description="Loại văn bản này không tồn tại hoặc đã bị xóa."
      >
        <Button onClick={backToList}>
          <ArrowLeft className="size-4" />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  return (
    <PageContainer className="space-y-5">
      <PageHeader
        title={isCreating ? 'Thêm loại văn bản' : (documentType?.name ?? '')}
        description={
          isCreating
            ? 'Khai báo một loại văn bản mới cho hệ thống.'
            : `Mã loại ${documentType?.code} · số hiệu dạng ${documentType?.prefix}-2026-001`
        }
        leading={
          // Chỉ icon: đặt sát tiêu đề rồi thì mũi tên đã đủ nghĩa "lùi ra danh
          // sách", thêm chữ chỉ đẩy tiêu đề đi xa.
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={backToList}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        actions={
          <>
            {!isCreating && documentType && (
              <ConfirmIconButton
                icon={Trash2}
                title="Xóa"
                destructive
                confirmTitle={`Xóa loại "${documentType.name}"?`}
                confirmDescription="Thao tác này không hoàn tác được. Văn bản đã tạo theo loại này vẫn giữ nguyên."
                confirmLabel="Xóa"
                onConfirm={() => {
                  remove(documentType.id)
                  toast.success(`Đã xóa loại "${documentType.name}"`)
                  backToList()
                }}
              />
            )}

            <Button variant="outline" onClick={backToList}>
              Hủy
            </Button>
            {/* Nút Lưu đứng ngoài form, nối vào bằng `form=` (xem `formId`). */}
            <Button type="submit" form={FORM_ID}>
              <Save className="size-4" />
              Lưu
            </Button>
          </>
        }
      />

      <DocumentTypeForm
        formId={FORM_ID}
        documentType={documentType}
        isCodeTaken={isCodeTaken}
        onSubmit={(values) => {
          const savedId = save(values, documentType?.id)
          toast.success(isCreating ? 'Đã thêm loại văn bản' : 'Đã cập nhật loại văn bản')
          // Thêm mới xong ở lại chính bản ghi vừa tạo (đổi URL sang id thật):
          // người dùng thường sửa tiếp hoặc muốn xem lịch sử ngay.
          if (isCreating) navigate(appRoutes.document.typeDetail(savedId), { replace: true })
        }}
      />

      {/* Chỉ bản ghi đã tồn tại mới có lịch sử để xem. */}
      {!isCreating && <RecordHistoryCard entries={history} />}
    </PageContainer>
  )
}
