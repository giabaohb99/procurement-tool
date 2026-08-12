import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
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
import { Textarea } from '@/shared/ui/textarea'
import { useSaveCompany } from '../hooks/use-companies'
import { useEmployees } from '../hooks/use-employees'
import {
  EMPTY_COMPANY_FORM,
  companySchema,
  type CompanyFormValues,
} from '../schemas/company-schema'
import type { Company } from '../types/company'
import { ActiveStatusSelect } from './active-status-select'
import { LookupSelect } from './lookup-select'

interface CompanyFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  company?: Company | null
}

/** Form thêm/sửa pháp nhân. Logo KHÔNG ở đây — đổi trực tiếp ở trang chi tiết. */
export function CompanyFormDialog({
  open,
  onOpenChange,
  company,
}: CompanyFormDialogProps) {
  const saveCompany = useSaveCompany()
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })

  const form = useForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: EMPTY_COMPANY_FORM,
  })

  useEffect(() => {
    if (!open) return
    form.reset(company ? { ...EMPTY_COMPANY_FORM, ...company } : EMPTY_COMPANY_FORM)
  }, [open, company, form])

  async function onSubmit(values: CompanyFormValues) {
    await saveCompany.mutateAsync({ id: company?.id, values })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{company ? 'Sửa công ty' : 'Thêm công ty'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Để trống để hệ thống tự sinh"
                        disabled={!!company}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

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
            </div>

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tên pháp nhân</FormLabel>
                  <FormControl>
                    <Input placeholder="Công ty Cổ phần …" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="invoice_email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email nhận hóa đơn</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} />
                  </FormControl>
                  <FormDescription>
                    Nơi nhận hóa đơn điện tử của pháp nhân này.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Địa chỉ</FormLabel>
                  <FormControl>
                    <Textarea rows={2} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="legal_representative_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Người đại diện pháp lý</FormLabel>
                    <LookupSelect
                      value={field.value}
                      // LookupSelect trả 0 cho mục bỏ chọn; backend nhận NULL.
                      onChange={(v) => field.onChange(v === 0 ? null : v)}
                      placeholder="Chọn nhân sự"
                      emptyLabel="— Chưa chỉ định —"
                      items={(employees?.items ?? []).map((e) => ({
                        id: e.id,
                        label: e.full_name,
                      }))}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="legal_rep_title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Chức danh</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Giám đốc" {...field} />
                    </FormControl>
                    <FormDescription>In trên hợp đồng / chứng từ.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="parent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Công ty mẹ (ID)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        value={field.value || ''}
                        onChange={(e) => field.onChange(Number(e.target.value) || 0)}
                      />
                    </FormControl>
                    <FormDescription>
                      ID pháp nhân cấp trên; để trống nếu đây là công ty gốc.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trạng thái</FormLabel>
                    <ActiveStatusSelect value={field.value} onChange={field.onChange} />
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Hủy
              </Button>
              <Button type="submit" disabled={saveCompany.isPending}>
                {saveCompany.isPending && <Loader2 className="size-4 animate-spin" />}
                Lưu
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
