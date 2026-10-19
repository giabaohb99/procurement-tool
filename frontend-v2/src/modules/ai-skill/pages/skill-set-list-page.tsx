import { BookOpen, Plus, Search, Upload } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { stripDiacritics } from '@/shared/utils/vn-text'
import { SKILL_SET_STATUS_OPTIONS } from '../config/ai-skill-constants'
import { SecurityLevelBadge, SkillStatusBadge } from '../config/ai-skill-meta'
import { SkillImportDialog } from '../components/skill-import-dialog'
import { SkillSetFormDialog } from '../components/skill-set-form-dialog'
import { useSkillSets } from '../hooks/use-ai-skill'
import type { SkillSet } from '../types/ai-skill'

const ALL = 'all'

/**
 * G2 — danh sách BỘ skill (doc 21 §6.2, K5 bao-CR-623). Backend trả cả danh sách theo quyền người xem (không phân
 * trang — một công ty có vài chục bộ), nên tìm kiếm và lọc trạng thái làm ngay trên trình duyệt.
 */
export function SkillSetListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canCreate = can('ai_skill', 'create')
  const canWrite = can('ai_skill', 'write')
  const { data, isLoading, isError } = useSkillSets()
  const { data: departments } = useDepartments({ page_size: 500 })
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [createOpen, setCreateOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)

  const departmentNames = useMemo(
    () => new Map((departments?.items ?? []).map((d) => [d.id, d.name] as const)),
    [departments],
  )

  const sets = data?.items
  const rows = useMemo(() => {
    if (!sets) return undefined
    const needle = stripDiacritics(debouncedValue.trim().toLowerCase())
    return sets.filter((s) => {
      if (status !== ALL && String(s.status) !== status) return false
      if (!needle) return true
      return stripDiacritics(`${s.name} ${s.code} ${s.description}`.toLowerCase()).includes(needle)
    })
  }, [sets, debouncedValue, status])

  const columns = useMemo<DataTableColumn<SkillSet>[]>(
    () => [
      {
        key: 'name',
        header: 'Tên bộ',
        width: 300,
        hideable: false,
        wrap: true,
        cell: (s) => (
          <div className="min-w-0">
            <div className="font-medium text-navy dark:text-foreground">{s.name}</div>
            {s.description && <div className="line-clamp-2 text-xs text-muted-foreground">{s.description}</div>}
          </div>
        ),
      },
      { key: 'code', header: 'Mã', width: 130, defaultHidden: true, cell: (s) => s.code || '—' },
      {
        key: 'owner_department',
        header: 'Phòng chủ quản',
        width: 180,
        cell: (s) => (
          <span className="text-muted-foreground">
            {s.owner_department_id ? (departmentNames.get(s.owner_department_id) ?? `Phòng #${s.owner_department_id}`) : '—'}
          </span>
        ),
      },
      { key: 'skill_count', header: 'Số skill', width: 90, align: 'right', cell: (s) => s.skill_count },
      {
        key: 'security_level',
        header: 'Mức bảo mật',
        width: 120,
        cell: (s) => <SecurityLevelBadge level={s.security_level} label={s.security_level_label} />,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 120,
        cell: (s) => <SkillStatusBadge status={s.status} label={s.status_label} />,
      },
      {
        key: 'updated_at',
        header: 'Cập nhật',
        width: 150,
        cell: (s) => <span className="whitespace-nowrap text-muted-foreground">{formatDateTime(s.updated_at)}</span>,
      },
    ],
    [departmentNames],
  )

  const isEmpty = sets !== undefined && sets.length === 0
  const filtering = debouncedValue.trim() !== '' || status !== ALL

  return (
    <PageContainer fill>
      <PageHeader
        title="Bộ skill"
        description="Cẩm nang công ty viết cho AI đọc. Gán bộ cho phòng ban hay chức vụ nào thì AI của người đó dùng được."
        actions={
          <>
            {canWrite && (sets?.length ?? 0) > 0 && (
              <Button variant="outline" onClick={() => setImportOpen(true)}>
                <Upload className="size-4" />
                Tải gói lên
              </Button>
            )}
            {canCreate && (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="size-4" />
                Tạo bộ
              </Button>
            )}
          </>
        }
      />

      {isEmpty ? (
        //  Trạng thái rỗng doc 21 §6.3 — câu gợi việc đầu tiên thay cho bảng trắng.
        <Card className="flex flex-1 flex-col items-center justify-center gap-3 p-10 text-center">
          <BookOpen className="size-10 text-muted-foreground" />
          <p className="max-w-md text-sm text-muted-foreground">
            Bắt đầu bằng một bộ skill cho phòng của bạn — ví dụ quy trình thu mua. Mỗi skill là một trang hướng dẫn AI
            đọc trước khi trả lời.
          </p>
          {canCreate && (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" />
              Tạo bộ đầu tiên
            </Button>
          )}
        </Card>
      ) : (
        <Card className="flex min-h-0 flex-1 flex-col p-4">
          <DataTable
            fillHeight
            columns={columns}
            rows={rows}
            getRowId={(s) => s.id}
            onRowClick={(s) => navigate(appRoutes.aiSkill.setDetail(s.id))}
            isLoading={isLoading}
            isError={isError}
            emptyMessage={filtering ? 'Không có bộ skill nào khớp bộ lọc.' : 'Chưa có bộ skill nào.'}
            storageKey="ai-skill.sets"
            toolbar={
              <>
                <div className="relative min-w-56 flex-1 md:max-w-xs">
                  <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder="Tìm theo tên, mã, mô tả…"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                  />
                </div>
                <Select value={status} onValueChange={setStatus}>
                  <SelectTrigger className="w-44" aria-label="Lọc trạng thái">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                    {SKILL_SET_STATUS_OPTIONS.map((o) => (
                      <SelectItem key={o.value} value={String(o.value)}>
                        {o.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </>
            }
          />
        </Card>
      )}

      <SkillSetFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={(created) => navigate(appRoutes.aiSkill.setDetail(created.id))}
      />
      <SkillImportDialog open={importOpen} onOpenChange={setImportOpen} sets={sets} />
    </PageContainer>
  )
}
