#!/usr/bin/env python3
"""Enriquece o dataset do app com datas funcionais e antiguidade.

Fontes (somente leitura):
  1. Listas de Antiguidade do CSMP (vault, 4 listas, data-base 14/10/2026):
     posicao na lista, data de nascimento, tempo na entrada (dias) e tempo no MPPE (dias).
     -> data de ingresso no MP      = data_base - tempo_no_mppe
     -> data de ingresso na entrada = data_base - tempo_na_entrancia
  2. Fichas funcionais do vault (Membros/*.md), bloco "Cargo atual (Quadro Geral OFICIAL)":
     "Ultimo provimento" + "Data" + "Portaria" -> data de inicio no cargo atual.

Casamento de nomes: tools/nome_match.py (exato, subconjunto de tokens, e difflib >= 0.86
com mesmo prenome e candidato unico). NUNCA "N tokens em comum": casa homonimo parcial.

Saida: enriquecimento.json  {id: {nascimento, ingressoMP, ingressoEntrancia,
                                 inicioCargo, ato, portaria, posicaoAntiguidade,
                                 listaAntiguidade, nomeLista, diasMP, diasEntrancia}}
"""
import json, re, os, glob, datetime, collections, difflib, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from nome_match import match, toks, fold  # noqa: E402

VAULT = "/Users/chlima/Documents/chlima123/001_TRABALHO"
LISTAS = os.path.join(VAULT, "Listas_Antiguidade")
FICHAS = os.path.join(VAULT, "Membros")
DATA_BASE = datetime.date(2026, 10, 14)


def d(s):
    try:
        return datetime.datetime.strptime(str(s).strip(), "%d/%m/%Y").date()
    except Exception:
        return None


# ---------- 1. Listas de antiguidade ----------
LISTS = [
    ("1ª Entrância", "Lista de Antiguidade 1ª Entrância.md"),
    ("2ª Entrância", "Lista de Antiguidade 2ª entrância.md"),
    ("3ª Entrância", "Lista de Antiguidade 3ª entrância.md"),
    ("2ª Instância", "Lista de Antiguidade 2ª Instância (Procuradores de Justiça).md"),
]
anti = {}
for lista_nome, arq in LISTS:
    path = os.path.join(LISTAS, arq)
    if not os.path.exists(path):
        sys.exit(f"ERRO: lista ausente: {path}")
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d{2}/\d{2}/\d{4})\s*\|", line)
        if not m:
            continue
        pos, nome, de, dm, nasc = m.groups()
        anti[" ".join(toks(nome))] = {
            "posicaoAntiguidade": int(pos),
            "listaAntiguidade": lista_nome,
            "nomeLista": nome.strip(),
            "diasEntrancia": int(de),
            "diasMP": int(dm),
            "nascimento": nasc,
            "ingressoMP": (DATA_BASE - datetime.timedelta(days=int(dm))).strftime("%d/%m/%Y"),
            "ingressoEntrancia": (DATA_BASE - datetime.timedelta(days=int(de))).strftime("%d/%m/%Y"),
        }
print(f"antiguidade: {len(anti)} linhas em {len(LISTS)} listas (data-base 14/10/2026)")


def casar_antiguidade(nome):
    v, regra = match(nome, anti)
    if v:
        return v, regra
    if regra.startswith("ambiguo"):
        return None, regra
    # camada final: grafia divergente (VEIGA/VIEGA, SOUSA/SOUZA...), mesmo prenome, unico
    a = " ".join(toks(nome))
    first = toks(nome)[0] if toks(nome) else ""
    cands = []
    for k in anti:
        kt = k.split()
        if not kt or difflib.SequenceMatcher(None, first, kt[0]).ratio() < 0.85:
            continue
        r = difflib.SequenceMatcher(None, a, k).ratio()
        if r >= 0.86:
            cands.append((r, k))
    cands.sort(reverse=True)
    if len(cands) == 1:
        return anti[cands[0][1]], "R4-fuzzy"
    return None, "sem-match" if not cands else "ambiguo-fuzzy"


# ---------- 2. Fichas funcionais ----------
def campo(t, nome):
    m = re.search(r"\|\s*" + nome + r"\s*\|\s*([^|\n]*)\|", t)
    return m.group(1).strip() if m else ""


fichas = {}
for f in glob.glob(os.path.join(FICHAS, "*", "*.md")):
    t = open(f, encoding="utf-8").read()
    if "Quadro Geral OFICIAL" not in t:
        continue
    nome = os.path.basename(f)[:-3].replace("_", " ")
    data = campo(t, "Data")
    if not d(data):
        continue
    fichas[" ".join(toks(nome))] = {
        "inicioCargo": data,
        "ato": campo(t, "Último provimento"),
        "portaria": campo(t, "Portaria"),
    }
print(f"fichas funcionais com data do ultimo provimento: {len(fichas)}")


def casar_ficha(nome):
    v, regra = match(nome, fichas)
    if v:
        return v, regra
    a = " ".join(toks(nome))
    cands = []
    for k in fichas:
        if not k or toks(nome)[0] != k.split()[0]:
            continue
        r = difflib.SequenceMatcher(None, a, k).ratio()
        if r >= 0.86:
            cands.append((r, k))
    cands.sort(reverse=True)
    if len(cands) == 1:
        return fichas[cands[0][1]], "R4-fuzzy"
    return None, "sem-match"


# ---------- 3. Merge ----------
ds = json.load(open(os.path.join(APP, "dataset.json"), encoding="utf-8"))
out, sem_anti, sem_ficha, stats = {}, [], [], collections.Counter()
for r in ds:
    a, ra = casar_antiguidade(r["nome"])
    fi, rf = casar_ficha(r["nome"])
    stats["anti_" + ra] += 1
    stats["ficha_" + rf] += 1
    if a:
        out.setdefault(r["id"], {}).update(a)
    else:
        sem_anti.append((r["nome"], ra))
    if fi:
        out.setdefault(r["id"], {}).update(fi)
    else:
        sem_ficha.append((r["nome"], rf))

print("casamento antiguidade:", {k[5:]: v for k, v in stats.items() if k.startswith("anti_")})
print("casamento ficha:      ", {k[6:]: v for k, v in stats.items() if k.startswith("ficha_")})
print(f"dataset: {len(ds)} | antiguidade: {len(ds)-len(sem_anti)} | inicio de cargo: {len(ds)-len(sem_ficha)}")
if sem_anti:
    print("sem antiguidade:", len(sem_anti))
    for n, r in sem_anti:
        print("   -", n, f"({r})")
if sem_ficha:
    print("sem ficha:", len(sem_ficha))
    for n, r in sem_ficha:
        print("   -", n, f"({r})")

json.dump(out, open(os.path.join(APP, "enriquecimento.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))

# ---------- 4. Overrides manuais (fichas com layout próprio / divergências de grafia) ----------
OVR = os.path.join(HERE, "overrides.json")
if os.path.exists(OVR):
    ovr = json.load(open(OVR, encoding="utf-8"))
    ids = {r["id"] for r in ds}
    for _id, campos in ovr.items():
        if _id not in ids:
            sys.exit(f"ERRO override: id inexistente no dataset: {_id}")
        limpos = {k: v for k, v in campos.items() if not k.startswith("_")}
        if limpos:
            out.setdefault(_id, {}).update(limpos)
    json.dump(out, open(os.path.join(APP, "enriquecimento.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"overrides aplicados: {len(ovr)}")

print(f"gravado enriquecimento.json: {len(out)} registros")
