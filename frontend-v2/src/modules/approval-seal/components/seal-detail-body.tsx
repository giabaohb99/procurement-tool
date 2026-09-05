import { Card } from '@/shared/ui/card'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatDateTime } from '@/shared/utils/format-date'
import type { SealRequest } from '../types/seal-request'

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}

/** Thân chi tiết phiếu đóng dấu — thẻ Thông tin yêu cầu · Người tạo · Ghi chú. */
export function SealDetailBody({ request }: { request: SealRequest }) {
  return (
    <>
      <Card className="flex flex-col gap-4 p-5">
        <SectionHeading>Thông tin yêu cầu</SectionHeading>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Mã phiếu">{request.code || '— (phiếu nháp)'}</InfoRow>
          <InfoRow label="Loại con dấu">{request.seal_type_name}</InfoRow>
          <InfoRow label="Mục đích sử dụng">{request.purpose}</InfoRow>
          <InfoRow label="Tên chứng từ">{request.title}</InfoRow>
          <InfoRow label="Công ty cần đóng dấu">{request.company_name}</InfoRow>
          <InfoRow label="Mã số thuế">{request.company_tax_code}</InfoRow>
          <InfoRow label="TBP phê duyệt">{request.approver_name}</InfoRow>
          <InfoRow label="Số bản">{String(request.copies)}</InfoRow>
          <InfoRow label="Số chứng từ đã ký">{String(request.signed_doc_count)}</InfoRow>
          <InfoRow label="Ngày tạo">{formatDateTime(request.created_at) || '—'}</InfoRow>
        </div>
      </Card>

      <Card className="flex flex-col gap-4 p-5">
        <SectionHeading>Người tạo</SectionHeading>
        <div className="grid gap-4 sm:grid-cols-2">
          <InfoRow label="Tên">{request.requester}</InfoRow>
          <InfoRow label="Email">{request.requester_email}</InfoRow>
          <InfoRow label="Số điện thoại">{request.requester_phone}</InfoRow>
          <InfoRow label="Vai trò">{request.requester_role}</InfoRow>
        </div>
      </Card>

      {request.note && (
        <Card className="flex flex-col gap-2 p-5">
          <SectionHeading>Ghi chú</SectionHeading>
          <ReadOnlyValue multiline>{request.note}</ReadOnlyValue>
        </Card>
      )}
    </>
  )
}
