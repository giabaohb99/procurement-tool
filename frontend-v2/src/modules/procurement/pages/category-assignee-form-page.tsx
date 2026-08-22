import { ArrowLeft, Save, UserCheck, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { httpClient } from '@/core/api/http-client'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { MultiPicker } from '@/shared/ui/multi-picker'

interface Option {
  value: number
  label: string
}

export function CategoryAssigneeFormPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [itemGroups, setItemGroups] = useState<Option[]>([])
  const [employees, setEmployees] = useState<Option[]>([])
  const [rowByCat, setRowByCat] = useState<Record<number, number>>({})

  const [selectedCatIds, setSelectedCatIds] = useState<number[]>([])
  const [primaryId, setPrimaryId] = useState<number | 0>(0)
  const [backupId, setBackupId] = useState<number | 0>(0)

  const [saving, setSaving] = useState(false)

  const editCatId = Number(searchParams.get('cats')) || 0
  const editRowId = editCatId ? rowByCat[editCatId] : undefined

  // Load assignees map to resolve item_group_id -> row id (for audit log)
  const loadAssignees = async () => {
    try {
      const res = await httpClient.get<{ items: any[] }>('/api/category-assignees', {
        params: { page_size: 1000 },
      })
      const items = res.data?.items || (res.data as any)?.data?.items || []
      const map: Record<number, number> = {}
      items.forEach((x: any) => {
        map[x.item_group_id] = x.id
      })
      setRowByCat(map)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    // Load item groups
    httpClient
      .get<{ items: any[] }>('/api/item-groups', { params: { page_size: 1000 } })
      .then((res) => {
        const items = res.data?.items || (res.data as any)?.data?.items || []
        const opts = items.map((x: any) => ({
          value: x.id,
          label: x.name,
        }))
        setItemGroups(opts)
      })

    // Load employees
    httpClient
      .get<{ items: any[] }>('/api/employees', { params: { page_size: 1000 } })
      .then((res) => {
        const items = res.data?.items || (res.data as any)?.data?.items || []
        const opts = items.map((x: any) => ({
          value: x.id,
          label: `${x.full_name}${x.code ? ` · ${x.code}` : ''}`,
        }))
        setEmployees(opts)
      })

    loadAssignees()
  }, [])

  // Prefill from query params when editing / copying
  useEffect(() => {
    const p = Number(searchParams.get('primary')) || 0
    const b = Number(searchParams.get('backup')) || 0
    const c = Number(searchParams.get('cats')) || 0

    if (p) setPrimaryId(p)
    if (b) setBackupId(b)
    if (c) setSelectedCatIds([c])
  }, [searchParams])

  const handleSave = async () => {
    if (selectedCatIds.length === 0) {
      toast.error('Vui lòng chọn ít nhất 1 phân loại')
      return
    }
    if (!primaryId) {
      toast.error('Vui lòng chọn NSTM chính')
      return
    }

    setSaving(true)
    try {
      await httpClient.post('/api/category-assignees/bulk', {
        item_group_ids: selectedCatIds,
        primary_employee_id: primaryId,
        backup_employee_id: backupId || 0,
      })
      toast.success(`Đã lưu phân công cho ${selectedCatIds.length} phân loại`)
      await loadAssignees()

      if (!editRowId) {
        navigate(appRoutes.procurement.categoryAssignees)
      }
    } catch (e: any) {
      toast.error(e.response?.data?.message || 'Lỗi khi lưu phân công')
    } finally {
      setSaving(false)
    }
  }

  const editCatLabel = useMemo(() => {
    if (!editCatId) return ''
    return itemGroups.find((c) => c.value === editCatId)?.label || ''
  }, [editCatId, itemGroups])

  const multiPickerOptions = useMemo(() => {
    return itemGroups.map((g) => ({ id: g.value, label: g.label }))
  }, [itemGroups])

  return (
    <div className="space-y-6 p-6 max-w-5xl mx-auto">
      {/* Top Header Toolbar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigate(appRoutes.procurement.categoryAssignees)}
            title="Quay lại danh sách"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              {editCatLabel ? `Sửa phân công: ${editCatLabel}` : 'Gán phân công phụ trách'}
            </h1>
            <p className="text-sm text-muted-foreground">
              Phân công Nhân sự thu mua chịu trách nhiệm xử lý các dòng YCMH theo phân loại.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => navigate(appRoutes.procurement.categoryAssignees)}
          >
            Hủy
          </Button>
          <Button onClick={handleSave} disabled={saving} className="shadow-sm">
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Đang lưu…' : 'Lưu phân công'}
          </Button>
        </div>
      </div>

      {/* Form Content */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Card className="p-6 space-y-6">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <UserCheck className="h-5 w-5 text-primary" />
              Thông tin phân công NSTM
            </h2>

            {/* Item Groups Picker */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none flex items-center justify-between">
                <span>
                  Phân loại VTBB <span className="text-red-500">*</span>
                </span>
                <span className="text-xs text-muted-foreground font-normal">
                  Đã chọn {selectedCatIds.length} phân loại
                </span>
              </label>

              <MultiPicker<number>
                options={multiPickerOptions}
                value={selectedCatIds}
                onChange={(ids) => setSelectedCatIds(ids)}
                placeholder="Chọn một hoặc nhiều phân loại…"
                searchPlaceholder="Tìm phân loại…"
              />
              <p className="text-xs text-muted-foreground">
                Có thể chọn nhiều phân loại để gán NSTM chính/dự phòng hàng loạt.
              </p>
            </div>

            {/* Primary Employee */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">
                NSTM chính <span className="text-red-500">*</span>
              </label>
              <select
                value={String(primaryId || '')}
                onChange={(e) => setPrimaryId(Number(e.target.value) || 0)}
                className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">-- Chọn Nhân sự thu mua chính --</option>
                {employees.map((e) => (
                  <option key={e.value} value={String(e.value)}>
                    {e.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                Nhân viên này sẽ được hệ thống ưu tiên tự động gán xử lý các dòng thuộc phân loại
                trên YCMH.
              </p>
            </div>

            {/* Backup Employee */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none">NSTM dự phòng (tùy chọn)</label>
              <select
                value={String(backupId || '')}
                onChange={(e) => setBackupId(Number(e.target.value) || 0)}
                className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">-- Không có dự phòng --</option>
                {employees.map((e) => (
                  <option key={e.value} value={String(e.value)}>
                    {e.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                Được gán xử lý khi NSTM chính vắng mặt hoặc được ủy quyền.
              </p>
            </div>
          </Card>
        </div>

        {/* Audit Timeline Sidebar */}
        <div className="space-y-6">
          <Card className="p-6 space-y-4">
            <h3 className="text-md font-semibold flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              Lịch sử thao tác
            </h3>
            {editRowId ? (
              <AuditTimeline entity="category_assignee" entityId={editRowId} />
            ) : (
              <p className="text-sm text-muted-foreground italic">
                Lịch sử thay đổi sẽ hiển thị khi xem/sửa bản ghi phân công đã lưu.
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
