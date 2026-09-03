import { ArrowDown, ArrowUp, MapPin, Plus, Send, Trash2, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { DialogContent } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { useCreateVehicleBooking, useUpdateVehicleBooking } from '../hooks/use-vehicle-bookings'
import {
  REQUEST_TYPE,
  emptyStop,
  type Stop,
  type VehicleBooking,
  type VehicleBookingPayload,
} from '../types/vehicle-booking'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'

interface BookingFormDialogProps {
  /** Có = SỬA phiếu này; bỏ trống = TẠO mới. */
  booking?: VehicleBooking
  /** Đóng popup (đã qua chốt chống mất dữ liệu). */
  onClose: () => void
  /** Lưu/gửi duyệt thành công. */
  onSaved: () => void
}

function labelsFor(isDelivery: boolean) {
  return {
    start: isDelivery ? 'Điểm lấy hàng' : 'Điểm đi',
    end: isDelivery ? 'Điểm giao hàng' : 'Điểm đến',
    startTime: isDelivery ? 'Thời gian lấy hàng' : 'Thời gian đi',
    endTime: isDelivery ? 'Thời gian giao (dự kiến)' : 'Thời gian về (dự kiến)',
  }
}

export function BookingFormDialog({ booking, onClose, onSaved }: BookingFormDialogProps) {
  const isEdit = Boolean(booking)
  const createMutation = useCreateVehicleBooking()
  const updateMutation = useUpdateVehicleBooking()
  const pending = createMutation.isPending || updateMutation.isPending

  const [requestType, setRequestType] = useState<number>(booking?.request_type ?? REQUEST_TYPE.car)
  const isDelivery = requestType === REQUEST_TYPE.delivery
  const L = labelsFor(isDelivery)

  const [purpose, setPurpose] = useState(booking?.purpose ?? '')
  const [startLocation, setStartLocation] = useState(booking?.start_location ?? 'Văn phòng Degoholding')
  const [endLocation, setEndLocation] = useState(booking?.end_location ?? '')
  const [stops, setStops] = useState<Stop[]>(booking?.stops ?? [])
  const [startTime, setStartTime] = useState(booking?.start_time ?? '')
  const [endTime, setEndTime] = useState(booking?.end_time ?? '')
  const [note, setNote] = useState(booking?.note ?? '')

  const [passengerCount, setPassengerCount] = useState(booking?.passenger_count ?? 1)
  const [attendees, setAttendees] = useState(booking?.attendees ?? '')
  const [contactPhone, setContactPhone] = useState(booking?.contact_phone ?? '')
  const [isRoundTrip, setIsRoundTrip] = useState(booking?.is_round_trip ?? false)

  const [goodsName, setGoodsName] = useState(booking?.goods_name ?? '')
  const [goodsSize, setGoodsSize] = useState(booking?.goods_size ?? '')
  const [senderName, setSenderName] = useState(booking?.sender_name ?? '')
  const [senderPhone, setSenderPhone] = useState(booking?.sender_phone ?? '')
  const [receiverName, setReceiverName] = useState(booking?.receiver_name ?? '')
  const [receiverPhone, setReceiverPhone] = useState(booking?.receiver_phone ?? '')
  const [specialInstructions, setSpecialInstructions] = useState(booking?.special_instructions ?? '')

  const [error, setError] = useState('')

  function setStopField(index: number, field: keyof Stop, value: string) {
    setStops((prev) => prev.map((s, i) => (i === index ? { ...s, [field]: value } : s)))
  }
  function moveStop(index: number, dir: -1 | 1) {
    setStops((prev) => {
      const next = [...prev]
      const target = index + dir
      if (target < 0 || target >= next.length) return prev
      ;[next[index], next[target]] = [next[target], next[index]]
      return next
    })
  }

  function buildPayload(): VehicleBookingPayload {
    const cleanStops: Stop[] = stops
      .map((s) => ({
        location: s.location.trim(),
        contact_name: s.contact_name.trim(),
        contact_phone: s.contact_phone.trim(),
      }))
      .filter((s) => s.location)
    const base: VehicleBookingPayload = {
      request_type: requestType,
      purpose: purpose.trim(),
      start_location: startLocation.trim(),
      end_location: endLocation.trim(),
      stops: cleanStops,
      start_time: startTime,
      end_time: endTime,
      note: note.trim(),
    }
    if (isDelivery) {
      return {
        ...base,
        goods_name: goodsName.trim(),
        goods_size: goodsSize.trim(),
        sender_name: senderName.trim(),
        sender_phone: senderPhone.trim(),
        receiver_name: receiverName.trim(),
        receiver_phone: receiverPhone.trim(),
        special_instructions: specialInstructions.trim(),
      }
    }
    return {
      ...base,
      passenger_count: passengerCount,
      attendees: attendees.trim(),
      contact_phone: contactPhone.trim(),
      is_round_trip: isRoundTrip,
    }
  }

  // Ảnh chụp lúc mở để biết form đã đổi hay chưa (chống mất dữ liệu khi đóng nhầm).
  // Chụp một lần bằng lazy-init của useState — không đọc ref trong lúc render.
  const [initialSnapshot] = useState(() => JSON.stringify(buildPayload()))
  const payload = buildPayload()
  const dirty = JSON.stringify(payload) !== initialSnapshot

  /** Đóng theo case C-01: chỉ Hủy/X; nếu form đã đổi thì hỏi xác nhận. */
  function attemptClose() {
    if (pending) return
    if (dirty && !window.confirm('Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?')) return
    onClose()
  }

  function validate(): string {
    if (!purpose.trim()) return 'Vui lòng nhập mục đích.'
    // Lộ trình & thời gian bắt buộc cho cả hai loại.
    if (!startLocation.trim()) return `Vui lòng nhập ${L.start.toLowerCase()}.`
    if (!endLocation.trim()) return `Vui lòng nhập ${L.end.toLowerCase()}.`
    if (!startTime) return `Vui lòng chọn ${L.startTime.toLowerCase()}.`
    if (!endTime) return `Vui lòng chọn ${L.endTime.toLowerCase()}.`
    // Chuỗi datetime-local cùng định dạng nên so sánh chuỗi = so sánh thời gian.
    if (endTime <= startTime) return 'Thời gian về/giao phải SAU thời gian đi/lấy hàng.'
    if (isDelivery) {
      if (!goodsName.trim()) return 'Vui lòng nhập tên hàng hóa.'
      if (!senderName.trim() || !senderPhone.trim()) return 'Vui lòng nhập người gửi và SĐT.'
      if (!receiverName.trim() || !receiverPhone.trim()) return 'Vui lòng nhập người nhận và SĐT.'
    } else if (!passengerCount || passengerCount < 1) {
      return 'Số hành khách phải từ 1 trở lên.'
    }
    return ''
  }

  function handleSubmit(submit: boolean) {
    const msg = validate()
    if (submit && msg) {
      setError(msg)
      return
    }
    setError('')
    const body = buildPayload()
    if (isEdit && booking) {
      updateMutation.mutate(
        { id: booking.id, payload: body, submit },
        { onSuccess: onSaved },
      )
    } else {
      createMutation.mutate({ payload: body, submit }, { onSuccess: onSaved })
    }
  }

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) attemptClose()
      }}
    >
      <DialogContent
        showCloseButton={false}
        // Case C-01: KHÔNG đóng bằng Esc hay click ra ngoài — chỉ Hủy/X, tránh mất dữ liệu.
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        className="flex max-h-[90vh] flex-col gap-0 p-0 sm:max-w-2xl"
      >
        <DialogHeader className="flex-row items-start justify-between border-b px-6 py-4 text-left">
          <div>
            <DialogTitle>
              {isEdit ? `Chỉnh sửa yêu cầu ${booking?.code ?? ''}` : 'Tạo yêu cầu đặt xe'}
            </DialogTitle>
            <DialogDescription>
              Chọn loại yêu cầu, điền lộ trình và thông tin — lưu nháp hoặc gửi duyệt.
            </DialogDescription>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={attemptClose}
            aria-label="Đóng"
          >
            <X className="size-4" />
          </Button>
        </DialogHeader>

        <div className="flex flex-col gap-5 overflow-y-auto px-6 py-5">
          {/* Chọn loại yêu cầu */}
          <div className="grid grid-cols-2 gap-3">
            <TypeCard
              active={!isDelivery}
              title="Đặt xe công tác"
              desc="Chở người đi công tác, họp, đón khách."
              icon={<CarBookingIcon className="size-7" />}
              onClick={() => setRequestType(REQUEST_TYPE.car)}
            />
            <TypeCard
              active={isDelivery}
              title="Đặt xe giao hàng"
              desc="Vận chuyển hàng hóa, chứng từ giữa các điểm."
              icon={<DeliveryBookingIcon className="size-7" />}
              onClick={() => setRequestType(REQUEST_TYPE.delivery)}
            />
          </div>

          {/* Thông tin chung */}
          <div className="flex flex-col gap-4">
            <SectionHeading>Thông tin chung</SectionHeading>

            <Field label="Mục đích" required>
              <Input
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="VD: Đi thăm khách hàng quận 7"
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={L.start} required>
                <Input value={startLocation} onChange={(e) => setStartLocation(e.target.value)} />
              </Field>
              <Field label={L.end} required>
                <Input value={endLocation} onChange={(e) => setEndLocation(e.target.value)} />
              </Field>
            </div>

            {/* Điểm dừng trung gian — mỗi điểm có địa điểm + người liên hệ */}
            <div className="flex flex-col gap-2">
              <Label>Điểm dừng trung gian</Label>
              {stops.length === 0 && (
                <p className="text-sm text-muted-foreground">Chưa có điểm dừng nào.</p>
              )}
              {stops.map((stop, index) => (
                <div key={index} className="rounded-lg border p-3">
                  <div className="flex items-center gap-2">
                    <MapPin className="size-4 shrink-0 text-muted-foreground" />
                    <Input
                      value={stop.location}
                      onChange={(e) => setStopField(index, 'location', e.target.value)}
                      placeholder={`Điểm dừng ${index + 1}`}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      disabled={index === 0}
                      onClick={() => moveStop(index, -1)}
                      aria-label="Lên"
                    >
                      <ArrowUp className="size-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      disabled={index === stops.length - 1}
                      onClick={() => moveStop(index, 1)}
                      aria-label="Xuống"
                    >
                      <ArrowDown className="size-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => setStops((prev) => prev.filter((_, i) => i !== index))}
                      aria-label="Xóa điểm dừng"
                    >
                      <Trash2 className="size-4 text-destructive" />
                    </Button>
                  </div>
                  <div className="mt-2 grid gap-2 pl-6 sm:grid-cols-2">
                    <Input
                      value={stop.contact_name}
                      onChange={(e) => setStopField(index, 'contact_name', e.target.value)}
                      placeholder="Tên người liên hệ"
                    />
                    <Input
                      value={stop.contact_phone}
                      onChange={(e) => setStopField(index, 'contact_phone', e.target.value)}
                      placeholder="Số điện thoại"
                    />
                  </div>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-fit"
                onClick={() => setStops((prev) => [...prev, emptyStop()])}
              >
                <Plus className="size-4" />
                Thêm điểm dừng
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={L.startTime} required>
                <Input
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                />
              </Field>
              <Field label={L.endTime} required>
                <Input
                  type="datetime-local"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                />
              </Field>
            </div>

            {!isDelivery && (
              <label className="flex w-fit items-center gap-2 text-sm">
                <Checkbox
                  checked={isRoundTrip}
                  onCheckedChange={(v) => setIsRoundTrip(v === true)}
                />
                Yêu cầu chuyến khứ hồi
              </label>
            )}
          </div>

          {/* Khối riêng theo loại */}
          {isDelivery ? (
            <div className="flex flex-col gap-4">
              <SectionHeading>Thông tin giao hàng</SectionHeading>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Tên hàng hóa" required>
                  <Input value={goodsName} onChange={(e) => setGoodsName(e.target.value)} />
                </Field>
                <Field label="Kích thước / Khối lượng">
                  <Input
                    value={goodsSize}
                    onChange={(e) => setGoodsSize(e.target.value)}
                    placeholder="VD: 30x50x20cm, 5kg"
                  />
                </Field>
                <Field label="Người gửi" required>
                  <Input value={senderName} onChange={(e) => setSenderName(e.target.value)} />
                </Field>
                <Field label="SĐT người gửi" required>
                  <Input value={senderPhone} onChange={(e) => setSenderPhone(e.target.value)} />
                </Field>
                <Field label="Người nhận" required>
                  <Input value={receiverName} onChange={(e) => setReceiverName(e.target.value)} />
                </Field>
                <Field label="SĐT người nhận" required>
                  <Input value={receiverPhone} onChange={(e) => setReceiverPhone(e.target.value)} />
                </Field>
              </div>
              <Field label="Chỉ dẫn đặc biệt">
                <Textarea
                  value={specialInstructions}
                  onChange={(e) => setSpecialInstructions(e.target.value)}
                  placeholder="VD: Tránh mưa, hàng dễ vỡ."
                />
              </Field>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <SectionHeading>Thông tin chuyến đi</SectionHeading>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Số hành khách" required>
                  <Input
                    type="number"
                    min={1}
                    value={passengerCount}
                    onChange={(e) => setPassengerCount(Math.max(1, Number(e.target.value) || 1))}
                  />
                </Field>
                <Field label="SĐT liên hệ">
                  <Input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
                </Field>
              </div>
              <Field label="Người tham gia">
                <Textarea
                  value={attendees}
                  onChange={(e) => setAttendees(e.target.value)}
                  placeholder="Danh sách người đi cùng."
                />
              </Field>
            </div>
          )}

          {/* Ghi chú chung */}
          <Field label="Ghi chú">
            <Textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Ghi chú thêm cho điều phối viên (VD: cần xe 7 chỗ)."
            />
          </Field>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <div className="flex items-center justify-end gap-2 border-t px-6 py-4">
          <Button variant="ghost" onClick={attemptClose} disabled={pending}>
            Hủy
          </Button>
          <Button variant="outline" onClick={() => handleSubmit(false)} disabled={pending}>
            Lưu nháp
          </Button>
          <Button onClick={() => handleSubmit(true)} disabled={pending}>
            <Send className="size-4" />
            Gửi duyệt
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

interface TypeCardProps {
  active: boolean
  title: string
  desc: string
  icon: React.ReactNode
  onClick: () => void
}

function TypeCard({ active, title, desc, icon, onClick }: TypeCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex flex-col items-start gap-2 rounded-lg border p-4 text-left transition-colors',
        active
          ? 'border-primary bg-primary/5 text-foreground'
          : 'border-border text-muted-foreground hover:border-primary/40 hover:bg-accent',
      )}
    >
      <span className={cn(active ? 'text-primary' : 'text-muted-foreground')}>{icon}</span>
      <span className="text-sm font-semibold text-foreground">{title}</span>
      <span className="text-xs text-muted-foreground">{desc}</span>
    </button>
  )
}

interface FieldProps {
  label: string
  required?: boolean
  children: React.ReactNode
}

function Field({ label, required, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
    </div>
  )
}
