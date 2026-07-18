"""Тянет CC0/Public-domain SVG с Wikimedia Commons, конвертирует в вышивку,
добавляет в catalog.json. Только строго свободные лицензии.

Запуск:  python fetch_commons.py [сколько_добавить]
"""
import json
import re
import sys
from pathlib import Path

import requests

import convert_svg

ROOT = Path(__file__).resolve().parent
DESIGNS = ROOT / "designs"
THUMBS = ROOT / "thumbs"
DESIGNS.mkdir(exist_ok=True)
THUMBS.mkdir(exist_ok=True)
RAW = "https://raw.githubusercontent.com/TimurZak-Zak/embroidery-catalog/main"
UA = "EmbroideryStudio/1.0 (https://github.com/TimurZak-Zak; timka725@gmail.com)"

API = "https://commons.wikimedia.org/w/api.php"

# ключевое слово -> категория в каталоге
KEYWORDS = [
    ("heart silhouette", "Сердечки"),
    ("star outline", "Звёзды"),
    ("flower silhouette", "Цветы"),
    ("leaf silhouette", "Листья"),
    ("butterfly silhouette", "Бабочки"),
    ("bird silhouette", "Птицы"),
    ("cat silhouette", "Животные"),
    ("fish silhouette", "Животные"),
    ("tree silhouette", "Природа"),
    ("snowflake", "Зима"),
    ("anchor", "Морское"),
    ("crown outline", "Узоры"),
    ("fleur de lis", "Узоры"),
    ("paw print", "Животные"),
]

PALETTE = [0x8A3B3B, 0xB5651D, 0x4C6B8A, 0x5F7A4F, 0x8367C7, 0x2A9D8F, 0xC0577A]

FREE = ("cc0", "public domain", "no restrictions", "pd")


def _is_free(license_short: str) -> bool:
    s = (license_short or "").lower()
    return any(tok in s for tok in FREE)


def _slug(title: str) -> str:
    base = re.sub(r"^File:", "", title)
    base = re.sub(r"\.svg$", "", base, flags=re.I)
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()
    return base[:48] or "design"


def _clean(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html or "").strip()


def search(term, limit=10):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{term} filetype:drawing", "gsrnamespace": "6",
        "gsrlimit": str(limit), "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
    }
    r = requests.get(API, params=params, headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    return list(pages.values())


def load_catalog():
    f = ROOT / "catalog.json"
    if f.exists():
        return json.loads(f.read_text("utf-8"))
    return []


def main(target=6):
    catalog = load_catalog()
    have = {c["id"] for c in catalog}
    added = 0
    for term, category in KEYWORDS:
        if added >= target:
            break
        try:
            pages = search(term)
        except Exception as e:
            print("поиск не удался:", term, e)
            continue
        for pg in pages:
            if added >= target:
                break
            info = (pg.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            lic = meta.get("LicenseShortName", {}).get("value", "")
            mime = info.get("mime", "")
            size = info.get("size", 0) or 0
            url = info.get("url", "")
            if "svg" not in mime or not _is_free(lic) or size > 400_000:
                continue
            slug = _slug(pg.get("title", ""))
            if slug in have:
                continue
            try:
                svg_text = requests.get(
                    url, headers={"User-Agent": UA}, timeout=25
                ).text
                rgb = PALETTE[added % len(PALETTE)]
                size_mm = convert_svg.convert(
                    svg_text, DESIGNS / f"{slug}.vp3", THUMBS / f"{slug}.png", rgb
                )
            except Exception as e:
                print("конверт не удался:", slug, e)
                continue
            if not size_mm:
                continue
            author = _clean(meta.get("Artist", {}).get("value", "")) or "Wikimedia Commons"
            catalog.append({
                "id": slug,
                "name": re.sub(r"^File:|\.svg$", "", pg.get("title", slug), flags=re.I),
                "category": category,
                "size_mm": size_mm,
                "thumbnail": f"{RAW}/thumbs/{slug}.png",
                "file_url": f"{RAW}/designs/{slug}.vp3",
                "license": lic,
                "author": author[:80],
                "source": url,
            })
            have.add(slug)
            added += 1
            print(f"[+] {slug}  {size_mm['w']}x{size_mm['h']}мм  {lic}")
    (ROOT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), "utf-8"
    )
    print(f"Добавлено: {added}. Всего в каталоге: {len(catalog)}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
