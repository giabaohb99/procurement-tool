import { Lock } from 'lucide-react'

import { Card, CardContent } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import type { DocTypeLinkRuleInput, LinkRuleOptions } from '../types/document-link-rule'

interface LinkRuleParentChangeFieldsProps {
  values: DocTypeLinkRuleInput
  options?: LinkRuleOptions
  /** Quan hệ «trích từ» — ba ô bị khóa, backend ép lại dù khai gì. */
  isExcerpt: boolean
  onChange: <K extends keyof DocTypeLinkRuleInput>(
    key: K,
    value: DocTypeLinkRuleInput[K],
  ) => void
}

/**
 * Khối "khi văn bản cha thay đổi" của form quy tắc quan hệ.
 *
 * Tách khỏi `document-link-rule-form.tsx` vì đó là một câu hỏi nghiệp vụ riêng —
 * *cha đổi thì con ra sao* — và nó chiếm quá nửa chiều dài form.
 */
export function LinkRuleParentChangeFields({
  values,
  options,
  isExcerpt,
  onChange,
}: LinkRuleParentChangeFieldsProps) {
  return (
    <Card>
      <CardContent className="space-y-5">
        <div>
          <p className="text-sm font-medium">Khi văn bản cha thay đổi</p>
          <p className="text-sm text-muted-foreground">
            Hệ thống chỉ đánh dấu và liệt kê, không tự sửa nội dung văn bản con.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Cha lên phiên bản mới</Label>
            <Select
              value={String(values.on_parent_new_version)}
              disabled={isExcerpt}
              onValueChange={(next) => onChange('on_parent_new_version', Number(next))}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(options?.on_parent_new_version ?? []).map((item) => (
                  <SelectItem key={item.value} value={String(item.value)}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Cha bị bãi bỏ</Label>
            <Select
              value={String(values.on_parent_obsolete)}
              disabled={isExcerpt}
              onValueChange={(next) => onChange('on_parent_obsolete', Number(next))}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(options?.on_parent_obsolete ?? []).map((item) => (
                  <SelectItem key={item.value} value={String(item.value)}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/*  Cặp "thừa kế" đi với nhau — cùng trả lời "con lấy gì theo cha". */}
        <div className="grid gap-4 border-t pt-4 sm:grid-cols-2">
          <div className="flex items-start gap-3">
            <Checkbox
              id="rule-inherit-code"
              className="mt-0.5"
              checked={values.inherit_code}
              onCheckedChange={(checked) => onChange('inherit_code', checked === true)}
            />
            <div className="space-y-1">
              <Label htmlFor="rule-inherit-code">Thừa kế số hiệu</Label>
              <p className="text-sm text-muted-foreground">
                Con lấy mã theo cha: <span className="font-mono">DEGO-QC-012-HD01</span>.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <Checkbox
              id="rule-inherit-secrecy"
              className="mt-0.5"
              checked={values.inherit_secrecy}
              disabled={isExcerpt}
              onCheckedChange={(checked) => onChange('inherit_secrecy', checked === true)}
            />
            <div className="space-y-1">
              <Label htmlFor="rule-inherit-secrecy">Thừa kế mức mật</Label>
              <p className="text-sm text-muted-foreground">
                Con không được đặt mức mật thấp hơn cha.
              </p>
            </div>
          </div>
        </div>

        {/*  "Đang dùng" tách hẳn khỏi cặp thừa kế: nó nói về CẢ DÒNG quy tắc,
             không phải một thuộc tính của quan hệ như hai ô trên. */}
        <div className="flex items-start gap-3 border-t pt-4">
          <Checkbox
            id="rule-active"
            className="mt-0.5"
            checked={values.is_active}
            onCheckedChange={(checked) => onChange('is_active', checked === true)}
          />
          <div className="space-y-1">
            <Label htmlFor="rule-active">Đang dùng</Label>
            <p className="text-sm text-muted-foreground">
              Tắt thì không khai thêm và không chặn gửi duyệt; quan hệ đã khai vẫn còn.
            </p>
          </div>
        </div>

        {isExcerpt && (
          <p className="flex items-start gap-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <Lock className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Quan hệ «Trích từ» khóa ba ô trên. Bản trích là <b>cùng nội dung</b> với
              gốc, chỉ ít hơn — cho phép đặt "không làm gì" nghĩa là cho phép một bản
              trích nói sai tồn tại hợp lệ, và bỏ thừa kế mức mật nghĩa là phần nội dung
              ít hơn lại lỏng hơn phần đầy đủ.
            </span>
          </p>
        )}
      </CardContent>
    </Card>
  )
}
