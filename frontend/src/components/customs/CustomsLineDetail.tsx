// bao-CR-470 — chi tiết MỘT DÒNG HÀNG (không phải một tờ khai: tệp GTT02 không có số tờ khai,
// xem 02-thiet-ke-ky-thuat.md §2.2). Đủ 32 cột của tệp gốc, xếp thành 6 nhóm.
// bao-CR-608 (đại ca 07/10/2026): nút «Sửa» (quyền `customs_price.write`) chuyển hộp sang biểu mẫu
// sửa tại chỗ; nút «Xóa» (quyền `customs_price.delete`) hỏi xác nhận rồi xóa. Nút ẩn theo `can()`;
// backend gác lại bằng `require` và chụp bản trước khi sửa / xóa.
import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { askConfirm } from '../confirm'
import { toast } from '../toast'
import CustomsLineEditForm from './CustomsLineEditForm'
import CustomsModal from './CustomsModal'
import { fmtDate, fmtQty, fmtUsd, fmtVnd } from './customs-shared'

type Field = [string, string, (v: any, row: any) => string]

const txt = (v: any) => (v == null || v === '' ? '—' : String(v))
const num = (v: any) => fmtUsd(v)
const pct = (v: any) => (v == null || v === '' ? '—' : `${v}%`)
const day = (v: any) => fmtDate(v)
// bao-CR-603 — giá trị kèm nguồn: «(từ tệp)» khi lấy từ cột tùy chọn của tệp nạp, không thì «(suy ra)» / «(tính)».
const withSource = (value: string, fromFile: any, derivedNote: string) =>
  (value === '—' ? value : `${value} ${fromFile ? '(từ tệp)' : derivedNote}`)

const GROUPS: { title: string; fields: Field[] }[] = [
  { title: 'Tờ khai', fields: [
    ['reg_date', 'Ngày đăng ký', day], ['office_code', 'Nơi mở tờ khai', txt],
    ['line_no', 'Số thứ tự hàng', txt], ['import_country', 'Nước nhận hàng', txt],
  ] },
  { title: 'Doanh nghiệp', fields: [
    ['importer_name', 'Doanh nghiệp', txt], ['importer_tax_code', 'Mã số thuế', txt],
    ['partner_name', 'Đối tác (bên bán)', txt], ['origin_country', 'Nước xuất xứ', txt],
  ] },
  { title: 'Hàng hóa', fields: [
    ['product_name', 'Tên hàng', txt], ['hs_code', 'Mã HS', txt],
    ['active_ingredient', 'Hoạt chất', (v, r) => withSource(txt(v), r.active_ingredient_from_file, '(suy ra)')],
    ['formulation', 'Hàm lượng / dạng', (v, r) => withSource(txt(v), r.formulation_from_file, '(suy ra)')],
    ['quantity', 'Lượng', (v, r) => fmtQty(v, r.unit_code)], ['unit_code', 'Đơn vị tính', txt],
  ] },
  { title: 'Giá', fields: [
    ['price_usd', 'Đơn giá khai báo (USD)', num], ['adj_price_usd', 'Đơn giá điều chỉnh (USD)', num],
    ['price_nt', 'Đơn giá nguyên tệ khai báo', num], ['adj_price_nt', 'Đơn giá nguyên tệ điều chỉnh', num],
    ['currency', 'Nguyên tệ', txt], ['fx_rate', 'Tỷ giá nguyên tệ', num], ['usd_rate', 'Tỷ giá USD', num],
    // bao-CR-493 — hai cột VND: 7% tạm tính và theo thuế suất XNK của dòng (backend tính sẵn);
    // bao-CR-603: tệp nạp có cột VND thì lấy của tệp («từ tệp»).
    ['price_vnd_flat', 'Giá VND (thuế NK 7%)', (v, r) => withSource(fmtVnd(v), r.price_vnd_flat_from_file, '(tính)')],
    ['price_vnd_line_tax', 'Giá VND (thuế suất dòng)', (v, r) => withSource(fmtVnd(v), r.price_vnd_line_tax_from_file, '(tính)')],
  ] },
  { title: 'Hợp đồng & vận chuyển', fields: [
    ['contract_no', 'Số hợp đồng', txt], ['contract_date', 'Ngày hợp đồng', day],
    ['incoterm', 'Điều kiện giao hàng', txt], ['transport_mode', 'Phương tiện vận chuyển', (_v, r) => txt(r.transport_label || r.transport_mode)],
  ] },
  { title: 'Thuế', fields: [
    ['rate_import', 'Thuế suất XNK', pct], ['tax_import', 'Thuế XNK', num],
    ['rate_vat', 'Thuế suất VAT', pct], ['tax_vat', 'Thuế VAT', num],
    ['rate_excise', 'Thuế suất TTĐB', pct], ['tax_excise', 'Thuế TTĐB', num],
    ['rate_safeguard', 'Thuế suất tự vệ', pct], ['tax_safeguard', 'Thuế tự vệ', num],
    ['tax_environment', 'Thuế môi trường', num],
  ] },
]

type Pick = (id: number, name: string) => void

export default function CustomsLineDetail({ id, onClose, onFilterImporter, onFilterPartner, onChanged }: {
  id: number
  onClose: () => void
  /** bao-CR-493 — cộng thêm doanh nghiệp / đối tác của dòng này vào bộ lọc (như bản v2). */
  onFilterImporter?: Pick
  onFilterPartner?: Pick
  /** bao-CR-608 — gọi sau khi sửa / xóa để trang tải lại bảng. */
  onChanged?: () => void
}) {
  const { can } = useAuth()
  const [row, setRow] = useState<any>(null)
  const [editing, setEditing] = useState(false)
  const deleting = useRef(false)

  async function remove() {
    if (deleting.current || !row) return
    const ok = await askConfirm({
      title: 'Xóa dòng hàng',
      message: `Xóa dòng hàng ID ${row.id} — «${String(row.product_name || '').slice(0, 80)}»? Bản trước khi xóa được lưu trong nhật ký thay đổi.`,
      confirmText: 'Xóa',
    })
    if (!ok || deleting.current) return
    deleting.current = true
    try {
      await api.delete(`/api/customs/lines/${row.id}`)
      toast.success(`Đã xóa dòng hàng ID ${row.id}`)
      onChanged?.()
      onClose()
    } catch { /* interceptor đã báo lỗi */ } finally {
      deleting.current = false
    }
  }
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  // Chỉ tải lại khi đổi dòng — `onClose` của trang là hàm mới mỗi lượt render.
  useEffect(() => {
    api.get(`/api/customs/lines/${id}`).then((r) => setRow(r.data.data)).catch(() => closeRef.current())
  }, [id])
  return (
    <CustomsModal title={<>{editing ? 'Sửa dòng hàng' : 'Chi tiết dòng hàng'}{row && <span style={{ marginLeft: 8, fontSize: 13, fontWeight: 400, color: 'var(--muted)' }}>ID {row.id}</span>}</>}
      width={860} onClose={onClose}>
      {!row ? <div style={{ color: 'var(--muted)' }}>Đang tải…</div> : editing ? (
        <CustomsLineEditForm row={row} onCancel={() => setEditing(false)}
          onSaved={(fresh) => { setRow(fresh); setEditing(false); onChanged?.() }} />
      ) : (
        <>
          <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
            Một dòng hàng trong tệp GTT02 — một tờ khai có thể gồm nhiều dòng; tệp không có số tờ khai.
            Lô nạp #{row.batch_id}, dòng {row.source_row} của tệp gốc.
            {row.date_fixed && <> <span className="badge warn">Đã sửa ngày</span> ngày đăng ký trong tệp bị đảo ngày/tháng, hệ thống đã đọc lại.</>}
          </div>
          {(onFilterImporter || onFilterPartner || can('customs_price', 'write') || can('customs_price', 'delete')) && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
              {can('customs_price', 'write') && (
                <button className="btn ghost" type="button" onClick={() => setEditing(true)}>
                  <i className="ti ti-pencil" />Sửa
                </button>
              )}
              {can('customs_price', 'delete') && (
                <button className="btn ghost" type="button" style={{ color: '#b91c1c' }} onClick={remove}>
                  <i className="ti ti-trash" />Xóa
                </button>
              )}
              {onFilterImporter && row.importer_id > 0 && (
                <button className="btn ghost" type="button" onClick={() => onFilterImporter(row.importer_id, row.importer_name)}>
                  <i className="ti ti-building-factory-2" />Lọc theo doanh nghiệp này
                </button>
              )}
              {onFilterPartner && row.partner_id > 0 && (
                <button className="btn ghost" type="button" onClick={() => onFilterPartner(row.partner_id, row.partner_name)}>
                  <i className="ti ti-heart-handshake" />Lọc theo đối tác này
                </button>
              )}
            </div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
            {GROUPS.map((g) => (
              <div key={g.title} className="card" style={{ padding: '10px 14px' }}>
                <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--navy)' }}>{g.title}</div>
                {g.fields.map(([k, label, fmt]) => (
                  <div key={k} style={{ display: 'flex', gap: 10, fontSize: 13, padding: '3px 0' }}>
                    <span style={{ width: 190, flexShrink: 0, color: 'var(--muted)' }}>{label}</span>
                    <span style={{ userSelect: 'text', wordBreak: 'break-word' }}>{fmt(row[k], row)}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </>
      )}
    </CustomsModal>
  )
}
