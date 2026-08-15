import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { DocumentTypeForm } from '../components/document-type-form'
import {
  useDeleteDocumentType,
  useDocumentType,
  useSaveDocumentType,
} from '../hooks/use-document-types'
import { documentCodeSample } from '../types/document-type'

/**
 * Trang THÊM MỚI / SỬA một loại văn bản.
 *
 * Là trang riêng chứ không phải hộp thoại: form đã ba khối (thông tin, số hiệu,
 * quy tắc), bên dưới còn nhật ký thao tác, và sau này còn danh sách văn bản
 * thuộc loại đó — nhét hết vào popup thì không đủ chỗ, cũng không gửi link cho
 * nhau được.
 *
 * Một route dùng cho cả hai việc: `/document/types/new` → id không phải số →
 * form rỗng.
 */
const FORM_ID = 'document-type-form'

export function DocumentTypeDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  const documentTypeId = Number(id)
  const isCreating = !Number.isFinite(documentTypeId)

  const { data: documentType, isLoading } = useDocumentType(
    isCreating ? undefined : documentTypeId,
  )
  const save = useSaveDocumentType()
  const remove = useDeleteDocumentType()

  function backToList() {
    navigate(appRoutes.document.settingsTab('types'))
  }

  if (!isCreating && isLoading) {
    return (
      <PageContainer className="space-y-5">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-80 w-full" />
      </PageContainer>
    )
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
            : `Mã loại ${documentType?.code} · số hiệu dạng ${
                documentType
                  ? documentCodeSample(documentType.code, documentType.id_scheme)
                  : ''
              }`
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
                onConfirm={() => remove.mutate(documentType.id, { onSuccess: backToList })}
              />
            )}

            <Button variant="outline" onClick={backToList}>
              Hủy
            </Button>
            {/* Nút Lưu đứng ngoài form, nối vào bằng `form=` (xem `FORM_ID`). */}
            <Button type="submit" form={FORM_ID} disabled={save.isPending}>
              <Save className="size-4" />
              Lưu
            </Button>
          </>
        }
      />

      <DocumentTypeForm
        formId={FORM_ID}
        documentType={documentType}
        onSubmit={(values) =>
          save.mutate(
            {
              id: documentType?.id,
              // Ba trường không có trên form: `needs_request` đã bỏ khỏi bản 1,
              // hai trường còn lại giữ nguyên giá trị cũ.
              values: {
                ...values,
                needs_request: false,
                default_flow_id: documentType?.default_flow_id ?? 0,
                sort_order: documentType?.sort_order ?? 0,
              },
            },
            {
              onSuccess: (saved) => {
                // Thêm mới xong ở lại chính bản ghi vừa tạo (đổi URL sang id
                // thật): người dùng thường sửa tiếp hoặc xem nhật ký ngay.
                if (isCreating) {
                  navigate(appRoutes.document.typeDetail(saved.id), { replace: true })
                }
              },
            },
          )
        }
      />

      {/* Chỉ bản ghi đã tồn tại mới có nhật ký để xem. */}
      {!isCreating && documentType && (
        <AuditTimeline entity="doc_type" entityId={documentType.id} />
      )}
    </PageContainer>
  )
}
