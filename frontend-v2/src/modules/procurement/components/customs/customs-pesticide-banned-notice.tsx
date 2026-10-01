// Khung cảnh báo khi thuốc chứa hoạt chất CẤM theo TT 75/2025 (duoc-CR-489). Tách khỏi thẻ thông tin
// cũ khi làm lại bố cục trang chi tiết (01/10/2026).
import { OctagonAlert } from 'lucide-react'

import type { CustomsPesticideBanned } from '../../types/customs-pesticide'
import { formatBannedLabel } from '../../utils/customs'

/** Thuốc chứa hoạt chất trong danh sách CẤM (TT 75/2025) — đối chiếu theo tên, nói rõ là tham khảo. */
export function CustomsPesticideBannedNotice({ items }: { items: CustomsPesticideBanned[] }) {
  if (items.length === 0) return null
  return (
    <div
      role="alert"
      className="flex gap-3 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm"
    >
      <OctagonAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
      <div className="space-y-1">
        <p className="font-semibold text-destructive">Có hoạt chất nằm trong danh sách cấm</p>
        <ul className="space-y-0.5">
          {items.map((item) => (
            <li key={item.id}>
              <span className="font-medium">{item.name}</span>
              {item.cas_no && <span className="text-muted-foreground"> · CAS {item.cas_no}</span>}
              {' — '}
              {formatBannedLabel(item.banned_year)}
              {item.legal_basis && ` (${item.legal_basis})`}
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          Khớp theo tên hoạt chất giữa hai danh mục (không có số CAS để đối chiếu) — chỉ để tham
          khảo, xem lại văn bản gốc trước khi kết luận.
        </p>
      </div>
    </div>
  )
}
