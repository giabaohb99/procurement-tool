import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { cn } from '@/shared/utils/cn'
import type { SurveyCatalog } from '../helpers/survey-catalog'
import { isSupplierFromCatalog, isSurveyLineFieldRequired } from '../helpers/survey-line'
import {
  SURVEY_TABLE_LABELS,
  sectionsOf,
  type SurveyLine,
  type SurveyTable,
} from '../types/survey-detail'
import { LineAttachments } from './line-attachments'
import { SurveyLineField } from './survey-line-field'

/** Đính kèm của dòng khảo sát có entity riêng, không chung với đầu phiếu. */
const LINE_ATTACHMENT_ENTITY = 'survey_line'

interface SurveyLineDialogProps {
  open: boolean
  table: SurveyTable
  line: SurveyLine | null
  lineNumber: number
  /**
   * `edit` = sửa cả dòng (phiếu còn nháp);
   * `fill` = bổ sung khi phiếu ĐÃ gửi và TP/QL báo "Thiếu thông tin".
   */
  mode: 'edit' | 'fill'
  editable: boolean
  approveEditable: boolean
  /** Phiếu đang chờ duyệt + người xem có quyền duyệt -> cho lưu riêng ô duyệt. */
  liveApprove: boolean
  /** Khóa ô còn thiếu của RIÊNG dòng này. */
  invalidKeys: Set<string>
  catalog: SurveyCatalog
  pendingFiles: File[]
  isSaving: boolean
  onPendingFilesChange: (files: File[]) => void
  onOpenChange: (open: boolean) => void
  onChange: (changes: Partial<SurveyLine>) => void
  onSaveFill: () => void
  onSaveApprove: () => void
}

/**
 * Popup chi tiết MỘT dòng khảo sát — chỗ duy nhất thấy đủ 27/30 ô.
 *
 * Sửa thẳng vào dòng đang hiển thị chứ không giữ bản nháp riêng: bảng và popup
 * là hai khung nhìn của cùng một dòng, tách bản nháp ra là gõ ở popup xong nhìn
 * lên bảng thấy số cũ.
 */
export function SurveyLineDialog({
  open,
  table,
  line,
  lineNumber,
  mode,
  editable,
  approveEditable,
  liveApprove,
  invalidKeys,
  catalog,
  pendingFiles,
  isSaving,
  onPendingFilesChange,
  onOpenChange,
  onChange,
  onSaveFill,
  onSaveApprove,
}: SurveyLineDialogProps) {
  if (!line) return null

  // Ở chế độ bổ sung, phiếu đã gửi nhưng dòng này vẫn phải điền tiếp được.
  const fieldsEditable = editable || mode === 'fill'
  const lineId = typeof line.id === 'number' ? line.id : 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>
            {SURVEY_TABLE_LABELS[table]} — dòng {lineNumber}
          </DialogTitle>
          <DialogDescription>
            {mode === 'fill'
              ? 'Trưởng phòng / Quản lý yêu cầu bổ sung. Điền thêm rồi bấm Lưu bổ sung.'
              : 'Toàn bộ thông tin của dòng. Sửa ở đây hay ở bảng đều là một.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {sectionsOf(table).map((section) => (
            <section key={section.title} className="rounded-lg border p-3">
              <h4 className="mb-3 text-sm font-semibold text-navy dark:text-foreground">
                {section.title}
              </h4>
              <div className="grid gap-x-4 gap-y-3 sm:grid-cols-2">
                {section.fields.map((field) => (
                  <div
                    key={field.key}
                    className={cn('space-y-1.5', field.full && 'sm:col-span-2')}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <Label>
                        {field.label}
                        {/* Dấu sao lấy thẳng từ hàm đang chặn lúc gửi duyệt, nên
                            ô lấy mẫu chỉ có sao khi dòng đã tick "Mẫu sẵn". */}
                        {isSurveyLineFieldRequired(table, field.key, line) && <RequiredMark />}
                      </Label>
                      {/* Công tắc "NCC sẵn có" đi kèm ô NCC chứ không đứng riêng:
                          nó chỉ đổi kiểu của đúng ô đó. */}
                      {field.type === 'supplier' && fieldsEditable && (
                        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Checkbox
                            checked={isSupplierFromCatalog(line, catalog.supplierCodes)}
                            onCheckedChange={(next) =>
                              onChange({ supplier_available: next === true })
                            }
                          />
                          NCC sẵn có
                        </label>
                      )}
                    </div>
                    <SurveyLineField
                      field={field}
                      line={line}
                      variant="form"
                      editable={fieldsEditable}
                      approveEditable={approveEditable}
                      invalid={invalidKeys.has(field.key)}
                      catalog={catalog}
                      onChange={onChange}
                    />
                    {field.note && (
                      <p className="text-xs text-muted-foreground">{field.note}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ))}

          <LineAttachments
            entity={LINE_ATTACHMENT_ENTITY}
            lineId={lineId}
            canManage={fieldsEditable}
            pendingFiles={pendingFiles}
            onPendingFilesChange={onPendingFilesChange}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          {mode === 'fill' && lineId > 0 && (
            <Button disabled={isSaving} onClick={onSaveFill}>
              Lưu bổ sung
            </Button>
          )}
          {liveApprove && lineId > 0 && (
            <Button disabled={isSaving} onClick={onSaveApprove}>
              Lưu duyệt dòng
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
