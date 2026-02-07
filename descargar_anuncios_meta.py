#!/usr/bin/env python3
"""
Script simple para descargar anuncios desde Meta Ad Library API.
Uso basico:
  python descargar_anuncios_meta.py --page-id 100054211200913 --page-name "Be Grand"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from urllib import error, parse, request


API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}/ads_archive"

DEFAULT_FIELDS = [
    "id",
    "page_id",
    "page_name",
    "ad_creation_time",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "publisher_platforms",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Descarga anuncios de Meta Ad Library API."
    )
    parser.add_argument("--page-id", required=True, help="ID de la pagina en Meta.")
    parser.add_argument("--page-name", default="pagina", help="Nombre de la pagina.")
    parser.add_argument(
        "--countries",
        default="MX",
        help="Paises en formato ISO, separados por coma. Ej: MX,US",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Cantidad por pagina (max 100).",
    )
    parser.add_argument(
        "--max-ads",
        type=int,
        default=200,
        help="Limite total de anuncios a descargar (0 = sin limite).",
    )
    parser.add_argument(
        "--token",
        default="",
        help="Token de acceso. Si no se pasa, se usa META_ACCESS_TOKEN.",
    )
    return parser.parse_args()


def get_access_token(args):
    if args.token:
        return args.token
    for env in ("META_ACCESS_TOKEN", "FB_ACCESS_TOKEN", "ACCESS_TOKEN"):
        value = os.getenv(env)
        if value:
            return value
    return ""


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text or "pagina"


def request_json(url):
    req = request.Request(url, headers={"User-Agent": "meta-ads-script/1.0"})
    with request.urlopen(req) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def build_start_url(params):
    query = parse.urlencode(params)
    return f"{BASE_URL}?{query}"


def fetch_ads(params, max_ads):
    ads = []
    url = build_start_url(params)
    while url:
        data = request_json(url)
        if "error" in data:
            err = data["error"]
            message = err.get("message", "Error desconocido")
            code = err.get("code", "N/A")
            raise RuntimeError(f"API error {code}: {message}")

        batch = data.get("data", [])
        ads.extend(batch)

        if max_ads and len(ads) >= max_ads:
            ads = ads[:max_ads]
            break

        url = data.get("paging", {}).get("next")
    return ads


def first_text(ad):
    for key in ("ad_creative_bodies", "ad_creative_link_titles"):
        values = ad.get(key) or []
        if isinstance(values, list) and values:
            if isinstance(values[0], str):
                return values[0]
    return None


def main():
    args = parse_args()
    token = get_access_token(args)
    if not token:
        print("Falta el token. Usa --token o exporta META_ACCESS_TOKEN.")
        return 1

    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    if not countries:
        print("Debes indicar al menos un pais en --countries.")
        return 1

    params = {
        "access_token": token,
        "search_page_ids": args.page_id,
        "ad_type": "ALL",
        "ad_reached_countries": json.dumps(countries),
        "fields": ",".join(DEFAULT_FIELDS),
        "limit": args.limit,
    }

    try:
        ads = fetch_ads(params, args.max_ads)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error {exc.code}: {body}")
        return 1
    except error.URLError as exc:
        print(f"Network error: {exc}")
        return 1
    except RuntimeError as exc:
        print(str(exc))
        return 1

    if not ads:
        print("No se encontraron anuncios para esta pagina.")
        return 0

    active = sum(1 for ad in ads if not ad.get("ad_delivery_stop_time"))
    inactive = len(ads) - active

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(args.page_name)
    filename = f"ads_{slug}_{timestamp}.json"

    output = {
        "metadata": {
            "page_id": args.page_id,
            "page_name": args.page_name,
            "total_ads": len(ads),
            "active_ads": active,
            "inactive_ads": inactive,
            "download_date": timestamp,
        },
        "ads": ads,
    }

    with open(filename, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)

    print(f"Guardado en: {filename}")

    platforms = {}
    for ad in ads:
        for platform in ad.get("publisher_platforms", []) or []:
            platforms[platform] = platforms.get(platform, 0) + 1

    if platforms:
        print("\nPlataformas:")
        for platform, count in sorted(platforms.items()):
            print(f"  {platform}: {count}")

    print("\nPrimeros 5 anuncios:")
    for idx, ad in enumerate(ads[:5], 1):
        text = first_text(ad)
        status = "ACTIVE" if not ad.get("ad_delivery_stop_time") else "INACTIVE"
        print(f"\n  {idx}. {status}")
        if text:
            print(f"     {text[:80]}...")
        print(f"     {ad.get('ad_snapshot_url', 'N/A')}")

    print("\nDescarga completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
