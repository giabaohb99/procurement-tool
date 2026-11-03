import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { ASSIGNMENT_ACTIVE_TODAY, ASSIGNMENT_FILTER_ALL } from '../utils/leave-policy-assignment-filters'

interface NamedOption {
  id: number
  name: string
}

interface LeavePolicyAssignmentListToolbarProps {
  keyword: string
  onKeywordChange: (value: string) => void
  policyId: string
  onPolicyIdChange: (value: string) => void
  policies: readonly NamedOption[]
  active: string
  onActiveChange: (value: string) => void
  /** `undefined` = không đọc được danh mục pháp nhân → không dựng ô đó. */
  companies: readonly NamedOption[] | undefined
  companyId: string
  onCompanyIdChange: (value: string) => void
}

/** Thanh lọc của màn Phân bổ chính sách (duoc-CR-717): tìm · chính sách · hiệu lực hôm nay · pháp nhân. */
export function LeavePolicyAssignmentListToolbar({
  keyword,
  onKeywordChange,
  policyId,
  onPolicyIdChange,
  policies,
  active,
  onActiveChange,
  companies,
  companyId,
  onCompanyIdChange,
}: LeavePolicyAssignmentListToolbarProps) {
  return (
    <>
      <SearchField
        value={keyword}
        onChange={onKeywordChange}
        placeholder="Tìm tên, mã NV…"
        className="md:min-w-56 md:max-w-xs"
      />
      <Select value={policyId} onValueChange={onPolicyIdChange}>
        <SelectTrigger className="w-full md:w-52" aria-label="Chính sách">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ASSIGNMENT_FILTER_ALL}>Mọi chính sách</SelectItem>
          {policies.map((p) => (
            <SelectItem key={p.id} value={String(p.id)}>
              {p.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={active} onValueChange={onActiveChange}>
        <SelectTrigger className="w-full md:w-48" aria-label="Hiệu lực">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ASSIGNMENT_FILTER_ALL}>Mọi phân bổ</SelectItem>
          <SelectItem value={ASSIGNMENT_ACTIVE_TODAY}>Đang hiệu lực hôm nay</SelectItem>
        </SelectContent>
      </Select>
      {companies && (
        <Select value={companyId} onValueChange={onCompanyIdChange}>
          <SelectTrigger className="w-full md:w-48" aria-label="Pháp nhân">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ASSIGNMENT_FILTER_ALL}>Mọi pháp nhân</SelectItem>
            {companies.map((c) => (
              <SelectItem key={c.id} value={String(c.id)}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </>
  )
}
