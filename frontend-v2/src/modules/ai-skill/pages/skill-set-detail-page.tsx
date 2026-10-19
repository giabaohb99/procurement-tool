import { History, Pencil, ShieldCheck, Sparkles, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { DetailPageHeader } from '@/shared/ui/detail-page-header'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { Skeleton } from '@/shared/ui/skeleton'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { ACCESS_TARGET } from '../config/ai-skill-constants'
import { SecurityLevelBadge, SkillStatusBadge } from '../config/ai-skill-meta'
import { SkillAccessTab } from '../components/skill-access-tab'
import { SkillListTab } from '../components/skill-list-tab'
import { SkillSetFormDialog } from '../components/skill-set-form-dialog'
import { useDeleteSkillSet, useSkillSet, useSkills } from '../hooks/use-ai-skill'

const TABS = ['skills', 'access', 'history'] as const
type TabKey = (typeof TABS)[number]

function readTab(raw: string | null): TabKey {
  return TABS.find((t) => t === raw) ?? 'skills'
}

/**
 * G3 — chi tiết một BỘ skill (doc 21 §6.2): tab Skill · Ai được đọc · Lịch sử. Tab đang mở giữ trên `?tab=` để gửi
 * link cho nhau mở đúng chỗ.
 */
export function SkillSetDetailPage() {
  const { id: rawId } = useParams()
  const setId = Number(rawId)
  const validId = Number.isInteger(setId) && setId > 0
  const navigate = useNavigate()
  const { can } = usePermission()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = readTab(searchParams.get('tab'))
  const { data: skillSet, isLoading, isError } = useSkillSet(validId ? setId : 0)
  //  Đường chi tiết bộ trả `skill_count = 0` (chỉ danh sách bộ mới đếm) — đếm theo đúng danh sách tab đang vẽ; cùng khóa
  //  truy vấn với tab Skill nên không gọi thêm.
  const { data: skills } = useSkills(validId ? setId : 0)
  const remove = useDeleteSkillSet()
  const [editOpen, setEditOpen] = useState(false)

  const canWrite = can('ai_skill', 'write')
  const canDelete = can('ai_skill', 'delete')

  if (!validId || isError) {
    return (
      <PageContainer>
        <ErrorState title="Không mở được bộ skill" description="Bộ này không tồn tại hoặc bạn không có quyền xem.">
          <Button variant="outline" onClick={() => navigate(appRoutes.aiSkill.root)}>
            Về danh sách bộ skill
          </Button>
        </ErrorState>
      </PageContainer>
    )
  }

  async function handleDelete() {
    if (!skillSet) return
    const ok = await confirm({
      title: 'Xóa bộ skill',
      message: `Xóa bộ ${skillSet.name}? AI sẽ không đọc được mọi skill trong bộ này nữa.`,
      confirmLabel: 'Xóa bộ',
    })
    if (!ok) return
    try {
      await remove.mutateAsync(skillSet.id)
      navigate(appRoutes.aiSkill.root)
    } catch {
      //  Toast lỗi tự động.
    }
  }

  return (
    <PageContainer>
      <DetailPageHeader
        backTo={appRoutes.aiSkill.root}
        backLabel="Về danh sách bộ skill"
        title={skillSet?.name ?? 'Bộ skill'}
        badges={
          skillSet && (
            <>
              <SkillStatusBadge status={skillSet.status} label={skillSet.status_label} />
              <SecurityLevelBadge level={skillSet.security_level} label={skillSet.security_level_label} />
            </>
          )
        }
        secondaryActions={
          skillSet && (
            <>
              {canWrite && (
                <Button type="button" variant="outline" onClick={() => setEditOpen(true)}>
                  <Pencil className="size-4" />
                  Sửa bộ
                </Button>
              )}
              {canDelete && (
                <Button type="button" variant="outline" onClick={() => void handleDelete()} disabled={remove.isPending}>
                  <Trash2 className="size-4" />
                  Xóa bộ
                </Button>
              )}
            </>
          )
        }
      />

      {isLoading || !skillSet ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <>
          {skillSet.description && <p className="text-sm text-muted-foreground">{skillSet.description}</p>}
          <Tabs
            value={tab}
            onValueChange={(value) => setSearchParams(value === 'skills' ? {} : { tab: value }, { replace: true })}
            className="space-y-4"
          >
            <ScrollableTabsList value={tab}>
              <TabsTrigger value="skills" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <Sparkles className="size-4" />
                Skill ({skills?.items.length ?? skillSet.skill_count})
              </TabsTrigger>
              <TabsTrigger value="access" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <ShieldCheck className="size-4" />
                Ai được đọc
              </TabsTrigger>
              <TabsTrigger value="history" className={cn('gap-2', TAB_TRIGGER_UNDERLINE)}>
                <History className="size-4" />
                Lịch sử
              </TabsTrigger>
            </ScrollableTabsList>

            <TabsContent value="skills">
              <Card className="p-4">
                <SkillListTab setId={skillSet.id} canWrite={canWrite} canDelete={canDelete} />
              </Card>
            </TabsContent>
            <TabsContent value="access">
              <SkillAccessTab targetKind={ACCESS_TARGET.skillSet} targetId={skillSet.id} canWrite={canWrite} />
            </TabsContent>
            <TabsContent value="history">
              <AuditTimeline entity="ai_skill_set" entityId={skillSet.id} />
            </TabsContent>
          </Tabs>
        </>
      )}

      <SkillSetFormDialog open={editOpen} onOpenChange={setEditOpen} skillSet={skillSet} />
    </PageContainer>
  )
}
