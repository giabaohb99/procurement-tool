import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { cn } from '@/shared/utils/cn'

interface PersonAvatarProps {
  /** Tên đầy đủ — cho `title` và chữ dự phòng. */
  name: string
  /** URL ảnh đại diện; rỗng / undefined = chưa có ảnh → vẽ chữ tắt. */
  avatar?: string | null
  /** Chữ tắt đã tính sẵn — mỗi chỗ có luật riêng (`nameInitials` / `initials`). */
  initials: string
  className?: string
  /** Chữ hiện khi rê chuột; mặc định là `name`. */
  title?: string
}

/**
 * Ảnh đại diện MỘT NGƯỜI trong phân hệ Dự án — bao-CR-482.
 *
 * Trước CR này mọi chỗ (thành viên dự án, thành viên nhóm, người phụ trách việc)
 * đều tự vẽ một vòng tròn chữ tắt, dù hồ sơ có ảnh: API không gửi ảnh, và thành
 * phần cũng không có chỗ nhận. Nay có ảnh thì hiện ảnh, không thì lùi về chữ tắt
 * — cùng một cách rơi như menu tài khoản ở góc phải (`user-menu.tsx`).
 *
 * Chữ tắt nhận từ ngoài chứ không tự tính: bảng dự án lấy hai chữ đầu của HAI
 * TỪ CUỐI (`nameInitials`), thẻ việc lấy hai chữ đầu của TỪ CUỐI (`initials`).
 * Hai luật đó có lý do riêng (xem từng util), gộp về một là đổi cách hiện của
 * cả một màn.
 */
export function PersonAvatar({ name, avatar, initials, className, title }: PersonAvatarProps) {
  return (
    <Avatar
      title={title ?? name}
      className={cn('size-6 border bg-accent text-[10px] font-medium text-accent-foreground', className)}
    >
      {avatar ? <AvatarImage src={avatar} alt={name} /> : null}
      <AvatarFallback className="bg-transparent text-inherit" aria-hidden>
        {initials}
      </AvatarFallback>
    </Avatar>
  )
}
