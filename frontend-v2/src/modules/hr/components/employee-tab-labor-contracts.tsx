import { Plus } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'

import { DataTable } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { sortRowsByCell } from '@/shared/utils/sort-rows-by-cell'
import { laborContractApi } from '../api/labor-contract-api'
import {
  buildEmployeeLaborContractColumns,
  EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS,
} from '../config/employee-labor-contract-columns'
import {
  useDeleteLaborContract,
  useEmployeeLaborContracts,
  useUploadSignedLaborContract,
} from '../hooks/use-employee-labor-contracts'
import { useLocalTableSort } from '../hooks/use-local-table-sort'
import type { EmployeeDetail } from '../types/employee'
import type { LaborContract } from '../types/labor-contract'
import { LaborContractCard } from './labor-contract-card'
import { LaborContractFormDialog } from './labor-contract-form-dialog'
import { LaborContractGenerateDialog } from './labor-contract-generate-dialog'
import type { LaborContractRowActionHandlers } from './labor-contract-row-actions'
import { LaborContractTransitionDialog, type PendingTransition } from './labor-contract-transition-dialog'

interface EmployeeTabLaborContractsProps {
  employee: EmployeeDetail
}

/** Tên gợi ý khi server không gửi tên tệp. */
const fallbackName = (row: LaborContract, ext: string) => `HDLD-${row.contract_no || row.code}.${ext}`

/**
 * Tab "Hợp đồng" ở hồ sơ nhân sự. CHỈ được dựng khi người xem có `labor_contract.read`
 * (trang cha gác) — nên lương không bao giờ render ra cho người không có quyền, và không có
 * lượt gọi API nào lúc mount để ăn toast 403.
 *
 * Hiện/ẩn nút theo cờ BACKEND trả (`can_*`, `transitions`), không tự ghép `can()`.
 */
export function EmployeeTabLaborContracts({ employee }: EmployeeTabLaborContractsProps) {
  const { data, isLoading, isError } = useEmployeeLaborContracts(employee.id, true)
  const deleteMutation = useDeleteLaborContract(employee.id)
  const uploadMutation = useUploadSignedLaborContract(employee.id)

  const [formOpen, setFormOpen] = useState(false)
  const [editRow, setEditRow] = useState<LaborContract | null>(null)
  const [generateRow, setGenerateRow] = useState<LaborContract | null>(null)
  const [pending, setPending] = useState<PendingTransition | null>(null)
  const [busyIds, setBusyIds] = useState<ReadonlySet<number>>(new Set())
  //  duoc-CR-748: bấm tiêu đề cột xếp ngay ở trình duyệt — API trả đủ mọi hợp đồng của người này, không phân trang.
  const sort = useLocalTableSort()
  const items = data?.items
  const rows = useMemo(
    () => items && sortRowsByCell(items, sort.sortBy, sort.sortDir, EMPLOYEE_LABOR_CONTRACT_SORT_GETTERS),
    [items, sort.sortBy, sort.sortDir],
  )

  /** Chạy một lệnh gọi trên dòng, khóa nút của dòng đó trong lúc chạy. Lỗi đã được toast sẵn. */
  const runOnRow = useCallback(async (id: number, task: () => Promise<unknown>) => {
    setBusyIds((prev) => new Set(prev).add(id))
    try {
      await task()
    } catch {
      //  http-client đã toast câu lỗi tiếng Việt của backend.
    } finally {
      setBusyIds((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }, [])

  //  Bộ hàm thao tác dùng CHUNG cho cột Thao tác của bảng và nút "⋯" của thẻ khổ điện thoại — hai
  //  lối bày một dòng phải gọi đúng một luồng (xác nhận xóa, khóa nút khi đang chạy).
  const handlers = useMemo<LaborContractRowActionHandlers>(
    () => ({
      onEdit: (r) => {
        setEditRow(r)
        setFormOpen(true)
      },
      onGenerate: setGenerateRow,
      onDownloadDocument: (r) =>
        void runOnRow(r.id, () => laborContractApi.downloadDocument(r.id, fallbackName(r, 'docx'))),
      onUploadSigned: (r, file) =>
        void runOnRow(r.id, () => uploadMutation.mutateAsync({ id: r.id, file })),
      onDownloadSigned: (r) =>
        void runOnRow(r.id, () => laborContractApi.downloadSignedFile(r.id, fallbackName(r, 'pdf'))),
      onTransition: (row, spec) => setPending({ row, spec }),
      onDelete: (r) =>
        void runOnRow(r.id, async () => {
          const ok = await confirm({
            title: 'Xóa hợp đồng',
            message: `Xóa hợp đồng ${r.contract_no || r.code}? Tệp đã sinh và bản ký (nếu có) cũng bị xóa.`,
            confirmLabel: 'Xóa',
          })
          if (ok) await deleteMutation.mutateAsync(r.id)
        }),
    }),
    [runOnRow, uploadMutation, deleteMutation],
  )

  const columns = useMemo(
    () =>
      buildEmployeeLaborContractColumns({
        isBusy: (r) => busyIds.has(r.id),
        canReadSigned: true,
        ...handlers,
      }),
    [busyIds, handlers],
  )

  function openCreate() {
    setEditRow(null)
    setFormOpen(true)
  }

  return (
    <div className="flex flex-col gap-4">
      <DataTable
        columns={columns}
        rows={rows}
        getRowId={(r) => r.id}
        sortBy={sort.sortBy}
        sortDir={sort.sortDir}
        onSortChange={sort.onSortChange}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Không tải được danh sách hợp đồng."
        emptyMessage="Nhân sự này chưa có hợp đồng lao động nào."
        storageKey="hr.employee-labor-contracts"
        mobileCard={(r) => <LaborContractCard row={r} busy={busyIds.has(r.id)} canReadSigned {...handlers} />}
        filtersActive={false}
        toolbar={<h3 className="text-sm font-semibold">Hợp đồng lao động</h3>}
        toolbarEnd={
          data?.can_create ? (
            <Button type="button" size="sm" onClick={openCreate}>
              <Plus className="size-4" />
              Lập hợp đồng
            </Button>
          ) : undefined
        }
      />

      <LaborContractFormDialog open={formOpen} onOpenChange={setFormOpen} employee={employee} row={editRow} />
      <LaborContractGenerateDialog row={generateRow} employeeId={employee.id} onClose={() => setGenerateRow(null)} />
      <LaborContractTransitionDialog pending={pending} employeeId={employee.id} onClose={() => setPending(null)} />
    </div>
  )
}
