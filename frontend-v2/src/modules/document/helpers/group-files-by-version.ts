/** Tập trường tối thiểu để gom nhóm — `DocumentVersionFile` đầy đủ vẫn khớp. */
export interface GroupableFile {
  version_id: number
  version_no: string
  is_current_version: boolean
}

export interface FileVersionGroup<T> {
  versionId: number
  /** «Bản 2.0 · đang dùng» hoặc «Bản 1.0» — nhãn cha của nhánh trong cây tệp. */
  versionLabel: string
  isCurrent: boolean
  files: T[]
}

/** Chỉ MỘT phiên bản trong bộ tệp — cây phẳng, không có nút cha thừa. */
export interface FlatFileGroup<T> {
  flat: true
  files: T[]
}

export interface NestedFileGroup<T> {
  flat: false
  groups: FileVersionGroup<T>[]
}

/**
 * Gom tệp của tab «Tệp» (phase 09) THEO PHIÊN BẢN, cho `document-file-tree.tsx`
 * dựng cây: nhiều phiên bản → nhóm theo *Bản n.n · đang dùng* / *Bản n.n* (bản
 * mới trước); CHỈ một phiên bản (ca thường gặp nhất — văn bản chưa từng sửa
 * lớn/nhỏ) → trả cây PHẲNG, không bọc một nút cha vô nghĩa.
 *
 * Hàm THUẦN — không tự sắp tệp bên trong một nhóm (giữ nguyên thứ tự
 * `sort_order` mà backend đã trả).
 */
export function groupFilesByVersion<T extends GroupableFile>(
  files: T[],
): FlatFileGroup<T> | NestedFileGroup<T> {
  const versionIds = new Set(files.map((file) => file.version_id))
  if (versionIds.size <= 1) {
    return { flat: true, files }
  }

  const groupMap = new Map<number, FileVersionGroup<T>>()
  for (const file of files) {
    let group = groupMap.get(file.version_id)
    if (!group) {
      group = {
        versionId: file.version_id,
        versionLabel: file.is_current_version
          ? `Bản ${file.version_no} · đang dùng`
          : `Bản ${file.version_no}`,
        isCurrent: file.is_current_version,
        files: [],
      }
      groupMap.set(file.version_id, group)
    }
    group.files.push(file)
  }

  //  Bản ĐANG DÙNG lên đầu, còn lại theo id giảm dần (id lớn = phiên bản mở
  //  sau, tức mới hơn) — cùng thứ tự "bản mới trước" của yêu cầu.
  const groups = [...groupMap.values()].sort((a, b) => {
    if (a.isCurrent !== b.isCurrent) return a.isCurrent ? -1 : 1
    return b.versionId - a.versionId
  })
  return { flat: false, groups }
}
