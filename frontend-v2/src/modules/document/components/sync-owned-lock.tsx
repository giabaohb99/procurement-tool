import type { ReactNode } from 'react'

/**
 * Khóa MỘT ô của form khi giá trị do nơi khác sở hữu — vd tiêu đề / tóm tắt / ngày hiệu lực của BẢN LƯU TRỮ hợp đồng
 * lao động do hợp đồng ở Nhân sự đồng bộ (duoc-CR-640). `fieldset disabled` khóa mọi ô bên trong bằng cơ chế trình
 * duyệt; `contents` để không phá lưới bố cục.
 */
export function SyncOwnedLock({ locked, children }: { locked: boolean; children: ReactNode }) {
  if (!locked) return <>{children}</>
  return (
    <fieldset disabled className="contents" data-sync-owned>
      {children}
    </fieldset>
  )
}
