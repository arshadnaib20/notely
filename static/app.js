const $ = (s) => document.querySelector(s);
let currentId = null;
let activeTag = "";
let searchQ = "";
let saveTimer = null;

const listEl = $("#noteList");
const tagsEl = $("#tagList");
const editor = $("#editor");
const emptyState = $("#emptyState");
const titleEl = $("#title");
const bodyEl = $("#body");
const metaEl = $("#meta");

marked.setOptions({ gfm: true, breaks: true });

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  return res.json();
}

function fmtDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    ", " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

async function refresh() {
  const params = new URLSearchParams();
  if (searchQ) params.set("q", searchQ);
  if (activeTag) params.set("tag", activeTag);
  const notes = await api("/api/notes?" + params.toString());
  listEl.innerHTML = notes.length
    ? notes.map((n) => `
        <div class="note-item ${n.id === currentId ? "active" : ""}" data-id="${n.id}">
          <h4>${escapeHtml(n.title || "Untitled")}</h4>
          <p>${escapeHtml((n.body || "").replace(/[#*`]/g, "").slice(0, 80))}</p>
          <div class="when">${fmtDate(n.updated_at)}</div>
        </div>`).join("")
    : `<p style="color:var(--muted);padding:10px;font-size:13px;">No notes found.</p>`;
  listEl.querySelectorAll(".note-item").forEach((el) =>
    el.addEventListener("click", () => openNote(Number(el.dataset.id)))
  );
  const tags = await api("/api/tags");
  tagsEl.innerHTML = `<span class="tag-chip ${!activeTag ? "active" : ""}" data-tag="">all</span>` +
    tags.map((t) => `<span class="tag-chip ${activeTag === t.name ? "active" : ""}" data-tag="${t.name}">#${t.name} · ${t.count}</span>`).join("");
  tagsEl.querySelectorAll(".tag-chip").forEach((el) =>
    el.addEventListener("click", () => { activeTag = el.dataset.tag; refresh(); })
  );
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function openNote(id) {
  const n = await api("/api/notes/" + id);
  currentId = id;
  editor.classList.remove("hidden");
  emptyState.classList.add("hidden");
  titleEl.value = n.title;
  bodyEl.value = n.body;
  metaEl.textContent = "Edited " + fmtDate(n.updated_at);
  renderPreview();
  refresh();
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(save, 600);
}

async function save() {
  if (!currentId) return;
  await api("/api/notes/" + currentId, {
    method: "PUT",
    body: JSON.stringify({ title: titleEl.value, body: bodyEl.value }),
  });
  metaEl.textContent = "Saved " + new Date().toLocaleTimeString();
  refresh();
}

async function newNote() {
  const n = await api("/api/notes", { method: "POST", body: JSON.stringify({ title: "", body: "" }) });
  openNote(n.id);
  titleEl.focus();
}

async function deleteNote() {
  if (!currentId) return;
  if (!confirm("Delete this note?")) return;
  await api("/api/notes/" + currentId, { method: "DELETE" });
  currentId = null;
  editor.classList.add("hidden");
  emptyState.classList.remove("hidden");
  refresh();
}

function renderPreview() {
  $("#md").innerHTML = marked.parse(bodyEl.value || "");
}

$("#newBtn").addEventListener("click", newNote);
$("#deleteBtn").addEventListener("click", deleteNote);
$("#previewToggle").addEventListener("click", () => {
  $(".editor-body").classList.toggle("previewing");
});
titleEl.addEventListener("input", scheduleSave);
bodyEl.addEventListener("input", () => { renderPreview(); scheduleSave(); });
$("#search").addEventListener("input", (e) => { searchQ = e.target.value; refresh(); });

$("#themeToggle").addEventListener("click", () => {
  const cur = document.documentElement.dataset.theme === "dark" ? "" : "dark";
  document.documentElement.dataset.theme = cur;
  localStorage.setItem("notely-theme", cur);
});
if (localStorage.getItem("notely-theme") === "dark") {
  document.documentElement.dataset.theme = "dark";
}

refresh();
