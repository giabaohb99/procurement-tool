import { Navigate, useParams } from 'react-router-dom'

import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { appRoutes } from '@/shared/constants/app-routes'
import { useWorkTask } from '../hooks/use-work-board'

/**
 * Mở MỘT công việc theo id — trang trung chuyển cho link của chuông thông báo.
 *
 * Panel chi tiết không có route riêng (nó là một `Sheet` mở bằng state trong
 * trang dự án), nhưng chuông thì cần một địa chỉ dán được: khi ai đó nhắc tên
 * bạn trong bình luận, backend dựng link `{route}/{task_id}` với `route` lấy từ
 * `COMMENT_POLICY` — xem `core/comment_registry.py`.
 *
 * Người bấm chuông thường KHÔNG biết việc đó nằm ở dự án nào, nên trang này tra
 * `list_id` rồi mới dẫn tiếp, kèm `?task=` để dự án tự bung panel ra.
 *
 * Không có trang này thì cái chuông vẫn kêu nhưng bấm vào rơi vào màn 404 —
 * kiểu hỏng khó chịu nhất vì nó chỉ lộ ra sau khi tính năng đã lên thật.
 */
export function TaskRedirectPage() {
  const params = useParams()
  const taskId = Number(params.taskId ?? 0)
  const { data: task, isLoading, isError } = useWorkTask(taskId || undefined)

  if (isLoading) {
    return (
      <div className="space-y-3 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  //  403 cũng rơi vào đây: người bị gỡ khỏi dự án sau khi được nhắc tên vẫn còn
  //  cái chuông cũ trong danh sách. Nói thẳng ra thay vì đẩy họ về một trang
  //  trống không hiểu vì sao.
  if (isError || !task) {
    return (
      <ErrorState
        title="Không mở được công việc"
        description="Công việc không còn tồn tại, hoặc bạn không còn là thành viên của dự án chứa nó."
      />
    )
  }

  return <Navigate replace to={`${appRoutes.project.detail(task.list_id)}?task=${task.id}`} />
}
