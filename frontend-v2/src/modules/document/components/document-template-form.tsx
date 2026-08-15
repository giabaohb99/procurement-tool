import { zodResolver } from '@hookform/resolvers/zod'
import { Info } from 'lucide-react'
import type { RefObject } from 'react'
import { useForm } from 'react-hook-form'

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
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { RichTextEditor, type RichTextEditorHandle } from '@/shared/ui/rich-text-editor'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { TabsContent } from '@/shared/ui/tabs'
import { Textarea } from '@/shared/ui/textarea'
import { useDocumentTypes } from '../hooks/use-document-types'
import {
  documentTemplateSchema,
  type DocumentTemplateFormValues,
} from '../schemas/document-template-schema'
import type { DocumentTemplate } from '../types/document-template'

interface DocumentTemplateFormProps {
  formId: string
  template?: DocumentTemplate
  onSubmit: (values: DocumentTemplateFormValues) => void
  onInvalid?: () => void
  editorRef: RefObject<RichTextEditorHandle | null>
}

const EMPTY_FORM: DocumentTemplateFormValues = {
  doc_type_id: 0,
  name: '',
  description: '',
  content_html: '',
  is_active: true,
}

export function DocumentTemplateForm({
  formId,
  template,
  onSubmit,
  onInvalid,
  editorRef,
}: DocumentTemplateFormProps) {
  const { items: documentTypes } = useDocumentTypes()
  const form = useForm<DocumentTemplateFormValues>({
    resolver: zodResolver(documentTemplateSchema),
    defaultValues: template ? { ...EMPTY_FORM, ...template } : EMPTY_FORM,
  })

  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(onSubmit, () => onInvalid?.())}>
        <TabsContent value="compose" forceMount className="mt-0 data-[state=inactive]:hidden">
          <RichTextEditor
            ref={editorRef}
            key={template?.id ?? 'new'}
            showOutline
            defaultContent={form.getValues('content_html')}
            onChange={(html) => form.setValue('content_html', html, { shouldDirty: true })}
          />
        </TabsContent>

        <TabsContent value="info" forceMount className="mt-0 data-[state=inactive]:hidden">
          <FormCard title="Thông tin văn bản mẫu" icon={Info} iconClassName="text-primary">
            <div className="grid items-stretch gap-4 xl:grid-cols-[minmax(0,3fr)_minmax(15rem,1fr)]">
              <div className="grid items-start gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tên văn bản mẫu</FormLabel>
                      <FormControl>
                        <Input placeholder="VD: Quyết định bổ nhiệm" {...field} />
                      </FormControl>
                      <FormDescription>
                        Tên dùng để nhận biết trong danh sách chọn mẫu.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="doc_type_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Loại văn bản</FormLabel>
                      <Select
                        value={field.value ? String(field.value) : ''}
                        onValueChange={(value) => field.onChange(Number(value))}
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="Chọn loại văn bản" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {documentTypes.map((type) => (
                            <SelectItem
                              key={type.id}
                              value={String(type.id)}
                              disabled={!type.is_active && type.id !== field.value}
                            >
                              {type.code} · {type.name}
                              {!type.is_active && ' (đã ngừng)'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Mẫu chỉ xuất hiện khi chọn đúng loại văn bản này.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem className="sm:col-span-2">
                      <FormLabel>Mô tả</FormLabel>
                      <FormControl>
                        <Textarea
                          rows={3}
                          placeholder="Mẫu này dùng trong trường hợp nào?"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex min-h-28 flex-row items-start justify-between gap-4 rounded-lg border bg-muted/35 p-4 xl:min-h-full">
                    <div className="space-y-1.5">
                      <FormLabel>Trạng thái sử dụng</FormLabel>
                      <FormDescription className="leading-relaxed">
                        Khi tắt, mẫu vẫn được lưu nhưng không xuất hiện lúc tạo văn bản mới.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
          </FormCard>
        </TabsContent>
      </form>
    </Form>
  )
}
