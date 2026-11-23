/* Service worker — Membros MPPE
   Navegação: network-first (um deploy novo aparece na primeira abertura online).
   Assets: cache-first. Offline: serve o último index.html em cache + fotos precacheadas. */
const CACHE_NAME = 'membros-v9';
const BASE_ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-180.png',
  './icon-512.png'
];
// Fotos do acervo: lista gerada por build.py a partir do campo `foto` do dataset.
const FOTOS = [
  "./fotos/ana-clezia-ferreira-nunes.jpg",
  "./fotos/ana-joemia-marques-da-rocha.jpg",
  "./fotos/ana-maria-moura-maranhao-da-fonte.jpg",
  "./fotos/ana-rita-coelho-colaco-dias.jpg",
  "./fotos/andre-angelo-de-almeida.jpg",
  "./fotos/andre-jacinto-de-almeida-neto.jpg",
  "./fotos/andreia-aparecida-moura-de-couto.jpg",
  "./fotos/ariano-tercio-silva-de-aguiar.jpg",
  "./fotos/camila-mendes-de-santana-coutinho.jpg",
  "./fotos/carolina-gurgel-lima.jpg",
  "./fotos/crisley-patrick-tostes.jpg",
  "./fotos/daniel-jose-mesquita-monteiro-dias.jpg",
  "./fotos/diogenes-luciano-nogueira-moreira.jpg",
  "./fotos/eduardo-leal-dos-santos.jpg",
  "./fotos/eduardo-pimentel-de-vasconcelos-de-aquino.jpg",
  "./fotos/eryne-avila-dos-anjos-luna.jpg",
  "./fotos/fabio-de-sousa-castro.jpg",
  "./fotos/fabio-henrique-cavalcanti-estevam.jpg",
  "./fotos/fernando-henrique-ferreira-cunha-ramos.jpg",
  "./fotos/filipe-coutinho-lima-britto.jpg",
  "./fotos/gabriela-lima-lapenda-figueiroa.jpg",
  "./fotos/gabriela-tavares-almeida.jpg",
  "./fotos/guilherme-graciliano-araujo-lima.jpg",
  "./fotos/gustavo-henrique-holanda-dias-kershaw.jpg",
  "./fotos/iron-miranda-dos-anjos.jpg",
  "./fotos/joao-paulo-carvalho-dos-santos.jpg",
  "./fotos/larissa-de-almeida-moura-albuquerque.jpg",
  "./fotos/leandro-guedes-matos.jpg",
  "./fotos/maria-cecilia-soares-tertuliano.jpg",
  "./fotos/milena-de-oliveira-santos-do-carmo.jpg",
  "./fotos/patricia-ferreira-wanderley-de-siqueira-golding.jpg",
  "./fotos/rafael-moreira-steinberger.jpg",
  "./fotos/regina-wanderley-leite-de-almeida.jpg",
  "./fotos/renata-de-lima-landim.jpg",
  "./fotos/rodrigo-amorim-da-silva-santos.jpg",
  "./fotos/romulo-siqueira-franca.jpg",
  "./fotos/themes-jaciara-mergulhao-da-costa.jpg",
  "./fotos/tiago-sales-boulhosa-gonzalez.jpg",
  "./fotos/vinicius-costa-e-silva.jpg",
  "./fotos/vinicius-silva-de-araujo.jpg",
  "./fotos/wanessa-kelly-almeida-silva.jpg",
];
const ASSETS = BASE_ASSETS.concat(FOTOS);

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // wa.me e afins passam direto

  const isNavigation =
    req.mode === 'navigate' ||
    url.pathname.endsWith('/') ||
    url.pathname.endsWith('index.html');

  if (isNavigation) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put('./index.html', copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./index.html').then((c) => c || caches.match('./')))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        if (res && res.status === 200 && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy)).catch(() => {});
        }
        return res;
      });
    })
  );
});
