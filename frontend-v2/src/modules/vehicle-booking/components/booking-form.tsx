import { ArrowDown, ArrowUp, Loader2, MapPin, Plus, Send, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'

import { cn } from '@/shared/utils/cn'
import { BookingPageHeader } from './booking-page-header'
import {
  useCreateVehicleBooking,
  useMyDriver,
  useUpdateVehicleBooking,
} from '../hooks/use-vehicle-bookings'
import {
  REQUEST_TYPE,
  emptyStop,
  type Stop,
  type VehicleBooking,
  type VehicleBookingPayload,
} from '../types/vehicle-booking'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'

function labelsFor(isDelivery: boolean) {
  return {
    start: isDelivery ? 'Điểm lấy hàng' : 'Điểm đi',
    end: isDelivery ? 'Điểm giao hàng' : 'Điểm đến',
    startTime: isDelivery ? 'Thời gian lấy hàng' : 'Thời gian đi',
    endTime: isDelivery ? 'Thời gian giao (dự kiến)' : 'Thời gian về (dự kiến)',
  }
}

interface BookingFormProps {
  /** Có = SỬA phiếu này. */
  booking?: VehicleBooking
  /** NHÂN BẢN: tạo mới, chép nội dung từ phiếu này. */
  duplicateFrom?: VehicleBooking
  /** Tiêu đề trang (vd "Tạo yêu cầu đặt xe"). */
  title: string
  /** Gọi sau khi lưu/gửi duyệt thành công hoặc bấm Hủy/back — điều hướng đi. */
  onDone: () => void
}

/** Đổi `Date` → chuỗi cho `<input type="datetime-local">` theo GIỜ ĐỊA PHƯƠNG. */
function toLocalInputValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/**
 * Biểu mẫu YÊU CẦU ĐẶT XE dùng trên TRANG (tạo `/vehicle-booking/new`, sửa
 * `/vehicle-booking/:id/edit`). Hai loại: công tác (chở người) / giao hàng.
 */
export function BookingForm({ booking, duplicateFrom, title, onDone }: BookingFormProps) {
  const isEdit = Boolean(booking)
  const source = booking ?? duplicateFrom
  const createMutation = useCreateVehicleBooking()
  const updateMutation = useUpdateVehicleBooking()
  const pending = createMutation.isPending || updateMutation.isPending

  const [requestType, setRequestType] = useState<number>(source?.request_type ?? REQUEST_TYPE.car)
  const isDelivery = requestType === REQUEST_TYPE.delivery
  const L = labelsFor(isDelivery)

  //  TỰ LÁI: người yêu cầu là tài xế + GPLX. Tự điền nếu họ đã là tài xế.
  const [selfDrive, setSelfDrive] = useState(source?.is_self_drive ?? false)
  const [licenseNumber, setLicenseNumber] = useState(source?.license_number ?? '')
  const [licenseClass, setLicenseClass] = useState(source?.license_class ?? '')
  const myDriver = useMyDriver()
  const isDriverProfile = Boolean(myDriver.data)

  function selectType(type: number, self: boolean) {
    setRequestType(type)
    setSelfDrive(self)
    //  Chọn tự lái mà người yêu cầu đã là tài xế → tự điền GPLX (khi còn trống).
    if (self && myDriver.data) {
      setLicenseNumber((v) => v || myDriver.data!.license_number)
      setLicenseClass((v) => v || myDriver.data!.license_class)
    }
  }

  const [purpose, setPurpose] = useState(source?.purpose ?? '')
  const [startLocation, setStartLocation] = useState(source?.start_location ?? 'Văn phòng Degoholding')
  const [endLocation, setEndLocation] = useState(source?.end_location ?? '')
  const [stops, setStops] = useState<Stop[]>(source?.stops ?? [])
  const [startTime, setStartTime] = useState(source?.start_time ?? '')
  const [endTime, setEndTime] = useState(source?.end_time ?? '')
  const [note, setNote] = useState(source?.note ?? '')

  const [passengerCount, setPassengerCount] = useState(source?.passenger_count ?? 1)
  const [attendees, setAttendees] = useState(source?.attendees ?? '')
  const [contactPhone, setContactPhone] = useState(source?.contact_phone ?? '')
  const [isRoundTrip, setIsRoundTrip] = useState(source?.is_round_trip ?? false)

  const [goodsName, setGoodsName] = useState(source?.goods_name ?? '')
  const [goodsSize, setGoodsSize] = useState(source?.goods_size ?? '')
  const [senderName, setSenderName] = useState(source?.sender_name ?? '')
  const [senderPhone, setSenderPhone] = useState(source?.sender_phone ?? '')
  const [receiverName, setReceiverName] = useState(source?.receiver_name ?? '')
  const [receiverPhone, setReceiverPhone] = useState(source?.receiver_phone ?? '')
  const [specialInstructions, setSpecialInstructions] = useState(source?.special_instructions ?? '')


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
      is_self_drive: selfDrive,
      license_number: selfDrive ? licenseNumber.trim() : '',
      license_class: selfDrive ? licenseClass.trim() : '',
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

  function validate(): string {
    if (!purpose.trim()) return 'Vui lòng nhập mục đích.'
    if (!startLocation.trim()) return `Vui lòng nhập ${L.start.toLowerCase()}.`
    if (!endLocation.trim()) return `Vui lòng nhập ${L.end.toLowerCase()}.`
    if (!startTime) return `Vui lòng chọn ${L.startTime.toLowerCase()}.`
    if (!endTime) return `Vui lòng chọn ${L.endTime.toLowerCase()}.`
    if (endTime <= startTime) return 'Thời gian về/giao phải SAU thời gian đi/lấy hàng.'
    if (selfDrive) {
      if (!licenseNumber.trim()) return 'Tự lái: vui lòng nhập Số giấy phép lái xe.'
      if (!licenseClass.trim()) return 'Tự lái: vui lòng nhập Hạng GPLX.'
    }
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
    //  KHÔNG cho Lưu hoặc Gửi duyệt khi Thời gian đi ở QUÁ KHỨ (áp cả hai nút).
    if (startTime && new Date(startTime).getTime() < Date.now()) {
      toast.error(`${L.startTime} không được ở quá khứ.`)
      return
    }
    const msg = validate()
    if (submit && msg) {
      toast.error(msg)
      return
    }
    const body = buildPayload()
    if (isEdit && booking) {
      updateMutation.mutate({ id: booking.id, payload: body, submit }, { onSuccess: onDone })
    } else {
      createMutation.mutate({ payload: body, submit }, { onSuccess: onDone })
    }
  }

  return (
    <div className="flex w-full flex-col">
      <BookingPageHeader
        title={title}
        onBack={onDone}
        actions={
          <>
            <Button variant="outline" onClick={onDone} disabled={pending}>
              Hủy
            </Button>
            <Button variant="outline" onClick={() => handleSubmit(false)} disabled={pending}>
              Lưu nháp
            </Button>
            <Button onClick={() => handleSubmit(true)} disabled={pending}>
              {pending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              Gửi duyệt
            </Button>
          </>
        }
      />
      <Card className="flex flex-col gap-5 p-5">
        {/* Chọn loại yêu cầu — 2 loại × (có tài xế / TỰ LÁI) */}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <TypeCard
            active={!isDelivery && !selfDrive}
            title="Đặt xe công tác"
            desc="Chở người đi công tác, họp, đón khách."
            icon={<CarBookingIcon className="size-7" />}
            onClick={() => selectType(REQUEST_TYPE.car, false)}
          />
          <TypeCard
            active={isDelivery && !selfDrive}
            tone="amber"
            title="Đặt xe giao hàng"
            desc="Vận chuyển hàng hóa, chứng từ giữa các điểm."
            icon={<DeliveryBookingIcon className="size-7" />}
            onClick={() => selectType(REQUEST_TYPE.delivery, false)}
          />
          <TypeCard
            active={!isDelivery && selfDrive}
            title="Đặt xe ô tô (tự lái)"
            desc="Bạn tự lái đi công tác — chỉ cần điều phối xe."
            icon={<CarBookingIcon className="size-7" />}
            onClick={() => selectType(REQUEST_TYPE.car, true)}
          />
          <TypeCard
            active={isDelivery && selfDrive}
            tone="amber"
            title="Đặt xe giao hàng (tự lái)"
            desc="Bạn tự lái giao hàng — chỉ cần điều phối xe."
            icon={<DeliveryBookingIcon className="size-7" />}
            onClick={() => selectType(REQUEST_TYPE.delivery, true)}
          />
        </div>

        {/* GPLX của người yêu cầu — chỉ khi TỰ LÁI (bắt buộc; tự điền nếu đã là tài xế) */}
        {selfDrive && (
          <div className="flex flex-col gap-4">
            <SectionHeading>Thông tin tài xế</SectionHeading>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Số giấy phép lái xe" required>
                <Input
                  value={licenseNumber}
                  readOnly={isDriverProfile}
                  onChange={(e) => setLicenseNumber(e.target.value)}
                  placeholder="VD: 79-012345678"
                />
              </Field>
              <Field label="Hạng GPLX" required>
                <Input
                  value={licenseClass}
                  readOnly={isDriverProfile}
                  onChange={(e) => setLicenseClass(e.target.value)}
                  placeholder="VD: B2, C, D"
                />
              </Field>
              {isDriverProfile && (
                <p className="text-xs text-muted-foreground sm:col-span-2">
                  Tự điền từ hồ sơ tài xế của bạn.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Thông tin chung */}
        <div className="flex flex-col gap-4">
          <SectionHeading>Thông tin chung</SectionHeading>

          <Field label="Mục đích" required>
            <Input value={purpose} onChange={(e) => setPurpose(e.target.value)} placeholder="VD: Đi thăm khách hàng quận 7" />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={L.start} required>
              <Input value={startLocation} onChange={(e) => setStartLocation(e.target.value)} />
            </Field>
            <Field label={L.end} required>
              <Input value={endLocation} onChange={(e) => setEndLocation(e.target.value)} />
            </Field>
          </div>

          <div className="flex flex-col gap-2">
            <Label>Điểm dừng trung gian</Label>
            {stops.length === 0 && <p className="text-sm text-muted-foreground">Chưa có điểm dừng nào.</p>}
            {stops.map((stop, index) => (
              <div key={index} className="rounded-lg border p-3">
                <div className="flex items-center gap-2">
                  <MapPin className="size-4 shrink-0 text-muted-foreground" />
                  <Input value={stop.location} onChange={(e) => setStopField(index, 'location', e.target.value)} placeholder={`Điểm dừng ${index + 1}`} />
                  <Button type="button" variant="ghost" size="icon" disabled={index === 0} onClick={() => moveStop(index, -1)} aria-label="Lên">
                    <ArrowUp className="size-4" />
                  </Button>
                  <Button type="button" variant="ghost" size="icon" disabled={index === stops.length - 1} onClick={() => moveStop(index, 1)} aria-label="Xuống">
                    <ArrowDown className="size-4" />
                  </Button>
                  <Button type="button" variant="ghost" size="icon" onClick={() => setStops((prev) => prev.filter((_, i) => i !== index))} aria-label="Xóa điểm dừng">
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                </div>
                <div className="mt-2 grid gap-2 pl-6 sm:grid-cols-2">
                  <Input value={stop.contact_name} onChange={(e) => setStopField(index, 'contact_name', e.target.value)} placeholder="Tên người liên hệ" />
                  <Input value={stop.contact_phone} onChange={(e) => setStopField(index, 'contact_phone', e.target.value)} placeholder="Số điện thoại" />
                </div>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" className="w-fit" onClick={() => setStops((prev) => [...prev, emptyStop()])}>
              <Plus className="size-4" />
              Thêm điểm dừng
            </Button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={L.startTime} required>
              {/* Chặn giờ quá khứ ở bộ chọn + báo NGAY khi chọn; kiểm lại lúc Lưu/Gửi duyệt. */}
              <Input
                type="datetime-local"
                min={toLocalInputValue(new Date())}
                value={startTime}
                onChange={(e) => {
                  const value = e.target.value
                  setStartTime(value)
                  if (value && new Date(value).getTime() < Date.now()) {
                    toast.error(`${L.startTime} không được ở quá khứ.`)
                  }
                }}
              />
            </Field>
            <Field label={L.endTime} required>
              <Input
                type="datetime-local"
                min={startTime || toLocalInputValue(new Date())}
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </Field>
          </div>

          {!isDelivery && (
            <label className="flex w-fit items-center gap-2 text-sm">
              <Checkbox checked={isRoundTrip} onCheckedChange={(v) => setIsRoundTrip(v === true)} />
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
                <Input value={goodsSize} onChange={(e) => setGoodsSize(e.target.value)} placeholder="VD: 30x50x20cm, 5kg" />
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
              <Textarea value={specialInstructions} onChange={(e) => setSpecialInstructions(e.target.value)} placeholder="VD: Tránh mưa, hàng dễ vỡ." />
            </Field>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <SectionHeading>Thông tin chuyến đi</SectionHeading>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Số hành khách" required>
                <Input type="number" min={1} value={passengerCount} onChange={(e) => setPassengerCount(Math.max(1, Number(e.target.value) || 1))} />
              </Field>
              <Field label="SĐT liên hệ">
                <Input value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
              </Field>
            </div>
            <Field label="Người tham gia">
              <Textarea value={attendees} onChange={(e) => setAttendees(e.target.value)} placeholder="Danh sách người đi cùng." />
            </Field>
          </div>
        )}

        <Field label="Ghi chú">
          <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú thêm cho điều phối viên (VD: cần xe 7 chỗ)." />
        </Field>

      </Card>
    </div>
  )
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

function TypeCard({
  active,
  title,
  desc,
  icon,
  onClick,
  tone = 'blue',
}: {
  active: boolean
  title: string
  desc: string
  icon: React.ReactNode
  onClick: () => void
  /** Màu khi đang chọn: blue (mặc định) | amber (giao hàng, khớp nút "Thuê ngoài"). */
  tone?: 'blue' | 'amber'
}) {
  const activeClass =
    tone === 'amber'
      ? 'border-amber-500 bg-amber-50 text-foreground dark:bg-amber-950/40'
      : 'border-primary bg-primary/5 text-foreground'
  const iconActive = tone === 'amber' ? 'text-amber-600 dark:text-amber-400' : 'text-primary'
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex flex-col items-start gap-2 rounded-lg border p-4 text-left transition-colors',
        active ? activeClass : 'border-border text-muted-foreground hover:border-primary/40 hover:bg-accent',
      )}
    >
      <span className={cn(active ? iconActive : 'text-muted-foreground')}>{icon}</span>
      <span className="text-sm font-semibold text-foreground">{title}</span>
      <span className="text-xs text-muted-foreground">{desc}</span>
    </button>
  )
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
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
