import { ArrowLeft, Globe, Home, Mail, Phone, Printer } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

import { useLeaveRequest } from '../hooks/use-leave'
import { LEAVE_SESSION, type LeaveRequest } from '../types/leave'

const DOTS = '..................................................'

const PRINT_STYLES = `
  @page {
    size: A4 portrait;
    margin: 0;
  }
  @media print {
    html, body {
      margin: 0 !important;
      padding: 0 !important;
      background: #fff !important;
    }
    .no-print,
    .tsqd-parent-container,
    [class*="tsqd"],
    [data-sonner-toaster] {
      display: none !important;
    }
    .a4-print-page {
      padding: 0 !important;
      background: transparent !important;
      min-height: 0 !important;
    }
    .a4-print-sheet {
      margin: 0 !important;
      padding: 20mm !important;
      box-shadow: none !important;
      border: none !important;
      width: 100% !important;
      min-height: 0 !important;
    }
  }
`

function getVietnameseWeekday(dateStr: string): string {
  const parts = dateStr.split('-').map(Number)
  if (parts.length !== 3 || parts.some(isNaN)) return ''
  const d = new Date(parts[0], parts[1] - 1, parts[2])
  if (isNaN(d.getTime())) return ''
  const day = d.getDay()
  switch (day) {
    case 0:
      return 'chủ nhật'
    case 1:
      return 'thứ hai'
    case 2:
      return 'thứ ba'
    case 3:
      return 'thứ tư'
    case 4:
      return 'thứ năm'
    case 5:
      return 'thứ sáu'
    case 6:
      return 'thứ bảy'
    default:
      return ''
  }
}

function formatDateVn(dateStr: string): string {
  if (!dateStr) return ''
  const parts = dateStr.split('T')[0].split('-')
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`
  }
  return dateStr
}

function parseDocDate(request: LeaveRequest) {
  const raw =
    request.decided_at ||
    request.submitted_at ||
    request.created_at ||
    request.from_date ||
    ''
  const d = raw ? new Date(raw) : new Date()
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = String(d.getFullYear())
  return { day, month, year }
}

function formatLeavePeriod(request: LeaveRequest): string {
  if (request.from_date && request.to_date && request.from_date === request.to_date) {
    const weekday = getVietnameseWeekday(request.from_date)
    let sessionExtra = ''
    if (request.from_session === LEAVE_SESSION.MORNING) {
      sessionExtra = ' (buổi sáng)'
    } else if (request.from_session === LEAVE_SESSION.AFTERNOON) {
      sessionExtra = ' (buổi chiều)'
    } else if (
      request.from_session === LEAVE_SESSION.HOURLY &&
      request.from_time &&
      request.to_time
    ) {
      sessionExtra = ` (${request.from_time.slice(0, 5)} - ${request.to_time.slice(0, 5)})`
    }
    return `${request.total_days} ngày${sessionExtra} ${weekday ? `${weekday} ` : ''}${formatDateVn(request.from_date)}`
  }
  if (request.from_date && request.to_date) {
    return `${request.total_days} ngày, từ ngày ${formatDateVn(request.from_date)} đến ngày ${formatDateVn(request.to_date)}`
  }
  return `${request.total_days} ngày`
}

export function LeaveRequestPrintPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const requestId = Number(id) || 0
  const { data: request, isLoading } = useLeaveRequest(requestId)

  return (
    <main className="a4-print-page min-h-[100dvh] bg-slate-200 p-6 no-print:pb-12">
      <style>{PRINT_STYLES}</style>

      {/* Thanh công cụ (ẩn khi in) */}
      <div className="no-print mx-auto mb-4 flex max-w-[210mm] items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button onClick={() => window.print()}>
            <Printer className="size-4" />
            In đơn / Lưu PDF
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              requestId > 0
                ? navigate(appRoutes.hr.leaveRequestDetail(requestId))
                : navigate(-1)
            }
          >
            <ArrowLeft className="size-4" />
            Quay lại
          </Button>
        </div>

        {request && (
          <span className="text-sm font-medium text-slate-700">
            {request.code || 'Đơn nghỉ phép'} · Khổ A4 chuẩn
          </span>
        )}
      </div>

      {isLoading || !request ? (
        <div className="mx-auto max-w-[210mm]">
          <Skeleton className="mb-4 h-10 w-48" />
          <Skeleton className="h-[297mm] w-full bg-white shadow-xl" />
        </div>
      ) : (
        <LeaveRequestPrintSheet request={request} />
      )}
    </main>
  )
}

function LeaveRequestPrintSheet({ request }: { request: LeaveRequest }) {
  const { day, month, year } = parseDocDate(request)

  // Phân loại loại nghỉ dựa vào danh sách dòng và loại chính
  const typeNames = [
    request.leave_type_name,
    ...(request.lines ?? []).map((l) => l.leave_type_name),
  ]
    .filter(Boolean)
    .map((s) => s!.toLowerCase())

  const isUnpaid = typeNames.some((t) => t.includes('không lương'))
  const isAnnual =
    typeNames.some((t) => t.includes('phép năm')) ||
    (!typeNames.some(
      (t) =>
        t.includes('không lương') ||
        t.includes('ốm') ||
        t.includes('chế độ') ||
        t.includes('thai sản'),
    ) &&
      request.total_days > 0)
  const isSick = typeNames.some((t) => t.includes('ốm'))
  const isStatutory = typeNames.some(
    (t) =>
      t.includes('chế độ') ||
      t.includes('thai sản') ||
      t.includes('cưới') ||
      t.includes('tang') ||
      t.includes('bù') ||
      t.includes('sinh con'),
  )

  const periodText = formatLeavePeriod(request)

  // Bàn giao công việc
  const handoversText =
    request.handovers && request.handovers.length > 0
      ? request.handovers
          .map((h) =>
            h.employee_name ? `${h.employee_name}: ${h.content}` : h.content,
          )
          .filter(Boolean)
          .join('; ')
      : 'Cá nhân tự sắp xếp công việc. Team hỗ trợ công việc'

  return (
    <div
      className="a4-print-sheet mx-auto bg-white text-black shadow-xl"
      style={{
        width: '210mm',
        minHeight: '297mm',
        padding: '20mm',
        fontFamily: "'Times New Roman', Times, serif",
        fontSize: '13pt',
        lineHeight: 1.6,
        boxSizing: 'border-box',
      }}
    >
      {/* Header thương hiệu DEGO HOLDING với Logo SVG & đường border gãy góc */}
      <div className="relative mb-6 overflow-hidden">
        <div className="flex items-start">
          <div className="w-[100px] shrink-0">
            <img
              src="/images/dego-logo.svg"
              onError={(e) => {
                if (!e.currentTarget.src.endsWith('/logo.svg')) {
                  e.currentTarget.src = '/logo.svg'
                }
              }}
              alt="DEGO HOLDING"
              className="w-[100px] h-[40px] object-contain block"
            />
          </div>
          <div className="flex-1 text-left font-serif text-black pl-10 pb-5 pt-0.5">
            <div className="text-[8.5pt] leading-normal space-y-1 text-black">
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Home className="w-3.5 h-3.5 shrink-0 text-black stroke-[2]" />
                <span>
                  B19, ĐDC Cần Thơ, Khu DCVH Tây Đô, P.Hưng Thạnh, Q.Cái Răng, TP. Cần Thơ
                </span>
              </div>
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Phone className="w-3.5 h-3.5 shrink-0 text-black stroke-[2]" />
                <span>1900.633.094 – 0898.001.113</span>
                <span className="text-black/40 mx-1">|</span>
                <Mail className="w-3.5 h-3.5 shrink-0 text-black stroke-[2]" />
                <span className="italic text-[#00aeef]">hr.degoholding@gmail.com</span>
              </div>
              <div className="flex items-center gap-1.5 whitespace-nowrap">
                <Globe className="w-3.5 h-3.5 shrink-0 text-black stroke-[2]" />
                <span>www.degoholding.com</span>
              </div>
            </div>
          </div>
        </div>

        {/* Đường phân cách đơn duy nhất: liền mạch từ logo, vát 45 độ và chạy ngang dưới domain với padding thoáng */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          fill="none"
        >
          <path
            d="M 0 27.2 L 98.7 27.2 L 139.5 68 H 1200"
            stroke="#000"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* Tiêu đề đơn */}
      <h1
        className="text-center font-bold uppercase my-5"
        style={{ fontSize: '14pt', letterSpacing: '0.5px' }}
      >
        ĐƠN XIN NGHỈ PHÉP
      </h1>

      {/* Kính gửi */}
      <div className="font-bold mb-4">
        <div className="flex">
          <span className="w-24 shrink-0">Kính gửi:</span>
          <div className="space-y-1">
            <div>
              - Trưởng phòng/Bộ phận/Nhóm:{' '}
              <span>{request.department_name || '................................................'}</span>
            </div>
            <div>- Trưởng phòng HCNS.</div>
          </div>
        </div>
      </div>

      {/* Thông tin nhân sự */}
      <div className="space-y-2 mb-3">
        <div className="flex justify-between items-baseline">
          <div className="w-[55%]">
            Tôi tên là: <span className="font-normal">{request.employee_name || DOTS}</span>
          </div>
          <div className="w-[45%]">
            SĐT: <span className="font-normal">{request.contact_phone || '........................................'}</span>
          </div>
        </div>
        <div className="flex justify-between items-baseline">
          <div className="w-[55%]">
            Chức vụ:{' '}
            <span className="font-normal">
              {request.employee_position || '........................................'}
            </span>
          </div>
          <div className="w-[45%]">
            Phòng:{' '}
            <span className="font-normal">
              {request.department_name || '........................................'}
            </span>
          </div>
        </div>
      </div>

      {/* Đề nghị xin nghỉ */}
      <div className="space-y-2 mb-4 text-justify">
        <p>
          Nay tôi làm đơn này xin phép Trưởng Bộ phận cho tôi được nghỉ phép {periodText}.
        </p>
        <p>
          Lý do: <span className="font-normal">{request.reason || DOTS}</span>
        </p>

        {/* Phân loại nghỉ */}
        <div className="flex items-center flex-wrap gap-x-5 gap-y-1 pt-1">
          <span>Nghỉ theo diện:</span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-flex items-center justify-center w-3.5 h-3.5 border border-black text-xs font-bold leading-none">
              {isUnpaid ? '✓' : ''}
            </span>
            Không lương
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-flex items-center justify-center w-3.5 h-3.5 border border-black text-xs font-bold leading-none">
              {isAnnual ? '✓' : ''}
            </span>
            Phép năm
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-flex items-center justify-center w-3.5 h-3.5 border border-black text-xs font-bold leading-none">
              {isSick ? '✓' : ''}
            </span>
            Nghỉ ốm
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-flex items-center justify-center w-3.5 h-3.5 border border-black text-xs font-bold leading-none">
              {isStatutory ? '✓' : ''}
            </span>
            Nghỉ chế độ
          </span>
        </div>

        <p className="pt-1">
          Người quản lý thay công việc:{' '}
          <span className="font-normal">{handoversText}</span>
        </p>
        <p>Rất mong Trưởng Bộ phận công ty xem xét và chấp thuận.</p>
      </div>

      {/* Địa điểm & ngày tháng */}
      <div className="text-right italic my-4 pr-4">
        Cần Thơ, ngày {day} tháng {month} năm {year}
      </div>

      {/* Bảng chữ ký 3 cột */}
      <div className="grid grid-cols-3 text-center mt-6">
        <div className="flex flex-col justify-between min-h-[140px]">
          <div className="font-bold">P.HCNS</div>
          <div className="h-20">{/* Khoảng trống ký tên */}</div>
          <div className="font-bold">&nbsp;</div>
        </div>
        <div className="flex flex-col justify-between min-h-[140px]">
          <div className="font-bold">Trưởng Phòng/Bộ phận</div>
          <div className="h-20">{/* Khoảng trống ký tên */}</div>
          <div className="font-bold">{request.decided_by_name || ''}</div>
        </div>
        <div className="flex flex-col justify-between min-h-[140px]">
          <div className="font-bold">Người làm đơn</div>
          <div className="h-20">{/* Khoảng trống ký tên */}</div>
          <div className="font-bold">{request.employee_name || ''}</div>
        </div>
      </div>
    </div>
  )
}
