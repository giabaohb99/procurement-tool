import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'

import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useSaveSupplier } from '../hooks/use-save-supplier'
import { supplierSchema, type SupplierFormValues } from '../schemas/supplier-schema'
import { SUPPLIER_TYPE_LABELS, type Supplier } from '../types/supplier'

interface SupplierFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Có = sửa, không có = thêm mới. */
  supplier?: Supplier | null
}

const EMPTY_FORM: SupplierFormValues = {
  code: '',
  name: '',
  supplier_type: 'goods',
  tax_code: '',
  phone: '',
  contact_person: '',
  address: '',
  vat: 0.08,
  is_active: true,
}

/** Form thêm/sửa nhà cung cấp — mẫu tham chiếu cho react-hook-form + zod trong hệ. */
export function SupplierFormDialog({
  open,
  onOpenChange,
  supplier,
}: SupplierFormDialogProps) {
  const saveSupplier = useSaveSupplier()

  const form = useForm<SupplierFormValues>({
    resolver: zodResolver(supplierSchema),
    defaultValues: EMPTY_FORM,
  })

  // Dialog không bị unmount giữa các lần mở nên phải nạp lại giá trị mỗi lần mở,
  // nếu không sẽ thấy dữ liệu của bản ghi trước.
  useEffect(() => {
    if (!open) return
    form.reset(supplier ? { ...EMPTY_FORM, ...supplier } : EMPTY_FORM)
  }, [open, supplier, form])

  async function onSubmit(values: SupplierFormValues) {
    await saveSupplier.mutateAsync({ id: supplier?.id, values })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {supplier ? 'Sửa nhà cung cấp' : 'Thêm nhà cung cấp'}
          </DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tên viết tắt</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: HOAPHAT" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="supplier_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loại</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(SUPPLIER_TYPE_LABELS).map(([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tên pháp lý</FormLabel>
                  <FormControl>
                    <Input placeholder="Công ty TNHH …" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="tax_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã số thuế</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Điện thoại</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="vat"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>VAT (%)</FormLabel>
                  <FormControl>
                    {/* Hiển thị theo phần trăm cho dễ nhập, lưu xuống dạng thập phân. */}
                    <Input
                      type="number"
                      step="0.1"
                      value={Math.round(field.value * 1000) / 10}
                      onChange={(e) => field.onChange(Number(e.target.value) / 100)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Hủy
              </Button>
              <Button type="submit" disabled={saveSupplier.isPending}>
                {saveSupplier.isPending && <Loader2 className="size-4 animate-spin" />}
                Lưu
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
