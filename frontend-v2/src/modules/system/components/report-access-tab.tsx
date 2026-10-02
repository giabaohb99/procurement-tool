import { Pencil } from 'lucide-react'
import { useMemo, useState } from 'react'

import { SubjectChips } from '@/shared/access-subject/access-subject-chips'
import { EFFECT } from '@/shared/access-subject/subject-kind'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { useReportAccessList } from '../hooks/use-report-access'
import type { ReportAccessItem } from '../types/report-access'
import { ReportAccessDialog } from './report-access-dialog'

interface ReportAccessTabProps {
  /** `can('role', 'write')` — thiếu thì ẩn hẳn nút Sửa, không chỉ khóa. */
  canWrite: boolean
}

/**
 * Tab «Báo cáo» của Phân quyền tài khoản — 13 báo cáo (`ReportKey`, backend),
 * mỗi dòng hiện chủ thể được CHO PHÉP / bị CẤM. Nhóm/nhãn đọc thẳng từ API
 * (`report.group` / `report.label`) — không import danh mục của `modules/report`
 * để `system` khỏi dính ruột phân hệ khác.
 *
 * 13 dòng cố định, không phân trang — `DataTable` chỉ lo hiển thị + ẩn/hiện cột.
 */
export function ReportAccessTab({ canWrite }: ReportAccessTabProps) {
  const { data, isLoading, isError } = useReportAccessList()
  //  Giữ KHÓA của dòng, không giữ cả OBJECT — object bắt tại lúc bấm Sửa đứng
  //  im trong state, còn `data` nạp lại (sau gán/thu hồi) luôn là mảng MỚI.
  //  Giữ object cũ thì hộp thoại hiện đúng tên báo cáo nhưng SAI danh sách
  //  chủ thể: thu hồi lần 2 gửi `accessId` đã chết (404/400) vì người dùng
  //  đang nhìn một bản chụp cũ (M1, rà soát tính năng phân quyền từng báo cáo).
  const [editingKey, setEditingKey] = useState<number | null>(null)
  const editingReport = useMemo(
    () => data?.find((row) => row.key === editingKey) ?? null,
    [data, editingKey],
  )

  const columns = useMemo<DataTableColumn<ReportAccessItem>[]>(
    () => [
      { key: 'group', header: 'Phân hệ', width: 140, hideable: false, cell: (row) => row.group },
      { key: 'label', header: 'Báo cáo', width: 220, hideable: false, cell: (row) => row.label },
      {
        key: 'allowed',
        header: 'Được xem',
        wrap: true,
        cell: (row) => <AllowedCell row={row} />,
      },
      {
        key: 'denied',
        header: 'Bị cấm',
        wrap: true,
        cell: (row) => <DeniedCell row={row} />,
      },
      {
        key: 'actions',
        header: 'Sửa',
        width: 72,
        align: 'center',
        hideable: false,
        cell: (row) =>
          canWrite ? (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title={`Sửa quyền xem «${row.label}»`}
              aria-label={`Sửa quyền xem «${row.label}»`}
              onClick={() => setEditingKey(row.key)}
            >
              <Pencil />
            </Button>
          ) : null,
      },
    ],
    [canWrite],
  )

  return (
    <Card className="p-4">
      {/*  H1 (rà soát tính năng phân quyền từng báo cáo): quyền ở tab này CHỈ
           gác trang biểu đồ tổng hợp của phân hệ Báo cáo (`/report/*`) — màn
           bảng gốc ở từng phân hệ (vd Báo cáo mua hàng bên Thu mua) vẫn theo
           quyền vai trò như cũ, không đọc gì ở đây. Nói rõ ra chứ không để
           người cấu hình tưởng gán/cấm ở đây khóa luôn cả màn bảng gốc. */}
      <p className="mb-3 text-xs text-muted-foreground">
        Quyền ở đây chỉ quyết định ai xem được trang báo cáo trong phân hệ Báo
        cáo. Màn bảng gốc ở từng phân hệ vẫn theo quyền vai trò như cũ.
      </p>

      <DataTable
        columns={columns}
        rows={data}
        getRowId={(row) => row.key}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Chưa có báo cáo nào."
        errorMessage="Không tải được danh sách — thử tải lại trang."
        storageKey="system.report-access"
      />

      <ReportAccessDialog
        report={editingReport}
        onOpenChange={(open) => !open && setEditingKey(null)}
      />
    </Card>
  )
}

function AllowedCell({ row }: { row: ReportAccessItem }) {
  const allowed = row.grants.filter((grant) => grant.effect === EFFECT.allow)
  if (allowed.length === 0) {
    //  H1: nói rõ phạm vi — không ai xem được TRONG PHÂN HỆ BÁO CÁO, chứ
    //  không phải không ai xem được số liệu này ở bất cứ đâu (màn bảng gốc
    //  của phân hệ vẫn theo quyền vai trò, không liên quan dòng này).
    return (
      <span className="text-xs text-muted-foreground">
        Chưa gán — không ai xem được trong phân hệ Báo cáo
      </span>
    )
  }
  return (
    <SubjectChips
      items={allowed.map((grant) => ({
        key: String(grant.id),
        label: grant.subject_name || '(đã xóa)',
      }))}
    />
  )
}

function DeniedCell({ row }: { row: ReportAccessItem }) {
  const denied = row.grants.filter((grant) => grant.effect === EFFECT.deny)
  if (denied.length === 0) {
    return <span className="text-xs text-muted-foreground">—</span>
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {denied.map((grant) => (
        <Badge key={grant.id} variant="destructive" className="font-normal">
          {grant.subject_name || '(đã xóa)'}
        </Badge>
      ))}
    </div>
  )
}
