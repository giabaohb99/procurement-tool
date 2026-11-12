import { Save } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { useSaveHrSettings } from '../hooks/use-hr-settings'
import { useRoles } from '../hooks/use-roles'
import type { HrSettingField, HrSettingValues } from '../types/hr-setting'
import {
  HR_SETTING_DEPENDS_ON,
  HR_SETTING_TABS,
  toHrSettingPayload,
  toHrSettingValues,
} from '../utils/hr-setting-values'
import { HrSettingRow } from './hr-setting-row'
import { HrSettingsLeaveShortcuts } from './hr-settings-leave-shortcuts'

/**
 * Tab con kiểu gạch chân, cùng nét với `SubTabLink` (dải tab Thiết lập Nhân sự) để cả cụm
 * Thiết lập trông một kiểu — đè các lớp nền / bóng / bo góc mặc định của `TabsTrigger` shadcn.
 */
const SUB_TAB_TRIGGER =
  '-mb-px h-auto flex-none rounded-none border-0 border-b-2 border-transparent bg-transparent px-1 pt-0 pb-2 text-sm font-medium text-muted-foreground shadow-none transition-colors hover:text-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none dark:data-[state=active]:border-primary dark:data-[state=active]:bg-transparent'

interface HrSettingsFormProps {
  fields: HrSettingField[]
  /** Có `setting.write` — không có thì mọi ô chỉ xem. */
  canWrite: boolean
  /** Có `role.read` — không có thì danh sách vai trò hiện mã trơn, không mở ô chọn. */
  canReadRoles: boolean
}

/**
 * Thân trang Cài đặt nhân sự (duoc-CR-713), bố cục HR Settings của ERPNext: dải tab gạch chân + nút Lưu cùng một hàng,
 * mỗi tab một khung các dòng cài đặt. Tab dựng theo `tab` backend khai (`HR_SETTING_TABS`); tab không có ô nào thì
 * không dựng. Nút Lưu nằm ở hàng tiêu đề và lưu MỌI tab một lần, nên state của form ở đây chứ không ở từng tab.
 *
 * Trang cha gắn `key` theo dữ liệu đã lưu nên state khởi tạo lại sau mỗi lần lưu thành công.
 */
export function HrSettingsForm({ fields, canWrite, canReadRoles }: HrSettingsFormProps) {
  const saved = toHrSettingValues(fields)
  const [values, setValues] = useState<HrSettingValues>(saved)
  const save = useSaveHrSettings()
  //  `disabled={isPending}` chỉ đúng ở lượt render sau — bấm đúp liền tay vẫn ra hai lần lưu. Chặn bằng ref.
  const savingRef = useRef(false)
  const { data: roles } = useRoles({ enabled: canReadRoles })

  const dirty = JSON.stringify(values) !== JSON.stringify(saved)
  const tabs = HR_SETTING_TABS.filter((tab) => fields.some((field) => field.tab === tab.value))
  const roleOptions = canReadRoles
    ? (roles ?? []).map((role) => ({ id: role.code, label: role.name, hint: role.code }))
    : null

  const submit = () => {
    if (savingRef.current || !dirty) return
    savingRef.current = true
    save.mutate(toHrSettingPayload(fields, values), {
      onSuccess: () => toast.success('Đã lưu cài đặt nhân sự'),
      onSettled: () => {
        savingRef.current = false
      },
    })
  }

  if (tabs.length === 0) return null

  return (
    <Tabs defaultValue={tabs[0].value} className="flex min-h-0 flex-1 flex-col gap-0">
      {/*  duoc-CR-754: cùng khuôn với các màn khác của cụm Thiết lập — tab con đứng hàng tiêu đề (kiểu gạch chân như
           `SubTabLink`), nút Lưu bên phải, tiêu đề chỉ còn cho trình đọc màn hình (`hideTitle`). Nút Lưu vẫn lưu MỌI
           tab một lần. */}
      <PageHeader
        title="Cài đặt nhân sự"
        hideTitle
        description={
          <TabsList className="h-auto gap-4 rounded-none bg-transparent p-0">
            {tabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value} className={SUB_TAB_TRIGGER}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
        }
        actions={
          canWrite ? (
            <Button type="button" onClick={submit} disabled={!dirty || save.isPending}>
              <Save />
              Lưu
            </Button>
          ) : undefined
        }
      />
      {tabs.map((tab) => (
        <TabsContent key={tab.value} value={tab.value} className="mt-0 space-y-6">
          {!canWrite && (
            <p className="text-sm text-muted-foreground">Bạn chỉ xem được — sửa cần quyền Cấu hình hệ thống.</p>
          )}
          {/*  Khung thẻ trắng như khung bảng của các màn danh sách cùng cụm. */}
          <Card className="gap-0 divide-y py-0">
            {fields
              .filter((field) => field.tab === tab.value)
              .map((field) => {
                const parent = HR_SETTING_DEPENDS_ON[field.key]
                const parentOff = parent !== undefined && values[parent] !== true
                return (
                  <HrSettingRow
                    key={field.key}
                    field={field}
                    value={values[field.key]}
                    onChange={(value) => setValues((current) => ({ ...current, [field.key]: value }))}
                    disabled={!canWrite || parentOff}
                    muted={parentOff}
                    roleOptions={roleOptions}
                  />
                )
              })}
          </Card>
          {tab.value === 'leave' && <HrSettingsLeaveShortcuts />}
        </TabsContent>
      ))}
    </Tabs>
  )
}
