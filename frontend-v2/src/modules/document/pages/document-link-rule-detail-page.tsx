import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentLinkRuleForm } from '../components/document-link-rule-form'
import { linkRuleToInput } from '../helpers/link-rule-input'
import {
  useDeleteDocumentLinkRule,
  useDocumentLinkRule,
  useSaveDocumentLinkRules,
} from '../hooks/use-document-link-rules'

const FORM_ID = 'document-link-rule-form'

/** Trang THÊM / SỬA một dòng quy tắc quan hệ (E01). */
export function DocumentLinkRuleDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  const ruleId = Number(id)
  const isCreating = !Number.isFinite(ruleId)

  const { data: rule, isLoading } = useDocumentLinkRule(isCreating ? undefined : ruleId)
  const save = useSaveDocumentLinkRules()
  const remove = useDeleteDocumentLinkRule()

  const backTo = appRoutes.document.linkRules

  return (
    <DetailPageShell
      title={
        isCreating
          ? 'Thêm quy tắc quan hệ'
          : rule
            ? `${rule.source_type_name} — ${rule.relation_label}`
            : ''
      }
      description={
        isCreating
          ? 'Loại văn bản này phải trỏ tới loại nào, bắt buộc hay không, được mấy cái.'
          : rule && `Tới ${rule.target_type_name}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={backTo}
      isMissing={!isCreating && !isLoading && !rule}
      missingTitle="Không tìm thấy quy tắc"
      audit={rule ? { entity: 'doc_type_link_rule', id: rule.id } : undefined}
      deleteConfirmTitle="Xóa quy tắc quan hệ?"
      //  Xóa quy tắc KHÔNG xóa quan hệ đã khai — nói rõ để người xóa khỏi tưởng
      //  mình đang dọn cả dữ liệu lịch sử.
      deleteConfirmDescription="Từ nay loại này không khai thêm quan hệ đó được nữa. Các quan hệ đã khai trên văn bản vẫn giữ nguyên."
      onDelete={
        rule ? () => remove.mutate(rule.id, { onSuccess: () => navigate(backTo) }) : undefined
      }
    >
      <DocumentLinkRuleForm
        //  Bản ghi về sau lượt render đầu — `key` làm form dựng lại với dữ liệu
        //  thật thay vì phải đồng bộ state bằng effect.
        key={rule?.id ?? 'new'}
        formId={FORM_ID}
        initial={rule && linkRuleToInput(rule)}
        sourceTypeName={rule?.source_type_name}
        //  Thêm mới cho chọn nhiều loại đích một lần; sửa thì đúng một dòng.
        allowMultipleTargets={isCreating}
        onSubmit={(rows) =>
          save.mutate(
            { id: rule?.id, rows },
            {
              onSuccess: ({ saved }) => {
                if (!isCreating || saved.length === 0) return
                //  Khai một dòng thì ở lại chính nó để sửa tiếp; khai nhiều thì
                //  về danh sách — không có "dòng vừa tạo" nào để đứng lại.
                navigate(
                  saved.length === 1
                    ? appRoutes.document.linkRuleDetail(saved[0].id)
                    : appRoutes.document.linkRules,
                  { replace: true },
                )
              },
            },
          )
        }
      />
    </DetailPageShell>
  )
}
