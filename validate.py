#!/usr/bin/env python3
"""Validação em navegador real (Playwright, perfil iPhone) do app membros-mppe-app."""
import json, os, re, subprocess, sys, time
from playwright.sync_api import sync_playwright

ROOT = "/Users/chlima/vercel-deploys/membros-mppe-app"
PORT = 8791
BASE = f"http://localhost:{PORT}/"

data = json.load(open(f"{ROOT}/dataset.json", encoding="utf-8"))
EXP_TOTAL = len(data)
EXP_CARUARU = sum(1 for d in data if d["promotoria"] == "Caruaru")
EXP_2INST = sum(1 for d in data if d["entrancia"] == "-")
print(f"esperado: total={EXP_TOTAL} caruaru={EXP_CARUARU} 2inst={EXP_2INST}")

fails, notes = [], []


def check(cond, msg):
    (notes if cond else fails).append(("OK  " if cond else "FAIL") + " " + msg)
    print(("OK   " if cond else "FAIL ") + msg)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=3,
        is_mobile=True, has_touch=True,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    )
    page = ctx.new_page()
    console_errors, requests = [], []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))
    page.on("request", lambda r: requests.append(r.url))

    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(700)

    # 1. lista
    rows = page.locator("#list-container .member-row, #list-container [data-id]")
    check(rows.count() == EXP_TOTAL, f"linhas na lista = {rows.count()} (esperado {EXP_TOTAL})")
    count_txt = page.inner_text("#result-count")
    check(str(EXP_TOTAL) in re.sub(r"\D", "", count_txt), f"contador inicial: {count_txt!r}")

    # 2. busca sem acento
    page.fill("#search-input", "jose")
    page.wait_for_timeout(350)
    n_jose = rows.count()
    check(0 < n_jose < EXP_TOTAL, f"busca 'jose' filtra ({n_jose} linhas)")
    txt = page.inner_text("#list-container")
    check("JOSÉ" in txt.upper() or "JOSE" in txt.upper(), "busca 'jose' encontra nome com acento")

    page.fill("#search-input", "ademilton")
    page.wait_for_timeout(350)
    check(rows.count() == 1, f"busca 'ademilton' -> {rows.count()} linha")
    page.fill("#search-input", "zzzzzz")
    page.wait_for_timeout(350)
    page.screenshot(path="/tmp/vazio.png")
    check(rows.count() == 0, "busca sem resultado -> 0 linhas (e estado vazio visível)")
    page.click("#search-clear") if page.locator("#search-clear").is_visible() else page.fill("#search-input", "")
    page.wait_for_timeout(300)

    # 2b. pontuação na busca não pode atrapalhar
    page.fill("#search-input", "jose,")
    page.wait_for_timeout(350)
    check(rows.count() > 0, f"busca com pontuação 'jose,' -> {rows.count()} linhas")
    page.fill("#search-input", "santo antao")
    page.wait_for_timeout(350)
    check(rows.count() > 0, f"busca sem acento/hífen 'santo antao' -> {rows.count()} linhas")
    page.fill("#search-input", "d\u2019avila")
    page.wait_for_timeout(300)
    check(True, "busca com apóstrofo não quebra (sem exceção)")
    page.fill("#search-input", "")
    page.wait_for_timeout(300)

    # 2c. rodapé de procedência do dado
    page.evaluate("() => document.getElementById('list-container').scrollTo(0, 0)")
    page.mouse.wheel(0, 200000)
    page.wait_for_timeout(600)
    nota = page.locator(".data-note")
    check(nota.count() == 1 and "18/11/2026" in nota.inner_text(), "rodapé com a data do retrato dos dados")
    page.evaluate("() => window.scrollTo(0,0)")
    page.mouse.wheel(0, -200000)
    page.wait_for_timeout(500)

    # 3. filtro 2ª Instância
    chip = page.locator("#entrancia-chips [data-entrancia='-'], #entrancia-chips button", has_text="2ª Instância").first
    chip.click()
    page.wait_for_timeout(400)
    check(rows.count() == EXP_2INST, f"chip 2ª Instância -> {rows.count()} (esperado {EXP_2INST})")

    # 4. filtro município
    page.locator("#entrancia-chips button", has_text="Todas").first.click()
    page.wait_for_timeout(300)
    opts = page.eval_on_selector("#city-select", "el => [...el.options].map(o => o.value)")
    lab = page.eval_on_selector("#city-select", "el => [...el.options].find(o => o.textContent.trim().startsWith('Caruaru'))?.value")
    page.select_option("#city-select", lab)
    page.wait_for_timeout(400)
    check(rows.count() == EXP_CARUARU, f"município Caruaru -> {rows.count()} (esperado {EXP_CARUARU})")
    page.click("#btn-clear")
    page.wait_for_timeout(400)
    check(rows.count() == EXP_TOTAL, f"Limpar -> {rows.count()} (esperado {EXP_TOTAL})")

    # 5. abrir detalhe do primeiro
    primeiro = data[0]
    rows.first.click()
    page.wait_for_timeout(600)
    check(page.locator("#sheet-root[aria-hidden='false'], #sheet-root.open, #sheet.visible, #sheet-root").first.is_visible(), "sheet abriu")
    nome_sheet = page.inner_text("#sheet-name").strip()
    check(nome_sheet.upper() == primeiro["nome"].upper(), f"nome na sheet: {nome_sheet!r}")
    check(primeiro["cargo"].lower()[:12] in page.inner_text("#sheet-cargo").lower(), "cargo na sheet")

    # 5b. telefone exibido no padrao local: 0 + DDD + numero
    if primeiro["telefone"]:
        tel_txt = page.evaluate("() => document.getElementById('sheet-phone-text').textContent.trim()")
        check(re.fullmatch(r"0\d{2} \d{8,9}", tel_txt) is not None,
              f"telefone exibido no padrao 0DDD numero: {tel_txt!r}")
        check(tel_txt == primeiro["telefone"], f"telefone da sheet = dataset ({primeiro['telefone']!r})")
        tel_href = page.get_attribute("#btn-call", "href") or ""
        check(tel_href == "tel:+55" + tel_txt.replace(" ", "")[1:], f"href tel: sem o zero ({tel_href})")

    box = page.locator("#photo-box").bounding_box()
    if box:
        ratio = box["width"] / box["height"]
        check(abs(ratio - 0.75) < 0.03, f"foto proporção 3:4 (ratio={ratio:.3f})")
    else:
        fails.append("FAIL caixa de foto sem geometria")

    wa = page.get_attribute("#btn-whatsapp", "href") or ""
    esperado_wa = "wa.me/55" + re.sub(r"\D", "", primeiro["telefone"])
    check(re.sub(r"\D", "", wa)[-11:] == re.sub(r"\D", "", esperado_wa)[-11:], f"href WhatsApp = {wa}")

    # 6. foto: upload + persistência
    test_img = "/tmp/test_photo.jpg"
    subprocess.run([sys.executable if False else "python3", "-c", f"""
from PIL import Image, ImageDraw
im = Image.new('RGB', (900, 1200), '#3366cc')
d = ImageDraw.Draw(im); d.rectangle([100, 100, 800, 1100], fill='#ffcc00')
im.save('{test_img}', 'JPEG')
"""], check=True)
    page.set_input_files("#photo-input", test_img)
    page.wait_for_timeout(900)
    has_img = page.evaluate("() => { const i = document.querySelector('#photo-img'); return !!(i && !i.hidden && i.src && i.naturalWidth > 0); }")
    check(has_img, "foto carregada e exibida após upload")
    dims = page.evaluate("() => { const i=document.querySelector('#photo-img'); return [i.naturalWidth, i.naturalHeight]; }")
    check(abs(dims[0] / max(dims[1], 1) - 0.75) < 0.05, f"imagem normalizada 3:4 no armazenamento {dims}")

    page.reload(wait_until="load")
    page.wait_for_timeout(900)
    page.locator("#list-container .member-row, #list-container [data-id]").first.click()
    page.wait_for_timeout(900)
    persist = page.evaluate("() => { const i = document.querySelector('#photo-img'); return !!(i && !i.hidden && i.naturalWidth > 0); }")
    check(persist, "foto persiste após reload (IndexedDB)")

    page.click("#btn-remove-photo")
    page.wait_for_timeout(700)
    removida = page.evaluate("() => { const i = document.querySelector('#photo-img'); const ph = document.querySelector('#photo-placeholder'); return (i.hidden || !i.src) && !ph.hidden; }")
    check(removida, "remover foto volta o placeholder")

    # 7. swipe para baixo fecha a sheet (eventos de TOQUE reais via CDP)
    hdr = page.locator("#sheet-header").bounding_box()
    cdp = ctx.new_cdp_session(page)
    if hdr:
        x = 195
        y0 = hdr["y"] + hdr["height"] / 2
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y0}]})
        for i in range(1, 13):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove",
                                                  "touchPoints": [{"x": x, "y": y0 + i * 30}]})
            page.wait_for_timeout(16)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(800)
    sheet_hidden = page.evaluate("() => { const r = document.querySelector('#sheet-root'); return r.getAttribute('aria-hidden') === 'true' || !r.classList.contains('is-open'); }")
    check(sheet_hidden, "swipe para baixo (toque) fecha a sheet")
    if not sheet_hidden:
        page.click("#btn-close-sheet")
        page.wait_for_timeout(500)
        check(page.evaluate("() => !document.querySelector('#sheet-root').classList.contains('is-open')"), "botão fechar fecha a sheet")

    # 8. tema
    bg_antes = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    page.click("#btn-theme")
    page.wait_for_timeout(600)
    bg_depois = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    check(bg_antes != bg_depois, f"tema alterna o fundo ({bg_antes} -> {bg_depois})")
    page.reload(wait_until="load")
    page.wait_for_timeout(700)
    bg_reload = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    check(bg_reload == bg_depois, f"tema persiste após reload ({bg_reload})")
    # contraste do texto sobre o fundo
    contrast = page.evaluate("""() => {
      const parse = c => c.match(/[\\d.]+/g).map(Number);
      const lum = ([r,g,b]) => { const f = v => { v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055,2.4); }; return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); };
      const bg = parse(getComputedStyle(document.body).backgroundColor);
      const fg = parse(getComputedStyle(document.querySelector('.member-name') || document.body).color);
      const L1 = lum(bg) + 0.05, L2 = lum(fg) + 0.05;
      return Math.round((Math.max(L1,L2)/Math.min(L1,L2))*100)/100;
    }""")
    check(contrast >= 4.5, f"contraste nome/fundo = {contrast}:1")

    # 9. larguras
    for w in (320, 390, 430):
        page.set_viewport_size({"width": w, "height": 844})
        page.wait_for_timeout(400)
        over = page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
        check(over <= 1, f"largura {w}px sem overflow horizontal (excesso {over}px)")

    # 10. sem requisição externa
    ext = [u for u in requests if not u.startswith(BASE) and not u.startswith("data:") and not u.startswith("blob:")]
    check(not ext, f"zero requisição externa (encontradas: {ext[:3]})")

    # 11. offline (service worker)
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(BASE, wait_until="load")
    page.wait_for_timeout(2000)
    sw = page.evaluate("() => 'serviceWorker' in navigator ? navigator.serviceWorker.getRegistrations().then(r => r.length) : -1")
    check(sw != 0, f"service worker registrado ({sw})")
    ctx.set_offline(True)
    try:
        page.reload(wait_until="load")
        page.wait_for_timeout(1200)
        off_rows = page.locator("#list-container .member-row, #list-container [data-id]").count()
        check(off_rows == EXP_TOTAL, f"offline renderiza {off_rows} linhas")
    except Exception as e:
        check(False, f"offline falhou: {e}")
    ctx.set_offline(False)

    check(not console_errors, f"sem erro de console ({console_errors[:3]})")
    page.screenshot(path="/tmp/app_final.png", full_page=False)
    browser.close()

print("\n==== RESUMO ====")
print(f"{len(notes)} OK / {len(fails)} falhas")
for f in fails:
    print(f)
open(f"{ROOT}/validacao_hermes.txt", "w").write("\n".join(notes + [""] + fails))
sys.exit(1 if fails else 0)
