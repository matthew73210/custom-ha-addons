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
    return /^\/(api|auth|ws|doc|assets|_next|static|images|img|favicon\.ico|login|setup)(\/|$|\?)/.test(path);
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

  function rewriteAttributeValue(value) {
    if (typeof value !== 'string' || !value || directRoot) return value;
    if (value.indexOf(basePath) === 0) return value;
    if (value[0] === '/' && isManagedPath(value)) return trimBase() + value;
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
      url.pathname = joinBase(url.pathname);
    }
    return url.toString();
  }

  window.PyMCHABasePath = basePath;
  window.PyMCHAJoinPath = joinBase;
  window.PyMCHAJoinAsset = joinAsset;

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

  var NativeRequest = window.Request;
  if (NativeRequest) {
    function PyMCRequest(input, init) {
      if (typeof input === 'string') {
        return new NativeRequest(rewriteUrl(input), init);
      }
      if (input instanceof URL) {
        return new NativeRequest(new URL(rewriteUrl(input.toString())), init);
      }
      if (input instanceof NativeRequest) {
        var rewritten = rewriteUrl(input.url);
        if (rewritten !== input.url) {
          return new NativeRequest(rewritten, requestInitFromRequest(input, init));
        }
      }
      return new NativeRequest(input, init);
    }
    PyMCRequest.prototype = NativeRequest.prototype;
    window.Request = PyMCRequest;
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

  function rewriteElement(element) {
    if (!element || !element.getAttribute) return;
    ['href', 'src', 'action', 'poster'].forEach(function (name) {
      var value = element.getAttribute(name);
      var rewritten = rewriteAttributeValue(value);
      if (rewritten !== value) {
        element.setAttribute(name, rewritten);
      }
    });
    if (element.srcset) {
      var rewrittenSrcset = element.srcset
        .split(',')
        .map(function (part) {
          var pieces = part.trim().split(/\s+/);
          if (pieces[0]) pieces[0] = rewriteAttributeValue(pieces[0]);
          return pieces.join(' ');
        })
        .join(', ');
      if (rewrittenSrcset !== element.srcset) element.srcset = rewrittenSrcset;
    }
  }

  var nativeSetAttribute = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function (name, value) {
    if (/^(href|src|action|poster)$/i.test(name)) {
      value = rewriteAttributeValue(String(value));
    }
    return nativeSetAttribute.call(this, name, value);
  };

  function rewriteExistingElements(root) {
    if (!root || !root.querySelectorAll) return;
    root.querySelectorAll('[href], [src], [action], [poster], [srcset]').forEach(rewriteElement);
  }

  document.addEventListener(
    'submit',
    function (event) {
      rewriteElement(event.target);
    },
    true
  );

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      rewriteExistingElements(document);
    });
  } else {
    rewriteExistingElements(document);
  }

  if (window.MutationObserver) {
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.type === 'attributes') {
          rewriteElement(mutation.target);
        }
        mutation.addedNodes &&
          mutation.addedNodes.forEach(function (node) {
            if (node.nodeType === 1) {
              rewriteElement(node);
              rewriteExistingElements(node);
            }
          });
      });
    }).observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['href', 'src', 'action', 'poster', 'srcset']
    });
  }
})();
