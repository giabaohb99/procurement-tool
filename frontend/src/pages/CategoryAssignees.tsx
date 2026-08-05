import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { askConfirm } from '../components/confirm'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import Pagination from '../components/Pagination'
import { useAuth } from '../auth/AuthContext'
import TableHead, { TableCells, TableColGroup } from '../components/TableHead'
import TableToolbar from '../components/TableToolbar'
import { useTableColumns, TableColumn } from '../hooks/useTableColumns'

type Row = {
  id: number; item_group_id: number; item_group_name: string
  primary_employee_id: number; primary_name: string; primary_code: string
  backup_employee_id: number; backup_name: string; backup_code: string
}

type SortField = 'item_group_name' | 'primary_name' | 'backup_name'

export default function CategoryAssignees() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const canCreate = can('category_assignee', 'create')
  const canDelete = can('category_assignee', 'delete')

  const [rows, setRows] = useState<Row[]>([])
  const [cats, setCats] = useState<{ id: number; name: string }[]>([])
  const [fCat, setFCat] = useState('')     // filter phân loại (id)
  const [fName, setFName] = useState('')   // filter tên NSTM
  const [fCode, setFCode] = useState('')   // filter mã NV

  const [sortField, setSortField] = useState<SortField>('item_group_name')  // mặc định: Phân loại A→Z
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const COLS = useMemo<TableColumn<Row>[]>(() => [
    { key: 'item_group_name', label: 'Phân loại', sort: 'item_group_name', width: '32%', cell: (r) => <b>{r.item_group_name || '—'}</b> },
    {
      key: 'primary_name', label: 'NSTM chính', sort: 'primary_name', width: '30%',
      cell: (r) => <>{r.primary_name || '—'}{r.primary_code ? <span style={{ color: '#94a3b8', fontSize: 12 }}> · {r.primary_code}</span> : ''}</>,
    },
    {
      key: 'backup_name', label: 'NSTM dự phòng', sort: 'backup_name', width: '30%',
      cell: (r) => (r.backup_name
        ? <>{r.backup_name}{r.backup_code ? <span style={{ color: '#94a3b8', fontSize: 12 }}> · {r.backup_code}</span> : ''}</>
        : <span style={{ color: '#94a3b8' }}>—</span>),
    },
    {
      key: 'actions', label: 'Thao tác', width: 120, align: 'center', fixed: true, td: { whiteSpace: 'nowrap' },
      cell: (r) => (
        <>
          {canCreate && <button className="btn ghost" style={{ height: 30, padding: '0 8px', marginRight: 6 }} title="Sửa phân công"
            onClick={() => navigate(`/category-assignees/new?cats=${r.item_group_id}&primary=${r.primary_employee_id}&backup=${r.backup_employee_id}`)}><i className="ti ti-pencil" />Sửa</button>}
          {canDelete && <button className="btn err" style={{ height: 30, padding: '0 8px' }} onClick={() => del(r.id)}><i className="ti ti-trash" /></button>}
        </>
      ),
    },
  ], [canCreate, canDelete])
  const table = useTableColumns('category-assignees', COLS)

  async function load() {
    // Tải hết (page_size lớn) để lọc/sort/phân trang phía client; API đã tối ưu JOIN nên nhanh
    const r = await api.get('/api/category-assignees', { params: { page_size: 1000 } })
    setRows(r.data.data.items || [])
  }
  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then(r => setCats(r.data.data.items || []))
    load()
  }, [])

  async function del(id: number) {
    if (!(await askConfirm({ message: 'Xóa phân công này?' }))) return
    await api.delete(`/api/category-assignees/${id}`); await load()
  }

  function handleSort(field: string) {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortField(field as SortField); setSortDir('asc') }
    setPage(1)
  }

  const filtered = useMemo(() => rows.filter(r =>
    (!fCat || String(r.item_group_id) === fCat) &&
    (!fName || `${r.primary_name || ''} ${r.backup_name || ''}`.toLowerCase().includes(fName.trim().toLowerCase())) &&
    (!fCode || `${r.primary_code || ''} ${r.backup_code || ''}`.toLowerCase().includes(fCode.trim().toLowerCase()))
  ), [rows, fCat, fName, fCode])

  const sorted = useMemo(() => {
    const arr = [...filtered]
    arr.sort((a, b) => {
      const va = (a[sortField] || '').toString()
      const vb = (b[sortField] || '').toString()
      if (!va) return 1        // trống xuống cuối
      if (!vb) return -1
      return sortDir === 'asc' ? va.localeCompare(vb, 'vi') : vb.localeCompare(va, 'vi')
    })
    return arr
  }, [filtered, sortField, sortDir])

  // Kẹp trang khi số dòng lọc thay đổi
  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  useEffect(() => { if (page > totalPages) setPage(1) }, [page, totalPages])
  const paged = sorted.slice((page - 1) * pageSize, page * pageSize)

  function resetFilters() { setFCat(''); setFName(''); setFCode(''); setPage(1) }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Phân công phụ trách (theo phân loại)</h2>
        {canCreate && <button className="btn" onClick={() => navigate('/category-assignees/new')}><i className="ti ti-plus" />Gán phân công</button>}
      </div>

      <FilterPanel onClear={resetFilters} canClear={!!(fCat || fName || fCode)}>
        <FilterItem label="Phân loại" width={240}>
          <select value={fCat} onChange={e => { setFCat(e.target.value); setPage(1) }}>
            <option value="">Tất cả</option>
            {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </FilterItem>
        <FilterItem label="Tên NSTM" grow>
          <input value={fName} onChange={e => { setFName(e.target.value); setPage(1) }} placeholder="Tìm theo tên NSTM…" />
        </FilterItem>
        <FilterItem label="Mã nhân viên" grow>
          <input value={fCode} onChange={e => { setFCode(e.target.value); setPage(1) }} placeholder="Tìm theo mã NV…" />
        </FilterItem>
      </FilterPanel>

      <div className="card table-card">
        <TableToolbar {...table} onRefresh={load} />
        <div className="table-scroll">
          {/* table-layout fixed + colgroup: khóa bề rộng cột để sort/đổi trang không làm bảng giật */}
          <table style={{ tableLayout: 'fixed' }}>
            <TableColGroup columns={table.columns} colW={table.colW} />
            <TableHead columns={table.columns} startResize={table.startResize}
              sortBy={sortField} sortDir={sortDir} onSort={handleSort} />
            <tbody>
              {paged.map((r, i) => (
                <tr key={r.id}>
                  <TableCells columns={table.columns} row={r} index={i} />
                </tr>
              ))}
              {sorted.length === 0 && <tr><td colSpan={table.columns.length} className="table-empty">Không có phân công nào khớp bộ lọc</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={sorted.length}
            onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>
    </div>
  )
}
