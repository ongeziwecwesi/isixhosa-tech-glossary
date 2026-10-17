// Front end for the glossary. Plain JavaScript, no framework: it only
// needs to call three API endpoints and draw the results.

// Page text in each language. Fill in the isiXhosa ("xh") strings and an
// English/isiXhosa toggle appears in the header. Empty strings fall back
// to English.
const LABELS = {
  en: {
    title: "isiXhosa Tech Glossary",
    tagline: "Computing and technology terms in English and isiXhosa",
    apiDocs: "API docs",
    searchLabel: "Search for a term",
    searchPlaceholder: "Search in English or isiXhosa, e.g. network",
    all: "All",
    showMore: "Show more",
    suggestTitle: "Suggest a term",
    suggestHint: "Know a good isiXhosa term that's missing? Suggestions are reviewed before they appear.",
    fieldEnglish: "English term",
    fieldXhosa: "isiXhosa term",
    fieldCategory: "Category",
    fieldDefinition: "What does it mean? (in English)",
    fieldExample: "Example sentence in isiXhosa (optional)",
    fieldName: "Your name (optional)",
    send: "Send suggestion",
    thanks: "Thank you. Your suggestion will be reviewed.",
    empty: "The glossary is empty for now. Terms are being added.",
    noResults: "No terms match your search.",
    count: (n) => (n === 1 ? "1 term" : `${n} terms`),
  },
  xh: {
    title: "", tagline: "", apiDocs: "", searchLabel: "", searchPlaceholder: "",
    all: "", showMore: "", suggestTitle: "", suggestHint: "",
    fieldEnglish: "", fieldXhosa: "", fieldCategory: "", fieldDefinition: "",
    fieldExample: "", fieldName: "", send: "", thanks: "", empty: "", noResults: "",
    count: null,
  },
};

const PAGE_SIZE = 20;
const state = { q: "", category: "", offset: 0, lang: "en" };

const $ = (id) => document.getElementById(id);

function t(key) {
  return LABELS[state.lang][key] || LABELS.en[key];
}

function applyLabels() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-label]").forEach((el) => {
    el.textContent = t(el.dataset.label);
  });
  document.querySelectorAll("[data-label-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.labelPlaceholder);
  });
}

// Build an element with text set via textContent, never innerHTML, so text
// from the database can't inject HTML or scripts into the page.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function renderTerm(term) {
  const li = el("li", "term");
  const head = el("div", "term-head");
  head.append(el("span", "term-xh", term.xhosa), el("span", "term-en", term.english),
              el("span", "term-cat", term.category));
  li.append(head, el("p", "", term.definition));
  if (term.definition_xh) li.append(el("p", "", term.definition_xh));
  if (term.example_xh) li.append(el("p", "example", term.example_xh));
  return li;
}

async function search({ append = false } = {}) {
  if (!append) state.offset = 0;
  const params = new URLSearchParams({ limit: PAGE_SIZE, offset: state.offset });
  if (state.q) params.set("q", state.q);
  if (state.category) params.set("category", state.category);

  const res = await fetch(`/api/terms?${params}`);
  if (!res.ok) return;
  const page = await res.json();

  const list = $("results");
  if (!append) list.replaceChildren();
  page.items.forEach((term) => list.append(renderTerm(term)));

  const shown = page.offset + page.items.length;
  $("more").hidden = shown >= page.total;

  const countFn = LABELS[state.lang].count || LABELS.en.count;
  if (page.total === 0) {
    $("summary").textContent = state.q || state.category ? t("noResults") : t("empty");
  } else {
    $("summary").textContent = countFn(page.total);
  }
}

async function loadCategories() {
  const res = await fetch("/api/categories");
  if (!res.ok) return;
  const categories = await res.json();

  const box = $("categories");
  const select = $("suggest-category");
  box.replaceChildren();
  select.replaceChildren();

  const makeChip = (name, label, count) => {
    const chip = el("button", "chip", label);
    chip.type = "button";
    chip.setAttribute("aria-pressed", String(state.category === name));
    if (count !== undefined) chip.append(el("span", "count", String(count)));
    chip.addEventListener("click", () => {
      state.category = name;
      box.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
      chip.setAttribute("aria-pressed", "true");
      search();
    });
    return chip;
  };

  box.append(makeChip("", t("all")));
  categories.forEach((c) => {
    box.append(makeChip(c.name, c.name, c.count));
    const option = el("option", "", c.name);
    option.value = c.name;
    select.append(option);
  });
}

// Wait until the person stops typing for a moment before searching,
// instead of sending a request on every key press.
let timer;
$("q").addEventListener("input", (e) => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    state.q = e.target.value.trim();
    search();
  }, 250);
});

$("more").addEventListener("click", () => {
  state.offset += PAGE_SIZE;
  search({ append: true });
});

$("suggest-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const status = $("suggest-status");
  const data = Object.fromEntries(new FormData(form));
  for (const key of ["example_xh", "submitted_by"]) {
    if (!data[key]) delete data[key];
  }

  const res = await fetch("/api/suggestions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (res.ok) {
    status.className = "form-status";
    status.textContent = t("thanks");
    form.reset();
  } else {
    const body = await res.json().catch(() => ({}));
    status.className = "form-status error";
    status.textContent = typeof body.detail === "string"
      ? body.detail
      : "Please check the form and try again.";
  }
});

// Show the language toggle only once the isiXhosa labels are filled in
if (LABELS.xh.title) {
  const toggle = $("lang-toggle");
  toggle.hidden = false;
  toggle.addEventListener("click", () => {
    state.lang = state.lang === "en" ? "xh" : "en";
    toggle.textContent = state.lang === "en" ? "isiXhosa" : "English";
    applyLabels();
    loadCategories();
    search();
  });
}

applyLabels();
loadCategories();
search();
