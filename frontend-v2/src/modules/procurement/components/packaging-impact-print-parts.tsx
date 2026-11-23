/**
 * duoc-CR-784 — các khối của bản in Tác động giá bao bì, dựng theo bản mẫu HTML: khối ô lọc (ô mã chọn + dòng thông tin) liền
 * bảng MÃ ĐÃ CHỌN (đầu navy, ô giá giả định nền vàng), rồi khối SẢN PHẨM BỊ ẢNH HƯỞNG (ô thành phần ghi mã + giá, mã đang chọn
 * tô xanh nhạt). Cùng cột + định dạng với màn hình (dùng lại hàm định dạng, nhãn vai trò, câu ghi chú). Bảng mã đã chọn không
 * có cột "Sàn – Trần": ngưỡng đang tắt (`PACKAGING_LIMITS_ENABLED`). Chênh lệch TĂNG xanh, GIẢM đỏ (luật màu của hệ).
 */
import { PACKAGING_PART_COLUMNS } from '../config/packaging-part-columns'
import type {
  PackagingImpactProduct,
  PackagingPart,
  PackagingSelectedCode,
} from '../types/packaging-cost-types'
import {
  formatPackagingDiff,
  formatPackagingPercent,
  formatPackagingPrice,
} from '../utils/packaging-price-format'
import {
  buildSelectedCodeNote,
  joinPackagingWarnings,
  packagingRoleLabel,
} from '../utils/packaging-warning-text'
import { PrintChipsBox, PrintDash } from './packaging-print-widgets'

type Num = number | null | undefined

function toneClass(value: Num): string | undefined {
  if (typeof value !== 'number' || !Number.isFinite(value) || Math.abs(value) < 1e-6) return undefined
  return value > 0 ? 'up' : 'down'
}

function Price({ value }: { value: Num }) {
  const text = formatPackagingPrice(value)
  return text ? <>{text}</> : <PrintDash />
}

function Diff({ value }: { value: Num }) {
  const text = formatPackagingDiff(value)
  if (!text) return <PrintDash />
  return <span className={toneClass(value)}>{text}</span>
}

function Percent({ value }: { value: Num }) {
  const text = formatPackagingPercent(value)
  if (!text) return <PrintDash />
  return <span className={toneClass(value)}>{text}</span>
}

interface PrintImpactSelectionProps {
  codes: readonly string[]
  /** Giá giả định / khoảng ngày / từ khóa đang bật — từ `describeImpactFilters`. */
  extras: readonly string[]
  rows: readonly PackagingSelectedCode[]
}

/** Khối ô lọc + dòng điều kiện đang bật + bảng MÃ ĐÃ CHỌN (ba thẻ số liệu đã bỏ theo người chủ, 23/11/2026). */
export function PrintImpactSelection({ codes, extras, rows }: PrintImpactSelectionProps) {
  return (
    <div className="panel">
      <div className="pfilters">
        <div className="field ms">
          <label>Mã chai / nắp / nhãn / nhãn thùng / thùng</label>
          <PrintChipsBox codes={codes} emptyText="Chưa chọn mã" />
        </div>
      </div>
      {extras.length > 0 && <div className="info">{extras.join(' · ')}</div>}
      {rows.length === 0 ? (
        <p className="empty">Các mã đã chọn chưa có trong định mức nào.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Mã</th>
              <th>Tên vật tư</th>
              <th>Nhóm</th>
              <th className="n">Giá cũ</th>
              <th className="n">Giá mới</th>
              <th className="n">Giá giả định</th>
              <th className="n">Chênh lệch</th>
              <th className="n">%</th>
              <th className="n">Số SP</th>
              <th className="n">Min</th>
              <th className="n">Max</th>
              <th>Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.code}>
                <td className="code">
                  <b>{row.code}</b>
                </td>
                <td className="name">{row.name}</td>
                <td>{row.group}</td>
                <td className="n">
                  <Price value={row.old} />
                </td>
                <td className="n">
                  <Price value={row.new} />
                </td>
                <td className="n">
                  {row.assumed != null ? (
                    <span className="cell-inp">
                      <Price value={row.assumed} />
                    </span>
                  ) : (
                    <span className="cell-inp faint">Bỏ trống</span>
                  )}
                </td>
                <td className="n">
                  <Diff value={row.diff} />
                </td>
                <td className="n">
                  <Percent value={row.pct} />
                </td>
                <td className="n">{row.usage}</td>
                <td className="n">
                  <Price value={row.min} />
                </td>
                <td className="n">
                  <Price value={row.max} />
                </td>
                <td className="nt">
                  <span className="note">{buildSelectedCodeNote(row, row.applied)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

/** Ô thành phần: mã trên, giá dưới ("cũ → mới" khi đổi); mã đang chọn tô xanh nhạt cả ô. */
function PartCell({ part }: { part: PackagingPart | undefined }) {
  if (!part?.code) {
    return (
      <td className="pc">
        <PrintDash />
      </td>
    )
  }
  const current = part.applied ?? part.new
  const changed = part.old != null && current != null && Math.abs(current - part.old) > 1e-9
  return (
    <td className={part.selected ? 'pc hl' : 'pc'}>
      <div>{part.code}</div>
      <small className={part.selected ? undefined : 'faint'}>
        {current == null ? (
          'chưa có giá'
        ) : changed ? (
          <>
            {formatPackagingPrice(part.old)} →{' '}
            <b className={toneClass(current - (part.old ?? 0))}>{formatPackagingPrice(current)}</b>
          </>
        ) : (
          formatPackagingPrice(current)
        )}
      </small>
    </td>
  )
}

/** Khối "Sản phẩm sử dụng các mã đã chọn". */
export function PrintImpactProducts({
  rows,
  matched,
  empty,
}: {
  rows: readonly PackagingImpactProduct[]
  matched: number
  /** Câu hiện khi không có sản phẩm nào. */
  empty: string
}) {
  return (
    <div className="panel gap">
      <div className="tbar">
        <span className="ttl">Sản phẩm sử dụng các mã đã chọn</span>
        <span className="cnt">{matched.toLocaleString('vi-VN')} sản phẩm</span>
      </div>
      {rows.length === 0 ? (
        <p className="empty">{empty}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th className="c">STT</th>
              <th>Mã HH</th>
              <th>Tên hàng hóa</th>
              <th className="n">Quy cách thùng</th>
              {PACKAGING_PART_COLUMNS.map((part) => (
                <th key={part.role}>
                  {part.perCarton
                    ? `${packagingRoleLabel(part.role)} (giá /thùng)`
                    : packagingRoleLabel(part.role)}
                </th>
              ))}
              <th className="n">CP bao bì/chai cũ</th>
              <th className="n">CP bao bì/chai mới</th>
              <th className="n">Tăng/giảm /chai</th>
              <th className="n">Tăng/giảm /thùng</th>
              <th>Ghi chú</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={row.hh_code}>
                <td className="c faint">{index + 1}</td>
                <td className="code">{row.hh_code}</td>
                <td className="name">{row.hh_name}</td>
                <td className="n">{row.carton_qty ? row.carton_qty.toLocaleString('vi-VN') : <PrintDash />}</td>
                {PACKAGING_PART_COLUMNS.map((part) => (
                  <PartCell key={part.role} part={row.parts.find((item) => item.role === part.role)} />
                ))}
                <td className="n">
                  <Price value={row.cost_old_bottle} />
                </td>
                <td className="n">
                  <b>
                    <Price value={row.cost_applied_bottle} />
                  </b>
                </td>
                <td className="n">
                  <Diff value={row.diff_bottle} />
                </td>
                <td className="n">
                  <Diff value={row.diff_carton} />
                </td>
                <td className="nt">
                  <span className="note">{joinPackagingWarnings(row.warnings)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
