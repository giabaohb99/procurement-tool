import { cn } from '@/shared/utils/cn'
import { useMyDocumentTasks } from '../hooks/use-my-document-approvals'

/**
 * Huy hiệu ĐỎ trên mục menu «Chờ tôi duyệt» — số văn bản đang chờ chính tôi.
 *
 * Thư báo (chuông) nói *có việc mới*; huy hiệu này nói *còn bao nhiêu việc chưa
 * làm*. Hai thứ khác nhau: thư đọc một lần rồi thôi, còn con số ở đây nằm đó tới
 * khi việc được xử lý xong — đó mới là thứ khiến người ta vào duyệt.
 *
 * Không có việc nào thì KHÔNG hiện gì. Một số 0 nằm trên menu cả ngày dạy người
 * dùng bỏ qua chỗ đó, và hôm nó thành số 3 thì mắt cũng lướt qua luôn.
 */
export function DocumentApprovalNavBadge() {
  const { items } = useMyDocumentTasks()
  if (items.length === 0) return null

  const overdue = items.some((row) => row.is_overdue)

  return (
    <span
      //  `ml-auto` do chính huy hiệu mang: mục menu là một hàng flex, đẩy từ đây
      //  thì tầng menu dùng chung không phải biết gì về huy hiệu.
      className={cn(
        'ml-auto rounded-full px-1.5 py-0.5 text-[0.6875rem] font-semibold',
        //  Có việc quá hạn thì đổi sang đỏ: cùng một con số nhưng gấp hơn hẳn.
        overdue ? 'bg-destructive text-white' : 'bg-primary text-primary-foreground',
      )}
      //  Đọc màn hình chỉ nghe "3" thì không biết 3 cái gì.
      aria-label={`${items.length} văn bản đang chờ bạn duyệt`}
    >
      {items.length > 99 ? '99+' : items.length}
    </span>
  )
}
