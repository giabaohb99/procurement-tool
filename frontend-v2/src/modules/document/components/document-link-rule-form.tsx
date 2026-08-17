import { useState } from 'react'

import { Card, CardContent } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useDocumentTypes } from '../hooks/use-document-types'
import { useLinkRuleOptions } from '../hooks/use-document-link-rules'
import type { DocTypeLinkRule, DocTypeLinkRuleInput } from '../types/document-link-rule'
import { LinkRuleParentChangeFields } from './link-rule-parent-change-fields'
import { RELATION } from '../types/document-link'

const EMPTY: DocTypeLinkRuleInput = {
  source_type_id: 0,
  relation: RELATION.guide,
  target_type_id: null,
  is_required: false,
  min_count: 0,
  max_count: 0,
  on_parent_obsolete: 2,
  on_parent_new_version: 3,
  inherit_code: false,
  inherit_secrecy: false,
  is_active: true,
}

interface DocumentLinkRuleFormProps {
  formId: string
  rule?: DocTypeLinkRule
  onSubmit: (values: DocTypeLinkRuleInput) => void
}

/**
 * Khai một dòng quy tắc quan hệ (E01).
 *
 * Quan hệ **trích từ** khóa ba cột (`on_parent_*`, thừa kế mức mật) — giao diện
 * tắt ô và nói rõ vì sao. Backend ép lại giá trị dù khai gì, nên đây chỉ là để
 * người khai khỏi tưởng mình đổi được.
 */
export function DocumentLinkRuleForm({ formId, rule, onSubmit }: DocumentLinkRuleFormProps) {
  const { items: docTypes } = useDocumentTypes()
  const { data: options } = useLinkRuleOptions()
  //  Khởi tạo THẲNG từ `rule` chứ không đồng bộ bằng `useEffect`: trang cha
  //  gắn `key` theo id nên khi bản ghi về là component dựng lại, và ta tránh
  //  được một vòng render thừa (`setState` trong effect).
  const [values, setValues] = useState<DocTypeLinkRuleInput>(() =>
    rule
      ? {
          source_type_id: rule.source_type_id,
          relation: rule.relation,
          target_type_id: rule.target_type_id,
          is_required: rule.is_required,
          min_count: rule.min_count,
          max_count: rule.max_count,
          on_parent_obsolete: rule.on_parent_obsolete,
          on_parent_new_version: rule.on_parent_new_version,
          inherit_code: rule.inherit_code,
          inherit_secrecy: rule.inherit_secrecy,
          is_active: rule.is_active,
        }
      : EMPTY,
  )

  const isExcerpt = values.relation === RELATION.excerpt

  function set<K extends keyof DocTypeLinkRuleInput>(key: K, value: DocTypeLinkRuleInput[K]) {
    setValues((truoc) => ({ ...truoc, [key]: value }))
  }

  return (
    <form
      id={formId}
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit(values)
      }}
    >
      <Card>
        <CardContent className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label>
                Loại văn bản<span className="text-destructive"> *</span>
              </Label>
              <Select
                value={values.source_type_id ? String(values.source_type_id) : ''}
                onValueChange={(next) => set('source_type_id', Number(next))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn loại…" />
                </SelectTrigger>
                <SelectContent>
                  {docTypes.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Quan hệ</Label>
              <Select
                value={String(values.relation)}
                onValueChange={(next) => set('relation', Number(next))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(options?.relations ?? []).map((item) => (
                    <SelectItem key={item.value} value={String(item.value)}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Tới loại</Label>
              <Select
                value={values.target_type_id ? String(values.target_type_id) : 'any'}
                onValueChange={(next) =>
                  set('target_type_id', next === 'any' ? null : Number(next))
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Loại bất kỳ</SelectItem>
                  {docTypes.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4 border-t pt-4">
            <div className="flex items-start gap-3">
              <Checkbox
                id="rule-required"
                className="mt-0.5"
                checked={values.is_required}
                onCheckedChange={(checked) => set('is_required', checked === true)}
              />
              <div className="space-y-1">
                <Label htmlFor="rule-required">Bắt buộc</Label>
                <p className="text-sm text-muted-foreground">
                  Thiếu quan hệ này thì không gửi duyệt được.
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:max-w-md sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="rule-min">Số lượng tối thiểu</Label>
                <Input
                  id="rule-min"
                  type="number"
                  min={0}
                  value={values.min_count}
                  onChange={(event) => set('min_count', Number(event.target.value))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rule-max">Số lượng tối đa</Label>
                <Input
                  id="rule-max"
                  type="number"
                  min={0}
                  value={values.max_count}
                  onChange={(event) => set('max_count', Number(event.target.value))}
                />
                <p className="text-xs text-muted-foreground">0 = không giới hạn.</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <LinkRuleParentChangeFields
        values={values}
        options={options}
        isExcerpt={isExcerpt}
        onChange={set}
      />
    </form>
  )
}
