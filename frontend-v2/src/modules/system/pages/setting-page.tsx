import {
  CloudCheck,
  GitBranch,
  HardDrive,
  Info,
  KeyRound,
  Loader2,
  Mail,
  RefreshCw,
  Save,
  Send,
  SlidersHorizontal,
  Sparkles,
  Store,
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { Skeleton } from '@/shared/ui/skeleton'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'

import { settingApi } from '../api/setting-api'
import { EmailExclusionPanel } from '../components/email-exclusion-panel'
import { RagIndexPanel } from '../components/rag-index-panel'
import { SettingFieldRow } from '../components/setting-field-row'
import { SettingSecretRow } from '../components/setting-secret-row'
import { useSaveSettings, useSettings } from '../hooks/use-settings'
import type { SettingField, SettingGroup, SettingSecret } from '../types/setting'
import { buildSettingValues } from '../utils/build-setting-values'

/**
 * Các TAB của trang Cấu hình, mỗi tab bám đúng một `SettingGroup` backend trả về.
 *
 * ⚠️ **Tách tab ngày 14/09/2026** (duoc-CR-397). Trước đó sáu khối xếp dọc một
 * mạch, cuộn hơn ba màn hình: đổi một ô SMTP phải lăn qua cả khối lưu trữ và
 * bảng mẫu email. Khối *Mẫu email thông báo* đã ra TRANG RIÊNG
 * (`/system/email-templates`) chứ không thành tab — nó là nội dung soạn thảo,
 * không phải thông số, và tự lưu lấy chứ không dùng nút *Lưu cấu hình* chung.
 *
 * ⚠️ Ba tab cuối thêm ở bao-CR-429: đây là các thông số trước kia chỉ sửa được
 * bằng cách vào máy chủ sửa tệp môi trường rồi dựng lại dịch vụ. Hai hệ ngoài
 * tách thành HAI tab chứ không gộp một tab «Đồng bộ» — mỗi hệ có cầu dao và mã
 * đăng nhập riêng, xếp chung một thẻ thì lúc cần tắt gấp một hệ rất dễ tắt nhầm
 * hệ kia.
 */
const TABS: {
  value: string
  label: string
  icon: typeof Mail
  /** Nhóm ô nhập backend trả về; tab không có ô nhập nào thì bỏ trống. */
  group?: SettingGroup
  description: string
}[] = [
  {
    value: 'workflow',
    label: 'Quy trình duyệt',
    icon: GitBranch,
    group: 'workflow',
    description: 'Công tắc bật/tắt các bước duyệt dùng chung của hệ thống.',
  },
  {
    value: 'email',
    label: 'Email (SMTP)',
    icon: Mail,
    group: 'email',
    description: 'Máy chủ gửi email đi, địa chỉ người gửi và danh sách loại trừ.',
  },
  {
    value: 'storage',
    label: 'Lưu trữ (R2 / S3)',
    icon: HardDrive,
    group: 'storage',
    description: 'Kho lưu tệp đính kèm: endpoint, bucket và khóa truy cập.',
  },
  {
    value: 'assistant',
    label: 'Trợ lý AI',
    icon: Sparkles,
    group: 'ai',
    description:
      'Khóa API nhà cung cấp model, model dùng cho từng loại câu hỏi và trần chi phí mỗi ngày.',
  },
  {
    value: 'sync',
    label: 'App đặt xe (cũ)',
    icon: RefreshCw,
    group: 'sync',
    description:
      'Đường nối hai chiều với app đặt xe & duyệt dấu cũ: cầu dao bật tắt, địa chỉ, mã ký chung.',
  },
  {
    value: 'pos365',
    label: 'POS365 (Điểm cà phê)',
    icon: Store,
    group: 'pos365',
    description: 'Cửa hàng POS365 mà hệ thống kéo đơn về: địa chỉ, tài khoản và mã thanh toán.',
  },
  {
    value: 'system',
    label: 'Chung',
    icon: SlidersHorizontal,
    group: 'system',
    description: 'Địa chỉ giao diện dùng trong email, số ngày giữ thông báo và số bản sao lưu.',
  },
]

/**
 * CẤU HÌNH HỆ THỐNG — chỉnh nóng, không cần sửa `.env` hay dựng lại Docker.
 *
 * Danh sách trường do backend quyết định (`modules/setting/service.py`); trang
 * này chỉ vẽ theo `type`. Nhờ vậy thêm một cấu hình mới chỉ phải sửa một nơi.
 *
 * Khóa bí mật không bao giờ đi ngược từ server ra đây — xem `setting-secret-row.tsx`.
 */
export function SettingPage() {
  const { can } = usePermission()
  const canWrite = can('setting', 'write')
  // Nạp lại chỉ mục = việc của người quản HDSD, gác theo đúng quyền backend đòi
  // (`help_article.write`), không phải quyền sửa cấu hình.
  const canReindex = can('help_article', 'write')

  const { data, isPending, isError, refetch } = useSettings()
  const saveSettings = useSaveSettings()

  /**
   * Người dùng sửa nhiều ô rồi mới bấm Lưu một lần, nên phải giữ bản nháp. Giữ
   * dạng "chỉ những ô ĐÃ SỬA" chứ không sao chép cả danh sách vào state: sao
   * chép thì phải có `useEffect` đồng bộ lại mỗi khi tải xong, và mọi lần lưu
   * lại có một nhịp danh sách rỗng.
   */
  const [edited, setEdited] = useState<Record<string, unknown>>({})
  const [secretInputs, setSecretInputs] = useState<Record<string, string>>({})
  const [testTo, setTestTo] = useState('')
  const [testing, setTesting] = useState<'' | 'email' | 'storage'>('')
  const [tab, setTab] = useUrlParamState('tab', TABS[0].value)

  const draft: SettingField[] = (data?.fields ?? []).map((field) =>
    field.key in edited ? { ...field, value: edited[field.key] } : field,
  )

  function setFieldValue(key: string, value: unknown) {
    setEdited((prev) => ({ ...prev, [key]: value }))
  }

  async function save() {
    try {
      await saveSettings.mutateAsync(buildSettingValues(draft, secretInputs))
      // Xóa ô bí mật sau khi lưu: giữ lại là để mật khẩu nằm trong DOM suốt
      // phiên làm việc mà chẳng để làm gì. Xóa luôn bản nháp để màn hình quay
      // về đúng thứ server vừa xác nhận.
      setSecretInputs({})
      setEdited({})
      toast.success('Đã lưu cấu hình')
    } catch {
      // HTTP client đã hiện thông báo lỗi cho thao tác PUT.
    }
  }

  async function runTest(kind: 'email' | 'storage') {
    setTesting(kind)
    try {
      const result =
        kind === 'email' ? await settingApi.testEmail(testTo) : await settingApi.testStorage()
      // Backend trả 200 kèm `ok: false` khi kết nối hỏng — phải đọc `ok`, không
      // thể chỉ dựa vào việc lời gọi không ném lỗi.
      if (result.ok) toast.success(result.message)
      else toast.error(result.message)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setTesting('')
    }
  }

  if (isError && !data) {
    return (
      <PageContainer>
        <PageHeader title="Cấu hình hệ thống" />
        <ErrorState
          title="Không tải được cấu hình"
          description="Máy chủ chưa trả về danh sách cấu hình. Hãy thử lại sau ít phút."
        >
          <Button variant="outline" onClick={() => void refetch()}>
            Tải lại
          </Button>
        </ErrorState>
      </PageContainer>
    )
  }

  //  Tab đang xem ghi lên URL (`?tab=`) nên gửi link cho người khác vẫn ra đúng
  //  chỗ, và quay lại từ trang con không rơi về tab đầu.
  //  ⚠️ Tab *Trợ lý AI* TỪNG bị ẩn với người không có `help_article.write`, vì
  //  hồi đó nó chỉ có mỗi nút nạp lại chỉ mục. Từ bao-CR-429 nó chứa khóa API và
  //  trần chi phí, tức là việc của người quản trị cấu hình — ẩn nó đi thì người
  //  đúng vai lại không thấy. Nút nạp chỉ mục vẫn gác riêng theo quyền cũ.
  const visibleTabs = TABS
  const current = visibleTabs.find((item) => item.value === tab) ?? visibleTabs[0]

  //  Số ô đã sửa mà CHƯA lưu. Bắt buộc phải bày ra từ khi chia tab: sửa ở tab
  //  Email rồi chuyển sang tab Lưu trữ thì thay đổi kia biến mất khỏi tầm mắt,
  //  mà nút Lưu lại là nút CHUNG cho mọi tab — không có con số này thì người
  //  dùng hoặc quên bấm Lưu, hoặc bấm Lưu mà không biết mình đang lưu những gì.
  const dirtyCount = Object.keys(edited).length + Object.keys(secretInputs).length

  return (
    <PageContainer className="w-full">
      <PageHeader
        title="Cấu hình hệ thống"
        description={current?.description ?? 'Thông số chạy nóng của hệ thống.'}
        actions={
          canWrite && (
            <div className="flex items-center gap-2.5">
              {dirtyCount > 0 && (
                <span className="text-xs whitespace-nowrap text-warning">
                  {dirtyCount} thay đổi chưa lưu
                </span>
              )}
              <Button onClick={() => void save()} disabled={saveSettings.isPending || isPending}>
                {saveSettings.isPending ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Save className="size-4" />
                )}
                Lưu cấu hình
              </Button>
            </div>
          )
        }
      />

      <p className="mb-4 flex gap-2 rounded-lg border border-sky-200 bg-sky-50 px-3 py-2.5 text-[13px] text-sky-900 dark:border-sky-900/50 dark:bg-sky-950/40 dark:text-sky-200">
        <Info className="mt-0.5 size-4 shrink-0" />
        <span>
          Cấu hình lưu trong cơ sở dữ liệu (khóa bí mật được mã hóa), đổi tại đây có hiệu
          lực ngay, không cần sửa tệp <code>.env</code> hay dựng lại Docker. Ô khóa bí mật
          để trống nghĩa là giữ nguyên giá trị cũ. Tệp <code>.env</code> vẫn là giá trị dự
          phòng khi cơ sở dữ liệu chưa đặt.
        </span>
      </p>

      {!canWrite && (
        <p className="mb-4 rounded-lg bg-accent px-3 py-2 text-[13px] text-muted-foreground">
          Bạn chỉ có quyền xem cấu hình. Liên hệ Quản trị hệ thống nếu cần thay đổi.
        </p>
      )}

      {isPending ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-10" />
          <Skeleton className="h-64" />
        </div>
      ) : (
        <Tabs value={current?.value} onValueChange={setTab}>
          {/*  Dải tab cuộn ngang được ở khổ hẹp và tự kéo tab đang chọn vào tầm
               nhìn — xem `ScrollableTabsList`. */}
          <ScrollableTabsList value={current?.value ?? ''}>
            {visibleTabs.map((item) => (
              <TabsTrigger key={item.value} value={item.value} className={TAB_TRIGGER_UNDERLINE}>
                <item.icon className="size-4" />
                {item.label}
              </TabsTrigger>
            ))}
          </ScrollableTabsList>

          {visibleTabs.map((item) => (
            <TabsContent key={item.value} value={item.value} className="mt-4 flex flex-col gap-4">
              {item.group && (
                <SettingGroupCard
                  group={item.group}
                  fields={draft.filter((f) => f.group === item.group)}
                  secrets={(data?.secrets ?? []).filter((s) => s.group === item.group)}
                  canWrite={canWrite}
                  onFieldChange={setFieldValue}
                  secretInputs={secretInputs}
                  onSecretChange={(key, value) =>
                    setSecretInputs((prev) => ({ ...prev, [key]: value }))
                  }
                  testing={testing}
                  testTo={testTo}
                  onTestToChange={setTestTo}
                  onTest={runTest}
                />
              )}

              {/*  Loại trừ email đi CÙNG tab Email: nó là "ai KHÔNG nhận", đọc
                   liền mạch ngay dưới phần khai máy chủ gửi. */}
              {item.value === 'email' && <EmailExclusionPanel canWrite={canWrite} />}

              {item.value === 'assistant' && canReindex && <RagIndexPanel />}
            </TabsContent>
          ))}
        </Tabs>
      )}
    </PageContainer>
  )
}

interface SettingGroupCardProps {
  group: SettingGroup
  fields: SettingField[]
  secrets: SettingSecret[]
  canWrite: boolean
  onFieldChange: (key: string, value: unknown) => void
  secretInputs: Record<string, string>
  onSecretChange: (key: string, value: string) => void
  testing: '' | 'email' | 'storage'
  testTo: string
  onTestToChange: (value: string) => void
  onTest: (kind: 'email' | 'storage') => void
}

/**
 * Một NHÓM ô cấu hình: ô thường + ô bí mật + nút thử kết nối của nhóm đó.
 *
 * Tách khỏi `SettingPage` khi chia tab (duoc-CR-397) — thân trang có nhiều tab,
 * để nguyên khối này ở giữa thì đọc không ra đâu là khung tab đâu là ruột nhóm.
 */
function SettingGroupCard({
  group,
  fields,
  secrets,
  canWrite,
  onFieldChange,
  secretInputs,
  onSecretChange,
  testing,
  testTo,
  onTestToChange,
  onTest,
}: SettingGroupCardProps) {
  //  Nhóm rỗng thì không dựng thẻ — backend có thể chưa khai ô nào cho nhóm đó.
  if (fields.length === 0 && secrets.length === 0) return null

  //  `Card` trần chứ không `FormCard`: `FormCard` bắt buộc có tiêu đề, mà tiêu
  //  đề đó lặp đúng chữ trên tab đang chọn ngay phía trên.
  return (
    <Card className="p-4">
      <div className="grid gap-x-5 sm:grid-cols-2">
        {fields.map((field) => (
          <SettingFieldRow
            key={field.key}
            field={field}
            disabled={!canWrite}
            onChange={onFieldChange}
          />
        ))}
      </div>

      {secrets.length > 0 && (
        <div className="mt-3 border-t border-dashed pt-3">
          <p className="flex items-center gap-2 text-xs text-muted-foreground">
            <KeyRound className="size-3.5" />
            Khóa bí mật — mã hóa khi lưu và không hiển thị lại. Để trống nếu không đổi.
          </p>
          <div className="grid gap-x-5 sm:grid-cols-2">
            {secrets.map((secret) => (
              <SettingSecretRow
                key={secret.key}
                secret={secret}
                value={secretInputs[secret.key] ?? ''}
                disabled={!canWrite}
                onChange={onSecretChange}
              />
            ))}
          </div>
        </div>
      )}

      {canWrite && group === 'email' && (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-dashed pt-3">
          <Input
            className="max-w-64"
            placeholder="Email nhận thử…"
            value={testTo}
            onChange={(event) => onTestToChange(event.target.value)}
          />
          <Button variant="outline" disabled={testing === 'email'} onClick={() => onTest('email')}>
            {testing === 'email' ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
            Gửi email thử
          </Button>
          {/* Thử bằng cấu hình ĐANG LƯU, không phải bằng ô vừa gõ — nói rõ để
              không ai tưởng đã thử được thông số mới. */}
          <span className="text-xs text-muted-foreground">
            Dùng cấu hình đã lưu — hãy bấm Lưu trước khi thử.
          </span>
        </div>
      )}

      {canWrite && group === 'storage' && (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-dashed pt-3">
          <Button
            variant="outline"
            disabled={testing === 'storage'}
            onClick={() => onTest('storage')}
          >
            {testing === 'storage' ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <CloudCheck className="size-4" />
            )}
            Kiểm tra kết nối lưu trữ
          </Button>
          <span className="text-xs text-muted-foreground">
            Ghi rồi xóa một tệp thử trong bucket — dùng cấu hình đã lưu.
          </span>
        </div>
      )}
    </Card>
  )
}
