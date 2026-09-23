// Vẽ mũi tên cho các sơ đồ tài liệu hướng dẫn sử dụng.
// Dùng: đặt <svg class="arrows"></svg> trong #canvas, nạp tệp này, rồi gọi
// hArrow / vArrow / arrow sau khi các khối đã có mặt trong trang.

const SODO = (() => {
  const canvas = document.getElementById('canvas');
  const svg = canvas.querySelector('svg.arrows');
  const C = {
    blue: '#0ea5e9', amber: '#d97706', red: '#dc2626',
    green: '#16a34a', violet: '#7c3aed', gray: '#94a3b8',
  };
  const GAP = 8;

  svg.innerHTML = Object.entries(C).map(([k, v]) =>
    `<marker id="ah-${k}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="${v}"/></marker>`,
  ).join('');

  // Điểm neo ở cạnh l/r/t/b của một khối, tọa độ tính trong #canvas.
  function anchor(id, side, shift = 0) {
    const b = document.getElementById(id).getBoundingClientRect();
    const c = canvas.getBoundingClientRect();
    const x = b.left - c.left, y = b.top - c.top;
    if (side === 'l') return [x, y + b.height / 2 + shift];
    if (side === 'r') return [x + b.width, y + b.height / 2 + shift];
    if (side === 't') return [x + b.width / 2 + shift, y];
    return [x + b.width / 2 + shift, y + b.height];
  }

  // Vẽ đường gấp khúc qua `points`; nhãn đặt ở giữa đoạn dài nhất.
  function arrow(points, color, label, opts = {}) {
    const d = points.map((p, i) => (i ? 'L' : 'M') + p[0] + ',' + p[1]).join(' ');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', C[color]);
    path.setAttribute('stroke-width', '2.5');
    if (opts.dashed) path.setAttribute('stroke-dasharray', '6 5');
    path.setAttribute('marker-end', `url(#ah-${color})`);
    svg.appendChild(path);
    if (!label) return;
    let best = 0, seg = 1;
    for (let i = 1; i < points.length; i++) {
      const len = Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
      if (len > best) { best = len; seg = i; }
    }
    const [a, b] = [points[seg - 1], points[seg]];
    const at = opts.at ?? 0.5;
    const t = document.createElement('span');
    t.className = 'tag';
    t.style.setProperty('--c', C[color]);
    t.style.left = (a[0] + (b[0] - a[0]) * at) + 'px';
    t.style.top = (a[1] + (b[1] - a[1]) * at) + 'px';
    t.textContent = label;
    canvas.appendChild(t);
  }

  // Mũi tên ngang chạy thẳng theo tâm khối ĐÍCH — khối cao thấp khác nhau thì
  // lấy tâm khối nguồn sẽ ra đường xiên.
  function hArrow(from, to, color, label, opts = {}) {
    const t = anchor(to, 'l'), f = anchor(from, 'r');
    arrow([[f[0], t[1]], [t[0] - GAP, t[1]]], color, label, opts);
  }

  // Mũi tên dọc chạy thẳng theo tâm khối ĐÍCH, xuống (hoặc lên nếu đích ở trên).
  function vArrow(from, to, color, label, opts = {}) {
    const fb = document.getElementById(from).getBoundingClientRect();
    const tb = document.getElementById(to).getBoundingClientRect();
    const down = tb.top > fb.top;
    const t = anchor(to, down ? 't' : 'b', opts.shift ?? 0);
    const f = anchor(from, down ? 'b' : 't');
    arrow([[t[0], f[1]], [t[0], down ? t[1] - GAP : t[1] + GAP]], color, label, opts);
  }

  return { anchor, arrow, hArrow, vArrow, GAP };
})();
