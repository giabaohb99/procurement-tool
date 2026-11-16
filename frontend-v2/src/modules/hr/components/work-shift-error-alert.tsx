import { TriangleAlert } from 'lucide-react'

import type { ShiftErrorView } from '../utils/work-shift-errors'

/** Lỗi của lượt ghi hàng loạt trong hộp thoại: câu chính + danh sách ô bị từ chối (đích danh người · ngày · lý do). */
export function WorkShiftErrorAlert({ error }: { error: ShiftErrorView }) {
  return (
    <div role="alert" className="flex gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm">
      <TriangleAlert aria-hidden className="mt-0.5 size-4 shrink-0 text-destructive" />
      <div className="min-w-0 space-y-1">
        <p className="font-medium text-destructive">{error.message}</p>
        {error.lines.length > 0 && (
          <ul className="list-disc space-y-0.5 pl-4 text-foreground">
            {error.lines.map((line, i) => (
              <li key={i} className="break-words">
                {line}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
