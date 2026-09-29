// Cột bảng hóa chất theo văn bản — dùng chung cho mục «Pháp lý» (bảng duyệt cả danh mục) và thẻ
// cảnh báo theo từ khóa. Tách từ `customs-legal-tab.tsx` cũ khi mục «Pháp lý & thuế» chia đôi
// thành «Pháp lý» và «Thuế» (29/09/2026).
import type { DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import type { CustomsRegulationHit } from '../types/customs'
import { formatBannedLabel, formatThresholdKg } from '../utils/customs'

/**
 * bao-CR-477 — tông huy hiệu theo MỨC NGHIÊM TRỌNG (xem `regulationSeverity`): cấm và tiền chất
 * vũ khí hóa học = đỏ · có ngưỡng khối lượng = cam · phải công bố theo lô (thủ tục, không phải
 * giới hạn) = xanh · chỉ có tên trong danh mục = xám. Trước đây mọi thứ ngoài «cấm» và «ngưỡng»
 * đều xanh, nên tiền chất vũ khí hóa học trông nhẹ ngang một thủ tục công bố.
 */
/** Mã danh sách — khớp `RegulationList` ở `backend/app/modules/customs/constants.py`. */
const LIST_BANNED_TT75 = 10
const LIST_ND24_PL3 = 3
const LIST_ND24_PL4 = 4
const LIST_PUBLISH_TT01 = 11

const THRESHOLD_TONE = 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300'

function regulationTone(listCode: number): string {
  if (listCode === LIST_BANNED_TT75 || listCode === LIST_ND24_PL3) return TONE_CLASS.danger
  if (listCode === LIST_ND24_PL4) return THRESHOLD_TONE
  if (listCode === LIST_PUBLISH_TT01) return TONE_CLASS.progress
  return TONE_CLASS.neutral
}

export const CUSTOMS_REGULATION_COLUMNS: DataTableColumn<CustomsRegulationHit>[] = [
  {
    key: 'list_label',
    header: 'Danh mục',
    width: 230,
    hideable: false,
    wrap: true,
    cell: (r) => (
      <Badge className={cn('whitespace-normal', regulationTone(r.list_code))}>
        {r.list_label || `Danh sách ${r.list_code}`}
      </Badge>
    ),
  },
  {
    key: 'name',
    header: 'Tên',
    width: 260,
    hideable: false,
    wrap: true,
    cell: (r) => (
      <span>
        {r.name}
        {r.name_vi && r.name_vi !== r.name && (
          <span className="block text-xs text-muted-foreground">{r.name_vi}</span>
        )}
      </span>
    ),
  },
  { key: 'cas_no', header: 'Số CAS', width: 120, hideable: false, cell: (r) => r.cas_no },
  //  bao-CR-477 — con số quan trọng nhất của dòng đứng thành CỘT RIÊNG, chữ to đậm; trước
  //  đây nó nằm lẫn giữa một câu chữ thường ở cột «Lưu ý», đọc lướt là trôi mất.
  {
    key: 'limit',
    header: 'Ngưỡng / Mức cấm',
    width: 150,
    hideable: false,
    cell: (r) => {
      if (r.list_code === LIST_BANNED_TT75) {
        return (
          <Badge className={cn('font-bold', TONE_CLASS.danger)}>
            {formatBannedLabel(r.banned_year)}
          </Badge>
        )
      }
      const threshold = formatThresholdKg(r.threshold_kg)
      if (!threshold) return null
      return (
        <span className="text-base font-bold tabular-nums text-orange-700 dark:text-orange-300">
          {threshold}
        </span>
      )
    },
  },
  {
    key: 'obligation',
    header: 'Lưu ý',
    width: 360,
    hideable: false,
    wrap: true,
    cell: (r) => r.obligation,
  },
]

/**
 * Cột «Thuốc BVTV chứa» — chỉ ở bảng duyệt mục «Pháp lý» (thẻ cảnh báo theo từ khóa không có
 * số này). Chỉ dòng TT 75 có số; `null` ở dòng TT 75 = danh mục thuốc CHƯA nạp, phải nói ra thay
 * vì hiện «0» (đọc thành «đã đối chiếu, không thuốc nào»). Tên cấm không rút ra được khóa so
 * khớp nào (chữ tiếng Việt có dấu…) cũng phải nói ra, cùng lý do. Bấm số → danh sách thuốc đó.
 */
export function buildRegulationPesticideColumn(
  onOpen: (row: CustomsRegulationHit) => void,
): DataTableColumn<CustomsRegulationHit> {
  return {
    key: 'pesticide_count',
    header: 'Thuốc BVTV chứa',
    width: 150,
    wrap: true,
    cell: (r) => {
      if (r.list_code !== LIST_BANNED_TT75) return null
      if (r.pesticide_matchable === false) {
        return <span className="text-xs text-muted-foreground italic">Tên không đối chiếu được</span>
      }
      if (r.pesticide_count === null || r.pesticide_count === undefined) {
        return <span className="text-xs text-muted-foreground italic">Chưa nạp danh mục thuốc</span>
      }
      if (r.pesticide_count === 0) return <span className="tabular-nums text-muted-foreground">0</span>
      return (
        <Button
          type="button"
          variant="link"
          className="h-auto p-0 font-semibold tabular-nums text-destructive"
          onClick={(event) => {
            event.stopPropagation()
            onOpen(r)
          }}
        >
          {r.pesticide_count.toLocaleString('vi-VN')} thuốc
        </Button>
      )
    },
  }
}
