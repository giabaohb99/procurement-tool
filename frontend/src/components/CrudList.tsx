import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { cruds } from '../config/cruds'
import FilterBar from './FilterBar'
import Pagination from './Pagination'

export default function CrudList() {
  const { entity } = useParams()
  const cfg = cruds[entity || '']
  const { can } = useAuth()
  const navigate = useNavigate()

  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleExport() {
    try {
      const params: any = { ...filters };
      if (selectedIds.length > 0) params.ids = selectedIds.join(',');
      const r = await api.get(`${cfg.apiPath}/export/csv`, { params, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${cfg.slug}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (e) {
      alert('Lỗi khi xuất file');
    }
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const r = await api.post(`${cfg.apiPath}/import/csv`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(r.data.message || 'Nhập file thành công');
      load(page, pageSize, filters);
    } catch (e: any) {
      alert(e.response?.data?.message || 'Lỗi khi nhập file');
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  async function load(p = 1, s = 20, f: Record<string, string> = {}) {
    const r = await api.get(cfg.apiPath, { params: { ...f, page: p, page_size: s } })
    setItems(r.data.data.items)
    setTotal(r.data.data.total)
    setSelectedIds([])
  }
  useEffect(() => {
    if (!cfg) return
    setPage(1); setPageSize(20); setFilters({})
    load(1, 20, {})
  }, [cfg?.slug])

  if (!cfg) return <div>Không tìm thấy trang.</div>

  function applyFilters(f: Record<string, string>) { setFilters(f); setPage(1); load(1, pageSize, f) }
  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s, filters) }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 className="page-title" style={{ marginBottom: 12 }}>{cfg.title}</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          {cfg.importExport && can(cfg.entity, 'write') && (
            <>
              <button className="btn outline" onClick={handleExport}><i className="ti ti-download" />Export CSV</button>
              <button className="btn outline" onClick={() => fileInputRef.current?.click()}><i className="ti ti-upload" />Import CSV</button>
              <input type="file" accept=".csv" ref={fileInputRef} style={{ display: 'none' }} onChange={handleImport} />
            </>
          )}
          {can(cfg.entity, 'create') && (
            <button className="btn" onClick={() => navigate(`/${cfg.slug}/new`)}><i className="ti ti-plus" />Thêm</button>
          )}
        </div>
      </div>

      <FilterBar fields={cfg.filters} onApply={applyFilters} />

      <div className="card">
        <table>
          <thead>
            <tr>
              <th style={{ width: 40 }}>
                <input 
                  type="checkbox" 
                  checked={selectedIds.length === items.length && items.length > 0} 
                  onChange={(e) => setSelectedIds(e.target.checked ? items.map(i => i.id) : [])} 
                />
              </th>
              <th>ID</th>
              {cfg.columns.map((c) => <th key={c.key}>{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.id} className="clickable" onClick={() => navigate(`/${cfg.slug}/${row.id}`)}>
                <td onClick={(e) => e.stopPropagation()}>
                  <input 
                    type="checkbox" 
                    checked={selectedIds.includes(row.id)} 
                    onChange={(e) => {
                      const checked = e.target.checked;
                      setSelectedIds(prev => checked ? [...prev, row.id] : prev.filter(id => id !== row.id));
                    }} 
                  />
                </td>
                <td>{row.id}</td>
                {cfg.columns.map((c) => <td key={c.key}>{c.render ? c.render(row) : (row[c.key] ?? '—')}</td>)}
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={cfg.columns.length + 2} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Không có dữ liệu</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
    </div>
  )
}
