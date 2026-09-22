import { ExternalLink, UserCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card } from '@/shared/ui/card'
import type { Employee } from '@/modules/hr/types/employee'
import { SealInfoRow } from './seal-info-row'
import { SealSectionHeader } from './seal-section-header'

interface SealClerkEmployeeCardProps {
  employeeId: number
  /** Tên/mã lấy từ chính dòng phân công — dùng khi chưa/không đọc được hồ sơ nhân sự. */
  fallbackName?: string | null
  fallbackCode?: string | null
  employee?: Employee
  /** Có quyền `employee.read` thì mới dựng liên kết sang hồ sơ. */
  canViewEmployee: boolean
}

/**
 * Thẻ **THÔNG TIN NHÂN SỰ** của trang chi tiết phân công văn thư — đứng ở CỘT
 * PHẢI (dời 22/09/2026, trước đó chiếm nửa trên cột chính).
 *
 * Đây là khối CHỈ ĐỌC, mượn từ hồ sơ nhân sự: người ta mở trang này để **sửa
 * phân công**, thông tin nhân sự chỉ để đối chiếu "đúng người chưa". Để nó nằm
 * trên cùng cột chính thì phần việc thật bị đẩy xuống dưới màn hình.
 *
 * ⚠️ Xếp kiểu NHÃN TRÁI — GIÁ TRỊ PHẢI (`SealInfoRow`) thay cho bảy ô có viền +
 * biểu tượng của bản cũ: trong cột 380px, bảy ô xếp chồng cao hơn 400px, tức
 * đẩy Trao đổi và Lịch sử ra khỏi tầm nhìn. Cùng khuôn với hai thẻ ở chi tiết
 * phiếu đóng dấu nên hai màn đọc như một.
 */
export function SealClerkEmployeeCard({
  employeeId,
  fallbackName,
  fallbackCode,
  employee,
  canViewEmployee,
}: SealClerkEmployeeCardProps) {
  const mail = employee?.email
  const phone = employee?.phone

  return (
    <Card className="flex flex-col gap-3 p-5">
      <SealSectionHeader
        icon={UserCheck}
        title="Thông tin nhân sự"
        extra={
          employeeId > 0 && canViewEmployee ? (
            <Link
              to={appRoutes.hr.employeeDetail(employeeId)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary transition-colors hover:underline"
            >
              Xem hồ sơ
              <ExternalLink className="size-3" />
            </Link>
          ) : undefined
        }
      />

      <SealInfoRow label="Mã NV">{employee?.code || fallbackCode || '—'}</SealInfoRow>
      <SealInfoRow label="Họ và tên">{employee?.full_name || fallbackName || '—'}</SealInfoRow>

      <SealInfoRow label="Email">
        {mail ? (
          <a href={`mailto:${mail}`} className="text-primary hover:underline">
            {mail}
          </a>
        ) : (
          '—'
        )}
      </SealInfoRow>

      <SealInfoRow label="Điện thoại">
        {phone ? (
          <a href={`tel:${phone}`} className="tabular-nums text-primary hover:underline">
            {phone}
          </a>
        ) : (
          '—'
        )}
      </SealInfoRow>

      <SealInfoRow label="Phòng ban">{employee?.department_name || '—'}</SealInfoRow>
      <SealInfoRow label="Chức danh">{employee?.position || '—'}</SealInfoRow>

      {/*  Hai dòng cuối CHỈ hiện khi có dữ liệu: pháp nhân trực thuộc của nhân
          sự khác hẳn "công ty được giao đóng dấu" ở cột trái, bày dấu gạch
          trống ở đây chỉ tổ làm người đọc tưởng phân công bị thiếu. */}
      {employee?.company_name && (
        <SealInfoRow label="Pháp nhân">{employee.company_name}</SealInfoRow>
      )}
      {employee?.status_label && (
        <SealInfoRow label="Tình trạng">{employee.status_label}</SealInfoRow>
      )}
    </Card>
  )
}
