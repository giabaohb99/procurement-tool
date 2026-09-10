import type { ReactNode } from 'react'

import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import type {
  LandedCostAmounts,
  LandedCostOrderRow,
  LandedCostReport,
} from '../types/import-landed-cost'

/**
 * Bốn khối dựng nên báo cáo giá vốn lô hàng nhập khẩu (bao-CR-357).
 *
 * Tab trong màn Báo cáo mua hàng và trang in dùng CHUNG mấy khối này — giống hệt
 * cách bản v1 làm — để hai nơi không bao giờ hiện ra hai bảng khác nhau.
 *
 * Vì sao KHÔNG dùng `DataTable`: bảng đầu là bảng XOAY (mỗi lô hàng một CỘT, chỉ
 * tiêu nằm ở hàng) còn bảng sau có số cột do dữ liệu quyết định (mỗi loại chi phí
 * một cột) — cả hai đều ngoài khuôn "một dòng một bản ghi" của `DataTable`. Đây
 * là ngoại lệ đã có tiền lệ ở `report-metric-table.tsx`.
 */

/**
 * Kiểu dáng của hai bảng.
 *
 * Màu đi qua BIẾN CSS có giá trị dự phòng: trang in để nguyên giá trị dự phòng
 * (mã màu cứng, vì bản in ra giấy không có chế độ tối và không ăn theo bảng màu
 * người dùng chọn), còn trên màn hình thì `.lc-scope` gán lại bằng token của
 * giao diện nên bảng vẫn đúng nền sáng/tối và đúng bảng màu đang dùng.
 */
export const LANDED_COST_TABLE_STYLES = `
.lc-table { border-collapse: collapse; width: 100%; font-size: 12.5px; line-height: 1.35; }
.lc-table--compact { font-size: 10.5px; }
.lc-table th, .lc-table td { border: 1px solid var(--lc-border, #b8c4d0); padding: 4px 8px; }
.lc-table thead th {
  background: var(--lc-head-bg, #eef3f7);
  color: var(--lc-head-fg, inherit);
  font-weight: 600;
  text-align: left;
  vertical-align: bottom;
}
.lc-table .lc-num { text-align: right; white-space: nowrap; }
.lc-table .lc-label { width: 240px; }
.lc-table .lc-bold { font-weight: 700; }
.lc-table .lc-semibold { font-weight: 600; }
.lc-table .lc-sub { padding-left: 22px; font-weight: 400; }
.lc-table .lc-total { background: var(--lc-total-bg, #f4f7fa); }
.lc-table thead .lc-total { background: var(--lc-total-head-bg, #e4edf5); }
.lc-table .lc-accent { background: var(--lc-accent-bg, #fff8e6); }
.lc-table thead .lc-accent { background: var(--lc-accent-head-bg, #fff3cd); }
.lc-scope {
  --lc-border: var(--border);
  --lc-head-bg: var(--row-head);
  --lc-head-fg: var(--row-head-foreground);
  --lc-total-bg: var(--muted);
  --lc-total-head-bg: var(--row-head);
  --lc-accent-bg: color-mix(in oklab, var(--warning) 10%, var(--card));
  --lc-accent-head-bg: color-mix(in oklab, var(--warning) 22%, var(--card));
}
`

interface LandedCostTableProps {
  data: LandedCostReport
  /** Bản in: chữ nhỏ lại để lọt bề ngang khổ A4 nằm ngang. */
  compact?: boolean
}

/** Một cột của bảng xoay: hoặc một lô hàng, hoặc cột TỔNG. */
interface PivotColumn {
  title: string
  row: LandedCostAmounts
  order?: LandedCostOrderRow
  isTotal?: boolean
}

/**
 * Cách nhìn THEO LÔ HÀNG — bảng xoay: mỗi lô một cột, mỗi chỉ tiêu một hàng.
 *
 * Xoay vì số chỉ tiêu cố định (~16) còn số lô hàng thì ít, và người đọc cần so
 * ngang từng chỉ tiêu giữa các lô.
 */
export function LandedCostPivotTable({ data, compact }: LandedCostTableProps) {
  const columns: PivotColumn[] = data.orders.map((order) => ({
    title: order.code || `#${order.po_id}`,
    row: order,
    order,
  }))
  if (columns.length > 0) {
    columns.push({ title: 'TỔNG', row: data.totals, isTotal: true })
  }

  if (columns.length === 0) return <LandedCostEmpty message="Không có đơn nhập khẩu nào trong phạm vi đã chọn." />

  //  Hàng chỉ có nghĩa với TỪNG LÔ (ngày đặt, nhà cung cấp, tờ khai…): cột TỔNG
  //  để trống chứ không cộng, gộp bảy mã tờ khai lại thì đọc ra thứ vô nghĩa.
  const orderRow = (
    label: string,
    get: (order: LandedCostOrderRow) => ReactNode,
    options?: { num?: boolean },
  ) => (
    <tr key={label}>
      <th scope="row" className="lc-label lc-semibold">
        {label}
      </th>
      {columns.map((column) => (
        <td
          key={column.title}
          className={cn(options?.num && 'lc-num', column.isTotal && 'lc-total')}
        >
          {column.order ? get(column.order) : ''}
        </td>
      ))}
    </tr>
  )

  const amountRow = (
    label: string,
    get: (row: LandedCostAmounts) => ReactNode,
    options?: { bold?: boolean; no?: string },
  ) => (
    <tr key={label}>
      <th scope="row" className={cn('lc-label', options?.bold ? 'lc-bold' : 'lc-semibold')}>
        {options?.no ? `${options.no}. ${label}` : label}
      </th>
      {columns.map((column) => (
        <td
          key={column.title}
          className={cn('lc-num', options?.bold && 'lc-bold', column.isTotal && 'lc-total')}
        >
          {get(column.row)}
        </td>
      ))}
    </tr>
  )

  return (
    <div className="overflow-x-auto">
      <table
        className={cn('lc-table', compact && 'lc-table--compact')}
        style={{ minWidth: 520 + columns.length * 130 }}
      >
        <thead>
          <tr>
            <th className="lc-label">Chỉ tiêu</th>
            {columns.map((column) => (
              <th key={column.title} className={cn('lc-num', column.isTotal && 'lc-total')}>
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {orderRow('Ngày đặt hàng', (order) => formatDate(order.order_date))}
          {orderRow('Nhà cung cấp', (order) => order.supplier_name || order.supplier_code)}
          {orderRow('Trạng thái', (order) => order.status_label)}
          {orderRow('Ngày hàng rời cảng (ETD)', (order) => formatDate(order.etd_date))}
          {orderRow('Số tờ khai hải quan', (order) => order.customs_decl_no)}
          {orderRow('Ngày tờ khai', (order) => formatDate(order.customs_decl_date))}
          {orderRow('Ghi chú', (order) => order.note)}
          {amountRow('Số lượng', (row) => formatQuantity(row.qty_total))}
          {amountRow('Khối lượng (kg)', (row) => formatQuantity(row.weight_total))}
          {amountRow('Đồng tiền', (row) => (row.currency_mixed ? 'Nhiều loại' : row.currency))}
          {amountRow('Tiền hàng (nguyên tệ)', (row) =>
            //  Nhiều đồng tiền thì cộng nguyên tệ lại là sai — backend trả 0, ở đây
            //  để TRỐNG hẳn cho khỏi ai đọc số 0 đó thành "không mua gì".
            row.currency_mixed ? '' : formatUnitPrice(row.goods_amount),
          )}
          {/* Tỷ giá là của TỪNG lô — cột TỔNG bỏ trống, bình quân tỷ giá không có nghĩa. */}
          {orderRow('Tỷ giá', (order) => formatUnitPrice(order.exchange_rate), { num: true })}
          {amountRow('Tiền hàng (vnd)', (row) => formatMoney(row.goods_base), {
            bold: true,
            no: '1',
          })}
          {amountRow('Chi phí nhập khẩu (vnd)', (row) => formatMoney(row.cost_total), {
            bold: true,
            no: '2',
          })}
          {data.cost_types.map((costType) => (
            <tr key={costType.code}>
              <th scope="row" className="lc-label lc-sub">
                {costType.no}. {costType.label}
              </th>
              {columns.map((column) => (
                <td
                  key={column.title}
                  className={cn('lc-num', column.isTotal && 'lc-total')}
                >
                  {formatMoney(column.row.by_type?.[String(costType.code)] || 0)}
                </td>
              ))}
            </tr>
          ))}
          {amountRow('Tổng giá vốn (vnd)', (row) => formatMoney(row.landed_total), { bold: true })}
          {amountRow('Giá vốn/Kg (vnd)', (row) => formatUnitPrice(row.price_per_kg), {
            bold: true,
          })}
        </tbody>
      </table>
    </div>
  )
}

/** Cách nhìn THEO DÒNG HÀNG — bảng phẳng, mỗi loại chi phí một cột. */
export function LandedCostItemTable({ data, compact }: LandedCostTableProps) {
  const costTypes = data.cost_types
  const totals = data.item_totals

  if (data.items.length === 0)
    return <LandedCostEmpty message="Không có dòng hàng nào trong phạm vi đã chọn." />

  return (
    <div className="overflow-x-auto">
      <table
        className={cn('lc-table', compact && 'lc-table--compact')}
        style={{ minWidth: 1280 + costTypes.length * 130 }}
      >
        <thead>
          <tr>
            <th className="lc-num">STT</th>
            <th>Mã đơn</th>
            <th>Ngày ETD</th>
            <th>Mã hàng</th>
            <th>Tên hàng</th>
            <th>ĐVT</th>
            <th className="lc-num">Số lượng</th>
            <th className="lc-num">Khối lượng (kg)</th>
            <th className="lc-num">Tiền hàng (vnd)</th>
            {costTypes.map((costType) => (
              <th key={costType.code} className="lc-num">
                {costType.label}
              </th>
            ))}
            <th className="lc-num">Tổng chi phí (vnd)</th>
            <th className="lc-num lc-total">Tổng giá vốn (vnd)</th>
            <th className="lc-num lc-accent">Giá vốn/ĐVT (vnd)</th>
            <th className="lc-num">Giá vốn/Kg (vnd)</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((item, index) => (
            <tr key={`${item.po_id}-${item.item_id}`}>
              <td className="lc-num">{index + 1}</td>
              <td>{item.code}</td>
              <td>{formatDate(item.etd_date)}</td>
              <td>{item.product_code}</td>
              <td>{item.product_name}</td>
              <td>{item.unit}</td>
              <td className="lc-num">{formatQuantity(item.qty_order)}</td>
              <td className="lc-num">{formatQuantity(item.weight_kg)}</td>
              <td className="lc-num">{formatMoney(item.goods_base)}</td>
              {costTypes.map((costType) => (
                <td key={costType.code} className="lc-num">
                  {formatMoney(item.by_type?.[String(costType.code)] || 0)}
                </td>
              ))}
              <td className="lc-num">{formatMoney(item.cost_base)}</td>
              <td className="lc-num lc-semibold lc-total">{formatMoney(item.landed_base)}</td>
              <td className="lc-num lc-bold lc-accent">{formatUnitPrice(item.price_per_unit)}</td>
              <td className="lc-num">{formatUnitPrice(item.price_per_kg)}</td>
            </tr>
          ))}
          <tr className="lc-bold">
            <th scope="row" colSpan={6} className="lc-bold">
              TỔNG ({totals.line_count} dòng)
            </th>
            <td className="lc-num">{formatQuantity(totals.qty_order)}</td>
            <td className="lc-num">{formatQuantity(totals.weight_kg)}</td>
            <td className="lc-num">{formatMoney(totals.goods_base)}</td>
            {costTypes.map((costType) => (
              <td key={costType.code} className="lc-num">
                {formatMoney(totals.by_type?.[String(costType.code)] || 0)}
              </td>
            ))}
            <td className="lc-num">{formatMoney(totals.cost_base)}</td>
            <td className="lc-num lc-total">{formatMoney(totals.landed_base)}</td>
            {/* Giá vốn/ĐVT KHÔNG có dòng tổng: mỗi dòng một đơn vị tính. */}
            <td className="lc-accent" />
            <td className="lc-num">{formatUnitPrice(totals.price_per_kg)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

/**
 * Lưu ý khi chia chi phí về dòng hàng.
 *
 * Backend gửi kèm những chỗ nó phải ĐOÁN (thiếu khối lượng, thiếu tỷ giá…) — đây
 * là số liệu tính ra chứ không phải số ghi sổ, giấu mấy dòng này là để người đọc
 * tin nhầm vào một con số suy diễn.
 */
export function LandedCostWarnings({ data }: { data: LandedCostReport }) {
  if (!data.warnings?.length) return null
  return (
    <div
      className="rounded-md border p-3 text-[13px]"
      style={{
        background: 'var(--lc-accent-bg, #fff8e6)',
        borderColor: 'var(--lc-accent-head-bg, #f0d68a)',
      }}
    >
      <div className="mb-1 font-semibold">Lưu ý khi chia chi phí về dòng hàng:</div>
      <ul className="list-disc space-y-0.5 pl-5">
        {data.warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
    </div>
  )
}

const SIGNATURE_ROLES = ['Người lập biểu', 'Kế toán', 'Quản lý duyệt']

/** Ba ô ký ở cuối bản in. */
export function LandedCostSignatures() {
  return (
    <div className="mt-8 grid grid-cols-3 gap-4 text-center text-[12.5px]">
      {SIGNATURE_ROLES.map((role) => (
        <div key={role}>
          <div className="font-semibold">{role}</div>
          <div className="italic">(Ký, ghi rõ họ tên)</div>
          <div style={{ height: 62 }} />
        </div>
      ))}
    </div>
  )
}

function LandedCostEmpty({ message }: { message: string }) {
  return <div className="py-8 text-center text-[13px] text-muted-foreground">{message}</div>
}
