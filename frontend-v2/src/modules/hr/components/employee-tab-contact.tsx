import { Card } from '@/shared/ui/card'
import { FormSection } from '@/shared/ui/form-section'
import {
  EmployeeTextField,
  SensitiveFieldsNotice,
} from './employee-form-fields'
import { EmployeePeopleEditor, type PeopleColumn } from './employee-people-editor'
import {
  useEmployeeContacts,
  useSaveEmployeeContacts,
} from '../hooks/use-employee-profile'
import type { EmployeeContact } from '../types/employee'

/** Cột của bảng «Người báo tin» — khai ở tầng module, không dựng lại mỗi render. */
const CONTACT_COLUMNS: PeopleColumn<EmployeeContact>[] = [
  { key: 'full_name', label: 'Họ tên', kind: 'text', span: 3 },
  //  Ô CHỌN, không gõ tay (khách chốt 08/09/2026). Quan hệ với NHÂN VIÊN.
  { key: 'relation', label: 'Quan hệ', kind: 'relation', span: 2, placeholder: '— Chọn quan hệ —' },
  { key: 'phone', label: 'Điện thoại', kind: 'phone', span: 2 },
  { key: 'address', label: 'Địa chỉ', kind: 'text', span: 4 },
]

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
            <EmployeeTextField
              name="email"
              label="Email công việc"
              type="email"
              description="Cũng dùng làm tên đăng nhập. Đổi ở đây không tự đổi tài khoản đã cấp."
              disabled={!canWrite}
            />
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
          emptyRow={() => ({
            id: 0,
            full_name: '',
            relation: 0,   // 0 = chưa khai, xem RELATION_OPTIONS
            address: '',
            phone: '',
            sort_order: 0,
          })}
          canWrite={canWrite}
          isSaving={saveContacts.isPending}
          onSave={(rows) =>
            saveContacts.mutate(
              rows.map(({ full_name, relation, address, phone }) => ({
                full_name,
                relation,
                address,
                phone,
              })),
            )
          }
        />
      )}
    </div>
  )
}
