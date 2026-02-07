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

2) Ejecuta el script:

```
python descargar_anuncios_meta.py --page-id 100054211200913 --page-name "Be Grand" --countries MX
```

El script guardara un archivo JSON en el mismo directorio.

## Opciones utiles

- `--limit 100` Cantidad por pagina (maximo 100).
- `--max-ads 200` Limite total (0 = sin limite).
- `--countries MX,US` Lista de paises en formato ISO.
- `--token` Para pasar el token directo por linea de comandos.

## Nota sobre errores al copiar y pegar

Si pegas muchas lineas dentro del interprete interactivo de Python (`>>>`)
puedes obtener errores como `SyntaxError: EOL while scanning string literal`.
Para evitarlo, ejecuta el archivo con `python descargar_anuncios_meta.py`.
