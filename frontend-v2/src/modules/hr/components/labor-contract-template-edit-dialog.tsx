// duoc-CR-606 (07/10/2026) — «Sửa thông tin» mẫu hợp đồng: tên · loại hợp đồng · ghi chú. Backend
// đã có PATCH từ đầu nhưng màn hình chưa có nút, đổi tên mẫu phải xóa rồi tải lại. Pháp nhân CỐ Ý
// không sửa được (mẫu gắn một pháp nhân suốt đời — `TemplateUpdate` backend không nhận `company_id`).
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useRef } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { LABOR_CONTRACT_TYPE } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useUpdateLaborContractTemplate } from '../hooks/use-labor-contract-templates'
import type { LaborContractTemplate } from '../types/labor-contract'

/** Bám cột backend: name 200, note 500 (`template_schema.py`). */
const schema = z.object({
  name: z.string().trim().min(1, 'Nhập tên mẫu').max(200, 'Tên tối đa 200 ký tự'),
  contract_type: z.number().int().min(1, 'Chọn loại hợp đồng'),
  note: z.string().trim().max(500, 'Ghi chú tối đa 500 ký tự'),
})
type FormValues = z.infer<typeof schema>

interface EditDialogProps {
  template: LaborContractTemplate | null
  onOpenChange: (open: boolean) => void
}

export function LaborContractTemplateEditDialog({ template, onOpenChange }: EditDialogProps) {
  return (
    <Dialog open={template !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        {/* Radix chỉ dựng nội dung khi mở → mỗi lần mở là một form mới, không cần effect reset. */}
        {template && <EditDialogBody template={template} onOpenChange={onOpenChange} />}
      </DialogContent>
    </Dialog>
  )
}

function EditDialogBody({ template, onOpenChange }: { template: LaborContractTemplate } & Pick<EditDialogProps, 'onOpenChange'>) {
  const update = useUpdateLaborContractTemplate()
  //  `disabled={isPending}` không chặn nổi bấm đúp (state chỉ đổi ở lượt render sau).
  const submittingRef = useRef(false)
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: template.name, contract_type: template.contract_type, note: template.note ?? '' },
  })

  //  `handleSubmit` gọi TRONG sự kiện submit (không lúc render) — gọi lúc render thì lint React
  //  Compiler báo «đọc ref lúc render». Cùng cách hộp tải mẫu đang làm.
  function save(values: FormValues) {
    if (submittingRef.current) return
    submittingRef.current = true
    update.mutate(
      { id: template.id, payload: { name: values.name, contract_type: values.contract_type, note: values.note } },
      {
        onSuccess: () => onOpenChange(false),
        onSettled: () => {
          submittingRef.current = false
        },
      },
    )
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>Sửa thông tin mẫu</DialogTitle>
        <DialogDescription>
          Pháp nhân «{template.company_name}» cố định theo mẫu. Muốn sửa nội dung hợp đồng thì dùng «Soạn nội dung».
        </DialogDescription>
      </DialogHeader>
      <Form {...form}>
        <form id="labor-contract-template-edit" className="space-y-4" onSubmit={(e) => void form.handleSubmit(save)(e)}>
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  Tên mẫu <RequiredMark />
                </FormLabel>
                <FormControl>
                  <Input {...field} maxLength={200} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="contract_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  Loại hợp đồng <RequiredMark />
                </FormLabel>
                <Select value={field.value ? String(field.value) : ''} onValueChange={(v) => field.onChange(Number(v))}>
                  <FormControl>
                    <SelectTrigger aria-label="Loại hợp đồng">
                      <SelectValue placeholder="Chọn loại hợp đồng" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {LABOR_CONTRACT_TYPE.map((o) => (
                      <SelectItem key={o.value} value={o.value}>
                        {o.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="note"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Ghi chú</FormLabel>
                <FormControl>
                  <Textarea {...field} rows={3} maxLength={500} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </form>
      </Form>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
          Hủy
        </Button>
        <Button type="submit" form="labor-contract-template-edit" disabled={update.isPending}>
          {update.isPending && <Loader2 className="size-4 animate-spin" />}
          Lưu
        </Button>
      </DialogFooter>
    </>
  )
}
