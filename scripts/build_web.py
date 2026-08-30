"""Render data/n100/kr.json into a self-contained web page: web/n100.html.

Visual system is inherited from the Android app (netflix-tier): the same dark
Netflix palette, Roboto + Noto Sans KR, phone-width column. Adds a per-row
score bar and an expandable 5-component breakdown.

Pure stdlib. Run: python scripts/build_web.py   (after build_n100.py)
"""

from __future__ import annotations

import json
import os
import sys

from build_data import ROOT

SRC = os.path.join(ROOT, "data", "n100", "kr.json")
OUT = os.path.join(ROOT, "web", "n100.html")

PAGE = r"""<meta charset="utf-8">
<title>N100 Korea</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Roboto:wght@400;500;700;900&display=swap">
<style>
:root{
  --bg:#0A0A0A;--surface:#141414;--pill:#171717;
  --divider:#1C1C1C;--sep:#2A2A2A;--sep-faint:#3A3A3A;
  --accent:#E50914;
  --t1:#F2F2F2;--t2:#8C8C8C;--t3:#7A7A7A;--tmut:#9A9A9A;--tmut2:#B0B0B0;
  --rank-mut:#4A4A4A;--maxw:460px;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--t1);
  font-family:Roboto,"Noto Sans KR",system-ui,-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.device{max-width:var(--maxw);margin:0 auto;min-height:100vh;
  border-left:1px solid var(--divider);border-right:1px solid var(--divider);
  padding:0 20px 44px}
@media (max-width:480px){.device{border:0;padding:0 16px 44px}}
header{display:flex;align-items:center;justify-content:space-between;
  padding:16px 0 10px;position:sticky;top:0;background:var(--bg);z-index:5}
.brand{display:flex;align-items:center;gap:9px;font-size:20px;font-weight:700;letter-spacing:-.3px}
.brand .bar{width:3px;height:18px;background:var(--accent);border-radius:2px}
.brand .sub{color:var(--t3);font-weight:500;font-size:15px}
.lang{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--sep-faint)}
.lang button{background:none;border:0;padding:2px 3px;font:inherit;font-size:12px;
  color:var(--tmut);cursor:pointer}
.lang button[aria-pressed="true"]{color:var(--t1);font-weight:700}
.disclaimer{font-size:11px;line-height:1.55;color:var(--t3);
  border-left:2px solid var(--accent);padding:6px 0 6px 10px;margin:2px 0 14px}
.pills{display:flex;gap:7px;padding:0 0 12px}
.pills button{background:var(--pill);border:0;border-radius:8px;
  padding:7px 15px;font:inherit;font-size:13px;font-weight:600;color:var(--tmut);cursor:pointer}
.pills button[aria-pressed="true"]{background:var(--accent);color:#fff}
.meta{font-size:11.5px;color:var(--t3);letter-spacing:.2px;padding-bottom:4px}
ol.rows{list-style:none;margin:0;padding:0}
.row{border-top:1px solid var(--divider);padding:12px 0;cursor:pointer}
.row:first-child{border-top:0}
.row-main{display:flex;align-items:center;gap:15px}
.rank{width:38px;flex:none;font-size:27px;font-weight:900;line-height:1;
  letter-spacing:-1.5px;font-variant-numeric:tabular-nums;color:var(--rank-mut)}
.row.top3 .rank{color:var(--accent)}
.row-body{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}
.row-title{font-size:15px;font-weight:600;line-height:1.3;letter-spacing:-.1px;
  display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.type{font-size:9px;font-weight:700;letter-spacing:.7px;color:var(--t3);
  border:1px solid var(--sep);border-radius:3px;padding:1px 4px;flex:none}
.row-sub{font-size:12px;color:var(--t2);letter-spacing:.1px}
.delta.up{color:var(--accent)}
.delta.down{color:var(--tmut)}
.delta.flat{color:var(--t3)}
.score-bar{height:3px;background:var(--divider);border-radius:2px;overflow:hidden;margin-top:2px}
.score-bar i{display:block;height:100%;background:var(--accent);width:0;transition:width .6s ease}
.score{flex:none;font-size:14px;font-weight:700;font-variant-numeric:tabular-nums;
  min-width:40px;text-align:right}
.row-detail{padding:13px 0 3px 53px;display:grid;gap:7px}
.row-detail[hidden]{display:none}
.comp{display:grid;grid-template-columns:52px 1fr 26px;align-items:center;gap:9px;
  font-size:11px;color:var(--t2)}
.comp .meter{height:5px;background:var(--divider);border-radius:3px;overflow:hidden}
.comp .meter i{display:block;height:100%;background:var(--accent)}
.comp .v{text-align:right;font-variant-numeric:tabular-nums;color:var(--tmut2)}
.detail-foot{font-size:10.5px;color:var(--t3);line-height:1.65;padding-top:3px}
footer{margin-top:22px;padding-top:14px;border-top:1px solid var(--divider);
  font-size:10.5px;color:var(--t3);line-height:1.7}
footer a{color:var(--tmut)}
.row:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
<main class="device">
  <header>
    <div class="brand"><span class="bar"></span>N100<span class="sub">Korea</span></div>
    <div class="lang">
      <button data-lang="en" aria-pressed="false">EN</button><span>/</span><button data-lang="ko" aria-pressed="true">한국어</button>
    </div>
  </header>
  <p class="disclaimer" id="disclaimer"></p>
  <nav class="pills" id="pills">
    <button data-list="all" aria-pressed="true"></button>
    <button data-list="films" aria-pressed="false"></button>
    <button data-list="tv" aria-pressed="false"></button>
  </nav>
  <p class="meta" id="meta"></p>
  <ol class="rows" id="rows"></ol>
  <footer id="foot"></footer>
</main>

<script id="n100-data" type="application/json">__N100_DATA__</script>
<script>
(function(){
  var DATA = JSON.parse(document.getElementById("n100-data").textContent);
  var W = DATA.weights;
  var STR = {
    en: {
      sub: "Korea",
      disclaimer: "Not an official Netflix ranking. N100 is our own estimate, built by carrying "
        + DATA.window.weeks + " weeks of Netflix's public weekly TOP 10 forward and scoring what charted.",
      lists: {all:"All", films:"Films", tv:"Series"},
      types: {film:"FILM", tv:"SERIES"},
      meta: function(){ return "Week of " + fmtWeek(DATA.referenceWeek) + " · " + DATA.window.weeks
        + "-week window · pool " + DATA.pool.films + " films · " + DATA.pool.tv + " series"; },
      weeks: function(n){ return n + (n===1?" week charted":" weeks charted"); },
      peak: function(n){ return "peak #" + n; },
      newEntry: "NEW", reentry: "re-entry", held: "held",
      comps: {rank:"Rank", recency:"Recency", longevity:"Longevity", momentum:"Momentum", global:"Global"},
      foot: function(e){
        return "latest #" + e.lastRank + (e.prevRank!=null? " (prev #"+e.prevRank+")":"")
          + " · charting in " + e.countriesCharting + "/10 tracked countries"
          + " · first seen in window " + e.firstSeenInWindow;
      },
      credits: "formula " + DATA.formulaVersion + " · Rank " + pct(W.rank) + " · Recency " + pct(W.recency)
        + " · Longevity " + pct(W.longevity) + " · Momentum " + pct(W.momentum) + " · Global " + pct(W.global)
        + " · source: Netflix Tudum public TOP 10"
    },
    ko: {
      sub: "대한민국",
      disclaimer: "넷플릭스 공식 순위 아님. 공개 주간 TOP 10을 최근 "
        + DATA.window.weeks + "주 누적해 N100이 자체 산정한 실험 순위입니다.",
      lists: {all:"전체", films:"영화", tv:"시리즈"},
      types: {film:"영화", tv:"시리즈"},
      meta: function(){ return DATA.referenceWeek + " 기준 · 최근 " + DATA.window.weeks
        + "주 · 후보 영화 " + DATA.pool.films + " · 시리즈 " + DATA.pool.tv; },
      weeks: function(n){ return n + "주 차트인"; },
      peak: function(n){ return "최고 #" + n; },
      newEntry: "신규", reentry: "재진입", held: "유지",
      comps: {rank:"순위", recency:"최신", longevity:"장기", momentum:"상승", global:"글로벌"},
      foot: function(e){
        return "최근 #" + e.lastRank + (e.prevRank!=null? " (지난주 #"+e.prevRank+")":"")
          + " · " + e.countriesCharting + "/10개국 차트인"
          + " · 윈도우 첫 등장 " + e.firstSeenInWindow;
      },
      credits: "공식 " + DATA.formulaVersion + " · 순위 " + pct(W.rank) + " · 최신 " + pct(W.recency)
        + " · 장기 " + pct(W.longevity) + " · 상승 " + pct(W.momentum) + " · 글로벌 " + pct(W.global)
        + " · 출처: Netflix Tudum 공개 TOP 10"
    }
  };
  var MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  function fmtWeek(iso){ var p=iso.split("-"); return MONTHS[(+p[1])-1]+" "+(+p[2])+", "+p[0]; }
  function pct(x){ return Math.round(x*100)+"%"; }

  var state = {lang:"ko", list:"all"};
  try {
    var s = localStorage.getItem("n100");
    if (s){ var j = JSON.parse(s); if (j.lang) state.lang=j.lang; if (j.list) state.list=j.list; }
  } catch(e){}
  function persist(){ try { localStorage.setItem("n100", JSON.stringify(state)); } catch(e){} }

  var rowsEl = document.getElementById("rows");
  var open = {};  // rank -> bool, per list

  function deltaTag(e, t){
    if (e.prevRank == null) {
      return e.weeksCharted === 1
        ? '<span class="delta up">'+t.newEntry+'</span>'
        : '<span class="delta flat">'+t.reentry+'</span>';
    }
    if (e.delta > 0) return '<span class="delta up">▲'+e.delta+'</span>';
    if (e.delta < 0) return '<span class="delta down">▼'+(-e.delta)+'</span>';
    return '<span class="delta flat">'+t.held+'</span>';
  }

  function render(){
    var t = STR[state.lang];
    document.documentElement.lang = state.lang;
    document.querySelector(".brand .sub").textContent = t.sub;
    document.getElementById("disclaimer").textContent = t.disclaimer;
    document.getElementById("meta").textContent = t.meta();
    document.getElementById("foot").innerHTML = t.credits
      + ' · <a href="https://github.com/AIProject-k/netflix-tier-Data/blob/main/docs/n100-score-v1.md">'
      + (state.lang==="ko"?"공식 명세":"formula spec") + '</a>';

    document.querySelectorAll(".lang button").forEach(function(b){
      b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang));
    });
    document.querySelectorAll(".pills button").forEach(function(b){
      b.textContent = t.lists[b.dataset.list];
      b.setAttribute("aria-pressed", String(b.dataset.list === state.list));
    });

    var list = DATA[state.list];
    var order = ["rank","recency","longevity","momentum","global"];
    rowsEl.innerHTML = list.map(function(e){
      var isOpen = !!open[state.list + ":" + e.rank];
      var comps = order.map(function(k){
        return '<div class="comp"><span>'+t.comps[k]+'</span>'
          + '<div class="meter"><i style="width:'+Math.max(0,Math.min(100,e.components[k]))+'%"></i></div>'
          + '<span class="v">'+Math.round(e.components[k])+'</span></div>';
      }).join("");
      return '<li class="row'+(e.rank<=3?" top3":"")+'" data-rank="'+e.rank+'" tabindex="0"'
        + ' role="button" aria-expanded="'+isOpen+'">'
        + '<div class="row-main">'
        +   '<span class="rank">'+e.rank+'</span>'
        +   '<div class="row-body">'
        +     '<div class="row-title">'+esc(e.title)+' <span class="type">'+t.types[e.type]+'</span></div>'
        +     '<div class="row-sub">'+t.weeks(e.weeksCharted)+' · '+t.peak(e.peakRank)+' · '+deltaTag(e,t)+'</div>'
        +     '<div class="score-bar"><i data-w="'+e.score+'"></i></div>'
        +   '</div>'
        +   '<span class="score">'+e.score.toFixed(1)+'</span>'
        + '</div>'
        + '<div class="row-detail"'+(isOpen?"":" hidden")+'>'+comps
        +   '<div class="detail-foot">'+t.foot(e)+'</div>'
        + '</div>'
        + '</li>';
    }).join("");

    requestAnimationFrame(function(){
      rowsEl.querySelectorAll(".score-bar i").forEach(function(i){ i.style.width = i.dataset.w + "%"; });
    });
  }

  function esc(s){ return s.replace(/[&<>"]/g, function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }

  function toggleRow(li){
    var key = state.list + ":" + li.dataset.rank;
    open[key] = !open[key];
    var d = li.querySelector(".row-detail");
    d.hidden = !open[key];
    li.setAttribute("aria-expanded", String(open[key]));
  }

  rowsEl.addEventListener("click", function(ev){
    var li = ev.target.closest(".row"); if (li) toggleRow(li);
  });
  rowsEl.addEventListener("keydown", function(ev){
    if (ev.key !== "Enter" && ev.key !== " ") return;
    var li = ev.target.closest(".row"); if (!li) return;
    ev.preventDefault(); toggleRow(li);
  });
  document.getElementById("pills").addEventListener("click", function(ev){
    var b = ev.target.closest("button"); if (!b) return;
    state.list = b.dataset.list; persist(); render();
  });
  document.querySelector(".lang").addEventListener("click", function(ev){
    var b = ev.target.closest("button"); if (!b) return;
    state.lang = b.dataset.lang; persist(); render();
  });

  render();
})();
</script>
"""


def main() -> int:
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    embedded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    embedded = embedded.replace("</", "<\\/")  # keep </script> out of the inline block
    html = PAGE.replace("__N100_DATA__", embedded)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT}  ({len(html) // 1024} KB, {len(data['all'])}/{len(data['films'])}/{len(data['tv'])} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
