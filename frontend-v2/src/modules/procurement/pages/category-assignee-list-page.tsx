import { Pencil, Plus, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { httpClient } from '@/core/api/http-client'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table/data-table'
import type { DataTableColumn } from '@/shared/data-table/types'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import type { CategoryAssignee } from '../types/category-assignee'

interface ItemGroupOption {
  id: number
  name: string
}

export function CategoryAssigneeListPage() {
  const { can } = usePermission()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const canCreate = can('category_assignee', 'create')
  const canDelete = can('category_assignee', 'delete')

  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<CategoryAssignee[]>([])
  const [itemGroups, setItemGroups] = useState<ItemGroupOption[]>([])

  const search = searchParams.get('search') || ''
  const catFilter = searchParams.get('cat') || 'all'
  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const pageSize = Number(searchParams.get('pageSize')) || 20

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await httpClient.get<{ items: CategoryAssignee[]; total: number }>(
        '/api/category-assignees',
        {
          params: {
            page_size: 1000,
          },
        },
      )
      setItems(res.data?.items || (res.data as any)?.data?.items || [])
    } catch {
      toast.error('Không thể tải danh sách phân công phụ trách')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    httpClient
      .get<{ items: ItemGroupOption[] }>('/api/item-groups', { params: { page_size: 1000 } })
      .then((res) => setItemGroups(res.data?.items || (res.data as any)?.data?.items || []))
      .catch(() => {})
  }, [])

  const handleDelete = async (row: CategoryAssignee) => {
    if (!window.confirm(`Xóa phân công của phân loại "${row.item_group_name || 'này'}"?`)) {
      return
    }
    try {
      await httpClient.delete(`/api/category-assignees/${row.id}`)
      toast.success('Đã xóa phân công phụ trách')
      loadData()
    } catch {
      toast.error('Không thể xóa phân công')
    }
  }

  // Lọc client theo từ khóa tìm kiếm & phân loại chọn
  const filteredItems = useMemo(() => {
    return items.filter((row) => {
      if (catFilter !== 'all' && String(row.item_group_id) !== catFilter) {
        return false
      }
      if (!search.trim()) return true
      const q = search.trim().toLowerCase()
      const igName = (row.item_group_name || '').toLowerCase()
      const pName = (row.primary_name || '').toLowerCase()
      const pCode = (row.primary_code || '').toLowerCase()
      const bName = (row.backup_name || '').toLowerCase()
      const bCode = (row.backup_code || '').toLowerCase()

      return (
        igName.includes(q) ||
        pName.includes(q) ||
        pCode.includes(q) ||
        bName.includes(q) ||
        bCode.includes(q)
      )
    })
  }, [items, search, catFilter])

  // Phân trang client
  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredItems.slice(start, start + pageSize)
  }, [filteredItems, page, pageSize])

  const columns: DataTableColumn<CategoryAssignee>[] = useMemo(
    () => [
      {
        key: 'item_group_name',
        header: 'Phân loại',
        width: 320,
        sortable: true,
        cell: (r) => (
          <div className="flex items-center gap-2 font-medium text-foreground">
            <Badge variant="outline" className="bg-sky-50 text-sky-700 border-sky-200">
              {r.item_group_name || 'Chưa phân loại'}
            </Badge>
          </div>
        ),
      },
      {
        key: 'primary_name',
        header: 'NSTM chính',
        width: 280,
        sortable: true,
        cell: (r) =>
          r.primary_name ? (
            <div className="flex flex-col">
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {r.primary_name}
              </span>
              {r.primary_code && (
                <span className="text-xs text-muted-foreground font-mono">{r.primary_code}</span>
              )}
            </div>
          ) : (
            <span className="text-muted-foreground font-light">—</span>
          ),
      },
      {
        key: 'backup_name',
        header: 'NSTM dự phòng',
        width: 280,
        sortable: true,
        cell: (r) =>
          r.backup_name ? (
            <div className="flex flex-col">
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {r.backup_name}
              </span>
              {r.backup_code && (
                <span className="text-xs text-muted-foreground font-mono">{r.backup_code}</span>
              )}
            </div>
          ) : (
            <span className="text-muted-foreground font-light">—</span>
          ),
      },
      {
        key: 'actions',
        header: 'Thao tác',
        width: 140,
        align: 'right',
        cell: (r) => (
          <div className="flex items-center justify-end gap-1">
            {canCreate && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-muted-foreground hover:text-primary"
                title="Chỉnh sửa phân công"
                onClick={() =>
                  navigate(
                    `${appRoutes.procurement.categoryAssigneeNew}?cats=${r.item_group_id}&primary=${r.primary_employee_id}&backup=${r.backup_employee_id}`,
                  )
                }
              >
                <Pencil className="h-4 w-4 mr-1" />
                Sửa
              </Button>
            )}
            {canDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-destructive hover:bg-destructive/10 hover:text-destructive"
                title="Xóa phân công"
                onClick={() => handleDelete(r)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        ),
      },
    ],
    [canCreate, canDelete, navigate],
  )

  const updateParam = (key: string, val: string) => {
    const p = new URLSearchParams(searchParams)
    if (val) p.set(key, val)
    else p.delete(key)
    p.set('page', '1')
    setSearchParams(p)
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Phân công phụ trách</h1>
            <Badge variant="secondary" className="font-mono">
              {filteredItems.length} phân loại
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Tự động gán Nhân sự thu mua (NSTM) chính & dự phòng theo từng phân loại khi Duyệt Yêu
            cầu mua hàng (PYC).
          </p>
        </div>

        {canCreate && (
          <Button
            onClick={() => navigate(appRoutes.procurement.categoryAssigneeNew)}
            className="shadow-sm"
          >
            <Plus className="h-4 w-4 mr-2" />
            Gán phân công mới
          </Button>
        )}
      </div>

      {/* Main Table Card */}
      <Card className="p-4">
        <DataTable
          columns={columns}
          rows={paginatedItems}
          getRowId={(r) => r.id}
          isLoading={loading}
          storageKey="procurement.category-assignees"
          pagination={{
            page,
            pageSize,
            total: filteredItems.length,
            unitLabel: 'phân loại',
            onPageChange: (p) => updateParam('page', String(p)),
            onPageSizeChange: (s) => updateParam('pageSize', String(s)),
          }}
          toolbar={
            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
              <Input
                placeholder="Tìm theo phân loại, tên hoặc mã NSTM…"
                value={search}
                onChange={(e) => updateParam('search', e.target.value)}
                className="h-9 w-full sm:w-72"
              />

              <select
                value={catFilter}
                onChange={(e) => updateParam('cat', e.target.value)}
                className="h-9 w-full sm:w-56 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="all">Tất cả phân loại</option>
                {itemGroups.map((g) => (
                  <option key={g.id} value={String(g.id)}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
          }
        />
      </Card>
    </div>
  )
}
