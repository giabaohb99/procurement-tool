import type { CSSProperties } from 'react'
import type { PackagingImpactKpis } from '../../api/packaging-cost-types'
import { PKG_UP_COLOR } from '../../utils/packaging-price'
import { buildImpactSummaryCards } from '../../utils/packaging-print'
import type { ImpactSummaryCard, ImpactSummaryCardKey } from '../../utils/packaging-print'

/** Biểu tượng + màu nhấn của từng thẻ. Thẻ "Tăng nhiều nhất" xanh lá: chi phí TĂNG = xanh (luật màu của hệ). */
const LOOK: Record<ImpactSummaryCardKey, { icon: string; color: string }> = {
  selected: { icon: 'ti-list-check', color: '#2563eb' },
  affected: { icon: 'ti-packages', color: '#d97706' },
  'top-increase': { icon: 'ti-trending-up', color: PKG_UP_COLOR },
}

function CardBody({ card }: { card: ImpactSummaryCard }) {
  const look = LOOK[card.key]
  const toneStyle: CSSProperties | undefined = card.tone ? { color: PKG_UP_COLOR } : undefined
  //  Câu dài ("Không có sản phẩm tăng") hạ cỡ chữ như thẻ lịch sử, số thì to đậm.
  const long = card.value.length > 12
  return (
    <>
      <div className="pkg-stat-head">
        <span className="pkg-stat-ic" style={{ background: `${look.color}26`, color: look.color }}><i className={'ti ' + look.icon} /></span>
        <span className="pkg-stat-label">{card.label}</span>
        {card.product && <span className="pkg-stat-more"><i className="ti ti-sort-descending" />Xem</span>}
      </div>
      <div className="pkg-stat-row">
        <span className="pkg-stat-val" title={card.value} style={{ fontSize: long ? 15 : 24, ...(long ? { color: '#64748b' } : toneStyle) }}>{card.value}</span>
        {card.unit && <span className="pkg-stat-unit">{card.unit}</span>}
      </div>
      {(card.sub || card.detail) && (
        <div className="pkg-stat-sub">
          {card.sub && <span style={toneStyle}>{card.sub}</span>}
          {card.detail && <span title={card.detail}>{card.detail}</span>}
        </div>
      )}
    </>
  )
}

/**
 * duoc-CR-784 — ba THẺ NỔI đầu màn Tác động giá (người chủ chốt 23/11/2026: dòng chữ tóm tắt khó đọc, đổi sang thẻ như trang
 * Lịch sử mua hàng; chỉ ba thẻ này, không đưa lại "Sản phẩm tăng chi phí" / "giảm"). Số lấy từ `kpis` nên luôn tính trên TOÀN BỘ
 * tập bị ảnh hưởng. Thẻ "Tăng nhiều nhất /thùng" bấm được khi có sản phẩm tăng: `onShowTopIncrease` xếp bảng sản phẩm theo chênh
 * /thùng giảm dần và cuộn tới bảng.
 */
export default function PackagingImpactSummary({ kpis, filteredTotal, onShowTopIncrease }: {
  kpis: PackagingImpactKpis | undefined
  /** Số sản phẩm sau từ khóa / lọc nâng cao — CHỈ truyền khi đang lọc; thẻ "Sản phẩm bị ảnh hưởng" ghi "Đang lọc: x / M". */
  filteredTotal?: number
  onShowTopIncrease: () => void
}) {
  if (!kpis) return null
  return (
    <div className="pkg-stats three">
      {buildImpactSummaryCards(kpis, filteredTotal).map((card) => {
        const color = LOOK[card.key].color
        const style = { borderLeftColor: color, backgroundImage: `linear-gradient(135deg, ${color}12, transparent 60%)` }
        //  Có sản phẩm tăng → cả thẻ là một nút; không có thì chỉ là chữ (không giả vờ bấm được).
        return card.product ? (
          <button key={card.key} type="button" className="pkg-stat" style={style}
            title="Xếp bảng sản phẩm theo chênh lệch /thùng giảm dần và cuộn tới bảng" onClick={onShowTopIncrease}>
            <CardBody card={card} />
          </button>
        ) : (
          <div key={card.key} className="pkg-stat" style={style}><CardBody card={card} /></div>
        )
      })}
    </div>
  )
}
