// Image zoom overlay for content images: click to open, wheel zoom at cursor,
// drag to pan, double click or "Đặt lại" to reset, Esc / "Đóng" / click outside to close.
// Same behaviour as tools/visual_guide (build_html.py).
(function () {
  "use strict";
  // Sphinx loads this in <head>, so the overlay can only be built once <body> exists.
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  function init() {
  var ov = document.createElement("div");
  ov.id = "img-zoom";
  ov.setAttribute("role", "dialog");
  ov.setAttribute("aria-modal", "true");
  ov.innerHTML =
    '<div class="zbar"><button type="button" class="zreset">Đặt lại</button>' +
    '<button type="button" class="zclose">Đóng (Esc)</button></div>' +
    '<img alt="">' +
    '<div class="zhint">Cuộn chuột để phóng to, kéo để di chuyển, nhấp ra ngoài hình để đóng.</div>';
  document.body.appendChild(ov);

  var zi = ov.querySelector("img");
  var s = 1, tx = 0, ty = 0, fit = 1, moved = false, drag = null, opener = null;

  function apply() { zi.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + s + ")"; }
  function reset() {
    var w = zi.naturalWidth, h = zi.naturalHeight;
    if (!w || !h) return;
    // fill the viewport (upscale small images too), leaving room for the button bar
    fit = Math.min(innerWidth * 0.96 / w, innerHeight * 0.88 / h);
    s = fit;
    tx = (innerWidth - w * s) / 2;
    ty = (innerHeight - h * s) / 2;
    apply();
  }
  function open(img) {
    opener = img;
    zi.alt = img.alt || "";
    zi.onload = reset;
    zi.src = img.currentSrc || img.src;
    ov.classList.add("open");
    document.documentElement.style.overflow = "hidden";
    if (zi.complete && zi.naturalWidth) reset();
  }
  function close() {
    ov.classList.remove("open");
    document.documentElement.style.overflow = "";
    zi.removeAttribute("src");
    if (opener) { try { opener.focus({ preventScroll: true }); } catch (e) {} opener = null; }
  }

  // Content images only: skip logos, icons and images inside the zoom overlay.
  document.addEventListener("click", function (e) {
    var img = e.target;
    if (!img.matches || !img.matches(".rst-content img") || img.closest(".headerlink")) return;
    e.preventDefault(); // images wrapped in a link (:target:) open the zoom instead of navigating
    open(img);
  });

  ov.querySelector(".zclose").addEventListener("click", close);
  ov.querySelector(".zreset").addEventListener("click", reset);
  document.addEventListener("keydown", function (e) {
    if (!ov.classList.contains("open")) return;
    if (e.key === "Escape") close();
    else if (e.key === "0") reset();
  });
  window.addEventListener("resize", function () { if (ov.classList.contains("open")) reset(); });

  ov.addEventListener("wheel", function (e) {
    e.preventDefault();
    var f = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    var ns = Math.max(fit * 0.5, Math.min(s * f, 12));
    tx = e.clientX - (e.clientX - tx) * (ns / s);
    ty = e.clientY - (e.clientY - ty) * (ns / s);
    s = ns;
    apply();
  }, { passive: false });

  ov.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".zbar")) return;
    drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty };
    moved = false;
    ov.setPointerCapture(e.pointerId);
  });
  ov.addEventListener("pointermove", function (e) {
    if (!drag) return;
    var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
    tx = drag.tx + dx;
    ty = drag.ty + dy;
    apply();
  });
  ov.addEventListener("pointerup", function (e) {
    var wasClick = drag && !moved && e.target === ov;
    drag = null;
    if (wasClick) close();
  });
  zi.addEventListener("dblclick", reset);
  }
})();
