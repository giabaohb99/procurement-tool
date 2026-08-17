import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { numberingRuleSample } from '../helpers/numbering-rule-sample'
import { useDocumentBooks } from '../hooks/use-document-books'
import { useDocumentTypes } from '../hooks/use-document-types'
import {
  documentNumberingRuleSchema,
  type DocumentNumberingRuleFormValues,
} from '../schemas/document-numbering-rule-schema'
import {
  NUMBERING_DIRECTIONS,
  NUMBERING_TOKENS,
  type DocumentNumberingRule,
  type NumberingDirection,
} from '../types/document-numbering-rule'
import { ScopeChecklist, ScopeModeCard } from './numbering-rule-scope-fields'

const DEFAULT_NUMBERING_PATTERN = '{STT}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}'

interface DocumentNumberingRuleFormProps {
  formId: string
  rule?: DocumentNumberingRule
  /** Chiều đang mở ở danh sách — quy tắc mới nhận sẵn chiều đó. */
  initialDirection: NumberingDirection
  onSubmit: (values: DocumentNumberingRuleFormValues) => void
}

function emptyValues(direction: NumberingDirection): DocumentNumberingRuleFormValues {
  return {
    direction,
    pattern: DEFAULT_NUMBERING_PATTERN,
    start_no: 1,
    priority: 100,
    reset_yearly: true,
    allow_manual: false,
    is_active: true,
    doc_type_mode: 1,
    //  Văn bản nội bộ mặc định không vào sổ.
    book_mode: direction === 3 ? 3 : 1,
    doc_type_ids: [],
    book_ids: [],
  }
}

/**
 * Khai báo một quy tắc đánh số — hai card: mẫu số đánh ra sao, rồi áp cho ai.
 *
 * Quy tắc **đã cấp số ra ngoài thì khóa** phần sinh số (chiều, mẫu, số bắt đầu,
 * cách đếm): sửa mấy thứ đó là số cũ đã phát hành và số mới không còn cùng một
 * dãy. Phần còn lại (ưu tiên, cho sửa số, bật/tắt) vẫn đổi được.
 */
export function DocumentNumberingRuleForm({
  formId,
  rule,
  initialDirection,
  onSubmit,
}: DocumentNumberingRuleFormProps) {
  const form = useForm<DocumentNumberingRuleFormValues>({
    resolver: zodResolver(documentNumberingRuleSchema),
    defaultValues: emptyValues(initialDirection),
    // `values` chứ không chỉ `defaultValues`: bản ghi về sau lượt render đầu.
    values: rule
      ? {
          direction: rule.direction,
          pattern: rule.pattern,
          start_no: rule.start_no,
          priority: rule.priority,
          reset_yearly: rule.reset_yearly,
          allow_manual: rule.allow_manual,
          is_active: rule.is_active,
          doc_type_mode: rule.doc_type_mode,
          book_mode: rule.book_mode,
          doc_type_ids: rule.doc_type_ids,
          book_ids: rule.book_ids,
        }
      : undefined,
  })

  const { items: docTypes } = useDocumentTypes()
  const { items: books } = useDocumentBooks()

  const locked = Boolean(rule?.has_issued_numbers)
  const values = form.watch()
  //  Loại dùng mã tài liệu bất biến có bộ đếm riêng, không đi qua quy tắc này.
  const numberedTypes = docTypes.filter((item) => item.id_scheme === 2)
  const directionBooks = books.filter(
    (book) => book.kind === values.direction && book.is_active,
  )

  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        <Card>
          <CardContent className="space-y-5">
            <FormField
              control={form.control}
              name="direction"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Chiều văn bản</FormLabel>
                  <FormControl>
                    <RadioGroup
                      className="sm:flex sm:gap-6"
                      value={String(field.value)}
                      onValueChange={(value) => {
                        const next = Number(value) as NumberingDirection
                        field.onChange(next)
                        // Đổi chiều là đổi cả tập sổ chọn được — giữ lại lựa
                        // chọn cũ thì quy tắc trỏ vào sổ của chiều khác.
                        form.setValue('book_mode', next === 3 ? 3 : 1)
                        form.setValue('book_ids', [])
                      }}
                    >
                      {NUMBERING_DIRECTIONS.map((item) => (
                        <Label
                          key={item.value}
                          htmlFor={`direction-${item.value}`}
                          className="font-normal"
                        >
                          <RadioGroupItem
                            id={`direction-${item.value}`}
                            value={String(item.value)}
                            disabled={locked}
                          />
                          {item.label}
                        </Label>
                      ))}
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="pattern"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mẫu số hiệu</FormLabel>
                  <div className="flex flex-wrap gap-2">
                    {NUMBERING_TOKENS.map((item) => (
                      <Button
                        key={item.token}
                        type="button"
                        size="sm"
                        variant="secondary"
                        disabled={locked}
                        title={item.token}
                        onClick={() => field.onChange(`${field.value}${item.token}`)}
                      >
                        {item.label}
                      </Button>
                    ))}
                  </div>
                  <FormControl>
                    <Input
                      className="font-mono"
                      placeholder="Ví dụ: {STT}/{Nam}/{LoaiVB}"
                      disabled={locked}
                      {...field}
                    />
                  </FormControl>
                  <div className="rounded-md border border-dashed bg-muted/30 px-3 py-2 text-sm">
                    <span className="text-muted-foreground">Xem trước: </span>
                    <span className="font-mono font-medium">
                      {numberingRuleSample(
                        values.pattern,
                        values.start_no,
                        new Date().getFullYear(),
                      ) || 'Chưa có mẫu số'}
                    </span>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="start_no"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Bắt đầu từ số</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} disabled={locked} {...field} />
                    </FormControl>
                    <FormDescription>
                      {locked
                        ? 'Quy tắc đã cấp số nên không đổi được.'
                        : 'Chuyển từ sổ giấy đang dở thì nhập số kế tiếp.'}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="priority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mức ưu tiên</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} max={9999} {...field} />
                    </FormControl>
                    <FormDescription>Số nhỏ được xét trước.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 border-t pt-4 sm:grid-cols-3">
              <FormField
                control={form.control}
                name="reset_yearly"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start gap-3">
                    <FormControl>
                      <Checkbox
                        className="mt-0.5"
                        checked={field.value}
                        disabled={locked}
                        onCheckedChange={(checked) => field.onChange(checked === true)}
                      />
                    </FormControl>
                    <div className="space-y-1">
                      <FormLabel>Đếm lại mỗi năm</FormLabel>
                      <FormDescription>Tắt là đếm liên tục qua các năm.</FormDescription>
                    </div>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="allow_manual"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start gap-3">
                    <FormControl>
                      <Checkbox
                        className="mt-0.5"
                        checked={field.value}
                        onCheckedChange={(checked) => field.onChange(checked === true)}
                      />
                    </FormControl>
                    <div className="space-y-1">
                      <FormLabel>Cho phép văn thư sửa số</FormLabel>
                      <FormDescription>Sửa phải ghi lý do.</FormDescription>
                    </div>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start gap-3">
                    <FormControl>
                      <Checkbox
                        className="mt-0.5"
                        checked={field.value}
                        onCheckedChange={(checked) => field.onChange(checked === true)}
                      />
                    </FormControl>
                    <div className="space-y-1">
                      <FormLabel>Đang dùng</FormLabel>
                      <FormDescription>Tắt thì quy tắc không được xét nữa.</FormDescription>
                    </div>
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Áp dụng quy tắc này cho</p>
              <p className="text-sm text-muted-foreground">
                Quy tắc cụ thể hơn được chọn trước khi hai quy tắc cùng mức ưu tiên.
              </p>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <FormField
                control={form.control}
                name="doc_type_ids"
                render={({ field }) => (
                  <FormItem>
                    <ScopeModeCard
                      title="Loại văn bản"
                      name="doc-type-mode"
                      mode={values.doc_type_mode}
                      onModeChange={(mode) => {
                        form.setValue('doc_type_mode', mode as 1 | 2)
                        field.onChange([])
                      }}
                      options={[
                        { value: 1, label: 'Tất cả loại văn bản' },
                        { value: 2, label: 'Chọn loại văn bản' },
                      ]}
                    >
                      {values.doc_type_mode === 2 && (
                        <ScopeChecklist
                          name="doc-type"
                          items={numberedTypes}
                          selected={field.value}
                          onChange={field.onChange}
                        />
                      )}
                      <p className="text-xs text-muted-foreground">
                        Loại dùng mã tài liệu bất biến có bộ đếm riêng, không áp quy tắc này.
                      </p>
                      <FormMessage />
                    </ScopeModeCard>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="book_ids"
                render={({ field }) => (
                  <FormItem>
                    <ScopeModeCard
                      title="Sổ văn bản"
                      name="book-mode"
                      mode={values.book_mode}
                      onModeChange={(mode) => {
                        form.setValue('book_mode', mode as 1 | 2 | 3)
                        field.onChange([])
                      }}
                      options={[
                        { value: 1, label: 'Tất cả sổ văn bản' },
                        { value: 2, label: 'Chọn sổ văn bản' },
                        { value: 3, label: 'Văn bản không vào sổ' },
                      ]}
                    >
                      {values.book_mode === 2 && (
                        <ScopeChecklist
                          name="book"
                          items={directionBooks}
                          selected={field.value}
                          onChange={field.onChange}
                          emptyLabel="Chưa có sổ đang dùng cho chiều văn bản này."
                        />
                      )}
                      <FormMessage />
                    </ScopeModeCard>
                  </FormItem>
                )}
              />
            </div>

            {locked && (
              <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
                Quy tắc đã cấp số. Chiều, mẫu số, số bắt đầu và cách đếm được khóa để giữ
                nguyên các số đã ban hành.
              </p>
            )}
          </CardContent>
        </Card>
      </form>
    </Form>
  )
}
