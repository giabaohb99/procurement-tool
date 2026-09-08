import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Textarea } from '@/shared/ui/textarea'
import {
  LIST_DESCRIPTION_MAX,
  LIST_NAME_MAX,
  type ListInfoForm,
} from '../hooks/use-list-info-form'
import type { WorkList } from '../types/work'
import { cn } from '@/shared/utils/cn'
import { WorkColorPicker } from './work-color-picker'

interface ListInfoPanelProps {
  list: WorkList
  form: ListInfoForm
  /**
   * Chỉ CHỦ SỞ HỮU mới sửa được thông tin dự án.
   *
   * ⚠️ Không phải Quản trị. Backend gác `update_list` bằng `CAN_OWN`
   * (`list_service.py`), nên mở ô nhập cho Quản trị là họ gõ xong bấm Lưu rồi ăn
   * 403 — tệ hơn hẳn việc thấy ngay là mình không sửa được.
   */
  canEdit: boolean
}

/**
 * Khối THÔNG TIN của hộp Quản lý dự án: tên · mô tả · màu.
 *
 * Trạng thái nằm ở `useListInfoForm` chứ không ở đây, vì nút *Lưu thông tin* đặt
 * dưới đáy hộp (sau danh sách thành viên) chứ không nằm trong khối này.
 *
 * Trước đợt này không màn nào gọi được `PATCH /api/work/lists/{id}` — API, hàm
 * gọi và cả hook `useUpdateWorkList` đều đã có sẵn từ lâu nhưng không có nút nào,
 * nên đặt tên sai lúc tạo là phải xoá dự án làm lại, mất sạch việc bên trong.
 *
 * ⚠️ Người không sửa được KHÔNG dùng `<Input disabled>`: `disabled` gỡ luôn khả
 * năng nhận con trỏ nên không bôi đen, không copy được, lại bị làm mờ nhìn như
 * chữ gợi ý. Dùng `ReadOnlyValue` — xem luật ở CLAUDE.md.
 */
export function ListInfoPanel({ list, form, canEdit }: ListInfoPanelProps) {
  if (!canEdit) {
    return (
      <section className="space-y-3">
        <SectionTitle />
        <div className="space-y-2">
          <Label>Tên dự án</Label>
          <ReadOnlyValue>{list.name}</ReadOnlyValue>
        </div>
        <div className="space-y-2">
          <Label>Mô tả</Label>
          <ReadOnlyValue multiline>{list.description || '—'}</ReadOnlyValue>
        </div>
      </section>
    )
  }

  return (
    <section className="space-y-3">
      <SectionTitle />

      {/*  Tên và màu cùng một hàng: màu là một dải chấm nhỏ, cho nó chiếm trọn
           một hàng riêng thì hộp dài thêm mà chẳng rõ hơn. */}
      <div className="flex items-end gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <Label htmlFor="work-info-name">Tên dự án</Label>
          <Input
            id="work-info-name"
            value={form.name}
            maxLength={LIST_NAME_MAX}
            onChange={(e) => form.setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.nativeEvent.isComposing) return
              if (e.key === 'Enter') {
                e.preventDefault()
                form.save()
              }
            }}
          />
        </div>
        <div className="shrink-0 space-y-2">
          <Label>Màu</Label>
          <WorkColorPicker
            value={form.color}
            onChange={form.setColor}
            className="max-w-[9rem] py-2"
          />
        </div>
      </div>

      {!form.trimmedName && (
        <p className="text-xs text-destructive">
          Tên không được để trống — dự án không tên là một dòng trắng trong cây bên trái.
        </p>
      )}

      <div className="space-y-2">
        <Label htmlFor="work-info-description">Mô tả</Label>
        {/*  Textarea chứ không Input: mô tả dự án hay là hai ba câu, ô một dòng
             thì không thấy được phần đã gõ trước đó. Enter ở đây là XUỐNG DÒNG. */}
        <Textarea
          id="work-info-description"
          rows={3}
          value={form.description}
          maxLength={LIST_DESCRIPTION_MAX}
          onChange={(e) => form.setDescription(e.target.value)}
          placeholder="Dự án này làm gì, phạm vi tới đâu…"
        />
        {/*  Bộ đếm hiện SUỐT, không chờ gần chạm trần: `maxLength` của trình
             duyệt chặn im lặng — gõ tới ký tự 1501 thì bàn phím như chết, không
             một dòng chữ nào nói vì sao. Thấy số từ đầu thì người ta biết có
             giới hạn trước khi đụng phải nó. */}
        <p
          className={cn(
            'text-right text-xs tabular-nums',
            form.description.length >= LIST_DESCRIPTION_MAX
              ? 'font-medium text-destructive'
              : 'text-muted-foreground',
          )}
        >
          {form.description.length}/{LIST_DESCRIPTION_MAX}
        </p>
      </div>
    </section>
  )
}

function SectionTitle() {
  return <h3 className="text-sm font-semibold text-navy dark:text-foreground">Thông tin</h3>
}
