# -*- coding: utf-8 -*-
"""pricing schema のバリデーション。
Phase2: 価格ポイント単位の整合性をビルド時に検証し、invalidなpricingは明確なエラーにする。
- display.price_point_id が price_points[] に存在するか
- 各価格ポイントが price_per_meal_yen または min/max（または regional=true）を持つか
- レンジの min<=max、スカラー値がレンジ内
- regional=true は単一値を持たない（捏造禁止）
- basis / status が enum 内
- id の一意性
エラーは ValueError で raise し、警告は print で報告する。"""
from sitegen import templates

_ERROR_PREFIX = "[pricing error]"


def _err(msg):
    raise ValueError(f"{_ERROR_PREFIX} {msg}")


def _warn(msg):
    print(f"[pricing warn] {msg}")


def validate_service(service):
    """サービス1件のpricingを検証する。"""
    svc_id = service.get("id", "?")
    pricing = service.get("pricing")
    # 新schemaが無い場合は旧price_planフォールバック（検証対象外）
    if not pricing:
        return
    points = pricing.get("price_points", [])
    if not isinstance(points, list):
        _err(f"{svc_id}: price_points が配列ではありません")

    # id の一意性
    seen = set()
    for p in points:
        pid = p.get("id")
        if pid in seen:
            _err(f"{svc_id}: price_point id が重複しています: {pid}")
        seen.add(pid)

    # display.price_point_id の参照整合性
    disp = pricing.get("display")
    if disp is not None:
        if not isinstance(disp, dict) or not disp.get("price_point_id"):
            _err(f"{svc_id}: display.price_point_id が未設定です")
        ref = disp.get("price_point_id")
        if ref not in seen:
            _err(f"{svc_id}: display.price_point_id='{ref}' は price_points[] に存在しません")
    elif points:
        # display無しで数値を持つ価格ポイントがあるのは不自然（警告のみ）
        _warn(f"{svc_id}: display が無いが price_points が {len(points)} 件あります")

    # 各価格ポイントの検証
    for p in points:
        pid = p.get("id")
        basis = p.get("basis")
        status = p.get("status")
        if basis not in templates._BASIS_VALID:
            _err(f"{svc_id}/{pid}: basis='{basis}' が不正です（{sorted(templates._BASIS_VALID)}）")
        if status not in templates._STATUS_VALID:
            _err(f"{svc_id}/{pid}: status='{status}' が不正です（{sorted(templates._STATUS_VALID)}）")

        val = p.get("price_per_meal_yen")
        lo = p.get("min_per_meal_yen")
        hi = p.get("max_per_meal_yen")
        regional = p.get("regional", False)

        if regional:
            # 地域依存価格は単一値を持たせない（捏造禁止）
            if val is not None:
                _err(f"{svc_id}/{pid}: regional=true ですが price_per_meal_yen={val} が設定されています（地域依存価格を単一値化してはいけません）")
        if val is None and lo is None and hi is None:
            # regional=true の場合は数値なしを許容（地域依存の事実のみ）
            if not regional:
                _err(f"{svc_id}/{pid}: price_per_meal_yen も min/max も設定されていません（regional=true以外の価格ポイントは数値が必要）")
        if lo is not None and hi is not None and lo > hi:
            _err(f"{svc_id}/{pid}: min_per_meal_yen({lo}) > max_per_meal_yen({hi})")
        if val is not None:
            if lo is not None and val < lo:
                _err(f"{svc_id}/{pid}: price_per_meal_yen({val}) < min_per_meal_yen({lo})")
            if hi is not None and val > hi:
                _err(f"{svc_id}/{pid}: price_per_meal_yen({val}) > max_per_meal_yen({hi})")
        if val is not None and val <= 0:
            _err(f"{svc_id}/{pid}: price_per_meal_yen が 0 以下です: {val}")

        # confirmed/derived は出典と確認日を持つべき（警告）
        if status in ("confirmed", "derived") and not (p.get("source_id") and p.get("last_checked")):
            _warn(f"{svc_id}/{pid}: {status} ですが source_id/last_checked が不足しています")


def validate_services(services):
    """全サービスのpricingを検証する。エラーがあればValueErrorをraise。"""
    for svc in services:
        validate_service(svc)

