import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SearchSelect, type SearchSelectOption } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import type { HeadcountPlanDocumentLink } from '../types/headcount-plan'
import type { HeadcountPlanDraft } from '../utils/headcount-plan-draft'
import { HeadcountPlanLinkedDocuments } from './headcount-plan-linked-documents'
import { PlanLabeledField } from './plan-labeled-field'

interface HeadcountPlanBasisFieldsProps {
  draft: HeadcountPlanDraft
  readOnly: boolean
  /** Ô chọn người duyệt — rỗng khi người xem không đọc được danh bạ nhân sự. */
  approverOptions: SearchSelectOption[]
  /** Tên người duyệt máy chủ trả kèm — để người không đọc được danh bạ vẫn thấy tên. */
  approverName?: string
  canSearchDocuments: boolean
  onPatch: (patch: Partial<HeadcountPlanDraft>) => void
  onDocumentsChange: (documents: HeadcountPlanDocumentLink[]) => void
}

/**
 * Nửa sau khối 1 — CĂN CỨ: số, ngày, người duyệt, văn bản liên kết, lý do (tài liệu 06 §2.1). Không
 * ô nào bắt buộc: bản này chỉ GHI căn cứ duyệt ngoài hệ thống, chưa có trạng thái duyệt (§9).
 */
export function HeadcountPlanBasisFields({
  draft,
  readOnly,
  approverOptions,
  approverName,
  canSearchDocuments,
  onPatch,
  onDocumentsChange,
}: HeadcountPlanBasisFieldsProps) {
  const approverLabel =
    approverOptions.find((o) => o.value === String(draft.approver_employee_id))?.label ?? approverName ?? ''

  return (
    <>
      <PlanLabeledField label="Số căn cứ" htmlFor="hp-basis-no">
        {readOnly ? (
          <ReadOnlyValue>{draft.basis_no}</ReadOnlyValue>
        ) : (
          <Input
            id="hp-basis-no"
            value={draft.basis_no}
            maxLength={100}
            placeholder="Ví dụ 12/QĐ-BGĐ"
            onChange={(e) => onPatch({ basis_no: e.target.value })}
          />
        )}
      </PlanLabeledField>
      <PlanLabeledField label="Ngày căn cứ" htmlFor="hp-basis-date">
        {readOnly ? (
          <ReadOnlyValue>{draft.basis_date ? formatDate(draft.basis_date) : ''}</ReadOnlyValue>
        ) : (
          <DatePicker
            id="hp-basis-date"
            value={draft.basis_date}
            clearable
            onChange={(basis_date) => onPatch({ basis_date })}
          />
        )}
      </PlanLabeledField>
      <PlanLabeledField label="Người duyệt" htmlFor="hp-approver">
        {readOnly || approverOptions.length === 0 ? (
          <ReadOnlyValue>{approverLabel}</ReadOnlyValue>
        ) : (
          <SearchSelect
            id="hp-approver"
            value={draft.approver_employee_id ? String(draft.approver_employee_id) : ''}
            options={approverOptions}
            clearable
            placeholder="Chọn nhân sự"
            searchPlaceholder="Tìm theo tên hoặc mã…"
            onChange={(v) => onPatch({ approver_employee_id: Number(v) || 0 })}
          />
        )}
      </PlanLabeledField>
      <PlanLabeledField label="Văn bản liên kết" fullWidth>
        <HeadcountPlanLinkedDocuments
          documents={draft.documents}
          onChange={onDocumentsChange}
          readOnly={readOnly}
          canSearch={canSearchDocuments}
        />
      </PlanLabeledField>
      <PlanLabeledField label="Lý do / ghi chú" htmlFor="hp-note" fullWidth>
        {readOnly ? (
          <ReadOnlyValue multiline>{draft.note}</ReadOnlyValue>
        ) : (
          <Textarea
            id="hp-note"
            value={draft.note}
            maxLength={500}
            placeholder="Ví dụ: Mở thêm mảng kế toán thuế"
            onChange={(e) => onPatch({ note: e.target.value })}
          />
        )}
      </PlanLabeledField>
    </>
  )
}
