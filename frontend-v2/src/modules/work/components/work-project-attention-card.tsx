import { ListChecks } from 'lucide-react'
import { useState } from 'react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'

import type { WorkOverview } from '../hooks/use-work-overview'
import { WorkTaskShortlistRows } from './work-task-shortlist'

type AttentionKey = 'overdue' | 'unassigned' | 'noDue'

interface AttentionGroup {
  key: AttentionKey
  label: string
  description: string
  emptyMessage: string
}

const GROUPS: AttentionGroup[] = [
  {
    key: 'overdue',
    label: 'Quá hạn',
    description: 'Trễ lâu nhất lên đầu, kèm số ngày trễ và người đang giữ.',
    emptyMessage: 'Không có việc nào quá hạn.',
  },
  {
    key: 'unassigned',
    label: 'Chưa nhận',
    description: 'Việc đang mở không có người phụ trách.',
    emptyMessage: 'Việc nào cũng đã có người nhận.',
  },
  {
    key: 'noDue',
    label: 'Chưa hạn',
    description: 'Không có hạn thì không bao giờ quá hạn. Việc tạo lâu nhất lên đầu.',
    emptyMessage: 'Việc nào cũng đã có hạn.',
  },
]

/** Lấy danh sách + tổng của từng nhóm từ dữ liệu báo cáo. */
function getGroupTasks(data: WorkOverview | undefined, key: AttentionKey) {
  if (key === 'overdue') return { tasks: data?.overdue_tasks ?? [], total: data?.task_overdue ?? 0 }
  if (key === 'unassigned') return { tasks: data?.unassigned_tasks ?? [], total: data?.task_unassigned ?? 0 }
  return { tasks: data?.no_due_tasks ?? [], total: data?.task_no_due ?? 0 }
}

/**
 * Thẻ CẦN XỬ LÝ ở cột phải báo cáo từng dự án (duoc-CR-782) — gom ba danh sách "Quá hạn / Chưa nhận / Chưa hạn" vào một
 * khung có nút chuyển kèm số đếm. Cột phải hẹp, xếp ba thẻ chồng nhau là cột phải dài gấp ba cột trái.
 *
 * Mở sẵn nhóm ĐẦU TIÊN có việc: dự án không trễ gì thì mở ra thấy ngay việc chưa ai nhận, không phải một câu "không có
 * việc quá hạn" rồi bắt người xem tự đi bấm.
 */
export function WorkProjectAttentionCard({ data, isLoading }: { data: WorkOverview | undefined; isLoading: boolean }) {
  const [picked, setPicked] = useState<AttentionKey | null>(null)
  const firstWithTasks = GROUPS.find((g) => getGroupTasks(data, g.key).total > 0)?.key ?? 'overdue'
  const active = picked ?? firstWithTasks
  const group = GROUPS.find((g) => g.key === active) ?? GROUPS[0]
  const { tasks, total } = getGroupTasks(data, active)

  return (
    <Card className="gap-3">
      <CardHeader className="px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <ListChecks className="size-4 text-muted-foreground" />
          Cần xử lý
        </CardTitle>
        <CardDescription>{group.description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 px-4">
        <div role="group" aria-label="Nhóm việc cần xử lý" className="grid grid-cols-3 gap-1 rounded-lg bg-muted p-0.5">
          {GROUPS.map((g) => {
            const count = getGroupTasks(data, g.key).total
            const on = g.key === active
            return (
              <button
                key={g.key}
                type="button"
                aria-pressed={on}
                onClick={() => setPicked(g.key)}
                //  Số trên, nhãn dưới: cột phải chỉ ~90px mỗi nút, "Chưa nhận 0" xếp một hàng là gãy đôi.
                className={cn(
                  'flex flex-col items-center rounded-md px-1 py-1.5 transition-colors',
                  on ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground',
                )}
              >
                <span
                  className={cn(
                    'text-base leading-tight font-semibold tabular-nums',
                    g.key === 'overdue' && count > 0 && 'text-destructive',
                  )}
                >
                  {count.toLocaleString('vi-VN')}
                </span>
                <span className="text-xs whitespace-nowrap">{g.label}</span>
              </button>
            )
          })}
        </div>
        <WorkTaskShortlistRows
          tasks={tasks}
          total={total}
          loading={isLoading}
          emptyMessage={group.emptyMessage}
          overdue={active === 'overdue'}
          hideProject
        />
      </CardContent>
    </Card>
  )
}
