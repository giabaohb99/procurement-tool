import { Plus } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import type { EmployeeConcurrentRowActions } from '../config/employee-concurrent-columns'
import { useDeleteEmployeeConcurrent, useEmployeeConcurrents } from '../hooks/use-employee-concurrents'
import { useBusyIds } from '../hooks/use-employee-work-history-row-apply'
import type { Employee } from '../types/employee'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { EmployeeConcurrentFilesDialog } from './employee-concurrent-files-dialog'
import { EmployeeConcurrentFormDialog } from './employee-concurrent-form-dialog'
import { EmployeeConcurrentTable } from './employee-concurrent-table'

interface EmployeeTabConcurrentProps {
  employee: Employee
}

/** Hộp thêm/sửa: `closed` · `create` · dòng đang sửa. */
type EditorState = { mode: 'closed' } | { mode: 'create' } | { mode: 'edit'; row: EmployeeConcurrent }

/**
 * Tab **Kiêm nhiệm** của hồ sơ nhân sự (duoc-CR-755; hai loại dòng ở duoc-CR-756) — thay thẻ chọn nhiều phòng cũ ở tab
 * Chung.
 *
 * Mỗi dòng là MỘT phòng ban của công ty hiện tại (loại Phòng ban) hoặc MỘT công ty khác (loại Công ty) người này phụ
 * trách thêm, có ngày, quyết định và công tắc phạm vi quyền. Hồ sơ chưa gắn pháp nhân chính thì backend chặn 400 cả hai
 * loại — nút Thêm tắt kèm câu giải thích, không để người dùng điền hết hộp rồi mới ăn lỗi. Được sửa /
 * được mở tệp lấy từ cờ BACKEND (`can_edit`, `can_open_files`) — không tự ghép `can()`: `can_edit` đã gồm L1 (không ai
 * tự sửa kiêm nhiệm của chính mình, kể cả quản trị). Chốt cuối vẫn ở backend (L2 theo loại, chồng giai đoạn, trần 30 dòng).
 */
export function EmployeeTabConcurrent({ employee }: EmployeeTabConcurrentProps) {
  const { user } = useAuth()
  const { data, isLoading, isError } = useEmployeeConcurrents(employee.id)
  const deleteMutation = useDeleteEmployeeConcurrent(employee.id)
  const deleting = useBusyIds()

  const [editor, setEditor] = useState<EditorState>({ mode: 'closed' })
  const [filesRow, setFilesRow] = useState<EmployeeConcurrent | null>(null)

  const canEdit = data?.can_edit ?? false
  const canOpenFiles = data?.can_open_files ?? false
  const isOwnProfile = Boolean(user?.employee_id) && user?.employee_id === employee.id
  const hasPrimaryCompany = employee.company_id > 0

  const openFiles = useCallback((row: EmployeeConcurrent) => setFilesRow(row), [])
  const { run: runDelete, ids: deletingIds } = deleting
  const actions = useMemo<EmployeeConcurrentRowActions | undefined>(
    () =>
      canEdit
        ? {
            onEdit: (row) => setEditor({ mode: 'edit', row }),
            onDelete: (row) => runDelete(row.id, (done) => deleteMutation.mutate(row.id, { onSettled: done })),
            isDeleting: (row) => deletingIds.has(row.id),
          }
        : undefined,
    [canEdit, runDelete, deletingIds, deleteMutation],
  )

  const addButton = canEdit ? (
    //  `type="button"`: tab nằm TRONG `<form>` của trang hồ sơ — thiếu là bấm Thêm thành lưu cả hồ sơ.
    <Button
      type="button"
      disabled={!hasPrimaryCompany}
      title={hasPrimaryCompany ? undefined : 'Gắn pháp nhân chính cho hồ sơ trước'}
      onClick={() => setEditor({ mode: 'create' })}
    >
      <Plus className="size-4" />
      Thêm kiêm nhiệm
    </Button>
  ) : undefined

  return (
    <div className="flex flex-col gap-3">
      {!isLoading && !isError && !canEdit && isOwnProfile && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Đây là hồ sơ của chính bạn nên chỉ xem được — kiêm nhiệm của bạn do người khác cập nhật.
        </p>
      )}

      {!isLoading && !isError && canEdit && !hasPrimaryCompany && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Hồ sơ chưa gắn pháp nhân chính nên chưa thêm được kiêm nhiệm. Chọn Pháp nhân ở tab Chung rồi Lưu trước.
        </p>
      )}

      <Card className="gap-4 p-3 sm:p-5">
        <EmployeeConcurrentTable
          items={data?.items}
          isLoading={isLoading}
          isError={isError}
          canOpenFiles={canOpenFiles}
          onOpenFiles={openFiles}
          actions={actions}
          addButton={addButton}
        />
      </Card>

      <EmployeeConcurrentFormDialog
        open={editor.mode !== 'closed'}
        onOpenChange={(next) => !next && setEditor({ mode: 'closed' })}
        employee={employee}
        row={editor.mode === 'edit' ? editor.row : null}
        canOpenFiles={canOpenFiles}
      />

      <EmployeeConcurrentFilesDialog
        open={Boolean(filesRow)}
        onOpenChange={(next) => !next && setFilesRow(null)}
        concurrentId={filesRow?.id ?? 0}
        employeeId={employee.id}
        editable={canEdit}
      />
    </div>
  )
}
