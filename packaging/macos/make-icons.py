"""Generate the macOS application icon and the disk image background.

The artwork is drawn from code so that a release maintainer never has to keep
binary design files in sync with the packaging pipeline. Running this script
refreshes:

  assets/AppIcon.png        1024x1024 master image
  assets/AppIcon.icns       icon set consumed by the application bundle
  assets/VolumeIcon.icns    icon shown for the mounted disk image
  assets/dmg-background.tiff  Retina-aware background of the installer window

The script only needs Pillow, which is already a runtime dependency of the
application, plus iconutil and tiffutil from the macOS command line tools.

Usage:
    python packaging/macos/make-icons.py [--force]
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# macOS draws application icons inside a rounded square that leaves a margin on
# a 1024 point canvas. These values follow Apple's icon grid.
CANVAS = 1024
PLATE_INSET = 100
PLATE_RADIUS = 185
SUPERSAMPLE = 4

PLATE_TOP_COLOR = (58, 138, 94)
PLATE_BOTTOM_COLOR = (20, 62, 42)
FOREGROUND = (255, 255, 255)

ICNS_SIZES = (16, 32, 64, 128, 256, 512, 1024)

BACKGROUND_TOP_COLOR = (248, 250, 248)
BACKGROUND_BOTTOM_COLOR = (228, 238, 231)
BACKGROUND_TITLE_COLOR = (26, 62, 42)
BACKGROUND_SUBTITLE_COLOR = (94, 116, 103)

# Must stay consistent with the window geometry used by make-dmg.sh.
BACKGROUND_WIDTH = 660
BACKGROUND_HEIGHT = 420

FONT_CANDIDATES = (
    "/System/Library/Fonts/SFNSRounded.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
    return ImageFont.load_default()


def vertical_gradient(
    size: tuple[int, int],
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> Image.Image:
    width, height = size
    gradient = Image.new("RGB", (1, height))
    for y in range(height):
        ratio = y / max(height - 1, 1)
        gradient.putpixel(
            (0, y),
            tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)),
        )
    return gradient.resize((width, height), Image.Resampling.BICUBIC)


def rounded_mask(size: tuple[int, int], box, radius: int) -> Image.Image:
    """Draw a rounded rectangle mask with supersampled edges."""
    width, height = size
    mask = Image.new("L", (width * SUPERSAMPLE, height * SUPERSAMPLE), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [coordinate * SUPERSAMPLE for coordinate in box],
        radius=radius * SUPERSAMPLE,
        fill=255,
    )
    return mask.resize((width, height), Image.Resampling.LANCZOS)


def rotated_ellipse(width: int, height: int, angle: float) -> Image.Image:
    """Return an antialiased mask holding a single rotated ellipse.

    The canvas is the diagonal of the ellipse so that rotation never clips it.
    """
    canvas = math.ceil(math.hypot(width, height)) + 4
    mask = Image.new("L", (canvas * SUPERSAMPLE, canvas * SUPERSAMPLE), 0)
    center = canvas * SUPERSAMPLE / 2
    ImageDraw.Draw(mask).ellipse(
        [
            center - width * SUPERSAMPLE / 2,
            center - height * SUPERSAMPLE / 2,
            center + width * SUPERSAMPLE / 2,
            center + height * SUPERSAMPLE / 2,
        ],
        fill=255,
    )
    mask = mask.resize((canvas, canvas), Image.Resampling.LANCZOS)
    return mask.rotate(angle, resample=Image.Resampling.BICUBIC)


def paste_mask(target: Image.Image, mask: Image.Image, center: tuple[int, int]) -> None:
    x = round(center[0] - mask.width / 2)
    y = round(center[1] - mask.height / 2)
    target.paste(255, (x, y), mask)


def draw_paw(size: int) -> Image.Image:
    """Draw a paw print mask on a square canvas of the requested size."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    scale = size / CANVAS

    def s(value: float) -> int:
        return round(value * scale)

    # Pad: two overlapping ellipses give the slightly tapered outline of a
    # real print without needing a bezier path.
    draw.ellipse([s(368), s(523), s(656), s(729)], fill=255)
    draw.ellipse([s(404), s(481), s(620), s(677)], fill=255)

    toes = (
        ((s(340), s(457)), s(112), s(142), 32.0),
        ((s(442), s(373)), s(118), s(154), 11.0),
        ((s(582), s(373)), s(118), s(154), -11.0),
        ((s(684), s(457)), s(112), s(142), -32.0),
    )
    for center, toe_width, toe_height, angle in toes:
        paste_mask(mask, rotated_ellipse(toe_width, toe_height, angle), center)

    return mask


def draw_viewfinder(size: int) -> Image.Image:
    """Draw the camera framing brackets that surround the paw print."""
    mask = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    scale = size * 2 / CANVAS

    def s(value: float) -> int:
        return round(value * scale)

    left, top, right, bottom = s(212), s(212), s(812), s(812)
    arm = s(132)
    width = s(30)

    corners = (
        ([(left, top + arm), (left, top), (left + arm, top)]),
        ([(right - arm, top), (right, top), (right, top + arm)]),
        ([(left, bottom - arm), (left, bottom), (left + arm, bottom)]),
        ([(right - arm, bottom), (right, bottom), (right, bottom - arm)]),
    )
    for points in corners:
        draw.line(points, fill=255, width=width, joint="curve")
        for point in (points[0], points[2]):
            draw.ellipse(
                [
                    point[0] - width // 2,
                    point[1] - width // 2,
                    point[0] + width // 2,
                    point[1] + width // 2,
                ],
                fill=255,
            )

    return mask.resize((size, size), Image.Resampling.LANCZOS)


def build_app_icon() -> Image.Image:
    icon = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))

    plate_box = (PLATE_INSET, PLATE_INSET, CANVAS - PLATE_INSET, CANVAS - PLATE_INSET)
    plate_mask = rounded_mask((CANVAS, CANVAS), plate_box, PLATE_RADIUS)

    # A soft drop shadow keeps the icon readable on light and dark backgrounds.
    shadow = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 105), (0, 18), plate_mask)
    icon.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))

    plate = vertical_gradient(
        (CANVAS, CANVAS), PLATE_TOP_COLOR, PLATE_BOTTOM_COLOR
    ).convert("RGBA")
    plate.putalpha(plate_mask)
    icon.alpha_composite(plate)

    # A faint highlight along the top edge mimics the depth of stock icons.
    highlight = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_draw.rounded_rectangle(
        [PLATE_INSET + 12, PLATE_INSET + 10, CANVAS - PLATE_INSET - 12, CANVAS // 2],
        radius=PLATE_RADIUS,
        fill=(255, 255, 255, 26),
    )
    highlight.putalpha(
        Image.composite(
            highlight.getchannel("A"), Image.new("L", (CANVAS, CANVAS), 0), plate_mask
        )
    )
    icon.alpha_composite(highlight.filter(ImageFilter.GaussianBlur(24)))

    viewfinder = Image.new("RGBA", (CANVAS, CANVAS), FOREGROUND + (0,))
    viewfinder.putalpha(draw_viewfinder(CANVAS).point(lambda value: value * 150 // 255))
    icon.alpha_composite(viewfinder)

    paw = Image.new("RGBA", (CANVAS, CANVAS), FOREGROUND + (0,))
    paw.putalpha(draw_paw(CANVAS))
    icon.alpha_composite(paw)

    return icon


def build_volume_icon(app_icon: Image.Image) -> Image.Image:
    """Reuse the application artwork for the mounted volume."""
    return app_icon.copy()


def write_icns(master: Image.Image, destination: Path) -> None:
    if not shutil.which("iconutil"):
        raise SystemExit("iconutil was not found; install the Xcode command line tools")

    with tempfile.TemporaryDirectory() as temp:
        iconset = Path(temp) / "AppIcon.iconset"
        iconset.mkdir()
        for size in ICNS_SIZES:
            resized = master.resize((size, size), Image.Resampling.LANCZOS)
            if size <= 512:
                resized.save(iconset / f"icon_{size}x{size}.png")
            if size >= 32:
                resized.save(iconset / f"icon_{size // 2}x{size // 2}@2x.png")
        subprocess.run(
            ["iconutil", "--convert", "icns", "--output", str(destination), str(iconset)],
            check=True,
        )


def build_background(scale: int) -> Image.Image:
    width = BACKGROUND_WIDTH * scale
    height = BACKGROUND_HEIGHT * scale
    image = vertical_gradient(
        (width, height), BACKGROUND_TOP_COLOR, BACKGROUND_BOTTOM_COLOR
    ).convert("RGBA")
    draw = ImageDraw.Draw(image)

    title_font = load_font(23 * scale)
    subtitle_font = load_font(13 * scale)

    draw.text(
        (width / 2, 52 * scale),
        "Camera Trap Assistant",
        font=title_font,
        fill=BACKGROUND_TITLE_COLOR,
        anchor="mm",
    )
    draw.text(
        (width / 2, 84 * scale),
        "Drag the application onto the Applications folder",
        font=subtitle_font,
        fill=BACKGROUND_SUBTITLE_COLOR,
        anchor="mm",
    )

    # Arrow drawn between the two icon positions defined by make-dmg.sh.
    arrow_y = 205 * scale
    start_x = 288 * scale
    end_x = 372 * scale
    thickness = max(3 * scale, 1)
    draw.line(
        [(start_x, arrow_y), (end_x - 10 * scale, arrow_y)],
        fill=BACKGROUND_SUBTITLE_COLOR,
        width=thickness,
    )
    head = 13 * scale
    draw.polygon(
        [
            (end_x + 4 * scale, arrow_y),
            (end_x - head, arrow_y - head * 0.62),
            (end_x - head, arrow_y + head * 0.62),
        ],
        fill=BACKGROUND_SUBTITLE_COLOR,
    )

    draw.text(
        (width / 2, 372 * scale),
        "AI classifications can be wrong. Review important results.",
        font=load_font(11 * scale),
        fill=(150, 165, 155),
        anchor="mm",
    )

    return image.convert("RGB")


def write_background(destination: Path) -> None:
    with tempfile.TemporaryDirectory() as temp:
        standard = Path(temp) / "background.png"
        retina = Path(temp) / "background@2x.png"
        build_background(1).save(standard)
        build_background(2).save(retina)

        if shutil.which("tiffutil"):
            subprocess.run(
                [
                    "tiffutil",
                    "-cathidpicheck",
                    str(standard),
                    str(retina),
                    "-out",
                    str(destination),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        else:
            # Without tiffutil the window still looks correct, only softer on
            # Retina displays.
            shutil.copyfile(standard, destination.with_suffix(".png"))
            print("warning: tiffutil not found, wrote a single resolution background")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="regenerate the artwork even when it is already present",
    )
    arguments = parser.parse_args()

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    app_icns = ASSETS_DIR / "AppIcon.icns"
    volume_icns = ASSETS_DIR / "VolumeIcon.icns"
    background = ASSETS_DIR / "dmg-background.tiff"

    if not arguments.force and app_icns.exists() and background.exists():
        print("Artwork is already present; pass --force to regenerate it.")
        return 0

    print("Drawing the application icon")
    icon = build_app_icon()
    icon.save(ASSETS_DIR / "AppIcon.png")
    write_icns(icon, app_icns)

    print("Drawing the volume icon")
    write_icns(build_volume_icon(icon), volume_icns)

    print("Drawing the disk image background")
    write_background(background)

    print(f"Artwork written to {ASSETS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
