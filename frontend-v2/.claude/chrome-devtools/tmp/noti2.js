import { getBrowser, disconnectBrowser, outputJSON } from '/Users/tmduoc/.claude/skills/chrome-devtools/scripts/lib/browser.js';
const nghi = ms => new Promise(r=>setTimeout(r,ms));
const b = await getBrowser();
// Tự chọn tab: đóng hết tab trắng rồi mở một tab sạch.
for (const t of await b.pages()) { try { await t.close(); } catch {} }
const p = await b.newPage();
await p.setViewport({ width: 1440, height: 900 });

const out = {};
await p.goto('http://localhost:8083/login', { waitUntil: 'domcontentloaded' });
await nghi(2500);
const inp = await p.$$('input');
await inp[0].type('TESTCONAGRI'); await inp[1].type('TESTCONAGRI');
await p.click('button[type=submit]'); await nghi(3500);
out.sauDangNhap = p.url();

for (const h of await p.$$('button')) {
  const svg = await h.evaluate(e => e.querySelector('svg')?.getAttribute('class') || '');
  if (svg.includes('lucide-bell')) { await h.click(); out.moChuong = true; break; }
}
await nghi(1800);
out.trongChuong = await p.evaluate(() => {
  const el = [...document.querySelectorAll('[data-radix-popper-content-wrapper]')].pop();
  return el ? el.innerText.replace(/\n/g,' | ').slice(0, 240) : 'khong mo duoc';
});
out.bam = await p.evaluate(() => {
  const goc = [...document.querySelectorAll('[data-radix-popper-content-wrapper] *')]
    .filter(e => (e.innerText||'').includes('ZZZ thu thong bao') && e.children.length <= 3);
  const el = goc[goc.length - 1];
  if (!el) return false;
  (el.closest('[role=menuitem],button,li') || el.parentElement).click();
  return true;
});
await nghi(3000);
out.urlSauBam = p.url();
outputJSON(out);
await disconnectBrowser();
