import { getBrowser, getPage, disconnectBrowser, outputJSON } from '/Users/tmduoc/.claude/skills/chrome-devtools/scripts/lib/browser.js';
const nghi = ms => new Promise(r=>setTimeout(r,ms));
const b = await getBrowser(); const p = await getPage(b);
await p.setViewport({ width: 1440, height: 900 });
await p.goto('http://localhost:8083/login', { waitUntil: 'domcontentloaded' });
await nghi(2000);
const inp = await p.$$('input');
await inp[0].type('TESTCONAGRI'); await inp[1].type('TESTCONAGRI');
await p.click('button[type=submit]'); await nghi(3000);

const out = {};
// Mở chuông
for (const h of await p.$$('button')) {
  const lbl = await h.evaluate(e => (e.getAttribute('aria-label')||'') + ' ' + (e.className||''));
  const svg = await h.evaluate(e => e.querySelector('svg')?.getAttribute('class') || '');
  if (svg.includes('lucide-bell')) { await h.click(); out.moChuong = true; break; }
}
await nghi(1500);
out.trongChuong = await p.evaluate(() => {
  const el = [...document.querySelectorAll('[role=dialog],[data-radix-popper-content-wrapper]')].pop();
  return el ? el.innerText.replace(/\n/g,' | ').slice(0, 260) : 'khong mo duoc';
});
// Bấm dòng thông báo của bản clone
out.bam = await p.evaluate(() => {
  const el = [...document.querySelectorAll('[data-radix-popper-content-wrapper] *')]
    .find(e => (e.innerText||'').startsWith('Bản nháp cần xử lý: ZZZ thu thong bao') && e.children.length < 6);
  if (!el) return false;
  (el.closest('button,[role=menuitem],li,div[tabindex]') || el).click();
  return true;
});
await nghi(3000);
out.urlSauBam = p.url();
outputJSON(out);
await disconnectBrowser();
