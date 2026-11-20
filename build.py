#!/usr/bin/env python3
"""Gera index.html a partir de app_template.html e dataset.json.

Tambem sincroniza o service worker (sw.js): a lista de fotos precacheadas
(FOTOS) e regerada a partir do campo `foto` do dataset, de forma idempotente.
"""

from pathlib import Path
import json
import re
import sys

MARKER = "__DATA_JSON__"
SW_FOTOS_RE = re.compile(r"^const FOTOS = \[.*?\];$", re.MULTILINE | re.DOTALL)


def sync_sw_fotos(root: Path, dataset_text: str) -> str:
    """Reescreve a constante FOTOS do sw.js com as fotos do dataset."""
    sw_path = root / "sw.js"
    if not sw_path.is_file():
        return "sw.js ausente (precache de fotos ignorado)"

    dados = json.loads(dataset_text)
    fotos = sorted(
        {
            "./" + str(m.get("foto") or "").strip()
            for m in dados
            if str(m.get("foto") or "").strip()
        }
    )
    lista = "const FOTOS = [\n" + "".join(f'  "{f}",\n' for f in fotos) + "];"
    atual = sw_path.read_text(encoding="utf-8")
    if not SW_FOTOS_RE.search(atual):
        return "sw.js sem a constante FOTOS (precache de fotos ignorado)"

    novo = SW_FOTOS_RE.sub(lambda _m: lista, atual, count=1)
    if novo != atual:
        sw_path.write_text(novo, encoding="utf-8")
        return f"sw.js: {len(fotos)} fotos no precache"
    return f"sw.js: {len(fotos)} fotos no precache (sem mudanca)"


def main() -> int:
    root = Path(__file__).resolve().parent
    template_path = root / "app_template.html"
    dataset_path = root / "dataset.json"
    output_path = root / "index.html"

    if not template_path.is_file():
        print(f"Erro: arquivo nao encontrado: {template_path}", file=sys.stderr)
        return 1
    if not dataset_path.is_file():
        print(f"Erro: arquivo nao encontrado: {dataset_path}", file=sys.stderr)
        return 1

    template = template_path.read_text(encoding="utf-8")
    count = template.count(MARKER)
    if count != 1:
        print(
            f"Erro: marcador {MARKER} deve aparecer exatamente 1 vez em "
            f"{template_path.name} (encontrado {count} vez(es)).",
            file=sys.stderr,
        )
        return 1

    dataset_text = dataset_path.read_text(encoding="utf-8").strip()
    if not dataset_text:
        print(f"Erro: {dataset_path.name} esta vazio.", file=sys.stderr)
        return 1

    rendered = template.replace(MARKER, dataset_text, 1)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Gerado {output_path.name} ({output_path.stat().st_size} bytes).")
    print(sync_sw_fotos(root, dataset_text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
