"""
宅食図鑑 静的サイト生成 - ページ描画層
data.py が読み込んだデータを受け取り、HTML文字列を組み立てる。
Batch1では既存ページの本文・タイトル・canonical・価格・キャンペーン内容は一切変更していない。
追加したのは共通ヘッダーへのOGP/favicon/基本JSON-LD、モバイル用テーブルCSSのみ。
"""
import base64
import json

from sitegen.data import SITE_NAME, SITE_DESC, SITE_URL, GSC_META, OPERATOR, LAST_VERIFIED_DATE, GA4_MEASUREMENT_ID, GTM_CONTAINER_ID


def esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _meal_form_note(meal_form):
    """meal_form内の（...）注記だけを抽出する（食欲喚起UI監査§11.4 提案2）。
    新規データは作らず、既存文字列の一部をそのまま使う。（...）が無ければNone。"""
    if not meal_form:
        return None
    start = meal_form.find("（")
    end = meal_form.find("）", start)
    if start == -1 or end == -1:
        return None
    note = meal_form[start + 1:end].strip()
    return note or None


def meal_form_categories(meal_form_text):
    """自由文のmeal_form（例:「冷凍（レンジで温めるだけ）」「冷凍 / 冷蔵」「日配（保冷ボックス）」）を
    診断ツールで絞り込める3カテゴリ（冷凍/冷蔵/日配）に正規化する。新規データ収集は不要
    （既存のmeal_formフィールドの文字列判定のみ）。PHASE2_IMPLEMENTATION_PLAN.md 8.1章。
    generators.pyから移設（VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md 項目5）。
    generators.pyがtemplatesをimportする構造のため、templates側から個別のtag文字列を
    同じ基準で判定する用途にも流用する（tags配列の要素をmeal_form_textの代わりに渡すだけで
    「保存方法を表す文字列か」を同一ロジックで判定できる）。"""
    text = meal_form_text or ""
    cats = []
    if "冷凍" in text:
        cats.append("冷凍")
    if "冷蔵" in text:
        cats.append("冷蔵")
    if "日配" in text:
        cats.append("日配")
    return cats


_STORAGE_ICONS = {
    "冷凍": '<svg class="tag-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1v14M2.5 4l11 8M13.5 4l-11 8"/></svg>',
    "冷蔵": '<svg class="tag-icon" viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="1" width="10" height="14" rx="1"/><path d="M3 6h10"/></svg>',
    "日配": '<svg class="tag-icon" viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="6" width="12" height="8" rx="1"/><path d="M2 6l6-4 6 4"/></svg>',
}


def _tag_html(t):
    """タグを「保存方法（冷凍/冷蔵/日配）」とそれ以外の特徴タグとで視覚的に区別する
    （VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md 項目5）。tags配列の文字列自体を
    meal_form_categories()の判定にかけるだけで、新規データ・新規スキーマは不要。
    保存方法カテゴリのみ最小限の単色ラインアイコンを前置する
    （VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目5）。"""
    cats = meal_form_categories(t)
    if cats:
        icon = _STORAGE_ICONS.get(cats[0], "")
        return f'<span class="tag tag-storage">{icon}{esc(t)}</span>'
    return f'<span class="tag">{esc(t)}</span>'


# ---------- デザインシステム（REDESIGN_UI_SPEC.md 2章〜16章）----------
# 既存データ・生成ロジックには一切触れず、UI層（CSS）のみをトークン体系へ再構築する。
# 値の数値・検証状態の意味は変更しない（confirmed/derived/pending/uncollected は
# 「情報の検証状態」であり優劣を表さない）。
_CSS = """/* ===== 宅食図鑑 デザインシステム（REDESIGN_UI_SPEC.md） ===== */
:root {
  /* ブランド（既存#e8552dを維持。再ブランディングしない） */
  --color-primary:#E8552D;
  --color-primary-hover:#C8431F;
  --color-primary-active:#A8371A;
  --color-primary-subtle:#FDEEE8;

  /* ニュートラル */
  --color-text:#1F2328;
  --color-text-muted:#5B6470;
  --color-text-faint:#8A9099;
  --color-border:#E7E2DB;
  --color-border-strong:#D3CCC1;
  --color-bg:#FAF7F5;
  --color-surface:#FFFFFF;
  --color-surface-alt:#FFF8F0;

  /* 検証状態（4状態のセマンティックカラー。意味は変更しない） */
  --status-confirmed-fg:#1E7E34; --status-confirmed-bg:#E6F4EA;
  --status-derived-fg:#1A56DB;   --status-derived-bg:#E8F0FE;
  --status-pending-fg:#B45300;   --status-pending-bg:#FFF4E5;
  --status-uncollected-fg:#6B7280; --status-uncollected-bg:#F1F1F1;

  /* 全項目確認済みバッジ（primaryの輪郭のみ。★・金色は使わない） */
  --badge-full-fg:var(--color-primary);
  --badge-full-border:var(--color-primary);

  /* タイポグラフィ（2.2節） */
  --font-family:"Hiragino Kaku Gothic ProN","Noto Sans JP","Yu Gothic",system-ui,sans-serif;
  --text-display:700 1.875rem/1.3 var(--font-family);
  --text-h1:700 1.5rem/1.35 var(--font-family);
  --text-h2:700 1.125rem/1.4 var(--font-family);
  --text-h3:600 1rem/1.4 var(--font-family);
  --text-body:400 1rem/1.7 var(--font-family);
  --text-body-sm:400 0.875rem/1.6 var(--font-family);
  --text-meta:400 0.8125rem/1.5 var(--font-family);
  --text-micro:600 0.6875rem/1.3 var(--font-family);
  --price-figure:700 1.375rem/1.2 var(--font-family);

  /* スペーシング（4px基準、2.3節） */
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px;
  --space-5:24px; --space-6:32px; --space-7:48px; --space-8:64px;

  /* 角丸・影・境界（2.4節） */
  --radius-sm:6px; --radius-md:10px; --radius-lg:16px;
  --shadow-sm:0 1px 2px rgba(31,35,40,.06);
  --shadow-md:0 4px 16px rgba(31,35,40,.08);
  --shadow-focus:0 0 0 3px rgba(232,85,45,.25);
  --border-default:1px solid var(--color-border);
  --border-strong:1px solid var(--color-border-strong);

  /* モーション（状態変化のみ。演出目的のアニメーションは使わない） */
  --transition-fast:120ms ease;
  --transition-base:180ms ease;
}

/* ---------- ベース ---------- */
* { box-sizing:border-box; margin:0; padding:0; }
html { -webkit-text-size-adjust:100%; }
body { font:var(--text-body); color:var(--color-text); background:var(--color-bg); line-height:1.7; }
.container { max-width:1000px; margin:0 auto; padding:0 var(--space-4); }
/* TOPページ本文専用の広いコンテナ（ヘッダー/フッターの.containerは1000pxのまま据え置き）。
   TOP_LAYOUT_IMPLEMENTATION_PLAN_2026_08_28.md H節「バリエーション2」採用。 */
.container-top { max-width:1200px; margin:0 auto; padding:0 var(--space-4); }
h1 { font:var(--text-h1); margin:var(--space-5) 0 var(--space-2); }
h2 { font:var(--text-h2); margin:var(--space-5) 0 var(--space-2); }
/* サイト最重要セクション（サービス一覧）の見出しのみに太罫線。h2全体には適用しない
   （VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目4）。 */
.heading-rule { display:inline-block; padding-bottom:var(--space-2); border-bottom:3px solid var(--color-border-strong); }
/* 「選び方のポイント」見出し専用：2本のオフセット罫線で単調な下線と差別化する
   （VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目6）。他の見出しには適用しない。 */
.heading-staggered { position:relative; display:inline-block; padding-bottom:10px; margin-bottom:var(--space-2); }
.heading-staggered::after {
  content:""; position:absolute; left:0; bottom:0;
  width:40px; height:3px; background:var(--color-primary); border-radius:2px;
}
.heading-staggered::before {
  content:""; position:absolute; left:48px; bottom:2px;
  width:14px; height:2px; background:var(--color-border-strong); border-radius:1px;
}
h3 { font:var(--text-h3); margin:var(--space-4) 0 var(--space-2); }
p { margin-bottom:var(--space-2); }
a { color:var(--color-primary); }
ul, ol { padding-left:1.4em; }

/* ---------- ヘッダー / ナビ（5章） ---------- */
header.site { background:var(--color-primary); color:#fff; padding:var(--space-3) 0; }
header.site .container { display:flex; align-items:center; justify-content:space-between; gap:var(--space-4); flex-wrap:wrap; }
header.site .site-logo { color:#fff; font-size:18px; font-weight:700; text-decoration:none; letter-spacing:.02em; }
nav.main { display:flex; align-items:center; gap:var(--space-4); flex-wrap:wrap; }
nav.main a { color:rgba(255,255,255,.9); text-decoration:none; font-size:14px; font-weight:600; padding:6px 2px; border-bottom:2px solid transparent; transition:border-color var(--transition-fast), color var(--transition-fast); }
nav.main a:hover { color:#fff; border-bottom-color:rgba(255,255,255,.85); }

/* ---------- カード / テーブル ---------- */
.card {
  background:var(--color-surface);
  border:var(--border-default);
  border-radius:var(--radius-md);
  padding:var(--space-4);
  margin:var(--space-3) 0;
  box-shadow:var(--shadow-sm);
  overflow-x:auto;
}
/* 詳細ページの脇役カード（基本情報・初回キャンペーン）のみに付与し、主役カード
  （こんな方におすすめ＝.panel-accent）を相対的に際立たせる（VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md 項目6）。
   .card自体は変更せず、新規トークンも追加しない。 */
.card-quiet { box-shadow:none; background:transparent; border-color:var(--color-border); }
/* TOP「このサイトのこだわり」専用：脱カード化で唯一の色面パネル扱いにする
   （VISUAL_EXPRESSION_ANTI_GENERIC_AUDIT_2026_08_28.md P1）。他セクションには適用しない。 */
.section-flat {
  background:var(--color-surface-alt);
  border:none;
  border-radius:var(--radius-sm);
  box-shadow:none;
  padding:var(--space-4) var(--space-5);
  margin:0 0 var(--space-4);
}
.section-flat h2 { margin-top:0; }
.panel-accent { background:var(--color-surface-alt); border:var(--border-default); }
/* TOP・campaigns.html共通のキャンペーン訴求：色帯＋大小非対称化
   （VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目3/3b）。box-shadowは追加しない。 */
.campaign-pick { background:var(--color-primary-subtle); border:none; border-radius:var(--radius-md); box-shadow:none; padding:var(--space-5); margin:var(--space-3) 0; }
/* P1-1：TOPのキャンペーン→こだわりの間を最広に。campaigns.htmlは.campaign-pick-featuredを使うため
   本ルールはTOP専用にスコープする（共有クラス.campaign-pickの既存marginは無変更）。 */
.container-top .campaign-pick { margin:0 0 var(--space-7); }
.campaign-pick-body { display:flex; gap:var(--space-5); align-items:stretch; }
.campaign-pick-main { flex:1 1 40%; background:var(--color-surface); border-radius:var(--radius-sm); padding:var(--space-4); display:flex; flex-direction:column; gap:4px; }
.campaign-pick-label { font:var(--text-meta); color:var(--color-primary); font-weight:700; letter-spacing:.05em; margin:0; }
.campaign-pick-name { font:var(--text-h3); margin:0; }
.campaign-pick-value { font:var(--price-figure); margin:0; }
.campaign-pick-list { flex:1 1 55%; margin:0; }
.campaign-pick-featured { background:var(--color-primary-subtle); border:none; border-radius:var(--radius-md); box-shadow:none; padding:var(--space-5); margin:var(--space-3) 0; }
table { width:100%; border-collapse:collapse; background:var(--color-surface); border-radius:var(--radius-md); overflow:hidden; font-size:14px; }
th, td { padding:var(--space-3) var(--space-3); text-align:left; border-bottom:1px solid var(--color-border); vertical-align:top; }
th { background:var(--color-surface-alt); font-weight:700; font-size:13px; white-space:nowrap; }
tr:last-child td { border-bottom:none; }
/* 比較一覧デスクトップ表のみ：価格セルの数字を右寄せにし縦の比較を容易にする
   （VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md 項目1）。ranking専用スコープで、
   比較ページ等の他の価格セルには影響しない。 */
#ranking-table td.td-price { text-align:right; }
/* sticky thead（VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md 項目2）は実装・実機検証済み。
   .cardのoverflow-x:autoによりoverflow-yも暗黙にautoとなり、position:stickyの基準が
   ビューポートではなく.card自身になるため実際には効かないことをPlaywrightで確認し、
   計画書の想定どおりCSSを撤回した。<thead>/<tbody>構造自体はマークアップの整理として維持する
   （build_ranking_pageのJSソートはparentNode.appendChildに依存しており明示的tbodyでも壊れない）。 */

/* ---------- ボタン（10章） ---------- */
.btn-primary {
  display:inline-flex; align-items:center; justify-content:center;
  background:var(--color-primary); color:#fff;
  padding:12px 24px; border-radius:var(--radius-sm);
  text-decoration:none; font-weight:700; font-size:14px;
  min-height:44px; border:none; cursor:pointer;
  transition:background var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast);
}
.btn-primary:hover { background:var(--color-primary-hover); transform:translateY(-1px); }
.btn-primary:active { background:var(--color-primary-active); transform:none; }
.btn-primary:focus-visible { outline:none; box-shadow:var(--shadow-focus); }
.btn-secondary {
  display:inline-flex; align-items:center; justify-content:center; flex-wrap:wrap;
  background:var(--color-surface); color:var(--color-text);
  border:1px solid var(--color-border-strong);
  padding:10px 20px; border-radius:var(--radius-sm);
  text-decoration:none; font-weight:700; font-size:14px;
  min-height:44px; cursor:pointer;
  transition:background var(--transition-fast), border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.btn-secondary:hover { background:var(--color-surface-alt); border-color:var(--color-border-strong); }
.btn-secondary:active { background:var(--color-border); }
.btn-secondary:focus-visible { outline:none; box-shadow:var(--shadow-focus); }
.btn-disabled {
  display:inline-flex; align-items:center;
  background:var(--status-uncollected-bg); color:var(--status-uncollected-fg);
  padding:10px 20px; border-radius:var(--radius-sm);
  font-size:13px; font-weight:700; min-height:44px;
}
.text-link { color:var(--color-primary); text-decoration:none; font-weight:700; }
.text-link:hover { text-decoration:underline; }

/* ---------- タグ / バッジ ---------- */
.tag {
  display:inline-block; background:var(--color-primary-subtle); color:var(--color-primary);
  padding:2px var(--space-3); border-radius:999px;
  font:var(--text-micro); letter-spacing:.02em; margin:2px 2px 2px 0;
}
/* 保存方法（冷凍/冷蔵/日配）タグをその他の特徴タグと視覚的に区別する
   （VISUAL_DESIGN_SYSTEM_IMPLEMENTATION_PLAN_2026_08_28.md 項目5）。新色は追加せず
   既存の--color-border-strong/--color-text-mutedのoutlineトーンのみ使用する。 */
.tag-storage { background:transparent; border:1px solid var(--color-border-strong); color:var(--color-text-muted); }
/* 保存方法タグの最小ラインアイコン。単色（currentColor継承）・16px以下・使用箇所はtag-storageのみに
   限定する（VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目5）。 */
.tag-icon { width:11px; height:11px; margin-right:3px; vertical-align:-1px; stroke:currentColor; fill:none; stroke-width:1.4; stroke-linecap:round; }
.vstatus {
  display:inline-flex; align-items:center; gap:3px;
  padding:2px 8px; border-radius:999px;
  font:var(--text-micro); letter-spacing:.02em; font-weight:700;
  white-space:nowrap; vertical-align:middle;
}
/* 確認済みのみ確認済み枠を足して強調し、未確認系はfont-weightを一段落として控えめに沈める
   （UI_DESIGN_PRINCIPLES.md 4.2.1「確認済みの値は強調・未確認の値は控えめに沈める」の徹底。
   色・記号・文言＝検証状態の意味は変更しない）。*/
.vstatus-confirmed { background:var(--status-confirmed-bg); color:var(--status-confirmed-fg); border:1px solid var(--status-confirmed-fg); }
.vstatus-derived { background:var(--status-derived-bg); color:var(--status-derived-fg); font-weight:600; }
.vstatus-pending { background:var(--status-pending-bg); color:var(--status-pending-fg); font-weight:600; }
.vstatus-uncollected { background:var(--status-uncollected-bg); color:var(--status-uncollected-fg); font-weight:600; }
.vfull-badge {
  display:inline-block; padding:2px 8px;
  border:1px solid var(--badge-full-border); color:var(--badge-full-fg);
  border-radius:999px; font:var(--text-micro); letter-spacing:.02em; font-weight:700;
  white-space:nowrap; margin-left:4px; vertical-align:middle;
}
.aff-note { flex-basis:100%; text-align:center; font-size:11px; opacity:.8; font-weight:400; margin-top:2px; }

/* ---------- 価格表示（4章・9章） ---------- */
.price-figure { font:var(--price-figure); color:var(--color-text); white-space:nowrap; font-variant-numeric:tabular-nums; }
.price-unit { font-size:13px; font-weight:400; color:var(--color-text-muted); margin-left:2px; }
.price-meta { font:var(--text-meta); color:var(--color-text-faint); }
/* P1-1：検証カバレッジ1行版（trust_line()）。見た目は.price-meta継承のまま、一覧の直前に
   最広の下marginを置いてサービス一覧を視覚の主役として際立たせる（既存トークンのみ使用）。
   P2-1：この余白はTOP（container-top）専用に限定。ranking（container内）のtrust-lineは
   デフォルトの<p> marginに戻し、比較表→検証1行→選び方の流れの過大な隙間（89px）を解消する。 */
.container-top .trust-line { margin:0 0 var(--space-7); }
/* 行の高さの統一は.svc-card-price-row{min-height}側で担保済み（285行目付近）のため、
   ここでは--price-figureに近づける必要はない。むしろ実画面監査（REAL_BROWSER_UI_AUDIT_2026_08_28.md）で
   価格数字と同じ視覚重量だと「取得エラー」に誤読されることが判明したため、
   UI_DESIGN_PRINCIPLES.md 4.2.1「未確認の値は控えめに沈める」により忠実に、
   フォントサイズ・太さを価格より明確に下げる（色による区別・値そのものの非捏造は維持）。 */
.price-unconfirmed { color:var(--color-text-muted); font-size:0.95rem; font-weight:400; line-height:1.2; }
/* 長い基準ラベル（例：ツクリオ「1人前あたり換算価格（当サイト算出）」）がモバイル幅で
   横に突き抜けないよう、折り返しを許可し丸角を控えめにする（15章：横スクロール禁止方針）。 */
.price-basis { font-size:12px; font-weight:600; color:var(--color-primary); background:var(--color-surface-alt); border:1px solid var(--color-border); border-radius:10px; padding:1px 8px; white-space:normal; max-width:100%; line-height:1.4; }
/* 初回/お試し価格は「継続利用時の実質価格ではない」ため、通常の.price-basisより
   高コントラストな塗りつぶしで区別する（COMPETITOR_UX_FUNNEL_AUDIT_2026_08_28.md：
   通常価格と初回/お試し価格が同一の視覚重量で並び、ユーザーが誤読する問題への対処）。
   --color-primaryの塗り潰しは.checks label:has(input:checked)と同じトーンを再利用し、
   新規の色トークンは追加しない。--status-*系（確認状態バッジ）とは別軸のため使わない。 */
.price-basis-onetime { background:var(--color-primary); color:#fff; border-color:var(--color-primary); font-weight:700; }
.source-link { font:var(--text-meta); color:var(--color-text-faint); }
.source-link:hover { color:var(--color-primary); }
.price-points-table { width:100%; border-collapse:collapse; margin-top:12px; }
.price-points-table th, .price-points-table td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--color-border); font-size:13px; vertical-align:top; }
.price-points-table th { font-size:12px; color:var(--color-text-muted); font-weight:600; white-space:nowrap; }

/* ---------- Hero（7章） ---------- */
.hero {
  background:var(--color-surface-alt);
  border:var(--border-default);
  border-radius:var(--radius-lg);
  /* TOP再設計：ページ内で最も重要なゾーンであることを影の強さで示す（E節「Tier2」）。
     縦方向の余白はpadding/marginを1段階詰め、ファーストビューでのサービス到達を早める。 */
  box-shadow:var(--shadow-md);
  padding:var(--space-5) var(--space-6);
  /* P1-1：縦リズムを下margin主体に統一。hero→目的の間は広めに取り、ファーストビューの完結感を出す。 */
  margin:0 0 var(--space-6);
}
.hero h1 { font:var(--text-display); margin:0 0 var(--space-3); }
.hero-lead { font:var(--text-body); color:var(--color-text-muted); margin:0 0 var(--space-4); max-width:44em; }
.hero-actions { display:flex; gap:var(--space-4); align-items:center; flex-wrap:wrap; }
.hero-sub-cta { font-weight:700; color:var(--color-primary); text-decoration:none; font-size:15px; }
.hero-sub-cta:hover { text-decoration:underline; }

/* ---------- ページ見出し（詳細ページ 12章） ---------- */
.page-head { display:flex; align-items:baseline; justify-content:space-between; gap:var(--space-2); flex-wrap:wrap; margin:var(--space-5) 0 var(--space-2); }
.page-head h1 { margin:0; }
.page-head-meta { font:var(--text-meta); color:var(--color-text-faint); white-space:nowrap; }

/* ---------- 目的別チップ（7章） ---------- */
.purpose-section { margin:var(--space-5) 0; }
.purpose-section h2 { margin-top:0; }
/* P2-0：目的で探すのモバイル折りたたみ。641px以上はsummary非表示でopen属性維持の常時展開
   （従来の色帯ゾーン）、640px以下はsummaryタップで開閉（初期閉はインラインscriptで行う）。
   既存のdetailsパターン（.svc-more/.faq-item）と同じ文法。新規トークンなし。 */
.purpose-collapse > summary { cursor:pointer; list-style:none; }
.purpose-collapse > summary::-webkit-details-marker { display:none; }
.purpose-collapse > summary::after { content:" ▾"; }
.purpose-collapse[open] > summary::after { content:" ▴"; }
.purpose-collapse > summary h2 { display:inline; }
@media (min-width:641px) {
  .purpose-collapse > summary { display:none; }
}
/* TOP専用：検証カバレッジより前段の「入口」。P2-2で色帯（primary-subtle）を撤去し、
   ページ地色（--color-bg）に透明化して、hero(A)とキャンペーン(B)の色帯反復を解消する。
   選択UIとしての役割は配下のチップ（--color-primary-subtle背景）が自己完結しており、
   セクション色帯なしでも視認・操作可能。新規色は追加しない（既存トークンのみ）。 */
.purpose-section-top { background:var(--color-bg); padding:var(--space-4) 0 0; margin:0 0 var(--space-4); }
.purpose-section-top h2 { font:var(--text-h1); }
.purpose-groups { display:flex; flex-wrap:wrap; gap:var(--space-4); }
.purpose-group { flex:1 1 180px; min-width:180px; }
.purpose-chip {
  display:inline-flex; align-items:center;
  background:var(--color-primary-subtle); color:var(--color-primary);
  border:1px solid var(--color-primary);
  border-radius:999px; padding:6px 14px;
  font-size:13px; font-weight:700; letter-spacing:.02em;
}
.purpose-services { display:flex; flex-wrap:wrap; gap:4px 8px; margin-top:var(--space-2); }
.purpose-services a {
  font:var(--text-body-sm); color:var(--color-text);
  text-decoration:none; border-bottom:1px solid var(--color-border-strong);
  padding:2px 0; line-height:1.5;
}
.purpose-services a:hover { color:var(--color-primary); border-bottom-color:var(--color-primary); }
/* TOP専用：詳細ページ直リンクの隣に、TOP自身の一覧内カードへのページ内アンカーを追加
   （TOP_PROGRESSIVE_DISCLOSURE_FINAL_AUDIT_2026_08_28.md）。既存リンクは維持し選択肢を1つ追加するのみ。 */
.purpose-service-link { display:inline-flex; align-items:center; gap:1px; }
/* TOP_P2_IMPROVEMENT_PLAN_2026_08_28.md 1b：発見性向上のため、文字装飾ではなく
   独立した小さなチップ（背景+角丸）にする。色・文言・遷移先は無変更。 */
.purpose-services a.purpose-anchor {
  display:inline-flex; align-items:center; justify-content:center;
  font-size:11px; color:var(--color-primary); text-decoration:none;
  /* TOP_P2_IMPROVEMENT_IMPLEMENTATION_2026_08_28.md 追記：親セクション
     (.purpose-section-top)の背景と同一トークンだったため溶け込んでいた。
     既存の白系トークンに変更しコントラストを確保する（新規色は追加しない）。 */
  background:var(--color-surface); border-radius:999px;
  border-bottom:none; min-width:20px; height:20px; padding:0 5px; margin-left:2px; line-height:1.5;
}
.purpose-services a.purpose-anchor:hover { background:var(--color-primary); color:#fff; }

/* ---------- Trust Panel（8章） ---------- */
.trust-panel {
  background:var(--color-surface);
  border:var(--border-default);
  border-radius:var(--radius-lg);
  padding:var(--space-5);
  margin:var(--space-5) 0;
}
.trust-panel h2 { margin-top:0; }
.trust-stats { display:flex; gap:var(--space-6); flex-wrap:wrap; margin:var(--space-4) 0 var(--space-3); }
.trust-stat { display:flex; flex-direction:column; gap:2px; }
.trust-figure { font:var(--price-figure); font-size:2rem; line-height:1.1; }
.trust-label { font:var(--text-meta); color:var(--color-text-faint); }
/* Hero専用の数字強調。.trust-figureとは独立させ、trust_panel()の統計数値には影響させない
   （VISUAL_EXPRESSION_ANTI_GENERIC_AUDIT_2026_08_28.md P1「見出し数字の書体コントラスト強化」）。 */
.hero-figure { font:var(--price-figure); font-size:2.75rem; line-height:1.05; letter-spacing:-0.01em; }
.trust-bar { display:flex; height:12px; border-radius:999px; overflow:hidden; background:var(--color-border); margin:var(--space-3) 0; }
.trust-bar > span { height:100%; min-width:2px; }
.trust-bar-confirmed { background:var(--status-confirmed-fg); }
.trust-bar-derived { background:var(--status-derived-fg); }
.trust-bar-pending { background:var(--status-pending-fg); }
.trust-bar-uncollected { background:var(--status-uncollected-fg); }
.trust-legend { display:flex; gap:var(--space-3); flex-wrap:wrap; align-items:center; font:var(--text-meta); color:var(--color-text-muted); }
.trust-legend-item { white-space:nowrap; }
.trust-link { display:inline-block; margin-top:var(--space-3); font-weight:700; }
.trust-note { font:var(--text-meta); color:var(--color-text-faint); margin-top:var(--space-3); }

/* ---------- Service Card（9章） ---------- */
.svc-card {
  background:var(--color-surface);
  border:var(--border-default);
  border-radius:var(--radius-md);
  padding:var(--space-4);
  margin:var(--space-3) 0;
  box-shadow:var(--shadow-sm);
  display:flex; flex-direction:column; gap:var(--space-2);
}
.svc-card-header { display:flex; align-items:flex-start; justify-content:space-between; gap:var(--space-2); flex-wrap:wrap; }
.svc-card-name { font:var(--text-h3); margin:0; }
.svc-card-name a { color:var(--color-text); text-decoration:none; }
.svc-card-name a:hover { color:var(--color-primary); }
.svc-card-tags { display:flex; flex-wrap:wrap; gap:2px; }
/* 確認済み価格（price-figure）と未確認価格（price-unconfirmed）で行の高さが
   ばらつかないよう最小高さを揃える（15社の価格表示リズム統一）。 */
.svc-card-price-row { display:flex; align-items:center; gap:var(--space-2); flex-wrap:wrap; min-height:1.7rem; }
.svc-card-meta { font:var(--text-meta); color:var(--color-text-faint); }
/* ラベル+値のミニ項目（モバイルカードで文章の羅列を避け、拾い読みできるようにする） */
.svc-card-specs { display:grid; grid-template-columns:1fr 1fr; gap:var(--space-2) var(--space-3); }
.svc-spec { display:flex; flex-direction:column; gap:2px; min-width:0; }
.svc-spec-wide { grid-column:1 / -1; }
.svc-spec-label { font:var(--text-meta); color:var(--color-text-faint); }
.svc-spec-value { font:var(--text-body-sm); font-weight:600; color:var(--color-text); }
.svc-card-footer { display:flex; gap:var(--space-2); flex-wrap:wrap; margin-top:var(--space-2); }
.service-list-section { margin:0 0 var(--space-6); }
.service-list-section h2 { margin-top:0; }
/* TOP専用：900px以上で3列・640-899pxで2列、640px未満は従来の縦積み1列のまま（B節・C節）。
   PCでは.svc-card自体の縦margin(--space-3)をgapに置き換えて重複を避ける。 */
.service-grid .svc-card { margin:var(--space-3) 0; }
@media (min-width:900px) {
  .service-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:var(--space-4) var(--space-6); }
  .service-grid .svc-card { margin:0; }
}
@media (min-width:640px) and (max-width:899px) {
  .service-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:var(--space-4) var(--space-5); }
  .service-grid .svc-card { margin:0; }
}
/* TOP専用カード：白い箱（背景・枠線・角丸・影）を外し、上罫線1本で区切る一覧形式にする
   （VERIFICATION_COVERAGE_AND_GRID_IMPLEMENTATION_PLAN_2026_08_28.md B1）。
   中身（名前/価格＋✓バッジ/向いている人/タグ3件/CTA2種）は完全に無変更。
   全カード共通の除去方向のみで、サービス間の視覚的ウェイト差は作らない。 */
.svc-card-top {
  gap:var(--space-2);
  background:transparent; border:none; border-radius:0; box-shadow:none;
  border-top:1px solid var(--color-border); padding:var(--space-4) 0;
}
/* TOP専用CTA行：公式サイトを確認をtext-link化した結果、A8.net経由の長いラベルが
   隣の主CTA「詳しく見る」ボタンの幅を圧迫して折り返す事象が実機で判明したため、
   主CTAは常に内容幅を維持し、長いtext-linkの方だけ折り返すようにする（F節）。 */
.svc-card-top .svc-card-footer .btn-primary { flex:0 0 auto; }
/* TOP段階開示（TOP_PROGRESSIVE_DISCLOSURE_FINAL_AUDIT_2026_08_28.md）。
   5・6枚目はPC（900px以上、3列gridが有効になる幅）でのみ常時表示し、
   900px未満（モバイル・タブレット2列時）は<details>側の展開に含める。 */
.svc-extra-initial { display:none; }
@media (min-width:900px) {
  .svc-extra-initial { display:flex; }
}
/* 「残りを見る」：既存のFAQアコーディオン（.faq-item）と同じくJS不要のネイティブdetails。
   .btn-primary（実CTA）とは明確に見た目を分け、押し売り感を出さない中立トーンにする。
   新しい色トークンは追加せず既存の--color-primary/--color-border-strongのみ使用。 */
.svc-more { margin:var(--space-4) 0; border:none; }
.svc-more summary {
  cursor:pointer; list-style:none; text-align:center;
  padding:var(--space-3); font-weight:700; color:var(--color-primary);
  border:1px solid var(--color-border-strong); border-radius:var(--radius-sm);
}
.svc-more summary::-webkit-details-marker { display:none; }
.svc-more summary::after { content:" ▾"; }
.svc-more[open] summary::after { content:" ▴"; }
.svc-more[open] summary { margin-bottom:var(--space-4); }
.svc-more .service-grid { margin:0; }

/* ---------- 選択チップ（診断・フィルタ、12章・14章） ---------- */
.checks { display:flex; flex-wrap:wrap; gap:var(--space-2); }
.checks label {
  display:inline-flex; align-items:center; gap:6px;
  border:1px solid var(--color-border-strong);
  border-radius:999px; padding:10px 16px;
  background:var(--color-surface);
  font-size:14px; font-weight:600; color:var(--color-text);
  cursor:pointer; min-height:44px;
  transition:background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), box-shadow var(--transition-fast);
  user-select:none;
}
.checks label:hover { border-color:var(--color-primary); background:var(--color-primary-subtle); }
.checks label:has(input:checked) { background:var(--color-primary); border-color:var(--color-primary); color:#fff; }
.checks label:has(input:checked)::after { content:"✓"; margin-left:2px; font-weight:700; }
.checks input[type=checkbox] { position:absolute; opacity:0; width:1px; height:1px; pointer-events:none; }
.checks label:has(input:focus-visible) { outline:none; box-shadow:var(--shadow-focus); }

/* ---------- 診断（14章） ---------- */
.diag-summary { font:var(--text-body-sm); color:var(--color-text-muted); margin-top:var(--space-3); font-weight:600; }
.diag-result-note { font:var(--text-meta); color:var(--color-text-faint); margin-top:var(--space-2); }

/* ---------- FAQアコーディオン（12章） ---------- */
.faq-item { border:var(--border-default); border-radius:var(--radius-sm); margin:var(--space-2) 0; background:var(--color-surface); }
.faq-item summary {
  cursor:pointer; padding:var(--space-3) var(--space-5) var(--space-3) var(--space-4);
  font-weight:700; font-size:15px; list-style:none; position:relative;
  transition:color var(--transition-fast);
}
.faq-item summary::-webkit-details-marker { display:none; }
.faq-item summary:hover { color:var(--color-primary); }
.faq-item summary::after {
  content:"＋"; position:absolute; right:var(--space-3); top:50%; transform:translateY(-50%);
  color:var(--color-primary); font-weight:700; font-size:16px;
  transition:transform var(--transition-fast);
}
.faq-item[open] summary::after { content:"－"; }
.faq-body { padding:0 var(--space-4) var(--space-3); font:var(--text-body-sm); color:var(--color-text-muted); }
.faq-body p { margin-bottom:0; }

/* ---------- 価格根拠アコーディオン（P2-7） ---------- */
/* .faq-item はカード風の重い装飾のため、価格テーブル直下の注記1行には過剰。
   .svc-moreと同じくJS不要のネイティブdetailsのみを使う軽量版。 */
.price-notes { margin:var(--space-2) 0 0; border:none; }
.price-notes summary { cursor:pointer; list-style:none; font:var(--text-meta); color:var(--color-text-muted); }
.price-notes summary::-webkit-details-marker { display:none; }
.price-notes summary::after { content:" ▾"; }
.price-notes[open] summary::after { content:" ▴"; }
.price-notes p.price-meta { margin-top:var(--space-2); }

/* ---------- pros/cons / feature-list ---------- */
.pros-cons { display:flex; gap:var(--space-4); flex-wrap:wrap; }
.pros-cons > div { flex:1; min-width:240px; }
/* 良い点[0]を「体験の一言」として視覚的に区別する（食欲喚起UI監査§11.4 提案3）。
   後段の「良い点・気になる点」箇条書きと同じ文言を再掲するため、重複感が強くならないよう
   罫線と太字だけで区別し、新規の装飾要素は追加しない。 */
.pros-highlight { border-left:3px solid var(--color-primary); padding:2px var(--space-3); margin:var(--space-3) 0; font:var(--text-body); font-weight:600; color:var(--color-text); }
.pros li, .cons li { margin-left:20px; font-size:14px; }
ul.feature-list li, ol.feature-list li { margin-left:20px; font-size:14px; }

/* ---------- フッター ---------- */
.updated { color:var(--color-text-muted); font-size:12px; margin-top:var(--space-5); border-top:1px solid var(--color-border); padding-top:var(--space-3); }
footer.site { text-align:center; padding:var(--space-5) var(--space-4); color:var(--color-text-muted); font-size:12px; margin-top:var(--space-6); }
footer.site .container p { margin-bottom:6px; }
.footer-nav a { color:var(--color-text-faint); margin:0 8px; text-decoration:none; white-space:nowrap; }
.footer-nav a:hover { color:var(--color-text-muted); text-decoration:underline; }

/* ---------- モバイル（640px以下、15章・16章） ---------- */
.mobile-scroll-hint { display:none; }
.ranking-mobile { display:none; }
@media (max-width:640px) {
  .container { padding:0 var(--space-3); }
  /* 多列テーブル（verification・比較）は横スクロール方式を維持（9.4節・15.5節） */
  table { min-width:520px; }
  .mobile-scroll-hint { display:block; font-size:12px; color:var(--color-text-muted); margin:4px 0; }
  /* 比較一覧：デスクトップ=テーブル / モバイル=Service Card縦積み（9.4節） */
  .ranking-desktop { display:none; }
  .ranking-mobile { display:block; }
  /* Hero（15.1節）。TOP再設計：モバイルも縦余白を1段階詰めてサービス到達を早める。 */
  .hero { padding:var(--space-4); margin:0 0 var(--space-4); }
  .hero h1 { font-size:1.5rem; }
  .hero-figure { font-size:2rem; }
  .hero-actions { flex-direction:column; align-items:stretch; }
  .hero-actions .btn-primary { width:100%; }
  /* キャンペーンPICK UP（VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目3）：
     狭幅では横並びを維持せず縦積みにする。 */
  .campaign-pick-body { flex-direction:column; }
  /* ナビ（5章） */
  nav.main { gap:var(--space-2); }
  nav.main a { font-size:13px; padding:4px 2px; }
  /* Trust Panel（15.5節・16章：モバイルは3数値を縦積み3行に。通常のtrust-panelは無変更） */
  .trust-stats { flex-direction:column; gap:var(--space-3); }
  .trust-stat { flex-direction:row; align-items:baseline; gap:6px; }
  .trust-figure { font-size:1.4rem; }
  /* 目的別チップ（15.1節） */
  .purpose-groups { gap:var(--space-3); }
  .purpose-group { flex:1 1 45%; min-width:0; }
  /* TOP専用：目的で探すを検証カバレッジより上位の選択UIとして扱うため、
     モバイルでも5カテゴリを2列gridで3行に収め、縦の占有を圧縮する（C節）。
     カテゴリ・リンク・遷移先は無変更、表示密度のみ変更。
     2列化で個々の列幅が狭まりサービス名の折り返しが増えて逆に高さが伸びたため
     （実測）、パディング・行間・リンクのフォントサイズも合わせて詰める。 */
  .purpose-section-top { padding:var(--space-3) 0 0; margin:0 0 var(--space-3); }
  /* P1-1：モバイルは縦が長いため、デスクトップの下marginを1段階圧縮する。 */
  .container-top .trust-line { margin:0 0 var(--space-5); }
  .service-list-section { margin:0 0 var(--space-4); }
  .container-top .campaign-pick { margin:0 0 var(--space-5); }
  .purpose-section-top .purpose-groups { display:grid; grid-template-columns:1fr 1fr; gap:var(--space-2) var(--space-3); }
  .purpose-section-top .purpose-group { min-width:0; }
  .purpose-section-top .purpose-services { gap:2px 6px; margin-top:4px; }
  .purpose-section-top .purpose-services a { font-size:12.5px; line-height:1.4; }
  /* Service CardのCTA */
  .svc-card-footer .btn-primary, .svc-card-footer .btn-secondary { flex:1; justify-content:center; }
}
@media (max-width:400px) {
  .purpose-group { flex:1 1 100%; }
}
"""


def yen(v):
    if v is None:
        return "公式確認中"
    return f"{v:,}円"


# ---------- フィールド単位の確認状態（verification status）----------
# 価格はpricing.price_points[]単位でstatusを保持し、_pricing_statusがdisplay価格の
# statusを採用する（plan_notesの自由文トークン判定からは脱却済み）。
# 送料・キャンペーンは従来通り shipping_fee/notes / requires_verification から導出する。

_VSTATUS_LABEL = {
    "confirmed": "確認済み",
    "derived": "算出値",
    "pending": "確認中",
    "uncollected": "未収集",
}

# 色覚に依存しない識別用の記号（REDESIGN_UI_SPEC.md 11章「表示の見方」）。
# 検証状態の意味は変更しない（優劣を表す記号ではない）。
_VSTATUS_SYMBOL = {
    "confirmed": "✓",
    "derived": "≈",
    "pending": "…",
    "uncollected": "—",
}


def vstatus_badge(status):
    label = _VSTATUS_LABEL.get(status, "確認中")
    symbol = _VSTATUS_SYMBOL.get(status, "…")
    return (f'<span class="vstatus vstatus-{status}">'
            f'<span class="vstatus-symbol" aria-hidden="true">{symbol}</span>{esc(label)}</span>')


def mobile_scroll_hint():
    """横幅の広い比較テーブルの直前に置く、モバイルでの横スクロール案内。
    .mobile-scroll-hintはCSS側で640px以下でのみ表示される（デスクトップでは非表示）。
    PHASE4_FINAL_DECISION.md 3章・PHASE4_COMPETITIVE_REAUDIT.md 1章（silver-choice.jp実測）。"""
    return '<p class="mobile-scroll-hint">◀ 表がはみ出す場合は横にスクロールしてご覧ください ▶</p>'


def trust_panel(coverage, num_services, link_to_dashboard=True):
    """検証カバレッジのフルパネル（REDESIGN_UI_SPEC.md 8章・16章）。verification.htmlで使用。
    サイト全体の情報収集状況を示す視覚的主役コンポーネントで、個社の優劣を示すものではない。
    数値はハードコードせず generators.compute_verification_coverage() の集計値と
    num_services（実際のサービス数）から表示する。confirmedのみを「確認済み」件数に数え、
    derived/pending/uncollectedは凡例として別途明記する（既存4状態の区別を壊さない）。"""
    total = coverage.get("total", 0) or 0
    confirmed = coverage.get("confirmed", 0) or 0
    derived = coverage.get("derived", 0) or 0
    pending = coverage.get("pending", 0) or 0
    uncollected = coverage.get("uncollected", 0) or 0

    def _pct(n):
        return round(n * 100 / total) if total else 0

    bar = (f'<span class="trust-bar-confirmed" style="width:{_pct(confirmed)}%"></span>'
           f'<span class="trust-bar-derived" style="width:{_pct(derived)}%"></span>'
           f'<span class="trust-bar-pending" style="width:{_pct(pending)}%"></span>'
           f'<span class="trust-bar-uncollected" style="width:{_pct(uncollected)}%"></span>')
    legend = (f'<span class="trust-legend-item">{vstatus_badge("confirmed")}{confirmed}件</span> '
              f'<span class="trust-legend-item">{vstatus_badge("derived")}{derived}件</span> '
              f'<span class="trust-legend-item">{vstatus_badge("pending")}{pending}件</span> '
              f'<span class="trust-legend-item">{vstatus_badge("uncollected")}{uncollected}件</span>')
    link = ('<a class="trust-link" href="/verification">→ 確認状況を一覧で見る</a>'
            if link_to_dashboard else "")
    panel_class = "trust-panel"
    return f"""
    <div class="{panel_class}">
      <h2>検証カバレッジ</h2>
      <div class="trust-stats">
        <div class="trust-stat"><span class="trust-figure">{num_services}</span><span class="trust-label">掲載サービス数</span></div>
        <div class="trust-stat"><span class="trust-figure">{total}</span><span class="trust-label">確認対象の総数</span></div>
        <div class="trust-stat"><span class="trust-figure">{confirmed}</span><span class="trust-label">公式一次情報で確認済み</span></div>
      </div>
      <div class="trust-bar">{bar}</div>
      <div class="trust-legend">{legend}</div>
      {link}
      <p class="trust-note">※このパネルはサイト全体の情報収集状況を示すもので、サービスの優劣を示すものではありません。</p>
    </div>"""


def trust_line(coverage, num_services, with_numbers=False):
    """検証カバレッジの1行版（TOP・比較一覧用）。
    trust_panel()の集計ダッシュボード（3数値・進捗バー・4状態凡例・免責文）はverification.htmlに
    集約し、TOP・rankingではこの1行テキスト＋/verificationへの入口だけを出す。
    値単位のvstatus_badge()・source_link()には一切影響しない。
    with_numbers=True（比較一覧）: 「16社×3項目（計48項目）のうち34件…」のように
    総数48の導出（3項目×16社）が読める数字入り文言にする。
    with_numbers=False（TOP）: 数字を含まない信頼シグナルの1文にする。
    （VERIFICATION_COVERAGE_AND_GRID_IMPLEMENTATION_PLAN_2026_08_28.md A1）"""
    total = coverage.get("total", 0) or 0
    confirmed = coverage.get("confirmed", 0) or 0
    if with_numbers:
        text = f"{num_services}社×3項目（計{total}項目）のうち{confirmed}件を公式一次情報で確認済み。"
    else:
        text = "価格・送料・初回キャンペーンを公式サイトで1項目ずつ確認し、出典つきで掲載しています。"
    return f'<p class="price-meta trust-line">{text}<a href="/verification">→ 確認状況を一覧で見る</a></p>'


def purpose_chips_block(purpose_matches, extra_class="", with_anchor=False):
    """目的別導線チップ（REDESIGN_UI_SPEC.md 7章）。既存tags/targetに一致するサービスへの
    直接リンク集約のみで、新規フィルタエンジン・新規ページ・新規データフィールドは作らない。
    該当社が無いカテゴリはそもそも渡されない（generators.py compute_purpose_matches()側で除外済み）。
    見た目は「チップ（カテゴリ名）+ 配下のサービステキストリンク」へ再設計するが、
    各サービスリンクの遷移先（/services/{id}.html）は変更しない（既存CTA遷移先の維持）。
    カテゴリチップ自体はナビゲーションではなくラベルであり、順位・おすすめ度を表さない。
    extra_class: TOPページのみ"purpose-section-top"を渡し、色帯ゾーンとして格上げする
    （TOP_LAYOUT_IMPLEMENTATION_PLAN_2026_08_28.md）。他ページの呼び出しは既定の空文字のまま。
    with_anchor: TOPページのみTrue。各サービスリンクの隣に、TOP自身のサービス一覧内の
    該当カード（id="svc-{id}"）へのページ内アンカーを追加する（既存の詳細ページ直リンクは
    そのまま維持し、選択肢を1つ追加するだけ）。他ページはid="svc-*"を持たないため既定False。
    （TOP_PROGRESSIVE_DISCLOSURE_FINAL_AUDIT_2026_08_28.md）"""
    if not purpose_matches:
        return ""
    groups = ""
    for _cat_id, label, matched in purpose_matches:
        if with_anchor:
            links = "".join(
                f'<span class="purpose-service-link">'
                f'<a href="/services/{esc(s["id"])}">{esc(s["name"])}</a>'
                f'<a href="#svc-{esc(s["id"])}" class="purpose-anchor" '
                f'aria-label="{esc(s["name"])}を一覧で見る">↓</a></span>'
                for s in matched
            )
        else:
            links = "".join(
                f'<a href="/services/{esc(s["id"])}">{esc(s["name"])}</a>'
                for s in matched
            )
        groups += (f'<div class="purpose-group">'
                   f'<span class="purpose-chip">{esc(label)}</span>'
                   f'<div class="purpose-services">{links}</div></div>')
    section_class = f"purpose-section {extra_class}".strip() if extra_class else "purpose-section"
    # P2-0：モバイルのみ<details>折りたたみ。既存の.svc-more/.faq-itemと同じネイティブdetails
    # パターンを再利用し、新規ライブラリは追加しない。
    # - デフォルトはopen（641px以上のPCは常時展開を維持。CSSでsummary非表示）。
    # - モバイル(640px以下)は最小のインラインscriptで初期openを外し、summaryタップで開閉する。
    #   ※details:not([open])の内容はCSSのdisplay指定では描画されない（Chromium仕様）ため、
    #      PCの常時展開はopen属性で担保し、モバイルの初期閉はscriptで行う。
    # - リンク生成・遷移先・アンカー・タップ領域・情報量は一切変更しない。
    collapse_script = ("""
    <script>
    (function(){
      /* P2-0：モバイル(640px以下)は目的で探すを初期状態で閉じる（PCはopen維持で常時展開）。
         既存のsvc_more_anchor_scriptと同種のインラインscriptで、依存ライブラリは追加しない。 */
      var d = document.querySelector('.purpose-collapse');
      if (d && window.matchMedia('(max-width:640px)').matches) { d.removeAttribute('open'); }
    })();
    </script>""")
    return (f'<details class="{section_class} purpose-collapse" open>'
            f'<summary><h2>目的で探す</h2></summary>'
            f'<div class="purpose-groups">{groups}</div></details>'
            f'{collapse_script}')


def fully_verified_badge():
    """価格・送料・初回キャンペーンの3項目すべてが公式一次情報で確認済み（CONFIRMEDのみ。
    算出値は含めない）であることを示す事実表示。序列化・スコアリングには一切使わない
    （並び順はservices.json記載順のまま変更しない）。FINAL_REDESIGN_SPEC.md 4章・5章。"""
    return ('<span class="vfull-badge" title="価格・送料・初回キャンペーンの3項目すべてを'
            '公式一次情報で確認済みという事実表示です。総合評価やおすすめ度ではありません。">'
            '3項目とも確認済み</span>')


def vstatus_legend(link_to_dashboard=True):
    link = ' <a href="/verification">→ 全社の確認状況を一覧で見る</a>' if link_to_dashboard else ""
    return (
        '<p class="price-meta" style="margin-top:8px;">表示の見方：'
        f'{vstatus_badge("confirmed")}＝公式一次情報で確認／'
        f'{vstatus_badge("derived")}＝公式情報から計算／'
        f'{vstatus_badge("pending")}＝情報はあるが裏付け不十分／'
        f'{vstatus_badge("uncollected")}＝公式情報にまだ到達できていません{link}</p>'
    )


def _price_status(price_plan):
    """旧price_plan（lowest_per_meal_yen）からの確認状態（フォールバック用）。
    既存のconfirmed/derived/pending/uncollectedの意味は維持する。
    新schema（pricing）ではこの関数は使わず、_pricing_status/_price_point_statusを使う。"""
    if not price_plan:
        return "uncollected"
    notes = price_plan.get("plan_notes") or ""
    if price_plan.get("lowest_per_meal_yen") is not None:
        return "derived" if "DERIVED" in notes else "confirmed"
    return "pending" if "PENDING_VERIFICATION" in notes else "uncollected"


# ---------- pricing schema（価格ポイント構造）----------
# 旧 price_plan 単一値（lowest_per_meal_yen）を廃止方向とし、pricing + price_points[] を
# 優先する。旧price_planはPhase1のフォールバック用に一時的に保持する。
# statusは価格ポイント単位で保持し、plan_notesの自由文トークン判定からは完全に脱却する。

_BASIS_LABELS = {
    "regular": "通常",
    "initial": "初回",
    "trial": "お試し",
    "subscription": "定期割引",
    "bulk": "数量割引",
    "alacarte": "アラカルト",
}

_BASIS_VALID = set(_BASIS_LABELS)
_STATUS_VALID = {"confirmed", "derived", "pending", "uncollected"}

# 初回/お試しは「継続利用時の実質価格ではない」ため、比較一覧等で通常価格と同じ
# 視覚的重みで並ぶと誤読を招く（COMPETITOR_UX_FUNNEL_AUDIT_2026_08_28.md）。
# alacarte（継続的な単価）・bulk（継続利用の数量割引）は対象外。
_ONE_TIME_BASES = {"initial", "trial"}


def _pricing_of(service):
    """サービス1件からpricingブロックを返す。pricingが無ければ旧price_planを
    pricing互換の形に変換してフォールバックする（Phase1の後方互換層）。"""
    if isinstance(service, dict) and service.get("pricing"):
        return service["pricing"]
    price_plan = service.get("price_plan", {}) if isinstance(service, dict) else {}
    return _legacy_pricing_from_price_plan(price_plan)


def _legacy_pricing_from_price_plan(price_plan):
    """旧price_planをpricing互換の形へ変換（フォールバック専用）。
    既存のconfirmed/derived/pending/uncollected判定を維持する。"""
    price_plan = price_plan or {}
    if not price_plan:
        return None
    cheapest = price_plan.get("lowest_per_meal_yen")
    notes = price_plan.get("plan_notes") or ""
    if cheapest is not None:
        stat = "derived" if "DERIVED" in notes else "confirmed"
    else:
        stat = "pending" if "PENDING_VERIFICATION" in notes else "uncollected"
    points = []
    if cheapest is not None:
        points.append({
            "id": "legacy-single",
            "basis": "regular",
            "price_per_meal_yen": cheapest,
            "meal_count": None,
            "plan": None,
            "conditions": notes,
            "shipping_included": False,
            "regional": False,
            "tax": "included",
            "status": stat,
            "source_id": price_plan.get("source_id"),
            "last_checked": price_plan.get("last_checked"),
        })
    return {
        "currency": "JPY",
        "tax": "included",
        "regional_dependency": False,
        "price_notes": notes,
        "display": {
            "price_point_id": "legacy-single" if cheapest is not None else None,
            "label": "通常価格" if cheapest is not None else "公式確認中",
            "caption": "",
        },
        "price_points": points,
    }


def _price_point_by_id(pricing, point_id):
    """price_points[]から指定idの価格ポイントを返す。無ければNone。"""
    if not pricing or not point_id:
        return None
    for p in pricing.get("price_points", []):
        if p.get("id") == point_id:
            return p
    return None


def _display_point(pricing):
    """display.price_point_id が参照する価格ポイントを返す。"""
    if not pricing:
        return None
    disp = pricing.get("display") or {}
    return _price_point_by_id(pricing, disp.get("price_point_id"))


def _price_point_status(point):
    """価格ポイント単位の確認状態（confirmed/derived/pending/uncollected）。"""
    if not point:
        return "uncollected"
    return point.get("status", "uncollected")


def _pricing_status(pricing):
    """pricingブロック（価格フィールド全体）の確認状態。
    displayが参照する価格ポイントのstatusを採用する。displayが無い場合
    （地域依存で数値なし等）は従来互換のpending/uncollected判定に留める。"""
    if not pricing:
        return "uncollected"
    dp = _display_point(pricing)
    if dp is not None:
        return _price_point_status(dp)
    notes = pricing.get("price_notes") or ""
    return "pending" if "PENDING_VERIFICATION" in notes else "uncollected"


def _display_label(pricing):
    """表示ラベル。display.labelがあればそれを、無ければbasisから導出する。"""
    if not pricing:
        return ""
    disp = pricing.get("display") or {}
    label = disp.get("label")
    if label:
        return label
    dp = _display_point(pricing)
    if dp:
        return _BASIS_LABELS.get(dp.get("basis"), "")
    return ""


def _display_basis(pricing):
    """display価格ポイントのbasis（regular/initial/trial等）。無ければNone。"""
    dp = _display_point(pricing)
    return dp.get("basis") if dp else None


def _price_label_html(pricing):
    """価格の基準ラベル（初回/通常等）をspanで返す。initial/trial（初回限定の
    価格）は通常より高コントラストな装飾（price-basis-onetime）を付け、
    価格の数字と見た目の重みを合わせて誤読を防ぐ（COMPETITOR_UX_FUNNEL_AUDIT_2026_08_28.md）。"""
    label = _display_label(pricing)
    if not label:
        return ""
    cls = "price-basis price-basis-onetime" if _display_basis(pricing) in _ONE_TIME_BASES else "price-basis"
    return f'<span class="{cls}">{esc(label)}</span>'


def _price_point_value_text(point):
    """価格ポイントの値テキスト（スカラー/レンジ/未確認）。"""
    if not point:
        return "公式確認中"
    val = point.get("price_per_meal_yen")
    lo = point.get("min_per_meal_yen")
    hi = point.get("max_per_meal_yen")
    if val is not None:
        return f"{val:,}円/食"
    if lo is not None and hi is not None:
        return f"{lo:,}〜{hi:,}円/食"
    if lo is not None:
        return f"{lo:,}円〜/食"
    return "公式確認中"


def _display_figure_html(pricing, sources_by_id=None):
    """display価格の図版部分（--price-figure）。スカラー値/レンジ/未確認を判別する。
    戻り値: (表示HTML, display価格ポイント or None)。"""
    pricing = pricing or {}
    dp = _display_point(pricing)
    if dp is None:
        return ('<span class="price-unconfirmed">公式確認中</span>', None)
    val = dp.get("price_per_meal_yen")
    lo = dp.get("min_per_meal_yen")
    if val is not None:
        return (f'<span class="price-figure">{val:,}</span><span class="price-unit">円/食</span>', dp)
    if lo is not None:
        return (f'<span class="price-figure">{lo:,}</span><span class="price-unit">円〜/食</span>', dp)
    return ('<span class="price-unconfirmed">公式確認中</span>', dp)


def _price_source_meta(pricing, stat, sources_by_id=None):
    """確認済み/算出値のときのみ確認日を、出典があれば出典リンクを組み立てる。
    未確認（pending/uncollected）の値には確認日を出さない。"""
    dp = _display_point(pricing)
    src = source_link(sources_by_id, dp.get("source_id") if dp else None)
    checked = dp.get("last_checked", "") if dp else ""
    if src:
        date_html = ""
    elif stat in ("confirmed", "derived") and checked:
        date_html = f"（{esc(checked)}時点）"
    else:
        date_html = ""
    return f"{src}{date_html}"


def price_cell_html(pricing, sources_by_id=None):
    """価格の表示（display価格＋ラベル＋確認日/出典＋確認状態バッジ）を組み立てる。
    未確認（pending/uncollected）の値には確認日を出さない。
    検証状況ダッシュボードで使用する。"""
    pricing = pricing or {}
    stat = _pricing_status(pricing)
    badge = vstatus_badge(stat)
    fig, dp = _display_figure_html(pricing, sources_by_id)
    if dp is None:
        return f'{fig} {badge}'
    label_html = _price_label_html(pricing)
    meta = _price_source_meta(pricing, stat, sources_by_id)
    if _display_basis(pricing) in _ONE_TIME_BASES:
        return f"{label_html} {fig} {badge}{meta}"
    return f"{fig} {label_html} {badge}{meta}"


def price_figure_html(pricing, sources_by_id=None):
    """Service Card・詳細ページの料金ブロック用の価格表示（REDESIGN_UI_SPEC.md 4章・9章）。
    display価格を大きく表示し、ラベル・検証バッジ・出典/確認日は補助情報として下げる。
    未確認（pending/uncollected）の値には確認日を出さない。"""
    pricing = pricing or {}
    stat = _pricing_status(pricing)
    badge = vstatus_badge(stat)
    fig, dp = _display_figure_html(pricing, sources_by_id)
    meta_text = _price_source_meta(pricing, stat, sources_by_id)
    meta = f'<div class="svc-card-meta">{meta_text}</div>' if meta_text else ""
    if dp is None:
        return f'<div class="svc-card-price-row">{fig} {badge}</div>{meta}'
    label_html = _price_label_html(pricing)
    if _display_basis(pricing) in _ONE_TIME_BASES:
        return f'<div class="svc-card-price-row">{label_html} {fig} {badge}</div>{meta}'
    return f'<div class="svc-card-price-row">{fig} {label_html} {badge}</div>{meta}'


def _price_inline_html(pricing, sources_by_id=None):
    """比較テーブル（ranking・comparison）のセル用の価格表示。
    display価格＋ラベル＋バッジ。未確認の値は価格として強調せず控えめに表示する。"""
    pricing = pricing or {}
    stat = _pricing_status(pricing)
    badge = vstatus_badge(stat)
    fig, dp = _display_figure_html(pricing, sources_by_id)
    if dp is None:
        return f'{fig} {badge}'
    label_html = _price_label_html(pricing)
    if _display_basis(pricing) in _ONE_TIME_BASES:
        return f'{label_html} {fig} {badge}'
    return f'{fig} {label_html} {badge}'


def pricing_detail_html(pricing, sources_by_id=None):
    """サービス詳細ページの料金カード用。display価格を主表示し、
    その他の価格ポイントを一覧表示する（初回/通常/お試し/食数/送料込み別/条件）。"""
    pricing = pricing or {}
    main_html = price_figure_html(pricing, sources_by_id)
    points = pricing.get("price_points", [])
    note = esc(pricing.get("price_notes", ""))
    if not points:
        return (f'<div class="pricing-detail">{main_html}'
                f'<p class="price-meta">{note}</p></div>')
    dp = _display_point(pricing)
    rows = []
    for p in points:
        is_display = dp is not None and p.get("id") == dp.get("id")
        basis_label = _BASIS_LABELS.get(p.get("basis"), p.get("basis", ""))
        val_txt = _price_point_value_text(p)
        total = p.get("total_yen")
        if total is not None:
            val_txt += f"（1回{total:,}円）"
        ship_txt = "送料込み" if p.get("shipping_included") else "送料別"
        cond = p.get("conditions") or ""
        pstat = vstatus_badge(_price_point_status(p))
        mark = ' <span class="price-basis">★代表</span>' if is_display else ""
        rows.append(
            f'<tr><td>{esc(basis_label)}{mark}</td><td>{esc(p.get("plan") or "—")}</td>'
            f'<td>{esc(val_txt)}</td><td>{esc(ship_txt)}</td><td>{esc(cond)} {pstat}</td></tr>'
        )
    return f"""
    <div class="pricing-detail">
      {main_html}
      {mobile_scroll_hint()}
      <div class="table-scroll">
        <table class="price-points-table">
          <tr><th>基準</th><th>プラン</th><th>価格</th><th>送料</th><th>条件</th></tr>
          {''.join(rows)}
        </table>
      </div>
      <details class="price-notes">
        <summary>価格の根拠を見る</summary>
        <p class="price-meta">※★代表は比較一覧に表示する価格です。{note}</p>
      </details>
    </div>"""


def _shipping_status(shipping_row):
    """送料の確認状態。shipping_fee/notesのみから導出。"""
    if not shipping_row:
        return "uncollected"
    notes = shipping_row.get("notes") or ""
    if shipping_row.get("shipping_fee") is not None:
        return "confirmed"
    if "UNCOLLECTED" in notes:
        return "uncollected"
    return "confirmed"  # 地域等により変動するが公式情報として文章で確認済み


def _campaign_status(first_time_campaign):
    """初回キャンペーンの確認状態。既存のrequires_verification(bool)をそのまま使う。"""
    if not first_time_campaign:
        return "uncollected"
    return "uncollected" if first_time_campaign.get("requires_verification", True) else "confirmed"


def source_link(sources_by_id, source_id):
    """source_idに対応するsources.jsonエントリがあれば出典リンクを返す。
    source_idが無い、またはsources.json側にエントリが見つからない場合は空文字
    （リンクできない出典を示さない。PHASE2_IMPLEMENTATION_PLAN.md 7章）。
    見た目は--text-meta相当の補助情報クラス（.source-link）に統一する。"""
    if not source_id or not sources_by_id:
        return ""
    src = sources_by_id.get(source_id)
    if not src:
        return ""
    return (f' <a class="source-link" href="{esc(src.get("url", ""))}" target="_blank" rel="noopener nofollow">'
            f'出典を見る（確認日: {esc(src.get("confirmed_at", ""))}）</a>')


def shipping_line(shipping_row, sources_by_id=None):
    """data/shipping.jsonの1行から送料の表示行を組み立てる。
    地域・食数・プランで変動し単一値にできないサービスは notes の事実記述をそのまま表示する
    （単一値への圧縮による誤誘導を避けるため）。
    notesに"UNCOLLECTED"を含む行（内部ブロッカーの理由等）は、その理由文自体は
    ユーザー向けに表示しないが、「未収集」であること自体は確認状態バッジで正直に示す。
    確認済み（変動ありを含む）の場合のみ、source_idがあれば出典リンクを付す。"""
    status = _shipping_status(shipping_row)
    badge = vstatus_badge(status)
    if status == "uncollected":
        return f'<p><strong>送料：</strong>{badge}（最新情報は公式サイトでご確認ください）</p>'
    fee = shipping_row.get("shipping_fee")
    notes = (shipping_row.get("notes") or "").strip()
    if fee is not None:
        fee_text = "送料無料" if fee == 0 else f"{yen(fee)}"
        text = f"{fee_text}（{notes}）" if notes else fee_text
    else:
        text = notes
    src = source_link(sources_by_id, shipping_row.get("source_id"))
    return f'<p><strong>送料：</strong>{esc(text)} {badge}{src}</p>'


# ---------- リンク生成 ----------

def aff_link(aff_links, service_id, label=None, cls="btn-primary"):
    """アフィリエイトリンク。actual_urlがあればそれ、なければ公式URLにフォールバック。
    両方ない場合は、壊れたリンクを出さず「要確認」表示にする。"""
    info = aff_links.get(service_id, {})
    actual = info.get("actual_url", "")
    fallback = info.get("fallback_url", "")
    url = actual or fallback
    target = info.get("asp", "")
    label = label or "公式サイトを見る"
    if not url:
        return '<span class="btn-disabled">公式サイト（公式確認中）</span>'
    note = ""
    if actual:
        note = f'<span class="aff-note">（{esc(target)}経由）</span>'
    return f'<a class="{cls}" href="{esc(url)}" rel="nofollow sponsored noopener" target="_blank">{esc(label)}{note}</a>'


# ---------- 共通メタ基盤（favicon / OGP / JSON-LD）----------

_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#e8552d"/>'
    '<text x="32" y="44" font-size="32" font-family="sans-serif" font-weight="bold" '
    'text-anchor="middle" fill="#ffffff">宅</text></svg>'
)
FAVICON_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(_FAVICON_SVG.encode("utf-8")).decode("ascii")


def _meta_block(title, description, canonical_url):
    """OGP・Twitterカード・基本JSON-LD（WebSite）。既存のtitle/description/canonical値をそのまま利用するのみで、
    本文・見出し・価格表記等のコンテンツは一切変更しない。"""
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": SITE_DESC,
    }
    json_ld_script = json.dumps(json_ld, ensure_ascii=False)
    return f"""<link rel="icon" href="{FAVICON_DATA_URI}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical_url)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">{json_ld_script}</script>"""


# ---------- 共通テンプレート ----------

def _ga4_block():
    """GA4計測タグ。測定ID（config/site.jsonのga4_measurement_id）が未設定の間は
    外部スクリプトを読み込まず、dataLayerへのpushのみ行う安全なgtag()スタブだけを出力する。
    これによりdiagnosis_start/diagnosis_completeの呼び出しが、GA4未設定の状態でも
    gtag未定義エラーで壊れることなく（かつ二重計測にもならず）常に安全に動作する。
    測定IDが設定されて初めて実際にGoogleへ送信が始まる。PHASE4_FINAL_DECISION.md 1章。"""
    if not GA4_MEASUREMENT_ID:
        return ("<script>window.dataLayer=window.dataLayer||[];"
                "function gtag(){dataLayer.push(arguments);}</script>")
    gid = esc(GA4_MEASUREMENT_ID)
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js', new Date());gtag('config', '{gid}');</script>")


def _gtm_head_block():
    """Google Tag Managerのヘッド用スニペット（<head>のできるだけ高い位置に配置）。
    GTMコンテナID（config/site.jsonのgtm_container_id）が未設定の間は何も出力しない。
    Googleが配布するそのままのコードにコンテナIDを埋め込むのみで、既存のGA4ブロック
    （gtag()スタブ or gtag.js）とは独立して動く。"""
    if not GTM_CONTAINER_ID:
        return ""
    return (
        "<!-- Google Tag Manager -->\n"
        "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':"
        "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],"
        "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src="
        "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);"
        "})(window,document,'script','dataLayer','" + GTM_CONTAINER_ID + "');</script>\n"
        "<!-- End Google Tag Manager -->"
    )


def _gtm_body_block():
    """Google Tag Managerのnoscriptスニペット（<body>直後に配置）。
    GTMコンテナIDが未設定の間は何も出力しない。"""
    if not GTM_CONTAINER_ID:
        return ""
    return (
        "<!-- Google Tag Manager (noscript) -->\n"
        '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=' + GTM_CONTAINER_ID + '"\n'
        'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
        "<!-- End Google Tag Manager (noscript) -->"
    )


def page_header(title, description, canonical_path, main_class="container"):
    """main_class: <main>のクラス。既定は全ページ共通の"container"（1000px）。
    TOPページのみ"container-top"（1200px）を渡す（他ページは呼び出し元を変更しないため無影響）。
    canonical_pathは呼び出し元では従来通り".html"付きファイル名を渡す（呼び出し箇所は変更不要）。
    ここで拡張子なし正規URLに正規化する（URL_NORMALIZATION_AUDIT_2026_08_28.md）。
    Cloudflare Workers Static Assets（wrangler.toml html_handling=auto-trailing-slash）が
    ".html"付きURLを拡張子なしURLへ307リダイレクトする実挙動に、canonical/sitemap側を合わせる。"""
    if canonical_path == "index.html":
        canonical_url = f"{SITE_URL}/"
    else:
        canonical_url = f"{SITE_URL}/{canonical_path.removesuffix('.html')}"
    meta_block = _meta_block(title, description, canonical_url)
    ga4_block = _ga4_block()
    gtm_head = _gtm_head_block()
    gtm_body = _gtm_body_block()
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{gtm_head}
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
{GSC_META}
<link rel="canonical" href="{canonical_url}">
{meta_block}
{ga4_block}
<style>
{_CSS}
</style>
</head>
<body>
{gtm_body}
<header class="site">
  <div class="container">
    <a href="/" class="site-logo">{SITE_NAME}</a>
    <nav class="main">
      <a href="/ranking">比較一覧</a>
      <a href="/campaigns">初回キャンペーン</a>
      <a href="/tool/diagnosis">診断ツール</a>
    </nav>
  </div>
</header>
<main class="{main_class}">
"""


def page_footer(updated_date, show_vstatus_legend=False):
    legend = vstatus_legend() if show_vstatus_legend else ""
    return f"""
<div class="updated">最終更新: {updated_date} ｜ 情報は確認時点のものであり、最新の価格・条件は必ず公式サイトをご確認ください。{legend}</div>
</main>
<footer class="site">
  <div class="container">
    <p>{SITE_NAME}は宅配食サービスの比較情報を提供するサイトです。各サービスの価格・キャンペーン情報は常に変動します。</p>
    <p>当サイトはアフィリエイト広告（PR）を含みます。リンク経由で購入すると当サイトに報酬が入ることがあります。</p>
    <nav class="footer-nav" style="margin-top:12px;font-size:13px;">
      <a href="/privacy">プライバシーポリシー</a>｜
      <a href="/disclaimer">免責事項</a>｜
      <a href="/operator">運営者情報</a>｜
      <a href="/contact">お問い合わせ</a>
    </nav>
  </div>
</footer>
</body>
</html>"""


# ---------- サービス詳細ページ ----------

def related_services_block(related):
    """関連サービスカード。tags+targetの一致数>=2件のサービスのみ渡される想定
    （計算はgenerators.pyのcompute_related()で事前に行う）。該当が無ければ何も出力しない。"""
    if not related:
        return ""
    items = "".join(
        f'<a class="btn-secondary" href="/services/{esc(r["id"])}">{esc(r["name"])}</a> '
        for r in related
    )
    return f"""
    <div class="card">
      <h2>関連サービス</h2>
      <p class="price-meta">共通する特徴・対象が多いサービスです。</p>
      <div style="margin-top:8px;">{items}</div>
    </div>"""


def comparison_links_block(comparison_links):
    """比較ページへのリンク。config/comparisons.jsonの既存ペアをそのまま表示するだけで、
    新規の比較ロジック・新規ページは作らない。該当が無ければ何も出力しない。
    PHASE3_IMPLEMENTATION_PLAN.md 1.4節（比較ページの内部リンク孤立の解消）。"""
    if not comparison_links:
        return ""
    items = "".join(
        f'<a class="btn-secondary" href="{esc(url)}" style="margin-right:8px;">{esc(partner_name)}と比較する →</a>'
        for partner_name, url in comparison_links
    )
    return f"""
    <div class="card">
      <h2>比較ページ</h2>
      <div style="margin-top:8px;">{items}</div>
    </div>"""


def service_recommend_block(service):
    """「こんな方におすすめ」早期セクション。既存targetフィールドを、基本情報テーブルの
    1行から独立したカードへ格上げするだけで、新規データは使わない。
    価格より前に提示し、--color-surface-alt背景で最初の視覚的着地点にする
    （REDESIGN_UI_SPEC.md 12章・17章）。"""
    target = service.get("target", [])
    if not target:
        return ""
    items = "".join(f"<li>{esc(t)}</li>" for t in target)
    return f"""
    <div class="card panel-accent" id="recommend">
      <h2>こんな方におすすめ</h2>
      <ul class="feature-list">{items}</ul>
    </div>"""


def service_faq_block(service, shipping_row):
    """よくある質問。表示するかどうかの判定はtarget/cancellation_note/shipping.notesの
    有無を使うが、回答本文は同じページ内で既に表示済みの本文（#recommend／
    #cancellation-shipping）への短い参照リンクとし、全文の逐語再掲はしない
    （文言重複の解消。FINAL_REDESIGN_SPEC.md 8章）。
    見た目は<details>/<summary>による開閉式アコーディオンのまま変更しない。
    REDESIGN_UI_SPEC.md 12章・15.3節（モバイルの縦スクロール圧縮）。"""
    qa = []
    target_txt = "・".join(service.get("target", []))
    if target_txt:
        qa.append(("どんな人に向いていますか？",
                   '向いている人・向いていない人の具体例は、<a href="#recommend">上記「こんな方におすすめ」</a>にまとめています。'))
    cancel = service.get("cancellation_note")
    if cancel:
        qa.append(("解約・スキップはいつまでにすればいいですか？",
                   '解約・スキップの条件は、<a href="#cancellation-shipping">上記「解約・送料について」</a>に記載しています。'))
    if shipping_row and shipping_row.get("notes"):
        qa.append(("送料はいくらですか？地域で変わりますか？",
                   '送料の金額や地域差は、<a href="#cancellation-shipping">上記「解約・送料について」</a>をご確認ください。'))
    if not qa:
        return ""
    body = "".join(
        f'<details class="faq-item"><summary>{esc(q)}</summary><div class="faq-body"><p>{a}</p></div></details>'
        for q, a in qa
    )
    return f"""
    <div class="card">
      <h2>よくある質問</h2>
      {body}
    </div>"""


def build_service_page(service, aff_links, shipping_by_id=None, related=None, sources_by_id=None, comparison_links=None):
    s_id = service["id"]
    s_name = service["name"]
    shipping_row = (shipping_by_id or {}).get(s_id)
    shipping_html = shipping_line(shipping_row, sources_by_id)
    related_html = related_services_block(related)
    comparison_html = comparison_links_block(comparison_links)
    recommend_html = service_recommend_block(service)
    faq_html = service_faq_block(service, shipping_row)
    last_checked = service.get("last_checked", "")
    pricing = _pricing_of(service)
    first_camp = service.get("first_time_campaign", {})

    # 関連記事リンク（サービスDBに article_link があれば表示）
    article_link_html = ""
    _art_link = service.get("article_link", "")
    if _art_link:
        _art_label = service.get("article_label", "関連記事を見る")
        # article_linkはdata/services.json由来（".html"付き）。データは変更せず、
        # 表示URLのみ拡張子なし正規URLに正規化する（URL_NORMALIZATION_AUDIT_2026_08_28.md）。
        article_link_html = f'<a class="btn-secondary" href="{esc(_art_link.removesuffix(".html"))}">{esc(_art_label)}</a> '

    # メニュー・栄養
    feature_list = "".join(f"<li>{esc(f)}</li>" for f in service.get("main_features", []))

    # 保存方法は ranking/diagnosis と同じ正規化3カテゴリ（冷凍/冷蔵/日配）を表示し、
    # 比較一覧・診断ツールとの表記を揃える（generators.main() が meal_form_categories を付与）。
    # 付与が無い場合のみ従来の meal_form 全文にフォールバックする。
    _mfc = service.get("meal_form_categories") or []
    storage_txt = "・".join(_mfc) if _mfc else service.get("meal_form", "公式確認中")
    pros_list = service.get("pros", [])
    pros = "".join(f"<li>{esc(p)}</li>" for p in pros_list)
    cons = "".join(f"<li>{esc(c)}</li>" for c in service.get("cons", []))
    # 良い点[0]を「体験の一言」として視覚的に区別し、確信形成段階での具体イメージを後押しする
    # （食欲喚起UI監査§11.4 提案3）。文言はそのまま、後段のpros一覧とは罫線のみで区別する。空なら非表示。
    pros_highlight_html = f'<p class="pros-highlight">{esc(pros_list[0])}</p>' if pros_list else ""
    tags = "".join(_tag_html(t) for t in service.get("tags", []))

    # 価格はdisplay価格を主表示し、全価格ポイントを一覧表示する（--price-figure、12章）。
    # 未確認の値は小さく控えめに。
    price_block_html = pricing_detail_html(pricing, sources_by_id)

    title = f"{s_name}の特徴・料金・初回キャンペーンを解説"
    desc = f"{s_name}の特徴・料金・初回キャンペーン・お試し情報をまとめました。{SITE_NAME}が公式サイトで最終確認した情報（2026年8月）に基づく内容です。"

    html = page_header(title, desc, f"services/{s_id}.html")
    html += f"""
    <div class="page-head">
      <h1>{esc(s_name)}</h1>
      <span class="page-head-meta">確認日: {esc(last_checked) or "未確認"}</span>
    </div>
    <div>{tags}</div>
    {pros_highlight_html}
    {recommend_html}

    <div class="card">
      <h2>料金</h2>
      {price_block_html}
      <div class="svc-card-footer" style="margin-top:12px;">{aff_link(aff_links, s_id, label="公式サイトで料金・キャンペーンを確認")}</div>
    </div>
    {vstatus_legend(link_to_dashboard=True)}

    <div class="card card-quiet">
      <h2>基本情報</h2>
      <!-- 「対象」（向いている人）は上部の「こんな方におすすめ」カードとFAQで既に提示済みのため
           ここでは重複させない（購買意思決定ファネル横断監査 提案3）。このテーブルは
           運営会社/形態/保存方法という客観スペックに専念させる。 -->
      <table>
        <tr><th>運営会社</th><td>{esc(service.get("operator", "公式確認中"))}</td></tr>
        <tr><th>形態</th><td>{esc(service.get("meal_type", ""))}（{esc(service.get("meal_form", ""))}）</td></tr>
        <tr><th>保存方法</th><td>{esc(storage_txt)}</td></tr>
      </table>
    </div>

    <div class="card card-quiet">
      <h2>初回キャンペーン・お試し</h2>
      <p>{esc(first_camp.get("summary", "公式確認中"))} {vstatus_badge(_campaign_status(first_camp))}{source_link(sources_by_id, first_camp.get("source_id"))}</p>
      <p class="price-meta">{esc(first_camp.get("detail", ""))}</p>
      <div class="svc-card-footer" style="margin-top:12px;">{aff_link(aff_links, s_id, label="公式サイトでキャンペーンを確認", cls="btn-secondary")}</div>
    </div>

    <div class="card" id="cancellation-shipping">
      <h2>解約・送料について</h2>
      {shipping_html}
      <p>{esc(service.get("cancellation_note", "公式確認中（公式サイトで確認してください）"))}</p>
    </div>

    <div class="card">
      <h2>特徴</h2>
      <ul class="feature-list">{feature_list}</ul>
    </div>

    <div class="card">
      <h2>良い点・気になる点</h2>
      <div class="pros-cons">
        <div><strong>良い点</strong><ul class="feature-list">{pros}</ul></div>
        <div><strong>気になる点</strong><ul class="feature-list">{cons}</ul></div>
      </div>
    </div>
    {faq_html}
    {related_html}
    {comparison_html}
    <div class="card" style="text-align:center;">
      <p style="margin-bottom:8px;">{esc(s_name)}が気になった方は、公式サイトで最新の料金・キャンペーンをご確認ください。</p>
      {aff_link(aff_links, s_id, label="公式サイトを見る")}
    </div>
    <div class="svc-card-footer" style="margin-top:16px;">
      {article_link_html}
      <a class="btn-secondary" href="/ranking">← 比較一覧に戻る</a>
      <a class="btn-secondary" href="/campaigns">初回キャンペーン一覧を見る</a>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE, show_vstatus_legend=False)
    return html


# ---------- ランキングページ ----------

def comparison_pairs_block(comparison_pairs):
    """比較ページへのリンク一覧。config/comparisons.jsonの既存ペアをそのまま表示するだけで、
    新規の比較ロジック・新規ページは作らない。両社提携済みでないペアも参考情報として
    控えめなテキストリンクで載せる（CTAとしては扱わない）。
    PHASE3_IMPLEMENTATION_PLAN.md 1.4節（比較ページの内部リンク孤立の解消）。"""
    if not comparison_pairs:
        return ""
    items = "".join(
        f'<li><a href="{esc(url)}">{esc(a_name)} と {esc(b_name)} を比較する</a></li>'
        for a_name, b_name, url in comparison_pairs
    )
    return f"""
    <div class="card">
      <h2>個別の比較ページ</h2>
      <ul class="feature-list">{items}</ul>
    </div>"""


def build_ranking_page(services, campaigns, aff_links, comparison_pairs=None,
                        purpose_matches=None, coverage=None, fully_verified_ids=None,
                        sources_by_id=None):
    # サービスID → 確認済みの初回キャンペーン特典（requires_verification=false のみ表示）
    # camp_txt/camp_badge は同じcampaigns.json（data/campaigns.json）を情報源として揃える
    # （services.json側のfirst_time_campaignは別データで鮮度がずれている場合があるため使わない）。
    confirmed_camp = {}
    any_camp_ids = set()
    for c in campaigns:
        any_camp_ids.add(c.get("service_id"))
        if not c.get("requires_verification", True):
            confirmed_camp[c.get("service_id")] = c.get("discount_type", "")

    rows = []
    cards = []
    for svc in services:
        pricing = _pricing_of(svc)
        # 「表示価格が安い順」並び替え用のソートキー（Fix2）。表示中の数字（_display_figure_html
        # と同じ値）をそのまま使い、新たな正規化・算出は行わない。未確認（dpなし/val・lo共に無し）
        # は属性を出さず、並び替え時は常に末尾（元の相対順序を保ったまま）に置かれる。
        _dp = _display_point(pricing)
        _price_val = _dp.get("price_per_meal_yen") if _dp else None
        _price_lo = _dp.get("min_per_meal_yen") if _dp else None
        sort_price = _price_val if _price_val is not None else _price_lo
        price_attr = f' data-price="{sort_price}"' if sort_price is not None else ""
        camp_txt = confirmed_camp.get(svc["id"], "公式確認中")
        if svc["id"] in confirmed_camp:
            camp_status = "confirmed"
        elif svc["id"] in any_camp_ids:
            camp_status = "pending"
        else:
            camp_status = "uncollected"
        camp_badge = vstatus_badge(camp_status)
        tags = "".join(_tag_html(t) for t in svc.get("tags", [])[:3])
        # 気になる点（1例）。スクリーニング段階で「合わない理由」を判断できるようにする
        # （UI_DESIGN_PRINCIPLES.md 1章。既存consフィールドの先頭1件のみを事実表示として使う。
        # 「唯一の欠点」と誤読されないよう「（1例）」を明示し、新規データ・評価は追加しない）。
        cons_list = svc.get("cons") or []
        cons_first = cons_list[0] if cons_list else ""
        cons_line_table = f'<br><span class="price-meta">気になる点（1例）：{esc(cons_first)}</span>' if cons_first else ""
        # 保存方法（冷凍/冷蔵/日配）。診断ツールと同じmeal_form_categories()の正規化結果を再利用する
        # （PHASE3_IMPLEMENTATION_PLAN.md 2章：新しいmatching engineやデータモデルは作らない）。
        mealform_cats = svc.get("meal_form_categories") or []
        mealform_txt = "・".join(mealform_cats) if mealform_cats else esc(svc.get("meal_form", "")) or "公式確認中"
        mealform_attr = esc(" ".join(mealform_cats))
        # 「全項目確認済み」の事実バッジ（CONFIRMEDのみ、序列化には使わない。FINAL_REDESIGN_SPEC.md 5章）。
        full_badge = fully_verified_badge() if svc["id"] in (fully_verified_ids or set()) else ""
        # 「評価」段階の主役は内部CTA（詳しく見る）。デスクトップ・モバイルで階層を統一する
        # （UI_DESIGN_PRINCIPLES.md 5.2「情報が不足している段階では外部CTAを主役にしない」）。
        # いずれも既存の遷移先（公式URL/ASP actual_url）は不変。
        detail_link = f'<a class="btn-primary" href="/services/{svc["id"]}">詳しく見る</a>'
        aff_cta_table = aff_link(aff_links, svc["id"], label="公式サイトを確認", cls="btn-secondary")
        aff_cta_card = aff_link(aff_links, svc["id"], label="公式サイトを確認", cls="btn-secondary")

        # デスクトップ：テーブル行（9.4節。価格セルだけ--price-figureで強調）
        price_cell = _price_inline_html(pricing, sources_by_id)
        rows.append(f"""
        <tr data-mealform="{mealform_attr}"{price_attr}>
          <td><a href="/services/{svc['id']}"><strong>{esc(svc['name'])}</strong></a>{full_badge}<br>{tags}{cons_line_table}</td>
          <td class="td-price">{price_cell}</td>
          <td>{esc(camp_txt)} {camp_badge}</td>
          <td>{mealform_txt}</td>
          <td>{', '.join(svc.get('target', []))}</td>
          <td>{detail_link} {aff_cta_table}</td>
        </tr>""")

        # モバイル：Service Card縦積み（9章・15.2節。価格→保存方法/向いている人→検証→CTAの順）
        price_html = price_figure_html(pricing, sources_by_id)
        target_txt = "・".join(svc.get("target", [])) or "公式確認中"
        # 保存方法の値に、meal_form内の（...）食べ方注記があれば添える（食欲喚起UI監査§11.4 提案2）。
        # デスクトップ表側のmealform_txtは変更しない（カードのみが対象）。
        meal_note = _meal_form_note(svc.get("meal_form"))
        mealform_card_txt = f"{mealform_txt}・{esc(meal_note)}" if meal_note else mealform_txt
        cards.append(f"""
        <div class="svc-card" data-mealform="{mealform_attr}"{price_attr}>
          <div class="svc-card-header">
            <h3 class="svc-card-name"><a href="/services/{svc['id']}">{esc(svc['name'])}</a></h3>
            {full_badge}
          </div>
          <div class="svc-card-tags">{tags}</div>
          {price_html}
          <div class="svc-card-specs">
            <div class="svc-spec"><span class="svc-spec-label">初回キャンペーン</span><span class="svc-spec-value">{esc(camp_txt)} {camp_badge}</span></div>
            <div class="svc-spec"><span class="svc-spec-label">保存方法</span><span class="svc-spec-value">{mealform_card_txt}</span></div>
            <div class="svc-spec svc-spec-wide"><span class="svc-spec-label">向いている人</span><span class="svc-spec-value">{target_txt}</span></div>
            {f'<div class="svc-spec svc-spec-wide"><span class="svc-spec-label">気になる点（1例）</span><span class="svc-spec-value">{esc(cons_first)}</span></div>' if cons_first else ''}
          </div>
          <div class="svc-card-footer">{detail_link} {aff_cta_card}</div>
        </div>""")

    # モバイルの段階開示（TOP=build_index_pageのsvc_more_blockと同一パターン）。
    # <details>は<table>の<tr>を直接ラップできないためdesktop tableは対象外とし、
    # モバイルカードのみ先頭6件を常時表示・残りを<details>に格納する。並び順は
    # servicesリスト（=services.json記載順）をそのままスライスするだけで、
    # 確認状況・価格等による並び替えは行わない（FINAL_REDESIGN_SPEC.md 5章の順位付け禁止）。
    MOBILE_PRIMARY_COUNT = 6
    cards_primary = cards[:MOBILE_PRIMARY_COUNT]
    cards_more = cards[MOBILE_PRIMARY_COUNT:]
    mobile_more_html = (f"""
      <details class="svc-more">
        <summary>残り{len(cards_more)}社をすべて見る</summary>
        {''.join(cards_more)}
      </details>""" if cards_more else "")

    # 「ランキング」は名乗らない：確認済み項目数等いかなる基準でも数値順位は付けない
    # （根拠のないランキングを作らないという既存方針。FINAL_REDESIGN_SPEC.md 5章の最終判断）。
    # URL（ranking.html）・ナビゲーションのリンク先は変更しない。ページ内文言のみ「比較一覧」に改める。
    title = "宅配食 比較一覧【2026年8月最新】"
    desc = "宅配食・宅配弁当サービスの最新比較。nosh、ワタミの宅食ダイレクト、三ツ星ファームなど主要サービスの料金・特徴・初回キャンペーンを一覧で比較。順位付けはせず、確認できた情報のみを一覧にしています。"

    num_services = len(services)
    # 検証カバレッジの集計ダッシュボードはverification.htmlに集約し、比較一覧では
    # 比較表より後（full_badge_noteの直後）に1行のtrust_line()を置く（A5）。
    trust_line_html = trust_line(coverage, num_services, with_numbers=True) if coverage else ""
    full_badge_note = (f'<p class="price-meta" style="margin-top:8px;">{fully_verified_badge()}＝'
                       '価格・送料・初回キャンペーンの3項目すべてを公式一次情報で確認済みという事実表示です。'
                       '並び順・おすすめ度とは関係ありません（当サイトは順位付けを行いません）。</p>')

    html = page_header(title, desc, "ranking.html")
    html += f"""
    <h1>宅配食 比較一覧【2026年8月最新】</h1>
    <p>主要宅配食サービスを比較しています。価格・キャンペーン情報は公式サイトで確認できたもののみ掲載し、未確認の項目は「公式確認中」と表示しています（{LAST_VERIFIED_DATE}時点）。当サイトは独自の点数やランキング順位を付けていません。</p>
    {purpose_chips_block(purpose_matches)}
    <div class="card card-quiet">
      <h3 style="margin-top:0;">保存方法で絞り込む（任意）</h3>
      <div id="mealform-filter" class="checks">
        <label><input type="checkbox" value="冷凍" onchange="filterRankingByMealform()"> 冷凍</label>
        <label><input type="checkbox" value="冷蔵" onchange="filterRankingByMealform()"> 冷蔵</label>
        <label><input type="checkbox" value="日配" onchange="filterRankingByMealform()"> 日配</label>
      </div>
    </div>
    <div class="card card-quiet">
      <h3 style="margin-top:0;">表示価格が安い順に並べ替える（任意）</h3>
      <div class="checks">
        <label><input type="checkbox" id="sort-by-price" onchange="sortRankingByPrice()"> 表示価格が安い順</label>
      </div>
      <p class="price-meta">表示価格は初回・お試し・通常価格が混在します（各行のラベルでご確認ください）。送料等を含めた正規化はしていません。</p>
    </div>
    {vstatus_legend(link_to_dashboard=True)}
    <div class="ranking-desktop">
      <div class="card">
        <table id="ranking-table">
          <thead><tr><th>サービス</th><th>1食あたりの料金</th><th>初回キャンペーン</th><th>保存方法</th><th>向いている人</th><th></th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </div>
    <div class="ranking-mobile">
      {''.join(cards_primary)}
      {mobile_more_html}
    </div>
    {full_badge_note}
    {trust_line_html}
    <div class="card card-quiet">
      <h2 class="heading-staggered">選び方のポイント</h2>
      <ul class="feature-list">
        <li>「お試し価格で始めたい」→ 初回キャンペーンがお得なサービスを選ぶ</li>
        <li>「糖質制限をしたい」→ nosh・三ツ星ファームなど低糖質に強いサービス</li>
        <li>「栄養バランス重視」→ 管理栄養士監修のサービス</li>
      </ul>
      <p style="margin-top:12px;"><a class="btn-primary" href="/tool/diagnosis">自分に合うサービスを診断する →</a></p>
    </div>
    {comparison_pairs_block(comparison_pairs)}
    <p class="price-meta">※各サービスの詳細はサービス名リンクから。価格・キャンペーン情報は常に変動するため、最新情報は公式サイトをご確認ください。</p>
    <script>
    function filterRankingByMealform() {{
      const checked = [...document.querySelectorAll('#mealform-filter input:checked')].map(x => x.value);
      document.querySelectorAll('#ranking-table tr[data-mealform], .ranking-mobile .svc-card[data-mealform]').forEach(el => {{
        const forms = (el.dataset.mealform || '').split(' ').filter(Boolean);
        const show = checked.length === 0 || forms.some(f => checked.includes(f));
        el.style.display = show ? '' : 'none';
      }});
    }}
    // 「表示価格が安い順」並び替え（Fix2）。当サイトは点数・順位付けを行わないため、
    // これはユーザー起点・既定オフの並び替えであり、評価やランキングではない。
    // 元の並び順（表示中の全要素）をページ読み込み時に1回だけ記録し、解除時に復元する。
    // モバイルの段階開示（.svc-more）導入により、カードの親要素が「.ranking-mobile直下」と
    // 「<details>内」の2種類に分かれるため、それぞれ独立に並べ替える（親をまたいで
    // 1つの配列を並べ替えると異なる親の要素が意図せず集まってしまうため）。
    const originalRows = [...document.querySelectorAll('#ranking-table tr[data-mealform]')];
    const originalCardsPrimary = [...document.querySelectorAll('.ranking-mobile > .svc-card[data-mealform]')];
    const originalCardsMore = [...document.querySelectorAll('.ranking-mobile .svc-more .svc-card[data-mealform]')];
    function reorderTo(elements) {{
      // table直下の裸<tr>はブラウザが暗黙のtbodyを生成するため、table自体にでは
      // なく各要素のparentNodeにappendChildする（実際の親がどちらでも正しく動く）。
      elements.forEach(el => el.parentNode.appendChild(el));
    }}
    function sortRankingByPrice() {{
      const asc = document.getElementById('sort-by-price').checked;
      if (!asc) {{
        reorderTo(originalRows);
        reorderTo(originalCardsPrimary);
        reorderTo(originalCardsMore);
        return;
      }}
      const byPrice = (a, b) => {{
        const pa = a.dataset.price === undefined ? Infinity : parseFloat(a.dataset.price);
        const pb = b.dataset.price === undefined ? Infinity : parseFloat(b.dataset.price);
        return pa - pb;
      }};
      reorderTo([...originalRows].sort(byPrice));
      reorderTo([...originalCardsPrimary].sort(byPrice));
      reorderTo([...originalCardsMore].sort(byPrice));
    }}
    </script>
    """
    html += page_footer(LAST_VERIFIED_DATE, show_vstatus_legend=False)
    return html


# ---------- キャンペーン一覧ページ ----------

def build_campaigns_page(campaigns, services, aff_links):
    svc_by_id = {s["id"]: s for s in services}
    # 確認済み優先ソート（TOPのbuild_index_page内confirmed_firstと同一ロジック。変更時は
    # 両方見ること＝VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目3/3b）。
    confirmed_first = sorted(campaigns, key=lambda c: c.get("requires_verification", True))
    cards = []
    for i, c in enumerate(confirmed_first):
        svc = svc_by_id.get(c.get("service_id"))
        svc_name = svc["name"] if svc else "公式確認中"
        svc_id = c.get("service_id", "")
        is_featured = (i == 0)
        wrapper_cls = "campaign-pick-featured" if is_featured else "card"
        label_html = '<p class="campaign-pick-label">PICK UP</p>' if is_featured else ""
        # 割引タイプが確認済みの場合、summaryは同じ内容の言い換えになり重複するため非表示にする。
        # discount_type未確認の場合はsummaryが唯一の説明文なので表示を維持する（情報欠落を避ける）。
        discount_type = c.get('discount_type')
        has_real_discount = bool(discount_type) and discount_type != '公式確認中'
        summary_html = "" if has_real_discount else f"<p>{esc(c['summary'])}</p>"
        cards.append(f"""
        <div class="{wrapper_cls}">
          {label_html}
          <h2>{esc(c['title'])}</h2>
          {summary_html}
          <table>
            <tr><th>対象サービス</th><td>{esc(svc_name)}</td></tr>
            <tr><th>割引タイプ</th><td>{esc(c.get('discount_type', '公式確認中'))}</td></tr>
            <tr><th>条件</th><td>{esc(c.get('conditions', '公式確認中'))}</td></tr>
            <tr><th>最終確認</th><td>{esc(c.get('last_checked', ''))}</td></tr>
          </table>
          <div style="margin-top:12px;">
            <a class="btn-secondary" href="/services/{esc(svc_id)}">サービス詳細を見る</a>
            {aff_link(aff_links, c['service_id'], label='公式サイトでキャンペーンを確認', cls='btn-primary')}
          </div>
        </div>""")

    title = "宅配食 初回キャンペーン・お試し情報まとめ【2026年8月】"
    desc = "宅配食サービスの最新の初回キャンペーン・お試し価格情報を一覧で紹介。お得に宅配食を始めたい人向け。"

    html = page_header(title, desc, "campaigns.html")
    html += f"""
    <h1>宅配食 初回キャンペーン・お試し情報まとめ</h1>
    <p>各サービスの初回キャンペーン・お試し情報を毎週更新しています。最新の割引条件は必ず公式サイトでご確認ください。</p>
    {''.join(cards)}
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 比較ページ ----------

def _comparison_price_diff_html(service_a, service_b):
    """両社のdisplay価格が『同一basis＋スカラー値＋confirmed/derived』の場合のみ
    価格差を算出して結論として先出しする。
    基準（basis）不一致・レンジ（min/max）・未確認は単純な「◯円安い」を出さない
    （基準の違う値・レンジ値・条件不一致の値の引き算は誤誘導になるため）。
    FINAL_REDESIGN_SPEC.md 4章・9章（基準一致の条件を追加）。"""
    pa = _pricing_of(service_a)
    pb = _pricing_of(service_b)
    da = _display_point(pa)
    db = _display_point(pb)
    if da is None or db is None:
        return ""
    sa, sb = _price_point_status(da), _price_point_status(db)
    if sa not in ("confirmed", "derived") or sb not in ("confirmed", "derived"):
        return ""
    if da.get("basis") != db.get("basis"):
        a_lab = _display_label(pa) or _BASIS_LABELS.get(da.get("basis"), "")
        b_lab = _display_label(pb) or _BASIS_LABELS.get(db.get("basis"), "")
        return (f"<p>{esc(service_a['name'])}の表示価格は「{esc(a_lab)}」、"
                f"{esc(service_b['name'])}の表示価格は「{esc(b_lab)}」と基準が異なるため、"
                f"単純な価格差は出していません（比較時は価格の基準を必ずご確認ください）。</p>")
    va, vb = da.get("price_per_meal_yen"), db.get("price_per_meal_yen")
    if va is None or vb is None:
        return "<p>両社の表示価格はレンジ（〜）のため、単純な価格差は出していません。</p>"
    diff = abs(va - vb)
    if diff == 0:
        return f"<p>{esc(service_a['name'])}と{esc(service_b['name'])}の1食あたり価格はほぼ同じです（確認済み・算出値どうしの比較）。</p>"
    cheaper = service_a["name"] if va < vb else service_b["name"]
    return f"<p><strong>{esc(cheaper)}の方が1食あたり{diff}円安い</strong>です（確認済み・算出値どうしの比較）。</p>"


def _comparison_target_diff_html(service_a, service_b):
    """targetの集合差分（A限定・B限定・共通）を提示する。新規スコアリングではなく
    既存targetフィールドの集合演算のみ。FINAL_REDESIGN_SPEC.md 4章・9章。"""
    a_list, b_list = service_a.get("target", []), service_b.get("target", [])
    a_set, b_set = set(a_list), set(b_list)
    only_a = [t for t in a_list if t not in b_set]
    only_b = [t for t in b_list if t not in a_set]
    common = [t for t in a_list if t in b_set]
    items = []
    if only_a:
        items.append(f"<li><strong>{esc(service_a['name'])}が向いている人：</strong>{esc('・'.join(only_a))}</li>")
    if only_b:
        items.append(f"<li><strong>{esc(service_b['name'])}が向いている人：</strong>{esc('・'.join(only_b))}</li>")
    if common:
        items.append(f"<li><strong>どちらでも当てはまる人：</strong>{esc('・'.join(common))}</li>")
    if not items:
        return ""
    return f'<ul class="feature-list">{"".join(items)}</ul>'


def build_comparison_page(service_a, service_b, aff_links, sources_by_id=None):
    a_id, b_id = service_a["id"], service_b["id"]
    a_name, b_name = service_a["name"], service_b["name"]

    # 価格セル：display価格＋ラベル。confirmed/derivedのみ--price-figureで強調し、未確認の値は控えめに沈める
    # （REDESIGN_UI_SPEC.md 13章「データの確実性とUIの強調度を一致させる」）。
    a_price = _price_inline_html(_pricing_of(service_a), sources_by_id)
    b_price = _price_inline_html(_pricing_of(service_b), sources_by_id)

    a_tags = "".join(_tag_html(t) for t in service_a.get("tags", []))
    b_tags = "".join(_tag_html(t) for t in service_b.get("tags", []))

    price_diff_html = _comparison_price_diff_html(service_a, service_b)
    target_diff_html = _comparison_target_diff_html(service_a, service_b)

    title = f"{a_name}と{b_name}を徹底比較！どっちがおすすめ？【2026年】"
    desc = f"{a_name}と{b_name}を料金・特徴・初回キャンペーンで比較。一人暮らし・ダイエット・糖質制限など目的別におすすめを解説。"

    html = page_header(title, desc, f"comparisons/{a_id}-vs-{b_id}.html")
    html += f"""
    <h1>{esc(a_name)}と{esc(b_name)}を徹底比較</h1>
    <p>どちらにするか迷っている人向けに、料金・特徴・初回キャンペーンを比較します。（2026年8月時点の情報）</p>

    <div class="card panel-accent">
      <h2>結論</h2>
      {price_diff_html}
      {target_diff_html}
      <!-- 公式サイトCTAはこの結論パネルのみに置く（購買意思決定ファネル横断監査 提案2）。
           比較表内・下部フッターに同一リンクの「公式サイト」行は重複させない。 -->
      <div class="svc-card-footer" style="margin-top:12px;">
        {aff_link(aff_links, a_id, label=f'{a_name}の公式サイトを見る', cls='btn-primary')}
        {aff_link(aff_links, b_id, label=f'{b_name}の公式サイトを見る', cls='btn-primary')}
      </div>
    </div>

    {vstatus_legend(link_to_dashboard=True)}
    {mobile_scroll_hint()}
    <div class="card">
      <table class="compare-table">
        <tr><th></th><th>{esc(a_name)}</th><th>{esc(b_name)}</th></tr>
        <tr><td><strong>特徴</strong></td><td>{a_tags}</td><td>{b_tags}</td></tr>
        <tr><td><strong>1食あたりの料金</strong></td><td class="price-cell">{a_price}</td><td class="price-cell">{b_price}</td></tr>
        <tr><td><strong>向いている人</strong></td><td>{', '.join(service_a.get('target', []))}</td><td>{', '.join(service_b.get('target', []))}</td></tr>
        <tr><td><strong>料金・特徴を詳しく見る</strong></td><td><a class="btn-secondary" href="/services/{esc(a_id)}">{esc(a_name)}の詳細ページ</a></td><td><a class="btn-secondary" href="/services/{esc(b_id)}">{esc(b_name)}の詳細ページ</a></td></tr>
      </table>
    </div>

    <div class="card">
      <h2>{esc(a_name)}の良い点・気になる点</h2>
      <div class="pros-cons">
        <div><strong>良い点</strong><ul class="feature-list">{''.join(f'<li>{esc(p)}</li>' for p in service_a.get('pros', []))}</ul></div>
        <div><strong>気になる点</strong><ul class="feature-list">{''.join(f'<li>{esc(c)}</li>' for c in service_a.get('cons', []))}</ul></div>
      </div>
    </div>

    <div class="card">
      <h2>{esc(b_name)}の良い点・気になる点</h2>
      <div class="pros-cons">
        <div><strong>良い点</strong><ul class="feature-list">{''.join(f'<li>{esc(p)}</li>' for p in service_b.get('pros', []))}</ul></div>
        <div><strong>気になる点</strong><ul class="feature-list">{''.join(f'<li>{esc(c)}</li>' for c in service_b.get('cons', []))}</ul></div>
      </div>
    </div>

    <div class="svc-card-footer" style="margin-top:16px;">
      <a class="btn-secondary" href="/campaigns">初回キャンペーン一覧を見る</a>
      <a class="btn-secondary" href="/tool/diagnosis">診断ツールで選ぶ</a>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE, show_vstatus_legend=False)
    return html


# ---------- 診断ツール ----------

def build_diagnosis_tool(services, aff_links, sources_by_id=None):
    # クライアントサイドで動作する条件検索ツール
    svc_data = []
    for svc in services:
        aff = aff_links.get(svc["id"], {})
        pricing = _pricing_of(svc)
        _dp = _display_point(pricing)
        # 診断結果カードにもTOP/ranking/詳細と同じ価格表示・検証バッジを出す
        # （購買意思決定ファネル横断監査 提案1。price_figure_htmlをそのまま再利用し、
        # 新規の表示ロジック・新規データは作らない）。
        price_html = price_figure_html(pricing, sources_by_id)
        svc_data.append({
            "id": svc["id"],
            "name": svc["name"],
            "tags": svc.get("tags", []),
            "target": svc.get("target", []),
            "price": _dp.get("price_per_meal_yen") if _dp else None,  # display価格（スカラーのみ）
            "price_html": price_html,
            "meal_form_categories": svc.get("meal_form_categories", []),
            "url": svc.get("official_url", ""),
            "aff_url": aff.get("actual_url", ""),  # アフィリエイトリンク（あれば優先）
            "detail_url": f"/services/{svc['id']}",  # 当サイト内サービス詳細ページ
        })
    svc_json = json.dumps(svc_data, ensure_ascii=False)

    title = "宅配食 診断ツール｜自分に合うサービスを条件で探す"
    desc = "予算・目的・こだわりを選ぶだけで、あなたに合う宅配食サービスがわかる無料の診断ツール。"

    html = page_header(title, desc, "tool/diagnosis.html")
    html += f"""
    <h1>宅配食 診断ツール</h1>
    <p class="price-meta">目的・保存方法を選ぶだけで、条件に近い上位3社をすぐに表示します。</p>

    <div class="card">
      <h3>目的を選んでください（複数可）</h3>
      <div id="goals" class="checks">
        <label><input type="checkbox" value="一人暮らし"> 一人暮らし</label>
        <label><input type="checkbox" value="ダイエット"> ダイエット</label>
        <label><input type="checkbox" value="糖質制限"> 糖質制限</label>
        <label><input type="checkbox" value="健康志向"> 健康志向</label>
        <label><input type="checkbox" value="時短"> 時短（手間を省きたい）</label>
        <label><input type="checkbox" value="高タンパク"> 高タンパク</label>
        <label><input type="checkbox" value="高齢者"> 親・高齢者の食事</label>
      </div>
      <h3 style="margin-top:16px;">保存方法で絞り込む（任意）</h3>
      <div id="mealforms" class="checks">
        <label><input type="checkbox" value="冷凍"> 冷凍</label>
        <label><input type="checkbox" value="冷蔵"> 冷蔵</label>
        <label><input type="checkbox" value="日配"> 日配</label>
      </div>
      <p id="diag-summary" class="diag-summary"></p>
      <p style="margin-top:12px;"><button class="btn-primary" onclick="runDiag()">診断する →</button></p>
    </div>

    <div id="result" class="card" style="display:none;"></div>

    <script>
    const SERVICES = {svc_json};
    // GA4計測（診断ツール専用。ページ遷移が無いGA4拡張計測ではカバーできないためこの2つのみ独自実装する。
    // PHASE4_FINAL_DECISION.md 1章）。診断開始は初回のチェック操作でのみ1回発火（多重発火防止）。
    let _diagStarted = false;
    // 選択サマリー（REDESIGN_UI_SPEC.md 14章）。選択済みチェックボックスの個数・名称を
    // 表示するだけの純粋な表示ロジックで、スコアリング・推薦アルゴリズムには一切影響しない。
    function updateDiagSummary() {{
      const goals = [...document.querySelectorAll('#goals input:checked')].map(x => x.parentNode.textContent.trim());
      const mealForms = [...document.querySelectorAll('#mealforms input:checked')].map(x => x.parentNode.textContent.trim());
      const parts = [];
      if (goals.length) parts.push(goals.join('・'));
      if (mealForms.length) parts.push('保存方法：' + mealForms.join('・'));
      document.getElementById('diag-summary').textContent = parts.length ? '選択中：' + parts.join(' ／ ') : '';
    }}
    document.querySelectorAll('#goals input, #mealforms input').forEach(el => {{
      el.addEventListener('change', () => {{
        if (!_diagStarted) {{ _diagStarted = true; window.dataLayer.push({{event: 'diagnosis_start'}}); }}
        updateDiagSummary();
      }});
    }});
    function runDiag() {{
      const goals = [...document.querySelectorAll('#goals input:checked')].map(x => x.value);
      const mealForms = [...document.querySelectorAll('#mealforms input:checked')].map(x => x.value);
      if (goals.length === 0 && mealForms.length === 0) {{
        document.getElementById('result').style.display = 'block';
        document.getElementById('result').innerHTML = '<p>目的または保存方法を1つ以上選んでください。</p>';
        return;
      }}
      // 保存方法（冷凍/冷蔵/日配）はAND条件の絞り込み。未選択なら全件を対象にする
      let candidates = SERVICES;
      if (mealForms.length > 0) {{
        candidates = candidates.filter(s => (s.meal_form_categories||[]).some(c => mealForms.includes(c)));
      }}
      // タグ or ターゲットとの一致数でスコアリング（目的が未選択なら絞り込みのみ行う）。
      // matchedGoalsは「一致理由」表示用に一致した目的タグ名をそのまま保持するだけで、
      // 新しい推薦エンジンやスコアの重み付けは追加しない。
      const scored = goals.length === 0
        ? candidates.map(s => ({{ ...s, score: 0, matchedGoals: [] }}))
        : candidates.map(s => {{
            const pool = [...(s.tags||[]), ...(s.target||[])];
            const matchedGoals = goals.filter(g => pool.includes(g));
            return {{ ...s, score: matchedGoals.length, matchedGoals }};
          }}).filter(s => s.score > 0).sort((a,b) => b.score - a.score);
      // 診断完了（「please select」の早期returnケースでは発火しない＝実際に診断を実行した回数のみ計測）。
      // result_countは表示件数ではなく実際に条件へ一致した全件数を送る。
      window.dataLayer.push({{
        event: 'diagnosis_complete',
        goal_count: goals.length,
        mealform_count: mealForms.length,
        result_count: scored.length
      }});
      // 結果は上位3件のみ表示する（推薦エンジンではなく、既存スコア計算の表示件数を絞るだけ。
      // FINAL_REDESIGN_SPEC.md 10章）。
      const TOP_N = 3;
      const topScored = scored.slice(0, TOP_N);
      let html = scored.length > 0
        ? `<h2>あなたの条件に近い上位${{topScored.length}}社</h2>`
        : '<h2>あなたにおすすめのサービス</h2>';
      if (scored.length === 0) {{
        html += '<p>条件に合うサービスがまだ登録されていません。近日中に追加予定です。</p>';
      }} else {{
        for (const s of topScored) {{
          const detail = `<a class="btn-primary" href="${{s.detail_url}}">詳しく見る</a>`;
          const url = s.aff_url || s.url || '';
          const rel = s.aff_url ? 'rel="nofollow sponsored"' : '';
          const label = s.aff_url ? '公式サイトを見る' : '公式サイト';
          const link = url ? `<a class="btn-secondary" href="${{url}}" ${{rel}} target="_blank" rel="noopener">${{label}}</a>` : '<span class="btn-disabled">公式確認中</span>';
          const STORAGE_ICONS = {{
            '冷凍': '<svg class="tag-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1v14M2.5 4l11 8M13.5 4l-11 8"/></svg>',
            '冷蔵': '<svg class="tag-icon" viewBox="0 0 16 16" aria-hidden="true"><rect x="3" y="1" width="10" height="14" rx="1"/><path d="M3 6h10"/></svg>',
            '日配': '<svg class="tag-icon" viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="6" width="12" height="8" rx="1"/><path d="M2 6l6-4 6 4"/></svg>'
          }};
          const storageCategory = t => ['冷凍', '冷蔵', '日配'].find(c => t.includes(c));
          const tags = (s.tags || []).slice(0, 3).map(t => {{
            const cat = storageCategory(t);
            const icon = cat ? STORAGE_ICONS[cat] : '';
            return `<span class="tag${{cat ? ' tag-storage' : ''}}">${{icon}}${{t}}</span>`;
          }}).join('');
          const matchTags = (s.matchedGoals && s.matchedGoals.length > 0)
            ? s.matchedGoals.map(g => `<span class="tag">${{g}}</span>`).join('')
            : '<span class="tag">保存方法の条件に一致</span>';
          html += `<div class="svc-card">
            <div class="svc-card-header">
              <h3 class="svc-card-name">${{s.name}}</h3>
            </div>
            <div class="svc-card-tags">${{tags}}</div>
            ${{s.price_html || ''}}
            <div class="svc-card-meta">一致した条件：${{matchTags}}</div>
            <div class="svc-card-footer">${{detail}} ${{link}}</div>
          </div>`;
        }}
        if (scored.length > TOP_N) {{
          html += `<p class="diag-result-note">他にも${{scored.length - TOP_N}}件が条件に一致しています。<a class="text-link" href="/ranking">比較一覧で全件見る →</a></p>`;
        }}
        html += '<p class="diag-result-note">※診断は簡易的なマッチングです。詳細は各サービスページをご確認ください。</p>';
      }}
      document.getElementById('result').style.display = 'block';
      document.getElementById('result').innerHTML = html;
    }}
    </script>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- トップページ ----------

def build_index_page(services, campaigns, aff_links, purpose_matches=None, coverage=None):
    svc_by_id = {s["id"]: s for s in services}
    num_services = len(services)
    # キャンペーン一覧（確認済みのものを優先して最大3件。未確認のものより先に見せる。
    # 表示文言はcampaigns.htmlと同じdiscount_type（実額）を使う。titleは汎用ラベルのため
    # 使わない＝FINAL_REDESIGN_SPEC.md 6章「TOPのキャンペーン表示に実額を反映」）。
    # 確認済み優先ソート（TOP・campaigns.htmlで同一ロジックを使用。変更時は両方見ること
    # ＝VISUAL_EXPRESSION_ANTI_GENERIC_IMPLEMENTATION_PLAN_2026_08_28.md 項目3/3b）。
    confirmed_first = sorted(campaigns, key=lambda c: c.get("requires_verification", True))
    camp_big_html = ""
    small_camp_items = ""
    if confirmed_first:
        c0 = confirmed_first[0]
        svc_name0 = svc_by_id.get(c0["service_id"], {}).get("name", "要確認")
        value_text0 = c0.get("discount_type") or c0.get("title", "要確認")
        camp_big_html = f'''
        <div class="campaign-pick-main">
          <p class="campaign-pick-label">PICK UP</p>
          <p class="campaign-pick-name">{esc(svc_name0)}</p>
          <p class="campaign-pick-value">{esc(value_text0)}</p>
          <a class="text-link" href="/campaigns">条件を見る →</a>
        </div>'''
        for c in confirmed_first[1:3]:
            svc_name = svc_by_id.get(c["service_id"], {}).get("name", "要確認")
            value_text = c.get("discount_type") or c.get("title", "要確認")
            small_camp_items += f'<li><a href="/campaigns">{esc(svc_name)}：{esc(value_text)}</a></li>'

    # TOP再設計：目的で探すを検証カバレッジより上位の「入口」として扱う（extra_classで色帯ゾーン化）。
    # 検証カバレッジは数字を含まない1行のtrust_line()に縮小し、詳細はverification.htmlに集約する
    # （VERIFICATION_COVERAGE_AND_GRID_IMPLEMENTATION_PLAN_2026_08_28.md A1/A4）。
    purpose_html = purpose_chips_block(purpose_matches, extra_class="purpose-section-top", with_anchor=True)
    trust_html = trust_line(coverage, num_services) if coverage else ""

    # ヒーローのリード文：ファーストビューでの差別化は数字の反復ではなく1文の信頼シグナルで伝える。
    # 数字（16・48・34）はTOPファーストビューではhero-figure以外に繰り返さない
    # （VERIFICATION_COVERAGE_AND_GRID_IMPLEMENTATION_PLAN_2026_08_28.md A2）。
    hero_lead = "価格・送料・初回キャンペーンを1項目ずつ、公式サイトで確認しています。"

    # 主要サービス一覧（9章のService Card簡易版）。TOP再設計により、視覚優先順位を
    # 「サービス名＋価格（検証バッジ同居）」→「向いている人（1行クランプ）」→「タグ」→CTA に変更
    # （TOP_LAYOUT_IMPLEMENTATION_PLAN_2026_08_28.md D節）。使用フィールドはtags/target/pricing/
    # aff_linksいずれも既存のまま、新規データ・新規ロジックは追加しない。
    # meal_form注記はTOPのみ非表示にする（詳細ページ＝pricing_detail_html等は無変更、_meal_form_note
    # 自体も削除しない）。
    # 公式サイトCTA（アフィリエイト）はUI_DESIGN_PRINCIPLES.md 5.2「情報が不足している段階では
    # 外部CTAを主役にしない」に合わせ、TOPでは.text-link（既存クラス）に変更。href/rel/aff_link()の
    # ロジック・遷移先は無変更（FINAL_REDESIGN_SPEC.md 6章の「比較→納得→信頼→公式クリックを最短化」）。
    # TOP段階開示（TOP_PROGRESSIVE_DISCLOSURE_FINAL_AUDIT_2026_08_28.md）。
    # servicesの並び順（services.json記載順）はそのまま使い、表示位置を4分割するだけで
    # 並び替え・フィルタ・スコアリングは一切行わない（評価・ランキングの新設ではない）。
    # 1〜4枚目=常時表示／5〜6枚目=PC(900px以上)のみ常時表示／7枚目以降=<details>で段階開示。
    def _svc_card_html(svc, extra_class=""):
        tags = "".join(_tag_html(t) for t in svc.get("tags", [])[:3])
        # 「誰向けか」を価格の次に提示する（食欲喚起UI監査§11.4 提案1。既存targetをそのまま使用、
        # 新規文言は作らない。空なら非表示）。1行クランプで密度を下げる（文言・データは無変更）。
        target_txt = "・".join(esc(t) for t in svc.get("target", []) if t)
        target_html = (f'<div class="svc-card-meta">向いている人：{target_txt}</div>'
                       if target_txt else "")
        # 1食あたりの価格を発見段階で提示し、予算スクリーニングを短時間化する
        # （UI_DESIGN_PRINCIPLES.md 3.1「TOP=発見」・6.2「比較は同軸」。ranking表と同じ
        # _price_inline_html を使うため表記はページ間で統一）。検証状態バッジを価格と一体化し、
        # 値単位の信頼（同4.2.1）を数値の根拠として見せる。未確認の値は控えめに「公式確認中」表示。
        price_inline = _price_inline_html(_pricing_of(svc))
        cls = f"svc-card svc-card-top {extra_class}".strip()
        return f"""
        <div class="{cls}" id="svc-{esc(svc['id'])}">
          <h3 class="svc-card-name"><a href="/services/{svc['id']}">{esc(svc['name'])}</a></h3>
          <div class="svc-card-price-row">{price_inline}</div>
          {target_html}
          <div class="svc-card-tags">{tags}</div>
          <div class="svc-card-footer">
            <a class="btn-primary" href="/services/{svc['id']}">詳しく見る</a>
            {aff_link(aff_links, svc['id'], label='公式サイトを確認', cls='text-link')}
          </div>
        </div>"""

    svc_primary = "".join(_svc_card_html(svc) for svc in services[:4])
    svc_extra = "".join(_svc_card_html(svc, extra_class="svc-extra-initial") for svc in services[4:6])
    svc_more_list = services[6:]
    svc_more = "".join(_svc_card_html(svc) for svc in svc_more_list)
    svc_more_block = (f"""
    <details class="svc-more">
      <summary>残り{len(svc_more_list)}社をすべて見る</summary>
      <div class="service-grid">{svc_more}</div>
    </details>""" if svc_more_list else "")
    # 任意の補助JS：フラグメント遷移で<details>内のカードを開く挙動はHTML標準でChromium系が
    # ネイティブ対応済みだが、非対応ブラウザでも確実に開くための補強（無くても機能は壊れない。
    # 既存の診断ツールと同種のインラインscriptで、新規の依存ライブラリは追加しない）。
    svc_more_anchor_script = ("""
    <script>
    (function(){
      var id = location.hash.slice(1);
      if (!id) return;
      var el = document.getElementById(id);
      var details = el && el.closest('details.svc-more');
      if (details && !details.open) details.open = true;
    })();
    </script>""" if svc_more_list else "")

    title = f"{SITE_NAME}｜宅配食の比較・初回キャンペーン情報"
    desc = SITE_DESC

    # main要素をcontainer-top（1200px）にするのはTOPのみ。他ページのpage_header呼び出しは
    # main_class未指定＝既定の"container"（1000px）のままで無変更（H節バリエーション2）。
    html = page_header(title, desc, "index.html", main_class="container-top")
    html += f"""
    <section class="hero">
      <h1>宅配食、どれを選べばいい？</h1>
      <p class="hero-lead">{hero_lead}</p>
      <div class="trust-stat" style="margin:0 0 var(--space-3);">
        <span class="hero-figure">{num_services}</span><span class="trust-label">社の宅配食サービスを掲載</span>
      </div>
      <div class="hero-actions">
        <a class="btn-primary" href="/tool/diagnosis">自分に合う宅配食を探す →</a>
        <a class="hero-sub-cta" href="/ranking">一覧で比較する →</a>
      </div>
    </section>

    {purpose_html}
    {trust_html}

    <div class="service-list-section">
      <h2 class="heading-rule">📊 主要サービス一覧</h2>
      <div class="service-grid">{svc_primary}{svc_extra}</div>
      {svc_more_block}
      <!-- TOP_P2_IMPROVEMENT_PLAN_2026_08_28.md 3a：Hero内CTA（発見段階の主役、btn-primary）とは
           役割を分け、一覧を見た後の救済導線として控えめなtext-linkのみで提示する。
           遷移先は既存の/tool/diagnosis.html、診断ロジック・クエリパラメータ等は無変更。 -->
      <p class="price-meta" style="margin-top:12px;">決めきれない場合は <a class="text-link" href="/tool/diagnosis">診断ツールで絞り込む →</a></p>
    </div>
    {svc_more_anchor_script}

    <div class="campaign-pick">
      <h2>🎯 初回キャンペーン・お試し情報（最新）</h2>
      <div class="campaign-pick-body">
        {camp_big_html}
        <ul class="feature-list campaign-pick-list">{small_camp_items or '<li>更新中</li>'}</ul>
      </div>
      <p style="margin-top:8px;"><a class="text-link" href="/campaigns">すべてのキャンペーンを見る →</a></p>
    </div>

    <div class="section-flat">
      <h2>このサイトのこだわり</h2>
      <ul class="feature-list">
        <li><strong>鮮度</strong>：価格・キャンペーン情報を毎週更新し、最終確認日を明記</li>
        <li><strong>公式確認</strong>：公式サイトの情報を確認したもののみ掲載し、未確認の項目は「公式確認中」と明示</li>
        <li><strong>目的別</strong>：一人暮らし・ダイエット・糖質制限など目的で比較できる</li>
      </ul>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 記事ページ：シェフの無添つくりおき 口コミ・評判 ----------

def build_article_chef_muten_kuchikomi(aff_links):
    """シェフの無添つくりおき 商標ロングテール記事（一次情報・公式サイト2026-08-26確認）"""
    title = "シェフの無添つくりおきの口コミ・評判を徹底検証！料金・送料・メニュー・「まずい？」まで【2026年8月】"
    desc = "シェフの無添つくりおきの料金（初回3,799円〜）・送料・メニュー・解約条件を公式情報で検証。「まずい？」の見方、口コミの確認方法、向いている人まで解説します。"
    html = page_header(title, desc, "articles/chef-muten-tukuritoki-kuchikomi.html")

    # A8 CTA（aff_link関数が actual_url を使用、rel=nofollow sponsored付き）
    cta = aff_link(aff_links, "chef-muten-tukuritoki", label="シェフの無添つくりおきを公式サイトで見る", cls="btn-primary")

    html += f"""
    <h1>シェフの無添つくりおきの口コミ・評判を徹底検証！料金・送料・メニュー・「まずい？」まで</h1>
    <p class="price-meta">最終確認日：2026年8月26日 ｜ 情報源：公式サイト（store.tavenal.com）・公式FAQ</p>

    <div class="card panel-accent">
      <h2>結論：どんな人に向いている？</h2>
      <p>「シェフの無添つくりおき」は、<strong>添加物（保存料・化学調味料）を一切使わない無添加のお惣菜を、週替わりで届けてくれる冷蔵の惣菜宅配</strong>です。</p>
      <p>以下のような人に向いていると判断できます（公式情報に基づく）。</p>
      <ul class="feature-list">
        <li><strong>小さな子どもがいる家庭</strong>：無添加・やさしい味付けで、お子様に安心して食べさせたい人</li>
        <li><strong>毎日の献立・調理の時間を減らしたい人</strong>：レンジで温めるだけで食卓が完成</li>
        <li><strong>無添加にこだわりたい人</strong>：シェフ手作り・添加物不使用に特化</li>
      </ul>
      <p>一方、以下の人は合わない可能性があります。</p>
      <ul class="feature-list">
        <li><strong>一人暮らし</strong>：1セットが「大人2名+子ども」の家族向け想定で、量が多い（公式FAQで「一人暮らしには量が多い？」という質問がある）</li>
        <li><strong>メニューを自分で選びたい人</strong>：メニューはおまかせ・週替わりで指定不可</li>
        <li><strong>冷凍で長く保存したい人</strong>：冷蔵お届けで消費期限は4日</li>
      </ul>
      <div style="margin-top:12px;">{cta}</div>
    </div>

    <div class="card">
      <h2>シェフの無添つくりおきとは？（基本情報）</h2>
      <table>
        <tr><th>運営</th><td>株式会社タベナル（公式サイトより）</td></tr>
        <tr><th>サービス内容</th><td>一流シェフが化学調味料を一切使わず手作りするお惣菜を、週替わりで宅配</td></tr>
        <tr><th>特徴</th><td>添加物不使用（保存料・化学調味料不使用）／専属の管理栄養士が栄養設計を監修</td></tr>
        <tr><th>お届け形態</th><td>冷蔵状態でお届け（冷凍ではない）</td></tr>
        <tr><th>消費期限</th><td>お届けから4日間</td></tr>
        <tr><th>利用方法</th><td>毎週の定期購入。レンジで温めるだけ</td></tr>
        <tr><th>確認日</th><td>2026年8月26日（公式サイト）</td></tr>
      </table>
      <p class="price-meta">※同じ運営グループの「FIT FOOD HOME」会員はログインして注文可能と公式サイトに記載があります。</p>
    </div>

    <div class="card">
      <h2>料金プランを比較（公式情報）</h2>
      <table>
        <tr><th></th><th>食卓サポートプラン</th><th>食卓おまかせプラン</th></tr>
        <tr><td><strong>想定家族</strong></td><td>大人2名+お子様1名（幼児）</td><td>大人2名+お子様2名（小中学生）</td></tr>
        <tr><td><strong>想定日数</strong></td><td>夕食2回分</td><td>夕食3回分</td></tr>
        <tr><td><strong>メニュー数</strong></td><td>主菜2種+副菜3種（5個）</td><td>主菜3種（各2パック）+副菜6種（9個）</td></tr>
        <tr><td><strong>1個あたり内容量</strong></td><td>150〜300g程度</td><td>150〜600g程度</td></tr>
        <tr><td><strong>通常価格（2回目以降）</strong></td><td>5,173円（税込）+送料990円</td><td>13,607円（税込）+送料990円</td></tr>
        <tr><td><strong>初回限定価格</strong></td><td><strong>3,799円（税込・送料無料）</strong></td><td><strong>9,980円（税込・送料無料）</strong></td></tr>
      </table>
      <p class="price-meta">初回価格は「26%OFF」の限定価格で、ご契約者様1回目のご注文のみ適用（公式FAQより）。※価格は2026年8月26日時点の公式情報です。</p>
      <div style="margin-top:12px;">{cta}</div>
    </div>

    <div class="card">
      <h2>送料は？</h2>
      <ul class="feature-list">
        <li>通常（2回目以降）：<strong>1回あたり990円（税込）</strong></li>
        <li>初回：<strong>送料無料</strong>（初回限定価格に含まれる）</li>
      </ul>
      <p>送料が毎回かかる点は、費用を計算する際に注意が必要です。1回あたり990円を加味した上で、総額を比較しましょう。</p>
    </div>

    <div class="card">
      <h2>メニューと内容量（週替わり・指定不可）</h2>
      <p>メニューは<strong>週替わり</strong>で、お客様自身での指定はできません（公式FAQより）。栄養や食材のバランスを考慮した献立が届きます。</p>
      <ul class="feature-list">
        <li>主菜・副菜をバランスよく組み合わせた構成</li>
        <li>レンジで温めてお皿に盛り付けるだけでOK</li>
        <li>余った分は冷蔵保存（開封後）・一部メニューは冷凍保存も可能</li>
        <li>お弁当のおかずとしても活用できる</li>
      </ul>
    </div>

    <div class="card">
      <h2>「まずい？」の真相を考える（断定しない）</h2>
      <p>当サイトは現時点で実際に試食した独自レビューは保有していません。そのため「美味しい」「まずい」と断定はしませんが、公式情報から判断材料を整理します。</p>
      <ul class="feature-list">
        <li>一流シェフが手作りしている（公式）</li>
        <li>無添加・やさしい味付けをコンセプトにしている（公式）</li>
        <li>味の感じ方は個人差が大きいため、<strong>初回限定価格（26%OFF・送料無料）で実際に試す</strong>のが確実</li>
      </ul>
      <p>冷蔵お届けのため、冷凍タイプの宅配食とは食感・保存方法が異なる点には注意してください。</p>
    </div>

    <div class="card">
      <h2>メリット・デメリット（公式情報から整理）</h2>
      <div class="pros-cons">
        <div>
          <strong>メリット</strong>
          <ul class="feature-list">
            <li>無添加（保存料・化学調味料不使用）で安心</li>
            <li>シェフ手作り・管理栄養士監修</li>
            <li>週替わりで飽きにくい</li>
            <li>レンジ調理のみで時短・後片付けが楽</li>
            <li>2回目以降はいつでも休止（解約）可能・違約金なし</li>
            <li>初回は26%OFF+送料無料で試せる</li>
          </ul>
        </div>
        <div>
          <strong>デメリット・注意点</strong>
          <ul class="feature-list">
            <li>メニュー指定不可（おまかせ・週替わり）</li>
            <li>冷蔵お届けのため消費期限が4日と短い</li>
            <li>毎回の送料990円がかかる</li>
            <li>家族向けの量で一人暮らしには多い可能性</li>
            <li>冷凍の宅配食と比べると長期保存には向かない</li>
          </ul>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>解約・スキップ・休止の条件（公式FAQより）</h2>
      <table>
        <tr><th>項目</th><th>内容</th></tr>
        <tr><td>初回お届け分</td><td>キャンセル不可（初回限定価格のため）</td></tr>
        <tr><td>2回目以降のスキップ</td><td>可能。お届けの6日前までに手続き（九州・島根・青森は7日前）</td></tr>
        <tr><td>休止（解約）</td><td>2回目以降はいつでも可能・違約金なし</td></tr>
        <tr><td>退会</td><td>定期休止手続き後、退会申請。完了まで約1週間</td></tr>
      </table>
      <p class="price-meta">初回はキャンセル不可のため、初回分は必ず受け取る前提で申し込んでください。2回目以降はいつでも解約できます。</p>
    </div>

    <div class="card panel-accent">
      <h2>まとめ：自分に合うかどうかの判断基準</h2>
      <p>購入前に確認しておきたいポイントは次の3点です。</p>
      <ul class="feature-list">
        <li>家族構成に合った量か（想定家族・想定日数は上記の料金プラン表を参照）</li>
        <li>週替わりメニューの好みに合うか（メニュー指定は不可）</li>
        <li>消費期限4日以内に食べ切れるか（冷蔵お届け）</li>
      </ul>
      <p class="price-meta">当サイトは他サイトの口コミ文を転載していません。判断は公式情報と、ご自身の家族構成・食習慣に照らして行ってください。</p>
      <p>初回は26%OFF+送料無料（3,799円〜）で試せます。</p>
      <div style="margin-top:12px;">{cta}</div>
      <p style="font-size:12px;color:#999;margin-top:8px;">※当サイトはアフィリエイト広告（PR）を含みます。リンク経由で購入すると当サイトに報酬が入ることがあります。</p>
    </div>

    <div style="margin-top:16px;">
      <a class="btn-secondary" href="/services/chef-muten-tukuritoki">シェフの無添つくりおきの詳細ページを見る</a>
      <a class="btn-secondary" href="/ranking">宅配食の比較一覧を見る</a>
      <a class="btn-secondary" href="/campaigns">初回キャンペーン一覧を見る</a>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 検証状況ダッシュボード ----------

def build_verification_dashboard(services, shipping_by_id, sources_by_id, coverage=None):
    """11社×価格・送料・キャンペーンの確認状況を1ページに集約するダッシュボード。
    data/sources.jsonは直接参照・列挙しない。確認状態判定関数（_pricing_status/
    _shipping_status/_campaign_status）とprice_cell_html()/source_link()をそのまま
    再利用するだけで、ASP内部情報・報酬額・program_id等はいずれの関数からも出力されない
    （source_linkが返すのはurl/confirmed_atのみで、sources.jsonのnoteフィールドは
    一切参照しない）。新しいスコアリング・ランキング付けは行わない。
    PHASE3_IMPLEMENTATION_PLAN.md 3.2節。"""
    rows = []
    for svc in services:
        s_id = svc["id"]
        price_html = price_cell_html(_pricing_of(svc), sources_by_id)
        shipping_row = (shipping_by_id or {}).get(s_id)
        ship_html = f"{vstatus_badge(_shipping_status(shipping_row))}{source_link(sources_by_id, (shipping_row or {}).get('source_id'))}"
        camp = svc.get("first_time_campaign", {})
        camp_html = f"{vstatus_badge(_campaign_status(camp))}{source_link(sources_by_id, camp.get('source_id'))}"
        rows.append(f"""
        <tr>
          <td><a href="/services/{s_id}"><strong>{esc(svc['name'])}</strong></a></td>
          <td>{price_html}</td>
          <td>{ship_html}</td>
          <td>{camp_html}</td>
        </tr>""")

    num_services = len(services)
    title = f"全{num_services}社の価格・送料・キャンペーン確認状況一覧"
    desc = f"{SITE_NAME}が{num_services}社それぞれの価格・送料・初回キャンペーンをどこまで公式一次情報で確認できているかを一覧で開示します。確認済みの項目には出典と確認日を明記しています。"

    html = page_header(title, desc, "verification.html")
    html += f"""
    <h1>全{num_services}社の価格・送料・キャンペーン確認状況</h1>
    <p>各サービスの価格・送料・初回キャンペーンについて、公式一次情報でどこまで確認できているかを一覧にしています。確認済み・算出値の項目には出典リンクと確認日を付けています。未確認の項目には出典・確認日を表示していません（存在しない裏付けを示さないため）。</p>
    {trust_panel(coverage, num_services, link_to_dashboard=False) if coverage else ""}
    {vstatus_legend(link_to_dashboard=False)}
    {mobile_scroll_hint()}
    <div class="card">
      <table>
        <tr><th>サービス</th><th>価格</th><th>送料</th><th>初回キャンペーン</th></tr>
        {''.join(rows)}
      </table>
    </div>
    <p class="price-meta">※このページはスコアやランキングを付けるものではなく、当サイトが確認できている範囲をそのまま開示するものです。最新情報は必ず公式サイトでご確認ください。</p>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- 404ページ ----------

def build_404_page():
    gtm_head = _gtm_head_block()
    gtm_body = _gtm_body_block()
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{gtm_head}
<title>ページが見つかりません | {SITE_NAME}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="{FAVICON_DATA_URI}">
<style>
body {{ font-family:"Hiragino Kaku Gothic ProN","Meiryo",sans-serif; background:#faf7f5; color:#222; text-align:center; padding:60px 16px; }}
h1 {{ font-size:1.5rem; margin-bottom:16px; }}
p {{ margin-bottom:16px; color:#666; }}
a {{ color:#e8552d; }}
.footer {{ margin-top:48px; font-size:12px; color:#999; }}
</style>
</head>
<body>
{gtm_body}
<h1>ページが見つかりません（404）</h1>
<p>お探しのページは移動したか、存在しない可能性があります。</p>
<p><a href="/">ホームに戻る</a> ｜ <a href="/ranking">宅配食の比較一覧を見る</a> ｜ <a href="/campaigns">初回キャンペーンを見る</a></p>
<p class="footer">
<a href="/privacy" style="color:#999;margin:0 6px;">プライバシーポリシー</a>｜
<a href="/disclaimer" style="color:#999;margin:0 6px;">免責事項</a>｜
<a href="/operator" style="color:#999;margin:0 6px;">運営者情報</a>｜
<a href="/contact" style="color:#999;margin:0 6px;">お問い合わせ</a>
</p>
</body>
</html>"""


# ---------- 法務ページ（プライバシー・免責・運営者・お問い合わせ） ----------

def _operator_name():
    return OPERATOR.get("name", "").strip() or "（運営者名は設定準備中です）"


def _operator_email():
    return OPERATOR.get("email", "").strip()


def build_privacy_page():
    title = "プライバシーポリシー"
    desc = f"{SITE_NAME}（宅配食比較サイト）のプライバシーポリシー。個人情報の取り扱い、Cookie・アクセス解析、アフィリエイト広告について説明します。"
    html = page_header(title, desc, "privacy.html")
    html += f"""
    <h1>プライバシーポリシー</h1>
    <p>{SITE_NAME}（以下「当サイト」）は、個人情報の保護に関する法律および関連法令を遵守し、以下の方針に基づいて個人情報を適正に取り扱います。</p>

    <div class="card">
      <h2>1. 個人情報の収集について</h2>
      <p>当サイトは、現時点ではユーザー登録・入力フォームによる個人情報の収集は行っておりません。</p>
      <p>お問い合わせをいただいた際に、メールアドレスや氏名などの情報を送信いただく場合があります。これらの情報は、お問い合わせへの対応にのみ利用し、それ以外の目的には利用いたしません。</p>
    </div>

    <div class="card">
      <h2>2. Cookieについて</h2>
      <p>当サイトでは、以下の目的でCookieを使用する場合があります。</p>
      <ul class="feature-list">
        <li>アクセス解析（サイトの利用状況の把握）</li>
        <li>広告配信（訪問履歴に基づく広告の表示）</li>
        <li>アフィリエイトプログラムの成果判定</li>
      </ul>
      <p>Cookieには氏名・住所・電話番号などの個人を特定する情報は含まれません。Cookieの無効化は、お使いのブラウザの設定で行うことができます。</p>
    </div>

    <div class="card">
      <h2>3. アクセス解析について</h2>
      <p>当サイトでは、サイト改善のためにアクセス解析ツール（Google Analytics 等）を利用する場合があります。この際、Cookieを通じて、お使いのブラウザの種類・OS・アクセス日時・参照元などの情報が収集されることがありますが、これらの情報から個人を特定することはできません。</p>
      <p>Google Analyticsによるデータ収集を無効化したい場合は、Googleが提供するオプトアウトアドオンをご利用ください。</p>
    </div>

    <div class="card">
      <h2>4. アフィリエイト広告について</h2>
      <p>当サイトは、アフィリエイトプログラム（A8.net、afb、アクセストレード 等）に参加しています。記事内・ページ内のリンクから商品・サービスを購入された場合、当サイトに成果報酬が支払われることがあります。</p>
      <p>アフィリエイト広告の成果判定にはCookieが使用される場合がありますが、個人を特定する情報は収集されません。</p>
    </div>

    <div class="card">
      <h2>5. 個人情報の第三者提供について</h2>
      <p>当サイトは、法令に基づく場合を除き、ご提供いただいた個人情報を事前の同意なく第三者に提供いたしません。</p>
    </div>

    <div class="card">
      <h2>6. お問い合わせ</h2>
      <p>個人情報の取り扱いに関するお問い合わせは、<a href="/contact">お問い合わせページ</a>よりご連絡ください。</p>
    </div>

    <div class="card">
      <h2>7. ポリシーの変更</h2>
      <p>本ポリシーの内容は、法令の変更やサイトの運営方針に応じて予告なく変更する場合があります。変更後の内容は、本ページに掲載した時点で効力を生じるものとします。</p>
      <p>最終更新日: 2026-08-26</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


def build_disclaimer_page():
    title = "免責事項"
    desc = f"{SITE_NAME}（宅配食比較サイト）の免責事項。情報の正確性、アフィリエイト広告、リンク先サイトについての注意事項を説明します。"
    html = page_header(title, desc, "disclaimer.html")
    html += f"""
    <h1>免責事項</h1>

    <div class="card">
      <h2>1. 情報の正確性・最新性について</h2>
      <p>当サイトでは、宅配食サービスの価格・キャンペーン・送料・メニューなどの情報を、できる限り正確かつ最新の状態で提供するよう努めています。ただし、各サービスの情報は頻繁に変更されるため、当サイトの情報が必ずしも最新・正確であることを保証するものではありません。</p>
      <p><strong>実際の価格・条件・キャンペーン内容は、必ず各サービスの公式サイトでご確認ください。</strong></p>
    </div>

    <div class="card">
      <h2>2. アフィリエイト広告について</h2>
      <p>当サイトはアフィリエイト広告（PR）を含みます。記事内・ページ内のリンクから商品・サービスを購入・申し込んだ場合、当サイトに成果報酬が支払われることがあります。</p>
      <p>アフィリエイトリンクの有無にかかわらず、当サイトの記事・比較内容は中立性を保って作成するよう努めていますが、すべての情報が完全に中立的であることを保証するものではありません。</p>
    </div>

    <div class="card">
      <h2>3. 当サイトはサービス提供者ではありません</h2>
      <p>当サイトは、紹介する宅配食サービスの運営会社・提供者ではありません。商品・サービスの品質、配送、契約、解約などのトラブルについては、各サービスの公式窓口にお問い合わせください。</p>
    </div>

    <div class="card">
      <h2>4. 損害の責任について</h2>
      <p>当サイトの情報の利用によって生じたいかなる損害（直接損害・間接損害を問いません）についても、当サイトは一切の責任を負いかねます。情報の利用は利用者ご自身の判断と責任で行ってください。</p>
    </div>

    <div class="card">
      <h2>5. リンク先サイトについて</h2>
      <p>当サイトからリンクされている外部サイト（公式サイト・ASP・その他）の内容、および外部サイトで提供される情報・サービスについて、当サイトは責任を負いません。</p>
    </div>

    <div class="card">
      <h2>6. 情報の更新について</h2>
      <p>当サイトの情報は毎週更新することを目標としていますが、更新頻度や最終更新日時によって最新性は変動します。各ページに記載された最終更新日をご確認ください。</p>
      <p>最終更新日: 2026-08-26</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


def build_operator_page():
    title = "運営者情報"
    desc = f"{SITE_NAME}の運営者情報。サイトの運営目的、連絡先、各サービスとの関係性について説明します。"
    email = _operator_email()
    contact_html = f'<a href="mailto:{esc(email)}">{esc(email)}</a>' if email else "（お問い合わせメールアドレスは設定準備中です）"
    html = page_header(title, desc, "operator.html")
    html += f"""
    <h1>運営者情報</h1>

    <div class="card">
      <h2>運営者</h2>
      <table>
        <tr><th>運営者名</th><td>{esc(_operator_name())}</td></tr>
        <tr><th>運営形態</th><td>{esc(OPERATOR.get("note", "個人運営"))}</td></tr>
        <tr><th>お問い合わせ</th><td>{contact_html}</td></tr>
      </table>
    </div>

    <div class="card">
      <h2>サイトの目的</h2>
      <p>当サイトは、宅配食・宅配弁当サービスを検討されている方に向けて、各サービスの特徴・料金・初回キャンペーン情報を比較して提供することを目的としています。</p>
      <p>情報の鮮度を保つため、価格・キャンペーン情報は定期的に更新し、各ページに最終確認日を記載しています。</p>
    </div>

    <div class="card">
      <h2>各サービスとの関係性</h2>
      <p>当サイトは、紹介する各宅配食サービス（nosh、ワタミの宅食ダイレクト、三ツ星ファーム 等）の公式サイト・運営会社とは一切関係のない、独立した第三者の個人サイトです。</p>
      <p>当サイトはアフィリエイトプログラムに参加しており、リンク経由での購入により報酬を得る場合があります。</p>
    </div>

    <div class="card">
      <h2>免責</h2>
      <p>当サイトの情報は、正確性・最新性に努めていますが、その完全性を保証するものではありません。詳細は<a href="/disclaimer">免責事項</a>をご確認ください。</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


def build_contact_page():
    title = "お問い合わせ"
    desc = f"{SITE_NAME}へのお問い合わせ方法。誤情報のご指摘、削除依頼、その他のご連絡を受け付けています。"
    email = _operator_email()
    if email:
        contact_html = f'<p>以下のメールアドレスまでご連絡ください。</p><p style="font-size:1.1rem;"><a href="mailto:{esc(email)}">{esc(email)}</a></p>'
    else:
        contact_html = '<p>お問い合わせメールアドレスは設定準備中です。公開までしばらくお待ちください。</p>'
    html = page_header(title, desc, "contact.html")
    html += f"""
    <h1>お問い合わせ</h1>

    <div class="card">
      <h2>お問い合わせ方法</h2>
      {contact_html}
      <p class="price-meta">返信には数日かかる場合があります。あらかじめご了承ください。</p>
    </div>

    <div class="card">
      <h2>お問い合わせいただける内容</h2>
      <ul class="feature-list">
        <li>記事・情報の誤りについてのご指摘</li>
        <li>掲載情報の削除依頼（当サイトが独自に作成したコンテンツに限ります）</li>
        <li>サイトに関するご質問・ご意見</li>
      </ul>
    </div>

    <div class="card">
      <h2>ご注意</h2>
      <p>当サイトは各宅配食サービスの運営会社ではありません。サービス自体の注文・解約・配送に関するお問い合わせは、各サービスの公式窓口にお願いいたします。</p>
    </div>
    """
    html += page_footer(LAST_VERIFIED_DATE)
    return html


# ---------- sitemap / robots ----------

def build_sitemap(pages):
    """pagesは実ファイル書き込みパス（".html"付き）のリスト（generators.py）。
    <loc>は拡張子なし正規URLに正規化する（page_header()のcanonical正規化とロジックを揃える。
    URL_NORMALIZATION_AUDIT_2026_08_28.md）。"""
    urls = []
    for p in pages:
        loc_path = "" if p == "index.html" else p.removesuffix(".html")
        urls.append(f"  <url>\n    <loc>{SITE_URL}/{loc_path}</loc>\n    <lastmod>{LAST_VERIFIED_DATE}</lastmod>\n  </url>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""


def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""
