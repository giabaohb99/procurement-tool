import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { PurchaseRequestDetail } from '../types/purchase-request-detail'

interface InfoCardProps {
  data: PurchaseRequestDetail
  editing: boolean
  onChange: (changes: Partial<PurchaseRequestDetail>) => void
}

/**
 * Thẻ "Thông tin chung" — GIỮ NGUYÊN thứ tự và tên nhãn của bản `frontend` cũ
 * (`PurchaseRequestDetail.tsx`) để người dùng không phải học lại màn hình.
 *
 * Bộ phận YC và Trưởng bộ phận luôn khóa: backend tự điền theo hồ sơ nhân sự
 * của người yêu cầu / theo phòng ban, sửa tay ở đây là sai nguồn dữ liệu.
 */
export function PurchaseRequestInfoCard({ data, editing, onChange }: InfoCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base text-navy dark:text-foreground">
          Thông tin chung
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Mã phiếu yêu cầu">{data.code || '— (phiếu nháp)'}</Field>
        <Field label="Ngày tạo">{formatDateTime(data.created_at) || '—'}</Field>

        <div className="space-y-1.5">
          <Label>
            Ngày tiếp nhận <span className="text-destructive">*</span>
          </Label>
          {editing ? (
            <Input
              type="date"
              value={data.request_date || ''}
              onChange={(e) => onChange({ request_date: e.target.value })}
            />
          ) : (
            <p className="text-sm">{formatDate(data.request_date) || '—'}</p>
          )}
        </div>

        <Field label="Công ty nhận hóa đơn *">{data.company_name}</Field>
        <Field label="Nhân sự YC *">{data.requester}</Field>
        <Field label="Bộ phận YC *">{data.department}</Field>

        <div className="space-y-1.5">
          <Label>Chức vụ (Nếu có)</Label>
          {editing ? (
            <Input
              value={data.requester_position}
              placeholder="Tự động theo Nhân sự"
              onChange={(e) => onChange({ requester_position: e.target.value })}
            />
          ) : (
            <p className="text-sm">{data.requester_position || '—'}</p>
          )}
        </div>

        <Field label="Trưởng bộ phận (TBP) / Người liên hệ">{data.head_of_dept}</Field>

        <div className="space-y-1.5">
          <Label>Tùy chọn phiếu</Label>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-destructive">
            <Checkbox
              checked={data.is_urgent}
              disabled={!editing}
              onCheckedChange={(checked) => onChange({ is_urgent: checked === true })}
            />
            Đơn gấp
          </label>
        </div>

        <div className="space-y-1.5 sm:col-span-2 lg:col-span-3">
          <Label>
            Mục đích mua hàng <span className="text-destructive">*</span>
          </Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập mục đích mua hàng/dịch vụ..."
              value={data.purpose}
              onChange={(e) => onChange({ purpose: e.target.value })}
            />
          ) : (
            <p className="text-sm whitespace-pre-wrap">{data.purpose || '—'}</p>
          )}
        </div>

        <div className="space-y-1.5 sm:col-span-2 lg:col-span-3">
          <Label>Nội dung mua hàng</Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập nội dung chi tiết..."
              value={data.note}
              onChange={(e) => onChange({ note: e.target.value })}
            />
          ) : (
            <p className="text-sm whitespace-pre-wrap">{data.note || '—'}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/** Ô chỉ đọc: dữ liệu do backend gán, màn này không cho sửa. */
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground">{label}</Label>
      <p className="text-sm">{children || '—'}</p>
    </div>
  )
}
