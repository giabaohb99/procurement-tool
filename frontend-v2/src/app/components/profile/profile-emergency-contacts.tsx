import { useRef } from 'react'

import { EmployeePeopleEditor } from '@/modules/hr/components/employee-people-editor'
import {
  CONTACT_COLUMNS,
  createEmptyContactRow,
  toContactPayload,
} from '@/modules/hr/config/employee-contact-columns'
import { useMyContacts, useSaveMyContacts } from '@/modules/hr/hooks/use-my-contact'
import type { EmployeeContact } from '@/modules/hr/types/employee'

interface ProfileEmergencyContactsProps {
  employeeId: number
}

/**
 * «Người báo tin trong trường hợp cần thiết» của CHÍNH MÌNH (bao-CR-508).
 *
 * Dùng lại nguyên `EmployeePeopleEditor` của hồ sơ nhân sự — cùng bộ cột
 * (`CONTACT_COLUMNS`), cùng trần 30 dòng hiện TRƯỚC khi gõ, cùng chốt chặn phím
 * Enter. Chỉ khác cửa API: `/api/employees/me/contacts`, không cần khóa
 * `employee.write` hay `employee_sensitive.read`.
 *
 * ⚠️ Chặn bấm đúp ở đây bằng `useRef`: nút «Lưu danh sách» của bảng chung chỉ
 * có `disabled={isSaving}` — state React, trễ một nhịp render.
 */
export function ProfileEmergencyContacts({ employeeId }: ProfileEmergencyContactsProps) {
  const contacts = useMyContacts(employeeId > 0)
  const saveContacts = useSaveMyContacts(employeeId)
  const savingRef = useRef(false)

  function handleSave(rows: EmployeeContact[]) {
    if (savingRef.current) return
    savingRef.current = true
    saveContacts.mutate(toContactPayload(rows), {
      onSettled: () => {
        savingRef.current = false
      },
    })
  }

  return (
    <EmployeePeopleEditor<EmployeeContact>
      title="Người báo tin trong trường hợp cần thiết"
      description="Người thân để công ty liên hệ khi cần. Bạn tự thêm, sửa, xóa được; bấm «Lưu danh sách» để áp dụng."
      columns={CONTACT_COLUMNS}
      rows={contacts.data}
      isLoading={contacts.isLoading}
      emptyRow={createEmptyContactRow}
      canWrite
      isSaving={saveContacts.isPending}
      onSave={handleSave}
    />
  )
}
