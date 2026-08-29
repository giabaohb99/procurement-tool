import { ArrowDown, ArrowUp, MapPin, Plus, Send, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { CarBookingIcon, DeliveryBookingIcon } from '../components/booking-type-icons'
import { useCreateVehicleBooking } from '../hooks/use-vehicle-bookings'
import { REQUEST_TYPE, type VehicleBookingPayload } from '../types/vehicle-booking'

/** Nhãn đổi theo loại yêu cầu (xe công tác vs giao hàng). */
function labelsFor(isDelivery: boolean) {
  return {
    start: isDelivery ? 'Điểm lấy hàng' : 'Điểm đi',
    end: isDelivery ? 'Điểm giao hàng' : 'Điểm đến',
    startTime: isDelivery ? 'Thời gian lấy hàng' : 'Thời gian đi',
    endTime: isDelivery ? 'Thời gian giao (dự kiến)' : 'Thời gian về (dự kiến)',
  }
}

export function VehicleBookingCreatePage() {
  const navigate = useNavigate()
  const createMutation = useCreateVehicleBooking()

  const [requestType, setRequestType] = useState<number>(REQUEST_TYPE.car)
  const isDelivery = requestType === REQUEST_TYPE.delivery
  const L = labelsFor(isDelivery)

  // Trường chung
  const [purpose, setPurpose] = useState('')
  const [startLocation, setStartLocation] = useState('Văn phòng Degoholding')
  const [endLocation, setEndLocation] = useState('')
  const [stops, setStops] = useState<string[]>([])
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [note, setNote] = useState('')

  // Đặt xe công tác
  const [passengerCount, setPassengerCount] = useState(1)
  const [attendees, setAttendees] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [isRoundTrip, setIsRoundTrip] = useState(false)

  // Giao hàng
  const [goodsName, setGoodsName] = useState('')
  const [goodsSize, setGoodsSize] = useState('')
  const [senderName, setSenderName] = useState('')
  const [senderPhone, setSenderPhone] = useState('')
  const [receiverName, setReceiverName] = useState('')
  const [receiverPhone, setReceiverPhone] = useState('')
  const [specialInstructions, setSpecialInstructions] = useState('')

  const [error, setError] = useState('')

  function setStopAt(index: number, value: string) {
    setStops((prev) => prev.map((s, i) => (i === index ? value : s)))
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

  function validate(): string {
    if (!purpose.trim()) return 'Vui lòng nhập mục đích.'
    if (isDelivery) {
      if (!goodsName.trim()) return 'Vui lòng nhập tên hàng hóa.'
      if (!senderName.trim() || !senderPhone.trim()) return 'Vui lòng nhập người gửi và SĐT.'
      if (!receiverName.trim() || !receiverPhone.trim()) return 'Vui lòng nhập người nhận và SĐT.'
    }
    return ''
  }

  function buildPayload(): VehicleBookingPayload {
    const cleanStops = stops.map((s) => s.trim()).filter(Boolean)
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

  function handleSubmit(submit: boolean) {
    const msg = validate()
    if (submit && msg) {
      setError(msg)
      return
    }
    setError('')
    createMutation.mutate(
      { payload: buildPayload(), submit },
      { onSuccess: () => navigate(appRoutes.vehicleBooking.root) },
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Tạo yêu cầu đặt xe"
        description="Chọn loại yêu cầu, điền lộ trình và thông tin — lưu nháp hoặc gửi duyệt."
      />

      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
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
        <Card className="flex flex-col gap-4 p-5">
          <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Thông tin chung
          </h3>

          <Field label="Mục đích" required>
            <Input
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              placeholder="VD: Đi thăm khách hàng quận 7"
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={L.start}>
              <Input value={startLocation} onChange={(e) => setStartLocation(e.target.value)} />
            </Field>
            <Field label={L.end}>
              <Input value={endLocation} onChange={(e) => setEndLocation(e.target.value)} />
            </Field>
          </div>

          {/* Điểm dừng trung gian */}
          <div className="flex flex-col gap-2">
            <Label>Điểm dừng trung gian</Label>
            {stops.length === 0 && (
              <p className="text-sm text-muted-foreground">Chưa có điểm dừng nào.</p>
            )}
            {stops.map((stop, index) => (
              <div key={index} className="flex items-center gap-2">
                <MapPin className="size-4 shrink-0 text-muted-foreground" />
                <Input
                  value={stop}
                  onChange={(e) => setStopAt(index, e.target.value)}
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
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-fit"
              onClick={() => setStops((prev) => [...prev, ''])}
            >
              <Plus className="size-4" />
              Thêm điểm dừng
            </Button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={L.startTime}>
              <Input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </Field>
            <Field label={L.endTime}>
              <Input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </Field>
          </div>
        </Card>

        {/* Khối riêng theo loại */}
        {isDelivery ? (
          <Card className="flex flex-col gap-4 p-5">
            <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Thông tin giao hàng
            </h3>
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
          </Card>
        ) : (
          <Card className="flex flex-col gap-4 p-5">
            <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Thông tin chuyến đi
            </h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Số hành khách">
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
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={isRoundTrip}
                onCheckedChange={(v) => setIsRoundTrip(v === true)}
              />
              Yêu cầu chuyến khứ hồi
            </label>
          </Card>
        )}

        {/* Ghi chú chung */}
        <Card className="flex flex-col gap-2 p-5">
          <Label>Ghi chú</Label>
          <Textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Ghi chú thêm cho điều phối viên (VD: cần xe 7 chỗ)."
          />
        </Card>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex items-center justify-end gap-2 pb-8">
          <Button
            variant="ghost"
            onClick={() => navigate(appRoutes.vehicleBooking.root)}
            disabled={createMutation.isPending}
          >
            Hủy
          </Button>
          <Button
            variant="outline"
            onClick={() => handleSubmit(false)}
            disabled={createMutation.isPending}
          >
            Lưu nháp
          </Button>
          <Button onClick={() => handleSubmit(true)} disabled={createMutation.isPending}>
            <Send className="size-4" />
            Gửi duyệt
          </Button>
        </div>
      </div>
    </PageContainer>
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
