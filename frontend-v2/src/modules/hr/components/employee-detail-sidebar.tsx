import { Briefcase, Building2, Cake, Clock, Factory, PartyPopper, UserCog } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'
import type { EmployeeDetail } from '../types/employee'
import { computeEmployeeMilestones, formatTenure } from '../utils/employee-milestones'

interface EmployeeDetailSidebarProps {
  employee: EmployeeDetail
  /** Ảnh đại diện (đã gắn sẵn quyền đổi ảnh ở trang cha). */
  avatar: ReactNode
  /** Mốc «hôm nay» — tiêm vào để test không phụ thuộc đồng hồ máy. */
  today?: Date
  className?: string
}

/**
 * Thanh bên PHẢI của màn chi tiết nhân sự (duoc-CR-708) — học khung form ERPNext:
 * ảnh vuông bo góc, tên + mã, vài dòng nhận diện, mốc sinh nhật / kỷ niệm làm việc,
 * lần sửa cuối. Không phải thẻ: nằm chung mặt phẳng với form, ngăn bằng đường kẻ dọc
 * (trang cha truyền `xl:border-l`).
 *
 * Chỉ ĐỌC: mọi ô sửa vẫn nằm trong các tab. Dòng nào chưa có dữ liệu thì ẩn hẳn,
 * riêng «Quản lý trực tiếp» luôn hiện vì «Chưa gán» là thông tin bộ máy duyệt cần
 * (đơn sẽ lùi về trưởng bộ phận).
 */
export function EmployeeDetailSidebar({
  employee,
  avatar,
  today = new Date(),
  className,
}: EmployeeDetailSidebarProps) {
  const { isBirthday, anniversaryYears, tenure } = computeEmployeeMilestones(
    employee.date_of_birth,
    employee.hire_date,
    today,
  )

  return (
    //  `aside` giữ đường kẻ dọc chạy hết chiều cao cột; phần NỘI DUNG bên trong mới dính.
    <aside className={className}>
      <div
        className={cn(
          //  Dưới `xl`: dải ngang gọn phía trên tab (ảnh trái, chữ 2 cột bên phải, bỏ biểu
          //  tượng và dòng «Cập nhật») — bản dọc đo được ~700px ở khổ 390px, đẩy dải tab
          //  xuống dưới nếp gấp. Từ `xl`: cột dọc bên phải như thanh bên ERPNext, DÍNH ngay
          //  dưới cụm tiêu đề + tab (trang cha ghi chiều cao cụm đó vào `--sticky-head-h`).
          'flex flex-wrap items-start gap-4 px-4 py-4 sm:px-6',
          'xl:sticky xl:top-[var(--sticky-head-h,0px)] xl:flex-col xl:flex-nowrap xl:px-5 xl:py-5',
        )}
      >
        <div className="space-y-3">
          {avatar}
          {/*  Tên + mã dưới ảnh như ERPNext. Tên chỉ hiện từ `xl` (dưới đó hàng tiêu đề ngay
             trên đã có tên); mã hiện ở mọi khổ. */}
          <div>
            <p className="font-semibold break-words max-xl:hidden">{employee.full_name}</p>
            <p className="font-mono text-sm text-muted-foreground">{employee.code}</p>
          </div>
        </div>

        <div className="min-w-0 flex-1 space-y-3 xl:w-full xl:space-y-4 xl:border-t xl:pt-4">
          <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-sm xl:grid-cols-1">
            {employee.position && (
              <SidebarRow icon={Briefcase} label="Chức vụ">
                {employee.position}
              </SidebarRow>
            )}
            {employee.department_name && (
              <SidebarRow icon={Building2} label="Phòng ban">
                {employee.department_name}
              </SidebarRow>
            )}
            <SidebarRow icon={UserCog} label="Quản lý trực tiếp" wide>
              {employee.direct_manager_name || (
                <span className="text-muted-foreground">Chưa gán</span>
              )}
            </SidebarRow>
            {employee.company_name && (
              <SidebarRow icon={Factory} label="Công ty" wide>
                {employee.company_name}
              </SidebarRow>
            )}
          </div>

          {(employee.hire_date || isBirthday || anniversaryYears > 0) && (
            <div className="space-y-2 border-t pt-3 text-sm">
              {employee.hire_date && (
                <SidebarRow icon={Clock} label="Vào làm">
                  {formatDate(employee.hire_date)}
                  {tenure && (
                    <span className="text-muted-foreground"> · {formatTenure(tenure)}</span>
                  )}
                </SidebarRow>
              )}
              {isBirthday && (
                <p className="flex items-center gap-2 font-medium text-success">
                  <Cake className="size-4 shrink-0" />
                  Sinh nhật hôm nay
                </p>
              )}
              {anniversaryYears > 0 && (
                <p className="flex items-center gap-2 font-medium text-success">
                  <PartyPopper className="size-4 shrink-0" />
                  Tròn {anniversaryYears} năm làm việc
                </p>
              )}
            </div>
          )}

          {employee.updated_at && (
            <p className="border-t pt-3 text-xs text-muted-foreground max-xl:hidden">
              Cập nhật lần cuối {formatDateTime(employee.updated_at)}
            </p>
          )}
        </div>
      </div>
    </aside>
  )
}

function SidebarRow({
  icon: Icon,
  label,
  wide = false,
  children,
}: {
  icon: LucideIcon
  label: string
  /** Chiếm cả hàng ở lưới 2 cột của khổ hẹp (giá trị dài như tên pháp nhân). */
  wide?: boolean
  children: ReactNode
}) {
  return (
    <div className={cn('flex items-start gap-2', wide && 'max-xl:col-span-2')}>
      <Icon aria-hidden className="mt-0.5 size-4 shrink-0 text-muted-foreground max-xl:hidden" />
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="break-words">{children}</p>
      </div>
    </div>
  )
}
