import { useQuery } from '@tanstack/react-query'
import { FolderKanban } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { workApi } from '@/modules/work/api/work-api'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { queryKeys } from '@/shared/constants/query-keys'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import type { ReportExtraFiltersProps } from '../types/report-analytics'

const ALL_PROJECTS = 'all'

/**
 * Lọc riêng "dự án" của báo cáo Công việc (phase 06) — đọc/ghi `list_id` thẳng
 * trên URL (`useReportFilters.queryParams` gom mọi tham số thừa trên URL, nên
 * trang báo cáo chung không cần biết tên tham số riêng này là gì). Backend
 * (`work/report_rows.valid_scope_ids`) tự đối chiếu lại với `visible_list_ids`
 * — gửi id dự án không thấy được thì 403, ô chọn này chỉ là tiện ích.
 *
 * Gọi `useQuery` trực tiếp (không qua `modules/work/hooks/use-work-lists.ts`)
 * vì hook đó chưa có tham số `enabled` — thêm vào sẽ đụng một tệp ngoài phạm vi
 * sở hữu của phase này; dùng lại ĐÚNG khóa `queryKeys.work.lists(false)` để
 * trùng cache với mọi nơi khác đã gọi `useWorkLists(false)`.
 */
export function WorkReportProjectFilter(_props: ReportExtraFiltersProps) {
  const { can } = usePermission()
  const canReadWork = can('work_task', 'read')
  const [listId, setListId] = useUrlParamState('list_id', ALL_PROJECTS)
  const { data: lists } = useQuery({
    queryKey: queryKeys.work.lists(false),
    queryFn: () => workApi.lists(false),
    enabled: canReadWork,
  })

  if (!canReadWork) return null

  return (
    <Select value={listId} onValueChange={setListId}>
      <SelectTrigger className="w-auto min-w-44 max-md:min-w-0 max-md:flex-1" aria-label="Dự án">
        <FolderKanban className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        <SelectValue placeholder="Dự án" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL_PROJECTS}>Tất cả dự án</SelectItem>
        {lists?.map((item) => (
          <SelectItem key={item.id} value={String(item.id)}>
            {item.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
