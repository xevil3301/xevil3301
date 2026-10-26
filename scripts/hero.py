"""个人主页头图 v2：左侧大字 + 右侧五个圆形头像（五部动画的「班底」）。

v1 试过竖向切片，失败的三个原因
  1. 左侧要给文字留渐隐，前两张素材直接被压没了 —— 五部动画变三部。
  2. 罗小黑原图只有 225px，切满高要放大 1.8 倍，糊。
  3. 五张素材的取景差异太大（全身 / 半身 / 特写），竖条里对不齐。
所以改成圆形：全部降采样（小图反而最锐）、取景统一、五种画风靠同一个圆环收边。

跑法：python scripts/hero.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ATT = Path(r"C:\Users\Administrator\.dsh\attachments\v1\objects")

# (文件, 焦点 cx, 焦点 cy, 方框边长占短边的比例, 亮度校正)
CAST = [
    ("33/33d9303e9f491a911a9ab92f7d704d2b50432a239c9eb5baaf9d28fdcfd1f260", 0.471, 0.569, 0.40, 0.96),  # 海绵宝宝
    ("eb/eb83f0a76fdf07736b913d3335cb02d1d7e3d5aac9ca6104d24dceee35be08b9", 0.53, 0.25, 0.44, 1.02),   # 蜡笔小新
    ("d9/d9706e15dd7c16e0463e291b73dfdf2b6bdf0912bd49577c30484f42c3de134f", 0.66, 0.27, 0.52, 1.55),   # 猫和老鼠
    ("5e/5e77f2a16e20e9d812cb6c1e8a33c719b67827d71b127cfce87709ceb10bf625", 0.50, 0.42, 0.92, 1.00),   # 罗小黑
    ("d0/d070567c155b9059c4088ea60ae9abf68370fd5ee0577f02a0a7b9c83ff598a7", 0.47, 0.36, 0.58, 1.05),   # 刺客伍六七
]

RING = (255, 255, 255, 92)   # 统一一圈白环，五张图风格才像一套

W, H = 1280, 360
OUT = Path(__file__).resolve().parent.parent / "assets"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_CN_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_CN = "C:/Windows/Fonts/msyh.ttc"

D = 100          # 头像直径
GAP = 20
SS = 4           # 超采样倍数


def face_circle(path: Path, cx: float, cy: float, ratio: float, bright: float):
    img = Image.open(path).convert("RGB")
    if bright != 1.0:
        img = ImageEnhance.Brightness(img).enhance(bright)
    iw, ih = img.size
    side = min(iw, ih) * ratio
    left = max(0, min(iw - side, iw * cx - side / 2))
    top = max(0, min(ih - side, ih * cy - side / 2))
    sq = img.crop((int(left), int(top), int(left + side), int(top + side)))
    sq = sq.resize((D * SS, D * SS), Image.LANCZOS)

    mask = Image.new("L", (D * SS, D * SS), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, D * SS - 1, D * SS - 1], fill=255)
    circle = Image.new("RGBA", (D * SS, D * SS), (0, 0, 0, 0))
    circle.paste(sq, (0, 0), mask)

    # 一圈白环
    d = ImageDraw.Draw(circle)
    d.ellipse([0, 0, D * SS - 1, D * SS - 1], outline=RING, width=SS * 2)
    circle = circle.resize((D, D), Image.LANCZOS)

    # 环外的柔光，让头像在深底上浮起来
    glow = Image.new("RGBA", (D + 36, D + 36), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([18, 18, D + 18, D + 18], fill=(76, 141, 255, 52))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    glow.alpha_composite(circle, (18, 18))
    return glow


def main():
    canvas = Image.new("RGBA", (W, H), (10, 13, 21, 255))

    # 右侧冷光
    halo = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(halo)
    hd.ellipse([W * 0.52, -H * 0.5, W * 1.05, H * 1.5], fill=90)
    halo = halo.filter(ImageFilter.GaussianBlur(70))
    tint = Image.new("RGBA", (W, H), (48, 96, 200, 255))
    tint.putalpha(halo)
    canvas = Image.alpha_composite(canvas, tint)

    # 头像带：左边界给文字留够，整体靠右
    total = len(CAST) * D + (len(CAST) - 1) * GAP
    x0 = 640 + (W - 60 - 640 - total) // 2
    for i, (rel, cx, cy, ratio, bright) in enumerate(CAST):
        chip = face_circle(ATT / rel, cx, cy, ratio, bright)
        x = x0 + i * (D + GAP) - 18
        y = (H - chip.height) // 2 - 14
        canvas.alpha_composite(chip, (x, y))

    draw = ImageDraw.Draw(canvas)
    # 头像带下面的小字：说明这五个人是谁
    caption = "海绵宝宝 · 蜡笔小新 · 猫和老鼠 · 罗小黑 · 刺客伍六七"
    cap_font = ImageFont.truetype(FONT_CN, 15)
    cap_w = draw.textlength(caption, font=cap_font)
    draw.text((x0 + total / 2 - cap_w / 2, 286), caption, font=cap_font, fill=(104, 114, 132))

    draw.text((76, 74), "楚汉", font=ImageFont.truetype(FONT_CN_BOLD, 74), fill=(247, 249, 253))
    draw.text((80, 168), "xevil3301", font=ImageFont.truetype(FONT_BOLD, 27), fill=(110, 152, 230))
    draw.line([(80, 214), (208, 214)], fill=(76, 141, 255), width=3)
    draw.text((80, 238), "做点小工具，也做点能用的话", font=ImageFont.truetype(FONT_CN, 22), fill=(180, 189, 204))
    draw.text((80, 276), "cw · flashmanager · dsh-chatlock · zufang-guide",
              font=ImageFont.truetype(FONT_CN, 18), fill=(120, 131, 150))

    canvas.convert("RGB").save(OUT / "hero.png", optimize=True)
    print("hero.png", canvas.size)


if __name__ == "__main__":
    main()
