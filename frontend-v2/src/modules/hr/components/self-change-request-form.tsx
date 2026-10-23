import { Loader2, Send } from 'lucide-react'
import { useId, useRef, useState } from 'react'
import { toast } from 'sonner'

import { ChangeRequestFieldInput } from './change-request-field-input'
import { SelfChangeRequestFamiliesTab } from './self-change-request-families-tab'
import {
  CHANGE_REQUEST_GROUP_FIELDS,
  CHANGE_REQUEST_GROUP_LABELS,
} from '../config/employee-profile-fields'
import { useSubmitMyChangeRequest } from '../hooks/use-employee-change-requests'
import type { Employee, EmployeeFamily } from '../types/employee'
import { MARITAL_MARRIED } from '../types/employee-codes'
import type { ChangeRequestGroup, ChangeRequestValue } from '../types/employee-change-request'
import {
  NO_CHANGE_MESSAGE,
  buildChangeRequestPayload,
  readChangeRequestValues,
  type ChangeRequestFieldValues,
} from '../utils/employee-change-request-diff'
import { Button } from '@/shared/ui/button'
import { DialogFooter } from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { Textarea } from '@/shared/ui/textarea'

/** Trạng thái nạp hộ gia đình hiện tại (`/me/families`) mà hộp cần biết. */
export interface FamiliesSource {
  data: EmployeeFamily[] | undefined
  isLoading: boolean
  isError: boolean
  retry: () => void
}

const FIELD_GROUPS: readonly ChangeRequestGroup[] = ['personal', 'bank', 'documents']

/** Câu chặn khi đã sửa hộ gia đình mà danh sách gốc chưa nạp được (review M4). */
const FAMILIES_NOT_LOADED_MESSAGE =
  'Chưa tải được danh sách hộ gia đình hiện tại — tải lại rồi mới gửi phần hộ gia đình được.'

/**
 * Thân hộp «Đề nghị sửa thông tin» (duoc-CR-676): bốn tab, ô ghi chú, nút Gửi. Hộp ngoài
 * (`SelfChangeRequestDialog`) dựng lại thân này MỖI LẦN mở nên nháp luôn đi từ hồ sơ mới nhất.
 *
 * ⚠️ KHÔNG dùng `<form>` + react-hook-form: không có luật kiểm phía giao diện (độ dài chặn bằng
 * `maxLength`, giá trị do backend kiểm) nên không có «ô sai ở tab ẩn»; bỏ `<form>` thì Enter trong
 * ô không vô tình gửi đề nghị. Nháp giữ ở state của thân này nên đổi tab không mất chữ.
 *
 * ⚠️ Chặn bấm đúp bằng `useRef` (bẫy thứ tư): `disabled={isPending}` trễ một nhịp render.
 */
interface SelfChangeRequestFormProps {
  employee: Employee
  families: FamiliesSource
  onDone: () => void
}

export function SelfChangeRequestForm({ employee, families, onDone }: SelfChangeRequestFormProps) {
  const noteId = useId()
  const [baseline] = useState<ChangeRequestFieldValues>(() => readChangeRequestValues(employee))
  const [values, setValues] = useState<ChangeRequestFieldValues>(baseline)
  //  `null` = chưa đụng bảng hộ gia đình → giữ nguyên danh sách hiện tại. Không chép sẵn
  //  `families.data` vào state vì nó có thể về SAU khi hộp mở.
  const [familiesDraft, setFamiliesDraft] = useState<EmployeeFamily[] | null>(null)
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [tab, setTab] = useState<string>('personal')
  const submittingRef = useRef(false)
  const submit = useSubmitMyChangeRequest()

  function setField(field: keyof ChangeRequestFieldValues, value: ChangeRequestValue) {
    setValues((prev) => ({ ...prev, [field]: value }))
    setError('')
  }

  async function handleSubmit() {
    if (submittingRef.current) return
    //  Đã sửa hộ gia đình mà KHÔNG có danh sách gốc → không so được, gửi đi là thay cả danh sách
    //  bằng bản nháp và xóa nhầm người đang có (review M4). Chặn hẳn, không đoán.
    if (familiesDraft !== null && families.data === undefined) {
      setError(FAMILIES_NOT_LOADED_MESSAGE)
      toast.error(FAMILIES_NOT_LOADED_MESSAGE)
      return
    }
    const baselineFamilies = families.data ?? []
    const payload = buildChangeRequestPayload(baseline, baselineFamilies, {
      values,
      families: familiesDraft ?? baselineFamilies,
      note,
    })
    if (!payload) {
      setError(NO_CHANGE_MESSAGE)
      toast.error(NO_CHANGE_MESSAGE)
      return
    }
    submittingRef.current = true
    try {
      await submit.mutateAsync(payload)
      onDone()
    } catch {
      //  http-client đã toast lỗi (400 / 409 / 422) — giữ hộp mở để người dùng sửa tiếp.
    } finally {
      submittingRef.current = false
    }
  }

  const married = Number(values.marital_status) === MARITAL_MARRIED

  return (
    <div className="flex flex-col gap-4">
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="w-full flex-wrap">
          {FIELD_GROUPS.map((group) => (
            <TabsTrigger key={group} value={group}>
              {CHANGE_REQUEST_GROUP_LABELS[group]}
            </TabsTrigger>
          ))}
          <TabsTrigger value="families">{CHANGE_REQUEST_GROUP_LABELS.families}</TabsTrigger>
        </TabsList>

        {FIELD_GROUPS.map((group) => (
          <TabsContent key={group} value={group} className="mt-4">
            <div className="grid gap-4 sm:grid-cols-2">
              {CHANGE_REQUEST_GROUP_FIELDS[group]
                //  «Số con» chỉ hỏi khi đã khai có gia đình — cùng luật với màn hồ sơ (MARITAL_MARRIED).
                .filter((field) => field !== 'children_count' || married)
                .map((field) => (
                  <ChangeRequestFieldInput
                    key={field}
                    field={field}
                    value={values[field]}
                    onChange={(value) => setField(field, value)}
                  />
                ))}
            </div>
          </TabsContent>
        ))}

        <TabsContent value="families" className="mt-4">
          <SelfChangeRequestFamiliesTab
            families={families.data}
            familiesLoading={families.isLoading}
            familiesError={families.isError}
            onRetry={families.retry}
            draft={familiesDraft}
            onDraftChange={(rows) => {
              setFamiliesDraft(rows)
              setError('')
            }}
          />
        </TabsContent>
      </Tabs>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor={noteId}>Ghi chú cho phòng Nhân sự</Label>
        <Textarea
          id={noteId}
          rows={2}
          maxLength={500}
          value={note}
          placeholder="Ví dụ: đổi ngân hàng nhận lương từ tháng sau"
          onChange={(event) => setNote(event.target.value)}
        />
      </div>

      {error && (
        <p role="alert" className="text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onDone}>
          Hủy
        </Button>
        <Button type="button" onClick={() => void handleSubmit()} disabled={submit.isPending}>
          {submit.isPending ? <Loader2 className="animate-spin" /> : <Send />}
          Gửi đề nghị
        </Button>
      </DialogFooter>
    </div>
  )
}
