"""主页头图 · 毛玻璃版（v2：单图渐进模糊）。

v1 的错：底层用「缩放铺满」、上层用「原尺寸贴边」，两层的取景不同，
拼在一起必然出现一道硬缝 —— 那不是玻璃，那是两张图。

v2 换成：同一张图、同一套几何，只让清晰度从左往右渐变。
底层和上层来自同一个 cover 裁切，所以过渡带上每一像素都对齐，接缝自然消失。

跑法：python .preview/make-hero-glass.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

SRC = Path(r"C:\Users\Administrator\.dsh\attachments\v1\objects\33\33d9303e9f491a911a9ab92f7d704d2b50432a239c9eb5baaf9d28fdcfd1f260")
OUT = Path(__file__).resolve().parent / "hero-glass.png"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_CN_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_CN = "C:/Windows/Fonts/msyh.ttc"

W, H = 1280, 360
FOCUS_Y = 0.40     # 竖向取景：留头，切脚
ZOOM = 1.32        # 稍微放大，换来横向移动的自由度
SUBJECT_AT = 0.62  # 主体（海绵宝宝）落在屏幕宽度的 62% 处，把渐变让到角色之间的空隙
BLUR = 34          # 毛玻璃模糊半径
RAMP_FROM, RAMP_TO = 260, 700   # 从左「全模糊」到右「全清晰」的过渡区间
VEIL_FLAT, VEIL_END = 260, 640  # 文字区先给一段均匀压暗，再渐隐


def cover(img: Image.Image, w: int, h: int, focus_y: float) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih) * ZOOM
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    resized = img.resize((nw, nh), Image.LANCZOS)
    # 让原图 42% 处（海绵宝宝）落到 SUBJECT_AT
    left = int(0.42 * nw - SUBJECT_AT * w)
    left = max(0, min(nw - w, left))
    top = int((nh - h) * focus_y)
    top = max(0, min(nh - h, top))
    return resized.crop((left, top, left + w, top + h))


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def main():
    src = Image.open(SRC).convert("RGB")
    base = cover(src, W, H, FOCUS_Y)

    # 毛玻璃层：同一张 base，重模糊 + 压暗 + 偏冷
    glass = base.filter(ImageFilter.GaussianBlur(BLUR))
    glass = ImageEnhance.Brightness(glass).enhance(0.52)
    glass = ImageEnhance.Color(glass).enhance(0.88)
    glass = Image.blend(glass, Image.new("RGB", (W, H), (16, 24, 46)), 0.30)

    # 过渡：左透明（露出玻璃）→ 右不透明（露出清晰原图）
    mask = Image.new("L", (W, 1), 0)
    mp = mask.load()
    for x in range(W):
        mp[x, 0] = int(255 * smoothstep((x - RAMP_FROM) / (RAMP_TO - RAMP_FROM)))
    mask = mask.resize((W, H))

    canvas = Image.composite(base.convert("RGBA"), glass.convert("RGBA"), mask)

    # 文字区压暗（只压左侧，右边交给画面）
    veil = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(veil)
    for x in range(0, VEIL_END):
        if x <= VEIL_FLAT:
            a = 214
        else:
            a = int(214 * smoothstep(1 - (x - VEIL_FLAT) / (VEIL_END - VEIL_FLAT)))
        vd.line([(x, 0), (x, H)], fill=a)
    dark = Image.new("RGBA", (W, H), (8, 11, 18, 255))
    dark.putalpha(veil)
    canvas = Image.alpha_composite(canvas, dark)

    # 极细噪点：大面积模糊渐变会出色带，噪点是唯一便宜的解法，
    # 顺带让这块区域看起来像「有材质的玻璃」而不是一块糊掉的图。
    noise = Image.effect_noise((W, H), 26).convert("L")
    region = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(region)
    for x in range(0, 900):
        rd.line([(x, 0), (x, H)], fill=int(255 * max(0.0, 1 - x / 900) ** 0.8))
    grain_alpha = Image.composite(noise.point(lambda v: int(v * 0.10)), Image.new("L", (W, H), 0), region)
    grain = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    grain.putalpha(grain_alpha)
    canvas = Image.alpha_composite(canvas, grain)

    draw = ImageDraw.Draw(canvas)
    draw.text((76, 74), "楚汉", font=ImageFont.truetype(FONT_CN_BOLD, 74), fill=(247, 249, 253))
    draw.text((80, 168), "xevil3301", font=ImageFont.truetype(FONT_BOLD, 27), fill=(126, 168, 240))
    draw.line([(80, 214), (208, 214)], fill=(96, 160, 255), width=3)
    draw.text((80, 238), "不知名三县城市小镇白日梦想家", font=ImageFont.truetype(FONT_CN, 22), fill=(198, 206, 220))
    draw.text((80, 276), "cw · flashmanager · dsh-chatlock · zufang-guide",
              font=ImageFont.truetype(FONT_CN, 18), fill=(140, 150, 168))

    canvas.convert("RGB").save(OUT, optimize=True)
    canvas.convert("RGB").save(OUT.with_suffix(".jpg"), quality=88, optimize=True, progressive=True)
    print("hero-glass.png / .jpg", canvas.size)


if __name__ == "__main__":
    main()
