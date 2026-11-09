"use strict";

const $ = (selector) => document.querySelector(selector);
const view = $("#view");
const kinds = ["Word", "Phrase", "Grammar", "Conjugation"];
const studyLanguages = {
  reference: {code: "en", name: "English", optionalArticle: /^(?:a|an|the)\s+/u},
  target: {code: "fr", name: "French", characters: "àâçéèêëîïôœùûüÿ",
    nounArticle: /^(?:(?:le|la|les|un|une|des)\s+|l['’])/iu},
};
const directions = ["reference", "target"];
const samples = {
  "Grammar pattern": "Make me a card for se faire + infinitive, e.g. il s’est faire connaître.",
  "Everyday phrase": "Help me learn how to use « ça marche » in conversation.",
  "Conjugation": "Make a card for the present tense of prendre, with short examples.",
};
const icons = {
  decks: '<rect x="5" y="6" width="15" height="15" rx="2"/><path d="M3 17V5a2 2 0 0 1 2-2h12m-8 9h7m-7 4h5"/>',
  deck: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6m-6 4h6m-6 4h4"/>',
  study: '<path d="M3 5h5a4 4 0 0 1 4 4v12a4 4 0 0 0-4-4H3zm18 0h-5a4 4 0 0 0-4 4v12a4 4 0 0 1 4-4h5z"/>',
  test: '<path d="M5 12h4l2-7 3 14 2-7h3"/><rect x="2" y="2" width="20" height="20" rx="5"/>',
  audio: '<path d="M11 5 6 9H3v6h3l5 4zM15 9a4 4 0 0 1 0 6m3-9a8 8 0 0 1 0 12"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2"/>',
  moon: '<path d="M20.9 13.3A9 9 0 0 1 10.7 3.1a9 9 0 1 0 10.2 10.2Z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  spark: '<path d="m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z"/>',
  arrow: '<path d="M4 12h15m-6-6 6 6-6 6"/>',
  back: '<path d="M20 12H5m6-6-6 6 6 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
};

function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[ch]);
}

const state = {
  cards: [], decks: [], library: "reading", saveDeck: "reading", loaded: false, loadError: "", screen: "deck", detail: null,
  composer: "", revision: "", draft: null, draftBusy: false, draftError: "",
  saving: false, query: "", kind: "", topic: "", session: null,
};

const deckById = (id) => state.decks.find((deck) => deck.id === id);
const included = (card) => Boolean(card.enabled && deckById(card.deck_id)?.enabled);
const due = (card) => card.due_at <= Date.now() / 1000;
const cardById = (id) => state.cards.find((card) => card.id === id);
let toastTimer;
let audioPlayer;
let audioUrl;
let audioButton;
let audioVersion = 0;
let selectedFrench = "";
let deleteId;

function toast(message) {
  clearTimeout(toastTimer);
  const notice = $("#notice");
  notice.textContent = message;
  notice.hidden = false;
  toastTimer = setTimeout(() => { notice.hidden = true; }, 5500);
}

async function api(path, data, audio = false) {
  const response = await fetch(`/api/${path}`, data === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data),
  });
  if (audio && response.ok) return response.blob();
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.error || "Request failed.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

async function loadCards() {
  try {
    const {cards, decks} = await api("cards");
    Object.assign(state, {cards, decks});
    state.loadError = "";
  } catch (error) {
    state.loadError = error.message;
  }
  state.loaded = true;
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const dark = theme === "dark";
  const button = $("#theme");
  button.setAttribute("aria-checked", dark);
  button.setAttribute("aria-label", "Dark mode");
  button.innerHTML = `${icon(dark ? "sun" : "moon")}<span>Dark mode ${dark ? "on" : "off"}</span>`;
  document.querySelector('meta[name="theme-color"]').content = dark ? "#131625" : "#f7f8fc";
}

function head(title, description, action = "") {
  return `<header class="page-head"><div>
    <h1>${title}</h1><p>${description}</p></div>${action}</header>`;
}

function empty(iconName, title, text, action = "") {
  return `<section class="panel empty"><span class="mark">${icon(iconName)}</span>
    <h2>${title}</h2><p>${text}</p>${action}</section>`;
}

function badge(kind) {
  return `<span class="chip ${escapeHtml(kind.toLowerCase())}">${escapeHtml(kind)}</span>`;
}

function speaker(text) {
  return `<button type="button" class="icon-button" data-action="listen" data-text="${escapeHtml(text)}"
    aria-label="Listen in French" title="Listen in French">${icon("audio")}</button>`;
}

function dueLabel(card) {
  if (!card.enabled) return "Disabled";
  if (!included(card)) return "Outside training";
  if (card.reviews === 0) return "New card";
  if (due(card)) return "Review due";
  const scheduled = new Date(card.due_at * 1000);
  const today = scheduled.toDateString() === new Date().toDateString();
  const format = today ? {hour: "numeric", minute: "2-digit"} : {month: "short", day: "numeric"};
  return `Due ${scheduled.toLocaleString(undefined, format)}`;
}

function normalize(text, accents = true, locale) {
  const normalized = text.normalize("NFC").toLocaleLowerCase(locale)
    .replace(/[’‘ʼ]/gu, "'").replace(/[‑‐]/gu, "-")
    .trim().replace(/[.!?…]+$/gu, "").replace(/\s+/gu, " ").trim();
  return accents ? normalized : normalized.normalize("NFD").replace(/\p{M}/gu, "");
}

function libraryCards() {
  return state.cards.filter((card) => state.library === "all" || card.deck_id === state.library);
}

function deckOptions(decks, selected) {
  return decks.map((deck) => `<option value="${deck.id}" ${selected === deck.id ? "selected" : ""}>
    ${escapeHtml(deck.name)}</option>`).join("");
}

function matchingCards() {
  const query = normalize(state.query, false);
  return libraryCards().filter((card) => (!state.kind || state.kind === card.kind)
    && (!state.topic || state.topic === card.topic)
    && normalize(`${card.title} ${card.cue}`, false).includes(query));
}

function renderCardGrid() {
  const grid = $("#card-grid");
  if (!grid) return;
  if (!state.loaded) {
    grid.innerHTML = '<p class="muted">Loading your deck…</p>';
    return;
  }
  if (state.loadError) {
    grid.innerHTML = empty("deck", "Couldn’t load your deck", escapeHtml(state.loadError),
      '<button class="button" data-action="refresh">Try again</button>');
    return;
  }
  const cards = matchingCards();
  if (!cards.length) {
    grid.innerHTML = libraryCards().length
      ? empty("deck", "No matching cards", "Try another search, topic or card type.")
      : empty("deck", "Your deck is empty", "Make a card from a word, phrase or grammar pattern you want to remember.",
        '<button class="button subtle" data-action="sample" data-sample="Grammar pattern">Try the grammar example</button>');
    return;
  }
  const tiles = (group) => `<div class="card-grid">${group.map((card) => `
    <button class="panel card-tile" data-action="open-card" data-id="${card.id}">
      ${badge(card.kind)}<h3 lang="fr">${escapeHtml(card.title)}</h3><p>${escapeHtml(card.cue)}</p>
      <small>${escapeHtml(dueLabel(card))}</small>
    </button>`).join("")}</div>`;
  if (!deckById(state.library)?.published) {
    grid.innerHTML = tiles(cards);
    return;
  }
  const groups = new Map();
  for (const card of cards) {
    const topic = card.topic || "Core expressions and other words";
    if (!groups.has(topic)) groups.set(topic, []);
    groups.get(topic).push(card);
  }
  const entries = [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  grid.innerHTML = entries.map(([topic, group]) => {
    const study = group.some(included)
      ? `<a class="button subtle" href="#study/${state.library}?${new URLSearchParams({topic})}">Study topic</a>`
      : "";
    return `<section class="topic-section"><div class="section-title">
      <h3>${escapeHtml(topic)} <small>· ${group.length}</small></h3>${study}
      </div>${tiles(group)}</section>`;
  }).join("");
}

function deckPage() {
  const count = state.cards.filter((card) => included(card) && due(card)).length;
  const deck = deckById(state.library);
  const published = Boolean(deck?.published);
  const topics = published ? [...new Set(libraryCards().map((card) => card.topic).filter(Boolean))].sort() : [];
  const heading = published
    ? head(escapeHtml(deck.name), escapeHtml(deck.description), '<a class="button" href="#decks">Back to decks</a>')
    : head("My flashcards", "Capture words, phrases and grammar as you come across them.",
      '<button class="button new-card" data-action="focus-composer">' + icon("plus") + ' New card</button>');
  return `${heading}
    ${published ? "" : `
    <div class="deck-top">
      <form id="composer" class="panel composer">
        <div class="panel-heading"><span class="mark">${icon("spark")}</span><div>
          <h2><label for="capture">Make a card</label></h2><p>Ask in your own words. You can review the draft before saving it.</p>
        </div></div>
        <textarea id="capture" name="request" rows="3" maxlength="1600" required
          placeholder="Make me a card for se faire + infinitive…">${escapeHtml(state.composer)}</textarea>
        <div class="composer-bottom">
          <div class="chips" aria-label="Example requests">${Object.keys(samples).map((name) =>
            `<button type="button" class="chip" data-action="sample" data-sample="${name}">${name}</button>`).join("")}</div>
          <button class="button primary" type="submit" ${state.draftBusy || state.saving ? "disabled" : ""}>
            ${state.draftBusy && !state.draft ? "Making draft…" : "Make draft"} ${icon("arrow")}</button>
        </div>
        ${!state.draft && state.draftError ? `<p role="alert" class="status-error">${escapeHtml(state.draftError)}</p>` : ""}
      </form>
      <aside class="panel review-overview">
        <div><h2>Review queue</h2><strong class="number">${count}</strong>
          <p class="subline">${count === 1 ? "card" : "cards"} due now · ${state.cards.filter(included).length} in training</p></div>
        <a href="#test" class="button primary">Start a test ${icon("arrow")}</a>
      </aside>
    </div>
    ${state.draft ? draftPanel() : ""}`}
    <section aria-labelledby="library-title">
      <div class="section-title"><h2 id="library-title">${published ? "Vocabulary" : "Cards"}</h2>
        <div class="filters">
        <select id="library" aria-label="Browse deck">${deckOptions(state.decks, state.library)}
          <option value="all" ${state.library === "all" ? "selected" : ""}>All decks</option></select>
        ${topics.length ? `<select id="topic" aria-label="Filter by topic"><option value="">All topics</option>
          ${topics.map((topic) => `<option value="${escapeHtml(topic)}" ${state.topic === topic ? "selected" : ""}>${escapeHtml(topic)}</option>`).join("")}
        </select>` : ""}
        <input id="search" type="search" aria-label="Search cards" placeholder="Search cards" value="${escapeHtml(state.query)}">
        <select id="kind" aria-label="Filter by card type"><option value="">All types</option>
          ${kinds.map((kind) => `<option ${kind === state.kind ? "selected" : ""}>${kind}</option>`).join("")}</select></div>
      </div><div id="card-grid"></div>
    </section>`;
}

function decksPage() {
  const heading = head("Decks", "Choose what to include in your personal training suite.");
  if (!state.loaded) return heading + '<p class="muted">Loading decks…</p>';
  if (state.loadError) return heading + empty("decks", "Couldn’t load decks", escapeHtml(state.loadError),
    '<button class="button" data-action="refresh">Try again</button>');
  function tiles(published) {
    return state.decks.filter((deck) => Boolean(deck.published) === published).map((deck) => {
      const cards = state.cards.filter((card) => card.deck_id === deck.id);
      const count = cards.filter((card) => card.enabled).length;
      return `<article class="panel deck-tile">
        <div><h3>${escapeHtml(deck.name)}</h3>
          ${deck.description ? `<p>${escapeHtml(deck.description)}</p>` : ""}
          <small>${cards.length} ${cards.length === 1 ? "card" : "cards"}${count < cards.length ? ` · ${cards.length - count} disabled` : ""}</small></div>
        <div class="actions"><a class="button" href="#deck/${deck.id}">Browse cards</a>
          <button class="button ${deck.enabled ? "subtle" : ""}" data-action="toggle-deck" data-id="${deck.id}"
            aria-pressed="${Boolean(deck.enabled)}" aria-label="Include ${escapeHtml(deck.name)} in training">
            ${deck.enabled ? "Included" : "Include in training"}</button></div>
      </article>`;
    }).join("");
  }
  return `${heading}<section class="deck-group">
    <div class="section-title"><h2>Published decks</h2></div><div class="card-grid">${tiles(true)}</div>
    </section><section class="deck-group">
    <div class="section-title"><h2>Local decks</h2></div><div class="card-grid">${tiles(false)}</div>
    <form id="create-deck" class="panel create-deck">
      <label for="deck-name">New local deck</label>
      <div class="actions"><input type="text" id="deck-name" maxlength="60" placeholder="e.g. Words from my reading" required>
        <button type="submit" class="button primary">Create deck</button></div>
    </form></section>`;
}

function textRows(rows) {
  return rows.map((row) => `<div class="text-row"><div>
    ${row.label ? `<small>${escapeHtml(row.label)}</small>` : ""}
    <p lang="fr">${escapeHtml(row.fr)}</p>${row.en ? `<p class="muted">${escapeHtml(row.en)}</p>` : ""}
    </div>${speaker(row.fr)}</div>`).join("");
}

function prose(text) {
  return text.split(/(«[^»]+»)/gu).map((piece) =>
    piece.startsWith("«") && piece.endsWith("»")
      ? `<span lang="fr">${escapeHtml(piece)}</span> ${speaker(piece.slice(1, -1).trim())}`
      : escapeHtml(piece)).join("");
}

function cardContent(card, reverse = false) {
  const heading = reverse ? card.cue : card.title;
  const subheading = reverse ? card.title : card.cue;
  const headingLanguage = reverse ? studyLanguages.reference : studyLanguages.target;
  const subheadingLanguage = reverse ? studyLanguages.target : studyLanguages.reference;
  return `${badge(card.kind)}
    <div class="detail-head"><div><h2 lang="${escapeHtml(headingLanguage.code)}">${escapeHtml(heading)}</h2>
      <p lang="${escapeHtml(subheadingLanguage.code)}">${escapeHtml(subheading)}</p></div>${speaker(card.title)}</div>
    ${card.correction ? `<div class="correction"><h3>Correction</h3>
      <div class="text-row"><p lang="fr">${escapeHtml(card.correction)}</p>${speaker(card.correction)}</div></div>` : ""}
    ${card.notes ? `<section class="detail-section"><h3>How to use it</h3><p>${prose(card.notes)}</p></section>` : ""}
    <section class="detail-section"><h3>Examples</h3>${textRows(card.examples)}</section>
    ${card.forms.length ? `<section class="detail-section"><h3>Forms and tenses</h3>${textRows(card.forms)}</section>` : ""}`;
}

function draftPanel() {
  return `<section class="draft" id="draft" tabindex="-1" aria-label="Card draft">
    <div class="draft-banner"><strong>Card draft</strong>
      <button class="button" data-action="discard" ${state.saving || state.draftBusy ? "disabled" : ""}>Discard draft</button></div>
    <article class="panel detail">
      <p class="draft-request">You asked: ${escapeHtml(state.draft.request)}</p>
      ${cardContent(state.draft.card)}
      <details class="detail-section"><summary>Preview recall questions</summary>
        ${textRows(state.draft.card.exercises.map((row) => ({fr: row.answer, en: row.prompt})))}
      </details>
      <form id="refine" class="detail-section draft-refine">
        <label for="revision">Ask for a change</label>
        <input id="revision" name="request" type="text" maxlength="1600" required
          placeholder="Add a future-tense example…" value="${escapeHtml(state.revision)}">
        <label for="save-deck" class="save-deck-label">Save to local deck</label>
        <select id="save-deck">${deckOptions(state.decks.filter((deck) => !deck.published), state.saveDeck)}</select>
        <div class="session-actions"><button class="button" type="submit" ${state.saving || state.draftBusy ? "disabled" : ""}>
          ${state.draftBusy ? "Working on draft…" : "Update draft"}</button>
          <button class="button primary" type="button" data-action="save" ${state.saving || state.draftBusy ? "disabled" : ""}>
            ${icon("check")} ${state.saving ? "Saving…" : "Save to deck"}</button></div>
        ${state.draftError ? `<p class="status-error" role="alert">${escapeHtml(state.draftError)}</p>` : ""}
      </form>
    </article>
  </section>`;
}

function detailPage() {
  const card = cardById(state.detail);
  const deck = card && deckById(card.deck_id);
  const topicQuery = state.topic && card?.topic === state.topic
    ? `?${new URLSearchParams({topic: state.topic})}` : "";
  const back = `<a class="button" href="#deck/${deck?.id || "reading"}${topicQuery}">${icon("back")} Back to deck</a>`;
  if (!card) return empty("deck", state.loaded ? "Card not found" : "Loading card…", "", back);
  const details = [deck?.name, card.topic, dueLabel(card)].filter(Boolean).join(" · ");
  return `<div class="workspace">${head(deck?.published ? "Published card" : "Saved card", escapeHtml(details), back)}
    <article class="panel detail">${cardContent(card)}
      <div class="session-actions">
        ${included(card) ? `<a class="button primary" href="#study/${card.id}">Study this card</a>` : ""}
        <div class="actions">
          <button class="button" data-action="toggle-card" data-id="${card.id}">${card.enabled ? "Disable card" : "Enable card"}</button>
          ${deck?.published ? "" : `<button class="button" data-action="delete" data-id="${card.id}">Delete card</button>`}
        </div>
      </div>
    </article></div>`;
}

function renderNav() {
  const count = state.cards.filter((card) => included(card) && due(card)).length;
  $("#nav").innerHTML = [["deck", "My cards"], ["decks", "Decks"], ["study", "Study"], ["test", "Test"]].map(([id, label]) => {
    const current = state.screen === id || (id === "deck" && state.screen === "card");
    return `<a href="#${id}" class="nav-link" ${current ? 'aria-current="page"' : ""}>
      ${icon(id)} ${label}${id === "test" && count ? `<span class="count">${count}</span>` : ""}</a>`;
  }).join("");
}

function loadStudyOptions() {
  let saved;
  try {
    saved = JSON.parse(localStorage.getItem("study-options"));
  } catch {
    saved = null;
  }
  const selected = directions.filter((side) => saved?.[side] === true);
  return {shuffle: saved?.shuffle === true, shortcuts: saved?.shortcuts !== false,
    reference: selected.length === 0 || selected.includes("reference"),
    target: selected.includes("target")};
}

const studyOptions = loadStudyOptions();

function shuffled(items) {
  const result = [...items];
  for (let end = result.length - 1; end > 0; end -= 1) {
    const index = Math.floor(Math.random() * (end + 1));
    [result[end], result[index]] = [result[index], result[end]];
  }
  return result;
}

function promptDirection(session) {
  const id = session.ids[session.position];
  const selected = directions.filter((side) => studyOptions[side]);
  if (!selected.includes(session.directions.get(id))) {
    const side = selected.length === 1 ? selected[0] : selected[Math.floor(Math.random() * selected.length)];
    session.directions.set(id, side);
  }
  return session.directions.get(id);
}

function trainingOptions(session) {
  const checkbox = (key, label) => `<label><input type="checkbox" name="${key}"
    ${studyOptions[key] ? "checked" : ""}> ${escapeHtml(label)}</label>`;
  return `<fieldset id="training-options" class="training-options" ${session.busy ? "disabled" : ""}>
    <legend>Session options</legend>
    ${checkbox("shuffle", "Shuffle cards")}
    <span class="training-options-label">Prompt in</span>
    ${directions.map((side) => checkbox(side, studyLanguages[side].name)).join("")}
    ${checkbox("shortcuts", "Letter shortcuts")}
  </fieldset>`;
}

function makeSession(mode, id, practice = false, topic = "") {
  let cards = state.cards.filter((card) => included(card) &&
    (topic ? card.deck_id === id && card.topic === topic : !id || card.id === id));
  if (mode === "test" && !practice) cards = cards.filter(due).sort((a, b) => a.due_at - b.due_at);
  const ordered = cards.map((card) => card.id);
  return {ordered, ids: studyOptions.shuffle ? shuffled(ordered) : [...ordered],
    position: 0, visited: 1, directions: new Map(), revealed: false, practice, topic,
    answer: "", result: null, ratings: [], busy: false, error: ""};
}

function sessionPage(mode) {
  const session = state.session;
  const isTest = mode === "test";
  const card = cardById(session.ids[session.position]);
  const title = isTest ? (session.practice ? "Practice test" : "Test yourself") : session.topic || "Study cards";
  const description = isTest
    ? (session.practice ? "Practise cards in your training suite. Your review dates stay as they are." : "Write the translation from memory, then rate your recall.")
    : "Think of the translation, then reveal the card to read and listen.";
  const topicBack = session.topic && deckById(state.detail)
    ? `<a class="button" href="#deck/${state.detail}?${new URLSearchParams({topic: session.topic})}">Back to topic</a>`
    : "";
  const heading = head(escapeHtml(title), description,
    isTest && state.cards.some(included)
      ? `<button class="button" data-action="${session.practice ? "due-test" : "all-test"}">${session.practice ? "Due cards" : "Practise all cards"}</button>`
      : topicBack);
  if (!card) {
    const finished = session.position > 0;
    let summary = "Include a deck with enabled cards to begin.";
    if (finished && isTest) {
      const strong = session.ratings.filter((rating) => rating === "got-it").length;
      summary = `${session.ratings.length} reviewed · ${strong} recalled confidently. ${session.practice ? "Review dates are unchanged." : "Your next reviews are scheduled."}`;
    } else if (finished) {
      summary = `You studied ${session.position} ${session.position === 1 ? "card" : "cards"}.`;
    } else if (isTest && state.cards.some(included)) {
      summary = "You're caught up on scheduled reviews. You can still practise the full training suite.";
    }
    const title = !state.loaded ? "Loading your cards…" : state.loadError ? "Couldn’t load your deck" : finished
      ? "Session complete" : isTest && state.cards.some(included) ? "No reviews due" : "No cards in training";
    const action = state.loadError ? '<button class="button" data-action="refresh">Try again</button>'
      : finished ? '<button class="button" data-action="restart">Start again</button>'
      : '<a class="button" href="#decks">Choose decks</a>';
    return `<div class="workspace">${heading}${trainingOptions(session)}${empty(mode, title, escapeHtml(state.loadError || summary), action)}</div>`;
  }
  const side = promptDirection(session);
  const promptLanguage = studyLanguages[side];
  const answerLanguage = studyLanguages[side === "target" ? "reference" : "target"];
  return `<div class="workspace">${heading}${trainingOptions(session)}<section class="panel session-panel" aria-label="${escapeHtml(title)}">
    <div class="session-head"><span class="chip">${escapeHtml(promptLanguage.name)} → ${escapeHtml(answerLanguage.name)}</span>
      <span>Card ${session.position + 1} of ${session.ids.length}</span></div>
    <progress class="progress" aria-label="Session progress" value="${session.position + 1}" max="${session.ids.length}"></progress>
    ${isTest ? testCard(card, session, side, promptLanguage, answerLanguage)
      : studyCard(card, session, side, promptLanguage, answerLanguage)}
  </section></div>`;
}

function promptHeading(text, language, aloud) {
  return `<div class="prompt-heading"><h2 lang="${escapeHtml(language.code)}">${escapeHtml(text)}</h2>
    ${aloud ? speaker(text) : ""}</div>`;
}

function shortcutLabel(label, key) {
  if (!studyOptions.shortcuts) return label;
  const position = label.toLowerCase().indexOf(key);
  return `${label.slice(0, position)}<u>${label[position]}</u>${label.slice(position + 1)}`;
}

function shortcutAttribute(key) {
  return studyOptions.shortcuts ? `aria-keyshortcuts="${key}"` : "";
}

function studyButton(action, label, key, primary = false) {
  return `<button type="button" class="button${primary ? " primary" : ""}"
    data-action="${action}" ${shortcutAttribute(key)}><span>${shortcutLabel(label, key)}</span></button>`;
}

function studyCard(card, session, side, promptLanguage, answerLanguage) {
  const reverse = side === "target";
  const next = session.position + 1 === session.ids.length ? "Finish study" : "Next card";
  return `<div class="study-actions">
    ${session.revealed ? studyButton("next", next, "n", true) : studyButton("reveal", "Reveal card", "r", true)}
    ${session.position > 0 ? studyButton("previous", "Previous", "p") : ""}
    ${session.revealed ? studyButton("hide", "Hide answer", "h") : ""}
  </div>
  <div class="prompt">${promptHeading(reverse ? card.title : card.cue, promptLanguage, reverse)}
    ${session.revealed ? "" : `<p>Say or think of the ${escapeHtml(answerLanguage.name)} before revealing the card.</p>`}</div>
    ${session.revealed ? `<div class="session-answer" id="revealed" tabindex="-1">${cardContent(card, reverse)}</div>` : ""}`;
}

function exercise(card, side) {
  if (side === "target") {
    const glosses = card.cue.replace(/\s*\([^()]*\)/gu, "").split(";").map((text) => text.trim()).filter(Boolean);
    return {prompt: card.title, answer: card.cue, alternatives: [], accepted: glosses};
  }
  return card.exercises[card.exercise_index ?? 0];
}

function testCard(card, session, side, promptLanguage, answerLanguage) {
  const reverse = side === "target";
  const item = exercise(card, side);
  return `<div class="prompt">${promptHeading(item.prompt, promptLanguage, reverse)}</div>
    ${session.result ? testFeedback(item, session, answerLanguage, !reverse) : `
      <form id="answer" class="answer-form">
        <label for="answer-text">Your answer in ${escapeHtml(answerLanguage.name)}</label>
        <input id="answer-text" type="text" lang="${escapeHtml(answerLanguage.code)}" maxlength="350" autocomplete="off" spellcheck="false" required
          value="${escapeHtml(session.answer)}">
        ${answerLanguage.characters ? `<div class="actions accents" aria-label="${escapeHtml(answerLanguage.name)} characters">
          ${[...answerLanguage.characters].map((char) =>
            `<button class="button subtle" type="button" data-action="accent" data-char="${escapeHtml(char)}">${escapeHtml(char)}</button>`).join("")}
        </div>` : ""}
        <div class="actions"><button class="button primary" type="submit">Check answer</button>
          <button class="button" type="button" data-action="show-answer">Show answer</button></div>
      </form>`}
    ${session.error ? `<p role="alert" class="status-error">${escapeHtml(session.error)}</p>` : ""}`;
}

function testFeedback(item, session, language, aloud) {
  const [heading, description] = {
    match: ["Matches a suggested answer", "Check that you can say it, then rate your recall."],
    close: ["Check the accents", "The letters match. Look at the accents in the suggested answer."],
    other: ["Compare your answer", "If your translation fits the meaning and the prompt, count it as recalled."],
    skipped: ["Suggested answer", "Rate how well you could recall it before looking."],
  }[session.result];
  const labels = session.practice ? ["Again", "Hard", "Got it"] : ["Again · 10 min", "Hard · 1 day", "Got it"];
  const suggested = {match: "got-it", close: "hard", other: "again", skipped: "again"}[session.result];
  const answerRow = (text, label) => `<div class="text-row"><div>
    <p lang="${escapeHtml(language.code)}">${escapeHtml(text)}</p><p class="muted">${label}</p>
    </div>${aloud ? speaker(text) : ""}</div>`;
  return `<div class="feedback ${session.result}" id="feedback" tabindex="-1">
    <h3>${heading}</h3><p>${description}</p>
    ${session.answer ? `<p>Your answer: <span lang="${escapeHtml(language.code)}">${escapeHtml(session.answer)}</span></p>` : ""}
    ${answerRow(item.answer, "Suggested answer")}
    ${item.alternatives.map((answer) => answerRow(answer, "Also accepted")).join("")}
  </div>
  <div class="rating-group"><p><strong>How well did you remember it?</strong></p><div class="actions">
    ${["again", "hard", "got-it"].map((rating, i) => `<button class="button ${rating === suggested ? "primary" : ""}"
      type="button" data-action="rate" data-rating="${rating}" ${shortcutAttribute(rating[0])}
      ${session.busy ? "disabled" : ""}><span>${shortcutLabel(labels[i], rating[0])}</span></button>`).join("")}
    <button class="button" type="button" data-action="retire" ${session.busy ? "disabled" : ""}>Disable this card</button>
    </div><small>${session.practice ? "Practice ratings stay in this session." : "Confident recall increases the time until the next review."}</small>
  </div>`;
}

function render() {
  renderNav();
  if (state.screen === "deck") {
    view.innerHTML = deckPage();
    renderCardGrid();
  } else if (state.screen === "decks") {
    view.innerHTML = decksPage();
  } else if (state.screen === "card") {
    view.innerHTML = detailPage();
  } else {
    view.innerHTML = sessionPage(state.screen);
  }
}

function route() {
  const [path, query] = location.hash.slice(1).split("?", 2);
  const [mode, id] = path.split("/");
  const topic = new URLSearchParams(query).get("topic") || "";
  if (mode === "main") return;
  state.screen = ["decks", "card", "study", "test"].includes(mode) ? mode : "deck";
  state.detail = id || null;
  if (state.screen === "deck") {
    const library = id || "reading";
    if (state.library !== library) Object.assign(state, {library, query: "", kind: ""});
    state.topic = topic;
    if (deckById(library)?.published === 0) state.saveDeck = library;
  }
  state.session = ["study", "test"].includes(state.screen)
    ? makeSession(state.screen, id, false, state.screen === "study" ? topic : "") : null;
  stopAudio();
  render();
  $("#main").focus();
}

function composerFocus() {
  $("#capture")?.focus();
}

async function makeDraft(refine) {
  if (state.draftBusy || state.saving) return;
  const request = (refine ? state.revision : state.composer).trim();
  if (!request) {
    state.draftError = "Enter a word, phrase or request first.";
    render();
    $(refine ? "#revision" : "#capture")?.focus();
    return;
  }
  state.draftBusy = true;
  state.draftError = "";
  render();
  let made = false;
  try {
    const result = await api("draft", {request, previous: refine ? state.draft.card : undefined});
    state.draft = {...result, request};
    state.revision = "";
    made = true;
  } catch (error) {
    state.draftError = error.message;
    toast(error.message);
  } finally {
    state.draftBusy = false;
    render();
    if (made) $("#draft")?.focus();
    else $(refine ? "#revision" : "#capture")?.focus();
  }
}

async function saveDraft() {
  if (state.saving || state.draftBusy || !state.draft) return;
  state.saving = true;
  state.draftError = "";
  render();
  try {
    const card = await api("cards", {id: state.draft.id, card: state.draft.card, deck_id: state.saveDeck});
    state.cards = [card, ...state.cards.filter((old) => old.id !== card.id)];
    state.composer = "";
    state.revision = "";
    state.draft = null;
    state.query = "";
    state.kind = "";
    location.hash = `card/${card.id}`;
    toast(`Saved to ${deckById(card.deck_id).name}.`);
  } catch (error) {
    state.draftError = error.message;
  } finally {
    state.saving = false;
    render();
  }
}

function stopAudio() {
  audioVersion += 1;
  if (audioPlayer) {
    audioPlayer.pause();
    audioPlayer.remove();
  }
  if (audioUrl) URL.revokeObjectURL(audioUrl);
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  if (audioButton) {
    audioButton.removeAttribute("aria-busy");
    if (audioButton.dataset.action === "listen") {
      audioButton.innerHTML = icon("audio");
      audioButton.setAttribute("aria-label", "Listen in French");
    }
  }
  audioButton = audioPlayer = audioUrl = null;
}

function browserSpeak(text, version) {
  if (!("speechSynthesis" in window)) return false;
  const voice = window.speechSynthesis.getVoices().find((candidate) =>
    candidate.localService && /^fr([-_]|$)/i.test(candidate.lang));
  if (!voice) return false;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = voice.lang;
  utterance.voice = voice;
  utterance.rate = 0.88;
  utterance.onend = () => { if (version === audioVersion) stopAudio(); };
  utterance.onerror = () => {
    if (version === audioVersion) {
      stopAudio();
      toast("Couldn’t play the French voice.");
    }
  };
  window.speechSynthesis.speak(utterance);
  return true;
}

async function listen(text, button) {
  if (audioButton === button) {
    stopAudio();
    return;
  }
  stopAudio();
  const version = audioVersion;
  audioButton = button;
  button.setAttribute("aria-busy", "true");
  if (button.dataset.action === "listen") {
    button.innerHTML = icon("stop");
    button.setAttribute("aria-label", "Stop French audio");
  }
  try {
    const blob = await api("audio", {text}, true);
    if (version !== audioVersion) return;
    audioUrl = URL.createObjectURL(blob);
    audioPlayer = new Audio(audioUrl);
    audioPlayer.addEventListener("ended", () => { if (version === audioVersion) stopAudio(); });
    await audioPlayer.play();
  } catch (error) {
    if (version !== audioVersion) return;
    if (error.name === "NotAllowedError" && audioPlayer) {
      audioPlayer.controls = true;
      audioPlayer.className = "manual-audio";
      audioPlayer.setAttribute("aria-label", "Play French audio");
      (button.closest("dialog") || document.body).append(audioPlayer);
      audioPlayer.focus();
      return;
    }
    if (!browserSpeak(text, version)) {
      stopAudio();
      toast("Couldn’t play French audio. Check the Mac voice or your browser’s sound settings.");
    }
  }
}

function moveSession(delta) {
  stopAudio();
  Object.assign(state.session, {position: state.session.position + delta,
    revealed: false, answer: "", result: null, error: ""});
  state.session.visited = Math.max(state.session.visited, state.session.position + 1);
  render();
  const nextControl = $("#answer-text") || view.querySelector('[data-action="reveal"]');
  nextControl?.focus({preventScroll: state.screen === "study"});
}

function checkAnswer(showOnly = false) {
  const session = state.session;
  const side = promptDirection(session);
  const card = cardById(session.ids[session.position]);
  const item = exercise(card, side);
  const language = studyLanguages[side === "target" ? "reference" : "target"];
  const text = session.answer.trim();
  const choices = [item.answer, ...item.alternatives, ...(item.accepted ?? [])];
  const article = side === "target" && card.kind === "Word" && studyLanguages.target.nounArticle?.test(card.title)
    ? language.optionalArticle : null;
  const matches = (choice, accents) => {
    const actual = normalize(text, accents, language.code);
    const expected = normalize(choice, accents, language.code);
    if (actual === expected) return true;
    return Boolean(article && article.test(actual) !== article.test(expected) &&
      actual.replace(article, "") === expected.replace(article, ""));
  };
  if (showOnly && !text) session.result = "skipped";
  else if (choices.some((choice) => matches(choice, true))) session.result = "match";
  else if (choices.some((choice) => matches(choice, false))) session.result = "close";
  else session.result = "other";
  render();
  $("#feedback").focus();
}

async function rate(rating) {
  const session = state.session;
  if (session.busy) return;
  const card = cardById(session.ids[session.position]);
  session.busy = true;
  session.error = "";
  render();
  try {
    if (!session.practice) {
      const updated = await api("review", {id: card.id, rating, reviews: card.reviews});
      state.cards = state.cards.map((item) => item.id === card.id ? updated : item);
    }
    session.ratings.push(rating);
    if (session === state.session) moveSession(1);
    else render();
  } catch (error) {
    session.error = error.message;
    if (error.status === 409 || error.status === 404) {
      await loadCards();
      if (session === state.session) state.session = makeSession("test", null, session.practice);
      toast(error.message);
    }
    render();
  } finally {
    session.busy = false;
    if (session === state.session) {
      render();
      $("#answer-text")?.focus();
    }
  }
}

function insertAccent(character) {
  const input = $("#answer-text");
  const start = input.selectionStart;
  const end = input.selectionEnd;
  if (input.value.length - (end - start) >= input.maxLength) return;
  input.setRangeText(character, start, end, "end");
  state.session.answer = input.value;
  input.focus();
}

view.addEventListener("input", (event) => {
  const value = event.target.value;
  switch (event.target.id) {
    case "capture": state.composer = value; break;
    case "revision": state.revision = value; break;
    case "answer-text": state.session.answer = value; break;
    case "search": state.query = value; renderCardGrid(); break;
  }
});

async function changeTraining(item, card, button) {
  button.disabled = true;
  try {
    const {enabled} = await api(card ? "card-training" : "deck-training", {id: item.id, enabled: !item.enabled});
    item.enabled = enabled;
    return true;
  } catch (error) {
    toast(error.message);
    button.disabled = false;
    return false;
  }
}

function changeStudyOption(input) {
  const session = state.session;
  const key = input.name;
  if (session.busy) return;
  const other = key === "reference" ? "target" : "reference";
  if (directions.includes(key) && !input.checked && !studyOptions[other]) {
    input.checked = true;
    toast("Choose at least one prompt language.");
    return;
  }
  const hasCard = Boolean(session.ids[session.position]);
  const current = hasCard ? promptDirection(session) : null;
  studyOptions[key] = input.checked;
  localStorage.setItem("study-options", JSON.stringify(studyOptions));
  if (key === "shuffle") {
    const seen = session.ids.slice(0, session.visited);
    const seenIds = new Set(seen);
    const remaining = session.ordered.filter((id) => !seenIds.has(id));
    session.ids = [...seen, ...(studyOptions.shuffle ? shuffled(remaining) : remaining)];
  } else if (hasCard && promptDirection(session) !== current) {
    stopAudio();
    Object.assign(session, {revealed: false, answer: "", result: null, error: ""});
  }
  render();
  $(`#training-options input[name="${key}"]`)?.focus();
}

view.addEventListener("change", (event) => {
  if (event.target.closest("#training-options")) changeStudyOption(event.target);
  if (event.target.id === "library") location.hash = `deck/${event.target.value}`;
  if (event.target.id === "save-deck") state.saveDeck = event.target.value;
  if (event.target.id === "topic") {
    state.topic = event.target.value;
    renderCardGrid();
  }
  if (event.target.id === "kind") {
    state.kind = event.target.value;
    renderCardGrid();
  }
});

document.addEventListener("submit", async (event) => {
  event.preventDefault();
  switch (event.target.id) {
    case "composer": await makeDraft(false); break;
    case "refine": await makeDraft(true); break;
    case "answer":
      state.session.answer = $("#answer-text").value;
      if (state.session.answer.trim()) checkAnswer();
      break;
    case "pronunciation-form":
      if ($("#say-text").value.trim()) listen($("#say-text").value.trim(), event.submitter || event.target.querySelector('[type="submit"]'));
      break;
    case "create-deck": {
      const button = event.submitter || event.target.querySelector("button");
      button.disabled = true;
      try {
        const deck = await api("decks", {name: $("#deck-name").value});
        state.decks.push(deck);
        state.saveDeck = deck.id;
        location.hash = `deck/${deck.id}`;
        toast("Local deck created.");
      } catch (error) {
        toast(error.message);
      } finally {
        button.disabled = false;
      }
      break;
    }
    case "remove-form": {
      const button = event.submitter || event.target.querySelector('[type="submit"]');
      button.disabled = true;
      try {
        await api("delete", {id: deleteId});
        const deckId = cardById(deleteId).deck_id;
        state.cards = state.cards.filter((card) => card.id !== deleteId);
        $("#remove-card").close();
        location.hash = `deck/${deckId}`;
        toast("Card deleted.");
      } catch (error) {
        toast(error.message);
      } finally {
        button.disabled = false;
      }
      break;
    }
  }
});

document.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  switch (button.dataset.action) {
    case "focus-composer": composerFocus(); break;
    case "sample":
      state.composer = samples[button.dataset.sample];
      $("#capture").value = state.composer;
      composerFocus();
      break;
    case "open-card": location.hash = `card/${button.dataset.id}`; break;
    case "discard":
      state.draft = null; state.draftError = ""; state.revision = ""; render(); composerFocus(); break;
    case "save": await saveDraft(); break;
    case "listen": await listen(button.dataset.text, button); break;
    case "toggle-deck":
      if (await changeTraining(deckById(button.dataset.id), false, button)) {
        render();
        view.querySelector(`[data-action="toggle-deck"][data-id="${button.dataset.id}"]`)?.focus();
      }
      break;
    case "toggle-card":
      if (await changeTraining(cardById(button.dataset.id), true, button)) {
        render();
        view.querySelector('[data-action="toggle-card"]')?.focus();
      }
      break;
    case "retire": {
      const session = state.session;
      if (session.busy) break;
      session.busy = true;
      const card = cardById(session.ids[session.position]);
      if (await changeTraining(card, true, button)) {
        session.busy = false;
        if (state.session === session) moveSession(1);
        else render();
        toast("Card disabled. You can enable it again from its card page.");
      } else {
        session.busy = false;
      }
      break;
    }
    case "delete":
      deleteId = button.dataset.id;
      $("#remove-copy").textContent = `“${cardById(deleteId).title}” and its review progress will be removed.`;
      $("#remove-card").showModal();
      break;
    case "close-dialog": button.closest("dialog").close(); break;
    case "reveal": state.session.revealed = true; render(); $("#revealed").focus({preventScroll: true}); break;
    case "hide": state.session.revealed = false; stopAudio(); render(); view.querySelector('[data-action="reveal"]').focus(); break;
    case "next": moveSession(1); break;
    case "previous": moveSession(-1); break;
    case "show-answer": checkAnswer(true); break;
    case "rate": await rate(button.dataset.rating); break;
    case "accent": insertAccent(button.dataset.char); break;
    case "all-test":
    case "due-test":
    case "restart":
      stopAudio();
      state.session = makeSession(state.screen, state.detail,
        button.dataset.action === "all-test" || (button.dataset.action === "restart" && state.session.practice),
        state.session.topic);
      render();
      $("#answer-text")?.focus();
      break;
    case "refresh": await loadCards(); route(); break;
  }
});

document.addEventListener("keydown", (event) => {
  if (!state.session || state.session.busy || event.defaultPrevented ||
      event.repeat || event.isComposing || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
      event.target.isContentEditable ||
      event.target.closest?.("input:not([type=checkbox]):not([type=radio]), textarea, select") || $("dialog[open]")) return;
  const key = event.key.toLowerCase();
  let button;
  if ((key === " " || key === "enter") && !event.target.closest?.("button, a, input, summary")) {
    button = view.querySelector('.rating-group button[data-action="rate"].primary:not(:disabled)');
  } else if (studyOptions.shortcuts && /^[a-z]$/u.test(key)) {
    button = view.querySelector(`button[aria-keyshortcuts="${key}"]:not(:disabled)`);
  }
  if (!button) return;
  event.preventDefault();
  button.click();
});

$("#theme").addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", theme);
  applyTheme(theme);
});

const pronounceButton = $("#pronounce");
pronounceButton.innerHTML = `${icon("audio")}<span>Pronounce text</span>`;
pronounceButton.setAttribute("aria-label", "Pronounce text");
pronounceButton.addEventListener("pointerdown", () => { selectedFrench = window.getSelection().toString().trim(); });
pronounceButton.addEventListener("click", () => {
  if (selectedFrench) $("#say-text").value = selectedFrench.slice(0, 1200);
  selectedFrench = "";
  $("#pronunciation").showModal();
});
$("#pronunciation").addEventListener("close", stopAudio);
window.addEventListener("hashchange", route);

applyTheme(localStorage.getItem("theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
route();
loadCards().then(() => {
  if (state.screen === "study" || state.screen === "test") route();
  else {
    if (state.screen === "deck" && deckById(state.library)?.published === 0) state.saveDeck = state.library;
    render();
  }
});
setInterval(() => {
  if (state.screen === "deck" && document.activeElement === document.body) render();
  else if (!$("#nav").contains(document.activeElement)) renderNav();
}, 60_000);
