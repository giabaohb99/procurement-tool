import { Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'

interface JobPositionRoleCardProps {
  name: string
  code: string
  /** Bỏ trống = người xem không có `role.write` — thẻ không có nút bỏ, đúng như bảng ẩn cột đó. */
  onRemove?: () => void
}

/**
 * Một vai trò trong gói "Quyền mặc định" của chức vụ, khổ điện thoại (duoc-CR-721).
 *
 * Bảng chỉ có hai cột (Vai trò · Mã) nhưng cột Mã khai `w-40` cứng, nên trong khung 322px tên vai
 * trò dài bị ép xuống ba bốn hàng. Thẻ đặt tên lên đầu, mã xuống dòng phụ (sky, chữ đơn cách như
 * bảng), nút bỏ đứng cạnh làm vùng chạm riêng — thẻ không bấm được nên không lồng nút vào nút.
 *
 * Bỏ vai trò chỉ sửa BẢN NHÁP; phải bấm Lưu mới ghi — giống hệt nút thùng rác của bảng.
 */
export function JobPositionRoleCard({ name, code, onRemove }: JobPositionRoleCardProps) {
  return (
    <div className="flex items-start gap-2 p-3">
      <div className="min-w-0 flex-1 space-y-0.5">
        <p className="truncate font-medium text-foreground">{name}</p>
        {code && <p className="truncate font-mono text-xs text-sky-600 dark:text-sky-400">{code}</p>}
      </div>
      {onRemove && (
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="shrink-0 text-destructive hover:text-destructive"
          aria-label={`Bỏ vai trò ${name} khỏi gói`}
          title="Bỏ vai trò khỏi gói"
          onClick={onRemove}
        >
          <Trash2 />
        </Button>
      )}
    </div>
  )
}
