#!/usr/bin/env python3
"""Inclui a foto do rosto dos membros no app (fotos/ + campo `foto` do dataset).

Fonte: /Users/chlima/Documents/ChatGPT/hermes_apps_factory/fotos_mppe
(colagem do acervo Bublup — mistura fotos de rosto com PDFs/prints de
correição e de páginas do MPPE; só as fotos entram).

Regras:
  * Cada foto é recortada em quadrado 400x400 centrado no rosto
    (CROP tem os ajustes manuais por arquivo; o padrão é topo-centro,
    que é onde o rosto aparece nos retratos 3x4 do acervo).
  * O arquivo de saída é `fotos/<id-do-membro>.jpg` (id = slug sem acento).
  * O campo `foto` do dataset.json é preenchido com esse caminho relativo.
  * Depois de rodar: `python3 build.py` (index.html) e `validate.py`.

O que NÃO entra (SKIP) está listado com o motivo: sem foto de rosto no arquivo.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("/Users/chlima/Documents/ChatGPT/hermes_apps_factory/fotos_mppe")
OUT_DIR = ROOT / "fotos"
SIZE = 400

# arquivo de origem -> nome do membro no dataset (conferido um a um)
MAP = {
    "ANA CLEZIA FERREIRA NUNES.png": "ANA CLÉZIA FERREIRA NUNES",
    "ANA JOEMIA MARQUES DA ROCHA.png": "ANA JOEMIA MARQUES DA ROCHA",
    "ANA MARIA MOURA MARANHAO DA FONTE.png": "ANA MARIA MOURA MARANHAO DA FONTE",
    "Ana Rita Coelho Colaço Dias.png": "ANA RITA COELHO COLAÇO DIAS",
    "André Jacinto de Almeida Neto.png": "ANDRÉ JACINTO DE ALMEIDA NETO",
    "Ariano Tercio Silva de Aguiar.png": "ARIANO TERCIO SILVA DE AGUIAR",
    "CAMILA MENDES DE SANTANA.png": "CAMILA MENDES DE SANTANA COUTINHO",
    "Carolina Gurgel Maia.jpg": "CAROLINA GURGEL LIMA",
    "Diogenes Luciano Nogueira Moreira.png": "DIÓGENES LUCIANO NOGUEIRA MOREIRA",
}

# nome no arquivo diferente do nome no quadro (mantido para auditoria)
APELIDOS = {
    "Carolina Gurgel Maia.jpg": "'Maia' no arquivo x 'Lima' no quadro (mesma pessoa, sobrenome alterado)",
    "CAMILA MENDES DE SANTANA.png": "quadro traz o nome de casada: CAMILA MENDES DE SANTANA COUTINHO",
}

# arquivo -> (cx, cy, lado) em fração da largura/altura; ausente = padrão retrato
CROP = {
    # retrato largo: rosto do homem no terço direito, abaixo do meio
    "André Jacinto de Almeida Neto.png": (0.70, 0.60, 0.60),
    # retrato com criança no canto esquerdo: recorta mais à direita
    "Ariano Tercio Silva de Aguiar.png": (0.55, 0.30, 0.95),
    # selfie com a catedral: pessoa à direita do quadro
    "CAMILA MENDES DE SANTANA.png": (0.64, 0.34, 0.85),
    # selfie de duas pessoas: recorta o homem (à esquerda)
    "Diogenes Luciano Nogueira Moreira.png": (0.33, 0.40, 0.68),
}

# arquivos sem foto de rosto (documento/print) — não entram no app
SKIP = {
    "Ademilton das Virgens Carvalho Leitão.jpg": "relatório de correição (documento)",
    "Adna Leonor Deo Vasconcelos.jpg": "ANEXO II - formulário da Corregedoria",
    "Adriano Camargo Vieira.jpg": "documento do MPPE",
    "Allison de Jesus Cavalcanti Carvalho.jpg": "relatório de correição (documento)",
    "André Silvani da Silva Carneiro.jpg": "print de processo PJe",
    "CRISTIANE MARIA CAITANO DA SILVA.jpg": "ANEXO II - formulário da Corregedoria",
    "Camila Amaral de Melo Teixeira.jpg": "relatório de correição (documento)",
    "Christiane Ramalho Leite Cavalcante.jpg": "portaria CGMP (documento)",
    "DELUSE AMARAL ROLIM FLORENTINO.jpg": "ANEXO II - formulário da Corregedoria",
    "ELEONORA MARISE DA SILVA RODRIGUES.jpg": "ANEXO II - formulário da Corregedoria",
    "EVA REGINA DE ALBUQUERQUE BRASIL.jpg": "ANEXO II - formulário da Corregedoria",
    "FLAVIO HENRIQUE SOUZA DOS SANTOS.jpg": "relatório de correição (documento)",
    "Filipe Wesley Leandro Pinheiro da Silva.jpg": "relatório de correição (documento)",
    "Édipo Soares Cavalcante Filho.jpg": "print de página do site do MPPE",
}


def slug(nome: str) -> str:
    import unicodedata

    nf = unicodedata.normalize("NFKD", nome)
    base = "".join(c for c in nf if not unicodedata.combining(c)).lower()
    out = []
    for ch in base:
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def crop_square(img: Image.Image, spec, w: int, h: int) -> Image.Image:
    cx, cy, lado = spec if spec else (0.5, 0.32, 1.0)
    side = min(int(round(lado * min(w, h))), min(w, h))
    side = max(1, side)
    left = max(0, min(int(round(cx * w - side / 2)), w - side))
    top = max(0, min(int(round(cy * h - side / 2)), h - side))
    return img.crop((left, top, left + side, top + side))


def main() -> int:
    data = json.loads((ROOT / "dataset.json").read_text(encoding="utf-8"))
    by_name = {m["nome"]: m for m in data}
    OUT_DIR.mkdir(exist_ok=True)

    for m in data:
        if m.get("foto"):
            m["foto"] = ""

    feitos, erros = [], []
    for arq, nome in MAP.items():
        membro = by_name.get(nome)
        if membro is None:
            erros.append(f"membro nao encontrado no dataset: {nome}")
            continue
        origem = SOURCE / arq
        if not origem.is_file():
            erros.append(f"foto ausente: {origem}")
            continue
        img = ImageOps.exif_transpose(Image.open(origem)).convert("RGB")
        w, h = img.size
        quad = crop_square(img, CROP.get(arq), w, h).resize(
            (SIZE, SIZE), Image.Resampling.LANCZOS
        )
        destino = OUT_DIR / (membro["id"] + ".jpg")
        quad.save(destino, "JPEG", quality=86, optimize=True, progressive=True)
        membro["foto"] = f"fotos/{destino.name}"
        feitos.append((membro["nome"], f"{origem.name} -> {destino.name}"))

    (ROOT / "dataset.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    print(f"fotos aplicadas: {len(feitos)}")
    for nome, info in feitos:
        print(f"  {nome}: {info}")
    if erros:
        print("\nERROS:", *erros, sep="\n  ", file=sys.stderr)
        return 1
    print(f"\nignorados (documento, sem rosto): {len(SKIP)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
