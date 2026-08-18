import { ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'

import { Card, CardContent } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { COUNT_PRESETS, countPresetOf } from '../helpers/link-rule-count-preset'
import { EMPTY_LINK_RULE } from '../helpers/link-rule-input'
import { linkRuleSentence } from '../helpers/link-rule-sentence'
import { useDocumentTypes } from '../hooks/use-document-types'
import { useLinkRuleOptions } from '../hooks/use-document-link-rules'
import type { DocTypeLinkRuleInput } from '../types/document-link-rule'
import { LinkRuleParentChangeFields } from './link-rule-parent-change-fields'
import { RELATION, RELATION_HINTS } from '../types/document-link'

interface DocumentLinkRuleFormProps {
  formId: string
  /**
   * Giá trị mở đầu. Nhận BỘ GIÁ TRỊ chứ không phải bản ghi, để form dùng được
   * cho cả dòng đã lưu lẫn dòng còn đang xếp hàng chờ (khai quan hệ ngay lúc
   * tạo loại văn bản mới, khi chưa có id nào để ghi vào).
   */
  initial?: DocTypeLinkRuleInput
  /**
   * Mở từ trang MỘT loại văn bản: loại nguồn đã biết rồi, giấu ô chọn đi.
   *
   * Để ô đó hiện ra thì người khai đổi được nó, và dòng vừa sửa nhảy sang loại
   * khác trong khi họ vẫn đang đứng ở trang loại cũ — sửa xong nhìn lại không
   * thấy dòng mình vừa sửa đâu nữa.
   */
  lockedSourceTypeId?: number
  /** Tên loại nguồn — chỉ để dựng câu xem trước cho dễ đọc. */
  sourceTypeName?: string
  /**
   * Cho chọn NHIỀU loại đích một lần — chỉ bật lúc thêm mới.
   *
   * Quan hệ giữa các loại là **một–nhiều**: một Quy trình vừa căn cứ theo Chính
   * sách, vừa căn cứ theo Quy chế, vừa căn cứ theo Quyết định. Bắt khai từng
   * dòng một thì cùng một câu ("căn cứ theo") phải mở form ba lần, và ba lần đó
   * dễ khai lệch nhau ở các ô bên dưới.
   *
   * Mỗi loại đích vẫn thành MỘT DÒNG riêng trong bảng — đó là hạt dữ liệu của
   * `tab_doc_type_link_rule`, và phải vậy thì mới đặt được số lượng / cách xử lý
   * khi cha đổi khác nhau cho từng đích về sau.
   */
  allowMultipleTargets?: boolean
  /** Nhận MẢNG dòng: chọn ba loại đích thì trả về ba dòng. Sửa thì luôn một dòng. */
  onSubmit: (rows: DocTypeLinkRuleInput[]) => void
}

/**
 * Khai một quy tắc quan hệ giữa hai LOẠI văn bản (E01).
 *
 * Form đi theo đúng thứ tự câu hỏi trong đầu người khai — *quan hệ gì · tới loại
 * nào · bắt buộc không · mấy văn bản* — và dựng lại thành **một câu xem trước**
 * ngay dưới. Trước đây form bày thẳng tên cột của bảng ("Số lượng tối thiểu",
 * "Số lượng tối đa", trong đó 0 nghĩa là không giới hạn), người khai phải tự
 * dịch bốn ô rời thành điều luật mình đang đặt ra.
 *
 * Bốn ô ít dùng (cha đổi thì con ra sao, thừa kế mã / mức mật) **gập lại** —
 * chín trên mười lần khai không ai đụng tới, mà để mở thì form dài gấp đôi và
 * phần quan trọng bị đẩy khỏi tầm nhìn.
 *
 * Quan hệ **trích từ** khóa ba ô nâng cao; backend ép lại giá trị dù khai gì.
 */
export function DocumentLinkRuleForm({
  formId,
  initial,
  lockedSourceTypeId,
  sourceTypeName,
  allowMultipleTargets,
  onSubmit,
}: DocumentLinkRuleFormProps) {
  const { items: docTypes } = useDocumentTypes()
  const { data: options } = useLinkRuleOptions()

  //  Khởi tạo THẲNG từ `initial` chứ không đồng bộ bằng `useEffect`: trang cha
  //  gắn `key` theo dòng nên khi dữ liệu về là component dựng lại, và ta tránh
  //  được một vòng render thừa (`setState` trong effect).
  const [values, setValues] = useState<DocTypeLinkRuleInput>(
    () => initial ?? { ...EMPTY_LINK_RULE, source_type_id: lockedSourceTypeId ?? 0 },
  )
  //  Chỉ dùng ở chế độ nhiều đích. Rỗng = «Loại bất kỳ» (dòng duy nhất,
  //  `target_type_id` để trống) — giữ được lối khai "bất kỳ tham chiếu bất kỳ".
  const [targetTypeIds, setTargetTypeIds] = useState<number[]>(() =>
    initial?.target_type_id ? [initial.target_type_id] : [],
  )
  const [preset, setPreset] = useState(() =>
    countPresetOf(values.min_count, values.max_count),
  )
  const [showAdvanced, setShowAdvanced] = useState(false)

  const isExcerpt = values.relation === RELATION.excerpt

  function set<K extends keyof DocTypeLinkRuleInput>(key: K, value: DocTypeLinkRuleInput[K]) {
    setValues((truoc) => ({ ...truoc, [key]: value }))
  }

  function doiMucSoLuong(next: string) {
    setPreset(next as typeof preset)
    const muc = COUNT_PRESETS.find((item) => item.value === next)
    //  "Tùy chỉnh" giữ nguyên số đang có rồi mở hai ô ra cho sửa — xóa về 0 thì
    //  người vừa bấm nhầm mất luôn con số mình khai từ đầu.
    if (muc) setValues((truoc) => ({ ...truoc, min_count: muc.min, max_count: muc.max }))
  }

  const relationLabel =
    options?.relations.find((item) => item.value === values.relation)?.label ?? ''
  //  `undefined` = chưa chọn loại nào, tức "loại bất kỳ" — câu xem trước đọc
  //  khác hẳn so với khi có tên loại thật.
  const targetTypeName = allowMultipleTargets
    ? docTypes.find((type) => type.id === targetTypeIds[0])?.name
    : docTypes.find((type) => type.id === values.target_type_id)?.name

  return (
    <form
      id={formId}
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        if (!allowMultipleTargets) {
          onSubmit([values])
          return
        }
        //  Không chọn loại nào = «Loại bất kỳ», vẫn là MỘT dòng.
        onSubmit(
          targetTypeIds.length === 0
            ? [{ ...values, target_type_id: null }]
            : targetTypeIds.map((id) => ({ ...values, target_type_id: id })),
        )
      }}
    >
      <Card>
        <CardContent className="space-y-4">
          <div
            className={cn('grid gap-4', lockedSourceTypeId ? 'sm:grid-cols-1' : 'sm:grid-cols-2')}
          >
            {!lockedSourceTypeId && (
              <div className="space-y-2">
                <Label>
                  Loại văn bản áp dụng<span className="text-destructive"> *</span>
                </Label>
                <Select
                  value={values.source_type_id ? String(values.source_type_id) : ''}
                  onValueChange={(next) => set('source_type_id', Number(next))}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Chọn loại văn bản…" />
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
            )}

            <div className="space-y-2">
              <Label>Loại quan hệ</Label>
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
              {/*  `min-h-8` giữ chỗ sẵn hai dòng: mười câu chú thích dài ngắn
                   khác nhau, đổi câu mà không giữ chỗ thì cả form xô lên xuống. */}
              <p className="min-h-8 text-xs text-muted-foreground">
                {RELATION_HINTS[values.relation]}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Trỏ tới loại văn bản</Label>
            {allowMultipleTargets ? (
              <>
                <MultiPicker
                  value={targetTypeIds}
                  onChange={setTargetTypeIds}
                  options={docTypes.map((type) => ({
                    id: type.id,
                    label: type.name,
                    hint: type.code,
                  }))}
                  placeholder="Chọn một hoặc nhiều loại văn bản…"
                  searchPlaceholder="Tìm loại văn bản…"
                />
                <p className="text-xs text-muted-foreground">
                  Chọn nhiều loại thì mỗi loại được lưu thành một quy tắc riêng, chỉnh số lượng
                  cho từng quy tắc sau. Để trống nếu chấp nhận <b>loại bất kỳ</b>.
                </p>
              </>
            ) : (
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
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Mức độ ràng buộc</Label>
              {/*  Ô tick "Bắt buộc" cũ chỉ nói được một nửa: bỏ tick nghĩa là gì
                   thì người khai phải tự suy. Hai lựa chọn bày ra cả hai vế. */}
              <RadioGroup
                value={values.is_required ? 'required' : 'optional'}
                onValueChange={(next) => set('is_required', next === 'required')}
                className="gap-2"
              >
                <div className="flex items-start gap-2">
                  <RadioGroupItem value="required" id="rule-required" className="mt-0.5" />
                  <div>
                    <Label htmlFor="rule-required" className="font-normal">
                      Bắt buộc
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Thiếu quan hệ này thì không gửi duyệt được.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <RadioGroupItem value="optional" id="rule-optional" className="mt-0.5" />
                  <div>
                    <Label htmlFor="rule-optional" className="font-normal">
                      Tùy chọn
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Khai được nhưng không ai bị chặn nếu bỏ trống.
                    </p>
                  </div>
                </div>
              </RadioGroup>
            </div>

            <div className="space-y-2">
              <Label>Số văn bản được khai</Label>
              <Select value={preset} onValueChange={doiMucSoLuong}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COUNT_PRESETS.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                  <SelectItem value="custom">Tùy chỉnh…</SelectItem>
                </SelectContent>
              </Select>

              {preset === 'custom' && (
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="space-y-1.5">
                    <Label htmlFor="rule-min" className="text-xs font-normal">
                      Tối thiểu
                    </Label>
                    <Input
                      id="rule-min"
                      type="number"
                      min={0}
                      value={values.min_count}
                      onChange={(event) => set('min_count', Number(event.target.value))}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="rule-max" className="text-xs font-normal">
                      Tối đa <span className="text-muted-foreground">(0 = không giới hạn)</span>
                    </Label>
                    <Input
                      id="rule-max"
                      type="number"
                      min={0}
                      value={values.max_count}
                      onChange={(event) => set('max_count', Number(event.target.value))}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/*  Câu xem trước là thứ dịch bốn ô rời phía trên thành điều luật mà
               người khai đang đặt ra. Đọc câu này sai là biết ngay mình chọn
               nhầm, không phải chờ tới lúc có người bị chặn gửi duyệt. */}
          <p className="rounded-md border bg-muted/50 px-3 py-2 text-sm">
            {linkRuleSentence({ rule: values, relationLabel, targetTypeName, sourceTypeName })}
            {allowMultipleTargets && targetTypeIds.length > 1 && (
              <span className="text-muted-foreground">
                {' '}
                (và {targetTypeIds.length - 1} loại nữa, mỗi loại một quy tắc)
              </span>
            )}
          </p>
        </CardContent>
      </Card>

      {/*  Gập lại mặc định: bốn ô này trả lời câu "cha đổi thì con ra sao", có
           sẵn mặc định an toàn, và hầu như không ai sửa. */}
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          {showAdvanced ? (
            <ChevronDown className="size-4" />
          ) : (
            <ChevronRight className="size-4" />
          )}
          Thiết lập nâng cao
          <span className="font-normal">
            — xử lý khi văn bản được trỏ tới thay đổi, thừa kế số hiệu và mức mật
          </span>
        </button>

        {showAdvanced && (
          <LinkRuleParentChangeFields
            values={values}
            options={options}
            isExcerpt={isExcerpt}
            onChange={set}
          />
        )}
      </div>
    </form>
  )
}
