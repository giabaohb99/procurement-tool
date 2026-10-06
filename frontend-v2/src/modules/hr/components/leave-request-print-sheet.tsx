// Mặt đơn của bản in nghỉ phép — dựng theo mẫu Word 2026 «ĐƠN XIN NGHỈ PHÉP / NGHỈ CHẾ ĐỘ»
// (`2026 Mau_Don_Xin_Nghi_Phep_Che_Do_Thai_San.docx`, đại ca gửi 06/10/2026): Quốc hiệu thay logo,
// ba mục đánh số, ba ô loại hình nghỉ, hai ô ký (Người xin nghỉ · Trưởng bộ phận).
// Lề trang 20mm = lề 1152 twip của tệp Word; cỡ chữ theo đúng tệp (thân 11pt, tiêu đề 18pt).
import { Check } from 'lucide-react'

import { LEAVE_SESSION, type LeaveRequest } from '../types/leave'
import { classifyLeaveForPrint } from '../utils/leave-print-category'

const DOTS = '……………………………………………'
//  Ô bảng KHÔNG viền (đại ca chốt 06/10/2026): viền xám mờ của tệp Word in ra đứt khúc, còn sót
//  mấy vạch dọc lơ lửng. Bỏ ở cả bản xem trước để màn hình khớp đúng tờ giấy in ra.
const CELL = 'py-1 pr-2 align-top'

function formatDateVn(dateStr: string): string {
  if (!dateStr) return '……/……/20…'
  const parts = dateStr.split('T')[0].split('-')
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr
}

/** Ngày ký đơn — mốc chốt gần nhất, không có thì ngày nghỉ, cùng lắm là hôm nay. */
function parseDocDate(request: LeaveRequest) {
  const raw = request.decided_at || request.submitted_at || request.created_at || request.from_date || ''
  const d = raw ? new Date(raw) : new Date()
  return {
    day: String(d.getDate()).padStart(2, '0'),
    month: String(d.getMonth() + 1).padStart(2, '0'),
    year: String(d.getFullYear()),
  }
}

/** Ghi chú buổi cạnh một mốc ngày — nghỉ cả ngày thì không ghi gì. */
function describeSession(session: number): string {
  if (session === LEAVE_SESSION.MORNING) return ' (buổi sáng)'
  if (session === LEAVE_SESSION.AFTERNOON) return ' (buổi chiều)'
  return ''
}

/** «Từ ngày … đến hết ngày …» của mẫu, kèm buổi / giờ khi không nghỉ trọn ngày. */
function formatLeaveRange(request: LeaveRequest): string {
  const from = formatDateVn(request.from_date)
  const to = formatDateVn(request.to_date || request.from_date)
  const hourly =
    request.from_session === LEAVE_SESSION.HOURLY && request.from_time && request.to_time
      ? ` (${request.from_time.slice(0, 5)} - ${request.to_time.slice(0, 5)})`
      : ''
  return `Từ ngày ${from}${hourly || describeSession(request.from_session)} đến hết ngày ${to}${
    hourly ? '' : describeSession(request.to_session)
  }`
}

/** Ô vuông in ra giấy (không phải ô nhập) — có dấu tick khi loại nghỉ thuộc ô này. */
function CheckRow({ checked, label }: { checked: boolean; label: string }) {
  return (
    <tr>
      <td className={CELL}>
        <span className="flex items-center gap-2.5">
          <span
            role="img"
            aria-label={checked ? 'Đã đánh dấu' : 'Chưa đánh dấu'}
            className="inline-flex size-[1.1em] shrink-0 items-center justify-center border border-black"
          >
            {checked && <Check className="size-[0.9em] stroke-[3]" />}
          </span>
          {label}
        </span>
      </td>
    </tr>
  )
}

function SignatureBlock({ title, name }: { title: string; name?: string }) {
  return (
    <div className="flex w-[44%] flex-col items-center text-center">
      <div className="font-bold">{title}</div>
      <div className="text-[10pt] italic">(Ký và ghi rõ họ tên)</div>
      <div className="h-24" />
      <div className={name ? 'font-bold' : undefined}>{name || DOTS}</div>
    </div>
  )
}

export function LeaveRequestPrintSheet({
  request,
  attachmentNote,
}: {
  request: LeaveRequest
  attachmentNote: string
}) {
  const { day, month, year } = parseDocDate(request)
  const categories = classifyLeaveForPrint(
    [request.leave_type_name, ...(request.lines ?? []).map((line) => line.leave_type_name)],
    request.total_days,
  )
  //  Mục bàn giao LUÔN có chữ (luật hr-leave): trống thì nói rõ là tự sắp xếp.
  const handoverText =
    request.handovers && request.handovers.length > 0
      ? request.handovers
          .map((h) => (h.employee_name ? `${h.employee_name}${h.content ? ` (${h.content})` : ''}` : h.content))
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
        fontSize: '11pt',
        lineHeight: 1.45,
        boxSizing: 'border-box',
      }}
    >
      {/* Quốc hiệu — tiêu ngữ */}
      <div className="mb-3 text-center font-bold">
        <div>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
        <div style={{ fontSize: '13pt' }}>Độc lập - Tự do - Hạnh phúc</div>
        <div>-----------------------</div>
      </div>

      <div className="mb-5 text-right italic">
        Cần Thơ, ngày {day} tháng {month} năm {year}
      </div>

      <h1 className="mb-5 text-center font-bold" style={{ fontSize: '18pt' }}>
        ĐƠN XIN NGHỈ PHÉP / NGHỈ CHẾ ĐỘ
      </h1>

      <div className="mb-4 flex">
        <span className="w-20 shrink-0 font-bold">Kính gửi:</span>
        <div>
          <div>- Ban Giám đốc {request.company_name || '[Tên Công ty]'}</div>
          <div>- Bộ phận Nhân sự</div>
          <div>- Trưởng bộ phận: {request.department_name || DOTS}</div>
        </div>
      </div>

      <h2 className="mt-5 mb-2 font-bold" style={{ fontSize: '13pt' }}>
        1. Thông tin nhân sự
      </h2>
      <table className="w-full table-fixed border-collapse">
        <tbody>
          <tr>
            <td className={CELL}>
              <b>Họ và tên:</b> {request.employee_name || ''}
            </td>
            <td className={CELL} />
          </tr>
          <tr>
            <td className={CELL}>
              <b>Chức danh / Vị trí:</b> {request.employee_position || ''}
            </td>
            <td className={CELL}>
              <b>Phòng / Bộ phận:</b> {request.department_name || ''}
            </td>
          </tr>
        </tbody>
      </table>

      <h2 className="mt-5 mb-2 font-bold" style={{ fontSize: '13pt' }}>
        2. Nội dung xin nghỉ
      </h2>
      <p className="mb-1">
        <b>a) Loại hình nghỉ</b> <i>(vui lòng đánh dấu vào ô tương ứng):</i>
      </p>
      <table className="mb-2 w-full border-collapse">
        <tbody>
          <CheckRow checked={categories.paid} label="Nghỉ phép năm (có lương)" />
          <CheckRow checked={categories.unpaid} label="Nghỉ việc riêng (không lương)" />
          <CheckRow
            checked={categories.insurance}
            label="Nghỉ chế độ bảo hiểm (ốm đau, thai sản ..)"
          />
        </tbody>
      </table>
      <div className="space-y-1">
        <p>
          <b>b) Thời gian xin nghỉ:</b> {formatLeaveRange(request)}
        </p>
        <p>
          <b>c) Tổng số ngày nghỉ:</b> {request.total_days} ngày.
        </p>
        <p className="text-justify">
          <b>d) Lý do xin nghỉ:</b> {request.reason || DOTS}
        </p>
        {attachmentNote && (
          <p>
            <b>e) Tài liệu đính kèm:</b> {attachmentNote}
          </p>
        )}
      </div>

      <h2 className="mt-5 mb-2 font-bold" style={{ fontSize: '13pt' }}>
        3. Bàn giao công việc
      </h2>
      <p>
        <b>• Người tiếp nhận bàn giao:</b> {handoverText}
      </p>
      <p className="mt-1 text-justify italic">
        Tôi xin cam đoan đã hoàn thành công tác bàn giao công việc trước khi nghỉ và sẽ quay trở lại
        làm việc đúng thời gian đã đăng ký trên. Kính mong Ban Giám đốc và Trưởng bộ phận xem xét, phê
        duyệt.
      </p>

      <div className="mt-8 flex justify-between">
        <SignatureBlock title="NGƯỜI XIN NGHỈ" name={request.employee_name} />
        <SignatureBlock title="TRƯỞNG BỘ PHẬN" name={request.decided_by_name} />
      </div>
    </div>
  )
}
