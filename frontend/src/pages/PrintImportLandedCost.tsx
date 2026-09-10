import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { LandedCostItemTable, LandedCostSignatures, LandedCostTable, VIEW_OPTS } from '../components/ImportLandedCostReport'
import type { LandedCostView } from '../components/ImportLandedCostReport'
import { usePrintTitle } from '../hooks/usePrintTitle'

/**
 * bao-CR-347 — Bản in BÁO CÁO GIÁ VỐN LÔ HÀNG NHẬP KHẨU, in ngang A4 để ký tay.
 *
 * `?view=orders|items` chọn in bảng theo lô hay bảng chi tiết theo dòng hàng — mỗi lần in
 * MỘT bảng, vì hai bảng xoay ngang dọc khác nhau, ghép chung một tờ là không đọc được.
 *
 * Không có luồng duyệt trong phần mềm (đại ca chốt 09/2026): quản lý duyệt bằng chữ ký trên
 * giấy, nên trang này chỉ cần đủ ba ô ký cuối biểu. Bảng số dùng chung component với tab báo
 * cáo để hai nơi không bao giờ lệch nhau.
 */
const dmy = (d: string) => { if (!d) return ''; const [y, m, dd] = String(d).split('-'); return `${dd}/${m}/${y}` }

export default function PrintImportLandedCost() {
  const [sp] = useSearchParams()
  const [data, setData] = useState<any>(null)
  const [company, setCompany] = useState('')
  const [err, setErr] = useState('')
  const view = (sp.get('view') === 'items' ? 'items' : 'orders') as LandedCostView
  const codes = sp.get('codes') || ''
  const dateFrom = sp.get('date_from') || ''
  const dateTo = sp.get('date_to') || ''
  const companyId = sp.get('company_id') || ''

  useEffect(() => {
    const params: any = {}
    if (codes) params.codes = codes
    else { if (dateFrom) params.date_from = dateFrom; if (dateTo) params.date_to = dateTo }
    if (companyId) params.company_id = companyId
    api.get('/api/reports/import-landed-cost', { params, _silent: true } as any)
      .then((r) => setData(r.data.data))
      .catch(() => setErr('Không tải được số liệu — có thể bạn không có quyền xem báo cáo này.'))
    if (companyId) {
      api.get('/api/companies', { params: { page_size: 200 }, _silent: true } as any)
        .then((r) => setCompany((r.data.data.items || []).find((c: any) => String(c.id) === companyId)?.name || ''))
        .catch(() => {})
    }
  }, [codes, dateFrom, dateTo, companyId])

  usePrintTitle(data ? `Bao-cao-gia-von-nhap-khau${dateFrom ? `-${dateFrom.replace(/-/g, '')}` : ''}` : '')
  if (err) return <div style={{ padding: 40 }}>{err}</div>
  if (!data) return <div style={{ padding: 40 }}>Đang tải...</div>

  const viewLabel = VIEW_OPTS.find((o) => o.value === view)?.label || ''
  const phamVi = codes ? `Mã đơn: ${codes}` : `Ngày đặt: ${dmy(dateFrom) || '...'} — ${dmy(dateTo) || '...'}`

  return (
    <div className="print-wrap" style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      <style>{`@media print {
        @page { size: A4 landscape; margin: 0; }
        html, body { margin: 0 !important; background: #fff !important; }
        .no-print { display: none !important; }
        .print-wrap { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
        .print-doc { padding: 8mm 10mm !important; max-width: none !important; }
        .items-scroll { overflow: visible !important; }
        .items-table { min-width: 0 !important; width: 100% !important; }
      }
      .print-doc .items-table th, .print-doc .items-table td { border: 1px solid #555; padding: 3px 5px; }
      `}</style>
      <div className="no-print" style={{ maxWidth: 1100, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div className="print-doc" style={{ maxWidth: 1100, margin: '0 auto', background: '#fff', padding: '20px 26px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        <div style={{ borderBottom: '2px solid #1a4d6b', paddingBottom: 6 }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>{company || 'DEGO HOLDING'}</div>
        </div>
        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '12px 0 2px' }}>BÁO CÁO GIÁ VỐN LÔ HÀNG NHẬP KHẨU</h2>
        <div style={{ textAlign: 'center', fontSize: 10.5, fontStyle: 'italic', marginBottom: 10 }}>
          {phamVi} · {viewLabel} · Lập ngày {new Date().toLocaleDateString('vi-VN')}
        </div>
        {view === 'items' ? <LandedCostItemTable data={data} compact /> : <LandedCostTable data={data} compact />}
        <div style={{ fontSize: 10, fontStyle: 'italic', marginTop: 6, color: '#444' }}>
          Chỉ bày những loại chi phí có phát sinh. Số liệu tính tại thời điểm in.
        </div>
        <LandedCostSignatures />
      </div>
    </div>
  )
}
