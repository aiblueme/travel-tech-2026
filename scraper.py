"""
scraper.py — Product image downloader for 2026 Travel Tech Comparison
Uses icrawler to pull clean product photos from Bing (global) and Baidu
(strong for Asian market device listings).

Install:
    pip install icrawler Pillow

Run:
    python scraper.py

Output structure:
    images/
    ├── apple_macbook_air_m4/
    │   ├── bing_000001.jpg
    │   └── baidu_000001.jpg
    ├── asus_zenbook_s14_oled/
    │   └── ...
    └── ...

After scraping, drop the images/ directory alongside index.html in the
nginx container — or reference them from the HTML with <img src="images/...">
"""

from icrawler.builtin import BingImageCrawler, BaiduImageCrawler
import os
import re

# ──────────────────────────────────────────────────────────────
#  Device definitions
#  bing_q  — English query targeting clean product/press photos
#  baidu_q — Chinese query; Baidu indexes more SEA market images
#             and manufacturer press kits for Asian distributors
# ──────────────────────────────────────────────────────────────
DEVICES = [
    {
        "slug":    "apple_macbook_air_m4",
        "bing_q":  "Apple MacBook Air 13 M4 2025 product photo press",
        "baidu_q": "苹果 MacBook Air M4 官方图",
    },
    {
        "slug":    "asus_zenbook_s14_oled",
        "bing_q":  "ASUS ZenBook S 14 OLED 2025 laptop press photo white background",
        "baidu_q": "华硕 ZenBook S14 OLED 产品图",
    },
    {
        "slug":    "lg_gram_14_2026",
        "bing_q":  "LG Gram 14 2026 laptop official press image",
        "baidu_q": "LG Gram 14 2026 轻薄本 产品",
    },
    {
        "slug":    "lenovo_thinkpad_x1_carbon_gen13",
        "bing_q":  "Lenovo ThinkPad X1 Carbon Gen 13 2025 press photo",
        "baidu_q": "联想 ThinkPad X1 Carbon 13代 官方图",
    },
    {
        "slug":    "dell_xps_13_2025",
        "bing_q":  "Dell XPS 13 9350 2025 laptop press official",
        "baidu_q": "戴尔 XPS 13 2025 产品图",
    },
    {
        "slug":    "samsung_galaxy_book5_pro14",
        "bing_q":  "Samsung Galaxy Book5 Pro 14 press photo official",
        "baidu_q": "三星 Galaxy Book5 Pro 14 产品图",
    },
    {
        "slug":    "hp_omnibook_ultra14",
        "bing_q":  "HP OmniBook Ultra 14 2025 laptop official press",
        "baidu_q": "惠普 OmniBook Ultra 14 产品图",
    },
    {
        "slug":    "microsoft_surface_pro11",
        "bing_q":  "Microsoft Surface Pro 11 Snapdragon press photo official",
        "baidu_q": "微软 Surface Pro 11 官方产品图",
    },
    {
        "slug":    "framework_13_amd",
        "bing_q":  "Framework Laptop 13 AMD Ryzen AI 300 press photo",
        "baidu_q": "Framework Laptop 13 AMD 产品图",
    },
    {
        "slug":    "acer_swift14_ai",
        "bing_q":  "Acer Swift 14 AI 2025 laptop official press photo",
        "baidu_q": "宏碁 Swift 14 AI 产品图",
    },
    {
        "slug":    "lenovo_yoga_slim7x_2025",
        "bing_q":  "Lenovo Yoga Slim 7x 2025 Snapdragon press photo",
        "baidu_q": "联想 Yoga Slim 7x 2025 产品图",
    },
    {
        "slug":    "huawei_matebook_x_pro_2025",
        "bing_q":  "Huawei MateBook X Pro 2025 official press photo",
        "baidu_q": "华为 MateBook X Pro 2025 官方图",
    },
    {
        "slug":    "razer_blade_14_2025",
        "bing_q":  "Razer Blade 14 2025 laptop press photo official",
        "baidu_q": "雷蛇 Blade 14 2025 产品图",
    },
]

# ──────────────────────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────────────────────
BASE_DIR    = "images"
BING_COUNT  = 3   # per device; enough for a manual pick
BAIDU_COUNT = 2   # Baidu tends toward duplicates at higher counts

# icrawler filters — target dimensions that are plausibly product shots
FILTERS = dict(
    size="large",           # skip thumbnails
    type="photo",           # skip illustrations / clipart
    license="creativecommon",  # prefer open-license images
)

# ──────────────────────────────────────────────────────────────
#  Scrape loop
# ──────────────────────────────────────────────────────────────
def scrape_device(device: dict) -> None:
    slug = device["slug"]
    print(f"\n{'─' * 56}")
    print(f"  Device: {slug}")

    # ── Bing ──────────────────────────────────────────────────
    bing_dir = os.path.join(BASE_DIR, slug, "bing")
    os.makedirs(bing_dir, exist_ok=True)

    bing = BingImageCrawler(
        feeder_threads=1,
        parser_threads=2,
        downloader_threads=4,
        storage={"root_dir": bing_dir},
    )
    bing.crawl(
        keyword=device["bing_q"],
        filters=FILTERS,
        max_num=BING_COUNT,
        file_idx_offset=0,
    )
    print(f"  ✓ Bing  → {bing_dir}")

    # ── Baidu ─────────────────────────────────────────────────
    baidu_dir = os.path.join(BASE_DIR, slug, "baidu")
    os.makedirs(baidu_dir, exist_ok=True)

    baidu = BaiduImageCrawler(
        feeder_threads=1,
        parser_threads=2,
        downloader_threads=4,
        storage={"root_dir": baidu_dir},
    )
    baidu.crawl(
        keyword=device["baidu_q"],
        max_num=BAIDU_COUNT,
        file_idx_offset=0,
    )
    print(f"  ✓ Baidu → {baidu_dir}")


def main() -> None:
    print(f"Saving images to ./{BASE_DIR}/")
    os.makedirs(BASE_DIR, exist_ok=True)

    for device in DEVICES:
        try:
            scrape_device(device)
        except Exception as exc:
            # Don't abort the whole run if one device fails
            print(f"  ✗ Error scraping {device['slug']}: {exc}")

    print(f"\n{'═' * 56}")
    print(f"  Done. Review ./{BASE_DIR}/ and pick the best shot per device.")
    print(f"  Rename chosen files to <slug>.jpg and serve from nginx.")
    print(f"{'═' * 56}\n")


if __name__ == "__main__":
    main()
