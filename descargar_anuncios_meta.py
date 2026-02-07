#!/usr/bin/env python3
"""
Script simple para descargar anuncios desde Meta Ad Library API.
Uso basico:
  python descargar_anuncios_meta.py --page-id 100054211200913 --page-name "Be Grand"
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import time
from datetime import datetime
from urllib import error, parse, request


DEFAULT_API_VERSION = "v24.0"

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
        "--ad-status",
        default="ALL",
        type=str.upper,
        choices=["ALL", "ACTIVE", "INACTIVE"],
        help="Estado de anuncios: ALL, ACTIVE o INACTIVE.",
    )
    parser.add_argument(
        "--ad-type",
        default="ALL",
        type=str.upper,
        choices=["ALL", "POLITICAL_AND_ISSUE_ADS"],
        help="Tipo de anuncios: ALL o POLITICAL_AND_ISSUE_ADS.",
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
    parser.add_argument(
        "--download-media",
        action="store_true",
        help="Descarga imagenes y videos desde ad_snapshot_url.",
    )
    parser.add_argument(
        "--media-dir",
        default="",
        help="Carpeta para guardar media (default: media_<pagina>_<timestamp>).",
    )
    parser.add_argument(
        "--api-version",
        default=DEFAULT_API_VERSION,
        help="Version de la API (ej: v24.0).",
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


def parse_page_ids(raw_value):
    items = [item.strip() for item in raw_value.split(",") if item.strip()]
    return items


def request_json(url, retries=3):
    attempt = 0
    while True:
        try:
            req = request.Request(url, headers={"User-Agent": "meta-ads-script/1.0"})
            with request.urlopen(req) as resp:
                payload = resp.read().decode("utf-8")
            return json.loads(payload)
        except error.HTTPError as exc:
            if exc.code in (500, 502, 503, 504) and attempt < retries:
                delay = 2**attempt
                print(f"Error {exc.code} del API. Reintentando en {delay}s...")
                time.sleep(delay)
                attempt += 1
                continue
            raise


def request_text(url, retries=3):
    attempt = 0
    while True:
        try:
            req = request.Request(url, headers={"User-Agent": "meta-ads-script/1.0"})
            with request.urlopen(req) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
            return payload
        except error.HTTPError as exc:
            if exc.code in (500, 502, 503, 504) and attempt < retries:
                delay = 2**attempt
                print(f"Error {exc.code} del API. Reintentando en {delay}s...")
                time.sleep(delay)
                attempt += 1
                continue
            raise


def build_start_url(params, api_version):
    query = parse.urlencode(params)
    return f"https://graph.facebook.com/{api_version}/ads_archive?{query}"


def fetch_ads(params, max_ads, api_version):
    ads = []
    url = build_start_url(params, api_version)
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


def strip_access_token(url):
    if not isinstance(url, str) or "access_token=" not in url:
        return url
    parts = parse.urlsplit(url)
    query = parse.parse_qsl(parts.query, keep_blank_values=True)
    filtered = [(key, value) for key, value in query if key != "access_token"]
    new_query = parse.urlencode(filtered)
    return parse.urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def ensure_access_token(url, token):
    if not token or "access_token=" in url:
        return url
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}access_token={parse.quote(token)}"


def extract_media_urls(html):
    urls = set()
    for key in ("image_url", "video_url", "video_hd_url", "video_sd_url", "thumbnail_url"):
        pattern = rf'"{key}":"(.*?)"'
        for raw in re.findall(pattern, html):
            try:
                value = json.loads(f'"{raw}"')
            except json.JSONDecodeError:
                value = raw.replace("\\/", "/")
            if isinstance(value, str) and value.startswith("http"):
                urls.add(value)
    return sorted(urls)


def download_media(url, output_base):
    req = request.Request(url, headers={"User-Agent": "meta-ads-script/1.0"})
    with request.urlopen(req) as resp:
        content_type = (resp.headers.get("Content-Type") or "").split(";")[0]
        data = resp.read()
    ext = os.path.splitext(parse.urlparse(url).path)[1]
    if not ext:
        ext = mimetypes.guess_extension(content_type) or ".bin"
    output_path = f"{output_base}{ext}"
    with open(output_path, "wb") as handle:
        handle.write(data)
    return output_path


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
        "search_page_ids": json.dumps(parse_page_ids(args.page_id)),
        "ad_type": args.ad_type,
        "ad_active_status": args.ad_status,
        "ad_reached_countries": json.dumps(countries),
        "fields": ",".join(DEFAULT_FIELDS),
        "limit": args.limit,
    }

    try:
        ads = fetch_ads(params, args.max_ads, args.api_version)
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

    for ad in ads:
        if isinstance(ad.get("ad_snapshot_url"), str):
            ad["ad_snapshot_url"] = strip_access_token(ad["ad_snapshot_url"])

    active = sum(1 for ad in ads if not ad.get("ad_delivery_stop_time"))
    inactive = len(ads) - active

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(args.page_name)
    filename = f"ads_{slug}_{timestamp}.json"

    output = {
        "metadata": {
            "page_id": args.page_id,
            "page_ids": parse_page_ids(args.page_id),
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

    if args.download_media:
        media_dir = args.media_dir or f"media_{slug}_{timestamp}"
        os.makedirs(media_dir, exist_ok=True)
        downloaded = 0
        for ad in ads:
            ad_id = ad.get("id") or "ad"
            snapshot_url = ad.get("ad_snapshot_url")
            if not snapshot_url:
                continue
            snapshot_url = ensure_access_token(snapshot_url, token)
            try:
                html = request_text(snapshot_url)
            except error.HTTPError as exc:
                print(f"No se pudo leer snapshot {ad_id}: HTTP {exc.code}")
                continue
            except error.URLError as exc:
                print(f"No se pudo leer snapshot {ad_id}: {exc}")
                continue

            media_urls = extract_media_urls(html)
            if not media_urls:
                continue
            for index, media_url in enumerate(media_urls, 1):
                try:
                    output_base = os.path.join(media_dir, f"{ad_id}_{index}")
                    download_media(media_url, output_base)
                    downloaded += 1
                except error.HTTPError as exc:
                    print(f"No se pudo descargar media {ad_id}: HTTP {exc.code}")
                except error.URLError as exc:
                    print(f"No se pudo descargar media {ad_id}: {exc}")
        if downloaded:
            print(f"\nMedia descargada: {downloaded} archivos en {media_dir}")
        else:
            print("\nNo se encontraron imagenes o videos en los snapshots.")

    print("\nDescarga completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
