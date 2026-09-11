import { ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentTypeForm } from '../components/document-type-form'
import { DocumentTypeLinkRulesCard } from '../components/document-type-link-rules-card'
import { useSaveDocumentLinkRules } from '../hooks/use-document-link-rules'
import {
  useDeleteDocumentType,
  useDocumentType,
  useSaveDocumentType,
} from '../hooks/use-document-types'
import { documentCodeSample } from '../types/document-type'
import type { DocTypeLinkRuleInput } from '../types/document-link-rule'

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

  //  Quan hệ khai lúc TẠO MỚI: dòng quy tắc cần một `source_type_id` có thật,
  //  mà loại thì chưa ra đời. Giữ tạm ở đây rồi gửi ngay sau khi lưu loại —
  //  đúng lối quyền / phạm vi đang dùng ở trang tạo văn bản.
  const [pendingRules, setPendingRules] = useState<DocTypeLinkRuleInput[]>([])

  const { data: documentType, isLoading } = useDocumentType(
    isCreating ? undefined : documentTypeId,
  )
  const save = useSaveDocumentType()
  const saveRules = useSaveDocumentLinkRules()
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
    //  ⚠️ **Dùng `DetailPageShell`, đừng dựng lại đầu trang bằng tay.** Trang này
    //  từng tự ghép `PageContainer` + `PageHeader` + nút lùi + Xóa/Hủy/Lưu +
    //  `AuditTimeline` — đúng từng thứ mà khung chung đã lo, chép lại khoảng 60
    //  dòng. Cái giá trả ngay: mọi bản vá đầu trang ở khung chung (duoc-CR-373 —
    //  bỏ nút Hủy thừa, cho Lưu trải hết hàng, ghim dải khi cuộn) **không tới
    //  được trang này**, nên nó vẫn bày ba nút chen chúc trong khi năm trang anh
    //  em đã gọn (khách bắt được 11/09/2026). Sáu trang chi tiết còn lại của phân
    //  hệ đều đi qua khung chung — trang này là cái cuối cùng còn đứng ngoài.
    //
    //  `stickyHeader`: form ba khối, dưới còn thẻ quan hệ và nhật ký nên trang
    //  rất dài, mà nút Lưu ở trên đầu.
    <DetailPageShell
      title={isCreating ? 'Thêm loại văn bản' : (documentType?.name ?? '')}
      //  ⚠️ Dòng mô tả ẨN ở khổ hẹp — cùng lý do với chi tiết Sổ văn bản
      //  (duoc-CR-372): ở trang đã có bản ghi nó chỉ nhắc lại *mã loại* (ô đầu
      //  tiên của biểu mẫu) và *mẫu số hiệu* (hiện ngay trong thẻ «Số hiệu» bên
      //  dưới), mà dải này GHIM nên mỗi dòng là chỗ đứng yên vĩnh viễn — riêng
      //  câu này rớt hai hàng, đẩy dải từ 97px lên **145px = 18%** màn 796px.
      //  Trang thêm mới thì giữ: ở đó chưa có ô nào điền.
      description={
        isCreating ? (
          'Khai báo một loại văn bản mới cho hệ thống.'
        ) : (
          <span className="max-md:hidden">
            {`Mã loại ${documentType?.code} · số hiệu dạng ${
              documentType
                ? documentCodeSample(documentType.code, documentType.id_scheme)
                : ''
            }`}
          </span>
        )
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={appRoutes.document.settingsTab('types')}
      stickyHeader
      audit={documentType ? { entity: 'doc_type', id: documentType.id } : undefined}
      deleteConfirmTitle={documentType ? `Xóa loại "${documentType.name}"?` : undefined}
      deleteConfirmDescription="Thao tác này không hoàn tác được. Văn bản đã tạo theo loại này vẫn giữ nguyên."
      onDelete={
        documentType
          ? () => remove.mutate(documentType.id, { onSuccess: backToList })
          : undefined
      }
    >
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
              onSuccess: async (saved) => {
                if (!isCreating) return

                // Quan hệ khai lúc chưa có id: giờ mới ghi được, và phải ghi
                // XONG rồi mới đổi URL — đổi trước thì trang dựng lại theo id
                // mới, component này rời DOM và mẻ ghi đứt giữa chừng.
                if (pendingRules.length > 0) {
                  await saveRules.mutateAsync({
                    rows: pendingRules.map((row) => ({ ...row, source_type_id: saved.id })),
                  })
                }

                // Thêm mới xong ở lại chính bản ghi vừa tạo (đổi URL sang id
                // thật): người dùng thường sửa tiếp hoặc xem nhật ký ngay.
                navigate(appRoutes.document.typeDetail(saved.id), { replace: true })
              },
            },
          )
        }
      />

      {/* Đứng NGOÀI thẻ `<form>` của form loại: form lồng form là mã HTML sai,
          và bấm Lưu ở hộp thoại quan hệ sẽ gửi luôn cả form loại.

          Lúc TẠO MỚI chưa có id để dòng quy tắc trỏ vào, nên thẻ chạy trên state
          tạm ở đây rồi ghi ngay sau khi loại được lưu — cùng lối với quyền và
          phạm vi ở trang tạo văn bản. */}
      {isCreating ? (
        <DocumentTypeLinkRulesCard pending={pendingRules} onPendingChange={setPendingRules} />
      ) : (
        documentType && (
          <DocumentTypeLinkRulesCard docTypeId={documentType.id} docTypeName={documentType.name} />
        )
      )}

      {/* Nhật ký thao tác do `DetailPageShell` dựng ở cuối, theo `audit` ở trên. */}
    </DetailPageShell>
  )
}
