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
    //  ⚠️ **Khổ hẹp phải CHO XUỐNG HÀNG, và đây là lỗi chặn chứ không phải
    //  chuyện thẩm mỹ.** Đủ bốn mục (tức đúng lúc CÓ việc quá hạn) thì dãy này
    //  rộng **411px** trong một thanh công cụ 324px; `shrink-0` giữ nó không co,
    //  mà cả trang lẫn thẻ đều không cuộn ngang — nên mép phải nút «Đã duyệt»
    //  nằm ở 441px trên màn 390px và **không có cách nào bấm tới**. Nút biến mất
    //  đúng vào ngày người ta bận nhất.
    //
    //  ⚠️ Gỡ `shrink-0` là điều kiện để `flex-wrap` có tác dụng: ô flex không co
    //  được thì nó tràn ra ngoài chứ không xuống hàng. Và `h-9` phải thành
    //  `min-h-9` — chiều cao ghim cộng với xuống hàng là cặp hỏng kinh điển
    //  (`TabsList` của Trang cá nhân, duoc-CR-367): hàng thứ hai tràn khỏi ô rồi
    //  bị khối bên dưới che mất, y như chưa sửa gì.
    //
    //  Ba mục (không có việc quá hạn) vẫn vừa MỘT hàng ở 390px — trường hợp
    //  thường ngày không đổi gì cả.
    <div className="inline-flex min-h-9 flex-wrap items-center gap-0.5 rounded-md border bg-muted/40 p-0.5 md:h-9 md:flex-nowrap md:shrink-0">
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
