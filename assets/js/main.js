/* Theme toggle, email links, language links that keep the section, print expansion, active nav. */
(function () {
  var root = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  /* Theme: an explicit choice is stored; otherwise the system setting wins. */
  var btn = document.querySelector(".theme");
  function current() {
    var t = root.getAttribute("data-theme");
    if (t === "light" || t === "dark") return t;
    return mq && mq.matches ? "dark" : "light";
  }
  function syncLabel() {
    if (!btn) return;
    var label = current() === "dark" ? btn.getAttribute("data-to-light") : btn.getAttribute("data-to-dark");
    btn.setAttribute("aria-label", label);
    btn.setAttribute("title", label);
  }
  if (btn) {
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      syncLabel();
    });
    syncLabel();
    if (mq && mq.addEventListener) mq.addEventListener("change", syncLabel);
  }

  /* Email: the address is only assembled in the browser, so plain-text scrapers miss it. */
  Array.prototype.forEach.call(document.querySelectorAll(".js-email"), function (a) {
    var addr = a.getAttribute("data-u") + "@" + a.getAttribute("data-d");
    a.setAttribute("href", "mailto:" + addr);
    if (a.hasAttribute("data-show")) a.textContent = addr;
  });

  /* Language links keep the section you are reading. */
  Array.prototype.forEach.call(document.querySelectorAll(".langs a"), function (a) {
    a.addEventListener("click", function () {
      if (location.hash) a.setAttribute("href", a.getAttribute("href").split("#")[0] + location.hash);
    });
  });

  /* Printing shows every bullet. */
  var opened = [];
  window.addEventListener("beforeprint", function () {
    Array.prototype.forEach.call(document.querySelectorAll("details:not([open])"), function (d) {
      d.open = true;
      opened.push(d);
    });
  });
  window.addEventListener("afterprint", function () {
    opened.forEach(function (d) { d.open = false; });
    opened = [];
  });

  /* Highlight the nav link for the section in view. */
  var links = {};
  Array.prototype.forEach.call(document.querySelectorAll(".nav a"), function (a) {
    links[a.getAttribute("href").slice(1)] = a;
  });
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = links[en.target.id];
        if (!a) return;
        if (en.isIntersecting) {
          Object.keys(links).forEach(function (k) { links[k].classList.remove("on"); });
          a.classList.add("on");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    Object.keys(links).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });
  }
})();
