import { Send, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { DialogContent } from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { confirm } from '@/shared/ui/confirm-dialog'
import { SearchSelect, type SearchSelectOption } from '@/shared/ui/search-select'
import {
  useDispatchVehicleBooking,
  useDriverOptions,
  useVehicleOptions,
} from '../hooks/use-vehicle-bookings'
import type { VehicleBooking } from '../types/vehicle-booking'

interface BookingDispatchDialogProps {
  booking: VehicleBooking
  onClose: () => void
  onDispatched: () => void
}

const NONE = ''

export function BookingDispatchDialog({ booking, onClose, onDispatched }: BookingDispatchDialogProps) {
  const selfDrive = booking.is_self_drive
  const dispatchMutation = useDispatchVehicleBooking()
  const { data: vehicles, isLoading: vehiclesLoading } = useVehicleOptions()
  const { data: drivers, isLoading: driversLoading } = useDriverOptions()

  const [vehicleId, setVehicleId] = useState<string>(
    booking.assigned_vehicle_id ? String(booking.assigned_vehicle_id) : NONE,
  )
  const [driverId, setDriverId] = useState<string>(
    booking.assigned_driver_id ? String(booking.assigned_driver_id) : NONE,
  )
  const [error, setError] = useState('')

  const initial = `${booking.assigned_vehicle_id ?? ''}|${booking.assigned_driver_id ?? ''}`
  const dirty = `${vehicleId}|${driverId}` !== initial
  const pending = dispatchMutation.isPending

  //  Chỉ đổ xe/tài xế ĐANG SẴN SÀNG vào ô chọn: xe bảo trì/ngưng dùng và tài xế nghỉ
  //  phép/nghỉ việc không phân được. Vẫn giữ lại đúng cái ĐANG được phân (dù trạng thái
  //  đã đổi) để ô hiện đúng lựa chọn hiện tại khi điều phối lại, không bị trống.
  const vehicleOptions: SearchSelectOption[] = (vehicles?.items ?? [])
    .filter((v) => v.status === 'available' || v.id === booking.assigned_vehicle_id)
    .map((v) => ({
      value: String(v.id),
      label: `${v.license_plate || '—'}${v.type ? ` — ${v.type}` : ''}`,
    }))
  const driverOptions: SearchSelectOption[] = (drivers?.items ?? [])
    .filter((d) => d.status === 'available' || d.id === booking.assigned_driver_id)
    .map((d) => ({
      value: String(d.id),
      label: `${d.name}${d.phone ? ` · ${d.phone}` : ''}`,
    }))

  async function attemptClose() {
    if (pending) return
    if (dirty && !(await confirm({ message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?' }))) return
    onClose()
  }

  function handleSubmit() {
    if (!vehicleId) {
      setError('Vui lòng chọn xe.')
      return
    }
    if (!selfDrive && !driverId) {
      setError('Vui lòng chọn tài xế.')
      return
    }
    setError('')
    dispatchMutation.mutate(
      {
        id: booking.id,
        assigned_vehicle_id: Number(vehicleId),
        //  Tự lái: người yêu cầu là tài xế → không gán tài xế.
        assigned_driver_id: selfDrive ? 0 : Number(driverId),
      },
      { onSuccess: onDispatched },
    )
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
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        className="sm:max-w-[600px]"
      >
        <DialogHeader className="flex-row items-start justify-between text-left">
          <div>
            <DialogTitle>Điều phối {booking.code}</DialogTitle>
            <DialogDescription>
              {selfDrive ? 'Chuyến tự lái — chỉ cần chọn 1 xe.' : 'Chọn 1 xe và 1 tài xế cho phiếu này.'}
            </DialogDescription>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={attemptClose} aria-label="Đóng">
            <X className="size-4" />
          </Button>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          <div className="flex flex-col gap-1.5">
            <Label>
              Xe
              <RequiredMark />
            </Label>
            <SearchSelect
              value={vehicleId}
              onChange={setVehicleId}
              options={vehicleOptions}
              disabled={vehiclesLoading}
              searchInTrigger
              placeholder={vehiclesLoading ? 'Đang tải…' : 'Chọn xe'}
              searchPlaceholder="Gõ biển số / loại xe…"
              emptyMessage="Không có xe phù hợp."
            />
          </div>

          {selfDrive ? (
            //  Tự lái: tài xế KHÓA = người yêu cầu (không chọn).
            <div className="flex flex-col gap-1.5">
              <Label>Tài xế</Label>
              <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
                {booking.requester || '—'} <span className="text-muted-foreground">(tự lái)</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Chuyến tự lái — người yêu cầu là tài xế, không cần chọn.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-1.5">
              <Label>
                Tài xế
                <RequiredMark />
              </Label>
              <SearchSelect
                value={driverId}
                onChange={setDriverId}
                options={driverOptions}
                disabled={driversLoading}
                searchInTrigger
                placeholder={driversLoading ? 'Đang tải…' : 'Chọn tài xế'}
                searchPlaceholder="Gõ tên / số điện thoại…"
                emptyMessage="Không có tài xế phù hợp."
              />
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" onClick={attemptClose} disabled={pending}>
            Hủy
          </Button>
          <Button onClick={handleSubmit} disabled={pending}>
            <Send className="size-4" />
            Điều phối
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
