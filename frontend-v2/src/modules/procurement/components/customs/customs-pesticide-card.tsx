import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'

import {
  PESTICIDE_STATUS,
  type CustomsPesticide,
  type CustomsPesticideBrief,
} from '../../types/customs-pesticide'
import { CustomsPesticideStatusBadge } from './customs-pesticide-status-badge'

/**
 * Một thuốc: bản rút gọn (khối "Thuốc liên quan") có đủ trường của `CustomsPesticideBrief`;
 * bản đầy đủ (danh sách Thuốc BVTV, hộp "Thuốc BVTV chứa") có thêm số đăng ký, hạn, hàm lượng…
 */
type PesticideCardRow = CustomsPesticideBrief &
  Partial<
    Pick<
      CustomsPesticide,
      'concentration' | 'registration_no' | 'expires_on' | 'use_count' | 'is_manual' | 'banned'
    >
  >

interface CustomsPesticideCardProps {
  row: PesticideCardRow
  /** Tab "Cùng công ty": mọi thẻ cùng một công ty (tên đã đứng trên thanh công cụ) — bỏ cho đỡ lặp. */
  hideRegistrant?: boolean
  /**
   * Khối "Thuốc liên quan" chỉ gắn nhãn khi thuốc KHÔNG còn hiệu lực — y như cột của bảng ở đó:
   * hai chục nhãn xanh "Còn hiệu lực" xếp dọc thì nhãn đỏ "Hết hiệu lực" chìm mất.
   */
  hideActiveStatus?: boolean
}

/**
 * Một THUỐC BVTV ở khổ điện thoại — dùng chung cho ba bảng: danh sách Thuốc BVTV (11 cột),
 * hộp "Thuốc BVTV chứa" hoạt chất cấm, khối "Thuốc liên quan" của trang chi tiết thuốc.
 *
 * ⚠️ **Tên thuốc lên đầu, số đăng ký tụt xuống dòng phụ** — người tra nhớ tên thương mại, không
 * nhớ số đăng ký. Hoạt chất đứng ngay dưới vì nó quyết định thuốc này có phải thứ đang tìm.
 *
 * ⚠️ **Hoạt chất cấm là huy hiệu ĐỎ riêng một dòng**, không gộp vào dòng phụ: có chữ ở đó là
 * danh mục vừa lọt một thuốc phải xem lại, phải nhìn thấy trước mọi thứ khác.
 *
 * Cả ba bảng khai `onRowClick` (mở trang chi tiết thuốc) nên cả thẻ là một `<button>` — trong
 * thẻ không có nút, ruột dựng bằng `<span>`.
 */
export function CustomsPesticideCard({
  row,
  hideRegistrant = false,
  hideActiveStatus = false,
}: CustomsPesticideCardProps) {
  const ingredient = [row.active_ingredient, row.concentration].filter(Boolean).join(' · ')
  const meta = [
    hideRegistrant ? '' : row.registrant,
    row.registration_no ? `Số ĐK ${row.registration_no}` : '',
  ].filter(Boolean)
  const showStatus = !(hideActiveStatus && row.status === PESTICIDE_STATUS.active)
  const banned = row.banned ?? []

  return (
    <span className="block space-y-1.5">
      <span className="flex flex-wrap items-center gap-1.5">
        <span className="font-medium break-words text-foreground">{row.trade_name || '—'}</span>
        {row.is_manual && (
          <Badge variant="outline" className="text-[10px] font-normal">
            Tự thêm
          </Badge>
        )}
      </span>

      {ingredient && <span className="block text-sm break-words">{ingredient}</span>}

      {meta.length > 0 && (
        <span className="block text-xs break-words text-muted-foreground">{meta.join(' · ')}</span>
      )}

      {banned.length > 0 && (
        <span className="flex flex-wrap gap-1">
          {banned.map((item) => (
            <Badge key={item.id} className={cn('whitespace-normal', TONE_CLASS.danger)}>
              Cấm: {item.name}
            </Badge>
          ))}
        </span>
      )}

      <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
        {showStatus && <CustomsPesticideStatusBadge status={row.status} label={row.status_label} />}
        {row.pest_group && <span>{row.pest_group}</span>}
        {row.expires_on && (
          <span className="whitespace-nowrap tabular-nums">Hết hạn {formatDate(row.expires_on)}</span>
        )}
        {(row.use_count ?? 0) > 0 && (
          <span className="whitespace-nowrap tabular-nums">{row.use_count} phạm vi sử dụng</span>
        )}
      </span>
    </span>
  )
}
