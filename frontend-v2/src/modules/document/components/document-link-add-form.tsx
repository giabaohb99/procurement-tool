import { Plus } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { HelpHint } from '@/shared/ui/help-hint'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { RELATION_HINTS, type DocumentLinkSlot } from '../types/document-link'

interface DocumentLinkAddFormProps {
  slots: DocumentLinkSlot[]
  /**
   * Số quan hệ đã khai cho TỪNG Ô, khóa theo `rule_id`.
   *
   * Không khóa theo `relation`: một loại văn bản có thể có hai dòng quy tắc cùng
   * quan hệ khác loại đích — Biểu mẫu *thuộc về* Quy trình (bắt buộc) và Biểu
   * mẫu *thuộc về* Quy chế (tùy chọn). Đếm gộp thì khai một cái là ô kia cũng
   * hiện "đã khai 1" rồi tự khóa.
   */
  countByRule: Record<number, number>
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
  countByRule,
  disabled = false,
  onAdd,
}: DocumentLinkAddFormProps) {
  //  Giá trị đang chọn của TỪNG ô, khóa theo `rule_id` — khóa theo `relation`
  //  thì hai ô "Thuộc về" dùng chung một ô nhớ, chọn ô này nhảy luôn ô kia.
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
        const daCo = countByRule[slot.rule_id] ?? 0
        const daDu = slot.max_count > 0 && daCo >= slot.max_count
        const value = picked[slot.rule_id] ?? ''

        return (
          <div key={slot.rule_id} className="space-y-2">
            {/*  Ba mẩu thông tin khác loại nhau nên tách hẳn ra, không dính
                 thành một dòng chữ: quan hệ + loại đích là NHÃN, "bắt buộc" là
                 RÀNG BUỘC, "đã khai n/m" là TÌNH TRẠNG. Gộp lại thì đọc ra
                 "Kèm theo → Quyết định * đã khai 1/1" — không ai biết dấu sao
                 và con số kia nói về cái gì. */}
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <Label className="font-medium">
                {/*  Kèm loại đích: hai dòng quy tắc cùng quan hệ mà chỉ ghi "Thuộc
                     về" thì trên màn hình ra hai ô y hệt nhau, không biết ô nào
                     đang bắt buộc. */}
                {slot.relation_label} → {slot.target_type_name}
                {slot.is_required && (
                  <RequiredMark hint="Quan hệ bắt buộc — thiếu thì không gửi duyệt được." />
                )}
              </Label>

              <HelpHint label={`Quan hệ «${slot.relation_label}» nghĩa là gì`}>
                {RELATION_HINTS[slot.relation]}
              </HelpHint>

              {slot.is_required && (
                <Badge variant="outline" className="border-destructive/40 font-normal text-destructive">
                  bắt buộc
                </Badge>
              )}

              <span className="text-xs text-muted-foreground">
                {slot.max_count > 0
                  ? `đã khai ${daCo} trên tối đa ${slot.max_count}`
                  : `đã khai ${daCo} · không giới hạn`}
              </span>
            </div>

            <div className="flex gap-2">
              <Select
                value={value}
                disabled={disabled || daDu || slot.options.length === 0}
                onValueChange={(next) =>
                  setPicked((truoc) => ({ ...truoc, [slot.rule_id]: next }))
                }
              >
                <SelectTrigger className="flex-1">
                  {/*  Lý do bị khóa phải nằm NGAY TRONG ô, không phải ở dòng chữ
                       mờ bên dưới: người dùng bấm vào ô, thấy nó trơ ra, và đọc
                       "Chọn văn bản…" — nghĩa là ô mời chọn mà không cho chọn.
                       Người dùng báo đúng lỗi này ("sao chỗ này chặn không cho
                       tôi chọn"), dù câu giải thích đã có sẵn ở ngay bên dưới. */}
                  <SelectValue
                    placeholder={
                      daDu
                        ? `Đã khai đủ ${slot.max_count} — gỡ bớt bên dưới rồi mới khai thêm được`
                        : slot.options.length === 0
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
                  setPicked((truoc) => ({ ...truoc, [slot.rule_id]: '' }))
                }}
              >
                <Plus className="size-4" />
                Khai
              </Button>
            </div>

            {/*  Câu này KHÔNG lặp lại placeholder ở trên — nó trả lời câu hỏi
                 tiếp theo: gỡ ở chỗ nào. */}
            {daDu && (
              <p className="text-xs text-muted-foreground">
                Ô này đã đủ số lượng tối đa. Gỡ một dòng ở thẻ «Văn bản này trỏ tới» bên
                dưới rồi mới khai thêm được.
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
