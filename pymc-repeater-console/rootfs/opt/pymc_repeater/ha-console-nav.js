(function () {
  'use strict';

  function computeIngressBase() {
    if (window.PyMCIngressBasePath) return window.PyMCIngressBasePath;

    var path = window.location.pathname || '/';
    var marker = '/api/hassio_ingress/';
    var markerIndex = path.indexOf(marker);
    if (markerIndex !== -1) {
      var afterMarker = path.slice(markerIndex + marker.length);
      var token = afterMarker.split('/')[0];
      if (token) return path.slice(0, markerIndex) + marker + token + '/';
    }
    return '/';
  }

  function join(base, path) {
    return base.replace(/\/$/, '') + path;
  }

  function addNav() {
    if (document.getElementById('pymc-console-nav')) return;

    var base = computeIngressBase();
    var inRepeater = /^\/(?:api\/hassio_ingress\/[^/]+\/)?repeater(\/|$)/.test(
      window.location.pathname || '/'
    );
    var target = inRepeater ? base : join(base, '/repeater/');
    var label = inRepeater ? 'Console' : 'Repeater UI';
    var current = inRepeater ? 'pyMC Repeater' : 'pyMC Console';

    var style = document.createElement('style');
    style.textContent =
      '#pymc-console-nav{position:fixed;right:16px;bottom:16px;z-index:2147483647;' +
      'display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;' +
      'background:rgba(15,23,42,.92);color:#fff;font:13px/1.2 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;' +
      'box-shadow:0 12px 30px rgba(0,0,0,.28);backdrop-filter:blur(10px)}' +
      '#pymc-console-nav span{opacity:.72;white-space:nowrap}' +
      '#pymc-console-nav a{color:#fff;text-decoration:none;font-weight:650;border:1px solid rgba(255,255,255,.32);' +
      'border-radius:6px;padding:7px 9px;background:rgba(255,255,255,.10)}' +
      '#pymc-console-nav a:hover{background:rgba(255,255,255,.18)}' +
      '@media(max-width:520px){#pymc-console-nav{left:12px;right:12px;bottom:12px;justify-content:space-between}}';

    var nav = document.createElement('div');
    nav.id = 'pymc-console-nav';

    var badge = document.createElement('span');
    badge.textContent = current;

    var link = document.createElement('a');
    link.href = target;
    link.textContent = label;

    nav.appendChild(badge);
    nav.appendChild(link);
    document.head.appendChild(style);
    document.body.appendChild(nav);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addNav);
  } else {
    addNav();
  }
})();
