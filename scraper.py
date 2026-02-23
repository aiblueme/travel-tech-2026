"""
scraper.py — Targeted product image downloader for 2026 Travel Tech Comparison

Strategy per device:
  1. Try Bing Tier-1 terms (brand + full model + "official" / "press")
  2. Validate every downloaded file: dimensions, file size, aspect ratio
  3. If <2 good images found, fall back to Tier-2 Bing terms
  4. If still <1 good image, try Baidu (better for Lenovo/Huawei/Samsung SEA press)
  5. Auto-select the highest-quality valid image → images/{slug}.jpg

Install:
    pip install icrawler Pillow

Run:
    python scraper.py

Output:
    images/macbook_air_m4.jpg          ← production (served by nginx)
    images/zenbook_s14_oled.jpg
    ...
    images/_raw/{slug}/bing_0/...      ← raw downloads (gitignored)
    images/_raw/{slug}/baidu_0/...
"""

import os
import shutil
import glob as globmod
import logging
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("WARNING: Pillow not installed — image validation disabled. pip install Pillow")

from icrawler.builtin import BingImageCrawler, BaiduImageCrawler

# ─────────────────────────────────────────────────────────────
#  Silence icrawler's noisy logger
# ─────────────────────────────────────────────────────────────
logging.getLogger("icrawler").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# ─────────────────────────────────────────────────────────────
#  DEVICE LIST  —  search terms ordered best → fallback
#  Bing tiers: press/official → review photo → generic product
#  Baidu terms: manufacturer Chinese names (stronger for Lenovo/Huawei)
# ─────────────────────────────────────────────────────────────
DEVICES = [
    {
        "slug": "macbook_air_m4",
        "bing": [
            "Apple MacBook Air 13 M4 2025 official press photo silver",
            "MacBook Air M4 laptop product photo white background 2025",
            "Apple MacBook Air M4 review laptop photo",
        ],
        "baidu": ["苹果 MacBook Air M4 2025 官方 产品图"],
    },
    {
        "slug": "zenbook_s14_oled",
        "bing": [
            "ASUS ZenBook S 14 OLED UX5406 2025 official product photo",
            "ASUS ZenBook S14 OLED laptop review press photo",
            "ASUS ZenBook S 14 laptop 2025",
        ],
        "baidu": ["华硕 ZenBook S14 OLED 2025 官方 产品图"],
    },
    {
        "slug": "lg_gram_14_2026",
        "bing": [
            "LG Gram 14 2026 official product photo laptop",
            "LG gram 14 2025 laptop press image white background",
            "LG gram 14 ultralight laptop photo",
        ],
        "baidu": ["LG gram 14 2026 轻薄本 官方 产品图"],
    },
    {
        "slug": "thinkpad_x1_carbon_13",
        "bing": [
            "Lenovo ThinkPad X1 Carbon Gen 13 2025 official press photo",
            "ThinkPad X1 Carbon Gen 13 Aura Edition laptop product photo",
            "ThinkPad X1 Carbon 13 laptop review photo 2025",
        ],
        "baidu": ["联想 ThinkPad X1 Carbon Gen 13 2025 官方图"],
    },
    {
        "slug": "dell_xps_13_2025",
        "bing": [
            "Dell XPS 13 9350 2025 official product press photo",
            "Dell XPS 13 2025 laptop review photo",
            "Dell XPS 13 plus 2025 laptop photo",
        ],
        "baidu": ["戴尔 XPS 13 2025 官方 产品图"],
    },
    {
        "slug": "galaxy_book5_pro_14",
        "bing": [
            "Samsung Galaxy Book5 Pro 14 official press product photo 2025",
            "Samsung Galaxy Book 5 Pro 14 inch laptop review photo",
            "Samsung Galaxy Book5 Pro laptop silver",
        ],
        "baidu": ["三星 Galaxy Book5 Pro 14 官方 产品图 2025"],
    },
    {
        "slug": "hp_omnibook_ultra_14",
        "bing": [
            "HP OmniBook Ultra 14 official product press photo 2025",
            "HP OmniBook Ultra 14 laptop review photo AMD",
            "HP OmniBook Ultra laptop 2025",
        ],
        "baidu": ["惠普 OmniBook Ultra 14 笔记本 官方 产品"],
    },
    {
        "slug": "surface_pro_11",
        "bing": [
            "Microsoft Surface Pro 11 official product photo Snapdragon 2024",
            "Microsoft Surface Pro 11 press photo tablet laptop",
            "Surface Pro 11 laptop tablet review photo",
        ],
        "baidu": ["微软 Surface Pro 11 官方 产品图"],
    },
    {
        "slug": "framework_13_amd",
        "bing": [
            "Framework Laptop 13 AMD Ryzen AI 300 official product photo",
            "Framework 13 AMD laptop press photo 2024",
            "Framework Laptop 13 AMD modular laptop photo",
        ],
        "baidu": ["Framework Laptop 13 AMD 模块化 笔记本 产品图"],
    },
    {
        "slug": "acer_swift_14_ai",
        "bing": [
            "Acer Swift 14 AI 2025 official product press photo laptop",
            "Acer Swift 14 AI Intel Core Ultra laptop review photo",
            "Acer Swift 14 AI laptop 2025 photo",
        ],
        "baidu": ["宏碁 Swift 14 AI 2025 笔记本 官方 产品图"],
    },
    {
        "slug": "yoga_slim_7x_gen10",
        "bing": [
            "Lenovo Yoga Slim 7x Gen 10 Snapdragon X Elite official product photo",
            "Lenovo Yoga Slim 7x 2024 laptop press photo Snapdragon",
            "Lenovo Yoga Slim 7x laptop review photo 2024",
        ],
        "baidu": ["联想 Yoga Slim 7x 骁龙X Elite 2024 官方 产品图"],
    },
    {
        "slug": "matebook_x_pro_2025",
        "bing": [
            "Huawei MateBook X Pro 2025 official press product photo",
            "Huawei MateBook X Pro 2025 laptop review photo OLED",
            "Huawei MateBook X Pro 2025 laptop photo",
        ],
        "baidu": ["华为 MateBook X Pro 2025 官方 产品图 笔记本"],
    },
    {
        "slug": "razer_blade_14_2025",
        "bing": [
            "Razer Blade 14 2025 official product press photo laptop",
            "Razer Blade 14 2025 gaming laptop review photo black",
            "Razer Blade 14 2025 laptop AMD RTX",
        ],
        "baidu": ["雷蛇 Blade 14 2025 笔记本 官方 产品图"],
    },
    # ── Lenovo Yoga Slim full lineup ──────────────────────────
    {
        "slug": "yoga_slim_9i_gen10",
        "bing": [
            "Lenovo Yoga Slim 9i Gen 10 14 inch 2025 official product photo",
            "Lenovo Yoga Slim 9i Gen 10 OLED under-display camera laptop press",
            "Lenovo Yoga Slim 9i 14 2025 laptop review photo",
        ],
        "baidu": ["联想 Yoga Slim 9i Gen 10 14英寸 2025 官方 产品图"],
    },
    {
        "slug": "yoga_slim_7i_aura_14",
        "bing": [
            "Lenovo Yoga Slim 7i Aura Edition 14 inch 2025 official product photo",
            "Lenovo Yoga Slim 7i Aura 14 laptop press photo Intel Core Ultra",
            "Lenovo Yoga Slim 7i Gen 9 Aura Edition 14 laptop photo",
        ],
        "baidu": ["联想 Yoga Slim 7i Aura Edition 14英寸 2025 官方 产品图"],
    },
    {
        "slug": "yoga_slim_7i_aura_15",
        "bing": [
            "Lenovo Yoga Slim 7i Aura Edition 15 inch 2025 official product photo",
            "Lenovo Yoga Slim 7i Aura 15.3 laptop press photo",
            "Lenovo Yoga Slim 7i Gen 9 Aura 15 laptop review photo",
        ],
        "baidu": ["联想 Yoga Slim 7i Aura Edition 15英寸 2025 官方图"],
    },
    {
        "slug": "yoga_slim_7x_gen11",
        "bing": [
            "Lenovo Yoga Slim 7x Gen 11 Snapdragon X2 Elite 2026 official product photo",
            "Lenovo Yoga Slim 7x Gen 11 laptop announced CES 2026",
            "Lenovo Yoga Slim 7x 2026 laptop press photo",
        ],
        "baidu": ["联想 Yoga Slim 7x Gen 11 骁龙X2 2026 产品图"],
    },
    {
        "slug": "yoga_slim_7a_gen11",
        "bing": [
            "Lenovo Yoga Slim 7a Gen 11 AMD Ryzen AI 2026 official product photo",
            "Lenovo Yoga Slim 7a Gen 11 laptop press photo announced",
            "Lenovo Yoga Slim 7a AMD laptop 2026",
        ],
        "baidu": ["联想 Yoga Slim 7a Gen 11 AMD 锐龙AI 2026 产品图"],
    },
    {
        "slug": "yoga_slim_7i_ultra_aura",
        "bing": [
            "Lenovo Yoga Slim 7i Ultra Aura Edition 14 inch 2026 official product photo",
            "Lenovo Yoga Slim 7i Ultra Aura Edition CES 2026 laptop press",
            "Lenovo Yoga Slim 7i Ultra Aura laptop photo 975g",
        ],
        "baidu": ["联想 Yoga Slim 7i Ultra Aura Edition 2026 官方 产品图"],
    },
]

# ─────────────────────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────────────────────
BASE_DIR      = Path("images")
RAW_DIR       = BASE_DIR / "_raw"
SELECTED_DIR  = BASE_DIR          # final files live at images/{slug}.jpg

BING_PER_TERM   = 5
BAIDU_PER_TERM  = 3
MIN_GOOD_IMAGES = 1   # move to next tier if fewer valid images than this

# Image quality thresholds
MIN_WIDTH_PX  = 380
MIN_HEIGHT_PX = 220
MIN_SIZE_KB   = 18
MAX_PORTRAIT  = 0.75   # width/height ratio — reject if narrower than this


# ─────────────────────────────────────────────────────────────
#  IMAGE VALIDATION
# ─────────────────────────────────────────────────────────────
def validate(path: Path) -> tuple[bool, str]:
    """Return (ok, reason). Checks file size, pixel dims, and aspect ratio."""
    if not PIL_OK:
        return os.path.getsize(path) > MIN_SIZE_KB * 1024, "no-PIL"
    try:
        if os.path.getsize(path) < MIN_SIZE_KB * 1024:
            return False, f"tiny file ({os.path.getsize(path)//1024}KB)"
        with Image.open(path) as img:
            w, h = img.size
            if w < MIN_WIDTH_PX or h < MIN_HEIGHT_PX:
                return False, f"low res {w}×{h}"
            if (w / h) < MAX_PORTRAIT:
                return False, f"portrait aspect {w/h:.2f}"
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


def score_image(path: Path) -> int:
    """Higher is better. Larger file → richer image."""
    return os.path.getsize(path)


# ─────────────────────────────────────────────────────────────
#  CRAWL HELPERS
# ─────────────────────────────────────────────────────────────
def crawl_bing(keyword: str, dest: Path, max_num: int) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        c = BingImageCrawler(
            feeder_threads=1,
            parser_threads=2,
            downloader_threads=4,
            storage={"root_dir": str(dest)},
        )
        c.crawl(
            keyword=keyword,
            filters={"size": "large", "type": "photo"},
            max_num=max_num,
            file_idx_offset=0,
        )
    except Exception as exc:
        print(f"    Bing crawl error: {exc}")


def crawl_baidu(keyword: str, dest: Path, max_num: int) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        c = BaiduImageCrawler(
            feeder_threads=1,
            parser_threads=2,
            downloader_threads=4,
            storage={"root_dir": str(dest)},
        )
        c.crawl(keyword=keyword, max_num=max_num, file_idx_offset=0)
    except Exception as exc:
        print(f"    Baidu crawl error: {exc}")


# ─────────────────────────────────────────────────────────────
#  COLLECT VALID IMAGES FROM A DIRECTORY
# ─────────────────────────────────────────────────────────────
def good_images(directory: Path) -> list[Path]:
    candidates = list(directory.glob("*.jpg")) + \
                 list(directory.glob("*.jpeg")) + \
                 list(directory.glob("*.png")) + \
                 list(directory.glob("*.webp"))
    result = []
    for p in candidates:
        ok, reason = validate(p)
        if ok:
            result.append(p)
        else:
            print(f"      skip {p.name}: {reason}")
    return result


# ─────────────────────────────────────────────────────────────
#  SAVE BEST IMAGE  →  images/{slug}.jpg
# ─────────────────────────────────────────────────────────────
def save_best(candidates: list[Path], slug: str) -> bool:
    if not candidates:
        return False
    best = max(candidates, key=score_image)
    dest = SELECTED_DIR / f"{slug}.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)

    if best.suffix.lower() in (".png", ".webp") and PIL_OK:
        # Convert to JPEG
        with Image.open(best) as img:
            rgb = img.convert("RGB")
            rgb.save(dest, "JPEG", quality=88, optimize=True)
    else:
        shutil.copy2(best, dest)

    kb = os.path.getsize(dest) // 1024
    print(f"    ✓ saved → images/{slug}.jpg  ({kb}KB, src: {best.name})")
    return True


# ─────────────────────────────────────────────────────────────
#  PROCESS ONE DEVICE
# ─────────────────────────────────────────────────────────────
def process(device: dict) -> bool:
    slug   = device["slug"]
    raw    = RAW_DIR / slug
    found  = []

    print(f"\n  {slug}")

    # ── Bing tiers ────────────────────────────────────────────
    for tier, term in enumerate(device.get("bing", [])):
        if len(found) >= MIN_GOOD_IMAGES and tier > 0:
            break   # already have enough from a previous tier
        dest = raw / f"bing_{tier}"
        label = (term[:60] + '...') if len(term) > 60 else term
        print(f"    Bing tier-{tier}: \"{label}\"")
        crawl_bing(term, dest, BING_PER_TERM)
        found.extend(good_images(dest))

    # ── Baidu fallback ────────────────────────────────────────
    if len(found) < MIN_GOOD_IMAGES:
        for tier, term in enumerate(device.get("baidu", [])):
            if found:
                break
            dest = raw / f"baidu_{tier}"
            print(f"    Baidu fallback-{tier}: \"{term}\"")
            crawl_baidu(term, dest, BAIDU_PER_TERM)
            found.extend(good_images(dest))

    return save_best(found, slug)


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────
def main() -> None:
    SELECTED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    success, failed = [], []
    total = len(DEVICES)

    print(f"Scraping images for {total} devices …")
    print(f"Output: images/<slug>.jpg\n{'─'*56}")

    for i, device in enumerate(DEVICES, 1):
        print(f"[{i:02d}/{total}]", end="")
        try:
            ok = process(device)
            (success if ok else failed).append(device["slug"])
        except Exception as exc:
            print(f"    ✗ exception: {exc}")
            failed.append(device["slug"])

    print(f"\n{'═'*56}")
    print(f"  ✓ Success: {len(success)}/{total}")
    if failed:
        print(f"  ✗ No image: {', '.join(failed)}")
        print("    → Check network, try running scraper.py again for failed slugs.")
    print(f"{'═'*56}\n")


if __name__ == "__main__":
    main()
