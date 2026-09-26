import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SearchSelect } from '@/shared/ui/search-select'

import type { DeptHeadCandidate } from '../types/purchase-request-detail'

/**
 * Ô «Trưởng phòng phê duyệt» dùng chung cho YCMH · YCBG · ĐMH — bao-CR-499 (đại ca chốt 26/09/2026).
 *
 * Một cột, hai nghĩa theo thời điểm: TRƯỚC khi duyệt là người ĐƯỢC CHỌN (hệ gửi chuông + mail cho
 * người này lúc gửi duyệt); bấm Duyệt xong hệ ghi đè bằng người THỰC duyệt (bao-CR-490) và ô khóa.
 * Bản in luôn in tên đang nằm trong cột. Cố ý KHÔNG gộp với ô «Trưởng bộ phận» (CR-474): đại ca
 * muốn giữ hai ô tách để sau này bỏ ô này được mà không đụng ô kia.
 *
 * Danh sách chọn = người DUYỆT ĐƯỢC chứng từ này (backend `core/approver_candidates.py`), không
 * phải cả danh mục nhân sự — đại ca chốt hướng 1 ngày 26/09/2026.
 */
interface ApproverSelectProps {
  id: string
  /** id nhân sự đang nằm trong cột (0 = chưa chọn). */
  value: number
  /** Tên hiển thị backend trả — dùng khi khóa hoặc khi người đó không còn trong danh sách. */
  name: string
  candidates: DeptHeadCandidate[]
  /** Đang ở chế độ sửa VÀ phiếu chưa duyệt. */
  editable: boolean
  onChange: (next: { approver_employee_id: number; approver_employee_name: string }) => void
}

export function ApproverSelect({ id, value, name, candidates, editable, onChange }: ApproverSelectProps) {
  const inList = candidates.some((candidate) => candidate.employee_id === value)
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id} className={editable && candidates.length ? '' : 'text-muted-foreground'}>
        Trưởng phòng phê duyệt
      </Label>
      {editable && candidates.length ? (
        <SearchSelect
          id={id}
          searchInTrigger
          value={inList ? String(value) : ''}
          placeholder={name || 'Chọn người sẽ duyệt — hệ báo cho người này khi gửi duyệt'}
          searchPlaceholder="Gõ tên hoặc mã nhân sự…"
          options={candidates.map((candidate) => ({
            value: String(candidate.employee_id),
            label: candidate.position
              ? `${candidate.code} - ${candidate.name} - ${candidate.position}`
              : `${candidate.code} - ${candidate.name}`,
          }))}
          onChange={(next) => {
            const candidate = candidates.find((option) => option.employee_id === Number(next))
            if (!candidate || candidate.employee_id === value) return
            onChange({ approver_employee_id: candidate.employee_id, approver_employee_name: candidate.name })
          }}
        />
      ) : (
        <ReadOnlyValue>
          {name ||
            (editable ? 'Chưa có ai duyệt được phiếu này — kiểm tra phân quyền phòng ban' : 'Chưa chọn')}
        </ReadOnlyValue>
      )}
    </div>
  )
}
