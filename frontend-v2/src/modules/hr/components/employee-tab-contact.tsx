import { Card } from '@/shared/ui/card'
import { FormSection } from '@/shared/ui/form-section'
import {
  EmployeeTextField,
  SensitiveFieldsNotice,
} from './employee-form-fields'
import { EmployeePeopleEditor } from './employee-people-editor'
import {
  CONTACT_COLUMNS,
  createEmptyContactRow,
  toContactPayload,
} from '../config/employee-contact-columns'
import {
  useEmployeeContacts,
  useSaveEmployeeContacts,
} from '../hooks/use-employee-profile'
import type { EmployeeContact } from '../types/employee'

interface EmployeeTabContactProps {
  employeeId: number
  canWrite: boolean
  canReadSensitive: boolean
}

/**
 * Tab «Liên hệ & Ngân hàng» — nhóm 3 (địa chỉ) + nhóm 4 (ngân hàng) + bảng
 * người báo tin.
 *
 * Cả ba khối đều thuộc nhóm NHẠY CẢM, nên thiếu quyền thì tab này gần như trống
 * — phải nói ra bằng chữ, không để người dùng đọc mấy ô rỗng rồi kết luận nhầm.
 */
export function EmployeeTabContact({
  employeeId,
  canWrite,
  canReadSensitive,
}: EmployeeTabContactProps) {
  //  ⚠️ `enabled` bắt buộc: cửa `/contacts` trả 403 khi thiếu quyền, cứ mount
  //  là gọi thì tab hiện trạng thái lỗi thay vì câu giải thích.
  const contacts = useEmployeeContacts(employeeId, canReadSensitive)
  const saveContacts = useSaveEmployeeContacts(employeeId)
  const lockedField = !canWrite || !canReadSensitive

  return (
    <div className="flex flex-col gap-5">
      {!canReadSensitive && <SensitiveFieldsNotice />}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="gap-4 p-5">
          <FormSection title="Liên hệ">
            {/*  «Email công việc» đã dời sang tab Chung (đại ca chốt 23/09/2026) —
                 nó là email ĐĂNG NHẬP, đứng cạnh Trạng thái hồ sơ, xem ghi chú ở đó. */}
            <EmployeeTextField
              name="phone"
              label="Số điện thoại"
              type="tel"
              disabled={!canWrite}
            />
            {/*  MỘT trường chữ gộp, cố ý không tách tỉnh/phường như HrOnline:
                 phiếu giấy của công ty cũng ghi một dòng, mà tách ba ô thì phải
                 nuôi thêm danh mục địa giới — thứ vừa đổi cả nước năm 2025. */}
            <EmployeeTextField
              name="permanent_address"
              label="Địa chỉ thường trú"
              disabled={lockedField}
            />
            <EmployeeTextField
              name="current_address"
              label="Địa chỉ hiện nay (tạm trú)"
              disabled={lockedField}
            />
          </FormSection>
        </Card>

        <Card className="gap-4 p-5">
          <FormSection title="Ngân hàng nhận lương">
            <EmployeeTextField
              name="bank_account_no"
              label="Số tài khoản"
              disabled={lockedField}
            />
            <EmployeeTextField
              name="bank_account_name"
              label="Tên chủ tài khoản"
              disabled={lockedField}
            />
            <EmployeeTextField name="bank_name" label="Ngân hàng" disabled={lockedField} />
            <EmployeeTextField name="bank_branch" label="Chi nhánh" disabled={lockedField} />
          </FormSection>
        </Card>
      </div>

      {canReadSensitive && (
        <EmployeePeopleEditor<EmployeeContact>
          title="Người báo tin trong trường hợp cần thiết"
          description="Người thân để liên hệ khi cần. Có thể khai nhiều người."
          columns={CONTACT_COLUMNS}
          rows={contacts.data}
          isLoading={contacts.isLoading}
          emptyRow={createEmptyContactRow}
          canWrite={canWrite}
          isSaving={saveContacts.isPending}
          onSave={(rows) => saveContacts.mutate(toContactPayload(rows))}
        />
      )}
    </div>
  )
}
