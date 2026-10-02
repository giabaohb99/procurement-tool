import { useMemo } from 'react'

import { SUBJECT_KIND } from '@/shared/access-subject/subject-kind'
import type { SubjectOption } from '@/shared/access-subject/subject-kind'
import { useCompanies } from './use-companies'
import { useDepartments } from './use-departments'
import { useEmployees } from './use-employees'
import { useRoles } from './use-roles'

interface UseAccessSubjectOptionsResult {
  options: SubjectOption[]
  loading: boolean
}

/**
 * Dựng danh mục BỐN loại chủ thể (người · phòng ban · pháp nhân · vai trò)
 * cho `AccessSubjectPicker` (`shared/access-subject/`) — `hr` sở hữu bốn danh
 * bạ gốc nên hook đứng ở đây; `document` (và `system` ở phase 06 của kế hoạch
 * `plans/261002-0836-phan-quyen-tung-bao-cao`) chỉ mượn, đúng tiền lệ
 * `role-permission-page.tsx` đã import hook của `hr` từ phân hệ khác.
 *
 * Giữ nguyên hai quy tắc đã có ở bản cũ (`folder-share-subject-picker.tsx`):
 *  - Thứ tự CỐ Ý pháp nhân · phòng ban · vai trò LÊN TRƯỚC, người xuống cuối
 *    (phản hồi 24/09/2026: 272 dòng người đứng đầu vùi mất 18 phòng ban + 14
 *    pháp nhân, người dùng tưởng chỉ chia sẻ được cho từng người);
 *  - Tên phòng ban kèm tên pháp nhân (`"Kế toán · DEGO Holding"`) vì nhiều
 *    công ty có phòng TRÙNG TÊN, không kèm thì chọn nhầm phòng của công ty khác.
 */
export function useAccessSubjectOptions(): UseAccessSubjectOptionsResult {
  const employees = useEmployees({ page_size: 1000, is_active: true })
  const departments = useDepartments({ page_size: 500 })
  const companies = useCompanies({ page_size: 200, is_active: true })
  const roles = useRoles()

  const options = useMemo<SubjectOption[]>(() => {
    const companyNames = new Map(
      (companies.data?.items ?? []).map((c) => [c.id, c.short_name || c.name] as const),
    )
    const fromCompanies = (companies.data?.items ?? []).map((c) => ({
      subject_kind: SUBJECT_KIND.company,
      subject_id: c.id,
      label: c.short_name || c.name,
    }))
    const fromDepartments = (departments.data?.items ?? [])
      .filter((d) => d.is_active)
      .map((d) => {
        const company = companyNames.get(d.company_id)
        return {
          subject_kind: SUBJECT_KIND.department,
          subject_id: d.id,
          label: company ? `${d.name} · ${company}` : d.name,
        }
      })
    const fromRoles = (roles.data ?? []).map((r) => ({
      subject_kind: SUBJECT_KIND.role,
      subject_id: r.id,
      label: r.name,
    }))
    const fromEmployees = (employees.data?.items ?? []).map((e) => ({
      subject_kind: SUBJECT_KIND.employee,
      subject_id: e.id,
      label: e.full_name,
    }))
    return [...fromCompanies, ...fromDepartments, ...fromRoles, ...fromEmployees]
  }, [companies.data, departments.data, roles.data, employees.data])

  return {
    options,
    loading:
      employees.isLoading || departments.isLoading || companies.isLoading || roles.isLoading,
  }
}
