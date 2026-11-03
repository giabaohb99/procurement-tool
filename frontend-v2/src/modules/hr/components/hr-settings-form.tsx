import { Save } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { useIsBreadcrumbDuplicate } from '@/shared/ui/breadcrumb-page-label'
import { Button } from '@/shared/ui/button'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_LIST_UNDERLINE_ALWAYS, TAB_TRIGGER_UNDERLINE_ALWAYS } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
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

interface HrSettingsFormProps {
  fields: HrSettingField[]
  /** Có `setting.write` — không có thì mọi ô chỉ xem. */
  canWrite: boolean
  /** Có `role.read` — không có thì danh sách vai trò hiện mã trơn, không mở ô chọn. */
  canReadRoles: boolean
}

/**
 * Thân trang Cài đặt nhân sự (duoc-CR-713), bố cục HR Settings của ERPNext: hàng tiêu đề + nút Lưu, dải tab gạch chân,
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
  //  Breadcrumb đã ghi «Cài đặt nhân sự» thì không lặp lại ở hàng tiêu đề (duoc-CR-714).
  const titleHidden = useIsBreadcrumbDuplicate('Cài đặt nhân sự')

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
    <Tabs defaultValue={tabs[0].value} className="flex-1 gap-0">
      {/*  Tiêu đề trùng breadcrumb thì chỉ còn cho trình đọc màn hình (duoc-CR-714); khác thì hiện thành một hàng. */}
      {titleHidden ? (
        <h1 className="sr-only">Cài đặt nhân sự</h1>
      ) : (
        <div className="border-b px-4 py-3 md:px-6">
          <h1 className="text-lg font-semibold">Cài đặt nhân sự</h1>
        </div>
      )}
      {/*  Nút Lưu ở đầu PHẢI của dải tab (lưu mọi tab một lần). Khối nút giãn hết chiều cao hàng + có viền dưới riêng
           để đường kẻ chân chạy liền với đường kẻ của khung cuộn tab. */}
      <div className="flex">
        <ScrollableTabsList
          value={tabs[0].value}
          scroll="always"
          className="min-w-0 flex-1 max-md:mx-0"
          listClassName={cn(TAB_LIST_UNDERLINE_ALWAYS, 'gap-5 border-b-0 px-0')}
        >
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
              {tab.label}
            </TabsTrigger>
          ))}
        </ScrollableTabsList>
        {canWrite && (
          <div className="flex shrink-0 items-center border-b pr-4 md:pr-6">
            <Button type="button" size="sm" onClick={submit} disabled={!dirty || save.isPending}>
              <Save />
              Lưu
            </Button>
          </div>
        )}
      </div>
      {tabs.map((tab) => (
        <TabsContent key={tab.value} value={tab.value} className="mt-0 space-y-6 p-4 md:p-6">
          {!canWrite && (
            <p className="text-sm text-muted-foreground">Bạn chỉ xem được — sửa cần quyền Cấu hình hệ thống.</p>
          )}
          <div className="divide-y rounded-lg border">
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
          </div>
          {tab.value === 'leave' && <HrSettingsLeaveShortcuts />}
        </TabsContent>
      ))}
    </Tabs>
  )
}
