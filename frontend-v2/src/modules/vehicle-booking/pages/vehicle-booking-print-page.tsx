import { ArrowLeft, Printer } from 'lucide-react'
import { type CSSProperties } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

import { useVehicleBooking } from '../hooks/use-vehicle-bookings'
import { REQUEST_TYPE, type VehicleBooking } from '../types/vehicle-booking'

const DOTS = '..............................'

const cell: CSSProperties = { border: '1px solid #888', padding: '4px 8px', fontSize: 12, verticalAlign: 'top' }
const cellLabel: CSSProperties = { ...cell, width: '28%', color: '#334155', fontWeight: 600, background: '#f1f5f9' }
const section: CSSProperties = {
  background: '#dbe5f1',
  fontWeight: 700,
  padding: '4px 8px',
  fontSize: 12.5,
  margin: '12px 0 4px',
  border: '1px solid #c6d4e6',
}

function row(label: string, value: string) {
  return (
    <tr>
      <td style={cellLabel}>{label}</td>
      <td style={cell}>{value || DOTS}</td>
    </tr>
  )
}

/**
 * Bản in phiếu đặt xe (A4). Nút In gọi `window.print()`; thanh thao tác tự ẩn khi
 * in (class `print:hidden`). Dữ liệu chỉ đọc — dùng lại đúng hook chi tiết.
 */
export function VehicleBookingPrintPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const bookingId = Number(id)
  const { data, isLoading } = useVehicleBooking(Number.isFinite(bookingId) ? bookingId : null)

  return (
    <div className="mx-auto w-full max-w-[820px] p-4">
      <div className="mb-4 flex items-center gap-2 print:hidden">
        <Button onClick={() => window.print()}>
          <Printer className="size-4" />
          In phiếu
        </Button>
        <Button variant="ghost" onClick={() => navigate(appRoutes.vehicleBooking.detail(bookingId))}>
          <ArrowLeft className="size-4" />
          Quay lại
        </Button>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-96" />
      ) : (
        <PrintSheet booking={data} />
      )}
    </div>
  )
}

function PrintSheet({ booking }: { booking: VehicleBooking }) {
  const isCar = booking.request_type === REQUEST_TYPE.car
  const stops = (booking.stops ?? [])
    .map((s) => s.location)
    .filter(Boolean)
    .join(' → ')

  return (
    <div style={{ background: '#fff', color: '#0f172a', padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase' }}>DEGO HOLDING</div>
        <h1 style={{ fontSize: 18, fontWeight: 700, margin: '10px 0 2px' }}>PHIẾU YÊU CẦU ĐẶT XE</h1>
        <div style={{ fontSize: 12, color: '#475569' }}>
          Số: {booking.code} — {booking.request_type_label}
        </div>
      </div>

      <div style={section}>A. Thông tin chung</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {row('Người yêu cầu', booking.requester)}
          {row('Mục đích', booking.purpose)}
          {row(isCar ? 'Điểm đi' : 'Điểm lấy hàng', booking.start_location)}
          {row(isCar ? 'Điểm đến' : 'Điểm giao hàng', booking.end_location)}
          {stops ? row('Điểm dừng', stops) : null}
          {row('Thời gian đi', booking.start_time)}
          {row('Thời gian về/giao', booking.end_time)}
        </tbody>
      </table>

      <div style={section}>B. {isCar ? 'Thông tin công tác' : 'Thông tin giao hàng'}</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {isCar ? (
            <>
              {row('Số hành khách', String(booking.passenger_count || ''))}
              {row('SĐT liên hệ', booking.contact_phone)}
              {row('Người tham gia', booking.attendees)}
              {row('Khứ hồi', booking.is_round_trip ? 'Có' : 'Không')}
            </>
          ) : (
            <>
              {row('Tên hàng hóa', booking.goods_name)}
              {row('Kích thước / khối lượng', booking.goods_size)}
              {row('Người gửi', `${booking.sender_name} — ${booking.sender_phone}`)}
              {row('Người nhận', `${booking.receiver_name} — ${booking.receiver_phone}`)}
              {row('Chỉ dẫn đặc biệt', booking.special_instructions)}
            </>
          )}
        </tbody>
      </table>

      <div style={section}>C. Điều phối</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {row('Xe được phân', booking.assigned_vehicle_label)}
          {row('Tài xế', booking.assigned_driver_label)}
          {row('Trạng thái', booking.status_label)}
        </tbody>
      </table>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          marginTop: 28,
          textAlign: 'center',
          fontSize: 12,
        }}
      >
        {['Người yêu cầu', 'Người duyệt', 'Điều phối'].map((label) => (
          <div key={label}>
            <div style={{ fontWeight: 700 }}>{label}</div>
            <div style={{ color: '#64748b', fontStyle: 'italic' }}>(Ký, ghi rõ họ tên)</div>
            <div style={{ height: 56 }} />
          </div>
        ))}
      </div>
    </div>
  )
}
