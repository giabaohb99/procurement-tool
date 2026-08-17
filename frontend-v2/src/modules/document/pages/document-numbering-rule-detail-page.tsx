import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentNumberingRuleForm } from '../components/document-numbering-rule-form'
import {
  useDeleteDocumentNumberingRule,
  useDocumentNumberingRule,
  useSaveDocumentNumberingRule,
} from '../hooks/use-document-numbering-rules'
import {
  NUMBERING_DIRECTIONS,
  type NumberingDirection,
} from '../types/document-numbering-rule'

const FORM_ID = 'document-numbering-rule-form'

function directionLabel(direction: NumberingDirection): string {
  return NUMBERING_DIRECTIONS.find((item) => item.value === direction)?.label ?? ''
}

/**
 * Trang THÊM / SỬA quy tắc đánh số.
 *
 * Trước đây là hộp thoại. Đổi sang trang riêng cho khớp với Sổ văn bản và các
 * danh mục còn lại: form này dài (mẫu số, phạm vi loại, phạm vi sổ) nên nhét
 * trong hộp thoại thì phải cuộn trong khung cuộn, và không gửi link cho nhau
 * xem đúng một quy tắc được.
 */
export function DocumentNumberingRuleDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [searchParams] = useSearchParams()

  const ruleId = Number(id)
  const isCreating = !Number.isFinite(ruleId)

  const { data: rule, isLoading } = useDocumentNumberingRule(isCreating ? undefined : ruleId)
  const save = useSaveDocumentNumberingRule()
  const remove = useDeleteDocumentNumberingRule()

  //  Thêm mới từ tab nào thì nhận sẵn chiều của tab đó.
  const directionParam = Number(searchParams.get('direction'))
  const initialDirection: NumberingDirection =
    directionParam >= 1 && directionParam <= 3 ? (directionParam as NumberingDirection) : 1

  // Quay lại đúng tab vừa đứng, không phải lúc nào cũng về tab đầu. Chiều 1 là
  // mặc định của danh sách nên bỏ hẳn param — `useUrlParamState` cũng tự xóa
  // giá trị mặc định khỏi URL, ghi vào chỉ làm link lệch với link app tự sinh.
  const backDirection = rule?.direction ?? initialDirection
  const backTo =
    backDirection === 1
      ? appRoutes.document.numberingRules
      : `${appRoutes.document.numberingRules}?direction=${backDirection}`

  return (
    <DetailPageShell
      title={isCreating ? 'Thiết lập quy tắc đánh số' : (rule?.pattern ?? '')}
      description={
        isCreating
          ? 'Mẫu số hiệu và bộ đếm áp cho một nhóm văn bản.'
          : rule &&
            `${directionLabel(rule.direction)} · ưu tiên ${rule.priority}${
              rule.has_issued_numbers ? ' · đã cấp số' : ''
            }`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={backTo}
      isMissing={!isCreating && !isLoading && !rule}
      missingTitle="Không tìm thấy quy tắc"
      audit={rule ? { entity: 'document_numbering_rule', id: rule.id } : undefined}
      deleteConfirmTitle="Xóa quy tắc đánh số?"
      deleteConfirmDescription={`Quy tắc ${rule?.pattern} sẽ bị xóa vĩnh viễn.`}
      //  Quy tắc đã cấp số thì backend từ chối xóa — ẩn hẳn nút thay vì để người
      //  dùng bấm rồi ăn lỗi. Muốn ngừng dùng thì tắt cờ "Đang dùng" trong form.
      onDelete={
        rule && !rule.has_issued_numbers
          ? () => remove.mutate(rule.id, { onSuccess: () => navigate(backTo) })
          : undefined
      }
    >
      <DocumentNumberingRuleForm
        formId={FORM_ID}
        rule={rule}
        initialDirection={initialDirection}
        onSubmit={(values) =>
          save.mutate(
            { id: rule?.id, values },
            {
              onSuccess: (saved) => {
                if (isCreating) {
                  navigate(appRoutes.document.numberingRuleDetail(saved.id), { replace: true })
                }
              },
            },
          )
        }
      />
    </DetailPageShell>
  )
}
