import { useFormContext } from 'react-hook-form'

import { usePermission } from '@/core/authorization/use-permission'
import { Card } from '@/shared/ui/card'
import { FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { FormSection } from '@/shared/ui/form-section'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { ActiveStatusSelect } from './active-status-select'
import {
  EmployeeCodeSelect,
  EmployeeDateField,
  EmployeeNumberField,
  EmployeeTextField,
  SensitiveFieldsNotice,
} from './employee-form-fields'
import { LookupSelect } from './lookup-select'
import { useJobPositions } from '../hooks/use-job-positions'
import type { EmployeeProfileFormValues } from '../schemas/employee-schema'
import { employeeStatusOptions, type EmployeeDetail } from '../types/employee'
import {
  EDUCATION_LEVEL_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  JOB_LEVEL_OPTIONS,
  MARITAL_MARRIED,
  MARITAL_STATUS_OPTIONS,
} from '../types/employee-codes'
import { EMPLOYEE_GENDER_OPTIONS } from '../types/employee'

interface EmployeeTabGeneralProps {
  employee: EmployeeDetail
  canWrite: boolean
  canReadSensitive: boolean
  departments: { id: number; name: string }[]
  /** Danh bạ để chọn NGƯỜI QUẢN LÝ TRỰC TIẾP. */
  colleagues: { id: number; label: string }[]
}

/** Tab «Chung» — nhóm 1 (cá nhân) + nhóm 2 (công việc). */
export function EmployeeTabGeneral({
  employee,
  canWrite,
  canReadSensitive,
  departments,
  colleagues,
}: EmployeeTabGeneralProps) {
  const form = useFormContext<EmployeeProfileFormValues>()
  const disabled = !canWrite
  //  Theo dõi ô hôn nhân để ẩn/hiện ô «Số con» — xem ghi chú tại chỗ dùng.
  const maritalStatus = form.watch('marital_status')

  //  ⚠️ Danh mục Chức vụ là dữ liệu của MÀN KHÁC, nên phải tự tắt khi thiếu
  //  quyền: trên hệ đang chạy, vai trò cũ KHÔNG tự có khóa mới (D-018), và cứ
  //  mount là gọi thì người dùng ăn một toast 403 ngay lúc mở hồ sơ. Tắt rồi
  //  thì ô chọn vẫn hiện đúng chức vụ hiện tại nhờ `fallbackLabel`.
  const { can } = usePermission()
  const { data: positions } = useJobPositions(can('job_position', 'read'))
  const jobPositions = (positions?.items ?? []).map((p) => ({ id: p.id, label: p.name }))

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <Card className="gap-4 p-5">
        <FormSection title="Thông tin cá nhân">
          {/* Ngày sinh nằm trong nhóm nhạy cảm → cảnh báo ngay đầu khối. */}
          {!canReadSensitive && <SensitiveFieldsNotice />}

          <EmployeeTextField
            name="code"
            label="Mã NV"
            // Mã dùng khắp hệ — đổi sau khi tạo sẽ vỡ tham chiếu.
            disabled
          />
          <EmployeeTextField name="full_name" label="Họ tên" disabled={disabled} />

          <FormField
            control={form.control}
            name="gender"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Giới tính</FormLabel>
                <Select
                  onValueChange={(v) => field.onChange(Number(v))}
                  value={String(field.value)}
                  disabled={disabled}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EMPLOYEE_GENDER_OPTIONS.map((item) => (
                      <SelectItem key={item.value} value={String(item.value)}>
                        {item.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormDescription>
                  Dùng để lọc loại nghỉ theo giới, ví dụ nghỉ thai sản.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <EmployeeDateField
            name="date_of_birth"
            label="Ngày sinh"
            disabled={disabled || !canReadSensitive}
          />

          {/*  NƠI SINH chiếm cả hàng: thực tế người ta nhập nguyên một địa chỉ
               ("Xã …, Huyện …, Tỉnh …") chứ không nhập mỗi tên tỉnh, nhét vào
               nửa hàng thì chữ bị cắt. Nó cũng là ô lẻ của nhóm khai sinh — nhờ
               vậy các cặp bên dưới mới đứng đúng đôi với nhau. */}
          <div className="sm:col-span-2">
            <EmployeeTextField name="place_of_birth" label="Nơi sinh" disabled={disabled} />
          </div>

          <EmployeeTextField name="ethnicity" label="Dân tộc" disabled={disabled} />
          <EmployeeTextField name="religion" label="Tôn giáo" disabled={disabled} />

          <EmployeeCodeSelect
            name="marital_status"
            label="Tình trạng hôn nhân"
            options={MARITAL_STATUS_OPTIONS}
            disabled={disabled}
          />
          {/*  Ô «Số con» CHỈ hiện khi đã khai «Có gia đình» (khách chốt
               08/09/2026 — trước đó luật ngược lại: ẩn khi *Độc thân*).

               ⚠️ Ẩn/hiện chỉ là chuyện HIỂN THỊ — giá trị vẫn nằm trong form và
               vẫn gửi lên, đúng quy ước đã dùng ở màn Loại nghỉ (§11.1). Cố ý
               KHÔNG tự xóa về 0 khi người dùng đổi ô hôn nhân: tự ý xóa dữ liệu
               người ta đã nhập thì nguy hiểm hơn nhiều so với việc giữ một con
               số không hiện ra. Hệ quả kèm theo: hồ sơ *Ly hôn* có sẵn số con
               vẫn giữ nguyên con số đó, chỉ là không sửa được ở màn này.

               ⚠️ Ô rỗng thay chỗ khi ẩn: lưới là 2 cột và các ô xếp lần lượt,
               nên bỏ trống một ô là mọi cặp phía dưới lệch sang nửa hàng bên
               kia — đúng cảnh «Số con» từng nằm dưới «Tôn giáo» thay vì đứng
               cạnh «Tình trạng hôn nhân». */}
          {maritalStatus === MARITAL_MARRIED ? (
            <EmployeeNumberField name="children_count" label="Số con" disabled={disabled} />
          ) : (
            <div aria-hidden className="hidden sm:block" />
          )}

          <EmployeeCodeSelect
            name="education_level"
            label="Trình độ học vấn"
            options={EDUCATION_LEVEL_OPTIONS}
            disabled={disabled}
          />
          <EmployeeTextField name="major" label="Chuyên ngành" disabled={disabled} />

          <EmployeeTextField
            name="tax_code"
            label="Mã số thuế cá nhân"
            disabled={disabled || !canReadSensitive}
          />
          <EmployeeTextField
            name="personal_email"
            label="Email cá nhân"
            type="email"
            description="Email riêng, khác với email công việc ở tab Liên hệ."
            disabled={disabled}
          />
        </FormSection>
      </Card>

      <Card className="gap-4 p-5">
        <FormSection title="Công việc">
          {/*  CÔNG TY — CHỈ XEM. Đổi pháp nhân là đổi tập dữ liệu người đó đọc
               được, và phải kèm luật "phòng ban đang gán có thuộc pháp nhân mới
               không". Bày ô chọn ra mà chưa có luật đó là mở đường lệch dữ liệu.
               Dùng `ReadOnlyValue` chứ KHÔNG `<Input disabled>`: ô mờ thì không
               bôi đen, không copy được tên pháp nhân. */}
          <FormItem>
            <FormLabel>Công ty</FormLabel>
            <ReadOnlyValue>{employee.company_name || '— Chưa gán công ty —'}</ReadOnlyValue>
            <FormDescription>Pháp nhân của nhân sự. Đổi pháp nhân làm ở màn Công ty.</FormDescription>
          </FormItem>

          <FormField
            control={form.control}
            name="department_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Phòng ban</FormLabel>
                <LookupSelect
                  value={field.value}
                  onChange={field.onChange}
                  disabled={disabled}
                  placeholder="Chọn phòng ban"
                  emptyLabel="— Chưa gán phòng ban —"
                  fallbackLabel={employee.department_name ?? ''}
                  items={departments.map((d) => ({ id: d.id, label: d.name }))}
                />
                <FormMessage />
              </FormItem>
            )}
          />

          {/*  VỊ TRÍ / CHỨC VỤ — ô CHỌN từ danh mục kể từ duoc-CR-320, không
               còn gõ tay. Chữ tự do làm cùng một chức vụ hiện ra bốn cách viết
               trên bản in, tệp Excel và hồ sơ mà trợ lý AI đọc.

               ⚠️ `fallbackLabel` là bắt buộc, không phải cho đẹp: hồ sơ cũ chưa
               map (hoặc đang giữ một chức vụ vừa bị cho ngừng dùng) không có
               dòng nào trong danh sách, và thiếu nhãn dự phòng thì ô hiện trống
               — người đọc hiểu thành «chưa khai chức vụ» rồi lưu đè lên. */}
          <FormField
            control={form.control}
            name="position_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Vị trí / Chức vụ</FormLabel>
                <LookupSelect
                  value={field.value}
                  onChange={field.onChange}
                  disabled={disabled}
                  placeholder="Chọn chức vụ"
                  emptyLabel="— Chưa gán chức vụ —"
                  fallbackLabel={employee.position ?? ''}
                  items={jobPositions}
                />
                <FormDescription>
                  Chức danh in trên phiếu — không phải phân quyền. Thêm chức vụ mới ở
                  danh mục Chức vụ.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          {/*  NGƯỜI QUẢN LÝ TRỰC TIẾP — dữ liệu mà bộ máy duyệt đọc để tìm người
               ký, không phải trường hiển thị cho đẹp. Sai ô này thì đơn từ chạy
               sai đường mà không màn nào báo. Chưa gán thì luồng lùi về trưởng
               bộ phận nên đơn không kẹt. */}
          <FormField
            control={form.control}
            name="manager_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Người quản lý trực tiếp</FormLabel>
                <LookupSelect
                  value={field.value}
                  onChange={field.onChange}
                  disabled={disabled}
                  placeholder="Chọn người quản lý"
                  emptyLabel="— Chưa gán —"
                  fallbackLabel={employee.direct_manager_name ?? ''}
                  items={colleagues}
                />
                <FormDescription>
                  Người ký duyệt đơn từ của nhân viên này. Bỏ trống thì đơn chuyển cho
                  trưởng bộ phận.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <EmployeeCodeSelect
            name="employment_type"
            label="Hình thức nhân viên"
            options={EMPLOYMENT_TYPE_OPTIONS}
            disabled={disabled}
          />
          <EmployeeCodeSelect
            name="job_level"
            label="Cấp bậc"
            options={JOB_LEVEL_OPTIONS}
            disabled={disabled}
          />
          <EmployeeTextField name="work_location" label="Nơi làm việc" disabled={disabled} />

          <FormField
            control={form.control}
            name="status"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tình trạng làm việc</FormLabel>
                <Select onValueChange={field.onChange} value={field.value} disabled={disabled}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {employeeStatusOptions(field.value).map((item) => (
                      <SelectItem key={item.value} value={item.value}>
                        {item.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          {/*  NGÀY VÀO LÀM — mốc THÂM NIÊN. Cột có trong bảng từ 03/09/2026
               nhưng không ô nào khai được cho tới 07/09, nên thâm niên của cả
               công ty đang tính bằng 0. */}
          <EmployeeDateField
            name="hire_date"
            label="Ngày vào làm"
            description="Dùng để tính thâm niên và số ngày phép được cộng thêm."
            disabled={disabled}
          />
          <EmployeeDateField
            name="resign_date"
            label="Ngày nghỉ việc"
            description="Điền ngày này thì nhớ đổi cả ô Tình trạng làm việc."
            disabled={disabled}
          />

          <FormField
            control={form.control}
            name="is_active"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Trạng thái hồ sơ</FormLabel>
                <ActiveStatusSelect
                  value={field.value}
                  onChange={field.onChange}
                  disabled={disabled}
                />
                <FormMessage />
              </FormItem>
            )}
          />
        </FormSection>
      </Card>
    </div>
  )
}
