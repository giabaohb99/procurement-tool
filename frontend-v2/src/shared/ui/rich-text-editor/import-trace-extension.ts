import { Extension } from '@tiptap/core'

/**
 * Mốc nguồn của nội dung dựng lại từ PDF.
 *
 * Thuộc tính này không hiện trên giấy, chỉ giúp hộp báo cáo import nhảy đúng tới
 * node đầu tiên của trang PDF cần rà soát. Giữ nó trong HTML để trace không bị
 * mất sau transaction serialize đầu tiên của Tiptap.
 */
export const ImportTrace = Extension.create({
  name: 'importTrace',

  addGlobalAttributes() {
    return [
      {
        types: ['paragraph', 'heading', 'image'],
        attributes: {
          importId: {
            default: null,
            parseHTML: (element) =>
              element.getAttribute('data-import-id') ||
              element.querySelector('img')?.getAttribute('data-import-id') ||
              null,
            renderHTML: (attributes) =>
              attributes.importId ? { 'data-import-id': attributes.importId } : {},
          },
          sourcePage: {
            default: null,
            parseHTML: (element) => {
              const page = Number.parseInt(
                element.getAttribute('data-source-page') ??
                  element.querySelector('img')?.getAttribute('data-source-page') ??
                  '',
                10,
              )
              return Number.isFinite(page) && page > 0 ? page : null
            },
            renderHTML: (attributes) =>
              attributes.sourcePage ? { 'data-source-page': attributes.sourcePage } : {},
          },
        },
      },
    ]
  },
})
