import { useEffect, useState } from 'react'
import { api } from '../api/client'
import SearchSelect from '../components/SearchSelect'
import PrLinesReport from '../components/PrLinesReport'

// bao-CR-296 — trang riêng cho báo cáo "Chi tiết YC mua hàng" (nội dung dùng chung với
// tab cùng tên trong Báo cáo mua hàng). Bộ lọc Năm/Công ty áp dụng ngay, không cần nút Lọc.
export default function PrLinesReportPage() {
  const thisYear = new Date().getFullYear()
  const [companies, setCompanies] = useState<any[]>([])
  const [year, setYear] = useState(String(thisYear))
  const [companyId, setCompanyId] = useState('')

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
  }, [])

  return (
    <div>
      <div className="no-print" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Chi tiết YC mua hàng</h2>
        <div className="filters" style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="filter-item" style={{ flex: '0 0 190px' }}><label>Công ty</label>
            <SearchSelect value={companyId} placeholder="Tất cả"
              options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
              onChange={(v) => setCompanyId(v)} /></div>
          <div className="filter-item" style={{ flex: '0 0 150px', minWidth: 150 }}><label>Năm</label>
            <SearchSelect value={year} placeholder="Tất cả"
              options={[{ value: 'all', label: 'Tất cả' }, ...[thisYear, thisYear - 1, thisYear - 2].map((y) => ({ value: String(y), label: String(y) }))]}
              onChange={(v) => setYear(v)} /></div>
          <button className="btn ghost" onClick={() => window.print()}><i className="ti ti-printer" />In</button>
        </div>
      </div>
      <PrLinesReport year={year} companyId={companyId} />
    </div>
  )
}
