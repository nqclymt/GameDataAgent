"""生成应用图标。

三种风格：
- petals: 六片花瓣环环相扣（默认，接近 GPT 的旋转结构）
- rings:  两个方环交叉相扣（蓝色菱环压过紫色方环）
- type:   字母拼贴（DATA Σ / AGENT）

用法:
    python -m scripts.make_icon              # petals
    python -m scripts.make_icon --style rings
    python -m scripts.make_icon --style type
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

SIZE = 512
BG = (255, 255, 255)
BORDER = (229, 231, 235)
NAVY = (30, 58, 138)
GREEN = (22, 163, 74)

BLUE = (37, 99, 235)
VIOLET = (109, 40, 217)

FONT_BOLD = "ariblk.ttf"


def _lerp(c1, c2, t: float):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def _gradient() -> Image.Image:
    """对角渐变：左上蓝 → 右下紫；小图算完再放大，省掉逐像素开销。"""
    small = Image.new("RGB", (64, 64))
    pixels = small.load()
    for y in range(64):
        for x in range(64):
            pixels[x, y] = _lerp(BLUE, VIOLET, (x + y) / 126)
    return small.resize((SIZE, SIZE), Image.BICUBIC)


def _paint(mask: Image.Image) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img.paste(_gradient(), (0, 0), mask)
    return img


def _polar(radius: float, deg: float) -> tuple[float, float]:
    theta = math.radians(deg)
    return SIZE / 2 + radius * math.cos(theta), SIZE / 2 + radius * math.sin(theta)


def build_petals() -> Image.Image:
    """六片花瓣环环相扣：尾在内圈、头在外圈，跨 96°。

    相邻花瓣相隔 60°，却各跨 96°，于是每个花瓣的「头」与下一个的「尾」
    在同一角度上分别占据外圈和内圈，中间留出一道螺旋缝隙——这就是
    GPT logo 那种层层咬合的结构，而不是把六个图形摆成一圈。
    """
    mask = Image.new("L", (SIZE, SIZE), 0)
    pen = ImageDraw.Draw(mask)

    r_tail, r_head = 130.0, 198.0
    w_tail, w_head = 9.0, 25.0
    span = 96.0
    samples = 140

    for index in range(6):
        base = index * 60 - 90
        outer: list[tuple[float, float]] = []
        inner: list[tuple[float, float]] = []
        for i in range(samples):
            t = i / (samples - 1)
            radius = r_tail + (r_head - r_tail) * t
            width = w_tail + (w_head - w_tail) * (t**1.5)
            theta = math.radians(base + span * t)
            cos_t, sin_t = math.cos(theta), math.sin(theta)
            outer.append(
                (SIZE / 2 + (radius + width) * cos_t, SIZE / 2 + (radius + width) * sin_t)
            )
            inner.append(
                (SIZE / 2 + (radius - width) * cos_t, SIZE / 2 + (radius - width) * sin_t)
            )
        pen.polygon(outer + inner[::-1], fill=255)

        for t_end, radius_end, width_end in (
            (0.0, r_tail, w_tail),
            (1.0, r_head, w_head),
        ):
            hx, hy = _polar(radius_end, base + span * t_end)
            pen.ellipse(
                [hx - width_end, hy - width_end, hx + width_end, hy + width_end],
                fill=255,
            )

    return _paint(mask)


def _ring_mask(radius: float, stroke: int, angle: float) -> Image.Image:
    layer = Image.new("L", (SIZE, SIZE), 0)
    half = SIZE / 2
    ImageDraw.Draw(layer).rounded_rectangle(
        [half - radius, half - radius, half + radius, half + radius],
        radius=radius * 0.42,
        outline=255,
        width=stroke,
    )
    return layer.rotate(angle, resample=Image.BICUBIC, center=(half, half))


def build_rings() -> Image.Image:
    """两个方环交叉相扣：外环紫、内环蓝，蓝环压过紫环处留透明间隙。"""
    stroke = 48
    gap = 13
    base_mask = _ring_mask(176, stroke, 0)
    over_mask = _ring_mask(132, stroke, 45)

    # 用更粗的环当"挖刀"，把底环在交叉处切出透明间隙
    cutter = _ring_mask(132, stroke + gap * 2, 45)
    base_mask = ImageChops.subtract(base_mask, cutter)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    base_img = Image.new("RGBA", (SIZE, SIZE), VIOLET + (255,))
    base_img.putalpha(base_mask)
    over_img = Image.new("RGBA", (SIZE, SIZE), BLUE + (255,))
    over_img.putalpha(over_mask)

    canvas.alpha_composite(base_img)
    canvas.alpha_composite(over_img)
    return canvas


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [2, 2, SIZE - 3, SIZE - 3],
        radius=82,
        fill=BG,
        outline=BORDER,
        width=2,
    )
    return img, draw


def _measure(draw: ImageDraw.ImageDraw, font, text: str) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def build_type() -> Image.Image:
    """字母拼贴：DATA Σ + AGENT。"""
    img, draw = _canvas()
    big = ImageFont.truetype(FONT_BOLD, 112)
    mid = ImageFont.truetype(FONT_BOLD, 96)
    sign = ImageFont.truetype(FONT_BOLD, 60)

    w_data, _ = _measure(draw, big, "DATA")
    w_sign, _ = _measure(draw, sign, "Σ")
    total = w_data + 12 + w_sign
    start = (SIZE - total) // 2
    draw.text((start, 128), "DATA", font=big, fill=NAVY)
    draw.text((start + w_data + 12, 126), "Σ", font=sign, fill=GREEN)

    w_agent, _ = _measure(draw, mid, "AGENT")
    draw.text(((SIZE - w_agent) // 2, 280), "AGENT", font=mid, fill=NAVY)
    return img


def _scaled(poly, factor: float, center):
    """绕指定中心等比缩小，得到与外形同比例的小号轮廓。"""
    cx, cy = center
    return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in poly]


def build_star(
    color: tuple = (17, 17, 17),
    star_radius: float = 106.0,
    star_offset: float = 30.0,
    star_line: int = 11,
    tip: float = 242.0,
    side: float = 156.0,
    notch: float = 100.0,
) -> Image.Image:
    """六个镂空菱形围成一圈，中间一枚线条六芒星。

    菱形是「外形减去等比缩小的自身」，所以镂空与外形同比例；
    中间六芒星用两条三角线框，细线，不与菱形粘连。
    """
    outer = Image.new("L", (SIZE, SIZE), 0)
    op = ImageDraw.Draw(outer)
    holes = Image.new("L", (SIZE, SIZE), 0)
    hp = ImageDraw.Draw(holes)

    for index in range(6):
        a = index * 60 - 90
        blade = [
            _polar(tip, a),
            _polar(side, a + 24),
            _polar(notch, a),
            _polar(side, a - 24),
        ]
        op.polygon(blade, fill=255)
        # 绕菱形几何中心缩放，两端边框才会一样宽
        hp.polygon(_scaled(blade, 0.50, _polar((tip + notch) / 2, a)), fill=255)

    mask = ImageChops.subtract(outer, holes)

    star = Image.new("L", (SIZE, SIZE), 0)
    sp = ImageDraw.Draw(star)
    # 旋转 star_offset 度：让星芒落在菱形之间，菱形尖端正对星形凹槽
    for start in (-90 + star_offset, 90 + star_offset):
        pts = [_polar(star_radius, start + i * 120) for i in range(3)]
        sp.line(pts + [pts[0]], fill=255, width=star_line, joint="curve")

    mask = ImageChops.lighter(mask, star)

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (SIZE, SIZE), color + (255,)), (0, 0), mask)
    return img


def build_tile(
    tile_color: tuple = (17, 17, 17),
    glyph_color: tuple = (255, 255, 255),
    glyph_ratio: float = 0.70,
) -> Image.Image:
    """实底圆角方块 + 白色图形，专供 .ico。

    资源管理器是浅色背景、任务栏是深色背景，同一张透明图标不可能两边都看清；
    给一个实底方块就都能站住，代价是少了透明感。
    """
    tile = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pen = ImageDraw.Draw(tile)
    margin = int(SIZE * 0.03)
    pen.rounded_rectangle(
        [margin, margin, SIZE - margin, SIZE - margin],
        radius=int(SIZE * 0.22),
        fill=tile_color + (255,),
    )

    glyph = build_star(glyph_color)
    inner = int(SIZE * glyph_ratio)
    glyph = glyph.resize((inner, inner), Image.LANCZOS)
    offset = (SIZE - inner) // 2
    tile.alpha_composite(glyph, (offset, offset))
    return tile


BUILDERS = {
    "star": build_star,
    "petals": build_petals,
    "rings": build_rings,
    "type": build_type,
}


def main() -> None:
    style = "star"
    if "--style" in sys.argv:
        style = sys.argv[sys.argv.index("--style") + 1]
    if style not in BUILDERS:
        print(f"未知风格 {style}，可选：{', '.join(BUILDERS)}")
        return

    ASSETS.mkdir(parents=True, exist_ok=True)
    original = ASSETS / "icon.png"
    backup = ASSETS / "icon_ai_backup.png"
    if original.exists() and not backup.exists():
        original.replace(backup)
        print(f"已备份原图 → {backup.name}")

    if style == "star":
        # 侧栏是浅色面板 → 透明底黑字形；
        # .ico 要给资源管理器（白底）和任务栏（深底）共用 → 实底方块 + 白字形
        icon = build_star((17, 17, 17))
        taskbar = build_tile()
    else:
        icon = BUILDERS[style]()
        taskbar = icon

    icon.save(ASSETS / "icon.png")
    taskbar.save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"已生成 {style} 风格图标 → icon.png（黑）/ icon.ico（白）")


if __name__ == "__main__":
    main()
