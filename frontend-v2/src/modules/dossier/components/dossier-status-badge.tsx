import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import {
  DOSSIER_EXPIRY,
  DOSSIER_EXPIRY_LABEL,
  DOSSIER_STATUS,
  DOSSIER_STATUS_LABEL,
  type DossierExpiryState,
  type DossierStatus,
} from '../types/dossier'

/**
 * HAI huy hiệu, hai câu hỏi khác nhau — đừng gộp.
 *
 * *Tình trạng* trả lời «ai đó đã xếp hồ sơ này vào đâu» (nháp · đang lưu · lưu
 * trữ). *Hiệu lực* trả lời «tờ giấy còn giá trị không», và nó do NGÀY quyết
 * định chứ không do ai bấm nút. Một hồ sơ *Đang lưu* mà giấy đã hết hạn là
 * chuyện có thật và cần thấy ngay — gộp hai thứ vào một cột thì đúng ca ấy biến
 * mất.
 */

//  Màu dùng biến thể `dark:` vì bậc 600/700 quá tối trên nền tối — cùng luật
//  với `ErpModule.accent`.
const STATUS_CLASS: Record<DossierStatus, string> = {
  [DOSSIER_STATUS.DRAFT]: 'text-muted-foreground',
  [DOSSIER_STATUS.ACTIVE]: 'border-emerald-300 text-emerald-700 dark:text-emerald-400',
  [DOSSIER_STATUS.ARCHIVED]: 'border-slate-300 text-slate-600 dark:text-slate-400',
}

export function DossierStatusBadge({ status }: { status: DossierStatus }) {
  return (
    <Badge variant="outline" className={cn('font-medium', STATUS_CLASS[status])}>
      {DOSSIER_STATUS_LABEL[status]}
    </Badge>
  )
}

const EXPIRY_CLASS: Record<DossierExpiryState, string> = {
  //  *Vô thời hạn* để mờ: nó là trạng thái BÌNH THƯỜNG của rất nhiều giấy tờ
  //  (đăng ký doanh nghiệp, quyết định bổ nhiệm). Tô màu cho nó thì cả cột sáng
  //  đèn và hai dòng thật sự cần chú ý chìm mất.
  [DOSSIER_EXPIRY.NONE]: 'text-muted-foreground',
  [DOSSIER_EXPIRY.VALID]: 'border-emerald-300 text-emerald-700 dark:text-emerald-400',
  [DOSSIER_EXPIRY.NEAR]: 'border-amber-400 text-amber-700 dark:text-amber-400',
  [DOSSIER_EXPIRY.OVER]: 'border-destructive/40 text-destructive',
}

interface DossierExpiryBadgeProps {
  state: DossierExpiryState
  /** Số ngày còn lại; âm = đã quá hạn; `null` = vô thời hạn. */
  days: number | null
}

/**
 * Huy hiệu HIỆU LỰC, kèm số ngày khi nó nói thêm được điều gì.
 *
 * ⚠️ `state` và `days` đều do **backend** tính (`dossier/expiry.py`) — đừng so
 * `expiry_date` với hôm nay ở đây. Hai bản luật ngày tháng sẽ lệch nhau vào
 * đúng một ngày không ai để ý, mà bản lệch là bản người dùng nhìn.
 */
export function DossierExpiryBadge({ state, days }: DossierExpiryBadgeProps) {
  //  Chỉ nói số ngày ở hai mức cần hành động. «Còn hạn · 812 ngày» thì con số
  //  không đổi được quyết định nào, chỉ làm ô bảng dài thêm.
  const suffix =
    state === DOSSIER_EXPIRY.NEAR && days !== null
      ? ` · còn ${days} ngày`
      : state === DOSSIER_EXPIRY.OVER && days !== null
        ? ` · quá ${Math.abs(days)} ngày`
        : ''

  return (
    <Badge variant="outline" className={cn('font-medium', EXPIRY_CLASS[state])}>
      {DOSSIER_EXPIRY_LABEL[state]}
      {suffix}
    </Badge>
  )
}
