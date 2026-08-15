import { Hash, Loader2, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { useDocumentBooks } from '../hooks/use-document-books'
import {
  useDeleteDocumentNumberingRule,
  useDocumentNumberingRules,
  useSaveDocumentNumberingRule,
} from '../hooks/use-document-numbering-rules'
import { useDocumentTypes } from '../hooks/use-document-types'
import type { DocumentBook } from '../types/document-book'
import type { DocumentType } from '../types/document-type'
import {
  NUMBERING_DIRECTIONS,
  NUMBERING_TOKENS,
  type BookScopeMode,
  type DocumentNumberingRule,
  type DocumentNumberingRuleInput,
  type NumberingDirection,
  type ScopeMode,
} from '../types/document-numbering-rule'

const DEFAULT_PATTERN = '{STT}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}'

function emptyRule(direction: NumberingDirection): DocumentNumberingRuleInput {
  return {
    direction,
    pattern: DEFAULT_PATTERN,
    start_no: 1,
    reset_yearly: true,
    allow_manual: false,
    doc_type_mode: 1,
    book_mode: direction === 3 ? 3 : 1,
    priority: 100,
    is_active: true,
    doc_type_ids: [],
    book_ids: [],
  }
}

function inputFromRule(rule: DocumentNumberingRule): DocumentNumberingRuleInput {
  return {
    direction: rule.direction,
    pattern: rule.pattern,
    start_no: rule.start_no,
    reset_yearly: rule.reset_yearly,
    allow_manual: rule.allow_manual,
    doc_type_mode: rule.doc_type_mode,
    book_mode: rule.book_mode,
    priority: rule.priority,
    is_active: rule.is_active,
    doc_type_ids: rule.doc_type_ids,
    book_ids: rule.book_ids,
  }
}

function scopeText(rule: DocumentNumberingRule) {
  const types = rule.doc_type_mode === 1 ? 'Tất cả loại văn bản' : rule.doc_type_names.join(', ')
  const books =
    rule.book_mode === 1
      ? 'Tất cả sổ'
      : rule.book_mode === 3
        ? 'Không vào sổ'
        : rule.book_names.join(', ')
  return { types, books }
}

function sampleNumber(values: DocumentNumberingRuleInput) {
  const sample: Record<string, string> = {
    STT: String(values.start_no).padStart(2, '0'),
    Ngay: '15',
    Thang: '08',
    Nam: String(new Date().getFullYear()),
    LoaiVB: 'TB',
    PhongBan: 'HCNS',
    PhapNhan: 'DEGO',
    SoVB: 'CV',
  }
  return Object.entries(sample).reduce(
    (result, [token, value]) => result.replaceAll(`{${token}}`, value),
    values.pattern,
  )
}

export function DocumentNumberingRulesPage() {
  const [direction, setDirection] = useState<NumberingDirection>(1)
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<DocumentNumberingRule | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const { data, isLoading } = useDocumentNumberingRules(direction)
  const deleteRule = useDeleteDocumentNumberingRule()

  const rows = useMemo(() => {
    const keyword = search.trim().toLocaleLowerCase('vi')
    return (data?.items ?? []).filter((rule) => {
      if (!keyword) return true
      const scope = scopeText(rule)
      return [rule.pattern, scope.types, scope.books].some((value) =>
        value.toLocaleLowerCase('vi').includes(keyword),
      )
    })
  }, [data?.items, search])

  function openNew() {
    setEditing(null)
    setFormOpen(true)
  }

  function openEdit(rule: DocumentNumberingRule) {
    setEditing(rule)
    setFormOpen(true)
  }

  return (
    <PageContainer fill>
      <PageHeader
        title="Quy tắc đánh số"
        description="Thiết lập mẫu số hiệu và bộ đếm tự động cho từng chiều văn bản."
        actions={
          <Button onClick={openNew}>
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      <Card className="min-h-0 flex-1 gap-0 overflow-hidden py-0">
        <Tabs
          value={String(direction)}
          onValueChange={(value) => setDirection(Number(value) as NumberingDirection)}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="border-b bg-muted/30 px-4 pt-3">
            <TabsList>
              {NUMBERING_DIRECTIONS.map((item) => (
                <TabsTrigger key={item.value} value={String(item.value)}>
                  {item.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <CardContent className="flex min-h-0 flex-1 flex-col gap-4 p-4 lg:p-6">
            <div className="relative max-w-md">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Tìm theo mẫu số hoặc phạm vi áp dụng"
                className="pl-9"
              />
            </div>

            <Table containerClassName="min-h-0 flex-1 rounded-lg border">
              <TableHeader className="sticky top-0 z-10 bg-muted/70">
                <TableRow>
                  <TableHead className="w-[280px]">Quy tắc đánh số</TableHead>
                  <TableHead>Đối tượng áp dụng</TableHead>
                  <TableHead className="w-[110px]">Bắt đầu</TableHead>
                  <TableHead className="w-[150px]">Đánh số</TableHead>
                  <TableHead className="w-[130px]">Sửa số</TableHead>
                  <TableHead className="w-[120px]">Trạng thái</TableHead>
                  <TableHead className="w-[90px] text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                      <Loader2 className="mx-auto mb-2 size-5 animate-spin" />
                      Đang tải quy tắc
                    </TableCell>
                  </TableRow>
                ) : rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="h-32 text-center text-muted-foreground">
                      <Hash className="mx-auto mb-2 size-6" />
                      {search ? 'Không có quy tắc khớp tìm kiếm.' : 'Chưa có quy tắc nào.'}
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((rule) => {
                    const scope = scopeText(rule)
                    return (
                      <TableRow key={rule.id}>
                        <TableCell>
                          <button
                            type="button"
                            onClick={() => openEdit(rule)}
                            className="font-mono font-medium text-primary hover:underline"
                          >
                            {rule.pattern}
                          </button>
                          <div className="mt-1 text-xs text-muted-foreground">
                            Ưu tiên {rule.priority}
                            {rule.has_issued_numbers ? ' · Đã cấp số' : ''}
                          </div>
                        </TableCell>
                        <TableCell className="max-w-[360px] whitespace-normal">
                          <div className="line-clamp-1 font-medium">{scope.types}</div>
                          <div className="line-clamp-1 text-xs text-muted-foreground">
                            {scope.books}
                          </div>
                        </TableCell>
                        <TableCell className="tabular-nums">{rule.start_no}</TableCell>
                        <TableCell>
                          {rule.reset_yearly ? 'Theo từng năm' : 'Liên tục các năm'}
                        </TableCell>
                        <TableCell>{rule.allow_manual ? 'Cho phép' : 'Không'}</TableCell>
                        <TableCell>
                          <Badge variant={rule.is_active ? 'default' : 'secondary'}>
                            {rule.is_active ? 'Đang dùng' : 'Ngừng dùng'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end">
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              title="Sửa quy tắc"
                              onClick={() => openEdit(rule)}
                            >
                              <Pencil />
                            </Button>
                            <ConfirmIconButton
                              icon={Trash2}
                              title="Xóa quy tắc"
                              confirmTitle="Xóa quy tắc đánh số?"
                              confirmDescription={
                                rule.has_issued_numbers
                                  ? 'Quy tắc đã cấp số nên chỉ có thể chuyển sang Ngừng dùng.'
                                  : `Quy tắc ${rule.pattern} sẽ bị xóa vĩnh viễn.`
                              }
                              confirmLabel="Xóa"
                              destructive
                              disabled={rule.has_issued_numbers || deleteRule.isPending}
                              onConfirm={() => deleteRule.mutate(rule.id)}
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Tabs>
      </Card>

      {formOpen && (
        <NumberingRuleDialog
          key={editing?.id ?? 'new'}
          rule={editing}
          initialDirection={direction}
          open={formOpen}
          onOpenChange={setFormOpen}
        />
      )}
    </PageContainer>
  )
}

function NumberingRuleDialog({
  rule,
  initialDirection,
  open,
  onOpenChange,
}: {
  rule: DocumentNumberingRule | null
  initialDirection: NumberingDirection
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [values, setValues] = useState<DocumentNumberingRuleInput>(
    rule ? inputFromRule(rule) : emptyRule(initialDirection),
  )
  const [error, setError] = useState('')
  const { items: docTypes } = useDocumentTypes()
  const { items: books } = useDocumentBooks()
  const saveRule = useSaveDocumentNumberingRule()
  const locked = Boolean(rule?.has_issued_numbers)

  const directionBooks = books.filter((book) => book.kind === values.direction && book.is_active)

  function patch(next: Partial<DocumentNumberingRuleInput>) {
    setValues((current) => ({ ...current, ...next }))
    setError('')
  }

  function insertToken(token: string) {
    if (locked) return
    patch({ pattern: `${values.pattern}${token}` })
  }

  function submit() {
    const pattern = values.pattern.trim()
    if (!pattern.includes('{STT}')) {
      setError('Quy tắc phải có token {STT}.')
      return
    }
    if (values.doc_type_mode === 2 && values.doc_type_ids.length === 0) {
      setError('Hãy chọn ít nhất một loại văn bản.')
      return
    }
    if (values.book_mode === 2 && values.book_ids.length === 0) {
      setError('Hãy chọn ít nhất một sổ văn bản.')
      return
    }
    saveRule.mutate(
      { id: rule?.id, values: { ...values, pattern } },
      { onSuccess: () => onOpenChange(false) },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>{rule ? 'Sửa quy tắc đánh số' : 'Thiết lập quy tắc'}</DialogTitle>
          <DialogDescription>
            Quy tắc cụ thể hơn được chọn trước khi hai quy tắc có cùng mức ưu tiên.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <FieldBlock label="Chiều văn bản" required>
            <RadioGroup
              value={String(values.direction)}
              onValueChange={(value) =>
                patch({
                  direction: Number(value) as NumberingDirection,
                  book_mode: Number(value) === 3 ? 3 : 1,
                  book_ids: [],
                })
              }
            >
              {NUMBERING_DIRECTIONS.map((item) => (
                <Label key={item.value} htmlFor={`direction-${item.value}`}>
                  <RadioGroupItem
                    id={`direction-${item.value}`}
                    value={String(item.value)}
                    disabled={locked}
                  />
                  {item.label}
                </Label>
              ))}
            </RadioGroup>
          </FieldBlock>

          <FieldBlock label="Quy tắc đánh số" required>
            <div className="flex flex-wrap gap-2">
              {NUMBERING_TOKENS.map((item) => (
                <Button
                  key={item.token}
                  type="button"
                  size="sm"
                  variant="secondary"
                  disabled={locked}
                  onClick={() => insertToken(item.token)}
                  title={item.token}
                >
                  {item.label}
                </Button>
              ))}
            </div>
            <Input
              value={values.pattern}
              onChange={(event) => patch({ pattern: event.target.value })}
              disabled={locked}
              className="font-mono"
              placeholder="Ví dụ: {STT}/{Nam}/{LoaiVB}"
            />
            <div className="rounded-md border border-dashed bg-muted/30 px-3 py-2 text-sm">
              <span className="text-muted-foreground">Xem trước: </span>
              <span className="font-mono font-medium">
                {sampleNumber(values) || 'Chưa có mẫu số'}
              </span>
            </div>
          </FieldBlock>

          <div className="grid gap-4 sm:grid-cols-2">
            <FieldBlock label="Bắt đầu từ số" required>
              <Input
                type="number"
                min={1}
                value={values.start_no}
                disabled={locked}
                onChange={(event) => patch({ start_no: Math.max(1, Number(event.target.value)) })}
              />
            </FieldBlock>
            <FieldBlock label="Mức ưu tiên">
              <Input
                type="number"
                min={1}
                max={9999}
                value={values.priority}
                onChange={(event) => patch({ priority: Math.max(1, Number(event.target.value)) })}
              />
              <p className="text-xs text-muted-foreground">Số nhỏ được xét trước.</p>
            </FieldBlock>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <ChoiceCard
              title="Cách đánh số"
              options={[
                { value: 'year', label: 'Theo từng năm' },
                { value: 'continuous', label: 'Liên tiếp các năm' },
              ]}
              value={values.reset_yearly ? 'year' : 'continuous'}
              disabled={locked}
              onChange={(value) => patch({ reset_yearly: value === 'year' })}
            />
            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-medium">Tùy chọn sử dụng</h3>
              <CheckRow
                id="allow-manual"
                label="Cho phép văn thư sửa số"
                checked={values.allow_manual}
                onChange={(checked) => patch({ allow_manual: checked })}
              />
              <CheckRow
                id="rule-active"
                label="Đang sử dụng quy tắc"
                checked={values.is_active}
                onChange={(checked) => patch({ is_active: checked })}
              />
            </div>
          </div>

          <div className="border-t pt-5">
            <h3 className="mb-4 text-base font-semibold">Áp dụng quy tắc đánh số này cho</h3>
            <div className="grid gap-4 lg:grid-cols-2">
              <ScopeCard
                title="Loại văn bản"
                mode={values.doc_type_mode}
                onModeChange={(mode) => patch({ doc_type_mode: mode, doc_type_ids: [] })}
                allLabel="Tất cả loại văn bản"
                selectedLabel="Chọn loại văn bản"
              >
                {values.doc_type_mode === 2 && (
                  <ScopeChecklist
                    items={docTypes.filter((item) => item.id_scheme === 2)}
                    selected={values.doc_type_ids}
                    getLabel={(item) => `${item.code} · ${item.name}`}
                    onChange={(ids) => patch({ doc_type_ids: ids })}
                  />
                )}
                <p className="text-xs text-muted-foreground">
                  Loại dùng mã tài liệu bất biến có bộ đếm riêng và không áp dụng quy tắc này.
                </p>
              </ScopeCard>

              <BookScopeCard
                mode={values.book_mode}
                onModeChange={(mode) => patch({ book_mode: mode, book_ids: [] })}
              >
                {values.book_mode === 2 && (
                  <ScopeChecklist
                    items={directionBooks}
                    selected={values.book_ids}
                    getLabel={(item) => `${item.code} · ${item.name}`}
                    emptyLabel="Chưa có sổ đang dùng cho chiều văn bản này."
                    onChange={(ids) => patch({ book_ids: ids })}
                  />
                )}
              </BookScopeCard>
            </div>
          </div>

          {locked && (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
              Quy tắc đã cấp số. Chiều, mẫu số, số bắt đầu và cách đếm được khóa để giữ nguyên các
              số đã ban hành.
            </p>
          )}
          {error && <p className="text-sm font-medium text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button onClick={submit} disabled={saveRule.isPending}>
            {saveRule.isPending && <Loader2 className="size-4 animate-spin" />}
            {rule ? 'Lưu thay đổi' : 'Tạo quy tắc'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function FieldBlock({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <Label>
        {label}
        {required && <span className="text-destructive">*</span>}
      </Label>
      {children}
    </div>
  )
}

function CheckRow({
  id,
  label,
  checked,
  onChange,
}: {
  id: string
  label: string
  checked: boolean
  onChange: (checked: boolean) => void
}) {
  return (
    <Label htmlFor={id} className="font-normal">
      <Checkbox id={id} checked={checked} onCheckedChange={(value) => onChange(value === true)} />
      {label}
    </Label>
  )
}

function ChoiceCard({
  title,
  options,
  value,
  disabled,
  onChange,
}: {
  title: string
  options: Array<{ value: string; label: string }>
  value: string
  disabled?: boolean
  onChange: (value: string) => void
}) {
  return (
    <div className="space-y-3 rounded-lg border p-4">
      <h3 className="font-medium">{title}</h3>
      <RadioGroup value={value} onValueChange={onChange}>
        {options.map((option) => (
          <Label key={option.value} htmlFor={`${title}-${option.value}`} className="font-normal">
            <RadioGroupItem
              id={`${title}-${option.value}`}
              value={option.value}
              disabled={disabled}
            />
            {option.label}
          </Label>
        ))}
      </RadioGroup>
    </div>
  )
}

function ScopeCard({
  title,
  mode,
  onModeChange,
  allLabel,
  selectedLabel,
  children,
}: {
  title: string
  mode: ScopeMode
  onModeChange: (mode: ScopeMode) => void
  allLabel: string
  selectedLabel: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-3 rounded-lg border p-4">
      <h4 className="font-medium">{title}</h4>
      <RadioGroup
        value={String(mode)}
        onValueChange={(value) => onModeChange(Number(value) as ScopeMode)}
      >
        <Label htmlFor={`${title}-all`} className="font-normal">
          <RadioGroupItem id={`${title}-all`} value="1" />
          {allLabel}
        </Label>
        <Label htmlFor={`${title}-selected`} className="font-normal">
          <RadioGroupItem id={`${title}-selected`} value="2" />
          {selectedLabel}
        </Label>
      </RadioGroup>
      {children}
    </div>
  )
}

function BookScopeCard({
  mode,
  onModeChange,
  children,
}: {
  mode: BookScopeMode
  onModeChange: (mode: BookScopeMode) => void
  children: React.ReactNode
}) {
  return (
    <div className="space-y-3 rounded-lg border p-4">
      <h4 className="font-medium">Sổ văn bản</h4>
      <RadioGroup
        value={String(mode)}
        onValueChange={(value) => onModeChange(Number(value) as BookScopeMode)}
      >
        {[
          { value: 1, label: 'Tất cả sổ văn bản' },
          { value: 2, label: 'Chọn sổ văn bản' },
          { value: 3, label: 'Văn bản không vào sổ' },
        ].map((option) => (
          <Label key={option.value} htmlFor={`book-mode-${option.value}`} className="font-normal">
            <RadioGroupItem id={`book-mode-${option.value}`} value={String(option.value)} />
            {option.label}
          </Label>
        ))}
      </RadioGroup>
      {children}
    </div>
  )
}

function ScopeChecklist<T extends DocumentType | DocumentBook>({
  items,
  selected,
  getLabel,
  onChange,
  emptyLabel = 'Không có dữ liệu để chọn.',
}: {
  items: T[]
  selected: number[]
  getLabel: (item: T) => string
  onChange: (ids: number[]) => void
  emptyLabel?: string
}) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>
  }
  return (
    <div className="max-h-44 space-y-1 overflow-y-auto rounded-md border p-2">
      {items.map((item) => {
        const checked = selected.includes(item.id)
        return (
          <Label
            key={item.id}
            htmlFor={`scope-${item.id}-${getLabel(item)}`}
            className="rounded px-2 py-2 font-normal hover:bg-muted"
          >
            <Checkbox
              id={`scope-${item.id}-${getLabel(item)}`}
              checked={checked}
              onCheckedChange={(value) =>
                onChange(
                  value === true ? [...selected, item.id] : selected.filter((id) => id !== item.id),
                )
              }
            />
            <span className="truncate">{getLabel(item)}</span>
          </Label>
        )
      })}
    </div>
  )
}
