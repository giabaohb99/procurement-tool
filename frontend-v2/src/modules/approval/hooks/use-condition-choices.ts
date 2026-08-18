import { useCallback } from 'react'

import { useActiveDocumentTypes } from '@/modules/document/hooks/use-document-types'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import type { Employee } from '@/modules/hr/types/employee'
import type { MultiPickerOption } from '@/shared/ui/multi-picker'
import type { ConditionFieldDef } from '../config/condition-fields'

/**
 * Danh sách giá trị chọn được của từng ô điều kiện.
 *
 * Gom vào một hook để bộ dựng không phải biết ô nào lấy dữ liệu từ phân hệ nào.
 * Ba danh mục ở đây đều nhỏ và dùng chung khắp app nên đã nằm sẵn trong cache
 * của TanStack Query — mở bảng khai bước không sinh thêm lượt gọi mạng nào.
 */
export function useConditionChoices(employees: Employee[]) {
  const docTypes = useActiveDocumentTypes()
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })

  return useCallback(
    (field: ConditionFieldDef): MultiPickerOption[] => {
      switch (field.source) {
        case 'level':
          return (field.choices ?? []).map((item) => ({ id: item.value, label: item.label }))
        case 'doc_type':
          return docTypes.map((item) => ({ id: item.id, label: item.name, hint: item.code }))
        case 'company':
          return (companies?.items ?? []).map((item) => ({
            id: item.id,
            label: item.name,
            hint: item.code,
          }))
        case 'department':
          return (departments?.items ?? [])
            .filter((item) => item.is_active)
            .map((item) => ({ id: item.id, label: item.name, hint: item.code }))
        case 'employee':
          return employees.map((item) => ({
            id: item.id,
            label: item.full_name,
            hint: item.code,
          }))
      }
    },
    [companies?.items, departments?.items, docTypes, employees],
  )
}
