import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import {
  useWorkOverviewPersonTasks,
  type WorkOverviewPerson,
  type WorkOverviewPersonTask,
} from '../hooks/use-work-overview'

interface WorkOverviewPersonTasksDialogProps {
  person: WorkOverviewPerson | null
  onClose: () => void
}

/**
 * Hộp VIỆC ĐANG MỞ của một người, mở từ bảng đối chiếu theo người của màn Tổng quan Dự án (duoc-CR-782): quá hạn
 * trước, rồi theo hạn gần nhất; bấm một việc là mở thẳng thẻ việc đó. Chỉ gồm việc trong phạm vi màn Tổng quan.
 */
export function WorkOverviewPersonTasksDialog({ person, onClose }: WorkOverviewPersonTasksDialogProps) {
  const { data, isLoading, isError } = useWorkOverviewPersonTasks(person?.employee_id ?? null)

  return (
    <Dialog open={person !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Việc đang mở của {person?.name || 'nhân sự'}</DialogTitle>
          <DialogDescription>
            {person
              ? `${person.open.toLocaleString('vi-VN')} việc đang mở, ${person.overdue.toLocaleString('vi-VN')} việc quá hạn. Quá hạn lên đầu.`
              : ''}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : isError ? (
          <p className="py-6 text-center text-sm text-destructive">Không tải được danh sách việc. Thử mở lại.</p>
        ) : !data?.length ? (
          <p className="py-6 text-center text-sm text-muted-foreground">Người này không còn việc nào đang mở.</p>
        ) : (
          <ul className="-mx-2 max-h-[60vh] divide-y overflow-y-auto">
            {data.map((task) => (
              <li key={task.id}>
                {task.can_open ? (
                  <Link
                    to={appRoutes.project.task(task.id)}
                    onClick={onClose}
                    className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/60"
                  >
                    <PersonTaskText task={task} />
                    <ChevronRight className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  </Link>
                ) : (
                  //  Không là thành viên dự án chứa việc: mở ra là 403, nên không dẫn link (duoc-CR-782).
                  <div
                    className="flex items-center gap-3 px-2 py-2.5"
                    title="Bạn chưa là thành viên dự án này nên chưa mở được việc"
                  >
                    <PersonTaskText task={task} />
                    <span className="shrink-0 text-xs text-muted-foreground">chưa là thành viên</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
        {data && data.length >= 50 && (
          <p className="text-xs text-muted-foreground">Hiện 50 việc đầu — mở dự án để xem đủ.</p>
        )}
      </DialogContent>
    </Dialog>
  )
}

function PersonTaskText({ task }: { task: WorkOverviewPersonTask }) {
  return (
    <span className="min-w-0 flex-1">
      <span className="block truncate text-sm font-medium">{task.title || '(Việc chưa đặt tên)'}</span>
      <span className="block truncate text-xs text-muted-foreground">
        {task.list_name}
        {' · '}
        <span className={cn(task.overdue && 'font-medium text-destructive')}>
          {task.due_date ? `hạn ${formatDate(task.due_date)}` : 'chưa đặt hạn'}
          {task.overdue && ' (quá hạn)'}
        </span>
      </span>
    </span>
  )
}
