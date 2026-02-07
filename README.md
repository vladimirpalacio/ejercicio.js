# Descarga de anuncios de Meta (Ad Library API)

Este repositorio incluye un script sencillo para descargar anuncios desde la
Meta Ad Library API usando un token de acceso.

## Requisitos

- Python 3.8+
- Token de acceso con permisos para Ad Library API

## Pasos rapidos

1) Exporta tu token:

```
export META_ACCESS_TOKEN="TU_TOKEN_AQUI"
```

2) Ejecuta el script (puedes usar cualquiera de los dos nombres):

```
python3 descargar_anuncios.py --page-id 100054211200913 --page-name "Be Grand" --countries MX
```

Si en Ads Library ves anuncios pero el script no devuelve nada, verifica:
- Que el `page_id` sea el de Ads Library (view_all_page_id).
- Que los paises en `--countries` coincidan con "Paises donde se mostro".

El script guardara un archivo JSON en el mismo directorio.

## Opciones utiles

- `--limit 100` Cantidad por pagina (maximo 100).
- `--max-ads 200` Limite total (0 = sin limite).
- `--countries MX,US` Lista de paises en formato ISO.
- `--ad-status ACTIVE` Filtra por anuncios activos (o INACTIVE/ALL).
- `--ad-type POLITICAL_AND_ISSUE_ADS` Para anuncios de temas sociales/politicos.
- `--token` Para pasar el token directo por linea de comandos.
- `--api-version v24.0` Version de la API de Meta.
- `--download-media` Descarga imagenes y videos del snapshot.
- `--media-dir carpeta` Carpeta destino para media.
- `--min-bytes 10240` Tamano minimo de media para guardar.

## Interfaz grafica (GUI)

Si prefieres interfaz grafica, ejecuta:

```
python3 gui_anuncios_meta.py
```

La GUI permite:
- Configurar token, page_id, paises, estado/tipo de anuncios.
- Limitar anuncios y descargar media.
- Elegir carpeta de salida.

Si tu macOS no soporta Tkinter, usa la interfaz web:

```
python3 web_gui_anuncios.py --port 8000
```

Luego abre http://localhost:8000 en tu navegador.

## Descargar imagenes y videos

Puedes descargar los archivos desde `ad_snapshot_url`:

```
python3 descargar_anuncios_meta.py --page-id 684860751673005 --page-name "Be Grand" --countries MX --ad-status ACTIVE --download-media
```

Esto crea una carpeta `media_<pagina>_<timestamp>` con imagenes y videos.

Si no descarga media, algunos snapshots no exponen URLs directas; intenta con
`--ad-status ALL` o revisa el snapshot en el navegador.

Nota: los links impresos de `ad_snapshot_url` se guardan sin token por
seguridad y pueden expirar rapido. El script agrega el token internamente
cuando descarga el media.

## Nota sobre errores al copiar y pegar

Si pegas muchas lineas dentro del interprete interactivo de Python (`>>>`)
puedes obtener errores como `SyntaxError: EOL while scanning string literal`.
Para evitarlo, ejecuta el archivo con `python3 descargar_anuncios_meta.py`.
