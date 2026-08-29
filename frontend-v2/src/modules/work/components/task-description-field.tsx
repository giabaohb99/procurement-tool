import { useEffect, useRef, useState } from 'react'

import { RichTextField } from '@/shared/ui/rich-text-editor'
import { cn } from '@/shared/utils/cn'
import { sanitizeHtml } from '@/shared/utils/sanitize-html'
import { isRichEmpty, toRichHtml } from '../utils/description-html'
import { EmptyValueButton } from './task-detail-row'

interface TaskDescriptionFieldProps {
  /** HTML (dữ liệu cũ có thể là chữ trơn — xem `description-html.ts`). */
  description: string
  canEdit: boolean
  onSave: (description: string) => void
}

/**
 * Mô tả công việc: bình thường là CHỮ ĐÃ ĐỊNH DẠNG, bấm vào mới mở trình soạn
 * thảo rich text nhỏ (đậm · nghiêng · gạch · danh sách · trích dẫn · liên kết),
 * thanh công cụ nằm DƯỚI đáy khung như Lark.
 *
 * Hai điểm khác một ô chữ thường, và cả hai đều là lý do tệp này không dùng
 * `onBlur`:
 *
 * 1. Bấm một nút trên thanh công cụ là vùng gõ MẤT tiêu điểm — bắt `blur` thì
 *    vừa bấm «In đậm» đã đóng ô, chưa kịp gõ gì.
 * 2. Menu «Liên kết» mở bằng portal nên nằm NGOÀI khung; bấm vào ô nhập địa chỉ
 *    trong đó cũng không được tính là rời ô.
 *
 * Nên chốt lưu bằng một cú bấm RA NGOÀI khung, giữ đúng nếp «không có nút Lưu»
 * của cả panel.
 */
export function TaskDescriptionField({
  description,
  canEdit,
  onSave,
}: TaskDescriptionFieldProps) {
  const [dangSua, setDangSua] = useState(false)
  //  Bản nháp để trong ref, KHÔNG phải state: mỗi phím gõ mà vẽ lại cả panel thì
  //  trình soạn thảo bị dựng lại và con trỏ nhảy về đầu.
  const nhapRef = useRef(description)
  const khungRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!dangSua) return

    function raNgoai(su: PointerEvent) {
      const dich = su.target as HTMLElement | null
      if (!dich) return
      if (khungRef.current?.contains(dich)) return
      if (dich.closest('[data-slot=popover-content]')) return

      setDangSua(false)
      const moi = isRichEmpty(nhapRef.current) ? '' : nhapRef.current
      if (moi !== description) onSave(moi)
    }

    document.addEventListener('pointerdown', raNgoai)
    return () => document.removeEventListener('pointerdown', raNgoai)
  }, [dangSua, description, onSave])

  function moSua() {
    nhapRef.current = description
    setDangSua(true)
  }

  if (dangSua) {
    return (
      <div ref={khungRef} className="w-full">
        <RichTextField
          autoFocus
          toolbarPosition="bottom"
          placeholder="Thêm mô tả"
          defaultValue={toRichHtml(description)}
          onChange={(html) => {
            nhapRef.current = html
          }}
          //  Ô mô tả của một việc thì thấp hơn ô soạn văn bản nhiều: `doc-rich-
          //  field` mặc định cao tối thiểu 9rem, ở đây hạ xuống còn ~4 dòng.
          className="[&_.doc-rich-field]:max-h-64 [&_.doc-rich-field]:min-h-24"
        />
      </div>
    )
  }

  if (isRichEmpty(description)) {
    return (
      <EmptyValueButton disabled={!canEdit} onClick={moSua}>
        {canEdit ? 'Thêm mô tả' : 'Chưa có mô tả'}
      </EmptyValueButton>
    )
  }

  return (
    <div
      role={canEdit ? 'button' : undefined}
      tabIndex={canEdit ? 0 : undefined}
      aria-label="Mô tả công việc"
      onClick={() => canEdit && moSua()}
      onKeyDown={(su) => {
        if (canEdit && su.key === 'Enter') moSua()
      }}
      className={cn(
        //  `doc-excerpt-preview` khai ở `index.css` — CÙNG bộ luật hiển thị với
        //  trình soạn thảo, nên xem và sửa ra đúng một hình.
        'doc-excerpt-preview w-full rounded-md px-1.5 py-1 text-sm',
        canEdit && 'cursor-text hover:bg-accent/60',
      )}
      //  Nội dung do người dùng nhập → luôn lọc trước khi vẽ.
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(toRichHtml(description)) }}
    />
  )
}
