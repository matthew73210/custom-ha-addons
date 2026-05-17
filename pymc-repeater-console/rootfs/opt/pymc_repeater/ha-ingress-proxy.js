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
      if (path === '/repeater' || path.indexOf('/repeater/') === 0) {
        return '/';
      }
      return path.slice(0, path.lastIndexOf('/') + 1) || '/';
    }
    if (path.indexOf('/repeater/') === 0) {
      return '/';
    }
    return path;
  }

  var basePath = computeBasePath();
  var directRoot = basePath === '/';
  var repeaterMode = /^\/repeater(\/|$)/.test(window.location.pathname || '');
  var repeaterBasePath = directRoot ? '/repeater/' : basePath + 'repeater/';

  function trimBase() {
    return basePath.replace(/\/$/, '');
  }

  function trimRepeaterBase() {
    return repeaterBasePath.replace(/\/$/, '');
  }

  function isManagedPath(path) {
    return /^\/(api|auth|ws|doc|assets|_next|static|images|img|favicon\.ico|login|setup|configuration|neighbors|statistics|system-stats|cad-calibration|sessions|room-servers|companions|logs|terminal|help)(\/|$|\?)/.test(
      path
    );
  }

  function isRepeaterAssetPath(path) {
    return /^\/(assets|favicon\.ico)(\/|$|\?)/.test(path);
  }

  function joinBase(path) {
    if (!path || directRoot) return path;
    if (path.indexOf(basePath) === 0) return path;
    if (path[0] === '/' && isManagedPath(path)) return trimBase() + path;
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
    if (repeaterMode && value[0] === '/' && isRepeaterAssetPath(value)) {
      return trimRepeaterBase() + value;
    }
    if (value[0] === '/') return joinBase(value);

    try {
      var url = new URL(value, window.location.href);
      if (url.origin === window.location.origin && isManagedPath(url.pathname)) {
        url.pathname = joinBase(url.pathname);
        return url.toString();
      }
    } catch (_) {}

    return value;
  }

  function rewriteWebSocketUrl(value) {
    var url = new URL(value, window.location.href);
    if (!directRoot && url.host === window.location.host) {
      url.pathname = joinBase(url.pathname || '/');
    }
    return url.toString();
  }

  function requestInitFromRequest(request, init) {
    var requestInit = {
      method: request.method,
      headers: request.headers,
      mode: request.mode,
      credentials: request.credentials,
      cache: request.cache,
      redirect: request.redirect,
      referrer: request.referrer,
      referrerPolicy: request.referrerPolicy,
      integrity: request.integrity,
      keepalive: request.keepalive,
      signal: request.signal
    };
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      try {
        requestInit.body = request.clone().body;
        requestInit.duplex = 'half';
      } catch (_) {}
    }
    if (init) {
      Object.keys(init).forEach(function (key) {
        if (init[key] !== undefined) requestInit[key] = init[key];
      });
    }
    return requestInit;
  }

  window.PyMCIngressBasePath = basePath;
  window.PyMCRepeaterBasePath = repeaterBasePath;
  window.PyMCIngressJoinPath = joinBase;
  window.PyMCIngressJoinAsset = joinAsset;

  var NativeRequest = window.Request;
  if (NativeRequest) {
    function PyMCIngressRequest(input, init) {
      if (typeof input === 'string') return new NativeRequest(rewriteUrl(input), init);
      if (input instanceof URL) return new NativeRequest(new URL(rewriteUrl(input.toString())), init);
      if (input instanceof NativeRequest) {
        var rewritten = rewriteUrl(input.url);
        if (rewritten !== input.url) {
          return new NativeRequest(rewritten, requestInitFromRequest(input, init));
        }
      }
      return new NativeRequest(input, init);
    }
    PyMCIngressRequest.prototype = NativeRequest.prototype;
    window.Request = PyMCIngressRequest;
  }

  var nativeFetch = window.fetch ? window.fetch.bind(window) : null;
  if (nativeFetch) {
    window.fetch = function (input, init) {
      if (typeof input === 'string') return nativeFetch(rewriteUrl(input), init);
      if (input instanceof URL) return nativeFetch(new URL(rewriteUrl(input.toString())), init);
      if (NativeRequest && input instanceof NativeRequest) {
        var rewritten = rewriteUrl(input.url);
        if (rewritten !== input.url) {
          return nativeFetch(new NativeRequest(rewritten, requestInitFromRequest(input, init)));
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
    function PyMCIngressWebSocket(url, protocols) {
      var rewritten = rewriteWebSocketUrl(url);
      if (protocols !== undefined) return new NativeWebSocket(rewritten, protocols);
      return new NativeWebSocket(rewritten);
    }
    PyMCIngressWebSocket.prototype = NativeWebSocket.prototype;
    PyMCIngressWebSocket.CONNECTING = NativeWebSocket.CONNECTING;
    PyMCIngressWebSocket.OPEN = NativeWebSocket.OPEN;
    PyMCIngressWebSocket.CLOSING = NativeWebSocket.CLOSING;
    PyMCIngressWebSocket.CLOSED = NativeWebSocket.CLOSED;
    window.WebSocket = PyMCIngressWebSocket;
  }

  function rewriteWorkerUrl(value) {
    if (typeof value === 'string') return rewriteUrl(value);
    if (value instanceof URL) return new URL(rewriteUrl(value.toString()));
    return value;
  }

  var NativeWorker = window.Worker;
  if (NativeWorker) {
    function PyMCIngressWorker(url, options) {
      return new NativeWorker(rewriteWorkerUrl(url), options);
    }
    PyMCIngressWorker.prototype = NativeWorker.prototype;
    window.Worker = PyMCIngressWorker;
  }

  var NativeSharedWorker = window.SharedWorker;
  if (NativeSharedWorker) {
    function PyMCIngressSharedWorker(url, options) {
      return new NativeSharedWorker(rewriteWorkerUrl(url), options);
    }
    PyMCIngressSharedWorker.prototype = NativeSharedWorker.prototype;
    window.SharedWorker = PyMCIngressSharedWorker;
  }

  function patchUrlProperty(proto, property) {
    var descriptor = Object.getOwnPropertyDescriptor(proto, property);
    if (!descriptor || !descriptor.set || !descriptor.get) return;
    Object.defineProperty(proto, property, {
      configurable: true,
      enumerable: descriptor.enumerable,
      get: descriptor.get,
      set: function (value) {
        return descriptor.set.call(this, rewriteUrl(String(value)));
      }
    });
  }

  if (window.HTMLImageElement) patchUrlProperty(HTMLImageElement.prototype, 'src');
  if (window.HTMLScriptElement) patchUrlProperty(HTMLScriptElement.prototype, 'src');
  if (window.HTMLLinkElement) patchUrlProperty(HTMLLinkElement.prototype, 'href');
  if (window.HTMLAnchorElement) patchUrlProperty(HTMLAnchorElement.prototype, 'href');
  if (window.HTMLFormElement) patchUrlProperty(HTMLFormElement.prototype, 'action');
  if (window.HTMLSourceElement) patchUrlProperty(HTMLSourceElement.prototype, 'src');

  var nativeSetAttribute = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (name, value) {
    if (/^(href|src|action|poster)$/i.test(name)) value = rewriteUrl(String(value));
    return nativeSetAttribute.call(this, name, value);
  };
})();
