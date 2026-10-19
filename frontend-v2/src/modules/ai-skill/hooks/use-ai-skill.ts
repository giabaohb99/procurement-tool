import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { aiSkillApi } from '../api/ai-skill-api'
import type { SkillAccessGrantInput, SkillInput, SkillPatch, SkillSetInput, SkillSetPatch } from '../types/ai-skill'

/**
 * Hook TanStack Query của Kho skill AI. Lỗi của lệnh ghi đã có toast tự động ở `http-client` (in nguyên câu backend,
 * vd «Thiếu tóm tắt cho AI»), nên ở đây chỉ báo thành công và làm tươi khóa liên quan.
 */

export function useSkillSets() {
  return useQuery({ queryKey: queryKeys.aiSkill.sets(), queryFn: () => aiSkillApi.listSets() })
}

export function useSkillSet(id: number) {
  return useQuery({ queryKey: queryKeys.aiSkill.set(id), queryFn: () => aiSkillApi.getSet(id), enabled: id > 0 })
}

export function useCreateSkillSet() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SkillSetInput) => aiSkillApi.createSet(body),
    onSuccess: () => {
      toast.success('Đã tạo bộ skill.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.sets() })
    },
  })
}

export function useUpdateSkillSet(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SkillSetPatch) => aiSkillApi.updateSet(id, body),
    onSuccess: () => {
      toast.success('Đã lưu bộ skill.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.sets() })
    },
  })
}

export function useDeleteSkillSet() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => aiSkillApi.deleteSet(id),
    onSuccess: () => {
      toast.success('Đã xóa bộ skill.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.sets() })
    },
  })
}

export function useSkills(setId: number) {
  return useQuery({
    queryKey: queryKeys.aiSkill.skills(setId),
    queryFn: () => aiSkillApi.listSkills(setId),
    enabled: setId > 0,
  })
}

export function useCreateSkill(setId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SkillInput) => aiSkillApi.createSkill(setId, body),
    onSuccess: () => {
      toast.success('Đã tạo skill. Soạn nội dung rồi bấm Xuất bản để AI đọc được.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.sets() })
    },
  })
}

export function useImportSkillPackage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ setId, file, slug }: { setId: number; file: File; slug?: string }) =>
      aiSkillApi.importPackage(setId, file, slug),
    onSuccess: (result) => {
      const skipped = result.skipped.length > 0 ? `, bỏ qua ${result.skipped.length} tệp` : ''
      toast.success(
        result.replaced
          ? `Đã thay gói skill ${result.slug}: ${result.files} tệp đi kèm${skipped}. Bản nháp mới, bấm Xuất bản để AI đọc.`
          : `Đã tạo skill ${result.slug} từ gói: ${result.files} tệp đi kèm${skipped}.`,
      )
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.all })
    },
  })
}

export function useSkill(id: number) {
  return useQuery({ queryKey: queryKeys.aiSkill.skill(id), queryFn: () => aiSkillApi.getSkill(id), enabled: id > 0 })
}

/** Lưu NHÁP — `silent` cho lần lưu tự động trước khi xuất bản (một toast «Đã xuất bản» là đủ). */
export function useUpdateSkill(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ body }: { body: SkillPatch; silent?: boolean }) => aiSkillApi.updateSkill(id, body),
    onSuccess: (detail, { silent }) => {
      if (!silent) toast.success('Đã lưu nháp.')
      queryClient.setQueryData(queryKeys.aiSkill.skill(id), detail)
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.skills(detail.skill_set_id) })
    },
  })
}

export function useDeleteSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => aiSkillApi.deleteSkill(id),
    onSuccess: () => {
      toast.success('Đã xóa skill.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.all })
    },
  })
}

export function usePublishSkill(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (changeNote: string) => aiSkillApi.publishSkill(id, changeNote),
    onSuccess: (result) => {
      toast.success(`Đã xuất bản phiên bản ${result.version_no}. AI của người được gán đọc được bản này.`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.all })
    },
  })
}

export function useSkillVersions(skillId: number) {
  return useQuery({
    queryKey: queryKeys.aiSkill.versions(skillId),
    queryFn: () => aiSkillApi.listVersions(skillId),
    enabled: skillId > 0,
  })
}

export function useSkillVersion(versionId: number) {
  return useQuery({
    queryKey: queryKeys.aiSkill.version(versionId),
    queryFn: () => aiSkillApi.getVersion(versionId),
    enabled: versionId > 0,
  })
}

export function usePutSkillFile(skillId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ path, content }: { path: string; content: string }) => aiSkillApi.putFile(skillId, path, content),
    onSuccess: (file) => {
      toast.success(`Đã lưu tệp ${file.path}.`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.skill(skillId) })
    },
  })
}

export function useDeleteSkillFile(skillId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) => aiSkillApi.deleteFile(skillId, fileId),
    onSuccess: () => {
      toast.success('Đã xóa tệp.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.skill(skillId) })
    },
  })
}

export function useSkillAccess(targetKind: number, targetId: number) {
  return useQuery({
    queryKey: queryKeys.aiSkill.access(targetKind, targetId),
    queryFn: () => aiSkillApi.listAccess(targetKind, targetId),
    enabled: targetId > 0,
  })
}

export function useGrantSkillAccess(targetKind: number, targetId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: Omit<SkillAccessGrantInput, 'target_kind' | 'target_id'>) =>
      aiSkillApi.grantAccess({ ...body, target_kind: targetKind, target_id: targetId }),
    onSuccess: (result) => {
      const parts = [
        result.created > 0 && `thêm ${result.created}`,
        result.updated > 0 && `cập nhật ${result.updated}`,
        result.skipped > 0 && `bỏ qua ${result.skipped} (đã có y hệt)`,
      ].filter(Boolean)
      toast.success(`Đã lưu quyền đọc: ${parts.join(', ') || 'không có gì thay đổi'}.`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.access(targetKind, targetId) })
    },
  })
}

export function useRevokeSkillAccess(targetKind: number, targetId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) => aiSkillApi.revokeAccess(id, reason),
    onSuccess: () => {
      toast.success('Đã thu hồi dòng quyền.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.access(targetKind, targetId) })
    },
  })
}
