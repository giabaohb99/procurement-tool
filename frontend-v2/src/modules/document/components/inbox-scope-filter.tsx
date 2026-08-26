import { cn } from '@/shared/utils/cn'
import { INBOX_SCOPE, type InboxScope } from './approval-inbox-row'

interface InboxScopeFilterProps {
  value: string
  onChange: (value: InboxScope) => void
  pendingCount: number
  overdueCount: number
  approvedCount: number
}

/**
 * Ô lọc nhanh của hộp duyệt: **Tất cả · Cần duyệt · Quá hạn · Đã duyệt**.
 *
 * Là dãy nút liền nhau chứ không phải ô chọn xổ xuống, vì hai lẽ:
 *
 * 1. **Con số phải nhìn thấy mà không cần bấm.** Câu hỏi mỗi sáng là "còn bao
 *    nhiêu việc" — giấu con số sau một cú bấm là bắt người ta thao tác mới biết
 *    thứ đáng lẽ hiện sẵn.
 * 2. Chỉ có bốn lựa chọn, luôn cùng bộ. Ô chọn xổ xuống hợp khi danh sách dài
 *    hoặc thay đổi theo dữ liệu; ở đây nó chỉ thêm một lớp che.
 *
 * Mục **Quá hạn** chỉ hiện khi thật sự có việc quá hạn — bày một nút luôn bằng 0
 * là dạy người dùng bỏ qua chỗ đó, rồi hôm nó thành 3 thì mắt cũng lướt qua.
 */
export function InboxScopeFilter({
  value,
  onChange,
  pendingCount,
  overdueCount,
  approvedCount,
}: InboxScopeFilterProps) {
  const muc: { value: InboxScope; label: string; count: number; gap?: boolean }[] = [
    { value: INBOX_SCOPE.all, label: 'Tất cả', count: pendingCount + approvedCount },
    { value: INBOX_SCOPE.pending, label: 'Cần duyệt', count: pendingCount },
    ...(overdueCount > 0
      ? [{ value: INBOX_SCOPE.overdue, label: 'Quá hạn', count: overdueCount, gap: true }]
      : []),
    { value: INBOX_SCOPE.done, label: 'Đã duyệt', count: approvedCount },
  ]

  return (
    <div className="inline-flex h-9 shrink-0 items-center gap-0.5 rounded-md border bg-muted/40 p-0.5">
      {muc.map((item) => {
        const selection = value === item.value
        return (
          <button
            key={item.value}
            type="button"
            //  `aria-pressed` chứ không phải `role="tab"`: đây là bộ lọc trên
            //  một bảng, không phải mấy trang nội dung thay nhau hiện ra.
            aria-pressed={selection}
            onClick={() => onChange(item.value)}
            className={cn(
              'flex h-8 items-center gap-1.5 rounded-sm px-2.5 text-sm whitespace-nowrap transition-colors',
              selection
                ? 'bg-background font-medium text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {item.label}
            <span
              className={cn(
                'rounded-full px-1.5 py-0.5 text-[0.6875rem] font-semibold tabular-nums',
                //  Số việc quá hạn tô đỏ ở mọi trạng thái nút: mức gấp gáp không
                //  phụ thuộc vào chỗ này có đang được chọn hay không.
                item.gap
                  ? 'bg-destructive text-white'
                  : selection
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground',
              )}
            >
              {item.count}
            </span>
          </button>
        )
      })}
    </div>
  )
}
