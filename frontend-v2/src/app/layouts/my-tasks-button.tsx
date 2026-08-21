import { Inbox } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useMyTasks } from '@/modules/approval/hooks/use-approvals'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'

/**
 * HỘP VIỆC trên thanh trên — lối vào «Chờ tôi duyệt» từ bất kỳ đâu.
 *
 * Sidebar dựng theo TỪNG PHÂN HỆ: đứng trong Thu mua thì không thấy menu của
 * Văn bản. Nút này ở thanh trên (cạnh chuông thông báo) nên số việc đang chờ
 * theo người dùng đi khắp các phân hệ, không phải bấm logo về màn chọn phân hệ
 * mới biết mình còn phải ký gì.
 *
 * ⚠️ Trỏ tới **`/document/pending-approval`** chứ không còn `/approval/my-tasks`
 * (màn đó đã xóa 21/08/2026). Hiện chỉ Văn bản chạy bộ máy duyệt, nên đích này
 * phủ đúng mọi việc mà huy hiệu đang đếm. Ngày bật bộ máy cho Thu mua thì phải
 * xem lại: hoặc nút này dẫn tới hộp việc của phân hệ đang đứng, hoặc dựng lại
 * một màn gom chung — nhưng gom chung thì KHÔNG được có nút duyệt trên dòng.
 *
 * Số trên huy hiệu là **việc đang chờ CHÍNH người đăng nhập** — không có việc
 * nào thì không hiện số, nút vẫn còn để vào xem.
 */
export function MyTasksButton() {
  const { data } = useMyTasks()
  const dangCho = data?.total ?? 0

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          asChild
          variant="ghost"
          size="icon"
          className="relative text-muted-foreground hover:text-foreground"
        >
          <Link
            to={appRoutes.document.pendingApproval}
            aria-label={`Chờ tôi duyệt (${dangCho})`}
          >
            <Inbox className="size-5" />
            {dangCho > 0 && (
              //  Cùng hình dáng với huy hiệu của chuông để hai thứ đọc như một bộ.
              <span className="absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[0.625rem] font-semibold text-white">
                {dangCho > 9 ? '9+' : dangCho}
              </span>
            )}
          </Link>
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        {dangCho > 0 ? `Chờ tôi duyệt — ${dangCho} việc đang chờ` : 'Chờ tôi duyệt'}
      </TooltipContent>
    </Tooltip>
  )
}
