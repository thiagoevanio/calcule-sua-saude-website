/* nav.js — controla o menu hambúrguer mobile (off-canvas).
   Sem dependências. Idempotente. Compartilhado por todas as páginas. */
(function () {
  function init() {
    var toggle = document.querySelector('.nav-toggle');
    var header = document.querySelector('.main-header');
    if (!toggle || !header) return;
    var menu = header.querySelector('.nav-menu');
    if (!menu) return;

    // Backdrop único
    var backdrop = document.querySelector('.nav-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'nav-backdrop';
      document.body.appendChild(backdrop);
    }

    function open() {
      menu.classList.add('open');
      backdrop.classList.add('show');
      document.body.classList.add('nav-open');
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Fechar menu');
    }
    function close() {
      menu.classList.remove('open');
      backdrop.classList.remove('show');
      document.body.classList.remove('nav-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Abrir menu');
    }
    function isOpen() { return menu.classList.contains('open'); }

    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      isOpen() ? close() : open();
    });

    backdrop.addEventListener('click', close);

    // Fecha ao clicar num link (mas não no botão do dropdown "Ferramentas")
    menu.addEventListener('click', function (e) {
      var link = e.target.closest('a');
      if (link) close();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && isOpen()) { close(); toggle.focus(); }
    });

    // Reseta o estado ao voltar para desktop
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900 && isOpen()) close();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
