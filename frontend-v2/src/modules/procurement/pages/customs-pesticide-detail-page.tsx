// CHI TIẾT MỘT THUỐC BVTV — `/procurement/customs-prices/pesticides/:id` (duoc-CR-492, 29/09/2026).
//
// Trang riêng thay cho hộp thoại cũ (đại ca chốt): hộp thoại phải nhét nút Sửa/Xóa chen giữa tiêu đề
// và thông tin, và bảng phạm vi sử dụng dưới đáy không có tiêu đề đủ rõ để biết nó là gì. Trang đi
// theo khuôn mọi màn chi tiết của v2: tiêu đề + nút ở đầu, thẻ thông tin, bảng phạm vi có tiêu đề
// + câu giải thích, tệp đính kèm (duoc-CR-494), lịch sử thao tác cuối trang.
//
// Gác quyền: đường này nằm DƯỚI mục menu «Thuốc BVTV» (`customs_price.read`) nên `canAccessRoute` tự
// gác; nút Sửa / Xóa theo khóa riêng `customs_pesticide` (duoc-CR-490).
import { ArrowLeft, Pencil } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { AuditTimeline } from '@/shared/audit'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useBackTarget } from '@/shared/hooks/use-back-target'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { DocumentAttachmentsCard } from '../components/document-attachments-card'
import { CustomsPesticideFormDialog } from '../components/customs/customs-pesticide-form-dialog'
import {
  CustomsPesticideBannedNotice,
  CustomsPesticideInfoCard,
} from '../components/customs/customs-pesticide-info-card'
import { CustomsPesticideStatusBadge } from '../components/customs/customs-pesticide-status-badge'
import { buildCustomsSectionPath } from '../config/customs-sections'
import {
  useCustomsPesticide,
  useDeleteCustomsPesticide,
  usePesticidePermissions,
} from '../hooks/use-customs-pesticides'
import type { CustomsPesticideUse } from '../types/customs-pesticide'
import { toPesticideInput } from '../utils/customs-pesticide-form'

const USE_COLUMNS: DataTableColumn<CustomsPesticideUse>[] = [
  { key: 'crop', header: 'Cây trồng', width: 150, wrap: true, cell: (row) => row.crop },
  { key: 'pest', header: 'Dịch hại', width: 180, wrap: true, cell: (row) => row.pest },
  { key: 'dosage', header: 'Liều lượng', width: 150, wrap: true, cell: (row) => row.dosage },
  {
    key: 'pre_harvest_interval',
    header: 'Thời gian cách ly',
    width: 140,
    wrap: true,
    cell: (row) => row.pre_harvest_interval,
  },
  { key: 'usage', header: 'Cách dùng', width: 380, wrap: true, cell: (row) => row.usage },
]

export function CustomsPesticideDetailPage() {
  const { id } = useParams<{ id: string }>()
  const pesticideId = Number(id) || 0
  const navigate = useNavigate()
  const back = useBackTarget(buildCustomsSectionPath('pesticides'))
  const { canCreate, canEdit, canDelete } = usePesticidePermissions()
  const [editing, setEditing] = useState(false)
  const { data, isLoading } = useCustomsPesticide(pesticideId || null)
  const remove = useDeleteCustomsPesticide()

  const backButton = (
    <Button
      variant="outline"
      size="icon"
      title="Quay lại danh mục thuốc BVTV"
      aria-label="Quay lại danh mục thuốc BVTV"
      onClick={() => navigate(back.url)}
    >
      <ArrowLeft className="size-4" />
    </Button>
  )

  if (isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải thuốc BVTV…</p>
      </PageContainer>
    )
  }
  if (!data) {
    return (
      <PageContainer>
        <PageHeader leading={backButton} title="Không tìm thấy thuốc BVTV" />
        <p className="text-sm text-muted-foreground">
          Thuốc này không còn trong danh mục — có thể đã bị xóa, hoặc đã thay bằng lần nạp danh mục mới.
        </p>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        leading={backButton}
        title={
          <span className="flex flex-wrap items-center gap-2">
            {data.trade_name}
            <CustomsPesticideStatusBadge status={data.status} label={data.status_label} />
            {data.is_manual && <Badge variant="outline">Tự thêm</Badge>}
          </span>
        }
        description={[data.pest_group, data.registration_no].filter(Boolean).join(' · ') || 'Thuốc bảo vệ thực vật'}
        actions={
          canEdit || canDelete ? (
            <>
              {canEdit && (
                <Button type="button" variant="outline" onClick={() => setEditing(true)}>
                  <Pencil className="size-4" />
                  Sửa
                </Button>
              )}
              {canDelete && (
                <DeleteConfirmButton
                  recordName={data.trade_name}
                  pending={remove.isPending}
                  warning={
                    data.is_manual
                      ? undefined
                      : 'Thuốc này lấy từ bản cào — lần «Nạp danh mục» sau sẽ thêm lại nó theo nguồn.'
                  }
                  onConfirm={async () => {
                    await remove.mutateAsync(data.id)
                    navigate(back.url, { replace: true })
                  }}
                />
              )}
            </>
          ) : undefined
        }
      />

      <div className="space-y-4">
        <CustomsPesticideBannedNotice items={data.banned} />
        <CustomsPesticideInfoCard pesticide={data} />

        <DataTable
          columns={USE_COLUMNS}
          rows={data.uses}
          getRowId={(use) => use.id}
          emptyMessage={
            data.is_manual
              ? 'Chưa nhập phạm vi sử dụng nào — bấm «Sửa» để thêm.'
              : 'Nguồn không ghi phạm vi sử dụng cho thuốc này.'
          }
          storageKey="procurement.customs-pesticide-uses-v1"
          //  Tiêu đề nằm NGAY trên hàng công cụ của bảng: đặt riêng phía trên thì hai nút Tải lại / Cột
          //  chen giữa tiêu đề và bảng, người đọc không nối được chữ với bảng (đại ca góp ý 29/09).
          toolbar={
            <div className="min-w-0">
              <h2 className="text-base font-semibold">Phạm vi sử dụng ({data.uses.length})</h2>
              <p className="text-xs text-muted-foreground">
                Thuốc được đăng ký dùng cho cây trồng nào, trị dịch hại gì, liều lượng bao nhiêu và
                phải ngừng phun trước thu hoạch bao lâu (thời gian cách ly).
              </p>
            </div>
          }
        />

        {/*  duoc-CR-494 — tệp của thuốc (nhãn, giấy chứng nhận đăng ký, MSDS…). Xem theo quyền xem
             màn (`READ_PARENT` ở backend); tải lên / xóa khớp `_check` backend: `write` HOẶC
             `create` trên `customs_pesticide`. Tệp giữ qua các lần «Nạp danh mục» vì id thuốc giữ. */}
        <DocumentAttachmentsCard
          entity="customs_pesticide"
          entityId={data.id}
          canManage={canEdit || canCreate}
        />

        <AuditTimeline entity="customs_pesticide" entityId={data.id} showMessage />
      </div>

      {editing && (
        <CustomsPesticideFormDialog
          pesticideId={data.id}
          initial={toPesticideInput(data)}
          fromSource={!data.is_manual}
          onClose={() => setEditing(false)}
          onSaved={() => setEditing(false)}
        />
      )}
    </PageContainer>
  )
}
