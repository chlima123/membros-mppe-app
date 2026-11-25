#!/usr/bin/env python3
"""Extrai e cruza os dados dos membros do MPPE a partir das fontes locais.

Fontes:
  1. Quadro Geral de Membros (4 telas oficiais parseadas) -> ~/vercel-deploys/quadro-membros-mppe/index.html
     (const DATA = [...]) — fornece NOME, CARGO, PROMOTORIA (município), entrância, circunscrição.
  2. AMPPE 2026 — telefones + link wa.me
  3. Telefones anotados na Corregedoria (fallback de telefone)
  4. Export do diretório de usuários (e-mails @mppe.mp.br)

Saída: dataset.json
"""
import json, re, unicodedata, os, sys

QUADRO = os.path.expanduser("~/vercel-deploys/quadro-membros-mppe/index.html")
VAULT = "/Users/chlima/Documents/chlima123/001_TRABALHO/CGMP/Membros_CGMP"
AMPPE = os.path.join(VAULT, "2026-08-06_amppe_telefones_whatsapp_membros.md")
CORREG = os.path.join(VAULT, "2026-08-31_Telefones_Anotados_Corregedoria.md")
EMAILS = os.path.join(VAULT, "2026-10-06_emails_membros_mppe_export_diretorio.md")
CONTATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contatos_2026-11-24.json")
OUT = "dataset.json"


def fold(s):
    nf = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in nf if not unicodedata.combining(c)).lower()


def toks(n):
    return [t for t in re.findall(r"[a-z]+", fold(n)) if t not in {"de", "da", "do", "das", "dos", "e"}]


def norm_name(n):
    return re.sub(r"\s+", " ", (n or "").strip()).upper()


# ---------- 1. Quadro Geral ----------
html = open(QUADRO, encoding="utf-8").read()
m = re.search(r"const DATA = (\[.*?\]);\n", html, re.S)
if not m:
    sys.exit("ERRO: const DATA nao encontrado no index.html do quadro")
quadro = json.loads(m.group(1))
print(f"quadro registros: {len(quadro)}")

# ---------- 1b. Entradas posteriores (ou nao refletidas) no snapshot do Quadro ----------
# Quem tomou posse depois da captura oficial do Quadro Geral (18/11/2026) nao aparece nas telas
# baixadas; e quem entrou por permuta nacional pode ter deixado o cargo como VAGO na captura.
# O overlay preenche o cargo VAGO do municipio indicado.
#   posse_2026-11-19.json          -- DOE MPPE de 19/11/2026 (portarias PGJ 3.947 a 3.957/2026)
#   entradas_2026-10-06_permuta.json -- permuta nacional MPMG->MPPE (Portaria PGJ 3.357/2026)
BASE = os.path.dirname(os.path.abspath(__file__))
OVERLAYS = [os.path.join(BASE, f) for f in ("posse_2026-11-19.json",
                                            "entradas_2026-10-06_permuta.json")
            if os.path.exists(os.path.join(BASE, f))]
posses = []
for _ov in OVERLAYS:
    _lista = json.load(open(_ov, encoding="utf-8"))
    posses += _lista
    print(f"overlay {os.path.basename(_ov)}: {len(_lista)} entradas")
if posses:
    usados = set()
    for p in posses:
        # Municipio com mais de um cargo vago exige o campo opcional "cargo" na entrada:
        # sem ele o build pegava o primeiro VAGO do municipio (Petrolândia: 2º PJ em vez do 1º).
        alvo = next((i for i, r in enumerate(quadro)
                     if i not in usados
                     and fold(r.get("municipio")) == fold(p["municipio"])
                     and norm_name(r.get("promotor")) == "VAGO"
                     and (not p.get("cargo") or fold(r.get("cargo")) == fold(p["cargo"]))), None)
        if alvo is None:
            sys.exit(f"ERRO overlay: cargo vago nao encontrado em {p['municipio']}"
                     f"{' (' + p['cargo'] + ')' if p.get('cargo') else ''} para {p['nome']}")
        quadro[alvo] = dict(quadro[alvo], promotor=p["nome"], causa=p.get("causa", "Nomeação"))
        usados.add(alvo)
    print(f"entradas aplicadas (overlay): {len(posses)}")
else:
    print(f"aviso: nenhum overlay de entrada encontrado em {BASE}")

# Quem empossou agora nao consta do AMPPE (ago/2026) nem do export de e-mails (jan/2026):
# tentar casar por nome so gera homonimo falso. Ficam sem contato ate a fonte oficial trazer.
POSSE_NOMES = {norm_name(p["nome"]) for p in posses}

cargos_vagos = [r for r in quadro if norm_name(r.get("promotor")) == "VAGO"]
print(f"vagos: {len(cargos_vagos)} / ocupados: {len(quadro) - len(cargos_vagos)}")

ordem_cargo = {"Promotor de Justiça": 0, "Procurador de Justiça": 1}
ENTRANCIA_RANK = {"1ª": 1, "2ª": 2, "3ª": 3, "-": 4}


def cargo_rank(r):
    c = fold(r.get("cargo", ""))
    return (ENTRANCIA_RANK.get(r.get("entrancia", "-"), 9), 0 if "substitut" in c else 1, r.get("cargo", ""))


people = {}
for r in quadro:
    nome = norm_name(r.get("promotor"))
    if nome == "VAGO" or not nome:
        continue
    p = people.setdefault(nome, {"nome": nome, "cargos": []})
    p["cargos"].append(r)

print(f"pessoas distintas no quadro: {len(people)}")
mult = {k: v for k, v in people.items() if len(v["cargos"]) > 1}
print(f"pessoas com mais de um cargo: {len(mult)}")
for k, v in list(mult.items())[:10]:
    print("  ", k, "->", [c["cargo"] + " / " + c["municipio"] for c in v["cargos"]])

def _split(ddd, tel):
    """normaliza cadastros sujos: 8/9 digitos sem DDD, nono digito faltando, prefixo 55."""
    d = re.sub(r"\D", "", (ddd or "") + (tel or ""))
    if d.startswith("55") and len(d) > 11:
        d = d[2:]
    if len(d) in (8, 9):
        d = "81" + d                    # sem DDD = PE
    if len(d) == 10:
        sub = d[2:]
        if sub[0] == "9":
            sub = "9" + sub             # celular cadastrado sem o nono digito
        return d[:2], sub
    if len(d) == 11:
        return d[:2], d[2:]
    return d[:2], d[2:]


def fmt_phone(ddd, tel):
    """Formato de exibicao local: 0 + DDD + numero, sem separador (ex.: 081 994324196)."""
    ddd2, sub = _split(ddd, tel)
    if not re.fullmatch(r"\d{8,9}", sub or ""):
        return (f"{ddd} {tel}").strip()
    return f"0{ddd2} {sub}"


def wa_from(ddd, tel):
    ddd2, sub = _split(ddd, tel)
    if not re.fullmatch(r"\d{8,9}", sub or ""):
        return ""
    return f"https://wa.me/55{ddd2}{sub}"


# ---------- 2. AMPPE ----------
amppe = {}
raw = open(AMPPE, encoding="utf-8").read()
blocks = re.split(r"\n\*\*", raw)
for b in blocks[1:]:
    nome = b.split("**", 1)[0].strip()
    tel = re.search(r"- Telefone:\s*`([^`]+)`", b)
    wa = re.search(r"https://wa\.me/(\d+)", b)
    cond = re.search(r"- Condi[çc][ãa]o:\s*(.+)", b)
    if not nome:
        continue
    _tel = tel.group(1).strip() if tel else ""
    _d = re.sub(r"\D", "", _tel)
    _ddd, _sub = _d[:2] if len(_d) > 9 else "", _d[2:] if len(_d) > 9 else _d
    amppe[norm_name(nome)] = {
        "telefone": _tel,
        "telefoneNorm": fmt_phone(_ddd, _sub) if _tel else "",
        "whatsapp": f"https://wa.me/{wa.group(1)}" if wa else "",
        "whatsappNorm": wa_from(_ddd, _sub) if _tel else "",
        "condicao": cond.group(1).strip() if cond else "",
    }
print(f"AMPPE registros: {len(amppe)}")

# ---------- 3. Corregedoria ----------
correg = {}
for line in open(CORREG, encoding="utf-8"):
    if not line.startswith("|") or line.startswith("|---") or line.startswith("| Nome"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 5:
        continue
    nome, matr, ddd, tel = cells[0], cells[1], cells[2], cells[3]
    if not nome or not re.search(r"\d", tel):
        continue
    correg[norm_name(nome)] = {
        "telefone": fmt_phone(ddd, tel),
        "matricula": matr,
        "whatsapp": wa_from(ddd, tel),
        "vinculo": cells[6] if len(cells) > 6 else "",
    }
print(f"Corregedoria registros: {len(correg)}")

# telefones do AMPPE repetidos em varios membros = erro de cadastro da fonte
from collections import Counter
amppe_freq = Counter(re.sub(r"\D", "", v["telefone"]) for v in amppe.values() if v["telefone"])
amppe_last9 = Counter(re.sub(r"\D", "", v["telefone"])[-9:] for v in amppe.values() if len(re.sub(r"\D", "", v["telefone"])) >= 10)
print("numeros AMPPE repetidos (>=2 membros):",
      [(k, v) for k, v in amppe_last9.items() if v >= 2])

# ---------- 4. E-mails ----------
emails = {}
rows = 0
for line in open(EMAILS, encoding="utf-8"):
    if not line.startswith("|") or line.startswith("|---"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        continue                      # tabela canonica: # | Matricula | Nome | E-mail
    if not re.fullmatch(r"\d+", cells[0]):
        continue
    matr, nome, mail = cells[1], cells[2], cells[3]
    if "@" not in mail:
        continue
    emails[norm_name(nome)] = {"email": mail.lower(), "matricula": re.sub(r"\D", "", matr), "nome": norm_name(nome)}
    rows += 1
print(f"e-mails registros: {len(emails)} (linhas: {rows})")

# ---------- matching ----------
def best_match(alvo, pool):
    """primeiro nome como ancora + maxima interseccao de tokens; exige >=2 tokens em comum."""
    ta = toks(alvo)
    if not ta:
        return None, 0
    first = ta[0]
    best, score = None, 0
    for cand, val in pool.items():
        tc = toks(cand)
        if not tc or first not in tc:
            continue
        inter = len(set(ta) & set(tc))
        if inter > score:
            best, score = cand, inter
    return (best, score) if score >= 2 else (None, score)


def match_by_matricula(matr, pool):
    if not matr:
        return None
    key = str(matr).lstrip("0")
    for cand, val in pool.items():
        if str(val.get("matricula", "")).lstrip("0") == key:
            return cand
    return None


stats = {"amppe": 0, "correg": 0, "amppe_dup": 0, "email": 0}
out = []
for nome, p in people.items():
    cargos = sorted(p["cargos"], key=cargo_rank)
    principal = cargos[0]
    fone, fonte_fone, wa, suspeito = "", "", "", False
    c_am = best_match(nome, amppe) if nome not in POSSE_NOMES else (None, 0)
    c_co = best_match(nome, correg) if nome not in POSSE_NOMES else (None, 0)

    am_ok = c_am[0] and c_am[1] >= 2
    if am_ok:
        cand = amppe[c_am[0]]
        dup = amppe_last9.get(re.sub(r"\D", "", cand["telefone"])[-9:], 0) >= 2
        if not dup:
            fone, wa, fonte_fone = cand["telefoneNorm"], cand["whatsappNorm"], "AMPPE"
            stats["amppe"] += 1
        else:
            # numero repetido em varios cadastros: usa a Corregedoria e, sem ela, marca como suspeito
            if c_co[0] and c_co[1] >= 2:
                fone, wa, fonte_fone = correg[c_co[0]]["telefone"], correg[c_co[0]]["whatsapp"], "Corregedoria"
                stats["amppe_dup"] += 1
            else:
                fone, wa, fonte_fone, suspeito = "", "", "", True   # numero compartilhado no AMPPE: nao confirmado

    if not fone and c_co[0] and c_co[1] >= 2:
        fone, wa, fonte_fone = correg[c_co[0]]["telefone"], correg[c_co[0]]["whatsapp"], "Corregedoria"
        stats["correg"] += 1

    matr = ""
    if fonte_fone == "Corregedoria" and c_co[0]:
        matr = correg[c_co[0]]["matricula"]
    elif am_ok and c_am[0]:
        matr = ""

    email, email_row = "", ""
    c_em = best_match(nome, emails) if nome not in POSSE_NOMES else (None, 0)
    if c_em[0] and c_em[1] >= 2:
        email = emails[c_em[0]]["email"]
        email_row = emails[c_em[0]]["nome"]
        stats["email"] += 1

    out.append({
        "id": re.sub(r"[^a-z0-9]+", "-", fold(nome)).strip("-"),
        "nome": nome,
        "cargo": principal["cargo"],
        "promotoria": principal["municipio"],
        "entrancia": principal["entrancia"],
        "circunscricao": principal["circunscricao"],
        "atribuicao": principal.get("atribuicao", ""),
        "atuacao": principal.get("atuacao", "")[:220],
        "outrosCargos": [{"cargo": c["cargo"], "promotoria": c["municipio"]} for c in cargos[1:]],
        "telefone": fone,
        "whatsapp": wa,
        "email": email,
        "fonteTelefone": fonte_fone,
        "telefoneSuspeito": suspeito,
        "matricula": matr,
        "_emailRow": email_row,
    })

# colisao de e-mail (homonimo no export): vence quem mais se parece com o nome da linha do export
# pos-passe: telefone repetido entre membros = erro de "arrastar" no AMPPE -> desambigua pela Corregedoria
from collections import defaultdict
by9 = defaultdict(list)
for p in out:
    if p["telefone"]:
        by9[re.sub(r"\D", "", p["telefone"])[-9:]].append(p)
for last9, grupo in by9.items():
    if len(grupo) < 2:
        continue
    for p in grupo:
        c = best_match(p["nome"], correg)
        if c[0] and c[1] >= 2:
            alt = correg[c[0]]
            if alt["telefone"] and re.sub(r"\D", "", alt["telefone"])[-9:] != last9:
                p["telefone"], p["whatsapp"], p["fonteTelefone"] = alt["telefone"], alt["whatsapp"], "Corregedoria"
                p["matricula"] = alt["matricula"]
                p["telefoneSuspeito"] = False
    restantes = [p for p in grupo if p["telefone"] and re.sub(r"\D", "", p["telefone"])[-9:] == last9]
    if len(restantes) < 2:
        continue
    confirmados = []
    for p in restantes:
        c = best_match(p["nome"], correg)
        if c[0] and c[1] >= 2 and re.sub(r"\D", "", correg[c[0]]["telefone"])[-9:] == last9:
            confirmados.append(p)
    for p in restantes:
        if p in confirmados:
            p["telefoneSuspeito"] = len(confirmados) > 1
        else:
            p["telefone"], p["whatsapp"], p["telefoneSuspeito"] = "", "", True
    print("telefone repetido", last9, "-> mantidos:", [p["nome"] for p in confirmados],
          "| zerados:", [p["nome"] for p in restantes if p not in confirmados])

mail_freq = Counter(p["email"] for p in out if p["email"])
for mail, n in mail_freq.items():
    if n < 2:
        continue
    grupos = [p for p in out if p["email"] == mail]
    row = grupos[0]["_emailRow"]
    row_toks = set(t for t in re.findall(r"[a-z]+", fold(row)) if t not in {"de", "da", "do", "das", "dos", "e"})
    def score(p):
        toks = set(t for t in re.findall(r"[a-z]+", fold(p["nome"])) if t not in {"de", "da", "do", "das", "dos", "e"})
        return len(toks & row_toks) / max(len(row_toks), 1)
    grupos.sort(key=score, reverse=True)
    keep = grupos[0]
    if score(keep) < 1.0:
        keep, resto = None, grupos
    else:
        resto = grupos[1:]
    for p in resto:
        p["email"] = ""
        p["emailConflito"] = True
    print("colisao de e-mail:", mail, "linha do export =", row, "->", keep["nome"] if keep else "ninguem",
          "| sem e-mail:", [p["nome"] for p in resto])

for p in out:
    p.pop("_emailRow", None)

# ---------- 5. Contatos manuais (overlay por id) ----------
# Quem empossou depois das fontes de contato (AMPPE ago/2026, export jan/2026) está em POSSE_NOMES e
# fica sem telefone: o matching por nome é proibido ali. Contato confirmado de outra origem entra por
# aqui, com a fonte anotada; id inexistente aborta (id não é dado a inventar).
if os.path.exists(CONTATOS):
    manuais = json.load(open(CONTATOS, encoding="utf-8"))
    por_id = {r["id"]: r for r in out}
    aplicados = 0
    for c in manuais:
        r = por_id.get(c.get("id"))
        if r is None:
            sys.exit(f"ERRO contatos: id inexistente no dataset: {c.get('id')}")
        if not any(c.get(k) for k in ("telefone", "email", "matricula")):
            continue
        if c.get("telefone"):
            dig = re.sub(r"\D", "", c["telefone"])
            r["telefone"] = c["telefone"]
            r["whatsapp"] = c.get("whatsapp") or f"https://wa.me/55{dig.lstrip('0')}"
            r["fonteTelefone"] = c.get("fonte", "contato manual")
            r["telefoneSuspeito"] = bool(c.get("suspeito", False))
        if c.get("email"):
            r["email"] = c["email"]
        if c.get("matricula"):
            r["matricula"] = c["matricula"]
        aplicados += 1
    print(f"contatos manuais aplicados: {aplicados} ({os.path.basename(CONTATOS)})")
else:
    print(f"aviso: overlay de contatos ausente ({CONTATOS})")

finais = Counter(re.sub(r"\D", "", p["telefone"])[-9:] for p in out if p["telefone"])
for p in out:
    if p["telefone"] and finais[re.sub(r"\D", "", p["telefone"])[-9:]] > 1:
        p["telefoneSuspeito"] = True

out.sort(key=lambda x: fold(x["nome"]))
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nPESSOAS: {len(out)}")
print(f"com telefone: {sum(1 for x in out if x['telefone'])} (AMPPE {stats['amppe']} / Correg {stats['correg']})")
print(f"com whatsapp: {sum(1 for x in out if x['whatsapp'])}")
print(f"com e-mail: {sum(1 for x in out if x['email'])}")
print(f"sem nada: {sum(1 for x in out if not x['telefone'] and not x['email'])}")
print("\nExemplos:")
for x in out[:3] + out[200:203]:
    print(json.dumps(x, ensure_ascii=False)[:400])
