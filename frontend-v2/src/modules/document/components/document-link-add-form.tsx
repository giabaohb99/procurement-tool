import { Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import type { DocumentLinkSlot } from '../types/document-link'

interface DocumentLinkAddFormProps {
  slots: DocumentLinkSlot[]
  /** Số quan hệ đã khai theo từng loại — để tắt ô đã đủ số lượng tối đa. */
  countByRelation: Record<number, number>
  disabled?: boolean
  onAdd: (relation: number, targetDocumentId: number) => void
}

/**
 * KHAI QUAN HỆ — ô hiện ra theo quy tắc của loại văn bản (E03).
 *
 * Người soạn **không phải nhớ quy tắc**: chọn loại "Hướng dẫn công việc" thì tự
 * có ô "Hướng dẫn cho", và danh sách trong ô đã lọc sẵn đúng loại đích cho phép,
 * chỉ còn văn bản đang hiệu lực. Backend dựng danh sách đó, giao diện không tự
 * lọc lại — lọc hai nơi thì sớm muộn hai nơi lệch nhau.
 */
export function DocumentLinkAddForm({
  slots,
  countByRelation,
  disabled = false,
  onAdd,
}: DocumentLinkAddFormProps) {
  //  Giá trị đang chọn của TỪNG ô, khóa theo `relation`: hai ô cùng mở một lúc
  //  mà dùng chung một state thì chọn ô này làm nhảy ô kia.
  const [picked, setPicked] = useState<Record<number, string>>({})

  if (slots.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Loại văn bản này chưa khai quy tắc quan hệ nào. Thêm ở màn Quy tắc quan hệ.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {slots.map((slot) => {
        const daCo = countByRelation[slot.relation] ?? 0
        const daDu = slot.max_count > 0 && daCo >= slot.max_count
        const value = picked[slot.relation] ?? ''

        return (
          <div key={`${slot.relation}-${slot.rule_id}`} className="space-y-2">
            <Label>
              {slot.relation_label}
              {slot.is_required && <span className="text-destructive"> *</span>}
              <span className="ml-2 font-normal text-muted-foreground">
                {slot.max_count > 0
                  ? `đã khai ${daCo}/${slot.max_count}`
                  : `đã khai ${daCo}`}
              </span>
            </Label>

            <div className="flex gap-2">
              <Select
                value={value}
                disabled={disabled || daDu || slot.options.length === 0}
                onValueChange={(next) =>
                  setPicked((truoc) => ({ ...truoc, [slot.relation]: next }))
                }
              >
                <SelectTrigger className="flex-1">
                  <SelectValue
                    placeholder={
                      slot.options.length === 0
                        ? 'Chưa có văn bản nào đang hiệu lực để chọn'
                        : 'Chọn văn bản…'
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {slot.options.map((option) => (
                    <SelectItem key={option.id} value={String(option.id)}>
                      {option.display_code ? `${option.display_code} · ` : ''}
                      {option.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                type="button"
                variant="outline"
                disabled={disabled || daDu || !value}
                onClick={() => {
                  onAdd(slot.relation, Number(value))
                  setPicked((truoc) => ({ ...truoc, [slot.relation]: '' }))
                }}
              >
                <Plus className="size-4" />
                Khai
              </Button>
            </div>

            {daDu && (
              <p className="text-xs text-muted-foreground">
                Đã đủ số lượng tối đa. Gỡ bớt bên dưới rồi mới khai thêm được.
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
