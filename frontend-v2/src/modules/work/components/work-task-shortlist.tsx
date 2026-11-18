import { ChevronRight, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import type { WorkOverviewTask } from '../hooks/use-work-overview'

interface WorkTaskShortlistProps {
  icon: LucideIcon
  title: string
  description: string
  tasks: WorkOverviewTask[]
  /** Tổng số việc thuộc nhóm này — dùng cho dòng "còn N việc nữa". */
  total: number
  loading?: boolean
  /** Câu nói khi không có việc nào. Phải là tin MỪNG, không phải "không có dữ liệu". */
  emptyMessage: string
  /** Tô đỏ ngày hạn — dùng cho nhóm quá hạn. */
  overdue?: boolean
}

/**
 * Danh sách RÚT GỌN vài việc trên màn Tổng quan Dự án.
 *
 * ⚠️ **Đây là ĐƯỜNG ĐI, không phải số liệu.** Thẻ đếm phía trên nói "22 việc
 * quá hạn" rồi dừng ở đó: người đọc biết mình đang có vấn đề nhưng không biết
 * vấn đề nằm ở đâu, và không có chỗ nào bấm vào — một cảnh báo không có lối ra.
 * Khối này là lối ra đó.
 *
 * ⚠️ **Chỉ tám dòng, và phải NÓI RA là còn nữa.** Đây là màn tổng quan, không
 * phải màn danh sách; tám dòng để nó còn là một lời mời đi tiếp chứ không thành
 * một bảng thứ hai. Nhưng cắt mà im lặng thì người đọc tưởng mình đã thấy hết —
 * nên khi `total` lớn hơn số dòng, chân khối ghi rõ còn bao nhiêu.
 *
 * ⚠️ **Câu rỗng là tin MỪNG.** "Không có việc quá hạn" khác hẳn "không có dữ
 * liệu": cái đầu nói mọi thứ đang đúng hạn, cái sau nói màn hình hỏng. Ở một
 * khối cảnh báo, để nhầm câu là người đọc đi tìm lỗi ở chỗ không có lỗi.
 */
export function WorkTaskShortlist({
  icon: Icon,
  title,
  description,
  tasks,
  total,
  loading = false,
  emptyMessage,
  overdue = false,
}: WorkTaskShortlistProps) {
  return (
    <Card className="gap-3">
      <CardHeader className="max-md:px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon className={cn('size-4', overdue ? 'text-destructive' : 'text-muted-foreground')} />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent className="max-md:px-4">
        <WorkTaskShortlistRows
          tasks={tasks}
          total={total}
          loading={loading}
          emptyMessage={emptyMessage}
          overdue={overdue}
        />
      </CardContent>
    </Card>
  )
}

type WorkTaskShortlistRowsProps = Pick<
  WorkTaskShortlistProps,
  'tasks' | 'total' | 'loading' | 'emptyMessage' | 'overdue'
> & {
  /** Ẩn tên dự án ở dòng phụ — trong báo cáo của MỘT dự án thì dòng nào cũng cùng tên, lặp lại chỉ tốn chỗ. */
  hideProject?: boolean
}

/**
 * Phần THÂN của danh sách rút gọn (dòng việc + câu rỗng + "còn N việc nữa"), không kèm khung thẻ — thẻ "Cần xử lý" ở
 * cột phải báo cáo từng dự án gom ba nhóm vào một khung có nút chuyển nên chỉ mượn phần này (duoc-CR-782).
 */
export function WorkTaskShortlistRows({
  tasks,
  total,
  loading = false,
  emptyMessage,
  overdue = false,
  hideProject = false,
}: WorkTaskShortlistRowsProps) {
  const remaining = total - tasks.length

  return (
    <>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : tasks.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <ul className="-mx-2 divide-y">
            {tasks.map((task) => (
              <li key={task.id}>
                {/*  Cả dòng là một liên kết: trên điện thoại vùng chạm phải rộng
                     bằng dòng chứ không bằng mấy chữ tiêu đề. Đích là route
                     trung chuyển `/project/tasks/:id` — nó tra dự án chứa việc
                     rồi mở đúng thẻ, vì panel chi tiết không có route riêng. */}
                {/*  duoc-CR-782: phạm vi "mọi dự án" có việc ở dự án người xem không là thành viên — mở ra là 403,
                     nên vẽ thành dòng thường, không phải link. */}
                {task.can_open === false ? (
                  <div
                    className="flex items-center gap-3 px-2 py-2.5"
                    title="Bạn chưa là thành viên dự án này nên chưa mở được việc"
                  >
                    <ShortlistRowText task={task} overdue={overdue} hideProject={hideProject} />
                    <span className="shrink-0 text-xs text-muted-foreground">chưa là thành viên</span>
                  </div>
                ) : (
                  <Link
                    to={appRoutes.project.task(task.id)}
                    className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/60"
                  >
                    <ShortlistRowText task={task} overdue={overdue} hideProject={hideProject} />
                    <ChevronRight className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  </Link>
                )}
              </li>
            ))}
          </ul>
        )}

        {remaining > 0 && (
          <p className="mt-2 text-xs text-muted-foreground">
            Còn {remaining.toLocaleString('vi-VN')} việc nữa — mở dự án để xem đủ.
          </p>
        )}
    </>
  )
}

/** Tên việc + dòng phụ (dự án · hạn · số ngày trễ · người giữ) — dùng chung cho dòng link và dòng không mở được. */
function ShortlistRowText({
  task,
  overdue,
  hideProject,
}: {
  task: WorkOverviewTask
  overdue: boolean
  hideProject: boolean
}) {
  //  Các mẩu dòng phụ nối bằng " · " — bỏ tên dự án thì mẩu đầu là hạn, không được mở đầu bằng dấu chấm giữa.
  const lead = hideProject ? '' : task.list_name
  const sep = lead ? ' · ' : ''
  return (
    <span className="min-w-0 flex-1">
      <span className="block truncate text-sm font-medium text-foreground">
        {task.title || '(Việc chưa đặt tên)'}
      </span>
      <span className="block truncate text-xs text-muted-foreground">
        {lead}
        {task.due_date && (
          <>
            {sep}
            <span className={cn(overdue && 'text-destructive')}>
              hạn {formatDate(task.due_date)}
            </span>
          </>
        )}
        {!task.due_date && `${sep}chưa đặt hạn`}
        {/*  duoc-CR-782: dòng quá hạn kèm số ngày trễ + người đang giữ — biết việc nào trễ mà
             không biết ai giữ thì vẫn phải mở từng thẻ để hỏi. */}
        {!!task.overdue_days && (
          <span className="text-destructive"> · trễ {task.overdue_days} ngày</span>
        )}
        {task.assignees &&
          (task.assignees.filter(Boolean).length
            ? ` · ${task.assignees.filter(Boolean).join(', ')}`
            : ' · chưa ai nhận')}
      </span>
    </span>
  )
}
