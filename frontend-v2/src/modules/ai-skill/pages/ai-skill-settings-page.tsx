import { RotateCcw, Save } from 'lucide-react'
import { useRef, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { useMcpSettings, useSaveMcpSettings } from '../hooks/use-ai-usage'
import type { McpSettings } from '../types/ai-skill'
import { buildPatch, isPatchEmpty, toDraft, validateDraft, type McpSettingsDraft } from '../utils/mcp-settings-form'

/**
 * G7 — Cấu hình cổng MCP (doc 21 §6.2, hợp đồng doc/agent-hub/06 §7.3, backend ai-CR-216): bật / tắt NHÓM công cụ
 * ERP mà AI riêng của nhân sự được gọi, các trần tần suất, số ngày giữ nhật ký và câu dặn thêm cho AI. Đọc cần
 * `agent_group.read`, lưu cần `agent_group.write` (máy chủ trả `can_write`). Mục menu gác theo hai khóa của phân hệ như
 * Tổng quan; người thiếu `agent_group.read` mở ra thấy câu giải thích, không gọi để ăn 403.
 */
export function AiSkillSettingsPage() {
  const { can } = usePermission()
  const allowed = can('agent_group', 'read')
  const { data, isLoading, isError } = useMcpSettings(allowed)

  return (
    <PageContainer>
      <PageHeader
        title="Cấu hình"
        description="AI riêng của nhân sự được tra cứu những nhóm dữ liệu nào trong ERP, và được gọi nhanh tới đâu."
      />
      {!allowed ? (
        <ErrorState
          title="Cấu hình dành cho người quản lý trợ lý AI"
          description="Bạn vẫn dùng được Bộ skill và Nhật ký sử dụng ở menu bên trái."
        />
      ) : isError ? (
        <ErrorState title="Không tải được cấu hình" description="Dịch vụ AI chưa trả lời. Thử lại sau ít phút." />
      ) : isLoading || !data ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        //  `key` theo bản đã lưu: lưu xong bản nháp dựng lại từ dữ liệu mới, không giữ chuỗi cũ người dùng gõ.
        <SettingsForm key={JSON.stringify(toDraft(data))} settings={data} />
      )}
    </PageContainer>
  )
}

function SettingsForm({ settings }: { settings: McpSettings }) {
  const canWrite = settings.can_write === true
  const [draft, setDraft] = useState<McpSettingsDraft>(() => toDraft(settings))
  const save = useSaveMcpSettings()
  const savingRef = useRef(false)

  const errors = validateDraft(settings, draft)
  const hasErrors = Object.keys(errors).length > 0
  const patch = hasErrors ? null : buildPatch(settings, draft)
  const dirty = JSON.stringify(draft) !== JSON.stringify(toDraft(settings))

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!canWrite || !patch || isPatchEmpty(patch) || savingRef.current) return
    savingRef.current = true
    save.mutate(patch, {
      onSettled: () => {
        savingRef.current = false
      },
    })
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {!canWrite && (
        <p className="rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          Bạn đang xem ở chế độ chỉ đọc — sửa cấu hình cần quyền ghi trợ lý AI.
        </p>
      )}

      <Card>
        <CardHeader>
          <SectionHeading>Nhóm công cụ qua MCP</SectionHeading>
          <p className="text-sm text-muted-foreground">Nhóm tắt thì AI riêng không thấy công cụ trong nhóm; gọi thẳng cũng bị từ chối. Quyền xem dữ liệu của từng người vẫn giữ nguyên.</p>
        </CardHeader>
        <CardContent className="divide-y">
          {settings.groups.map((group) => {
            const enabled = draft.groups[group.key] ?? group.enabled
            const id = `mcp-group-${group.key}`
            return (
              <div key={group.key} className="flex items-start gap-3 py-3">
                <Switch
                  id={id}
                  checked={enabled}
                  disabled={!canWrite}
                  onCheckedChange={(checked) =>
                    setDraft((d) => ({ ...d, groups: { ...d.groups, [group.key]: checked } }))
                  }
                />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Label htmlFor={id} className="font-medium">
                      {group.label}
                    </Label>
                    {enabled !== group.default && (
                      <Badge variant="outline" className="text-xs">
                        Khác mặc định ({group.default ? 'bật' : 'tắt'})
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-xs break-words text-muted-foreground">
                    {group.tools.length} công cụ: {group.tools.join(', ')}
                  </p>
                </div>
              </div>
            )
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeading>Giới hạn</SectionHeading>
          <p className="text-sm text-muted-foreground">Áp cho mọi khóa kết nối AI riêng.</p>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          {settings.limits.map((limit) => {
            const id = `mcp-limit-${limit.key}`
            const error = errors[`limit:${limit.key}`]
            return (
              <div key={limit.key} className="space-y-1.5">
                <Label htmlFor={id}>{limit.label}</Label>
                <Input
                  id={id}
                  inputMode="numeric"
                  value={draft.limits[limit.key] ?? ''}
                  readOnly={!canWrite}
                  aria-invalid={error ? true : undefined}
                  onChange={(e) => setDraft((d) => ({ ...d, limits: { ...d.limits, [limit.key]: e.target.value } }))}
                />
                <p className={cn('text-xs', error ? 'text-destructive' : 'text-muted-foreground')}>
                  {error ??
                    `Từ ${limit.min} tới ${limit.max} · mặc định ${limit.default}${limit.min === 0 ? ' · 0 = không chặn' : ''}`}
                </p>
              </div>
            )
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeading>Câu dặn thêm cho AI</SectionHeading>
          <p className="text-sm text-muted-foreground">Nối sau lời dặn sẵn của cổng, AI riêng của mọi nhân sự đều đọc. Để trống nếu không cần.</p>
        </CardHeader>
        <CardContent className="space-y-1.5">
          <Textarea
            aria-label="Câu dặn thêm cho AI"
            rows={4}
            value={draft.extra}
            readOnly={!canWrite}
            aria-invalid={errors.extra ? true : undefined}
            onChange={(e) => setDraft((d) => ({ ...d, extra: e.target.value }))}
          />
          <p className={cn('text-right text-xs', errors.extra ? 'text-destructive' : 'text-muted-foreground')}>
            {draft.extra.trim().length} / {settings.extra_max_len}
          </p>
        </CardContent>
      </Card>

      {canWrite && (
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={!dirty || save.isPending}
            onClick={() => setDraft(toDraft(settings))}
          >
            <RotateCcw className="size-4" />
            Hoàn tác
          </Button>
          <Button type="submit" disabled={hasErrors || !patch || isPatchEmpty(patch) || save.isPending}>
            <Save className="size-4" />
            Lưu cấu hình
          </Button>
        </div>
      )}
    </form>
  )
}
