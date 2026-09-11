import {
  Banknote,
  BriefcaseBusiness,
  Building2,
  Cake,
  CalendarCheck,
  CalendarX,
  CreditCard,
  GraduationCap,
  Heart,
  HeartPulse,
  Home,
  IdCard,
  Landmark,
  Mail,
  MapPin,
  Receipt,
  ShieldCheck,
  Signpost,
  UserRound,
  Users,
  type LucideIcon,
} from 'lucide-react'

import type { Employee } from '@/modules/hr/types/employee'
import { FormCard } from '@/shared/ui/form-card'
import { formatDate } from '@/shared/utils/format-date'
import { ProfileFieldRow } from './profile-field-row'

interface Field {
  icon: LucideIcon
  label: string
  value?: string
}

/** `0` chưa khai · `1` nam · `2` nữ — bộ mã số gõ tay, xem `hr/types/employee-codes.ts`. */
const GENDER_LABELS: Record<number, string> = { 1: 'Nam', 2: 'Nữ' }

/** Ngày `YYYY-MM-DD` → `dd/MM/yyyy`; rỗng/`null` trả chuỗi rỗng để hiện «Chưa cập nhật». */
function asDate(value?: string | null): string {
  return value ? formatDate(value) : ''
}

/**
 * HỒ SƠ NHÂN SỰ ĐẦY ĐỦ ở Trang cá nhân — sáu khối, CHỈ XEM.
 *
 * ⚠️ **Vì sao chỉ xem.** Mã nhân viên, phòng ban, vai trò… là dữ liệu gốc của
 * phân hệ Nhân sự; cho sửa ở hai nơi thì sớm muộn cũng lệch nhau. Đây là quyết
 * định có sẵn của trang, đợt này chỉ bổ sung thứ để ĐỌC chứ không mở cửa ghi.
 *
 * ⚠️ **KHÔNG dựng `SensitiveFieldsNotice` ở đây, và đó là chủ ý.** Ở màn hồ sơ
 * người khác, 15 trường nhạy cảm (ngày sinh · MST · địa chỉ nhà · ngân hàng ·
 * CCCD · BHXH) bị backend che thành chuỗi rỗng, nên phải có câu nhắc để người
 * đọc khỏi tưởng công ty chưa có số tài khoản của người đó. Còn ở đây là **hồ sơ
 * của chính mình**: nhánh `self` của `sensitive.can_read_sensitive` cho đọc đủ
 * mà không cần khóa `employee_sensitive`, nên ô rỗng ở đây đúng nghĩa là **chưa
 * ai nhập** — dựng câu nhắc vào là nói sai.
 *
 * ⚠️ Nhãn của bốn ô mã số (tình trạng hôn nhân · học vấn · loại hình · cấp bậc)
 * lấy từ `*_label` mà backend gửi kèm, **không tự tra bảng mã ở TS** — bộ mã số
 * của hồ sơ gõ tay ở `hr/types/employee-codes.ts` và rất dễ lệch với backend.
 */
export function ProfileHrDetails({ employee }: { employee: Employee }) {
  const personal: Field[] = [
    { icon: Cake, label: 'Ngày sinh', value: asDate(employee.date_of_birth) },
    { icon: MapPin, label: 'Nơi sinh', value: employee.place_of_birth },
    { icon: UserRound, label: 'Giới tính', value: GENDER_LABELS[employee.gender ?? 0] },
    { icon: Signpost, label: 'Dân tộc', value: employee.ethnicity },
    { icon: Heart, label: 'Tôn giáo', value: employee.religion },
    { icon: Users, label: 'Tình trạng hôn nhân', value: employee.marital_status_label },
    {
      icon: Users,
      label: 'Số con',
      //  `0` là một câu trả lời THẬT («chưa có con»), không phải «chưa nhập» —
      //  để rơi vào nhánh rỗng thì hồ sơ khai đủ lại hiện «Chưa cập nhật».
      value: employee.children_count === undefined ? '' : String(employee.children_count),
    },
    { icon: Mail, label: 'Email cá nhân', value: employee.personal_email },
    { icon: Receipt, label: 'Mã số thuế', value: employee.tax_code },
  ]

  const work: Field[] = [
    { icon: CalendarCheck, label: 'Ngày vào làm', value: asDate(employee.hire_date) },
    { icon: BriefcaseBusiness, label: 'Loại hình làm việc', value: employee.employment_type_label },
    { icon: ShieldCheck, label: 'Cấp bậc', value: employee.job_level_label },
    { icon: Building2, label: 'Nơi làm việc', value: employee.work_location },
    { icon: UserRound, label: 'Quản lý trực tiếp', value: employee.direct_manager_name },
    { icon: GraduationCap, label: 'Trình độ học vấn', value: employee.education_level_label },
    { icon: GraduationCap, label: 'Chuyên ngành', value: employee.major },
    //  Chỉ hiện khi CÓ: người đang làm mà thấy dòng «Ngày nghỉ việc — Chưa cập
    //  nhật» trong hồ sơ của chính mình thì đọc ra như một câu hỏi bỏ ngỏ.
    ...(employee.resign_date
      ? [{ icon: CalendarX, label: 'Ngày nghỉ việc', value: asDate(employee.resign_date) }]
      : []),
  ]

  const address: Field[] = [
    { icon: Home, label: 'Địa chỉ thường trú', value: employee.permanent_address },
    { icon: MapPin, label: 'Chỗ ở hiện tại', value: employee.current_address },
  ]

  const idCard: Field[] = [
    { icon: IdCard, label: 'Số CCCD / CMND', value: employee.id_number },
    { icon: CalendarCheck, label: 'Ngày cấp', value: asDate(employee.id_issue_date) },
    { icon: MapPin, label: 'Nơi cấp', value: employee.id_issue_place },
    { icon: CalendarX, label: 'Ngày hết hạn', value: asDate(employee.id_expiry_date) },
  ]

  const insurance: Field[] = [
    { icon: HeartPulse, label: 'Số BHXH', value: employee.social_insurance_no },
    { icon: HeartPulse, label: 'Nơi khám chữa bệnh', value: employee.health_care_place },
    { icon: CreditCard, label: 'Mã thẻ BHYT', value: employee.health_care_code },
  ]

  const bank: Field[] = [
    { icon: CreditCard, label: 'Số tài khoản', value: employee.bank_account_no },
    { icon: UserRound, label: 'Chủ tài khoản', value: employee.bank_account_name },
    { icon: Landmark, label: 'Ngân hàng', value: employee.bank_name },
    { icon: Building2, label: 'Chi nhánh', value: employee.bank_branch },
  ]

  //  ⚠️ Thứ tự XẾP THEO CẶP chứ không theo mạch đọc: lưới hai cột lấy chiều cao
  //  của thẻ CAO NHẤT trong mỗi hàng, nên ghép «Thông tin cá nhân» (9 dòng) với
  //  «Địa chỉ» (2 dòng) là chừa một lỗ trắng bảy dòng bên phải. Ghép thẻ dài với
  //  thẻ dài, ngắn với ngắn thì hai cột đi gần bằng nhau.
  //
  //  Tên thẻ lấy đúng tên `FormSection` mà phân hệ Nhân sự dùng cho cùng bộ
  //  trường ở màn chi tiết nhân sự — người vừa xem hồ sơ người khác rồi mở hồ sơ
  //  của mình không phải dò lại xem khối nào là khối nào.
  const groups: { title: string; icon: LucideIcon; fields: Field[] }[] = [
    { title: 'Thông tin cá nhân', icon: UserRound, fields: personal },
    { title: 'Công việc', icon: BriefcaseBusiness, fields: work },
    { title: 'Căn cước công dân', icon: IdCard, fields: idCard },
    { title: 'Ngân hàng nhận lương', icon: Banknote, fields: bank },
    { title: 'Bảo hiểm', icon: HeartPulse, fields: insurance },
    { title: 'Địa chỉ', icon: Home, fields: address },
  ]

  return (
    //  ⚠️ Khối này tự dựng LƯỚI RIÊNG chứ không nhét vào một cột của lưới phía
    //  trên: nhét vào thì cột trái có chín thẻ còn cột phải hai thẻ, và cả nửa
    //  phải màn hình trống từ giữa trang trở xuống.
    //
    //  `items-start` để mỗi thẻ giữ chiều cao của chính nó — thiếu nó thì thẻ
    //  ngắn bị kéo dãn bằng thẻ dài cùng hàng, thành một ô viền rỗng nửa dưới.
    <div className="grid items-start gap-4 lg:grid-cols-2">
      {groups.map((group) => (
        <FormCard
          key={group.title}
          title={group.title}
          icon={group.icon}
          iconClassName="text-muted-foreground"
        >
          {group.fields.map((field) => (
            <ProfileFieldRow key={field.label} {...field} />
          ))}
        </FormCard>
      ))}
    </div>
  )
}
