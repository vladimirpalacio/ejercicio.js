#!/usr/bin/env python3
"""
Interfaz web para descargar anuncios con Meta Ad Library API.
Ejecuta un servidor local y abre http://localhost:PUERTO.
"""

import argparse
import html
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs


DEFAULTS = {
    "page_id": "636758826348325",
    "page_name": "Hawkers Co.",
    "countries": "ES",
    "ad_status": "ACTIVE",
    "ad_type": "ALL",
    "limit": "50",
    "max_ads": "50",
    "api_version": "v24.0",
    "min_bytes": "10240",
    "media_dir": "",
    "output_dir": os.getcwd(),
    "download_media": "",
    "keep_snapshot_token": "",
    "allow_gif": "",
    "token": "",
}


def build_command(data):
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "descargar_anuncios_meta.py"
    )
    cmd = [
        sys.executable,
        script_path,
        "--page-id",
        data["page_id"],
        "--page-name",
        data["page_name"] or "pagina",
        "--countries",
        data["countries"],
        "--ad-status",
        data["ad_status"],
        "--ad-type",
        data["ad_type"],
        "--limit",
        data["limit"],
        "--max-ads",
        data["max_ads"],
        "--api-version",
        data["api_version"],
    ]
    if data.get("download_media"):
        cmd.append("--download-media")
        if data.get("media_dir"):
            cmd.extend(["--media-dir", data["media_dir"]])
        cmd.extend(["--min-bytes", data["min_bytes"]])
    if data.get("keep_snapshot_token"):
        cmd.append("--keep-snapshot-token")
    if data.get("allow_gif"):
        cmd.append("--allow-gif")
    return cmd


def html_escape(value):
    return html.escape(value or "", quote=True)


def render_form(data, output="", error=""):
    def opt(value, current):
        return "selected" if value == current else ""

    download_checked = "checked" if data.get("download_media") else ""
    keep_checked = "checked" if data.get("keep_snapshot_token") else ""
    allow_checked = "checked" if data.get("allow_gif") else ""
    error_html = f'<div class="error">{html_escape(error)}</div>' if error else ""
    output_html = f"<pre>{html_escape(output)}</pre>" if output else ""

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Meta Ad Library - Descargador</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    label {{ display: block; margin-top: 10px; font-weight: bold; }}
    input, select {{ padding: 6px; width: 420px; max-width: 100%; }}
    .row {{ display: flex; gap: 16px; flex-wrap: wrap; }}
    .row > div {{ flex: 1 1 280px; }}
    .actions {{ margin-top: 16px; }}
    pre {{ background: #111; color: #eee; padding: 12px; overflow: auto; }}
    .error {{ color: #b00020; font-weight: bold; }}
    .note {{ color: #666; font-size: 0.9em; }}
  </style>
</head>
<body>
  <h1>Descarga de anuncios (Meta)</h1>
  <p class="note">El token no se guarda; se usa solo para esta ejecucion.</p>
  {error_html}
  <form method="post">
    <label>Access token</label>
    <input type="password" name="token" value="{html_escape(data.get("token",""))}" />

    <div class="row">
      <div>
        <label>Page ID</label>
        <input name="page_id" value="{html_escape(data["page_id"])}" />
      </div>
      <div>
        <label>Page name</label>
        <input name="page_name" value="{html_escape(data["page_name"])}" />
      </div>
    </div>

    <div class="row">
      <div>
        <label>Countries (ISO)</label>
        <input name="countries" value="{html_escape(data["countries"])}" />
      </div>
      <div>
        <label>API version</label>
        <input name="api_version" value="{html_escape(data["api_version"])}" />
      </div>
    </div>

    <div class="row">
      <div>
        <label>Ad status</label>
        <select name="ad_status">
          <option {opt("ALL", data["ad_status"])}>ALL</option>
          <option {opt("ACTIVE", data["ad_status"])}>ACTIVE</option>
          <option {opt("INACTIVE", data["ad_status"])}>INACTIVE</option>
        </select>
      </div>
      <div>
        <label>Ad type</label>
        <select name="ad_type">
          <option {opt("ALL", data["ad_type"])}>ALL</option>
          <option {opt("POLITICAL_AND_ISSUE_ADS", data["ad_type"])}>POLITICAL_AND_ISSUE_ADS</option>
        </select>
      </div>
    </div>

    <div class="row">
      <div>
        <label>Limit</label>
        <input name="limit" value="{html_escape(data["limit"])}" />
      </div>
      <div>
        <label>Max ads</label>
        <input name="max_ads" value="{html_escape(data["max_ads"])}" />
      </div>
    </div>

    <label>
      <input type="checkbox" name="download_media" {download_checked} />
      Descargar media (imagenes/videos)
    </label>
    <label>
      <input type="checkbox" name="keep_snapshot_token" {keep_checked} />
      Mantener token en URLs (no recomendado)
    </label>
    <label>
      <input type="checkbox" name="allow_gif" {allow_checked} />
      Permitir GIF (puede traer pixeles)
    </label>

    <div class="row">
      <div>
        <label>Min bytes</label>
        <input name="min_bytes" value="{html_escape(data["min_bytes"])}" />
      </div>
      <div>
        <label>Media dir (opcional)</label>
        <input name="media_dir" value="{html_escape(data["media_dir"])}" />
      </div>
    </div>

    <label>Output dir</label>
    <input name="output_dir" value="{html_escape(data["output_dir"])}" />

    <div class="actions">
      <button type="submit">Descargar anuncios</button>
    </div>
  </form>
  {output_html}
</body>
</html>
"""


class RequestHandler(BaseHTTPRequestHandler):
    def _send(self, body):
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._send(render_form(DEFAULTS.copy()))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        form = parse_qs(body)

        data = DEFAULTS.copy()
        for key in data.keys():
            if key in form:
                data[key] = form[key][0].strip()

        data["download_media"] = "download_media" in form
        data["keep_snapshot_token"] = "keep_snapshot_token" in form
        data["allow_gif"] = "allow_gif" in form

        error = ""
        for required in ("page_id", "countries"):
            if not data[required]:
                error = f"{required} es obligatorio."
                self._send(render_form(data, error=error))
                return
        for field in ("limit", "max_ads", "min_bytes"):
            try:
                int(data[field])
            except ValueError:
                error = f"{field} debe ser un numero."
                self._send(render_form(data, error=error))
                return

        output_dir = data.get("output_dir") or os.getcwd()
        if not os.path.isdir(output_dir):
            error = "La carpeta de salida no existe."
            self._send(render_form(data, error=error))
            return

        env = os.environ.copy()
        if data.get("token"):
            env["META_ACCESS_TOKEN"] = data["token"]

        cmd = build_command(data)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=output_dir,
            )
            output = (result.stdout or "") + (result.stderr or "")
        except Exception as exc:
            output = f"Error ejecutando el proceso: {exc}"

        self._send(render_form(data, output=output))


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def parse_args():
    parser = argparse.ArgumentParser(description="Web GUI para Meta Ad Library.")
    parser.add_argument("--port", type=int, default=8000, help="Puerto local.")
    return parser.parse_args()


def main():
    args = parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), RequestHandler)
    print(f"Servidor activo en http://localhost:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando servidor...")


if __name__ == "__main__":
    main()
