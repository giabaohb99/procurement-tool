import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from './toast'
import { useAuth } from '../auth/AuthContext'
import { cruds } from '../config/cruds'
import ConfirmModal from './ConfirmModal'
import FilterBar from './FilterBar'
import {
  ConditionalFilter, ConditionalFilterButton, readParamsFromUrl, RestQueryParams,
} from './conditional-filter'
import Pagination from './Pagination'
import TableHead, { TableCells } from './TableHead'
import TableToolbar from './TableToolbar'
import { useTableColumns, TableColumn } from '../hooks/useTableColumns'
import { useFilterUrlWriter } from '../hooks/use-url-filters'
import TableScroll from './TableScroll'

export default function CrudList() {
  const { entity } = useParams()
  const cfg = cruds[entity || '']
  const { can } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  // Các key query mà thanh lọc cơ bản quản lý. Ô "daterange" sinh 2 param <key>_from / <key>_to
  // nên phải liệt kê cả hai, nếu không F5 sẽ mất khoảng ngày đang lọc.
  const filterKeys = useMemo(() => {
    const ks: string[] = []
    cfg?.filters?.forEach((f: any) => {
      if (f.type === 'daterange') ks.push(`${f.key}_from`, `${f.key}_to`)
      else ks.push(f.key)
    })
    return ks
  }, [cfg?.slug])

  // Filter khởi tạo từ URL query (chỉ nhận key khớp cfg.filters) — vd /purchase-orders?pr_code=PYC-001
  const urlFilters = useMemo(() => {
    const o: Record<string, string> = {}
    filterKeys.forEach((k) => { const v = searchParams.get(k); if (v) o[k] = v })
    return o
  }, [filterKeys, searchParams])

  // Ghi ngược bộ lọc lên URL để F5 / gửi link giữ nguyên bộ lọc đang xem
  const writeFilterUrl = useFilterUrlWriter(filterKeys)

  // Bộ lọc điều kiện (`<field>__<op>`) cũng nằm trên URL — đọc sẵn để lần nạp đầu tiên
  // (mở link chia sẻ / F5) đã đúng bộ lọc, không phải đợi provider bắn onChange.
  const urlCondParams = useMemo<RestQueryParams>(
    () => (cfg?.condFilters ? readParamsFromUrl(searchParams, cfg.condFilters) : {}),
    [cfg?.slug, searchParams],
  )

  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState<Record<string, string>>(urlFilters)
  const [condParams, setCondParams] = useState<RestQueryParams>(urlCondParams)
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [sortField, setSortField] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [serverPaged, setServerPaged] = useState(true)   // API trả mảng thô (vd /roles) -> sort client
  const [cloneMode, setCloneMode] = useState(false)   // bật/tắt cột "Thao tác" (nhân bản)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const cloneEnabled = !!cfg?.cloneable && can(cfg.entity, 'create')
  const showClone = cloneEnabled && cloneMode   // cột "Thao tác" chỉ hiện khi bật chế độ nhân bản

  // CR-068 — cột tick chọn dòng: bật ở các màn có Xuất Excel, để chọn đúng phiếu cần xuất.
  // Nút "Xóa đã chọn" (có sẵn từ trước nhưng chưa từng dùng được vì thiếu chỗ tick) vẫn TẮT,
  // phải bật riêng bằng cờ `bulkDelete` — thêm cột tick không đồng nghĩa mở đường xóa hàng loạt.
  const selectable = !!cfg?.exportXlsx
  const pageIds = useMemo(() => items.map((r) => r.id), [items])
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.includes(id))

  function toggleRow(id: number) {
    setSelectedIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])
  }
  function toggleAllOnPage() {
    setSelectedIds((prev) => allPageSelected
      ? prev.filter((id) => !pageIds.includes(id))
      : [...prev, ...pageIds.filter((id) => !prev.includes(id))])
  }

  // Khai báo cột 1 lần: dùng chung cho header (sort + kéo giãn) và các ô dữ liệu
  const tableColumns = useMemo<TableColumn<any>[]>(() => {
    if (!cfg) return []
    const list: TableColumn<any>[] = [
      { key: 'id', label: 'ID', sort: 'id', width: 80 },
      ...cfg.columns.map((c): TableColumn<any> => ({
        key: c.key,
        label: c.label,
        sort: c.key,
        cell: (row) => {
          const content = c.render ? c.render(row) : (row[c.key] ?? '')
          const href = c.link?.(row)
          return href ? (
            <span className="clickable" style={{ color: 'var(--teal)', fontWeight: 500 }}
              onClick={(e) => { e.stopPropagation(); navigate(href) }}>{content}</span>
          ) : content
        },
      })),
    ]
    if (selectable) {
      list.unshift({
        key: '__select', label: (
          <input type="checkbox" checked={allPageSelected} onChange={toggleAllOnPage}
            title="Chọn/bỏ chọn toàn bộ dòng trên trang này" />
        ), width: 44, align: 'center', fixed: true,
        cell: (row) => (
          <span onClick={(e) => e.stopPropagation()}>
            <input type="checkbox" checked={selectedIds.includes(row.id)}
              onChange={() => toggleRow(row.id)} title="Chọn phiếu này để xuất Excel" />
          </span>
        ),
      })
    }
    if (showClone) {
      list.push({
        key: '__clone', label: 'Thao tác', width: 110, align: 'center', fixed: true,
        cell: (row) => (
          <span onClick={(e) => e.stopPropagation()}>
            <button className="btn ghost" style={{ height: 30, padding: '0 10px' }}
              title="Nhân bản thành phiếu nháp mới" onClick={() => cloneRow(row.id, row.code)}>
              <i className="ti ti-copy" />Nhân bản
            </button>
          </span>
        ),
      })
    }
    return list
  }, [cfg?.slug, showClone, selectable, selectedIds, pageIds, allPageSelected])

  const table = useTableColumns(`crud:${entity || ''}`, tableColumns)

  function handleSort(field: string) {
    // Sort phía server: đổi hướng nếu cùng cột, ngược lại asc; luôn về trang 1
    const nextDir: 'asc' | 'desc' = (sortField === field && sortDir === 'asc') ? 'desc' : 'asc'
    setSortField(field)
    setSortDir(nextDir)
    setPage(1)
    load(1, pageSize, filters, field, nextDir)
  }

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
      toast.error('Lỗi khi xuất file');
    }
  }

  /** CR-068 — Xuất Excel: đúng bộ lọc đang đặt (hoặc đúng các dòng đã tick), đúng cột đang hiện.
   *  Mỗi dòng hàng của phiếu là một hàng trong file, cụm đầu phiếu lặp lại. */
  async function handleExportXlsx() {
    try {
      const params: any = { ...filters, ...condParams }
      if (sortField) { params.sort_by = sortField; params.sort_dir = sortDir }
      if (selectedIds.length > 0) params.ids = selectedIds.join(',')
      // Bỏ cột kỹ thuật (ID, cột Thao tác) — file xuất theo cột nghiệp vụ người dùng đang thấy
      params.cols = table.columns.map((c) => c.key)
        .filter((k) => k !== 'id' && !k.startsWith('__')).join(',')
      const r = await api.get(`${cfg.apiPath}/export/xlsx`, { params, responseType: 'blob' })
      // Tên file do backend đặt (kèm ngày xuất) — nằm ở Content-Disposition
      const cd = String(r.headers['content-disposition'] || '')
      const name = /filename="?([^"]+)"?/.exec(cd)?.[1] || `${cfg.slug}.xlsx`
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', name)
      document.body.appendChild(link)
      link.click()
      link.parentNode?.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      // responseType blob nên thông báo lỗi của backend cũng về dạng blob -> phải đọc ra text
      let msg = 'Lỗi khi xuất file Excel'
      try {
        const body = e?.response?.data
        const text = body instanceof Blob ? await body.text() : ''
        msg = JSON.parse(text)?.error?.message || msg
      } catch { /* giữ thông báo mặc định */ }
      toast.error(msg)
    }
  }

  const [confirmModal, setConfirmModal] = useState<{
    open: boolean; title: string; message: string;
    confirmText?: string; cancelText?: string; hideCancel?: boolean; variant?: 'danger' | 'warn' | 'info';
    onConfirm: () => void;
  }>({
    open: false, title: '', message: '', onConfirm: () => {},
  })

  async function handleDeleteSelected() {
    if (selectedIds.length === 0) return;

    // Nếu là purchase-requests, kiểm tra chỉ cho xóa phiếu Nháp
    if (cfg.slug === 'purchase-requests') {
      const nonDraftItems = items.filter(
        (item) => selectedIds.includes(item.id) && item.status !== 'draft'
      );
      if (nonDraftItems.length > 0) {
        setConfirmModal({
          open: true,
          title: 'Không thể xóa',
          message: `Không thể xóa item này do trạng thái không phải là Nháp.`,
          confirmText: 'Đã hiểu',
          hideCancel: true,
          variant: 'warn',
          onConfirm: () => setConfirmModal((prev) => ({ ...prev, open: false })),
        });
        return;
      }
    }

    setConfirmModal({
      open: true,
      title: 'Xác nhận xóa',
      message: `Bạn có chắc chắn muốn xóa ${selectedIds.length} bản ghi đã chọn?`,
      confirmText: 'Xóa',
      cancelText: 'Hủy',
      variant: 'danger',
      onConfirm: async () => {
        setConfirmModal((prev) => ({ ...prev, open: false }));
        try {
          await api.delete(cfg.apiPath, { params: { ids: selectedIds.join(',') } });
          setSelectedIds([]);
          load(page, pageSize, filters);
        } catch (e: any) {
          toast.error(e.response?.data?.message || 'Lỗi khi xóa dữ liệu');
        }
      },
    });
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
      toast.success(r.data.message || 'Nhập file thành công');
      load(page, pageSize, filters);
    } catch (e: any) {
      toast.error(e.response?.data?.message || 'Lỗi khi nhập file');
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  async function load(p = 1, s = 20, f: Record<string, string> = {},
                      sf: string | null = sortField, sd: 'asc' | 'desc' = sortDir,
                      c: RestQueryParams = condParams) {
    // Lọc cơ bản (LIKE) + lọc điều kiện (`<field>__<op>`) gộp chung vào 1 request
    const params: any = { ...f, ...c, page: p, page_size: s }
    if (sf) { params.sort_by = sf; params.sort_dir = sd }   // sort phía server
    const r = await api.get(cfg.apiPath, { params })
    const data = r.data.data
    if (Array.isArray(data)) {
      setItems(data)
      setTotal(data.length)
      setServerPaged(false)
    } else {
      setItems(data.items || [])
      setTotal(data.total || 0)
      setServerPaged(true)
    }
    setSelectedIds([])
  }

  // API phân trang -> backend đã sort; API trả mảng thô (vd /roles) -> sort tại client
  const displayItems = useMemo(() => {
    if (serverPaged || !sortField) return items
    const dir = sortDir === 'asc' ? 1 : -1
    return [...items].sort((a, b) => {
      const av = a[sortField!], bv = b[sortField!]
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv), 'vi') * dir
    })
  }, [items, serverPaged, sortField, sortDir])
  useEffect(() => {
    if (!cfg) return
    setPage(1); setPageSize(20); setFilters(urlFilters); setSortField(null); setSortDir('asc')
    setCondParams(urlCondParams)
    load(1, 20, urlFilters, null, 'asc', urlCondParams)
  }, [cfg?.slug])

  if (!cfg) return <div>Không tìm thấy trang.</div>

  // Chứng từ giao dịch (txn: PYC/PO/khảo sát/YCTT): ai có 'read' là xem danh sách được
  // (trưởng phòng duyệt, quản lý theo dõi...). Nút Thêm/Sửa/Xóa vẫn ẩn theo quyền cụ thể bên dưới.
  // Danh mục (company/product/...): chỉ QUẢN LÝ (write/create/delete) mới xem; người chỉ có 'read'
  // dùng cho dropdown, không xem danh sách.
  const canManage = can(cfg.entity, 'write') || can(cfg.entity, 'create') || can(cfg.entity, 'delete')
  const canView = cfg.txn ? can(cfg.entity, 'read') : canManage
  if (!canView) return (
    <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>
      <i className="ti ti-lock" style={{ fontSize: 34, color: '#cbd5e1' }} />
      <div style={{ marginTop: 12, fontSize: 15, color: 'var(--navy)', fontWeight: 600 }}>
        {cfg.txn ? 'Không có quyền xem danh sách này' : 'Không có quyền quản lý danh mục này'}
      </div>
      <div style={{ marginTop: 6, fontSize: 13 }}>
        {cfg.txn ? 'Bạn không có quyền xem chứng từ này.' : 'Bạn chỉ có quyền dùng dữ liệu này trong biểu mẫu (dropdown), không xem/quản lý danh sách.'}
      </div>
      <button className="btn" style={{ marginTop: 16 }} onClick={() => navigate('/')}><i className="ti ti-home" />Về Trang chủ</button>
    </div>
  )

  function applyFilters(f: Record<string, string>) {
    setFilters(f); setPage(1); writeFilterUrl(f); load(1, pageSize, f)
  }
  // Bộ lọc điều kiện đổi (áp dụng / bỏ chip / bấm back) -> nạp lại từ trang 1
  function applyCondFilters(c: RestQueryParams) {
    setCondParams(c); setPage(1); load(1, pageSize, filters, sortField, sortDir, c)
  }
  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s, filters) }

  async function doClone(id: number) {
    try {
      const r = await api.post(`${cfg.apiPath}/${id}/clone`)
      const created = r.data.data
      toast.success(r.data.message || 'Đã nhân bản')
      if (created?.id) navigate(`/${cfg.slug}/${created.id}`)   // nhảy thẳng vào chi tiết phiếu mới
      else load(page, pageSize, filters)
    } catch (e: any) {
      toast.error(e.response?.data?.error?.message || e.response?.data?.message || 'Lỗi khi nhân bản')
    }
  }
  function cloneRow(id: number, code?: string) {
    setConfirmModal({
      open: true,
      title: 'Nhân bản phiếu',
      message: `Bạn chắc chắn muốn nhân bản ${code ? `phiếu "${code}"` : 'phiếu này'}?\n\n`
        + 'Hệ thống sẽ tạo một phiếu MỚI ở trạng thái Nháp. Phiếu mới độc lập, '
        + 'KHÔNG giữ liên kết khảo sát / đơn mua hàng / phê duyệt của phiếu gốc.',
      confirmText: 'Nhân bản',
      cancelText: 'Hủy',
      variant: 'info',
      onConfirm: () => { setConfirmModal((prev) => ({ ...prev, open: false })); doClone(id) },
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 className="page-title" style={{ margin: 0 }}>{cfg.title}</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {selectedIds.length > 0 && cfg.bulkDelete && can(cfg.entity, 'delete') && (
            <button className="btn err" onClick={handleDeleteSelected}>
              <i className="ti ti-trash" />Xóa đã chọn ({selectedIds.length})
            </button>
          )}
          {cfg.exportXlsx && can(cfg.entity, 'export') && (
            <button className="btn outline" onClick={handleExportXlsx}
              title={selectedIds.length > 0
                ? `Xuất ${selectedIds.length} phiếu đã chọn ra Excel`
                : 'Xuất toàn bộ kết quả đang lọc ra Excel'}>
              <i className="ti ti-file-spreadsheet" />
              Xuất Excel{selectedIds.length > 0 ? ` (${selectedIds.length})` : ''}
            </button>
          )}
          {cfg.importExport && can(cfg.entity, 'write') && (
            <>
              <button className="btn outline" onClick={handleExport}><i className="ti ti-download" />Export CSV</button>
              <button className="btn outline" onClick={() => fileInputRef.current?.click()}><i className="ti ti-upload" />Import CSV</button>
              <input type="file" accept=".csv" ref={fileInputRef} style={{ display: 'none' }} onChange={handleImport} />
            </>
          )}
          {cloneEnabled && (
            <button className={cloneMode ? 'btn' : 'btn outline'} onClick={() => setCloneMode((v) => !v)}
              title="Bật chế độ nhân bản: hiện cột Thao tác để nhân bản từng phiếu">
              <i className="ti ti-copy" />{cloneMode ? 'Xong' : 'Nhân bản'}
            </button>
          )}
          {can(cfg.entity, 'create') && (
            <button className="btn" onClick={() => navigate(`/${cfg.slug}/new`)}><i className="ti ti-plus" />Thêm</button>
          )}
        </div>
      </div>

      {/* Nút mở bảng điều kiện nằm chung hàng với thanh lọc cơ bản (slot `extra`) */}
      {(() => {
        const bar = (
          <FilterBar key={cfg.slug} fields={cfg.filters} initial={urlFilters} onApply={applyFilters}
            extra={cfg.condFilters ? <ConditionalFilterButton /> : undefined} />
        )
        if (!cfg.condFilters) return bar
        return (
          <ConditionalFilter key={cfg.slug} fields={cfg.condFilters} onChange={applyCondFilters}>
            {bar}
          </ConditionalFilter>
        )
      })()}

      <div className="card table-card">
        <TableToolbar {...table} onRefresh={() => load(page, pageSize, filters)} />
        <TableScroll>
          <table>
            <TableHead {...table} sortBy={sortField} sortDir={sortDir} onSort={handleSort} />
            <tbody>
              {/* Sort phía server (danh sách phân trang) / phía client (mảng thô) */}
              {displayItems.map((row, i) => (
                <tr key={row.id} className="clickable" onClick={() => navigate(`/${cfg.slug}/${row.id}`)}>
                  <TableCells columns={table.columns} row={row} index={i} />
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={table.columns.length} className="table-empty">Không có dữ liệu</td></tr>
              )}
            </tbody>
          </table>
        </TableScroll>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
        </div>
      </div>

      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        confirmText={confirmModal.confirmText || 'Xác nhận'}
        cancelText={confirmModal.cancelText || 'Hủy'}
        hideCancel={confirmModal.hideCancel}
        variant={confirmModal.variant || 'danger'}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal((prev) => ({ ...prev, open: false }))}
      />
    </div>
  )
}
