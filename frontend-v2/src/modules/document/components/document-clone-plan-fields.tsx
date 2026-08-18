import { Building2, Copy, Info } from 'lucide-react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { DatePicker } from '@/shared/ui/date-picker'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import type { DocumentClonePlanInput } from '../types/document-clone'

interface DocumentClonePlanFieldsProps {
  value: DocumentClonePlanInput
  onChange: (value: DocumentClonePlanInput) => void
  /**
   * Id pháp nhân suy từ khối «Phạm vi áp dụng» — đã bỏ pháp nhân ban hành.
   * Rỗng thì trang gọi KHÔNG dựng khối này, nên ở đây luôn có ít nhất một nơi.
   */
  companyIds: number[]
}

/**
 * KẾ HOẠCH CLONE khai ngay ở form TẠO văn bản (F06, nhịp đầu).
 *
 * ⚠️ Khối này **không sinh bản nháp nào**. Bản clone chép nội dung của phiên bản
 * đang dùng, mà văn bản vừa lập thì chưa có phiên bản nào đang dùng để chép —
 * backend từ chối thẳng: *"Chỉ clone được văn bản đã ban hành"*.
 *
 * **Nơi nhận bản riêng KHÔNG khai lại ở đây** — nó chính là các pháp nhân đã
 * chọn ở khối «Phạm vi áp dụng» ngay trên. Hỏi hai lần cùng một câu thì hai
 * danh sách chắc chắn sẽ lệch nhau, mà không có gì trên màn hình nói cái nào
 * đúng: văn bản áp cho mười pháp nhân nhưng chỉ tách bản riêng cho tám, hai nơi
 * còn lại im lặng dùng chung bản gốc.
 *
 * Cố ý KHÔNG tự chạy lúc duyệt: clone đẻ ra văn bản thật, mỗi bản một số hiệu
 * vĩnh viễn. Đó không nên là tác dụng phụ âm thầm của việc bấm nút Duyệt.
 */
export function DocumentClonePlanFields({
  value,
  onChange,
  companyIds,
}: DocumentClonePlanFieldsProps) {
  //  Cùng bộ tham số với ô "Pháp nhân ban hành" ở bước 1 nên dùng chung một
  //  lượt gọi trong bộ nhớ đệm — lệch tham số là gọi lại y hệt lần thứ hai.
  const { data: companyPage } = useCompanies({ page_size: 200, is_active: true })
  const companies = (companyPage?.items ?? []).filter((row) => companyIds.includes(row.id))

  return (
    <div className="space-y-4">
      <p className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
        <Info className="mt-0.5 size-4 shrink-0" />
        <span>
          Khai trước thôi — <b>chưa bản nháp nào được sinh ra</b>. Clone chép nội dung
          của phiên bản đang dùng, nên chỉ chạy được sau khi văn bản đã ban hành. Lúc
          đó thẻ «Bản clone ở pháp nhân con» tick sẵn đúng những nơi dưới đây.
        </span>
      </p>

      <div className="space-y-2">
        <Label>Pháp nhân sẽ nhận bản riêng</Label>
        <ul className="max-h-56 space-y-1.5 overflow-y-auto rounded-md border p-3">
          {companies.map((company) => (
            <li key={company.id} className="flex items-center gap-2 text-sm">
              <Building2 className="size-4 shrink-0 text-muted-foreground" />
              {company.name}
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          Suy từ phạm vi áp dụng, không khai lại ở đây. Bỏ bớt nơi nào thì sửa dòng
          phạm vi tương ứng.
        </p>
      </div>

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
          <b>{companyIds.length}</b> pháp nhân đang trong kế hoạch. Mỗi nơi sẽ mang{' '}
          <b>số hiệu của chính pháp nhân đó</b>, không dùng lại số của bản gốc.
        </span>
      </p>
    </div>
  )
}
