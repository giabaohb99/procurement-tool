import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

export const keepSelectionVisibleKey = new PluginKey<boolean>('keepSelectionVisible')

/** Lớp tô vệt bôi đen khi trình soạn thảo mất con trỏ — khai ở `index.css`. */
export const KEEP_SELECTION_CLASS = 'doc-selection-giu'

/**
 * GIỮ VỆT BÔI ĐEN khi con trỏ rời khỏi vùng soạn thảo.
 *
 * Trình duyệt chỉ tô vùng chọn khi phần tử đang giữ con trỏ. Bấm vào một ô chọn
 * trên thanh công cụ là con trỏ nhảy sang cái menu, vệt bôi đen **biến mất ngay
 * trước mắt** — người dùng tưởng mình vừa mất phần đã chọn nên không dám bấm
 * tiếp. Người dùng báo đúng chuyện này ngày 20/08/2026.
 *
 * Thực tế vùng chọn KHÔNG mất: ProseMirror giữ nguyên trong state, và lệnh vẫn
 * áp đúng chỗ (đã dựng lại trên Chrome — bấm nấc giãn dòng sau khi menu mở vẫn
 * đổi đúng đoạn đã chọn). Hỏng là hỏng ở chỗ NHÌN, mà nhìn thấy sai thì người
 * dùng không tin tính năng.
 *
 * Cách vá: lúc mất con trỏ thì tự vẽ một lớp nền lên đúng khoảng đang chọn.
 * Google Docs và Word bản web đều làm vậy.
 */
export const KeepSelectionVisible = Extension.create({
  name: 'keepSelectionVisible',

  addProseMirrorPlugins() {
    return [
      new Plugin<boolean>({
        key: keepSelectionVisibleKey,

        state: {
          init: () => false,
          apply(tr, hasFocus) {
            //  `focus`/`blur` gửi cờ qua meta; giao dịch khác thì giữ nguyên.
            const moi = tr.getMeta(keepSelectionVisibleKey)
            return typeof moi === 'boolean' ? moi : hasFocus
          },
        },

        props: {
          //  Bắt ở tầng DOM để không phụ thuộc thứ tự khởi tạo của Tiptap.
          handleDOMEvents: {
            focus: (view) => {
              view.dispatch(view.state.tr.setMeta(keepSelectionVisibleKey, true))
              return false
            },
            blur: (view) => {
              view.dispatch(view.state.tr.setMeta(keepSelectionVisibleKey, false))
              return false
            },
          },

          decorations(state) {
            const hasFocus = keepSelectionVisibleKey.getState(state)
            if (hasFocus) return DecorationSet.empty

            const { from, to, empty } = state.selection
            //  Con trỏ nhấp nháy một chỗ thì không có gì để tô.
            if (empty || from >= to) return DecorationSet.empty

            return DecorationSet.create(state.doc, [
              Decoration.inline(from, to, { class: KEEP_SELECTION_CLASS }),
            ])
          },
        },
      }),
    ]
  },
})
