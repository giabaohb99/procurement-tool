import {
  CloudCheck,
  GitBranch,
  HardDrive,
  Info,
  KeyRound,
  Loader2,
  Mail,
  Save,
  Send,
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'

import { settingApi } from '../api/setting-api'
import { SettingFieldRow } from '../components/setting-field-row'
import { SettingSecretRow } from '../components/setting-secret-row'
import { useSaveSettings, useSettings } from '../hooks/use-settings'
import type { SettingField, SettingGroup } from '../types/setting'
import { buildSettingValues } from '../utils/build-setting-values'

const GROUPS: { key: SettingGroup; title: string; icon: typeof Mail }[] = [
  { key: 'workflow', title: 'Quy trình duyệt', icon: GitBranch },
  { key: 'email', title: 'Email (SMTP)', icon: Mail },
  { key: 'storage', title: 'Lưu trữ (R2 / S3)', icon: HardDrive },
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

  return (
    <PageContainer className="mx-auto w-full max-w-4xl">
      <PageHeader
        title="Cấu hình hệ thống"
        description="Thông số chạy nóng: quy trình duyệt, email gửi đi và kho lưu trữ tệp"
        actions={
          canWrite && (
            <Button onClick={() => void save()} disabled={saveSettings.isPending || isPending}>
              {saveSettings.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Save className="size-4" />
              )}
              Lưu cấu hình
            </Button>
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
          <Skeleton className="h-40" />
          <Skeleton className="h-64" />
          <Skeleton className="h-56" />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {GROUPS.map((group) => {
            const fields = draft.filter((f) => f.group === group.key)
            const secrets = (data?.secrets ?? []).filter((s) => s.group === group.key)
            if (fields.length === 0 && secrets.length === 0) return null

            return (
              <FormCard
                key={group.key}
                title={group.title}
                icon={group.icon}
                iconClassName="text-muted-foreground"
              >
                <div className="grid gap-x-5 sm:grid-cols-2">
                  {fields.map((field) => (
                    <SettingFieldRow
                      key={field.key}
                      field={field}
                      disabled={!canWrite}
                      onChange={setFieldValue}
                    />
                  ))}
                </div>

                {secrets.length > 0 && (
                  <div className="mt-3 border-t border-dashed pt-3">
                    <p className="flex items-center gap-2 text-xs text-muted-foreground">
                      <KeyRound className="size-3.5" />
                      Khóa bí mật — mã hóa khi lưu và không hiển thị lại. Để trống nếu
                      không đổi.
                    </p>
                    <div className="grid gap-x-5 sm:grid-cols-2">
                      {secrets.map((secret) => (
                        <SettingSecretRow
                          key={secret.key}
                          secret={secret}
                          value={secretInputs[secret.key] ?? ''}
                          disabled={!canWrite}
                          onChange={(key, value) =>
                            setSecretInputs((prev) => ({ ...prev, [key]: value }))
                          }
                        />
                      ))}
                    </div>
                  </div>
                )}

                {canWrite && group.key === 'email' && (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-dashed pt-3">
                    <Input
                      className="max-w-64"
                      placeholder="Email nhận thử…"
                      value={testTo}
                      onChange={(event) => setTestTo(event.target.value)}
                    />
                    <Button
                      variant="outline"
                      disabled={testing === 'email'}
                      onClick={() => void runTest('email')}
                    >
                      {testing === 'email' ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Send className="size-4" />
                      )}
                      Gửi email thử
                    </Button>
                    {/* Thử bằng cấu hình ĐANG LƯU, không phải bằng ô vừa gõ — nói
                        rõ để không ai tưởng đã thử được thông số mới. */}
                    <span className="text-xs text-muted-foreground">
                      Dùng cấu hình đã lưu — hãy bấm Lưu trước khi thử.
                    </span>
                  </div>
                )}

                {canWrite && group.key === 'storage' && (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-dashed pt-3">
                    <Button
                      variant="outline"
                      disabled={testing === 'storage'}
                      onClick={() => void runTest('storage')}
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
              </FormCard>
            )
          })}
        </div>
      )}
    </PageContainer>
  )
}
