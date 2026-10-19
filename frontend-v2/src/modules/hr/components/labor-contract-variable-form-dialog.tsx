// duoc-CR-630 — hộp THÊM / SỬA một biến của mẫu hợp đồng. Biến HỆ THỐNG chỉ sửa tên hiển thị · mô tả ·
// ẩn khỏi danh sách (mã bất biến, giá trị lấy từ hệ thống); biến TÙY CHỈNH sửa đủ nhưng mã + kiểu bị KHÓA
// khi đã có mẫu / hợp đồng dùng (backend là chuẩn, giao diện chỉ hiện lý do).
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useRef } from 'react'
import { useForm } from 'react-hook-form'

import { LABOR_CONTRACT_VARIABLE_TYPE, labelOf } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { NumberInput } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import {
  useCreateLaborContractVariable,
  useLaborContractVariable,
  useUpdateLaborContractVariable,
} from '../hooks/use-labor-contract-variables'
import {
  buildVariableFormDefaults,
  buildVariableSchema,
  isSystemVariable,
  type VariableFormValues,
} from '../schemas/labor-contract-variable-schema'
import type { LaborContractVariable, LaborContractVariableDetail } from '../types/labor-contract-variable'
import { LaborContractVariableValueInput } from './labor-contract-variable-value-input'

interface FormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** `null` = THÊM biến tùy chỉnh mới. */
  variable: LaborContractVariable | null
}

export function LaborContractVariableFormDialog({ open, onOpenChange, variable }: FormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        {/* Radix chỉ dựng nội dung khi mở → mỗi lần mở là một form mới. */}
        {open && <Body variable={variable} onOpenChange={onOpenChange} />}
      </DialogContent>
    </Dialog>
  )
}

function Body({ variable, onOpenChange }: { variable: LaborContractVariable | null; onOpenChange: (open: boolean) => void }) {
  const detail = useLaborContractVariable(variable?.id ?? 0, variable !== null)
  if (variable && !detail.data) {
    return (
      <>
        <DialogHeader><DialogTitle>Sửa biến</DialogTitle></DialogHeader>
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          {detail.isError ? 'Không tải được thông tin biến.' : <><Loader2 className="size-4 animate-spin" /> Đang tải…</>}
        </p>
      </>
    )
  }
  return <FormBody variable={variable} detail={detail.data ?? null} onOpenChange={onOpenChange} />
}

function lockedSentence(detail: LaborContractVariableDetail | null, isSystem: boolean): string {
  if (isSystem) return 'Biến hệ thống — mã và cách lấy giá trị do hệ thống quy định, không đổi được.'
  const usage = detail?.usage
  return `Đang dùng trong ${usage?.template_count ?? 0} mẫu / ${usage?.contract_count ?? 0} hợp đồng — không đổi được mã và kiểu giá trị.`
}

function FormBody({ variable, detail, onOpenChange }: { variable: LaborContractVariable | null; detail: LaborContractVariableDetail | null } & { onOpenChange: (open: boolean) => void }) {
  const isSystem = isSystemVariable(variable)
  const locked = isSystem || Boolean(detail?.code_locked)
  const create = useCreateLaborContractVariable()
  const update = useUpdateLaborContractVariable()
  //  `disabled={isPending}` không chặn nổi bấm đúp (state chỉ đổi ở lượt render sau).
  const submittingRef = useRef(false)
  const form = useForm<VariableFormValues>({
    resolver: zodResolver(buildVariableSchema(isSystem)),
    //  Ưu tiên bản chi tiết (mới nhất từ máy chủ) — dòng bảng có thể đã cũ nếu người khác vừa sửa.
    defaultValues: buildVariableFormDefaults(detail ?? variable),
  })
  const valueType = form.watch('value_type')
  const pending = create.isPending || update.isPending

  function save(values: VariableFormValues) {
    if (submittingRef.current) return
    submittingRef.current = true
    const done = { onSuccess: () => onOpenChange(false), onSettled: () => { submittingRef.current = false } }
    if (!variable) {
      const { is_hidden: _hidden, ...payload } = values
      void _hidden
      create.mutate(payload, done)
    } else if (isSystem) {
      update.mutate({ id: variable.id, payload: { label: values.label, description: values.description, is_hidden: values.is_hidden } }, done)
    } else {
      const { is_hidden: _hidden, ...payload } = values
      void _hidden
      update.mutate({ id: variable.id, payload }, done)
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{variable ? 'Sửa biến' : 'Thêm biến tùy chỉnh'}</DialogTitle>
        <DialogDescription>
          {variable ? `Biến {{ ${variable.code} }}` : 'Biến tùy chỉnh được nhập tay theo từng hợp đồng rồi điền vào mẫu Word.'}
        </DialogDescription>
      </DialogHeader>
      <Form {...form}>
        <form id="labor-contract-variable-form" className="space-y-4" onSubmit={(e) => void form.handleSubmit(save)(e)}>
          <FormField control={form.control} name="code" render={({ field }) => (
            <FormItem>
              <FormLabel>Mã biến {!locked && <RequiredMark />}</FormLabel>
              {locked ? (
                <ReadOnlyValue>{field.value}</ReadOnlyValue>
              ) : (
                <FormControl><Input {...field} maxLength={40} placeholder="vd: so_ngay_phep" autoComplete="off" /></FormControl>
              )}
              {locked && variable && <FormDescription>{lockedSentence(detail, isSystem)}</FormDescription>}
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="label" render={({ field }) => (
            <FormItem>
              <FormLabel>Tên hiển thị <RequiredMark /></FormLabel>
              <FormControl><Input {...field} maxLength={200} /></FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="description" render={({ field }) => (
            <FormItem>
              <FormLabel>Mô tả</FormLabel>
              <FormControl><Textarea {...field} rows={2} maxLength={500} /></FormControl>
              <FormMessage />
            </FormItem>
          )} />

          {isSystem ? (
            <FormField control={form.control} name="is_hidden" render={({ field }) => (
              <FormItem className="flex items-center justify-between gap-3 rounded-md border p-3">
                <div>
                  <FormLabel>Ẩn khỏi danh sách hướng dẫn</FormLabel>
                  <FormDescription>Biến vẫn dùng được trong mẫu; chỉ không hiện ở khung «Chèn biến».</FormDescription>
                </div>
                <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} aria-label="Ẩn khỏi danh sách hướng dẫn" /></FormControl>
              </FormItem>
            )} />
          ) : (
            <>
              <FormField control={form.control} name="value_type" render={({ field }) => (
                <FormItem>
                  <FormLabel>Kiểu giá trị</FormLabel>
                  {locked ? (
                    <ReadOnlyValue>{labelOf(LABOR_CONTRACT_VARIABLE_TYPE, String(field.value))}</ReadOnlyValue>
                  ) : (
                    <Select value={String(field.value)} onValueChange={(v) => { field.onChange(Number(v)); form.setValue('default_value', '') }}>
                      <FormControl><SelectTrigger className="w-full" aria-label="Kiểu giá trị"><SelectValue /></SelectTrigger></FormControl>
                      <SelectContent>
                        {LABOR_CONTRACT_VARIABLE_TYPE.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  )}
                  <FormMessage />
                </FormItem>
              )} />
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField control={form.control} name="example" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ví dụ</FormLabel>
                    <FormControl><Input {...field} maxLength={255} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form.control} name="default_value" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Giá trị mặc định</FormLabel>
                    <LaborContractVariableValueInput key={valueType} valueType={valueType} value={field.value} onChange={field.onChange} aria-label="Giá trị mặc định" />
                    <FormDescription>Điền sẵn vào hợp đồng MỚI; đổi sau không ảnh hưởng hợp đồng đã lập.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )} />
              </div>
              <FormField control={form.control} name="sort_order" render={({ field }) => (
                <FormItem>
                  <FormLabel>Thứ tự</FormLabel>
                  <FormControl><NumberInput decimals={false} max={9999} value={field.value} onChange={field.onChange} aria-label="Thứ tự" /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              {([['is_required', 'Bắt buộc', 'Chặn Sinh tệp và chuyển sang «Đã ký» khi hợp đồng chưa nhập; lưu nháp thì không chặn.'],
                 ['is_active', 'Đang dùng', 'Tắt = ngừng dùng: biến không còn ở ô nhập và không nhận vào mẫu mới.']] as const).map(([name, label, hint]) => (
                <FormField key={name} control={form.control} name={name} render={({ field }) => (
                  <FormItem className="flex items-center justify-between gap-3 rounded-md border p-3">
                    <div><FormLabel>{label}</FormLabel><FormDescription>{hint}</FormDescription></div>
                    <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} aria-label={label} /></FormControl>
                  </FormItem>
                )} />
              ))}
            </>
          )}
        </form>
      </Form>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button>
        <Button type="submit" form="labor-contract-variable-form" disabled={pending}>
          {pending && <Loader2 className="size-4 animate-spin" />}
          Lưu
        </Button>
      </DialogFooter>
    </>
  )
}
