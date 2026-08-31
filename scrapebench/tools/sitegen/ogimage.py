"""
ScrapeBench OGP画像ジェネレータ（B1対応）
- 1200x630 の OGP 用 PNG を Python標準ライブラリのみ（struct/zlib）で生成する。
- テキストは最小限の5x7ビットマップフォント（固定文字列に必要な A-Z サブセット）で描画。
- 依存ライブラリなし。生成された PNG は site/og-image.png として sitegen が書き出す。
"""
import struct
import zlib

# 5x7 ビットマップフォント（各行=5bit、MSBが左端。1=塗る）
# 固定文字列「SCRAPEBENCH」「LLM WEB SCRAPING API BENCHMARKS」に必要な文字のみを定義。
_FONT = {
    "A": [14, 17, 17, 31, 17, 17, 17],
    "B": [30, 17, 17, 30, 17, 17, 30],
    "C": [14, 17, 16, 16, 16, 17, 14],
    "E": [31, 16, 16, 30, 16, 16, 31],
    "G": [14, 17, 16, 23, 17, 17, 14],
    "H": [17, 17, 17, 31, 17, 17, 17],
    "I": [31, 4, 4, 4, 4, 4, 31],
    "K": [17, 18, 20, 24, 20, 18, 17],
    "L": [16, 16, 16, 16, 16, 16, 31],
    "M": [17, 27, 21, 21, 17, 17, 17],
    "N": [17, 25, 21, 19, 17, 17, 17],
    "P": [30, 17, 17, 30, 16, 16, 16],
    "R": [30, 17, 17, 30, 20, 18, 17],
    "S": [15, 16, 16, 14, 1, 1, 30],
    "W": [17, 17, 17, 17, 21, 27, 17],
    " ": [0, 0, 0, 0, 0, 0, 0],
}

_TITLE = "SCRAPEBENCH"
_SUBTITLE = "LLM WEB SCRAPING API BENCHMARKS"

# 配色
_BG = (18, 47, 84)        # #122F54 暗いブルー
_CARD = (27, 74, 133)     # #1B4A85 カード面
_WHITE = (255, 255, 255)
_LIGHT = (191, 216, 255)  # #BFD8FF
_ACCENT = (46, 139, 255)  # #2E8BFF


def _new_canvas(width, height, color):
    """width x height のRGBキャンバス（各行は bytearray）を返す。"""
    return [bytearray([color[0], color[1], color[2]]) * width for _ in range(height)]


def _set_px(canvas, x, y, color):
    if 0 <= x < len(canvas[0]) // 3 and 0 <= y < len(canvas):
        i = x * 3
        canvas[y][i] = color[0]
        canvas[y][i + 1] = color[1]
        canvas[y][i + 2] = color[2]


def _fill_rect(canvas, x0, y0, x1, y1, color):
    for y in range(y0, y1):
        for x in range(x0, x1):
            _set_px(canvas, x, y, color)


def _text_width(text, scale):
    return len(text) * 6 * scale  # 5列 + 1列スペース


def _draw_text(canvas, width, text, cy, scale, color):
    x = (width - _text_width(text, scale)) // 2
    for ch in text:
        glyph = _FONT.get(ch, _FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    for dy in range(scale):
                        for dx in range(scale):
                            _set_px(canvas, x + col * scale + dx, cy + row * scale + dy, color)
        x += 6 * scale


def _png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def render_og_image(width=1200, height=630):
    """1200x630 の OGP用PNGバイト列を返す。"""
    canvas = _new_canvas(width, height, _BG)

    # 中央カード面
    _fill_rect(canvas, 40, 110, width - 40, height - 110, _CARD)

    # タイトル / アクセントバー / サブタイトル
    _draw_text(canvas, width, _TITLE, 170, 9, _WHITE)
    _fill_rect(canvas, (width - 140) // 2, 295, (width + 140) // 2, 305, _ACCENT)
    _draw_text(canvas, width, _SUBTITLE, 340, 4, _LIGHT)

    # PNG エンコード
    raw = b"".join(b"\x00" + bytes(row) for row in canvas)  # 各行の先頭にフィルタ0
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", zlib.compress(raw, 9))
            + _png_chunk(b"IEND", b""))


if __name__ == "__main__":
    out = __import__("pathlib").Path(__file__).resolve().parent.parent.parent / "site" / "og-image.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(render_og_image())
    print(f"OGP画像生成: {out} ({len(render_og_image())} bytes)")