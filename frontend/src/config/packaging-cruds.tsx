import type { CrudConfig } from './cruds'
import PackagingBomImportButton from '../components/packaging/PackagingBomImportButton'
import { PACKAGING_BOM_API, PACKAGING_QUOTE_API } from '../api/packaging-cost'
import { fmtDateStr, fmtDateTime } from '../utils/datetime'
import { fmtPrice } from '../utils/money'
import { PACKAGING_ROLE_LABELS } from '../utils/packaging-price'

/**
 * duoc-CR-784 — hai danh mục của cụm Giá bao bì khai báo kiểu CRUD chung của bản v1 (gộp vào `cruds` ở `config/cruds.tsx`):
 *   - Báo giá VTBB (`/api/product-price-quotes`): giá nhà cung cấp báo cho vật tư bao bì (VNĐ chưa VAT);
 *   - Định mức bao bì (`/api/packaging-boms`): mỗi mã hàng hóa dùng chai / nắp / nhãn / nhãn thùng / thùng nào.
 * Cả hai gác khóa quyền `packaging_cost`; `txn: true` để người chỉ có quyền Xem vẫn mở được danh sách.
 */

const ROLE_FIELDS = [
  { role: 1, key: 'bottle_code' }, { role: 2, key: 'cap_code' }, { role: 3, key: 'label_code' },
  { role: 4, key: 'carton_label_code' }, { role: 5, key: 'carton_code' },
] as const

/** Ngày hôm nay (YYYY-MM-DD) làm mặc định cho ngày hiệu lực của báo giá mới. */
function todayIso(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Ô thành phần của định mức: mã trên, tên dưới; mã chưa có trong danh mục sản phẩm tô đỏ (`parts[].in_catalog`). */
function partCell(row: any, role: number, field: string) {
  const code = String(row[field] ?? '')
  if (!code) return <span style={{ color: 'var(--muted)' }}>—</span>
  const part = (row.parts as any[] | undefined)?.find((p) => p.role === role)
  const missing = part ? !part.in_catalog : false
  return (
    <div style={{ lineHeight: 1.25 }} title={missing ? 'Mã chưa có trong danh mục sản phẩm' : part?.name}>
      <div style={{ fontSize: 12.5, fontWeight: 600, color: missing ? 'var(--red)' : undefined }}>{code}</div>
      <div style={{ fontSize: 12, color: 'var(--muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {missing ? 'chưa có trong danh mục' : part?.name}
      </div>
    </div>
  )
}

export const PACKAGING_CRUDS: Record<string, CrudConfig> = {
  'product-price-quotes': {
    slug: 'product-price-quotes', entity: 'packaging_cost', auditEntity: 'packaging_cost_quote', title: 'Báo giá VTBB',
    apiPath: PACKAGING_QUOTE_API, txn: true,
    columns: [
      { key: 'product_code', label: 'Mã VTBB', render: (r) => <b>{r.product_code}</b> },
      { key: 'product_name', label: 'Tên vật tư', noSort: true },
      { key: 'supplier_code', label: 'Mã NCC' },
      { key: 'supplier_name', label: 'Nhà cung cấp', noSort: true },
      { key: 'price', label: 'Đơn giá', render: (r) => <div style={{ textAlign: 'right' }}>{fmtPrice(r.price)}</div> },
      { key: 'vat', label: 'VAT %', render: (r) => Number(r.vat) },
      { key: 'valid_from', label: 'Ngày hiệu lực', render: (r) => fmtDateStr(r.valid_from) },
      { key: 'note', label: 'Ghi chú' },
      { key: 'updated_at', label: 'Cập nhật', render: (r) => fmtDateTime(r.updated_at) || '—', defaultHidden: true },
    ],
    filters: [
      { key: 'product_code', label: 'Mã VTBB' }, { key: 'supplier_code', label: 'Mã NCC' }, { key: 'note', label: 'Ghi chú' },
    ],
    detailChips: (row) => [
      { icon: 'ti-hash', text: row.product_code, cls: 'code' },
      ...(row.product_name ? [{ icon: 'ti-package', text: row.product_name }] : []),
      ...(row.supplier_name ? [{ icon: 'ti-truck', text: row.supplier_name }] : []),
    ],
    fields: [
      { key: 'product_code', label: 'Mã VTBB', readonlyOnEdit: true, group: 'Báo giá',
        hint: 'Mã vật tư bao bì có trong danh mục sản phẩm. Không sửa được sau khi tạo.' },
      { key: 'supplier_code', label: 'Mã NCC', group: 'Báo giá', hint: 'Bỏ trống nếu chưa rõ nhà cung cấp.' },
      { key: 'price', label: 'Đơn giá (VNĐ, chưa VAT)', type: 'number', group: 'Báo giá',
        hint: 'Theo đơn vị tính của danh mục. Báo giá mới nhất của một mã là giá mới ở màn Tác động.' },
      { key: 'vat', label: 'VAT (%)', type: 'number', group: 'Báo giá' },
      { key: 'valid_from', label: 'Ngày hiệu lực', type: 'date', default: todayIso(), group: 'Báo giá',
        hint: 'Báo giá có ngày hiệu lực ở tương lai VẪN tính ngay là giá mới, để xem trước tác động.' },
      { key: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true, group: 'Khác' },
    ],
  },
  'packaging-boms': {
    slug: 'packaging-boms', entity: 'packaging_cost', auditEntity: 'packaging_bom', title: 'Định mức bao bì',
    apiPath: PACKAGING_BOM_API, txn: true,
    headerExtra: () => <PackagingBomImportButton />,
    columns: [
      { key: 'hh_code', label: 'Mã HH', render: (r) => <b>{r.hh_code}</b> },
      { key: 'hh_name', label: 'Tên hàng hóa' },
      { key: 'legal_name', label: 'Tên pháp lý', defaultHidden: true },
      {
        key: 'carton_qty', label: 'Quy cách thùng',
        render: (r) => (r.carton_qty ? Number(r.carton_qty).toLocaleString('vi-VN') : <span style={{ color: 'var(--red)' }}>chưa có</span>),
      },
      ...ROLE_FIELDS.map((p) => ({ key: p.key, label: PACKAGING_ROLE_LABELS[p.role], render: (r: any) => partCell(r, p.role, p.key) })),
      { key: 'updated_at', label: 'Cập nhật', render: (r) => fmtDateTime(r.updated_at) || '—', defaultHidden: true },
    ],
    filters: [
      { key: 'hh_code', label: 'Mã HH' }, { key: 'hh_name', label: 'Tên hàng hóa' },
      ...ROLE_FIELDS.map((p) => ({ key: p.key, label: `Mã ${PACKAGING_ROLE_LABELS[p.role].toLowerCase()}` })),
    ],
    detailChips: (row) => [
      { icon: 'ti-hash', text: row.hh_code, cls: 'code' },
      ...(row.hh_name ? [{ icon: 'ti-package', text: row.hh_name }] : []),
    ],
    fields: [
      { key: 'hh_code', label: 'Mã HH', readonlyOnEdit: true, group: 'Hàng hóa' },
      { key: 'carton_qty', label: 'Quy cách thùng (chai / thùng)', type: 'number', default: 0, group: 'Hàng hóa',
        hint: '0 = chưa có — phần nhãn thùng / thùng sẽ không tính được.' },
      { key: 'hh_name', label: 'Tên hàng hóa', fullWidth: true, group: 'Hàng hóa' },
      { key: 'legal_name', label: 'Tên pháp lý', fullWidth: true, group: 'Hàng hóa' },
      ...ROLE_FIELDS.map((p) => ({
        key: p.key, label: `Mã ${PACKAGING_ROLE_LABELS[p.role].toLowerCase()}`, group: 'Thành phần bao bì',
        hint: p.role === 4 || p.role === 5 ? 'Giá tính cho cả thùng, chia quy cách thùng khi cộng vào chi phí /chai.' : undefined,
      })),
    ],
  },
}
