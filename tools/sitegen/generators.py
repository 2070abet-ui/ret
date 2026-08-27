"""
宅食図鑑 静的サイト生成 - 生成の司令塔
「何を何件生成するか」を決める唯一の場所。ページ描画そのものは templates.py に委譲する。
"""
from sitegen import data
from sitegen import templates


def _tag_set(svc):
    return set(svc.get("tags", [])) | set(svc.get("target", []))


def meal_form_categories(meal_form_text):
    """自由文のmeal_form（例:「冷凍（レンジで温めるだけ）」「冷凍 / 冷蔵」「日配（保冷ボックス）」）を
    診断ツールで絞り込める3カテゴリ（冷凍/冷蔵/日配）に正規化する。新規データ収集は不要
    （既存のmeal_formフィールドの文字列判定のみ）。PHASE2_IMPLEMENTATION_PLAN.md 8.1章。"""
    text = meal_form_text or ""
    cats = []
    if "冷凍" in text:
        cats.append("冷凍")
    if "冷蔵" in text:
        cats.append("冷蔵")
    if "日配" in text:
        cats.append("日配")
    return cats


# 目的別導線カード（TOP・ranking.htmlで共有するコンポーネント）の定義。
# 既存のtags/target文字列に対する部分一致のみで、新規データフィールドは追加しない。
# 「減塩」は表記ゆれ（減塩／塩分控えめ／塩分制限）が既存データに複数存在するため、
# 同義語をOR条件でまとめる（正規化用の新規キーは作らない）。
# FINAL_REDESIGN_SPEC.md 6章・7章。
PURPOSE_CATEGORIES = [
    ("mutenka", "無添加にこだわりたい", ["無添加"]),
    ("koreisha", "高齢の家族に", ["高齢者"]),
    ("gensen", "減塩・塩分が気になる", ["減塩", "塩分控えめ", "塩分制限"]),
    ("hitorigurashi", "一人暮らし", ["一人暮らし"]),
    ("diet", "ダイエット", ["ダイエット"]),
]


def compute_purpose_matches(services, max_items=4):
    """目的別カテゴリごとに、tags+targetのいずれかに該当語を含むサービスを抽出する。
    該当が無いカテゴリはそもそも出力に含めない（空のカードを出さない）。
    戻り値: [(カテゴリID, ラベル, [該当service, ...]), ...]"""
    result = []
    for cat_id, label, terms in PURPOSE_CATEGORIES:
        matched = [s for s in services if _tag_set(s) & set(terms)]
        if matched:
            result.append((cat_id, label, matched[:max_items]))
    return result


def compute_verification_coverage(services, shipping_by_id):
    """全11社×価格/送料/初回キャンペーンの確認状況を集計する。
    CONFIRMEDのみを「確認済み」件数に数え、DERIVED/PENDING/UNCOLLECTEDとは区別を保つ
    （既存の4状態の区別を壊さない。REDESIGN_IMPLEMENTATION指示：全項目確認済み判定と
    同じ基準をトップページ・ranking・verificationの集計表示に一貫して使う）。"""
    counts = {"confirmed": 0, "derived": 0, "pending": 0, "uncollected": 0}
    for svc in services:
        for status in (
            templates._price_status(svc.get("price_plan", {})),
            templates._shipping_status(shipping_by_id.get(svc["id"])),
            templates._campaign_status(svc.get("first_time_campaign", {})),
        ):
            counts[status] = counts.get(status, 0) + 1
    counts["total"] = sum(counts.values())
    return counts


def compute_fully_verified_ids(services, shipping_by_id):
    """価格・送料・初回キャンペーンの3項目すべてがCONFIRMED（算出値・確認中・未収集は
    含めない）のサービスIDの集合を返す。序列化には使わない、事実表示のバッジ用のみ。
    FINAL_REDESIGN_SPEC.md 4章・5章。"""
    result = set()
    for svc in services:
        if (templates._price_status(svc.get("price_plan", {})) == "confirmed"
                and templates._shipping_status(shipping_by_id.get(svc["id"])) == "confirmed"
                and templates._campaign_status(svc.get("first_time_campaign", {})) == "confirmed"):
            result.add(svc["id"])
    return result


def compute_comparison_links(comp_pairs, svc_by_id):
    """比較ページ（config/comparisons.json駆動）のURLを、サービス詳細ページ・ranking.html
    への内部リンクとして使える形に整理する。新規の比較ロジック・新規ページは作らず、
    既存3ペアをそのまま参照するだけ。PHASE3_IMPLEMENTATION_PLAN.md 1.4節（比較ページの内部リンク孤立の解消）。
    戻り値: (サービスIDごとの[(相手サービス名, 比較ページURL), ...], 全ペアの[(a名, b名, URL), ...])"""
    by_service = {}
    pairs_out = []
    for a_id, b_id in comp_pairs:
        if a_id not in svc_by_id or b_id not in svc_by_id:
            continue
        url = f"/comparisons/{a_id}-vs-{b_id}.html"
        a_name, b_name = svc_by_id[a_id]["name"], svc_by_id[b_id]["name"]
        pairs_out.append((a_name, b_name, url))
        by_service.setdefault(a_id, []).append((b_name, url))
        by_service.setdefault(b_id, []).append((a_name, url))
    return by_service, pairs_out


def compute_related(services, aff_links, min_score=2, max_items=3):
    """関連サービス（tags+targetの単純な集合演算のみ。汎用matching engineではない）。
    一致数 >= min_score のみ候補にし、スコア降順・A8提携承認済み優先・services.json記載順
    でタイブレークして上位max_items件を返す。一致0〜1件のサービスは候補に含めない。
    PHASE1_IMPLEMENTATION_PLAN.md 7章のアルゴリズムをそのまま実装したもの。"""
    order_index = {s["id"]: i for i, s in enumerate(services)}
    result = {}
    for svc in services:
        a = _tag_set(svc)
        candidates = []
        for other in services:
            if other["id"] == svc["id"]:
                continue
            score = len(a & _tag_set(other))
            if score < min_score:
                continue
            approved = 1 if aff_links.get(other["id"], {}).get("actual_url") else 0
            candidates.append((score, approved, order_index[other["id"]], other))
        candidates.sort(key=lambda t: (-t[0], -t[1], t[2]))
        result[svc["id"]] = [c[3] for c in candidates[:max_items]]
    return result


def main():
    services, campaigns, shipping, sources, aff_links = data.load_data()
    shipping_by_id = {s["service_id"]: s for s in shipping}
    sources_by_id = {s["id"]: s for s in sources}
    related_by_id = compute_related(services, aff_links)
    svc_by_id = {s["id"]: s for s in services}
    comp_pairs = data.load_comparison_pairs()
    comparison_links_by_id, comparison_pairs_flat = compute_comparison_links(comp_pairs, svc_by_id)
    # meal_formを正規化した3カテゴリ（冷凍/冷蔵/日配）を追加した複製リスト（元のservicesは変更しない）。
    # 診断ツールとranking.htmlの保存方法フィルタで同じ正規化ロジックを共有する
    # （PHASE3_IMPLEMENTATION_PLAN.md 2章：新しいmatching engineは作らず既存ロジックを再利用）。
    services_with_mealform = [dict(s, meal_form_categories=meal_form_categories(s.get("meal_form"))) for s in services]
    purpose_matches = compute_purpose_matches(services)
    coverage = compute_verification_coverage(services, shipping_by_id)
    fully_verified_ids = compute_fully_verified_ids(services, shipping_by_id)
    out_dir = data.OUT_DIR

    # 出力先クリーン
    # 外部プロセス（例: python -m http.server）が OUT_DIR をCWDとして使用していると
    # Windows ではディレクトリ自体を削除できないため、その場合は中身を削除して上書き再生成する。
    if out_dir.exists():
        import shutil
        try:
            shutil.rmtree(out_dir)
        except OSError:
            for _child in out_dir.iterdir():
                if _child.is_dir():
                    shutil.rmtree(_child, ignore_errors=True)
                else:
                    _child.unlink(missing_ok=True)
    (out_dir / "services").mkdir(parents=True)
    (out_dir / "comparisons").mkdir(parents=True)
    (out_dir / "tool").mkdir(parents=True)

    pages = []

    # トップ
    (out_dir / "index.html").write_text(
        templates.build_index_page(services, campaigns, aff_links, purpose_matches, coverage),
        encoding="utf-8")
    pages.append("index.html")

    # 比較一覧（旧称ランキング。FINAL_REDESIGN_SPEC.md 5章）
    (out_dir / "ranking.html").write_text(
        templates.build_ranking_page(
            services_with_mealform, campaigns, aff_links, comparison_pairs_flat,
            purpose_matches, coverage, fully_verified_ids, sources_by_id),
        encoding="utf-8")
    pages.append("ranking.html")

    # キャンペーン
    (out_dir / "campaigns.html").write_text(templates.build_campaigns_page(campaigns, services, aff_links), encoding="utf-8")
    pages.append("campaigns.html")

    # 診断ツール
    (out_dir / "tool" / "diagnosis.html").write_text(templates.build_diagnosis_tool(services_with_mealform, aff_links), encoding="utf-8")
    pages.append("tool/diagnosis.html")

    # 記事ページ（シェフの無添つくりおき 口コミ・評判）
    (out_dir / "articles").mkdir(parents=True, exist_ok=True)
    (out_dir / "articles" / "chef-muten-tukuritoki-kuchikomi.html").write_text(
        templates.build_article_chef_muten_kuchikomi(aff_links), encoding="utf-8")
    pages.append("articles/chef-muten-tukuritoki-kuchikomi.html")

    # 法務ページ
    legal_pages = [
        ("privacy.html", templates.build_privacy_page),
        ("disclaimer.html", templates.build_disclaimer_page),
        ("operator.html", templates.build_operator_page),
        ("contact.html", templates.build_contact_page),
    ]
    for fname, fn in legal_pages:
        (out_dir / fname).write_text(fn(), encoding="utf-8")
        pages.append(fname)

    # サービス個別ページ
    for svc in services:
        (out_dir / "services" / f"{svc['id']}.html").write_text(
            templates.build_service_page(
                svc, aff_links, shipping_by_id, related_by_id.get(svc["id"], []), sources_by_id,
                comparison_links_by_id.get(svc["id"], [])),
            encoding="utf-8")
        pages.append(f"services/{svc['id']}.html")

    # 検証状況ダッシュボード（11社×価格・送料・キャンペーンの確認状況を1ページに集約。
    # sources.jsonは直接参照せず、既存のvstatus/source_linkロジックのみを再利用する。
    # PHASE3_IMPLEMENTATION_PLAN.md 3.2節）
    (out_dir / "verification.html").write_text(
        templates.build_verification_dashboard(services, shipping_by_id, sources_by_id, coverage),
        encoding="utf-8")
    pages.append("verification.html")

    # 比較ページ（config/comparisons.json 駆動。中身のペアは従来のハードコードと同一）
    for a_id, b_id in comp_pairs:
        if a_id in svc_by_id and b_id in svc_by_id:
            (out_dir / "comparisons" / f"{a_id}-vs-{b_id}.html").write_text(
                templates.build_comparison_page(svc_by_id[a_id], svc_by_id[b_id], aff_links, sources_by_id), encoding="utf-8")
            pages.append(f"comparisons/{a_id}-vs-{b_id}.html")

    # 404 / sitemap / robots
    (out_dir / "404.html").write_text(templates.build_404_page(), encoding="utf-8")
    (out_dir / "sitemap.xml").write_text(templates.build_sitemap(pages), encoding="utf-8")
    (out_dir / "robots.txt").write_text(templates.build_robots(), encoding="utf-8")

    # Google Search Console 所有権確認ファイル（HTMLファイル方式）
    # 内容はGoogleが指定したファイル名そのもの（標準フォーマット）。sitemapには含めない。
    gsc_verify_files = {
        "googlef4d8b0b633188b1b.html": "google-site-verification: googlef4d8b0b633188b1b.html",
    }
    for _fname, _fcontent in gsc_verify_files.items():
        (out_dir / _fname).write_text(_fcontent, encoding="utf-8")

    print(f"生成完了: {len(pages)} ページ + sitemap.xml + robots.txt")
    print(f"出力先: {out_dir}")
