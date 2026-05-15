(function () {
  'use strict';

  function computeBasePath() {
    var path = window.location.pathname || '/';
    if (!path.endsWith('/')) {
      path = path.slice(0, path.lastIndexOf('/') + 1) || '/';
    }
    return path;
  }

  var basePath = computeBasePath();
  var directRoot = basePath === '/';

  function joinBase(path) {
    if (directRoot || !path || path[0] !== '/') return path;
    if (path.indexOf(basePath) === 0) return path;
    if (/^\/(api|ws|assets|vendor)(\/|$)/.test(path)) {
      return basePath.replace(/\/$/, '') + path;
    }
    return path;
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

  var NativeWebSocket = window.WebSocket;
  if (NativeWebSocket) {
    function rewriteWebSocketUrl(value) {
      var url = new URL(value, window.location.href);
      if (!directRoot && url.host === window.location.host) {
        if (url.pathname === '/' || url.pathname === '' || url.pathname === '/ws') {
          url.pathname = basePath;
        } else if (/^\/ws(\/|$)/.test(url.pathname)) {
          url.pathname = basePath.replace(/\/$/, '') + url.pathname;
        }
      }
      return url.toString();
    }

    function CoreScopeWebSocket(url, protocols) {
      var rewritten = rewriteWebSocketUrl(url);
      if (protocols !== undefined) return new NativeWebSocket(rewritten, protocols);
      return new NativeWebSocket(rewritten);
    }
    CoreScopeWebSocket.prototype = NativeWebSocket.prototype;
    CoreScopeWebSocket.CONNECTING = NativeWebSocket.CONNECTING;
    CoreScopeWebSocket.OPEN = NativeWebSocket.OPEN;
    CoreScopeWebSocket.CLOSING = NativeWebSocket.CLOSING;
    CoreScopeWebSocket.CLOSED = NativeWebSocket.CLOSED;
    window.WebSocket = CoreScopeWebSocket;
  }

  window.CoreScopeIngress = {
    basePath: basePath,
    apiBasePath: joinBase('/api/'),
    websocketPath: directRoot ? '/' : basePath
  };
})();
