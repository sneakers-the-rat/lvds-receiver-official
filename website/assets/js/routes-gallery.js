// Routes galleries (board page and every pass page): clicking a
// thumbnail swaps the main viewer instead of navigating to the
// SVG. The thumbnails are plain links to their SVGs, so without
// JavaScript they simply open the render; with it, the click is
// intercepted here. The viewer image stays wrapped in a link
// (.routes-open) whose href tracks the currently shown view, so
// clicking the big image opens that SVG full-size in a new tab
// either way. Binding is class-based and scoped to each
// .routes-gallery container, so this one script serves every
// gallery on the site.
(function () {
  document.querySelectorAll(".routes-gallery").forEach(function (gallery) {
    var main = gallery.querySelector(".routes-main");
    var open = gallery.querySelector(".routes-open");
    var caption = gallery.querySelector(".routes-caption");
    if (!main || !open) return;
    var thumbs = gallery.querySelectorAll(".routes-thumb");
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
  });
})();
