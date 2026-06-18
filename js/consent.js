/* Shared consent state for Google tags and the site-wide privacy banner. */
(function () {
  var consentKey = 'siteConsent';
  var legacyKey = 'cookiesAccepted';

  function readStorage(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function writeStorage(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      // Consent remains valid for the current page if storage is blocked.
    }
  }

  var savedConsent = window.__siteConsentSaved || readStorage(consentKey);
  if (!savedConsent && readStorage(legacyKey) === 'true') savedConsent = 'granted';
  var granted = savedConsent === 'granted';

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () {
    window.dataLayer.push(arguments);
  };

  if (!window.__siteConsentDefaultSet) {
    window.gtag('consent', 'default', {
      ad_storage: granted ? 'granted' : 'denied',
      analytics_storage: granted ? 'granted' : 'denied',
      ad_user_data: granted ? 'granted' : 'denied',
      ad_personalization: granted ? 'granted' : 'denied',
      wait_for_update: 500
    });
    window.gtag('set', 'ads_data_redaction', true);
  }

  function loadGoogleServices() {
    if (!document.querySelector('script[data-google-analytics]')) {
      var analytics = document.createElement('script');
      analytics.async = true;
      analytics.dataset.googleAnalytics = 'true';
      analytics.src = 'https://www.googletagmanager.com/gtag/js?id=G-EVCQQZV60N';
      document.head.appendChild(analytics);
    }

    if (!document.querySelector('script[data-google-adsense]')) {
      var adsense = document.createElement('script');
      adsense.async = true;
      adsense.crossOrigin = 'anonymous';
      adsense.dataset.googleAdsense = 'true';
      adsense.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5825554897787593';
      document.head.appendChild(adsense);
    }
  }

  if (granted) loadGoogleServices();

  function updateConsent(next) {
    var status = next === 'granted' ? 'granted' : 'denied';
    writeStorage(consentKey, status);
    writeStorage(legacyKey, status === 'granted' ? 'true' : 'false');
    window.gtag('consent', 'update', {
      ad_storage: status,
      analytics_storage: status,
      ad_user_data: status,
      ad_personalization: status
    });
  }

  function labels() {
    var lang = (document.documentElement.lang || 'pt').toLowerCase();
    if (lang.startsWith('en')) {
      return {
        title: 'Your privacy matters',
        text: 'We use cookies for audience measurement and advertising. Choose whether to allow optional cookies.',
        accept: 'Accept optional cookies',
        reject: 'Continue without cookies',
        policy: 'Privacy Policy',
        policyHref: 'politica-de-privacidade-en.html'
      };
    }
    if (lang.startsWith('es')) {
      return {
        title: 'Tu privacidad importa',
        text: 'Usamos cookies para medir la audiencia y mostrar anuncios. Elige si deseas permitir cookies opcionales.',
        accept: 'Aceptar cookies opcionales',
        reject: 'Continuar sin cookies',
        policy: 'Política de Privacidad',
        policyHref: 'politica-de-privacidade-es.html'
      };
    }
    return {
      title: 'Sua privacidade importa',
      text: 'Usamos cookies para medir a audiência e exibir anúncios. Escolha se deseja permitir cookies opcionais.',
      accept: 'Aceitar cookies opcionais',
      reject: 'Continuar sem cookies',
      policy: 'Política de Privacidade',
      policyHref: 'politica-de-privacidade.html'
    };
  }

  function rootUrl(relativePath) {
    var script = document.currentScript;
    if (!script || !script.src) return relativePath;
    return new URL('../' + relativePath, script.src).href;
  }

  var privacyLabels = labels();
  var privacyUrl = rootUrl(privacyLabels.policyHref);

  function createBanner() {
    var banner = document.getElementById('cookie-banner');
    if (banner) return banner;

    banner = document.createElement('div');
    banner.id = 'cookie-banner';
    banner.className = 'cookie-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-modal', 'true');
    banner.setAttribute('aria-labelledby', 'cookie-title');
    banner.innerHTML =
      '<div class="cookie-content">' +
        '<div id="cookie-title" class="cookie-title">' + privacyLabels.title + '</div>' +
        '<p class="cookie-text">' + privacyLabels.text + ' <a href="' + privacyUrl + '">' + privacyLabels.policy + '</a>.</p>' +
      '</div>' +
      '<div class="cookie-actions">' +
        '<button type="button" id="btn-cookie-close" class="btn-cookie-close">' + privacyLabels.reject + '</button>' +
        '<button type="button" id="btn-cookie-accept" class="btn-cookie-accept">' + privacyLabels.accept + '</button>' +
      '</div>';
    document.body.appendChild(banner);
    return banner;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var banner = createBanner();
    var acceptButton = document.getElementById('btn-cookie-accept');
    var rejectButton = document.getElementById('btn-cookie-close');

    if (rejectButton) rejectButton.textContent = privacyLabels.reject;
    if (acceptButton) acceptButton.textContent = privacyLabels.accept;

    if (!savedConsent) {
      window.setTimeout(function () {
        banner.classList.add('show');
      }, 500);
    }

    if (acceptButton) {
      acceptButton.addEventListener('click', function () {
        updateConsent('granted');
        loadGoogleServices();
        banner.classList.remove('show');
      });
    }

    if (rejectButton) {
      rejectButton.addEventListener('click', function () {
        updateConsent('denied');
        banner.classList.remove('show');
      });
    }
  });
})();
