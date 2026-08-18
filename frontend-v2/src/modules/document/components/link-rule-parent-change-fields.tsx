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
 * Khối THIẾT LẬP NÂNG CAO của form quy tắc quan hệ.
 *
 * Tách khỏi `document-link-rule-form.tsx` vì đó là một câu hỏi nghiệp vụ riêng —
 * *văn bản được trỏ tới thay đổi thì bên này ra sao* — và nó chiếm quá nửa chiều
 * dài form. Form gập khối này lại mặc định: có sẵn mặc định an toàn, hầu như
 * không ai sửa.
 *
 * Nhãn cố tình tránh chữ "cha / con": trong bảng dữ liệu thì đúng là quan hệ
 * cha–con, nhưng người khai chỉ nhìn thấy hai loại văn bản và không có gì trên
 * màn hình nói cho họ biết bên nào là "cha".
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
          <p className="text-sm font-medium">Khi văn bản được trỏ tới thay đổi</p>
          <p className="text-sm text-muted-foreground">
            Hệ thống chỉ đánh dấu và liệt kê để người ban hành quyết, không tự sửa nội dung văn
            bản nào.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Khi văn bản đó lên phiên bản mới</Label>
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
            <Label>Khi văn bản đó bị bãi bỏ</Label>
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

        {/*  Cặp "thừa kế" đi với nhau — cùng trả lời "văn bản này lấy gì theo
             văn bản nó trỏ tới". */}
        <div className="grid gap-4 border-t pt-4 sm:grid-cols-2">
          <div className="flex items-start gap-3">
            <Checkbox
              id="rule-inherit-code"
              className="mt-0.5"
              checked={values.inherit_code}
              onCheckedChange={(checked) => onChange('inherit_code', checked === true)}
            />
            <div className="space-y-1">
              <Label htmlFor="rule-inherit-code">Đánh số nối theo văn bản đó</Label>
              <p className="text-sm text-muted-foreground">
                Số hiệu nối thêm phần đuôi: <span className="font-mono">DEGO-QC-012-HD01</span>.
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
              <Label htmlFor="rule-inherit-secrecy">Không được hạ mức mật</Label>
              <p className="text-sm text-muted-foreground">
                Mức mật luôn phải bằng hoặc cao hơn văn bản được trỏ tới.
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
            <Label htmlFor="rule-active">Quy tắc đang áp dụng</Label>
            <p className="text-sm text-muted-foreground">
              Tắt thì từ nay không khai thêm và không chặn gửi duyệt nữa; các quan hệ đã khai
              trên văn bản cũ vẫn giữ nguyên.
            </p>
          </div>
        </div>

        {isExcerpt && (
          <p className="flex items-start gap-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <Lock className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Quan hệ «Trích từ» khóa ba ô trên, khai gì hệ thống cũng đặt lại. Bản trích
              là <b>cùng nội dung</b> với bản gốc, chỉ ít hơn — cho phép đặt "không làm gì"
              nghĩa là chấp nhận một bản trích nói sai vẫn tồn tại hợp lệ, còn bỏ ràng buộc
              mức mật nghĩa là phần nội dung ít hơn lại được bảo vệ lỏng hơn phần đầy đủ.
            </span>
          </p>
        )}
      </CardContent>
    </Card>
  )
}
