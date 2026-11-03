import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { DataTable } from '@/shared/data-table'
import { buildLeavePolicyAssignmentColumns } from '../config/leave-policy-assignment-columns'
import { useLeavePolicyAssignments } from '../hooks/use-leave-policy'
import { buildAssignmentListHref } from '../utils/leave-policy-display'

interface LeavePolicyAssignmentsTabProps {
  policyId: number
}

/**
 * Tab "Đang phân bổ" của một chính sách (duoc-CR-717) — bảng CHỈ ĐỌC: ai đang / đã / sắp được gán gói
 * này. Sửa (kết thúc, xóa) làm ở màn Phân bổ chính sách — bấm dòng là sang đó, đã lọc sẵn.
 *
 * Gác `leave_balance.read` (khóa của phân bổ), không phải `leave_type`: người khai danh mục chưa chắc
 * được xem phân bổ của từng người. Thiếu quyền thì KHÔNG gọi API (mount là ăn lỗi 403).
 *
 * Dòng chỉ BẤM ĐƯỢC khi có `leave_balance.write` — màn Phân bổ chính sách gác `write` (chỉ nhân sự), chỉ
 * đọc mà vẫn cho bấm là dẫn người ta tới trang bị chặn.
 */
export function LeavePolicyAssignmentsTab({ policyId }: LeavePolicyAssignmentsTabProps) {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canRead = can('leave_balance', 'read')
  const canOpenList = can('leave_balance', 'write')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { data, isLoading, isError } = useLeavePolicyAssignments(
    { policy_id: policyId, page, page_size: pageSize },
    { enabled: canRead },
  )
  const columns = useMemo(() => buildLeavePolicyAssignmentColumns({ showPolicy: false }), [])

  if (!canRead) {
    return (
      <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
        Bạn không có quyền xem phân bổ chính sách (cần quyền xem Quỹ phép năm).
      </p>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Ai đang, đã hoặc sắp được gán chính sách này.
        {canOpenList && ' Bấm một dòng để kết thúc hoặc xóa ở màn Phân bổ chính sách.'}
      </p>
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(a) => a.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Chưa phân bổ chính sách này cho ai."
        storageKey="hr.leave-policy-assignments-tab"
        onRowClick={canOpenList ? (a) => navigate(buildAssignmentListHref(policyId, a)) : undefined}
        getRowHref={canOpenList ? (a) => buildAssignmentListHref(policyId, a) : undefined}
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
          unitLabel: 'phân bổ',
        }}
      />
    </div>
  )
}
