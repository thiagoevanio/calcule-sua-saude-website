/* article.js — melhorias de leitura: barra de progresso, scrollspy do índice
   e botão "voltar ao topo". Sem dependências. Idempotente. */
(function () {
  function init() {
    var article = document.querySelector('.article-body');
    if (!article) return;

    /* ---- Barra de progresso de leitura ---- */
    var bar = document.getElementById('read-progress');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'read-progress';
      document.body.appendChild(bar);
    }

    /* ---- Botão voltar ao topo ---- */
    var toTop = document.getElementById('to-top');
    if (!toTop) {
      toTop = document.createElement('button');
      toTop.id = 'to-top';
      toTop.setAttribute('aria-label', 'Voltar ao topo');
      toTop.innerHTML = '↑';
      document.body.appendChild(toTop);
      toTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    function onScroll() {
      var rect = article.getBoundingClientRect();
      var total = article.offsetHeight - window.innerHeight;
      var scrolled = Math.min(Math.max(-rect.top, 0), total > 0 ? total : 1);
      var pct = total > 0 ? (scrolled / total) * 100 : 0;
      bar.style.width = pct + '%';
      toTop.classList.toggle('show', window.scrollY > 600);
    }

    /* ---- Scrollspy do índice ---- */
    var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.toc-list a[href^="#"]'));
    var sections = tocLinks
      .map(function (a) {
        var el = document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));
        return el ? { link: a, el: el } : null;
      })
      .filter(Boolean);

    function spy() {
      var pos = window.scrollY + 140;
      var current = null;
      for (var i = 0; i < sections.length; i++) {
        if (sections[i].el.offsetTop <= pos) current = sections[i];
      }
      tocLinks.forEach(function (a) { a.classList.remove('active'); });
      if (current) current.link.classList.add('active');
    }

    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          onScroll();
          if (sections.length) spy();
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    onScroll();
    if (sections.length) spy();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
