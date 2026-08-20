import { Inbox } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useMyTasks } from '@/modules/approval/hooks/use-approvals'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip'

/**
 * HỘP VIỆC trên thanh trên — lối vào «Việc của tôi» từ bất kỳ đâu.
 *
 * Sidebar dựng theo TỪNG PHÂN HỆ: đứng trong Văn thư chỉ thấy menu của Văn thư.
 * Mà «Việc của tôi» lại nằm ở phân hệ **Phê duyệt**, nên từ trang chi tiết văn
 * bản không có đường nào tới nó — phải bấm logo về màn chọn phân hệ rồi mới vào
 * được. Người dùng báo đúng: *"có đâu nè"*.
 *
 * Hộp việc là thứ **dùng chung** (gom việc của cả văn thư lẫn thu mua), nên chỗ
 * của nó là thanh trên cạnh chuông thông báo, không phải trong menu một phân hệ.
 * Cùng lý do mà chuông thông báo đứng ở đó chứ không nằm trong phân hệ nào.
 *
 * Số trên huy hiệu là **việc đang chờ CHÍNH người đăng nhập** — không có việc
 * nào thì không hiện số, nút vẫn còn để vào xem lịch sử.
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
          <Link to={appRoutes.approval.myTasks} aria-label={`Việc của tôi (${dangCho})`}>
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
        {dangCho > 0 ? `Việc của tôi — ${dangCho} việc đang chờ` : 'Việc của tôi'}
      </TooltipContent>
    </Tooltip>
  )
}
