import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { confirm } from '@/shared/ui/confirm-dialog'
import type { WorkShiftBody, WorkShiftBulkBody } from '../types/work-shift'
import { formatVnDate, toShiftErrorView, type ShiftErrorView } from '../utils/work-shift-errors'
import { useBulkWorkShift, useClearWorkShift, useSaveWorkShift } from './use-work-shifts'

interface WorkShiftSubmitOptions {
  employeeId: number
  fullName: string
  date: string
  /** Tra tên cho danh sách ô bị từ chối. */
  nameOf: (employeeId: number) => string | undefined
  /** Gọi sau mỗi lượt ghi thành công (đóng hộp). */
  onDone: () => void
}

/**
 * Ba lượt ghi của hộp xếp ca (duoc-CR-761): Lưu một ô · Về mẫu tuần · Áp cho nhiều ô. Gom một chỗ để chung MỘT chốt
 * chặn bấm đúp (`useRef` đổi ngay trong tick — luật biểu mẫu duoc-CR-317; `isPending` chỉ đúng ở lần render sau) và
 * MỘT cách bày lỗi trong hộp.
 */
export function useWorkShiftSubmit({ employeeId, fullName, date, nameOf, onDone }: WorkShiftSubmitOptions) {
  const save = useSaveWorkShift()
  const clear = useClearWorkShift()
  const bulk = useBulkWorkShift()
  const busy = useRef(false)
  const [error, setError] = useState<ShiftErrorView | null>(null)

  /** `held` = chốt đã được giữ từ trước (lúc hộp xác nhận đang mở) — không xét lại. */
  async function run(task: () => Promise<string>, held = false) {
    if (busy.current && !held) return
    busy.current = true
    setError(null)
    try {
      toast.success(await task())
      onDone()
    } catch (err) {
      //  PUT / DELETE: `http-client` đã toast câu lỗi; ghi lại trong hộp để còn đọc được khi toast đã tắt.
      setError(toShiftErrorView(err, nameOf))
    } finally {
      busy.current = false
    }
  }

  const saveCell = (body: WorkShiftBody) =>
    run(async () => {
      await save.mutateAsync({ employeeId, workDate: date, body })
      return body.segments.length === 0 ? 'Đã xếp nghỉ cả ngày' : 'Đã lưu ca'
    })

  const resetToTemplate = async () => {
    if (busy.current) return
    //  Giữ chốt suốt lúc hộp xác nhận mở: bấm "Về mẫu tuần" hai lần không mở hai hộp / gửi hai lệnh gỡ.
    busy.current = true
    const ok = await confirm({
      title: 'Về mẫu tuần',
      message: `Gỡ ca xếp riêng ngày ${formatVnDate(date)} của ${fullName}? Ngày này sẽ theo lại mẫu lịch tuần.`,
      confirmLabel: 'Về mẫu tuần',
    })
    if (!ok) {
      busy.current = false
      return
    }
    await run(async () => {
      await clear.mutateAsync({ employeeId, workDate: date })
      return 'Đã về mẫu tuần'
    }, true)
  }

  const applyBulk = (body: WorkShiftBulkBody) =>
    run(async () => {
      const res = await bulk.mutateAsync(body)
      const cells = body.employee_ids.length * body.dates.length
      return `Đã xếp ca cho ${cells} ô (thêm ${res.created}, cập nhật ${res.updated})`
    })

  return {
    pending: save.isPending || clear.isPending || bulk.isPending,
    error,
    saveCell,
    resetToTemplate,
    applyBulk,
  }
}
