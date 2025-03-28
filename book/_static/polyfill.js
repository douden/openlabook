!(function (e, t) {
  'object' == typeof exports && 'undefined' != typeof module
    ? (module.exports = t())
    : 'function' == typeof define && define.amd
    ? define(t)
    : ((e || self).loadingAttributePolyfill = t())
})(this, function () {
  var e,
    t = 'loading' in HTMLImageElement.prototype,
    r = 'loading' in HTMLIFrameElement.prototype,
    o = 'onscroll' in window
  function a(e) {
    var t,
      r,
      o = []
    'picture' === e.parentNode.tagName.toLowerCase() &&
      ((r = (t = e.parentNode).querySelector('source[data-lazy-remove]')) &&
        t.removeChild(r),
      (o = Array.prototype.slice.call(
        e.parentNode.querySelectorAll('source')
      ))),
      o.push(e),
      o.forEach(function (e) {
        e.hasAttribute('data-lazy-srcset') &&
          (e.setAttribute('srcset', e.getAttribute('data-lazy-srcset')),
          e.removeAttribute('data-lazy-srcset'))
      }),
      e.setAttribute('src', e.getAttribute('data-lazy-src')),
      e.removeAttribute('data-lazy-src')
  }
  function n(a) {
    var n = document.createElement('div')
    for (
      n.innerHTML = (function (a) {
        var n = a.textContent || a.innerHTML,
          i =
            'data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 ' +
            ((n.match(/width=['"](\d+)['"]/) || !1)[1] || 1) +
            ' ' +
            ((n.match(/height=['"](\d+)['"]/) || !1)[1] || 1) +
            '%27%3E%3C/svg%3E'
        return (
          ((/<img/gim.test(n) && !t) || (/<iframe/gim.test(n) && !r)) &&
            o &&
            (n =
              void 0 === e
                ? n.replace(/(?:\r\n|\r|\n|\t| )src=/g, ' lazyload="1" src=')
                : (n = n.replace(
                    '<source',
                    '<source srcset="' +
                      i +
                      '" data-lazy-remove="true"></source>\n<source'
                  ))
                    .replace(
                      /(?:\r\n|\r|\n|\t| )srcset=/g,
                      ' data-lazy-srcset='
                    )
                    .replace(
                      /(?:\r\n|\r|\n|\t| )src=/g,
                      ' src="' + i + '" data-lazy-src='
                    )),
          n
        )
      })(a);
      n.firstChild;

    ) {
      var i = n.firstChild
      if (
        o &&
        void 0 !== e &&
        i.tagName &&
        ((('img' === i.tagName.toLowerCase() ||
          'picture' === i.tagName.toLowerCase()) &&
          !t) ||
          ('iframe' === i.tagName.toLowerCase() && !r))
      ) {
        var c =
          'picture' === i.tagName.toLowerCase() ? n.querySelector('img') : i
        e.observe(c)
      }
      a.parentNode.insertBefore(i, a)
    }
    a.parentNode.removeChild(a)
  }
  window.NodeList &&
    !NodeList.prototype.forEach &&
    (NodeList.prototype.forEach = Array.prototype.forEach),
    'IntersectionObserver' in window &&
      (e = new IntersectionObserver(
        function (e, t) {
          e.forEach(function (e) {
            if (0 !== e.intersectionRatio) {
              var r = e.target
              t.unobserve(r), a(r)
            }
          })
        },
        { rootMargin: '0px 0px 256px 0px', threshold: 0.01 }
      ))
  var i = function () {
    document.querySelectorAll('noscript.loading-lazy').forEach(function (e) {
      return n(e)
    }),
      void 0 !== window.matchMedia &&
        window.matchMedia('print').addListener(function (e) {
          e.matches &&
            document
              .querySelectorAll(
                'img[loading="lazy"][data-lazy-src],iframe[loading="lazy"][data-lazy-src]'
              )
              .forEach(function (e) {
                a(e)
              })
        })
  }
  return (
    /comp|inter/.test(document.readyState)
      ? i()
      : 'addEventListener' in document
      ? document.addEventListener('DOMContentLoaded', function () {
          i()
        })
      : document.attachEvent('onreadystatechange', function () {
          'complete' === document.readyState && i()
        }),
    { prepareElement: n }
  )
})
//# sourceMappingURL=loading-attribute-polyfill.umd.js.map
