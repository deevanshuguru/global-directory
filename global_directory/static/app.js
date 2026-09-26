/**
 * app.js — Global Directory
 * Handles all client-side logic: filtering, sorting, searching,
 * grid/list view toggle, extension chips, and file preview modal.
 * Items are read from a <script type="application/json"> tag —
 * no server round-trip needed for filtering or sorting.
 */

"use strict";

// ── State ──────────────────────────────────────────────────────────────────
var ALL  = JSON.parse(document.getElementById("gd").textContent);
var ft   = "all";   // active type filter
var fe   = null;    // active extension filter
var fs   = "name";  // sort key
var fa   = true;    // sort ascending
var fq   = "";      // search query
var vm   = "grid";  // view mode: "grid" | "list"

// ── Previewable file types ─────────────────────────────────────────────────
// Determines whether clicking a file opens preview or triggers download.
var PREV_TEXT  = new Set([".txt",".md",".py",".js",".ts",".jsx",".tsx",
  ".html",".css",".json",".xml",".yaml",".yml",".toml",".ini",".sh",
  ".bash",".zsh",".rb",".go",".rs",".c",".cpp",".h",".java",".kt",
  ".swift",".php",".sql",".csv",".env",".log",".conf",".cfg",
  ".r",".vue",".dockerfile",".gitignore"]);
var PREV_IMAGE = new Set([".jpg",".jpeg",".png",".gif",".webp",".svg",".bmp"]);
var PREV_AUDIO = new Set([".mp3",".wav",".ogg",".m4a",".aac",".flac"]);
var PREV_VIDEO = new Set([".mp4",".webm",".ogv"]);
var PREV_PDF   = new Set([".pdf"]);

function canPreview(item) {
  return PREV_TEXT.has(item.ext)  || PREV_IMAGE.has(item.ext) ||
         PREV_AUDIO.has(item.ext) || PREV_VIDEO.has(item.ext) ||
         PREV_PDF.has(item.ext);
}

// ── Initialise on page load ────────────────────────────────────────────────
window.onload = function() {
  buildChips();
  render();
  bindEvents();
};

// ── Event bindings ─────────────────────────────────────────────────────────
function bindEvents() {

  // Search input
  document.getElementById("si").oninput = function(e) {
    fq = e.target.value.toLowerCase();
    document.getElementById("xb").classList.toggle("hidden", !fq);
    render();
  };
  document.getElementById("xb").onclick = function() {
    fq = "";
    document.getElementById("si").value = "";
    document.getElementById("xb").classList.add("hidden");
    render();
  };

  // Type filter tabs
  document.querySelectorAll(".tab").forEach(function(b) {
    b.onclick = function() {
      document.querySelectorAll(".tab").forEach(function(x) { x.classList.remove("on"); });
      b.classList.add("on");
      ft = b.dataset.f;
      fe = null; // reset extension filter when type changes
      document.querySelectorAll(".ec").forEach(function(x) { x.classList.remove("on"); });
      render();
    };
  });

  // Sort buttons — clicking the active sort reverses direction
  document.querySelectorAll(".sbtn").forEach(function(b) {
    b.onclick = function() {
      var k = b.dataset.s;
      if (fs === k) { fa = !fa; } else { fs = k; fa = true; }
      document.querySelectorAll(".sbtn").forEach(function(x) {
        x.textContent = x.textContent.replace(" \u25b2","").replace(" \u25bc","");
        x.classList.remove("on");
      });
      b.classList.add("on");
      b.textContent += fa ? " \u25b2" : " \u25bc";
      render();
    };
  });

  // View toggle: grid / list
  document.getElementById("gb").onclick = function() {
    vm = "grid";
    document.getElementById("gb").classList.add("on");
    document.getElementById("lb").classList.remove("on");
    render();
  };
  document.getElementById("lb").onclick = function() {
    vm = "list";
    document.getElementById("lb").classList.add("on");
    document.getElementById("gb").classList.remove("on");
    render();
  };

  // Modal: close button, overlay click, Escape key
  document.getElementById("modal-close").onclick = closeModal;
  document.getElementById("modal").onclick = function(e) {
    if (e.target === document.getElementById("modal")) closeModal();
  };
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") closeModal();
  });
}

// ── Extension chips ────────────────────────────────────────────────────────
// Built once from ALL items. Clicking a chip filters to that extension.
function buildChips() {
  var counts = {};
  ALL.forEach(function(i) {
    if (!i.is_dir && i.ext) counts[i.ext] = (counts[i.ext] || 0) + 1;
  });
  var keys = Object.keys(counts).sort(function(a, b) { return counts[b] - counts[a]; });
  if (!keys.length) return;

  var er  = document.getElementById("er");
  var lbl = document.createElement("span");
  lbl.className   = "el";
  lbl.textContent = "Extensions:";
  er.appendChild(lbl);

  keys.forEach(function(ext) {
    var c = document.createElement("button");
    c.className      = "ec";
    c.dataset.ext    = ext;
    c.innerHTML      = ext + '<span class="ecn">' + counts[ext] + "</span>";
    c.onclick = function() {
      if (fe === ext) {
        // Toggle off
        fe = null;
        c.classList.remove("on");
      } else {
        // Activate this chip, deactivate others, reset type filter
        fe = ext;
        document.querySelectorAll(".ec").forEach(function(x) { x.classList.remove("on"); });
        c.classList.add("on");
        ft = "all";
        document.querySelectorAll(".tab").forEach(function(x) { x.classList.remove("on"); });
        document.querySelector(".tab[data-f=\"all\"]").classList.add("on");
      }
      render();
    };
    er.appendChild(c);
  });
}

// ── Filtering + sorting ────────────────────────────────────────────────────
function filtered() {
  return ALL.filter(function(i) {
    if (ft !== "all" && i.type !== ft) return false;
    if (fe && i.ext !== fe) return false;
    if (fq && i.name.toLowerCase().indexOf(fq) < 0) return false;
    return true;
  }).sort(function(a, b) {
    // Folders always appear before files
    if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
    var c = 0;
    if      (fs === "name")     c = a.name.localeCompare(b.name);
    else if (fs === "size")     c = a.size - b.size;
    else if (fs === "modified") c = a.modified.localeCompare(b.modified);
    else                        c = a.ext.localeCompare(b.ext);
    return fa ? c : -c;
  });
}

// ── Render ─────────────────────────────────────────────────────────────────
function render() {
  var items = filtered();

  // Update stat counters
  document.getElementById("sf").textContent  = items.filter(function(i) { return i.is_dir; }).length;
  document.getElementById("sfi").textContent = items.filter(function(i) { return !i.is_dir; }).length;
  document.getElementById("sv").textContent  = items.length;

  var wrap = document.getElementById("wrap");
  var emp  = document.getElementById("emp");

  if (!items.length) {
    wrap.innerHTML = "";
    emp.classList.remove("hidden");
    return;
  }
  emp.classList.add("hidden");

  if (vm === "list") {
    wrap.className = "lv";
    wrap.innerHTML =
      '<div class="lhdr">' +
        "<span></span><span>Name</span><span>Type</span>" +
        '<span style="text-align:right">Size</span>' +
        '<span style="text-align:right">Date</span>' +
        "<span></span>" +
      "</div>" +
      items.map(lrow).join("");
  } else {
    wrap.className = "gv";
    wrap.innerHTML = items.map(gcard).join("");
  }

  // Attach preview click handlers after DOM is updated
  attachPreviewListeners(items);
}

// ── Card builder (grid view) ───────────────────────────────────────────────
function gcard(item) {
  if (item.is_dir) {
    return '<a href="' + item.url + '" class="card fdc">' +
      '<div style="font-size:28px;line-height:1">' + item.icon + "</div>" +
      '<div style="font-size:11px;font-weight:600;word-break:break-word;line-height:1.4">' + esc(item.name) + "</div>" +
      '<div style="font-size:10px;color:#94a3b8;margin-top:auto">Folder</div>' +
    "</a>";
  }

  var badge = item.ext
    ? '<span style="font-size:9px;font-weight:700;padding:2px 5px;border-radius:5px;background:' +
        item.color + '20;color:' + item.color + '">' + item.ext + "</span>"
    : "";

  var isP = canPreview(item);

  // Download button shown on card hover (only for previewable files —
  // non-previewable files download on click, so no separate button needed)
  var dlBtn = isP
    ? '<a href="' + item.url + '" download class="card-dl" ' +
        'onclick="event.stopPropagation()" title="Download">\u2193</a>'
    : "";

  return '<a href="' + (isP ? "#" : item.url) + '" class="card" ' +
    'data-key="' + esc(item.url) + '"' + (isP ? "" : " download") + ">" +
    '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:3px">' +
      '<div style="font-size:28px;line-height:1">' + item.icon + "</div>" + badge +
    "</div>" +
    '<div style="font-size:11px;font-weight:600;word-break:break-word;line-height:1.4">' + esc(item.name) + "</div>" +
    '<div style="font-size:10px;color:#94a3b8;margin-top:auto">' + item.size_str + "</div>" +
    dlBtn +
  "</a>";
}

// ── Row builder (list view) ────────────────────────────────────────────────
function lrow(item) {
  var cls  = "lrow" + (item.is_dir ? " fd" : "");
  var isP  = !item.is_dir && canPreview(item);
  var href = item.is_dir ? item.url : (isP ? "#" : item.url);

  // Action buttons: eye (preview) + arrow (download)
  var eyeBtn = isP
    ? '<button class="row-btn" title="Preview" ' +
        '>\uD83D\uDC41\uFE0F</button>'
    : "";
  var dlBtn = item.is_dir
    ? ""
    : '<a href="' + item.url + '" download class="row-btn" ' +
        'onclick="event.stopPropagation()" title="Download">\u2193</a>';

  return '<a href="' + href + '" class="' + cls + '" data-key="' + esc(item.url) + '"' +
    (item.is_dir || isP ? "" : " download") + ">" +
    '<span style="font-size:18px;text-align:center">' + item.icon + "</span>" +
    '<span style="font-size:12px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="' + esc(item.name) + '">' + esc(item.name) + "</span>" +
    '<span style="font-size:10px;color:#94a3b8;text-transform:capitalize">' + item.type + "</span>" +
    '<span style="font-size:11px;color:#64748b;text-align:right">' + item.size_str + "</span>" +
    '<span style="font-size:10px;color:#94a3b8;text-align:right">' + item.modified + "</span>" +
    '<span class="row-acts">' + eyeBtn + dlBtn + "</span>" +
  "</a>";
}

// ── Attach preview click listeners after render ────────────────────────────
function attachPreviewListeners(items) {
  items.forEach(function(item) {
    if (item.is_dir || !canPreview(item)) return;
    document.querySelectorAll("[data-key=\"" + item.url + "\"]").forEach(function(el) {
      el.onclick = function(e) { e.preventDefault(); showPreview(item); };
    });
  });
}

// ── Preview modal ──────────────────────────────────────────────────────────
function showPreview(item) {
  // Populate header
  document.getElementById("modal-icon").textContent = item.icon;
  document.getElementById("modal-name").textContent = item.name;
  document.getElementById("modal-meta").textContent =
    item.size_str + (item.size_str ? "  \u00b7  " : "") + item.modified;

  // Set download link
  var dlEl = document.getElementById("modal-dl");
  dlEl.href = item.url;
  dlEl.setAttribute("download", item.name);

  var body    = document.getElementById("modal-body");
  body.innerHTML = "";
  var previewUrl = "/preview" + item.url;

  if (PREV_IMAGE.has(item.ext)) {
    // ── Image ──
    var img = document.createElement("img");
    img.src = previewUrl;
    img.alt = item.name;
    body.appendChild(img);

  } else if (PREV_AUDIO.has(item.ext)) {
    // ── Audio player ──
    var audio = document.createElement("audio");
    audio.src      = previewUrl;
    audio.controls = true;
    body.appendChild(audio);

  } else if (PREV_VIDEO.has(item.ext)) {
    // ── Video player ──
    var video = document.createElement("video");
    video.src      = previewUrl;
    video.controls = true;
    body.appendChild(video);

  } else if (PREV_PDF.has(item.ext)) {
    // ── PDF inline ──
    var iframe = document.createElement("iframe");
    iframe.src = previewUrl;
    body.appendChild(iframe);

  } else if (PREV_TEXT.has(item.ext)) {
    // ── Code / text with highlight.js syntax highlighting ──
    var pre  = document.createElement("pre");
    var code = document.createElement("code");
    code.textContent = "Loading...";
    pre.appendChild(code);
    body.appendChild(pre);

    fetch(previewUrl)
      .then(function(r) { return r.text(); })
      .then(function(text) {
        code.textContent = text;
        // highlight.js auto-detects the language from the content
        if (window.hljs) hljs.highlightElement(code);
      })
      .catch(function() { code.textContent = "Could not load preview."; });
  }

  // Show modal, lock body scroll
  document.getElementById("modal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  document.getElementById("modal").classList.add("hidden");
  document.getElementById("modal-body").innerHTML = ""; // stop audio/video playback
  document.body.style.overflow = "";
}

// ── Utility: HTML escape ───────────────────────────────────────────────────
function esc(s) {
  var d = document.createElement("div");
  d.appendChild(document.createTextNode(s));
  return d.innerHTML;
}
