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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  useDispatchVehicleBooking,
  useDriverOptions,
  useVehicleOptions,
} from '../hooks/use-vehicle-bookings'
import { VEHICLE_STATUS_LABELS } from '../types/vehicle'
import { DRIVER_STATUS_LABELS } from '../types/driver'
import type { VehicleBooking } from '../types/vehicle-booking'

interface BookingDispatchDialogProps {
  booking: VehicleBooking
  onClose: () => void
  onDispatched: () => void
}

const NONE = ''

export function BookingDispatchDialog({ booking, onClose, onDispatched }: BookingDispatchDialogProps) {
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

  function attemptClose() {
    if (pending) return
    if (dirty && !window.confirm('Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?')) return
    onClose()
  }

  function handleSubmit() {
    if (!vehicleId || !driverId) {
      setError('Vui lòng chọn cả xe và tài xế.')
      return
    }
    setError('')
    dispatchMutation.mutate(
      { id: booking.id, assigned_vehicle_id: Number(vehicleId), assigned_driver_id: Number(driverId) },
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
        className="sm:max-w-md"
      >
        <DialogHeader className="flex-row items-start justify-between text-left">
          <div>
            <DialogTitle>Điều phối {booking.code}</DialogTitle>
            <DialogDescription>Chọn 1 xe và 1 tài xế cho phiếu này.</DialogDescription>
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
            <Select value={vehicleId} onValueChange={setVehicleId} disabled={vehiclesLoading}>
              <SelectTrigger>
                <SelectValue placeholder={vehiclesLoading ? 'Đang tải…' : 'Chọn xe'} />
              </SelectTrigger>
              <SelectContent>
                {(vehicles?.items ?? []).map((v) => (
                  <SelectItem key={v.id} value={String(v.id)}>
                    {v.license_plate}
                    {v.model ? ` — ${v.model}` : ''}
                    {` · ${VEHICLE_STATUS_LABELS[v.status] ?? v.status}`}
                    {v.is_external ? ' · Thuê ngoài' : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label>
              Tài xế
              <RequiredMark />
            </Label>
            <Select value={driverId} onValueChange={setDriverId} disabled={driversLoading}>
              <SelectTrigger>
                <SelectValue placeholder={driversLoading ? 'Đang tải…' : 'Chọn tài xế'} />
              </SelectTrigger>
              <SelectContent>
                {(drivers?.items ?? []).map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    {d.name}
                    {d.phone ? ` · ${d.phone}` : ''}
                    {` · ${DRIVER_STATUS_LABELS[d.status] ?? d.status}`}
                    {d.is_external ? ' · Thuê ngoài' : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

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
