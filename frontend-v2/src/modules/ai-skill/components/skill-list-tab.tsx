import { Plus, Trash2, Upload } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { formatDateTime } from '@/shared/utils/format-date'
import { SkillStatusBadge } from '../config/ai-skill-meta'
import { useDeleteSkill, useSkills } from '../hooks/use-ai-skill'
import type { Skill } from '../types/ai-skill'
import { SkillCreateDialog } from './skill-create-dialog'
import { SkillImportDialog } from './skill-import-dialog'

interface SkillListTabProps {
  setId: number
  canWrite: boolean
  canDelete: boolean
}

/** Tab «Skill» của chi tiết bộ (G3): bảng skill, bấm dòng mở trang soạn; thêm skill / tải gói / xóa skill. */
export function SkillListTab({ setId, canWrite, canDelete }: SkillListTabProps) {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useSkills(setId)
  const remove = useDeleteSkill()
  const [createOpen, setCreateOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)

  const columns = useMemo<DataTableColumn<Skill>[]>(
    () => [
      {
        key: 'title',
        header: 'Skill',
        width: 280,
        hideable: false,
        wrap: true,
        cell: (s) => (
          <div className="min-w-0">
            <div className="font-medium text-navy dark:text-foreground">{s.title || s.slug}</div>
            <div className="font-mono text-xs text-muted-foreground">{s.slug}</div>
          </div>
        ),
      },
      {
        key: 'summary',
        header: 'Tóm tắt cho AI',
        width: 320,
        wrap: true,
        cell: (s) =>
          s.summary ? (
            <span className="line-clamp-2 text-muted-foreground">{s.summary}</span>
          ) : (
            <span className="text-warning">Chưa có tóm tắt — chưa xuất bản được</span>
          ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 190,
        cell: (s) => (
          <div className="flex flex-wrap items-center gap-1">
            <SkillStatusBadge status={s.status} label={s.status_label} />
            {s.has_unpublished_changes && (
              <Badge variant="outline" className="font-normal text-warning">
                Có sửa chưa xuất bản
              </Badge>
            )}
          </div>
        ),
      },
      {
        key: 'version_no',
        header: 'Phiên bản',
        width: 100,
        align: 'right',
        cell: (s) => (s.version_no > 0 ? `v${s.version_no}` : '—'),
      },
      {
        key: 'published_at',
        header: 'Xuất bản',
        width: 150,
        cell: (s) => <span className="whitespace-nowrap text-muted-foreground">{formatDateTime(s.published_at)}</span>,
      },
      ...(canDelete
        ? [
            {
              key: 'actions',
              header: 'Thao tác',
              width: 90,
              hideable: false,
              cell: (s: Skill) => (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  aria-label={`Xóa skill ${s.slug}`}
                  disabled={remove.isPending}
                  onClick={async (event) => {
                    event.stopPropagation()
                    const ok = await confirm({
                      title: 'Xóa skill',
                      message: `Xóa skill ${s.slug}? AI sẽ không đọc được skill này nữa; lịch sử phiên bản vẫn giữ.`,
                      confirmLabel: 'Xóa',
                    })
                    if (ok) remove.mutate(s.id)
                  }}
                >
                  <Trash2 className="size-4" />
                </Button>
              ),
            } satisfies DataTableColumn<Skill>,
          ]
        : []),
    ],
    [canDelete, remove],
  )

  return (
    <div className="space-y-3">
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(s) => s.id}
        onRowClick={(s) => navigate(appRoutes.aiSkill.skillEditor(s.id))}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Bộ này chưa có skill nào. Thêm skill mới hoặc tải gói skill có sẵn lên."
        storageKey="ai-skill.skills"
        toolbarEnd={
          canWrite ? (
            <div className="flex gap-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setImportOpen(true)}>
                <Upload className="size-4" />
                Tải gói lên
              </Button>
              <Button type="button" size="sm" onClick={() => setCreateOpen(true)}>
                <Plus className="size-4" />
                Thêm skill
              </Button>
            </div>
          ) : undefined
        }
      />
      <SkillCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        setId={setId}
        onCreated={(skill) => navigate(appRoutes.aiSkill.skillEditor(skill.id))}
      />
      <SkillImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        setId={setId}
        onImported={(result) => navigate(appRoutes.aiSkill.skillEditor(result.skill_id))}
      />
    </div>
  )
}
