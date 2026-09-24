import { useEffect } from 'react'

import { useTreeExpansion } from '@/shared/tree/use-tree-expansion'

const EXPANDED_STORAGE_KEY = 'erp.document.folders.expanded'

function readPersistedExpanded(): (string | number)[] {
  try {
    const raw = localStorage.getItem(EXPANDED_STORAGE_KEY)
    return raw ? (JSON.parse(raw) as (string | number)[]) : []
  } catch {
    return []
  }
}

/**
 * `useTreeExpansion` (dùng chung, không tự nhớ trạng thái) + đồng bộ
 * `localStorage` cho RIÊNG cây thư mục văn bản — tách khỏi `folder-tree-panel.tsx`
 * để tệp đó giữ dưới 200 dòng.
 */
export function usePersistedFolderTreeExpansion() {
  const expansion = useTreeExpansion({ defaultExpandedIds: readPersistedExpanded() })
  useEffect(() => {
    try {
      localStorage.setItem(EXPANDED_STORAGE_KEY, JSON.stringify(Array.from(expansion.expandedIds)))
    } catch {
      //  Trình duyệt chặn storage — vẫn dùng được, chỉ không nhớ sang phiên sau.
    }
  }, [expansion.expandedIds])
  return expansion
}
