"""
ScrapeBench 静的サイト生成 - 生成の司令塔
「何を何件生成するか」を決める唯一の場所。ページ描画は templates.py に委譲する。
"""
import shutil

from sitegen import data
from sitegen import templates
from sitegen import validate


def main():
    bd = data.load_benchmark_data()
    out = data.OUT_DIR

    # 出力先クリーン（WindowsでCWDとして使用中でも削除できるよう中身を削除して上書き）
    if out.exists():
        try:
            shutil.rmtree(out)
        except OSError:
            for child in out.iterdir():
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)

    subdirs = ["benchmarks", "methodology", "about", "privacy", "terms", "disclaimer", "contact"]
    for d in subdirs:
        (out / d).mkdir(parents=True, exist_ok=True)

    pages = []

    # Top
    (out / "index.html").write_text(templates.build_index_page(bd), encoding="utf-8")
    pages.append("index.html")

    # ベンチマーク一覧
    (out / "benchmarks" / "index.html").write_text(templates.build_benchmarks_page(bd), encoding="utf-8")
    pages.append("benchmarks/index.html")

    # メソドロジー
    (out / "methodology" / "index.html").write_text(templates.build_methodology_page(bd), encoding="utf-8")
    pages.append("methodology/index.html")

    # インフォ・法務ページ
    info_pages = [
        ("about/index.html", templates.build_about_page),
        ("privacy/index.html", templates.build_privacy_page),
        ("terms/index.html", templates.build_terms_page),
        ("disclaimer/index.html", templates.build_disclaimer_page),
        ("contact/index.html", templates.build_contact_page),
    ]
    for fname, fn in info_pages:
        (out / fname).write_text(fn(bd), encoding="utf-8")
        pages.append(fname)

    # 404 / sitemap / robots
    (out / "404.html").write_text(templates.build_404_page(bd), encoding="utf-8")
    pages.append("404.html")
    (out / "sitemap.xml").write_text(templates.build_sitemap(pages, bd), encoding="utf-8")
    (out / "robots.txt").write_text(templates.build_robots(bd), encoding="utf-8")

    print(f"生成完了: {len(pages)} ページ + sitemap.xml + robots.txt")
    print(f"出力先: {out}")

    # 生成HTMLの基本検証（必須SEOメタタグ・タグバランス・必須ファイル）
    result = validate.validate_site(out, pages)
    for w in result["warnings"]:
        print(f"[validate warn] {w}")
    if result["errors"]:
        raise ValueError("\n".join(result["errors"]))
    print(f"検証完了: errors={len(result['errors'])} warnings={len(result['warnings'])}")