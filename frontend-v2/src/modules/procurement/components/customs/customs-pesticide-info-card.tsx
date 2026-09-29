// Thẻ «Thông tin đăng ký» của trang chi tiết thuốc BVTV (duoc-CR-492) + khung cảnh báo khi thuốc
// chứa hoạt chất CẤM theo TT 75/2025 (duoc-CR-489). Chỉ đọc — sửa đi qua hộp «Sửa» của trang.
import { OctagonAlert } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import type { CustomsPesticide, CustomsPesticideBanned } from '../../types/customs-pesticide'
import { formatBannedLabel } from '../../utils/customs'

export function CustomsPesticideInfoCard({ pesticide }: { pesticide: CustomsPesticide }) {
  const manual = pesticide.is_manual
  const term =
    pesticide.registered_on || pesticide.expires_on
      ? `${formatDate(pesticide.registered_on)} – ${formatDate(pesticide.expires_on)}`
      : ''
  return (
    <Card className="gap-0">
      <CardHeader className="border-b pb-3">
        <CardTitle className="text-base">Thông tin đăng ký</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 pt-4">
        <dl className="grid gap-x-8 gap-y-4 text-sm sm:grid-cols-2 xl:grid-cols-3">
          <Field manual={manual} label="Hoạt chất" value={pesticide.active_ingredient} />
          <Field manual={manual} label="Hàm lượng" value={pesticide.concentration} />
          <Field manual={manual} label="Công ty đăng ký" value={pesticide.registrant} />
          <Field manual={manual} label="Số đăng ký" value={pesticide.registration_no} />
          <Field manual={manual} label="Thời hạn đăng ký" value={term} />
          <Field manual={manual} label="Phân nhóm" value={pesticide.pest_group} />
          <Field manual={manual} label="Lĩnh vực" value={pesticide.sector} />
          <Field manual={manual} label="Nhóm độc" value={pesticide.toxicity} />
          <Field manual={manual} label="Nhóm kháng (quản lý tính kháng)" value={pesticide.resistance} wide />
        </dl>
        {/*  duoc-CR-495 — câu mô tả của trang nguồn, DƯỚI lưới thông tin, ngăn bằng một vạch mảnh
             và nhãn cùng kiểu các ô khác (đại ca chốt 29/09: không khung màu, không viền trái). */}
        {pesticide.summary && (
          <div className="space-y-0.5 border-t pt-4 text-sm">
            <p className="text-xs text-muted-foreground">Tóm tắt sử dụng</p>
            <p className="leading-relaxed">{pesticide.summary}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/** Thuốc chứa hoạt chất trong danh sách CẤM (TT 75/2025) — đối chiếu theo tên, nói rõ là tham khảo. */
export function CustomsPesticideBannedNotice({ items }: { items: CustomsPesticideBanned[] }) {
  if (items.length === 0) return null
  return (
    <div role="alert" className="flex gap-3 rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm">
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

/**
 * Một cặp nhãn – giá trị. Trống thì ghi rõ, đừng để một ô trắng tưởng lỗi màn: thuốc từ bản cào
 * là «Nguồn không ghi», thuốc tự thêm là «Chưa nhập» (không có nguồn nào để mà «không ghi»).
 */
function Field({ label, value, manual, wide }: { label: string; value: string | null; manual: boolean; wide?: boolean }) {
  return (
    <div className={cn('min-w-0 space-y-0.5', wide && 'sm:col-span-2 xl:col-span-3')}>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={cn('font-medium break-words', !value && 'font-normal text-muted-foreground italic')}>
        {value || (manual ? 'Chưa nhập' : 'Nguồn không ghi')}
      </dd>
    </div>
  )
}
