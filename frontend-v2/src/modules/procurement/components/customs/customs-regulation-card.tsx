import type { ReactNode } from 'react'

import {
  buildRegulationPesticideColumn,
  CUSTOMS_REGULATION_COLUMNS,
} from '../../config/customs-regulation-columns'
import type { CustomsRegulationHit } from '../../types/customs'

/**
 * Ô "Phụ lục / Văn bản" và "Ngưỡng / Mức cấm" lấy ĐÚNG hàm vẽ ô của bảng — luật tô màu theo mức
 * nghiêm trọng (cấm đỏ · ngưỡng kg cam · hỗn hợp chữ thường · không ngưỡng nghiêng mờ) đã chốt
 * qua nhiều lượt, chép ra một bản thứ hai là hai chỗ trôi khác nhau sau lần sửa tới.
 */
function renderColumnCell(key: string, row: CustomsRegulationHit): ReactNode {
  return CUSTOMS_REGULATION_COLUMNS.find((column) => column.key === key)?.cell(row) ?? null
}

interface CustomsRegulationCardProps {
  row: CustomsRegulationHit
  /**
   * Có thì bày dòng "Thuốc BVTV chứa" (chỉ bảng duyệt mục Pháp lý có số này); bấm số mở danh
   * sách thuốc. Thẻ cảnh báo theo từ khóa không truyền.
   */
  onOpenPesticides?: (row: CustomsRegulationHit) => void
}

/**
 * Một HÓA CHẤT THEO VĂN BẢN ở khổ điện thoại — dùng chung cho bảng duyệt mục Pháp lý (9 cột,
 * ~1.700px) và bảng cảnh báo theo từ khóa đang tra.
 *
 * ⚠️ **Tên chất lên đầu, tên khoa học / CAS / công thức xuống dòng phụ**: người thu mua tra
 * theo tên thường gọi; số CAS là để đối chiếu sau khi đã thấy đúng chất.
 *
 * ⚠️ **Mức cấm / ngưỡng đứng riêng một dòng ngay dưới văn bản** — con số quan trọng nhất của
 * dòng (bao-CR-477), không được chìm giữa câu "Lưu ý" dài.
 *
 * Hai bảng này không khai `onRowClick` nên thẻ là `<div>`; nút "N thuốc" vì vậy nằm được trong
 * thẻ mà không thành nút lồng trong nút.
 */
export function CustomsRegulationCard({ row, onOpenPesticides }: CustomsRegulationCardProps) {
  const title = row.name_vi || row.name
  const meta = [
    row.name_vi && row.name ? row.name : '',
    row.cas_no ? `CAS ${row.cas_no}` : '',
    row.formula,
  ].filter(Boolean)
  const limit = renderColumnCell('limit', row)
  const pesticides = onOpenPesticides
    ? buildRegulationPesticideColumn(onOpenPesticides).cell(row)
    : null

  return (
    <div className="space-y-1.5">
      <div className="flex items-start gap-2">
        <span className="min-w-0 flex-1 font-medium break-words text-foreground">
          {title || '—'}
        </span>
        {row.seq_no && (
          <span className="shrink-0 text-xs text-muted-foreground tabular-nums">STT {row.seq_no}</span>
        )}
      </div>

      {meta.length > 0 && (
        <p className="text-xs break-words text-muted-foreground">{meta.join(' · ')}</p>
      )}

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        {renderColumnCell('list_label', row)}
        {limit}
      </div>

      {row.obligation && <p className="text-xs break-words">{row.obligation}</p>}

      {pesticides && (
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
          Thuốc BVTV chứa: {pesticides}
        </div>
      )}
    </div>
  )
}
