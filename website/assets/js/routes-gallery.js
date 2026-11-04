// Board page Routes gallery: clicking a thumbnail swaps the main
// viewer instead of navigating to the SVG. The thumbnails are
// plain links to their SVGs, so without JavaScript they simply
// open the render; with it, the click is intercepted here. The
// viewer image stays wrapped in a link (#routes-open) whose href
// tracks the currently shown view, so clicking the big image opens
// that SVG full-size in a new tab either way.
(function () {
  var main = document.getElementById("routes-main");
  var open = document.getElementById("routes-open");
  var caption = document.getElementById("routes-caption");
  if (!main || !open) return;
  var thumbs = document.querySelectorAll(".routes-thumb");
  thumbs.forEach(function (t) {
    t.addEventListener("click", function (ev) {
      ev.preventDefault();
      var url = t.getAttribute("href");
      var label = t.getAttribute("data-label") || "";
      main.setAttribute("src", url);
      main.setAttribute("alt", label);
      open.setAttribute("href", url);
      if (caption) caption.textContent = label;
      thumbs.forEach(function (o) {
        o.classList.toggle("active", o === t);
      });
    });
  });
})();
