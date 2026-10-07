import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { extractErrorMessage } from '@/core/api'
import { LABOR_CONTRACT_TYPE } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { validateTemplateFile } from '../api/labor-contract-template-api'
import { useCompanies } from '../hooks/use-companies'
import {
  useCreateLaborContractTemplate,
  useReplaceLaborContractTemplateFile,
} from '../hooks/use-labor-contract-templates'
import { LaborContractTemplateFilePicker } from './labor-contract-template-file-picker'
import type { LaborContractTemplate } from '../types/labor-contract'
import { extractUnknownPlaceholders } from '../utils/labor-contract-template-errors'

/** Bám cột backend: name 200, note 500. `0` = chưa chọn nên bị chặn. */
const schema = z.object({
  name: z.string().trim().min(1, 'Nhập tên mẫu').max(200, 'Tên tối đa 200 ký tự'),
  company_id: z.number().int().min(1, 'Chọn pháp nhân'),
  contract_type: z.number().int().min(1, 'Chọn loại hợp đồng'),
  note: z.string().trim().max(500, 'Ghi chú tối đa 500 ký tự'),
})
type FormValues = z.infer<typeof schema>

const EMPTY: FormValues = { name: '', company_id: 0, contract_type: 0, note: '' }

interface UploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Có mẫu = chế độ «Thay tệp» (chỉ chọn tệp); không có = tải mẫu mới. */
  replacing?: LaborContractTemplate | null
}

/**
 * Hộp tải lên mẫu .docx mới, hoặc thay tệp của mẫu có sẵn.
 *
 * Toàn bộ state nằm ở `UploadDialogBody`, mà Radix chỉ dựng `DialogContent` khi hộp
 * MỞ — nên mỗi lần mở là một lần dựng mới, state tự sạch (không cần effect «reset»).
 */
export function LaborContractTemplateUploadDialog({ open, onOpenChange, replacing }: UploadDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <UploadDialogBody onOpenChange={onOpenChange} replacing={replacing} />
      </DialogContent>
    </Dialog>
  )
}

function UploadDialogBody({
  onOpenChange,
  replacing,
}: Pick<UploadDialogProps, 'onOpenChange' | 'replacing'>) {
  const isReplace = Boolean(replacing)
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [unknown, setUnknown] = useState<string[]>([])
  const [serverError, setServerError] = useState<string | null>(null)
  //  `disabled={isPending}` không chặn nổi bấm đúp (state chỉ đổi ở lượt render sau).
  const submittingRef = useRef(false)

  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: !isReplace })
  const create = useCreateLaborContractTemplate()
  const replace = useReplaceLaborContractTemplateFile()
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: EMPTY })

  function pickFile(files: File[]) {
    const picked = files[0]
    const problem = validateTemplateFile(picked)
    setFileError(problem)
    setFile(problem ? null : picked)
    setUnknown([])
    setServerError(null)
  }

  async function run(action: (picked: File) => Promise<unknown>) {
    const problem = validateTemplateFile(file)
    if (problem || !file) return setFileError(problem)
    if (submittingRef.current) return
    submittingRef.current = true
    setUnknown([])
    setServerError(null)
    try {
      await action(file)
      onOpenChange(false)
    } catch (error) {
      //  Biến lạ phải hiện NGAY trong hộp: toast biến mất sau vài giây còn người
      //  soạn mẫu thì cần danh sách đó để sửa trong Word.
      const bad = extractUnknownPlaceholders(error)
      setUnknown(bad)
      setServerError(extractErrorMessage(error))
    } finally {
      submittingRef.current = false
    }
  }

  const onCreate = (values: FormValues) =>
    run((picked) => create.mutateAsync({ values, file: picked }))
  const onReplace = () =>
    run((picked) => replace.mutateAsync({ id: replacing?.id ?? 0, file: picked }))
  const pending = create.isPending || replace.isPending

  const dropzone = (
    <LaborContractTemplateFilePicker
      file={file}
      fileError={fileError}
      serverError={serverError}
      unknown={unknown}
      busy={pending}
      onFiles={pickFile}
      onClear={() => setFile(null)}
    />
  )

  return (
    <>
        <DialogHeader>
          <DialogTitle>{isReplace ? `Thay tệp mẫu: ${replacing?.name}` : 'Tải lên mẫu hợp đồng'}</DialogTitle>
        </DialogHeader>

        {isReplace ? (
          <div className="space-y-4">
            {dropzone}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={pending}>Hủy</Button>
              <Button type="button" onClick={() => void onReplace()} disabled={pending || !file}>
                {pending && <Loader2 className="size-4 animate-spin" />}
                Thay tệp
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <Form {...form}>
            <form onSubmit={(e) => void form.handleSubmit(onCreate)(e)} className="space-y-4">
              <FormField control={form.control} name="name" render={({ field }) => (
                <FormItem>
                  <FormLabel>Tên mẫu <RequiredMark hint="Bắt buộc" /></FormLabel>
                  <FormControl><Input maxLength={200} {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField control={form.control} name="company_id" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Pháp nhân <RequiredMark hint="Bắt buộc" /></FormLabel>
                    <SearchSelect
                      value={field.value ? String(field.value) : ''}
                      onChange={(v) => field.onChange(Number(v) || 0)}
                      options={(companies?.items ?? []).map((c) => ({
                        value: String(c.id),
                        //  Kèm mã: có pháp nhân trùng tên (vd hai «CÔNG TY TNHH DEGO HOLDING»), chỉ tên thì chọn nhầm.
                        label: `${c.issue_code || c.code} — ${c.name}`,
                      }))}
                      placeholder="Chọn pháp nhân"
                      searchPlaceholder="Tìm pháp nhân…"
                    />
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form.control} name="contract_type" render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loại hợp đồng <RequiredMark hint="Bắt buộc" /></FormLabel>
                    <Select value={field.value ? String(field.value) : ''} onValueChange={(v) => field.onChange(Number(v))}>
                      <FormControl><SelectTrigger className="w-full"><SelectValue placeholder="Chọn loại" /></SelectTrigger></FormControl>
                      <SelectContent>
                        {LABOR_CONTRACT_TYPE.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )} />
              </div>
              <FormField control={form.control} name="note" render={({ field }) => (
                <FormItem>
                  <FormLabel>Ghi chú</FormLabel>
                  <FormControl><Textarea rows={2} maxLength={500} {...field} /></FormControl>
                  <FormMessage />
                </FormItem>
              )} />
              {dropzone}
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={pending}>Hủy</Button>
                <Button type="submit" disabled={pending || !file}>
                  {pending && <Loader2 className="size-4 animate-spin" />}
                  Tải lên
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
    </>
  )
}
