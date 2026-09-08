import { Card } from '@/shared/ui/card'
import { FormSection } from '@/shared/ui/form-section'
import { SectionHeading } from '@/shared/ui/section-heading'
import { EmployeeDateField, EmployeeTextField, SensitiveFieldsNotice } from './employee-form-fields'
import { EmployeeIdCardUploader } from './employee-id-card-uploader'
import { EmployeePeopleEditor, type PeopleColumn } from './employee-people-editor'
import {
  useEmployeeFamilies,
  useSaveEmployeeFamilies,
  useUploadIdImage,
} from '../hooks/use-employee-profile'
import type { EmployeeDetail, EmployeeFamily } from '../types/employee'

const FAMILY_COLUMNS: PeopleColumn<EmployeeFamily>[] = [
  { key: 'full_name', label: 'Họ tên', kind: 'text', span: 3 },
  //  Cùng bộ mã với bảng người báo tin, nhưng gốc quy chiếu là CHỦ HỘ —
  //  hồ sơ BHXH hỏi vậy, và nhân viên không phải lúc nào cũng là chủ hộ.
  { key: 'relation', label: 'Quan hệ với chủ hộ', kind: 'relation', span: 2, placeholder: '— Chọn quan hệ —' },
  { key: 'gender', label: 'Giới tính', kind: 'gender', span: 2 },
  { key: 'date_of_birth', label: 'Ngày sinh', kind: 'date', span: 2 },
  { key: 'id_number', label: 'Số CCCD', kind: 'text', span: 2 },
]

interface EmployeeTabDocumentsProps {
  employee: EmployeeDetail
  canWrite: boolean
  canReadSensitive: boolean
}

/**
 * Tab «Giấy tờ & BHXH» — nhóm 5, hai ảnh CCCD, và bảng thành viên hộ gia đình.
 *
 * Gần như toàn bộ tab nằm trong nhóm NHẠY CẢM. Ngoại lệ duy nhất là **nơi khám
 * chữa bệnh BHYT**: hành chính hỏi nhau hằng ngày để làm thủ tục, giấu nó chỉ
 * đẻ ra một vòng hỏi qua Zalo.
 */
export function EmployeeTabDocuments({
  employee,
  canWrite,
  canReadSensitive,
}: EmployeeTabDocumentsProps) {
  const families = useEmployeeFamilies(employee.id, canReadSensitive)
  const saveFamilies = useSaveEmployeeFamilies(employee.id)
  const uploadIdImage = useUploadIdImage(employee.id)
  const lockedField = !canWrite || !canReadSensitive

  return (
    <div className="flex flex-col gap-5">
      {!canReadSensitive && <SensitiveFieldsNotice />}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="gap-4 p-5">
          <FormSection title="Căn cước công dân">
            <EmployeeTextField name="id_number" label="Số CCCD" disabled={lockedField} />
            <EmployeeDateField name="id_issue_date" label="Ngày cấp" disabled={lockedField} />
            <EmployeeTextField name="id_issue_place" label="Nơi cấp" disabled={lockedField} />
            <EmployeeDateField name="id_expiry_date" label="Ngày hết hạn" disabled={lockedField} />
          </FormSection>

          {canReadSensitive && (
            <div className="flex flex-col gap-3 border-t pt-4">
              <SectionHeading>Ảnh CCCD</SectionHeading>
              <EmployeeIdCardUploader
                frontUrl={employee.id_front_image}
                backUrl={employee.id_back_image}
                canWrite={canWrite}
                isUploading={uploadIdImage.isPending}
                onUpload={(side, file) => uploadIdImage.mutate({ side, file })}
              />
            </div>
          )}
        </Card>

        <Card className="gap-4 p-5">
          <FormSection title="Bảo hiểm">
            {/*  CHỈ lưu số phục vụ hồ sơ. Nghiệp vụ báo tăng/giảm BHXH nằm ngoài
                 phạm vi (NS4 đã quyết không lấy) — đừng dựng luồng nào bám vào
                 ô này. Tình trạng sổ (dùng sổ cũ / cấp mới) không cần ô riêng:
                 có số nghĩa là dùng sổ cũ, rỗng nghĩa là chưa có. */}
            <EmployeeTextField
              name="social_insurance_no"
              label="Số sổ BHXH"
              description="Chưa có sổ thì để trống."
              disabled={lockedField}
            />
            <EmployeeTextField
              name="health_care_place"
              label="Nơi đăng ký KCB BHYT"
              placeholder="Tên bệnh viện"
              disabled={!canWrite}
            />
            <EmployeeTextField
              name="health_care_code"
              label="Mã nơi KCB BHYT"
              disabled={!canWrite}
            />
          </FormSection>
        </Card>
      </div>

      {canReadSensitive && (
        <EmployeePeopleEditor<EmployeeFamily>
          title="Thành viên hộ gia đình"
          description="Dùng cho hồ sơ bảo hiểm xã hội. Quan hệ ghi theo chủ hộ."
          columns={FAMILY_COLUMNS}
          rows={families.data}
          isLoading={families.isLoading}
          emptyRow={() => ({
            id: 0,
            full_name: '',
            relation: 0,   // 0 = chưa khai, xem RELATION_OPTIONS
            gender: 0,
            date_of_birth: null,
            phone: '',
            id_number: '',
            sort_order: 0,
          })}
          canWrite={canWrite}
          isSaving={saveFamilies.isPending}
          onSave={(rows) =>
            saveFamilies.mutate(
              rows.map(({ full_name, relation, gender, date_of_birth, phone, id_number }) => ({
                full_name,
                relation,
                gender,
                date_of_birth,
                phone,
                id_number,
              })),
            )
          }
        />
      )}
    </div>
  )
}
