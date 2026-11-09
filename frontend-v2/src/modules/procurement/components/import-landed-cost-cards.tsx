import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import {
  CardList,
  CostTypeFigures,
  EmptyMessage,
  Figure,
  Figures,
  TotalCard,
} from './import-landed-cost-card-parts'
import type {
  LandedCostAmounts,
  LandedCostItemRow,
  LandedCostItemTotals,
  LandedCostOrderRow,
  LandedCostReport,
  LandedCostType,
} from '../types/import-landed-cost'

/**
 * Báo cáo giá vốn nhập khẩu ở khổ điện thoại — thay cho hai bảng của
 * `import-landed-cost-tables.tsx` (bảng xoay ~520 + 130px mỗi lô, bảng dòng hàng
 * ~1280 + 130px mỗi loại chi phí).
 *
 * ⚠️ **Chỉ tab báo cáo đổi sang thẻ, trang in giữ bảng**: bản in ra giấy A4 nằm
 * ngang, không có khổ điện thoại; hai nơi vẫn đọc chung một bộ số từ backend.
 *
 * ⚠️ **Bảng xoay thành MỖI LÔ MỘT THẺ**: trên máy hẹp không thể so ngang nhiều cột,
 * nên đổi trục — mỗi thẻ là một cột cũ, chỉ tiêu xếp dọc. Cột TỔNG thành thẻ cuối.
 *
 * ⚠️ **Loại chi phí bằng 0 không in** trong thẻ: bảng phải giữ đủ cột cho thẳng hàng,
 * thẻ thì mỗi số 0 là một dòng nhiễu. Tổng chi phí vẫn in đủ nên không mất số.
 */

/** Phần số liệu chung của thẻ một lô và thẻ TỔNG — cùng thứ tự với các hàng của bảng xoay. */
function AmountFigures({ row, types }: { row: LandedCostAmounts; types: LandedCostType[] }) {
  return (
    <Figures>
      <Figure label="Số lượng" value={formatQuantity(row.qty_total)} />
      <Figure label="Khối lượng (kg)" value={formatQuantity(row.weight_total)} />
      {/*  Nhiều đồng tiền thì cộng nguyên tệ là sai (backend trả 0) — bỏ hẳn dòng. */}
      {row.currency_mixed ? (
        <Figure label="Đồng tiền" value="Nhiều loại" />
      ) : (
        <Figure
          label={`Tiền hàng (${row.currency || 'nguyên tệ'})`}
          value={formatUnitPrice(row.goods_amount)}
        />
      )}
      <Figure label="1. Tiền hàng (vnd)" value={formatMoney(row.goods_base)} />
      <Figure label="2. Chi phí nhập khẩu (vnd)" value={formatMoney(row.cost_total)} />
      <CostTypeFigures types={types} byType={row.by_type} />
      <Figure label="Tổng giá vốn (vnd)" value={formatMoney(row.landed_total)} strong />
      <Figure label="Giá vốn/Kg (vnd)" value={formatUnitPrice(row.price_per_kg)} />
    </Figures>
  )
}

function LandedCostOrderCard({
  order,
  types,
}: {
  order: LandedCostOrderRow
  types: LandedCostType[]
}) {
  const decl = [
    order.customs_decl_no && `TK ${order.customs_decl_no}`,
    formatDate(order.customs_decl_date),
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <div className="space-y-1.5 p-3">
      <p className="line-clamp-2 font-medium text-foreground">
        {order.supplier_name || order.supplier_code || '(chưa có NCC)'}
      </p>
      <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">
          {order.code || `#${order.po_id}`}
        </span>
        {[formatDate(order.order_date), order.status_label].filter(Boolean).map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </p>
      {(order.etd_date || decl) && (
        <p className="text-xs text-muted-foreground">
          {[order.etd_date && `ETD ${formatDate(order.etd_date)}`, decl]
            .filter(Boolean)
            .join(' · ')}
        </p>
      )}
      {/*  Tỷ giá là của TỪNG lô nên chỉ thẻ lô có, thẻ TỔNG không. */}
      {order.exchange_rate > 0 && (
        <p className="text-xs text-muted-foreground tabular-nums">
          Tỷ giá {formatUnitPrice(order.exchange_rate)}
        </p>
      )}
      <AmountFigures row={order} types={types} />
      {order.note && <p className="text-xs text-muted-foreground">{order.note}</p>}
    </div>
  )
}

/** Cách nhìn THEO LÔ HÀNG ở khổ hẹp: mỗi lô một thẻ, thẻ TỔNG ở cuối. */
export function LandedCostOrderCards({ data }: { data: LandedCostReport }) {
  if (data.orders.length === 0)
    return <EmptyMessage message="Không có đơn nhập khẩu nào trong phạm vi đã chọn." />

  return (
    <CardList>
      {data.orders.map((order) => (
        <LandedCostOrderCard key={order.po_id} order={order} types={data.cost_types} />
      ))}
      <TotalCard title={`TỔNG (${data.orders.length} lô)`}>
        <AmountFigures row={data.totals} types={data.cost_types} />
      </TotalCard>
    </CardList>
  )
}

function LandedCostItemCard({
  item,
  index,
  types,
}: {
  item: LandedCostItemRow
  index: number
  types: LandedCostType[]
}) {
  return (
    <div className="flex items-start gap-2 p-3">
      <span className="shrink-0 text-xs leading-5 text-muted-foreground tabular-nums">
        {index + 1}.
      </span>
      <div className="min-w-0 flex-1 space-y-1.5">
        <p className="line-clamp-2 font-medium text-foreground">
          {item.product_name || item.product_code || '(chưa đặt tên)'}
        </p>
        <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
          <span className="font-medium text-sky-600 dark:text-sky-400">
            {item.product_code || '—'}
          </span>
          {[item.code, item.etd_date && `ETD ${formatDate(item.etd_date)}`]
            .filter(Boolean)
            .map((text) => (
              <span key={text}>
                <span aria-hidden="true">· </span>
                {text}
              </span>
            ))}
        </p>
        <ItemFigures row={item} types={types} unit={item.unit} />
      </div>
    </div>
  )
}

/** Số liệu của một dòng hàng hoặc dòng TỔNG — cùng thứ tự với các cột của bảng phẳng. */
function ItemFigures({
  row,
  types,
  unit,
}: {
  row: LandedCostItemRow | LandedCostItemTotals
  types: LandedCostType[]
  unit?: string
}) {
  return (
    <Figures>
      <Figure
        label={unit ? `Số lượng (${unit})` : 'Số lượng'}
        value={formatQuantity(row.qty_order)}
      />
      <Figure label="Khối lượng (kg)" value={formatQuantity(row.weight_kg)} />
      <Figure label="Tiền hàng (vnd)" value={formatMoney(row.goods_base)} />
      <CostTypeFigures types={types} byType={row.by_type} />
      <Figure label="Tổng chi phí (vnd)" value={formatMoney(row.cost_base)} />
      <Figure label="Tổng giá vốn (vnd)" value={formatMoney(row.landed_base)} strong />
      {/*  Giá vốn/ĐVT KHÔNG có ở dòng tổng: mỗi dòng một đơn vị tính. */}
      {'price_per_unit' in row && (
        <Figure label="Giá vốn/ĐVT (vnd)" value={formatUnitPrice(row.price_per_unit)} strong />
      )}
      <Figure label="Giá vốn/Kg (vnd)" value={formatUnitPrice(row.price_per_kg)} />
    </Figures>
  )
}

/** Cách nhìn THEO DÒNG HÀNG ở khổ hẹp: mỗi dòng hàng một thẻ, thẻ TỔNG ở cuối. */
export function LandedCostItemCards({ data }: { data: LandedCostReport }) {
  if (data.items.length === 0)
    return <EmptyMessage message="Không có dòng hàng nào trong phạm vi đã chọn." />

  return (
    <CardList>
      {data.items.map((item, index) => (
        <LandedCostItemCard
          key={`${item.po_id}-${item.item_id}`}
          item={item}
          index={index}
          types={data.cost_types}
        />
      ))}
      <TotalCard title={`TỔNG (${data.item_totals.line_count} dòng)`}>
        <ItemFigures row={data.item_totals} types={data.cost_types} />
      </TotalCard>
    </CardList>
  )
}
