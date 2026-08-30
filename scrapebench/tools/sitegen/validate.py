"""
ScrapeBench 生成HTMLの基本検証
- 必須SEOメタタグ（title / canonical / meta description / og:title / og:description）の存在
- 主要タグの開始・終了バランス（不一致は警告）
- 必須ファイル（sitemap.xml / robots.txt）の存在
エラーは errors として返し、呼び出し元（generators.main）で ValueError にする。
"""
import re
from pathlib import Path

REQUIRED_META = [
    ("<title>", "title"),
    ('rel="canonical"', "canonical"),
    ('<meta name="description"', "meta description"),
    ('<meta property="og:title"', "og:title"),
    ('<meta property="og:description"', "og:description"),
]

# 検証対象の主要タグ（templates.py が常に閉じタグを明示的に出力するもの）
BALANCE_TAGS = ["div", "section", "article", "header", "footer", "main", "nav",
                "table", "thead", "tbody", "tr", "td", "th", "ul", "ol", "li",
                "p", "a", "h1", "h2", "h3", "span", "code", "strong", "em"]


def validate_html_text(text, path):
    errors, warnings = [], []
    for needle, label in REQUIRED_META:
        if needle not in text:
            errors.append(f"{path}: 必須メタタグ不足: {label}")
    if "<html" not in text or "</html>" not in text:
        errors.append(f"{path}: <html>...</html> が不完全")
    for tag in BALANCE_TAGS:
        opens = len(re.findall(rf"<{tag}(\s|>)", text))
        closes = len(re.findall(rf"</{tag}>", text))
        if opens != closes:
            warnings.append(f"{path}: <{tag}> 開始{opens} / 終了{closes} の不一致")
    return errors, warnings


def validate_site(out_dir, pages):
    errors, warnings = [], []
    for p in pages:
        f = out_dir / p
        if not f.exists():
            errors.append(f"生成ファイルが存在しない: {p}")
            continue
        e, w = validate_html_text(f.read_text(encoding="utf-8"), p)
        errors += e
        warnings += w
    for required in ["sitemap.xml", "robots.txt"]:
        if not (out_dir / required).exists():
            errors.append(f"生成ファイルが存在しない: {required}")
    return {"errors": errors, "warnings": warnings}