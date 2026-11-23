/**
 * duoc-CR-784 — các khối của bản in Lịch sử mua hàng, dựng theo bản mẫu HTML: ô lọc + dòng thông tin, biểu đồ đơn giá (đường
 * xanh lá đậm, chấm trắng viền xanh, chấm cuối xanh dương kèm số, đúng hàm `drawChart` của bản mẫu), bảng lần mua đầu navy.
 *
 * Số liệu + khuôn định dạng dùng lại đúng hàm của màn hình (`buildHistorySummary`, `formatPackagingPrice`...) nên bản in không
 * lệch con số với màn. Biểu đồ là SVG tĩnh (không phải recharts): recharts đo khung bằng JS lúc chạy, đổi sang khổ giấy có thể
 * ra biểu đồ sai cỡ hoặc rỗng.
 */
import { PACKAGING_ROLE, PRICE_SOURCE_TYPE_CODE } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'

import type {
  PackagingHistoryMode,
  PackagingHistoryPoint,
  PackagingHistoryRow,
} from '../types/packaging-cost-types'
import {
  formatPackagingDiff,
  formatPackagingPercent,
  formatPackagingPrice,
} from '../utils/packaging-price-format'
import { PrintChipsBox, PrintDash } from './packaging-print-widgets'

const ROLE_LABEL = new Map(PACKAGING_ROLE.map((role) => [Number(role.value), role.label]))

interface PrintHistoryFiltersProps {
  mode: PackagingHistoryMode
  codes: readonly string[]
  /** Dòng "CET0028 — tên · nhóm · ĐVT" khi đúng một mã; rỗng thì tự nói "Đã chọn N mã" / "Tất cả". */
  first: PackagingHistoryRow | undefined
  singleCode: boolean
  /** Các điều kiện còn lại đang bật (NCC, khoảng ngày, từ khóa) — từ `describeHistoryFilters`. */
  extras: readonly string[]
}

/** Khối ô lọc: hai chip chế độ + ô mã + dòng thông tin (cùng cấu trúc `.filters` + `.info` của bản mẫu). */
export function PrintHistoryFilters({ mode, codes, first, singleCode, extras }: PrintHistoryFiltersProps) {
  const isProduct = mode === 'product'
  const scope =
    singleCode && first ? (
      <>
        <b>{first.code}</b> — {first.name || '(chưa có tên)'}
        {first.group && ` · ${first.group}`}
        {first.unit && ` · ĐVT ${first.unit}`}
      </>
    ) : codes.length ? (
      <>
        Đã chọn <b>{codes.length}</b> {isProduct ? 'sản phẩm' : 'mã'}
      </>
    ) : (
      <b>{isProduct ? 'Tất cả sản phẩm có định mức' : 'Tất cả mã hàng'}</b>
    )
  return (
    <div className="panel">
      <div className="pfilters">
        <div className="field">
          <label>Xem theo</label>
          <div className="chips">
            <span className={isProduct ? 'chip' : 'chip on'}>Mã VTBB</span>
            <span className={isProduct ? 'chip on' : 'chip'}>Mã sản phẩm</span>
          </div>
        </div>
        <div className="field ms">
          <label>
            {isProduct
              ? 'Mã sản phẩm — để trống = tất cả sản phẩm có định mức'
              : 'Mã vật tư — để trống = tất cả mã hàng'}
          </label>
          <PrintChipsBox codes={codes} emptyText="Tất cả" />
        </div>
      </div>
      <div className="info">
        {scope}
        {extras.map((extra) => ` · ${extra}`).join('')}
      </div>
    </div>
  )
}

const CHART = { width: 1000, height: 200, left: 52, right: 14, top: 16, bottom: 30 }

/** "30/06/2026" -> "30/06/26" — nhãn trục ngày của bản mẫu. */
function shortDate(iso: string): string {
  const full = formatDate(iso)
  return full.length === 10 ? `${full.slice(0, 6)}${full.slice(8)}` : full
}

/** Biểu đồ "Diễn biến đơn giá qua các lần mua (VNĐ)": các lần mua CÓ GIÁ của đúng một mã, cũ -> mới. */
export function PrintPriceChart({ series }: { series: readonly PackagingHistoryPoint[] }) {
  if (series.length === 0) return null
  const { width: W, height: H, left, right, top, bottom } = CHART
  const prices = series.map((point) => point.price)
  const low = Math.min(...prices)
  const high = Math.max(...prices)
  const pad = (high - low) * 0.15 || high * 0.05 || 1
  const y0 = Math.max(0, low - pad)
  const y1 = high + pad
  const x = (i: number) =>
    series.length === 1 ? (left + W - right) / 2 : left + (i * (W - left - right)) / (series.length - 1)
  const y = (value: number) => top + (H - top - bottom) * (1 - (value - y0) / (y1 - y0))
  const lastIndex = series.length - 1
  const path = series.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.price).toFixed(1)}`).join(' ')
  const step = Math.max(1, Math.ceil(series.length / 10))
  return (
    <div className="panel chart">
      <h4>Diễn biến đơn giá qua các lần mua (VNĐ)</h4>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Diễn biến đơn giá">
        {[y0, (y0 + y1) / 2, y1].map((value) => (
          <g key={value}>
            <line x1={left} x2={W - right} y1={y(value)} y2={y(value)} stroke="#EEF1F5" />
            <text x={left - 8} y={y(value) + 4} textAnchor="end" fontSize="11" fill="#8C939C">
              {Math.round(value).toLocaleString('vi-VN')}
            </text>
          </g>
        ))}
        <path d={path} fill="none" stroke="#0B6A3A" strokeWidth="2.2" />
        {series.map((point, i) => (
          <circle
            key={i}
            cx={x(i)}
            cy={y(point.price)}
            r={i === lastIndex ? 5 : 3.5}
            fill={i === lastIndex ? '#00AEEF' : '#fff'}
            stroke={i === lastIndex ? '#00AEEF' : '#0B6A3A'}
            strokeWidth="2"
          />
        ))}
        <text
          x={Math.min(x(lastIndex), W - right - 4)}
          y={y(series[lastIndex].price) - 10}
          textAnchor="end"
          fontSize="12"
          fontWeight="700"
          fill="#0F3B6E"
        >
          {Math.round(series[lastIndex].price).toLocaleString('vi-VN')}
        </text>
        {series.map((point, i) =>
          i % step === 0 || i === lastIndex ? (
            <text
              key={`t${i}`}
              x={x(i)}
              y={H - 8}
              textAnchor={i === lastIndex ? 'end' : i === 0 ? 'start' : 'middle'}
              fontSize="11"
              fill="#5A5A5A"
            >
              {shortDate(point.date)}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  )
}

function roleText(row: PackagingHistoryRow): string {
  return row.roles.map((role) => ROLE_LABEL.get(role) ?? String(role)).join(', ')
}

function DiffCell({ row }: { row: PackagingHistoryRow }) {
  const diff = formatPackagingDiff(row.diff)
  if (!diff) return <PrintDash />
  if (row.diff === 0) return <span className="faint">0</span>
  const percent = formatPackagingPercent(row.pct)
  return (
    <span className={(row.diff ?? 0) > 0 ? 'up' : 'down'}>
      {diff}
      {percent && ` (${percent})`}
    </span>
  )
}

interface PrintHistoryTableProps {
  rows: readonly PackagingHistoryRow[]
  productMode: boolean
  singleCode: boolean
  /** Số lần mua theo máy chủ (có thể lớn hơn số dòng nếu bản in bị cắt ở trần). */
  total: number
}

/** Bảng "Toàn bộ lịch sử mua hàng" — cùng cột với màn hình. */
export function PrintHistoryTable({ rows, productMode, singleCode, total }: PrintHistoryTableProps) {
  return (
    <div className="panel gap">
      <div className="tbar">
        <span className="ttl">Toàn bộ lịch sử mua hàng</span>
        <span className="cnt">{total.toLocaleString('vi-VN')} lần mua</span>
        <span className="cnt">
          · Giá chưa VAT (VNĐ), bản chụp lúc mua: xanh = đắt hơn lần trước, đỏ = rẻ hơn
        </span>
      </div>
      {rows.length === 0 ? (
        <p className="empty">Không có lần mua nào khớp bộ lọc.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th className="c">Lần</th>
              <th>Ngày mua</th>
              <th>Mã VTBB</th>
              {!singleCode && <th>Tên vật tư</th>}
              {productMode && <th>Vai trò</th>}
              <th>Nhà cung cấp</th>
              <th>Kho</th>
              <th className="n">Số lượng</th>
              <th className="n">Đơn giá</th>
              <th className="n">Thành tiền</th>
              <th className="n">So lần trước</th>
              <th>Nguồn</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const quantity = formatQuantity(row.qty)
              const openPo = row.source_type === PRICE_SOURCE_TYPE_CODE.PO_LINE
              return (
                <tr key={row.id} className={row.price === 0 ? 'zero' : undefined}>
                  <td className="c">
                    <b>{row.seq}</b>
                  </td>
                  <td>{row.date ? formatDate(row.date) : <PrintDash />}</td>
                  <td className="code">{row.code}</td>
                  {!singleCode && <td className="name">{row.name || <span className="faint">(chưa có tên)</span>}</td>}
                  {productMode && <td>{roleText(row) || <PrintDash />}</td>}
                  <td>{row.supplier || <PrintDash />}</td>
                  <td className="wh">{row.warehouse || <PrintDash />}</td>
                  <td className="n">{quantity ? `${quantity}${row.unit ? ` ${row.unit}` : ''}` : <PrintDash />}</td>
                  <td className="n">
                    {row.price === 0 ? '0' : <b>{formatPackagingPrice(row.price) || <PrintDash />}</b>}
                  </td>
                  <td className="n">{row.price ? formatPackagingPrice(row.amount) || <PrintDash /> : <PrintDash />}</td>
                  <td className="n">
                    <DiffCell row={row} />
                  </td>
                  <td>
                    {openPo && <span className="pbadge">ĐMH đang mở</span>}
                    {row.doc_id > 0 && (row.po_code || `#${row.doc_id}`)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
