import { Copy, Info } from 'lucide-react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import type { DocumentClonePlanInput } from '../types/document-clone'

interface DocumentClonePlanFieldsProps {
  value: DocumentClonePlanInput
  onChange: (value: DocumentClonePlanInput) => void
  /** Pháp nhân ban hành đang chọn ở bước 1 — không clone văn bản về chính nó. */
  issuerCompanyId: number
}

/**
 * KẾ HOẠCH CLONE khai ngay ở form TẠO văn bản (F06, nhịp đầu).
 *
 * ⚠️ Khối này **không sinh bản nháp nào**. Bản clone chép nội dung của phiên bản
 * đang dùng, mà văn bản vừa lập thì chưa có phiên bản nào đang dùng để chép —
 * backend từ chối thẳng: *"Chỉ clone được văn bản đã ban hành"*.
 *
 * Nhưng người soạn biết ngay từ bây giờ là văn bản sẽ tách bản riêng cho những
 * pháp nhân nào. Ghi lại dự định ở đây thì sau khi ban hành, việc còn lại đúng
 * một nút bấm với danh sách đã tick sẵn — thay vì phải nhớ, mấy tuần sau, rằng
 * mình còn nợ mười hai pháp nhân con một bản văn bản.
 *
 * Cố ý KHÔNG tự chạy lúc duyệt: clone đẻ ra văn bản thật, mỗi bản một số hiệu
 * vĩnh viễn. Đó không nên là tác dụng phụ âm thầm của việc bấm nút Duyệt.
 */
export function DocumentClonePlanFields({
  value,
  onChange,
  issuerCompanyId,
}: DocumentClonePlanFieldsProps) {
  const { data: companyPage } = useCompanies({ page_size: 200 })

  const companies = (companyPage?.items ?? []).filter((row) => row.id !== issuerCompanyId)
  const picked = value.company_ids

  function toggle(companyId: number) {
    onChange({
      ...value,
      company_ids: picked.includes(companyId)
        ? picked.filter((id) => id !== companyId)
        : [...picked, companyId],
    })
  }

  return (
    <div className="space-y-4">
      <p className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
        <Info className="mt-0.5 size-4 shrink-0" />
        <span>
          Khai trước thôi — <b>chưa bản nháp nào được sinh ra</b>. Clone chép nội dung
          của phiên bản đang dùng, nên chỉ chạy được sau khi văn bản đã ban hành. Lúc
          đó thẻ «Bản clone ở pháp nhân con» tick sẵn đúng những nơi chọn ở đây.
        </span>
      </p>

      <div className="space-y-2">
        <Label>Pháp nhân sẽ nhận bản riêng</Label>
        {companies.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {issuerCompanyId
              ? 'Chưa có pháp nhân nào khác ngoài pháp nhân ban hành.'
              : 'Chọn pháp nhân ban hành ở bước «Thông tin chính» trước.'}
          </p>
        ) : (
          <ul className="max-h-56 space-y-2 overflow-y-auto rounded-md border p-3">
            {companies.map((company) => (
              <li key={company.id} className="flex items-center gap-3">
                <Checkbox
                  id={`clone-plan-${company.id}`}
                  checked={picked.includes(company.id)}
                  onCheckedChange={() => toggle(company.id)}
                />
                <Label htmlFor={`clone-plan-${company.id}`} className="font-normal">
                  {company.name}
                </Label>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/*  Hạn và ghi chú chỉ có nghĩa khi đã chọn nơi nhận — bày ra lúc chưa
           tick ai là hỏi một câu chưa tới lượt. */}
      {picked.length > 0 && (
        <>
          <div className="space-y-2">
            <Label>Hạn xử lý</Label>
            <DatePicker
              value={value.due_date}
              onChange={(next) => onChange({ ...value, due_date: next })}
            />
            <p className="text-xs text-muted-foreground">
              Hiện trong thư báo gửi pháp nhân con và trên bảng theo dõi.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="clone-plan-note">Ghi chú cho pháp nhân nhận</Label>
            <Textarea
              id="clone-plan-note"
              rows={2}
              placeholder="VD: Giữ nguyên Điều 1–4, chỉ sửa hạn mức ở Điều 5 cho đúng quy mô công ty."
              value={value.note}
              onChange={(event) => onChange({ ...value, note: event.target.value })}
            />
          </div>

          <p className="flex items-start gap-2 text-sm text-muted-foreground">
            <Copy className="mt-0.5 size-4 shrink-0" />
            <span>
              <b>{picked.length}</b> pháp nhân đang trong kế hoạch. Mỗi nơi sẽ mang{' '}
              <b>số hiệu của chính pháp nhân đó</b>, không dùng lại số của bản gốc.
            </span>
          </p>
        </>
      )}
    </div>
  )
}
