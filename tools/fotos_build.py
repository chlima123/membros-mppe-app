#!/usr/bin/env python3
"""Inclui a foto do rosto dos membros no app (fotos/ + campo `foto` do dataset).

Fontes (as duas na MESMA pasta):
  * /Users/chlima/Documents/ChatGPT/hermes_apps_factory/fotos_mppe
    - retratos com o nome do membro no nome do arquivo (acervo Bublup, colagem manual);
    - `evernote_<hash>.png`: miniaturas extraidas do caderno "Membros MPPE" do Evernote
      (uma nota por membro). O nome de cada uma NAO esta no arquivo: veio do titulo da
      nota correspondente no Evernote (ver MAP_EVERNOTE).

Regras:
  * Ordem de precedencia: MAP (retrato nomeado) > MAP_EVERNOTE (nota do Evernote).
  * Cada foto e recortada em quadrado 400x400 centrado no rosto (CROP tem os ajustes
    manuais; o padrao e topo-centro, onde o rosto aparece nos retratos 3x4 do acervo —
    miniaturas ja quadradas (300x300) passam inteiras, sem corte).
  * Saida: `fotos/<id-do-membro>.jpg` (id = slug sem acento, ja existente no dataset).
  * O campo `foto` do dataset.json e preenchido com esse caminho relativo.
  * Depois de rodar: `python3 build.py` (index.html) e `python3 validate.py`.

O que NAO entra (SKIP) esta listado com o motivo: documento, print ou tabela.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("/Users/chlima/Documents/ChatGPT/hermes_apps_factory/fotos_mppe")
OUT_DIR = ROOT / "fotos"
SIZE = 400

# 1) acervo Bublup: nome do arquivo = nome do membro (conferido um a um)
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

# 2) caderno "Membros MPPE" do Evernote: cada arquivo e a miniatura da nota do membro
#    (o vinculo arquivo -> nome veio do titulo da nota, nao do nome do arquivo)
MAP_EVERNOTE = {
    "evernote_5e97993c8bf5d82e.png": "CRISLEY PATRICK TOSTES",
    "evernote_e35bd4d18514755a.png": "IRON MIRANDA DOS ANJOS",
    "evernote_18745b129b8f5de0.png": "TIAGO SALES BOULHOSA GONZALEZ",
    "evernote_79e62348e44db51e.png": None,  # print de conversa - ver SKIP
    "evernote_8f166874c16a885b.png": "ROMULO SIQUEIRA FRANCA",
    "evernote_27fd049ab157de82.png": None,  # fora do Quadro - ver SKIP
    "evernote_532d7e6d58acb100.png": None,  # recorte de jornal - ver SKIP
    "evernote_b74c0ebabe53040b.png": None,  # print de texto - ver SKIP
    "evernote_e81fd99a0cb6d47d.png": None,  # foto de bilhete manuscrito - ver SKIP
    "evernote_53f8117a1d141f98.png": None,  # recorte de jornal - ver SKIP
    "evernote_95a28074446c6c7f.png": None,  # print de tabela - ver SKIP
    "evernote_29266bb10bec45e5.png": "PATRICIA FERREIRA WANDERLEY DE SIQUEIRA GOLDING",
    "evernote_7fd0f6b31c0c9266.png": "EDUARDO PIMENTEL DE VASCONCELOS DE AQUINO",
    "evernote_03aa3cc8209e4ca1.png": "FÁBIO HENRIQUE CAVALCANTI ESTEVAM",
    "evernote_c5b666aed1a8b91b.png": "ANDRÉ ÂNGELO DE ALMEIDA",
    "evernote_688b9faee6bcf684.png": None,  # fora do Quadro - ver SKIP
    "evernote_3c7d00723a35cd22.png": "VINICIUS SILVA DE ARAÚJO",
    "evernote_03daed997575529f.png": None,  # fora do Quadro - ver SKIP
    "evernote_89be2cc5b078ccc4.png": "ERYNE AVILA DOS ANJOS LUNA",
    "evernote_77bbbbb531012a94.png": "RAFAEL MOREIRA STEINBERGER",
    "evernote_3952263db8ac072b.png": "FILIPE COUTINHO LIMA BRITTO",
    "evernote_ffc386e4dc84520e.png": "FABIO DE SOUSA CASTRO",
    "evernote_d70879c1196dbca3.png": "DANIEL JOSÉ MESQUITA MONTEIRO DIAS",
    "evernote_bc3faad22bab514e.png": "GABRIELA LIMA LAPENDA FIGUEIROA",
    "evernote_d20174ab8b0cc4fc.png": "LEANDRO GUEDES MATOS",
    "evernote_8988e0ebbea99627.png": "GUSTAVO HENRIQUE HOLANDA DIAS KERSHAW",
    "evernote_aef142dc76822eb6.png": "THEMES JACIARA MERGULHÃO DA COSTA",
    "evernote_9c52e157cfaeaccd.png": "GABRIELA TAVARES ALMEIDA",
    "evernote_4e6379678e5d21fd.png": None,  # fora do Quadro - ver SKIP
    "evernote_4bc2aee5753d6f15.png": "JOÃO PAULO CARVALHO DOS SANTOS",
    "evernote_f5978aea39bfdaba.png": "ANDREIA APARECIDA MOURA DE COUTO",
    "evernote_edd2eb512b799c93.png": "MILENA DE OLIVEIRA SANTOS DO CARMO",
    "evernote_3c8067bfc044f0ad.png": None,  # fora do Quadro - ver SKIP
    "evernote_8bda3af2b26f7e5a.png": "RODRIGO AMORIM DA SILVA SANTOS",
    "evernote_b2af106121bd8148.png": "FERNANDO HENRIQUE FERREIRA CUNHA RAMOS",
    "evernote_79f4ffbc2eb3980b.png": "MARIA CECILIA SOARES TERTULIANO",
    "evernote_489b7418bd6f8b4f.png": "VINICIUS COSTA E SILVA",
    "evernote_d2687a4e57a9c7a5.png": "WANESSA KELLY ALMEIDA SILVA",
    "evernote_98b1d128988f7d33.png": "LARISSA DE ALMEIDA MOURA ALBUQUERQUE",
    "evernote_87355f3586515ddb.png": None,  # fora do Quadro - ver SKIP
    "evernote_b9658492294c17b8.png": None,  # parecer ministerial - ver SKIP
    "evernote_2b266d30df69bd5d.png": None,  # print de documento - ver SKIP
    "evernote_d33d59caceb69dcf.png": None,  # pagina do Diario Oficial - ver SKIP
    "evernote_c8bb104482b3fcc7.png": "EDUARDO LEAL DOS SANTOS",
    "evernote_fd44c6b8f906f173.png": "GUILHERME GRACILIANO ARAÚJO LIMA",
    "evernote_06b7096451277e7c.png": "ARIANO TERCIO SILVA DE AGUIAR",
    "evernote_8eee2ed07ac99054.png": None,  # print de e-mail - ver SKIP
    "evernote_c31bf5e4a61092d4.png": None,  # imagem impropria na nota - ver SKIP
    "evernote_2d9494164921ddce.png": "RENATA DE LIMA LANDIM",
    "evernote_0e77435a9fc19845.png": "REGINA WANDERLEY LEITE DE ALMEIDA",
}

# nomes em que o titulo da nota do Evernote difere do nome do Quadro (mantido para auditoria)
APELIDOS = {
    "Carolina Gurgel Maia.jpg": "'Maia' no arquivo x 'Lima' no quadro (mesma pessoa, sobrenome alterado)",
    "CAMILA MENDES DE SANTANA.png": "quadro traz o nome de casada: CAMILA MENDES DE SANTANA COUTINHO",
    "PATRICIA FERREIRA WANDERLEY DE SIQUEIRA": "quadro acrescenta 'GOLDING' (nome de casada)",
    "EDUARDO PIMENTEL DE VASCONCELOS AQUINO": "quadro grafa 'VASCONCELOS DE AQUINO'",
    "GUSTAVO HENRIQUE HOLANDA DIAS": "quadro acrescenta 'KERSHAW'",
    "ANDREIA APARECIDA MOURA DO COUTO": "quadro grafa 'MOURA DE COUTO'",
    "MILENA DE OLIVEIRA SANTOS": "quadro acrescenta 'DO CARMO'",
    "LUCIO LUIZ ALMEIDA NETO": "quadro grafa 'LUCIO LUIZ DE ALMEIDA NETO'",
}

# arquivo -> (cx, cy, lado) em fracao da largura/altura; ausente = padrao do retrato
CROP = {
    # retrato largo: rosto do homem no terco direito, abaixo do meio
    "André Jacinto de Almeida Neto.png": (0.70, 0.60, 0.60),
    # retrato com crianca no canto esquerdo: recorta mais a direita
    "Ariano Tercio Silva de Aguiar.png": (0.55, 0.30, 0.95),
    # selfie com a catedral: pessoa a direita do quadro
    "CAMILA MENDES DE SANTANA.png": (0.64, 0.34, 0.85),
    # selfie de duas pessoas: recorta o homem (a esquerda)
    "Diogenes Luciano Nogueira Moreira.png": (0.33, 0.40, 0.68),
    # selfie com outra pessoa no canto direito: fecha no rosto da promotora
    "evernote_0e77435a9fc19845.png": (0.42, 0.42, 0.80),
}

# arquivos sem foto de rosto (documento/print/tabela) - nao entram no app
SKIP = {
    "Ademilton das Virgens Carvalho Leitão.jpg": "relatorio de correicao (documento)",
    "Adna Leonor Deo Vasconcelos.jpg": "ANEXO II - formulario da Corregedoria",
    "Adriano Camargo Vieira.jpg": "documento do MPPE",
    "Allison de Jesus Cavalcanti Carvalho.jpg": "relatorio de correicao (documento)",
    "André Silvani da Silva Carneiro.jpg": "print de processo PJe",
    "CRISTIANE MARIA CAITANO DA SILVA.jpg": "ANEXO II - formulario da Corregedoria",
    "Camila Amaral de Melo Teixeira.jpg": "relatorio de correicao (documento)",
    "Christiane Ramalho Leite Cavalcante.jpg": "portaria CGMP (documento)",
    "DELUSE AMARAL ROLIM FLORENTINO.jpg": "ANEXO II - formulario da Corregedoria",
    "ELEONORA MARISE DA SILVA RODRIGUES.jpg": "ANEXO II - formulario da Corregedoria",
    "EVA REGINA DE ALBUQUERQUE BRASIL.jpg": "ANEXO II - formulario da Corregedoria",
    "FLAVIO HENRIQUE SOUZA DOS SANTOS.jpg": "relatorio de correicao (documento)",
    "Filipe Wesley Leandro Pinheiro da Silva.jpg": "relatorio de correicao (documento)",
    "Édipo Soares Cavalcante Filho.jpg": "print de pagina do site do MPPE",
    "Vitaliciamento 1.jpg": "tabela de faixas de judo (documento)",
    "Vitaliciamento 2.jpg": "tabela de posse com 5 retratos (documento)",
    "Vitaliciamento 3.jpg": "tabela de promotores nomeados com 6 retratos (documento)",
    "evernote_2b266d30df69bd5d.png": "print de documento assinado por promotor",
    "evernote_532d7e6d58acb100.png": "recorte de jornal",
    "evernote_53f8117a1d141f98.png": "recorte de jornal",
    "evernote_79e62348e44db51e.png": "print de conversa (WhatsApp)",
    "evernote_8eee2ed07ac99054.png": "print de e-mail da Corregedoria",
    "evernote_95a28074446c6c7f.png": "print de tabela da Corregedoria",
    "evernote_b74c0ebabe53040b.png": "print de texto juridico (celular)",
    "evernote_b9658492294c17b8.png": "foto de parecer ministerial (documento)",
    "evernote_27fd049ab157de82.png": "retrato de SONIA MARA ROCHA CARNEIRO, fora do Quadro Geral",
    "evernote_688b9faee6bcf684.png": "retrato de NARA THAMYRES BRITO GUIMARAES, fora do Quadro",
    "evernote_03daed997575529f.png": "retrato de TIAGO MEIRA DE SOUZA, fora do Quadro Geral",
    "evernote_4e6379678e5d21fd.png": "retrato de BRUNO MIQUELAO GOTTARDI, fora do Quadro Geral",
    "evernote_3c8067bfc044f0ad.png": "retrato de KELLY JANE RODRIGUES PRADO, fora do Quadro Geral",
    "evernote_87355f3586515ddb.png": "retrato de FERNANDO ANTONIO CARVALHO RIBEIRO PESSOA, fora do Quadro",
    "evernote_e81fd99a0cb6d47d.png": "foto de bilhete manuscrito (nao e retrato)",
    "evernote_d33d59caceb69dcf.png": "foto de pagina do Diario Oficial (documento)",
    "evernote_c31bf5e4a61092d4.png": "IMAGEM IMPROPRIA na nota do Evernote (nudez) - nao publicar",
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
        m["foto"] = ""

    feitos, erros, sem_foto = [], [], []
    aplicados = set()

    # 1) retratos nomeados (Bublup) - tem precedencia
    fila = [(arq, nome, "Bublup") for arq, nome in MAP.items()]
    # 2) miniaturas do Evernote - so para quem ainda nao tem foto
    fila += [(arq, nome, "Evernote") for arq, nome in MAP_EVERNOTE.items() if nome]

    for arq, nome, fonte in fila:
        membro = by_name.get(nome)
        if membro is None:
            erros.append(f"membro nao encontrado no dataset: {nome}")
            continue
        if membro["id"] in aplicados:
            sem_foto.append(f"{arq}: ja coberto por outro retrato ({membro['nome']})")
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
        aplicados.add(membro["id"])
        feitos.append((membro["nome"], f"{arq} [{fonte}] -> {destino.name}"))

    # remove fotos orfas (arquivo que nao corresponde mais a nenhum registro)
    validos = {Path(m["foto"]).name for m in data if m.get("foto")}
    for f in OUT_DIR.glob("*.jpg"):
        if f.name not in validos:
            f.unlink()
            print(f"orfao removido: {f.name}")

    (ROOT / "dataset.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    print(f"fotos aplicadas: {len(feitos)}")
    for nome, info in feitos:
        print(f"  {nome}: {info}")
    if sem_foto:
        print(f"\nnao aplicadas (membro ja tinha foto): {len(sem_foto)}")
        for s in sem_foto:
            print(f"  {s}")
    print(f"\nignorados (documento/fora do quadro): {len(SKIP)}")
    if erros:
        print("\nERROS:", *erros, sep="\n  ", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
