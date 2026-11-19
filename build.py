#!/usr/bin/env python3
"""Gera index.html a partir de app_template.html e dataset.json."""

from pathlib import Path
import sys

MARKER = "__DATA_JSON__"


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
