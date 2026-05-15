(function () {
  'use strict';

  function computeBasePath() {
    var path = window.location.pathname || '/';
    var marker = '/api/hassio_ingress/';
    var markerIndex = path.indexOf(marker);

    if (markerIndex !== -1) {
      var afterMarker = path.slice(markerIndex + marker.length);
      var token = afterMarker.split('/')[0];
      if (token) {
        return path.slice(0, markerIndex) + marker + token + '/';
      }
    }

    if (!path.endsWith('/')) {
      path = path.slice(0, path.lastIndexOf('/') + 1) || '/';
    }
    return path;
  }

  var basePath = computeBasePath();
  var directRoot = basePath === '/';

  function trimBase() {
    return basePath.replace(/\/$/, '');
  }

  function isManagedPath(path) {
    return /^\/(api|auth|ws|doc|assets|favicon\.ico)(\/|$|\?)/.test(path);
  }

  function joinBase(path) {
    if (!path || directRoot) return path;
    if (path.indexOf(basePath) === 0) return path;
    if (path[0] === '/' && isManagedPath(path)) {
      return trimBase() + path;
    }
    return path;
  }

  function joinAsset(path) {
    if (!path || directRoot) return path;
    if (path[0] === '/') return joinBase(path);
    if (path.indexOf(basePath) === 0) return path;
    return basePath + path.replace(/^\/+/, '');
  }

  function rewriteUrl(value) {
    if (typeof value !== 'string') return value;
    if (value[0] === '/') return joinBase(value);

    try {
      var url = new URL(value, window.location.href);
      if (url.origin === window.location.origin) {
        url.pathname = joinBase(url.pathname);
        return url.toString();
      }
    } catch (_) {}

    return value;
  }

  function rewriteWebSocketUrl(value) {
    var url = new URL(value, window.location.href);
    if (!directRoot && url.host === window.location.host) {
      url.pathname = joinBase(url.pathname);
    }
    return url.toString();
  }

  window.PyMCHABasePath = basePath;
  window.PyMCHAJoinPath = joinBase;
  window.PyMCHAJoinAsset = joinAsset;

  var nativeFetch = window.fetch ? window.fetch.bind(window) : null;
  if (nativeFetch) {
    window.fetch = function (input, init) {
      if (typeof input === 'string') {
        return nativeFetch(rewriteUrl(input), init);
      }
      if (input instanceof URL) {
        return nativeFetch(new URL(rewriteUrl(input.toString())), init);
      }
      if (input instanceof Request) {
        var rewritten = rewriteUrl(input.url);
        if (rewritten !== input.url) {
          return nativeFetch(new Request(rewritten, input), init);
        }
      }
      return nativeFetch(input, init);
    };
  }

  var NativeXMLHttpRequest = window.XMLHttpRequest;
  if (NativeXMLHttpRequest) {
    var nativeOpen = NativeXMLHttpRequest.prototype.open;
    NativeXMLHttpRequest.prototype.open = function (method, url) {
      arguments[1] = rewriteUrl(url);
      return nativeOpen.apply(this, arguments);
    };
  }

  var NativeEventSource = window.EventSource;
  if (NativeEventSource) {
    window.EventSource = function (url, config) {
      return new NativeEventSource(rewriteUrl(url), config);
    };
    window.EventSource.prototype = NativeEventSource.prototype;
  }

  var NativeWebSocket = window.WebSocket;
  if (NativeWebSocket) {
    function PyMCWebSocket(url, protocols) {
      var rewritten = rewriteWebSocketUrl(url);
      if (protocols !== undefined) return new NativeWebSocket(rewritten, protocols);
      return new NativeWebSocket(rewritten);
    }
    PyMCWebSocket.prototype = NativeWebSocket.prototype;
    PyMCWebSocket.CONNECTING = NativeWebSocket.CONNECTING;
    PyMCWebSocket.OPEN = NativeWebSocket.OPEN;
    PyMCWebSocket.CLOSING = NativeWebSocket.CLOSING;
    PyMCWebSocket.CLOSED = NativeWebSocket.CLOSED;
    window.WebSocket = PyMCWebSocket;
  }

  document.addEventListener(
    'click',
    function (event) {
      var anchor = event.target && event.target.closest ? event.target.closest('a[href]') : null;
      if (!anchor) return;

      var href = anchor.getAttribute('href');
      if (!href || href[0] !== '/' || !isManagedPath(href)) return;

      anchor.setAttribute('href', joinBase(href));
    },
    true
  );
})();
