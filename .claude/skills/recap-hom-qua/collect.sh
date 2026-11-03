#!/usr/bin/env bash
# Gom dữ liệu thô cho bài recap "hôm qua có gì mới" — chỉ ĐỌC, không sửa gì.
# Dùng: bash .claude/skills/recap-hom-qua/collect.sh [YYYY-MM-DD từ ngày] [YYYY-MM-DD tới ngày]
# Mặc định: từ đầu ngày làm việc trước (thứ Hai thì lấy từ thứ Bảy) tới hiện tại, giờ Việt Nam.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
export TZ=Asia/Ho_Chi_Minh

if [ "${1:-}" ]; then
  SINCE="$1"
else
  dow=$(date +%u)                      # 1 = thứ Hai
  if [ "$dow" = 1 ]; then SINCE=$(date -d "2 days ago" +%F); else SINCE=$(date -d "yesterday" +%F); fi
fi
UNTIL="${2:-$(date -d tomorrow +%F)}"
RANGE=(--since="$SINCE 00:00" --until="$UNTIL 00:00")

git fetch -q origin 2>/dev/null || echo "!! git fetch lỗi — số liệu có thể cũ"
echo "# KHOẢNG: $SINCE 00:00 → $UNTIL 00:00 (giờ VN)"

for BR in erp-v2 main; do
  echo
  echo "## COMMIT trên origin/$BR (không tính merge)"
  git log "origin/$BR" "${RANGE[@]}" --no-merges --date=format:'%d/%m %H:%M' \
      --format='%h | %ad | %an | %s' | sed 's/^/  /'
done

echo
echo "## ĐÃ LÊN PROD CHƯA: commit erp-v2 trong khoảng mà main CHƯA có (theo nội dung, cherry-pick cũng tính)"
git log origin/main...origin/erp-v2 "${RANGE[@]}" --no-merges --cherry-pick --right-only \
    --format='  %h | %an | %s' 2>/dev/null | head -60

echo
echo "## ĐỐI CHIẾU THEO MÃ CR (cherry-pick có xung đột thì bảng trên báo nhầm — tin bảng này hơn)"
for cr in $(git log origin/erp-v2 "${RANGE[@]}" --no-merges --format='%s' | grep -oE '[a-z]+-CR-[0-9]+' | sort -u); do
  if git log origin/main --since="60 days ago" --format='%s' | grep -q -- "$cr\b"; then st="ĐÃ trên main (prod)"; else st="CHƯA lên prod"; fi
  echo "  $cr | $st"
done

echo
echo "## TỆP THÊM (A) / XÓA (D) / ĐỔI TÊN (R) trên erp-v2 — đây là chỗ sinh hoặc mất chức năng"
git log origin/erp-v2 "${RANGE[@]}" --no-merges --name-status --format='@@%an' |
  awk '/^@@/{who=substr($0,3); next} NF==0{next}
       $1 ~ /^[ADR]/ && $NF !~ /^test\/|\.test\.tsx?$/ {k=substr($1,1,1)" | "$NF; if(!(k in s)){s[k]=who} else if(index(s[k],who)==0){s[k]=s[k]","who}}
       END{for(k in s) print "  " k " | " s[k]}' | sort

echo
echo "## TỆP SỬA (M) gom theo khu — số tệp · người"
git log origin/erp-v2 "${RANGE[@]}" --no-merges --name-status --format='@@%an' |
  awk '/^@@/{who=substr($0,3); next} NF==0{next}
       $1=="M" {f=$NF
         if (f ~ /^test\/|\.test\.tsx?$/) next
         n=split(f,p,"/"); area=p[1]
         if (f ~ /^backend\/app\/modules\//) area="backend:"p[4]
         else if (f ~ /^backend\/app\/core\//) area="backend:core"
         else if (f ~ /seed_help_/) area="hdsd:"p[3]
         else if (f ~ /^backend\//) area="backend:"p[2]
         else if (f ~ /^frontend-v2\/src\/modules\//) area="v2:"p[4]
         else if (f ~ /^frontend-v2\//) area="v2:"p[3]
         else if (f ~ /^doc\//) area="doc:"p[2]"/"p[3]
         if(!((area,f) in seen)){seen[area,f]=1; cnt[area]++}
         if(index(who_of[area],who)==0) who_of[area]=who_of[area] (who_of[area]?",":"") who}
       END{for(a in cnt) printf "  %-45s %3d tệp · %s\n", a, cnt[a], who_of[a]}' | sort

echo
echo "## TÀI LIỆU / HDSD / KẾ HOẠCH đã sửa (đầy đủ đường dẫn)"
git log origin/erp-v2 "${RANGE[@]}" --no-merges --name-status --format= -- doc plans 'backend/scripts/seed_help_*' |
  awk '{print "  " substr($1,1,1) " | " $NF}' | sort -u
echo "  (bài kiểm: $(git log origin/erp-v2 "${RANGE[@]}" --no-merges --name-only --format= | grep -cE '^test/|\.test\.tsx?$') lượt tệp — không liệt kê)"

echo
echo "## DÒNG CR MỚI / ĐỔI trong change-log (dòng thêm vào trong khoảng)"
base=$(git rev-list -1 --before="$SINCE 00:00" origin/erp-v2)
for f in doc/tai-lieu-ky-thuat/change-log.md doc/tai-lieu-ky-thuat/change-log-bao.md doc/tai-lieu-ky-thuat/change-log-ai.md; do
  [ -f "$f" ] || continue
  git diff "$base" origin/erp-v2 -- "$f" | grep -E '^\+\| \*\*' | cut -c2-900 | sed 's/^/  /'
done

echo
echo "## MỤC SỔ TASK có date trong khoảng (hoặc vừa đổi trạng thái)"
git diff "$base" origin/erp-v2 -- doc/tai-lieu-ky-thuat/nhat-ky-task.md |
  grep -E '^\+(## |- status:|- date:|- pic:)' | cut -c2-300 | sed 's/^/  /' | head -120

echo
echo "## MIGRATION mới"
git diff --name-only --diff-filter=A "$base" origin/erp-v2 -- backend/migrations/versions | sed 's/^/  /'

echo
echo "## ĐƯỜNG API thêm / bỏ (dòng @router.* trong diff)"
git diff "$base" origin/erp-v2 -- 'backend/app/modules/*controller*.py' | grep -E '^[+-]@router\.' | sed 's/^/  /' | head -80

echo
echo "## ROUTE màn v2 thêm / bỏ"
git diff "$base" origin/erp-v2 -- 'frontend-v2/src/modules/*/routes.tsx' 'frontend-v2/src/shared/constants/app-routes.ts' |
  grep -E "^[+-].*(path:|: '/)" | sed 's/^/  /' | head -60
