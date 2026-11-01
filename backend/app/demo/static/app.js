"use strict";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const geld = (v, w = "EUR") => v == null || v === "" ? "–" : Number(v).toLocaleString("de-DE", { style: "currency", currency: w || "EUR" });
const datum = (iso) => iso && /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso.split("-").reverse().join(".") : (iso || "–");
const prozent = (x) => `${Math.round((x || 0) * 100)} %`;
const anzahl = (n, eins, mehr) => `${n} ${n === 1 ? eins : mehr}`;
const AMPEL = { gruen: "Sicher", gelb: "Unsicher", rot: "Frei" };
const MONATE = ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."];
const HERKUNFT = { inland: "Inland", eu: "EU-Ausland", drittland: "Drittland" };
const BEREICH_TEXT = {
  sicher: (n, s) => `<b>${anzahl(n, "Rechnung", "Rechnungen")}</b> sicher vorkontiert · ${geld(s)}`,
  pruefen: (n, s) => `<b>${anzahl(n, "Rechnung", "Rechnungen")}</b> zur Prüfung · ${geld(s)}`,
  erledigt: (n) => `<b>${anzahl(n, "Rechnung", "Rechnungen")}</b> freigegeben`,
};

/* Symbole (Linien, weiß auf farbigem Quadrat wie in den iOS-Einstellungen) */
const PFADE = {
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  liste: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
  buchung: '<path d="M4 8h15l-4-4M20 16H5l4 4"/>',
  beleg: '<path d="M6 2h8l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/><path d="M14 2v5h5M8 13h8M8 17h5"/>',
  hoch: '<path d="M6 15l6-6 6 6"/>',
  runter: '<path d="M6 9l6 6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  passend: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
};
const svg = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${PFADE[name] || ""}</svg>`;
const setzeSymbole = (wurzel = document) => wurzel.querySelectorAll("[data-ikon]").forEach((el) => { el.innerHTML = svg(el.dataset.ikon); });

const zustand = {
  nutzer: "AK", stamm: null, seite: null, filter: "sicher", mandant: null, suche: "", modell: "",
  key: null, beleg: null, liste: null, uebersicht: null, ersterBlick: true, timer: null, sbGewaehlt: null,
};

/* ---------- Hilfen ---------- */
function monatText(ym) {
  if (!ym) return "–";
  const [j, m] = ym.split("-").map(Number);
  return `${MONATE[m - 1]} ${j}`;
}

function monateText(liste) {
  if (!liste || !liste.length) return "–";
  if (liste.length === 1) return monatText(liste[0]);
  const [a, b] = [liste[0], liste[liste.length - 1]];
  return a.slice(0, 4) === b.slice(0, 4)
    ? `${MONATE[Number(a.slice(5)) - 1]}–${monatText(b)}` : `${monatText(a)} – ${monatText(b)}`;
}

/* Leistungsdatum: ganzer Monat → „Okt. 2026“, Zeitraum → „01.10.–15.10.2026“, sonst Datum */
function leistungText(l, lang = false) {
  if (!l || !l.von) return "fehlt";
  if (l.art === "wie_rechnung") return `${datum(l.von)} (wie Rechnungsdatum)`;
  if (!l.bis) return datum(l.von);
  const [vj, vm, vt] = l.von.split("-");
  const [bj, bm, bt] = l.bis.split("-");
  const letzter = new Date(Number(bj), Number(bm), 0).getDate();
  if (!lang && vj === bj && vm === bm && vt === "01" && Number(bt) === letzter) return monatText(`${vj}-${vm}`);
  return vj === bj ? `${vt}.${vm}.–${bt}.${bm}.${bj}` : `${datum(l.von)} – ${datum(l.bis)}`;
}

async function api(url, opts = {}) {
  const r = await fetch(url, { ...opts, headers: { ...(opts.headers || {}), "X-Nutzer": zustand.nutzer } });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.detail || `Fehler ${r.status}`);
  return d;
}
const post = (url, body) => api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

function toast(text, fehler = false) {
  const t = $("toast");
  t.textContent = text;
  t.className = "toast" + (fehler ? " fehler" : "");
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { t.hidden = true; }, 2800);
}

function merke(name, wert) { try { localStorage.setItem(name, wert); } catch { /* ohne Speicher weiter */ } }
function lies(name) { try { return localStorage.getItem(name); } catch { return null; } }

/* ---------- Start ---------- */
async function init() {
  zustand.nutzer = lies("nutzer") || "AK";
  setzeSymbole();
  await ladeStamm();

  $("nutzer").addEventListener("change", async (e) => {
    zustand.nutzer = e.target.value; merke("nutzer", zustand.nutzer);
    await ladeStamm();
    toast(`Angemeldet als ${zustand.stamm.nutzer.name}`);
    route();
  });
  document.querySelectorAll(".segment.drei button").forEach((b) => b.addEventListener("click", () => setzeFilter(b.dataset.filter)));
  $("mandant").addEventListener("change", (e) => { location.hash = `#/belege/${e.target.value}`; });
  $("suche").addEventListener("input", (e) => { zustand.suche = e.target.value.toLowerCase(); zeigeListe(); });
  $("ue-suche").addEventListener("input", zeigeUebersicht);
  $("modell").addEventListener("change", async (e) => {
    zustand.modell = e.target.value;
    await ladeListe();
    if (zustand.key) oeffne(zustand.key, false);
  });
  $("datei").addEventListener("change", hochladen);
  $("a-knopf").addEventListener("click", aktion);
  $("sammel-knopf").addEventListener("click", oeffneSammelfreigabe);
  $("blatt-abbrechen").addEventListener("click", () => { $("blatt-hintergrund").hidden = true; });
  $("blatt-ok").addEventListener("click", sammelfreigabe);
  $("b-verlauf").addEventListener("click", () => { $("verlauf-blatt").hidden = false; });
  $("demo-knopf").addEventListener("click", (e) => { e.stopPropagation(); $("demo-liste").hidden = !$("demo-liste").hidden; });
  document.querySelectorAll("#demo-liste button").forEach((b) => b.addEventListener("click", () => demoAktion(b.dataset.demo)));
  document.querySelectorAll("[data-schliessen]").forEach((b) => b.addEventListener("click", () => { $(b.dataset.schliessen).hidden = true; }));
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".konto-feld, .dropdown")) schliesseDropdown();
    if (!e.target.closest(".demo-menue")) $("demo-liste").hidden = true;
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") document.querySelectorAll(".blatt-hintergrund").forEach((b) => { b.hidden = true; });
  });
  $("ue-neu").addEventListener("click", () => oeffneMandant(null));
  $("ue-rechte").addEventListener("click", oeffneRechte);
  $("mandant-form").addEventListener("submit", sichereMandant);
  document.querySelectorAll("#f-kontenrahmen button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#f-kontenrahmen button").forEach((x) => x.classList.toggle("aktiv", x === b));
  }));
  $("sb-form").addEventListener("submit", sichereSachbearbeiter);
  $("rechte-suche").addEventListener("input", zeigeRechte);
  bindeWerkzeuge();
  window.addEventListener("hashchange", route);
  route();
}

async function ladeStamm() {
  zustand.stamm = await api("/api/stammdaten");
  const s = zustand.stamm;
  if (!s.nutzer) { zustand.nutzer = s.sachbearbeiter[0].kuerzel; merke("nutzer", zustand.nutzer); return ladeStamm(); }
  zustand.modell = zustand.modell || s.standard_modell;
  $("nutzer").innerHTML = s.sachbearbeiter.map((p) => `<option value="${esc(p.kuerzel)}" ${p.kuerzel === zustand.nutzer ? "selected" : ""}>
    ${esc(p.name)} · ${esc(s.rollen[p.rolle])}</option>`).join("");
  $("nutzer-avatar").textContent = s.nutzer.kuerzel;
  $("modell").innerHTML = s.modelle.map((m) => `<option value="${m.id}" ${m.id === zustand.modell ? "selected" : ""}>${esc(m.kurz)}</option>`).join("");
  $("mandant").innerHTML = s.mandanten.map((m) => `<option value="${esc(m.id)}">${esc(m.name)}</option>`).join("");
  $("ue-aktionen").hidden = !s.leitung;
}

function route() {
  clearTimeout(zustand.timer);
  const m = location.hash.match(/^#\/belege(?:\/(\w+))?/);
  if (m) {
    const ziel = m[1] || lies("mandant") || zustand.stamm.mandanten[0]?.id;
    if (!zustand.stamm.mandanten.some((x) => x.id === ziel)) {
      if (m[1]) toast("Kein Zugriff auf diesen Mandanten", true);
      location.hash = "#/uebersicht";
      return;
    }
    if (!m[1]) { location.hash = `#/belege/${ziel}`; return; }
    return zeigeSeite("belege", ziel);
  }
  zeigeSeite("uebersicht");
}

function zeigeSeite(seite, mandant) {
  zustand.seite = seite;
  $("seite-uebersicht").hidden = seite !== "uebersicht";
  $("seite-belege").hidden = seite !== "belege";
  document.querySelectorAll(".hauptnav a").forEach((a) => a.classList.toggle("aktiv", a.dataset.nav === seite));
  document.title = seite === "uebersicht" ? "Belegautomatik – Übersicht" : "Belegautomatik – Belegverarbeitung";
  if (seite === "uebersicht") return ladeUebersicht();
  if (mandant !== zustand.mandant) {
    zustand.mandant = mandant; merke("mandant", mandant);
    zustand.key = null; zustand.ersterBlick = true;
    $("beleg").hidden = true; $("aktionsleiste").hidden = true; $("leer").hidden = false;
    leereVorschau();
  }
  $("mandant").value = mandant;
  zeigeMandantKopf();
  ladeListe();
}

/* ---------- Übersicht (Dashboard) ---------- */
async function ladeUebersicht() {
  try {
    zustand.uebersicht = await api(`/api/uebersicht?${new URLSearchParams({ modell: zustand.modell })}`);
  } catch (e) { return toast(e.message, true); }
  zeigeUebersicht();
  if (!zustand.uebersicht.bereit && zustand.seite === "uebersicht") zustand.timer = setTimeout(ladeUebersicht, 2500);
}

function team(personen) {
  return personen.map((p) => `<span class="kuerzel ${p.rolle === "Vertretung" ? "vertretung" : ""}"
    data-name="${esc(p.name)} · ${esc(p.rolle)}">${esc(p.kuerzel)}</span>`).join("") || `<span class="klein">–</span>`;
}

function zeigeUebersicht() {
  const u = zustand.uebersicht;
  if (!u) return;
  const s = zustand.stamm;
  const stunde = new Date().getHours();
  $("ue-gruss").textContent = `${stunde < 11 ? "Guten Morgen" : stunde < 18 ? "Guten Tag" : "Guten Abend"}, ${s.nutzer.name} · `
    + (s.leitung ? "Kanzleileitung: Sie sehen alle Mandanten" : `${anzahl(u.mandanten.length, "Mandant", "Mandanten")} zugeordnet`);
  $("k-offen").textContent = u.summe.offen;
  $("k-sicher").textContent = u.summe.sicher;
  $("k-pruefen").textContent = u.summe.pruefen;
  $("k-mandanten").textContent = u.mandanten.length;
  $("k-mandanten-text").textContent = s.leitung ? "Mandanten" : "Meine Mandanten";
  $("ue-titel").textContent = s.leitung ? "Alle Mandanten" : "Meine Mandanten";
  const q = $("ue-suche").value.trim().toLowerCase();
  const zeilen = u.mandanten.filter((m) => !q || `${m.name} ${m.nummer} ${m.ansprechpartner}`.toLowerCase().includes(q));
  $("ue-tabelle").innerHTML = zeilen.map((m) => `
    <div class="ue-zeile" data-mandant="${esc(m.id)}" tabindex="0">
      <span class="m-avatar">${esc(m.name.replace(/[^A-Za-zÄÖÜäöü ]/g, "").split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase())}</span>
      <span class="m-name"><b>${esc(m.name)}</b><small>${esc(m.ansprechpartner || "Kein Ansprechpartner")}</small></span>
      <span class="m-nr">${esc(m.nummer)}</span>
      <span><span class="marke">${esc(m.kontenrahmen)}</span></span>
      <span class="m-team">${team(m.team)}</span>
      <span class="m-offen">${m.lesen ? `<span class="klein">wird gelesen …</span>` : m.offen
        ? `<b class="offen-zahl">${m.offen}</b><small>${m.sicher} sicher · ${m.pruefen} prüfen</small>`
        : `<span class="erledigt-haken">✓ erledigt</span>`}</span>
      <span class="m-monat">${m.offen ? esc(monateText(m.monate)) : "–"}</span>
      <span class="m-aktion">${s.leitung ? `<button class="link blau-link" data-bearbeiten="${esc(m.id)}">Bearbeiten</button>` : ""}<span class="chevron">›</span></span>
    </div>`).join("") || `<p class="klein mitte">Keine Mandanten${q ? " zu dieser Suche" : " zugeordnet"}.</p>`;
  $("ue-tabelle").querySelectorAll(".ue-zeile").forEach((z) => {
    const oeffnen = () => { location.hash = `#/belege/${z.dataset.mandant}`; };
    z.addEventListener("click", (e) => { if (!e.target.closest("[data-bearbeiten]")) oeffnen(); });
    z.addEventListener("keydown", (e) => { if (e.key === "Enter") oeffnen(); });
  });
  $("ue-tabelle").querySelectorAll("[data-bearbeiten]").forEach((b) => b.addEventListener("click", () => oeffneMandant(b.dataset.bearbeiten)));
}

/* ---------- Mandant erfassen und bearbeiten ---------- */
function oeffneMandant(id) {
  const s = zustand.stamm;
  const m = id ? s.alle_mandanten.find((x) => x.id === id) : null;
  const f = $("mandant-form");
  f.reset();
  f.dataset.id = id || "";
  $("mandant-titel").textContent = m ? "Mandant bearbeiten" : "Neuer Mandant";
  f.name.value = m?.name || "";
  f.nummer.value = m?.nummer || naechsteNummer();
  f.ansprechpartner.value = m?.ansprechpartner || "";
  const rahmen = m?.kontenrahmen || "SKR03";
  document.querySelectorAll("#f-kontenrahmen button").forEach((b) => b.classList.toggle("aktiv", b.dataset.wert === rahmen));
  const option = (p, gewaehlt) => {
    const gesperrt = id && p.zugriff[id] === "gesperrt";
    return `<option value="${esc(p.kuerzel)}" ${gewaehlt === p.kuerzel ? "selected" : ""} ${gesperrt ? "disabled" : ""}>
      ${esc(p.kuerzel)} · ${esc(p.name)}${gesperrt ? " (gesperrt)" : ""}</option>`;
  };
  f.zustaendig.innerHTML = `<option value="">Bitte wählen</option>` + s.sachbearbeiter.map((p) => option(p, m?.zustaendig)).join("");
  f.vertretung.innerHTML = `<option value="">Keine Vertretung</option>` + s.sachbearbeiter.map((p) => option(p, m?.vertretung)).join("");
  $("mandant-fehler").hidden = true;
  $("mandant-blatt").hidden = false;
  f.name.focus();
}

function naechsteNummer() {
  const vergeben = new Set(zustand.stamm.alle_mandanten.map((m) => Number(m.nummer)));
  let n = 10001;
  while (vergeben.has(n)) n++;
  return n;
}

async function sichereMandant(e) {
  e.preventDefault();
  const f = e.target;
  const daten = {
    id: f.dataset.id || null, name: f.name.value, nummer: f.nummer.value, ansprechpartner: f.ansprechpartner.value,
    kontenrahmen: document.querySelector("#f-kontenrahmen .aktiv").dataset.wert,
    zustaendig: f.zustaendig.value || null, vertretung: f.vertretung.value || null,
  };
  try {
    await post("/api/kanzlei/mandant", daten);
    $("mandant-blatt").hidden = true;
    toast(daten.id ? "Mandant gesichert" : `Mandant ${daten.nummer} angelegt`);
    await ladeStamm();
    ladeUebersicht();
  } catch (err) {
    $("mandant-fehler").textContent = err.message;
    $("mandant-fehler").hidden = false;
  }
}

/* ---------- Sachbearbeiter und Rechte ---------- */
function oeffneRechte() {
  zustand.sbGewaehlt = zustand.sbGewaehlt || zustand.stamm.sachbearbeiter.find((p) => p.rolle !== "leitung")?.kuerzel;
  $("rechte-suche").value = "";
  zeigeRechte();
  $("rechte-blatt").hidden = false;
}

function zeigeRechte() {
  const s = zustand.stamm;
  const sbs = s.sachbearbeiter;
  if (!sbs.some((p) => p.kuerzel === zustand.sbGewaehlt)) zustand.sbGewaehlt = sbs[0].kuerzel;
  $("sb-liste").innerHTML = sbs.map((p) => {
    const n = Object.values(p.zugriff).filter((w) => w === "an").length;
    return `<li class="${p.kuerzel === zustand.sbGewaehlt ? "gewaehlt" : ""}" data-sb="${esc(p.kuerzel)}">
      <span class="avatar">${esc(p.kuerzel)}</span>
      <span><b>${esc(p.name)}</b><small>${esc(s.rollen[p.rolle])} · ${p.rolle === "leitung" ? "alle Mandanten" : anzahl(n, "Mandant", "Mandanten")}</small></span>
    </li>`;
  }).join("");
  $("sb-liste").querySelectorAll("li").forEach((li) => li.addEventListener("click", () => { zustand.sbGewaehlt = li.dataset.sb; zeigeRechte(); }));

  const p = sbs.find((x) => x.kuerzel === zustand.sbGewaehlt);
  $("rechte-kopf").innerHTML = `<div><b>${esc(p.name)}</b> <span class="klein">${esc(p.kuerzel)} · ${esc(s.rollen[p.rolle])}</span></div>
    <p class="klein">${p.rolle === "leitung" ? "Die Kanzleileitung sieht alle Mandanten. Die Einstellungen unten gelten, falls die Rolle geändert wird."
      : "Zugriff: sieht und bearbeitet den Mandanten. Gesperrt: darf diesem Mandanten nie zugeordnet werden (z. B. Interessenkonflikt)."}</p>`;
  const q = $("rechte-suche").value.trim().toLowerCase();
  const treffer = s.alle_mandanten.filter((m) => !q || m.name.toLowerCase().includes(q) || String(m.nummer).includes(q));
  $("rechte-liste").innerHTML = treffer.map((m) => {
    const wert = p.zugriff[m.id] || "aus";
    const rolle = m.zustaendig === p.kuerzel ? "zuständig" : m.vertretung === p.kuerzel ? "Vertretung" : null;
    const knopf = (w, text) => `<button data-wert="${w}" class="${wert === w ? "aktiv " + w : ""}" ${rolle && w !== "an" ? "disabled" : ""}>${text}</button>`;
    return `<li data-mandant="${esc(m.id)}">
      <span><b>${esc(m.name)}</b><small>${esc(m.nummer)} · ${esc(m.kontenrahmen)}${rolle ? ` · <span class="rolle-marke">${rolle}</span>` : ""}</small></span>
      <div class="segment klein-segment">${knopf("an", "Zugriff")}${knopf("aus", "Kein Zugriff")}${knopf("gesperrt", "Gesperrt")}</div>
    </li>`;
  }).join("") || `<li><span class="klein">Kein Mandant zu „${esc(q)}“</span></li>`;
  $("rechte-liste").querySelectorAll("li").forEach((li) => li.querySelectorAll("button").forEach((b) => b.addEventListener("click", async () => {
    try {
      zustand.stamm = { ...zustand.stamm, ...(await post("/api/kanzlei/zugriff", { kuerzel: p.kuerzel, mandant: li.dataset.mandant, wert: b.dataset.wert })) };
      zeigeRechte();
    } catch (e) { toast(e.message, true); }
  })));
}

async function sichereSachbearbeiter(e) {
  e.preventDefault();
  const f = e.target;
  try {
    zustand.stamm = { ...zustand.stamm, ...(await post("/api/kanzlei/sachbearbeiter", { kuerzel: f.kuerzel.value, name: f.name.value, rolle: f.rolle.value })) };
    zustand.sbGewaehlt = f.kuerzel.value.trim().toUpperCase();
    toast(`${f.name.value} angelegt – jetzt Mandanten zuordnen`);
    f.reset();
    await ladeStamm();
    zeigeRechte();
  } catch (err) { toast(err.message, true); }
}

/* ---------- Belegverarbeitung: Liste ---------- */
function zeigeMandantKopf() {
  const m = zustand.stamm.mandanten.find((x) => x.id === zustand.mandant);
  if (!m) return;
  $("mandant-info").innerHTML = `Mandant ${esc(m.nummer)} · ${esc(m.kontenrahmen)} · ${team(m.team)}`;
  const h = $("mandant-hinweis");
  h.hidden = m.kontenrahmen !== "SKR04";
  h.textContent = "SKR04 ist in der Demo noch nicht hinterlegt – Kontovorschläge kommen aus dem SKR03.";
}

function setzeFilter(f) {
  zustand.filter = f;
  document.querySelectorAll(".segment.drei button").forEach((x) => x.classList.toggle("aktiv", x.dataset.filter === f));
  zeigeListe();
}

async function ladeListe() {
  clearTimeout(zustand.timer);
  const mandant = zustand.mandant;
  try {
    const l = await api("/api/eingang?" + new URLSearchParams({ modell: zustand.modell, mandant }));
    if (mandant !== zustand.mandant) return;
    zustand.liste = l;
  } catch (e) { return toast(e.message, true); }
  if (zustand.ersterBlick && zustand.liste.bereit) {
    zustand.ersterBlick = false;
    if (!zustand.liste.anzahl.sicher) setzeFilter(zustand.liste.anzahl.pruefen ? "pruefen" : "erledigt");
  }
  zeigeListe();
  if (!zustand.liste.bereit && zustand.seite === "belege") zustand.timer = setTimeout(ladeListe, 2000);
}

function zelle(e) {
  if (!e.bereit) return `<li class="zelle"><span class="punkt grau"></span><span class="z1">${esc(e.id)} wird gelesen …</span><span></span>
    <span class="z2">${esc(e.mandant)}</span></li>`;
  const art = { xml: "E-Rechnung", scan: "Scan", foto: "Foto", pdf: "PDF" }[e.art] || e.art;
  const marken = [];
  if (e.bereich === "sicher") marken.push(`<span class="marke gruen">Sicher ${prozent(e.sicherheit)}</span>`);
  for (const a of e.ausnahmen || []) marken.push(`<span class="marke orange">${esc(a.split(" (")[0].split(" – ")[0])}</span>`);
  if (e.gelernt) marken.push(`<span class="marke blau">${e.gelernt}/${e.positionen} gelernt</span>`);
  if (e.frei) marken.push(`<span class="marke orange">${e.frei} ohne Konto</span>`);
  if (e.kreditor) marken.push(`<span class="marke">Kreditor ${esc(e.kreditor)}</span>`);
  marken.push(`<span class="marke">${art}</span>`);
  return `<li class="zelle ${e.key === zustand.key ? "gewaehlt" : ""}" data-key="${esc(e.key)}">
    <span class="punkt ${e.bereich === "erledigt" ? "grau" : e.ampel}"></span>
    <span class="z1">${esc(e.lieferant || e.id)}</span>
    <span class="z-betrag">${geld(e.brutto, e.waehrung)}</span>
    <span class="z2"><span>Rechnung ${datum(e.datum)} · Leistung ${esc(leistungText(e.leistung))}</span>${marken.join("")}</span>
  </li>`;
}

function zeigeListe() {
  const l = zustand.liste;
  if (!l) return;
  $("z-sicher").textContent = l.anzahl.sicher;
  $("z-pruefen").textContent = l.anzahl.pruefen;
  $("z-erledigt").textContent = l.anzahl.erledigt;
  const f = zustand.filter;
  $("summe").innerHTML = BEREICH_TEXT[f](l.anzahl[f], l.summe[f]) + (l.bereit ? "" : " · <i>werden gelesen …</i>");
  $("sammel").hidden = !(f === "sicher" && l.anzahl.sicher > 0);
  $("sammel-zahl").textContent = `${l.anzahl.sicher} sicher vorkontiert`;
  $("sammel-text").textContent = "Nur ansehen und freigeben";

  const eintraege = l.eintraege.filter((e) => e.bereich === f)
    .filter((e) => !zustand.suche || (e.lieferant || "").toLowerCase().includes(zustand.suche));
  const leer = { sicher: "Keine sicher vorkontierten Rechnungen.", pruefen: "Nichts zu prüfen.", erledigt: "Noch nichts freigegeben." }[f];
  $("liste").innerHTML = eintraege.map(zelle).join("") || `<li class="klein mitte">${leer}</li>`;
  $("liste").querySelectorAll(".zelle[data-key]").forEach((z) => z.addEventListener("click", () => oeffne(z.dataset.key)));
  $("konto-liste").innerHTML = l.nach_konto.map((g) => `<li><b>${esc(g.nr)}</b><span>${esc(g.name)}</span>
    <span class="klein">${g.anzahl}× · ${geld(g.summe)}</span></li>`).join("") || `<li class="klein">Alles verbucht</li>`;
}

/* ---------- Detail ---------- */
async function oeffne(key, neueVorschau = true) {
  try {
    const b = await api(`/api/beleg?${new URLSearchParams({ key, modell: zustand.modell })}`);
    const wechsel = key !== zustand.key;
    zustand.key = key;
    zeigeBeleg(b);
    zeigeListe();
    if (wechsel || neueVorschau) ladeVorschau(b);
  } catch (e) { toast(e.message, true); }
}

function zeigeBeleg(b) {
  zustand.beleg = b;
  $("leer").hidden = true;
  $("beleg").hidden = false;
  $("aktionsleiste").hidden = false;
  const fertig = b.status === "freigegeben";
  const k = b.kopf;
  const w = k.currency || "EUR";
  const chip = $("b-status");
  if (fertig) { chip.className = "status-chip fertig"; chip.innerHTML = "✓ Freigegeben"; }
  else if (b.bereich === "sicher") { chip.className = "status-chip gruen"; chip.innerHTML = `<span class="punkt gruen"></span>Sicher vorkontiert · ${prozent(b.sicherheit)}`; }
  else { chip.className = `status-chip ${b.ampel === "rot" ? "rot" : "gelb"}`; chip.innerHTML = `<span class="punkt ${b.ampel === "rot" ? "rot" : "gelb"}"></span>Bitte prüfen`; }

  $("b-lieferant").textContent = k.supplier_name || "Unbekannter Lieferant";
  $("b-meta").textContent = [b.mandant.name, k.document_type === "credit_note" ? "Gutschrift" : "Rechnung",
    k.invoice_number || "ohne Rechnungsnummer"].join(" · ");
  $("b-brutto").textContent = geld(k.gross_total, w);
  $("b-steuer").textContent = `Netto ${geld(k.net_total, w)} · USt ${geld(k.tax_total, w)}`;
  $("b-summen").textContent = b.steuerlogik.ok ? "✓ Summen stimmen" : "⚠ Summen passen nicht zusammen";
  $("b-summen").className = b.steuerlogik.ok ? "summen-ok" : "summen-fehler";
  const fakten = [
    ["Rechnungsdatum", datum(k.invoice_date)],
    ["Leistungsdatum", leistungText(k.leistung, true), !k.leistung],
    ["Währung", w === "EUR" ? "EUR" : `${w} (Fremdwährung)`, w !== "EUR"],
    ["Steuerfall", { inland: "Inland", ige: "i. g. Erwerb", "13b": "§ 13b UStG" }[b.steuerfall.id] || b.steuerfall.text, b.steuerfall.id !== "inland",
      `${b.steuerfall.text}${k.herkunft ? ` · Lieferant: ${HERKUNFT[k.herkunft]}` : ""}`],
  ];
  $("b-fakten").innerHTML = fakten.map(([t, v, auffaellig, titel]) => `<div class="fakt ${auffaellig ? "auffaellig" : ""}" title="${esc(titel || v)}">
    <span>${t}</span><b>${esc(v)}</b></div>`).join("");

  const aus = $("b-ausnahmen");
  aus.hidden = fertig || !b.ausnahmen.length;
  aus.innerHTML = `<b>Zur Prüfung, weil:</b><ul>${b.ausnahmen.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>`;

  zeigeKreditor(b, fertig);

  const sicher = b.positionen.filter((p) => p.ampel === "gruen").length;
  $("b-pos-info").textContent = `${anzahl(b.positionen.length, "Position", "Positionen")} · ${sicher} sicher` + (b.gelernt ? ` · ${b.gelernt} gelernt` : "");
  $("positionen").innerHTML = b.positionen.map((p) => `
    <li class="position">
      <div class="p-text">${esc(p.bezeichnung || "Position " + (p.pos + 1))}
        <small>${p.menge ? esc(Number(p.menge).toLocaleString("de-DE")) + " " + esc(p.einheit || "") : ""}</small></div>
      <div class="p-betrag">${geld(p.netto, w)}<small>${p.steuersatz ?? "–"} % USt</small></div>
      <div class="p-konto">
        <div class="konto-feld ${p.ampel}">
          <input data-pos="${p.pos}" ${fertig ? "disabled" : ""} autocomplete="off"
            value="${p.konto ? esc(p.konto.nr + " · " + p.konto.name) : ""}"
            placeholder="Konto wählen: Nummer oder Begriff, z. B. „War“">
        </div>
        ${steuerChip(p.steuer)}
        <div class="ampel ${p.ampel}" title="${esc(p.grund)}"><span class="punkt ${p.ampel}"></span>
          <span><b>${AMPEL[p.ampel]}</b><br>${esc(p.grund)}</span></div>
      </div>
    </li>`).join("");
  $("positionen").querySelectorAll("input[data-pos]").forEach(bindeKontoFeld);

  zeigeBuchungen(b);

  const lief = `${HERKUNFT[k.herkunft] || "–"}${k.lieferant_ustid ? ` · USt-IdNr. ${k.lieferant_ustid}` : ""}`;
  $("kopf").innerHTML = [["Lieferant", esc(k.supplier_name)], ["Sitz des Lieferanten", esc(lief)],
    ["Rechnungsnummer", esc(k.invoice_number ?? "–")], ["Rechnungsdatum", datum(k.invoice_date)],
    ["Leistungsdatum / -zeitraum", esc(leistungText(k.leistung, true))], ["Währung", esc(w)],
    ["Netto", geld(k.net_total, w)], ["Umsatzsteuer", geld(k.tax_total, w)], ["Brutto", geld(k.gross_total, w)],
    ["Steuerfall", esc(b.steuerfall.text)],
    ["Mandant", esc(`${b.mandant.name} · ${b.mandant.nummer} · ${b.mandant.kontenrahmen}`)]]
    .map(([a, c]) => `<tr><td>${a}</td><td>${c}</td></tr>`).join("");
  $("verlauf").innerHTML = b.protokoll.slice().reverse().map((e) => `<li><span><b>${esc(e.feld)}</b>: ${esc(e.alt ?? "–")} → ${esc(e.neu ?? "–")}
    <small>${new Date(e.zeit).toLocaleString("de-DE")} · ${esc(e.nutzer)} · ${esc(e.quelle)}</small></span></li>`).join("")
    || `<li><span class="klein">Noch keine Änderungen</span></li>`;

  const knopf = $("a-knopf");
  if (fertig) {
    knopf.textContent = "Wieder öffnen";
    knopf.className = "knopf grau gross";
    knopf.disabled = false;
    $("a-hinweis").innerHTML = `Freigegeben am ${new Date(b.freigegeben_am).toLocaleString("de-DE")} · Kreditor ${esc(b.kreditor?.nr)}.
      Wieder öffnen nimmt auch das dabei Gelernte zurück.`;
  } else {
    knopf.textContent = "Freigeben";
    knopf.className = "knopf blau gross";
    knopf.disabled = !b.freigabe_moeglich;
    $("a-hinweis").innerHTML = !b.freigabe_moeglich ? "Noch offen: " + b.offen.map(esc).join(" · ")
      : b.bereich === "sicher" ? "Alles sicher erkannt – ansehen und freigeben."
      : "Freigabe möglich – gelbe Punkte bitte kurz prüfen.";
  }
}

function steuerChip(st) {
  if (!st || (!st.bu && !st.text)) return `<span class="bu-chip leer" title="Steuerschlüssel folgt mit dem Konto">BU –</span>`;
  if (st.automatik) return `<span class="bu-chip auto" title="${esc(st.text)} – DATEV rechnet die Steuer aus dem Konto, kein Steuerschlüssel">Automatik</span>`;
  if (!st.bu) return `<span class="bu-chip leer" title="${esc(st.text)}">ohne BU</span>`;
  return `<span class="bu-chip" title="DATEV-Steuerschlüssel ${esc(st.bu)}: ${esc(st.text)}">BU ${esc(st.bu)}</span>`;
}

function zeigeBuchungen(b) {
  const w = b.kopf.currency || "EUR";
  const zeilen = b.buchungen.map((z) => `<tr>
      <td class="zahl-sp">${geld(z.umsatz, z.waehrung)}</td><td>${z.soll_haben}</td>
      <td><b>${esc(z.konto)}</b><small>${esc(z.konto_name)}</small></td>
      <td>${z.gegenkonto ? `<b>${esc(z.gegenkonto)}</b><small>Kreditor</small>` : `<span class="fehlt">fehlt</span>`}</td>
      <td>${z.bu ? `<b>${esc(z.bu)}</b>` : "–"}<small>${esc(z.steuer)}</small></td>
      <td>${datum(z.belegdatum)}<small>Leistung ${z.leistungsdatum ? datum(z.leistungsdatum) : "fehlt"}</small></td>
      <td>${esc(z.belegfeld1 || "–")}</td>
    </tr>`).join("");
  $("buchungen").innerHTML = `<thead><tr><th class="zahl-sp">Umsatz</th><th>S/H</th><th>Konto</th><th>Gegenkonto</th><th>BU</th><th>Belegdatum</th><th>Belegfeld 1</th></tr></thead>
    <tbody>${zeilen || `<tr><td colspan="7" class="klein">Noch keine Konten gewählt</td></tr>`}</tbody>`;
  const hinweise = [];
  if (b.steuerfall.id === "inland") hinweise.push("Umsatz brutto: DATEV rechnet die Vorsteuer aus Konto oder Steuerschlüssel heraus.");
  else hinweise.push("Umsatz netto: Vorsteuer und Umsatzsteuer bucht DATEV über Konto oder Steuerschlüssel.");
  if (w !== "EUR") hinweise.push(`Beträge in ${w}: Vor dem Export in Euro umrechnen (Kurs zum Leistungsdatum).`);
  $("buchungen-hinweis").textContent = hinweise.join(" ");
}

function zeigeKreditor(b, fertig) {
  const el = $("kreditor-karte");
  if (b.kreditor) {
    const regeln = b.regeln.map((r) => `
      <div class="regel ${r.aktiv ? "" : "aus"}">
        <span><b>${esc(r.beispiel)}</b> · ${esc(r.satz)} % → ${esc(r.konto)} ${esc(r.konto_name)}</span>
        <small>${r.bestaetigungen}× bestätigt${r.korrekturen ? `, ${r.korrekturen}× korrigiert` : ""} · ${r.sicher ? "sicher" : "noch unsicher"}
          · zuletzt ${datum((r.zuletzt || "").slice(0, 10))}</small>
        <label class="schalter" title="${r.aktiv ? "Regel abschalten" : "Regel einschalten"}">
          <input type="checkbox" data-regel="${esc(r.id)}" ${r.aktiv ? "checked" : ""}><span></span></label>
      </div>`).join("");
    el.innerHTML = `<div class="kreditor"><div><div class="klein">Kreditor</div><div class="nr">${esc(b.kreditor.nr)}</div></div>
      <div><div>${esc(b.kreditor.name)}</div><div class="klein">fest zugeordnet für ${esc(b.mandant.name)}</div></div></div>
      <details class="regeln" ${b.regeln.length ? "" : "hidden"}><summary>Gelernte Regeln für diesen Lieferanten (${b.regeln.length})</summary>${regeln}</details>`;
    el.querySelectorAll("input[data-regel]").forEach((i) => i.addEventListener("change", async () => {
      try {
        const neu = await post("/api/regel/aktiv", { key: b.key, regel: i.dataset.regel, aktiv: i.checked, modell: zustand.modell });
        zeigeBeleg(neu); el.querySelector(".regeln").open = true; ladeListe();
        toast(i.checked ? "Regel eingeschaltet" : "Regel abgeschaltet – Konto kommt wieder von der KI");
      } catch (e) { toast(e.message, true); }
    }));
    return;
  }
  const v = b.kreditor_vorschlag;
  el.innerHTML = `<div class="hinweis-zeile"><span class="punkt gelb"></span>Neuer Lieferant – bitte zuerst eine Kreditorennummer vergeben</div>
    <div class="kreditor-neu">
      <label>Kreditorennummer<input id="k-nr" class="feld" inputmode="numeric" value="${v.nr}" ${fertig ? "disabled" : ""}></label>
      <label>Name<input id="k-name" class="feld" value="${esc(v.name || "")}" ${fertig ? "disabled" : ""}></label>
      <button id="k-knopf" class="knopf blau" ${fertig ? "disabled" : ""}>Anlegen</button>
    </div>
    <div class="klein" style="margin-top:6px">Nummernkreis ${v.von}–${v.bis}. Vorgeschlagen ist die nächste freie Nummer. Nach dem Anlegen ist die Nummer fest.</div>`;
  $("k-knopf").addEventListener("click", async () => {
    try {
      const neu = await post("/api/beleg/kreditor", { key: b.key, nr: Number($("k-nr").value), name: $("k-name").value, modell: zustand.modell });
      zeigeBeleg(neu); ladeListe(); toast(`Kreditor ${neu.kreditor.nr} angelegt`);
    } catch (e) { toast(e.message, true); }
  });
}

/* ---------- Kontoauswahl: Klick leert das Feld und öffnet sofort die Suche ---------- */
let dd = { input: null, eintraege: [], aktiv: 0, timer: null };

function bindeKontoFeld(input) {
  input.addEventListener("focus", () => {
    input.dataset.bisher = input.value;
    input.placeholder = input.value ? `Suchen … (bisher ${input.value})` : "Konto suchen: Nummer oder Begriff, z. B. „War“";
    input.value = "";
    zeigeDropdown(input, "");
  });
  input.addEventListener("blur", () => { input.value = input.dataset.bisher || ""; });  // ohne Auswahl: altes Konto bleibt
  input.addEventListener("input", () => {
    clearTimeout(dd.timer);
    dd.timer = setTimeout(() => zeigeDropdown(input, input.value), 120);
  });
  input.addEventListener("keydown", (e) => {
    if (dd.input !== input || $("dropdown").hidden) return;
    if (e.key === "ArrowDown") { dd.aktiv = Math.min(dd.aktiv + 1, dd.eintraege.length - 1); markiere(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { dd.aktiv = Math.max(dd.aktiv - 1, 0); markiere(); e.preventDefault(); }
    else if (e.key === "Enter") { if (dd.eintraege[dd.aktiv]) waehle(dd.eintraege[dd.aktiv].nr); e.preventDefault(); }
    else if (e.key === "Escape") { schliesseDropdown(); input.blur(); }
  });
}

async function zeigeDropdown(input, text) {
  const pos = zustand.beleg.positionen[Number(input.dataset.pos)];
  const q = text.trim();
  const vorschlaege = pos.vorschlaege;
  const treffer = q ? await api("/api/konten?" + new URLSearchParams({ q })) : [];
  if (document.activeElement !== input) return;
  dd = { ...dd, input, eintraege: [...(q ? [] : vorschlaege), ...treffer], aktiv: 0 };
  const zeile = (k, i) => `<div class="dd-eintrag" data-i="${i}"><b>${esc(k.nr)}</b><span>${esc(k.name)}${k.kennzeichen ? `<span class="kennz">${esc(k.kennzeichen)}</span>` : ""}</span>
    ${k.quelle ? `<small class="quelle">${esc(k.quelle)}</small>` : ""}</div>`;
  let html = "";
  if (!q) html += `<div class="dd-titel">Vorschläge</div>` + (vorschlaege.map(zeile).join("") || `<div class="dd-leer">Keine Vorschläge – tippen Sie eine Nummer oder einen Begriff</div>`);
  if (q) html += `<div class="dd-titel">Konten im SKR03</div>` + (treffer.map((k, i) => zeile(k, i)).join("") || `<div class="dd-leer">Kein Konto zu „${esc(q)}“</div>`);
  html += `<div class="dd-fuss">AV = Automatikkonto (Vorsteuer im Konto) · sonst setzt das Programm den Steuerschlüssel</div>`;
  const d = $("dropdown");
  d.innerHTML = html;
  const r = input.getBoundingClientRect();
  d.style.left = r.left + "px";
  d.style.width = Math.max(r.width, 400) + "px";
  const unten = window.innerHeight - r.bottom;
  if (unten < 280) { d.style.top = ""; d.style.bottom = (window.innerHeight - r.top + 6) + "px"; }
  else { d.style.bottom = ""; d.style.top = (r.bottom + 6) + "px"; }
  d.hidden = false;
  d.querySelectorAll(".dd-eintrag").forEach((el) => el.addEventListener("mousedown", (e) => {
    e.preventDefault(); waehle(dd.eintraege[Number(el.dataset.i)].nr);
  }));
  markiere();
}

function markiere() {
  $("dropdown").querySelectorAll(".dd-eintrag").forEach((el) => el.classList.toggle("aktiv", Number(el.dataset.i) === dd.aktiv));
}

function schliesseDropdown() {
  $("dropdown").hidden = true;
  if (dd.input) dd.input.value = dd.input.dataset.bisher || "";
  dd.input = null;
}

async function waehle(nr) {
  const pos = Number(dd.input.dataset.pos);
  dd.input.dataset.bisher = nr;
  $("dropdown").hidden = true;
  dd.input.blur();
  dd.input = null;
  try {
    const b = await post("/api/beleg/konto", { key: zustand.key, pos, nr, modell: zustand.modell });
    zeigeBeleg(b); ladeListe();
    toast(`Position ${pos + 1}: Konto ${nr} übernommen`);
  } catch (e) { toast(e.message, true); }
}

/* ---------- Freigabe ---------- */
async function aktion() {
  const b = zustand.beleg;
  try {
    if (b.status === "freigegeben") {
      zeigeBeleg(await post("/api/beleg/wiedereroeffnen", { key: b.key, modell: zustand.modell }));
      toast("Beleg wieder geöffnet");
      return ladeListe();
    }
    const bereich = b.bereich;
    await post("/api/beleg/freigeben", { key: b.key, modell: zustand.modell });
    toast(`${b.kopf.supplier_name}: freigegeben`);
    await ladeListe();
    const naechste = zustand.liste.eintraege.find((e) => e.bereich === bereich && e.bereit && e.key !== b.key);
    oeffne(naechste ? naechste.key : b.key);
  } catch (e) { toast(e.message, true); }
}

function oeffneSammelfreigabe() {
  const sichere = zustand.liste.eintraege.filter((e) => e.bereich === "sicher");
  $("blatt-liste").innerHTML = sichere.map((e) => `
    <li><input type="checkbox" checked data-key="${esc(e.key)}" data-brutto="${esc(e.brutto)}">
      <span><b>${esc(e.lieferant)}</b><small>Kreditor ${esc(e.kreditor)} · Rechnung ${datum(e.datum)} · Leistung ${esc(leistungText(e.leistung))} · ${e.gelernt}/${e.positionen} gelernt</small></span>
      <span class="z-betrag">${geld(e.brutto, e.waehrung)}</span>
      <button class="link blau-link" data-oeffnen="${esc(e.key)}">Ansehen</button></li>`).join("");
  $("blatt-liste").querySelectorAll("input").forEach((i) => i.addEventListener("change", sammelSumme));
  $("blatt-liste").querySelectorAll("[data-oeffnen]").forEach((b) => b.addEventListener("click", () => {
    $("blatt-hintergrund").hidden = true; oeffne(b.dataset.oeffnen);
  }));
  sammelSumme();
  $("blatt-hintergrund").hidden = false;
}

function sammelSumme() {
  const gewaehlt = [...$("blatt-liste").querySelectorAll("input:checked")];
  const summe = gewaehlt.reduce((a, i) => a + Number(i.dataset.brutto || 0), 0);
  $("blatt-summe").textContent = `${gewaehlt.length} ausgewählt · ${geld(summe)}`;
  $("blatt-ok").textContent = `${gewaehlt.length} freigeben`;
  $("blatt-ok").disabled = !gewaehlt.length;
}

async function sammelfreigabe() {
  const keys = [...$("blatt-liste").querySelectorAll("input:checked")].map((i) => i.dataset.key);
  try {
    const r = await post("/api/sammelfreigabe", { keys, modell: zustand.modell });
    $("blatt-hintergrund").hidden = true;
    toast(`${anzahl(r.freigegeben.length, "Rechnung", "Rechnungen")} freigegeben` + (r.uebersprungen.length ? `, ${r.uebersprungen.length} übersprungen` : ""));
    await ladeListe();
    if (zustand.key) oeffne(zustand.key, false);
  } catch (e) { toast(e.message, true); }
}

/* ---------- Demo ---------- */
async function demoAktion(was) {
  $("demo-liste").hidden = true;
  try {
    if (was === "oktober") {
      toast("Oktober wird gebucht …");
      const r = await post("/api/demo/oktober", {});
      toast(`Oktober gebucht: ${r.freigegeben} Rechnungen, ${r.kreditoren} Kreditoren angelegt`);
      await ladeListe(); setzeFilter("erledigt");
    } else if (was === "november") {
      const r = await post("/api/demo/november", {});
      toast(`${r.eingespielt} Rechnungen für November eingespielt`);
      await ladeListe(); setzeFilter("sicher");
    } else if (was === "reset") {
      if (!confirm("Alle Kreditoren, Lernregeln, Kontoänderungen, Freigaben und Kanzlei-Stammdaten der Demo zurücksetzen?")) return;
      await post("/api/demo/zuruecksetzen", {});
      zustand.key = null; $("beleg").hidden = true; $("aktionsleiste").hidden = true; $("leer").hidden = false;
      leereVorschau();
      await ladeStamm();
      route();
      toast("Demo zurückgesetzt");
    }
  } catch (e) { toast(e.message, true); }
}

/* ---------- Belegansicht: Seite x von y, Zoom ---------- */
const ansichtZ = { seiten: 0, seite: 1, zoom: 1 };
const ZOOM = [0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3];

function leereVorschau() {
  $("vorschau").innerHTML = `<p class="klein mitte">Keine Rechnung gewählt</p>`;
  $("v-seiten").textContent = "";
  $("werkzeuge").hidden = true;
}

async function ladeVorschau(b) {
  const v = $("vorschau");
  ansichtZ.zoom = 1;
  if (b.art === "xml") {
    const t = await (await fetch(`/api/beleg/datei?${new URLSearchParams({ key: b.key })}`, { headers: { "X-Nutzer": zustand.nutzer } })).text();
    v.innerHTML = `<pre>${esc(t)}</pre>`;
    $("v-seiten").textContent = "E-Rechnung (XML)";
    $("werkzeuge").hidden = true;
    return;
  }
  const { anzahl: n } = await api(`/api/beleg/seiten?${new URLSearchParams({ key: b.key })}`);
  ansichtZ.seiten = n; ansichtZ.seite = 1;
  v.innerHTML = [...Array(n).keys()].map((i) => `<div class="seite" data-seite="${i + 1}">
    <img src="/api/beleg/seite?${new URLSearchParams({ key: b.key, i, nutzer: zustand.nutzer })}" alt="Seite ${i + 1} von ${n}" draggable="false"></div>`).join("");
  v.querySelectorAll("img").forEach((img) => img.addEventListener("load", aktuelleSeite));
  $("werkzeuge").hidden = false;
  $("w-gesamt").textContent = `/ ${n}`;
  wendeZoomAn();
  v.scrollTop = 0;
  zeigeSeitenzahl();
}

function zeigeSeitenzahl() {
  $("v-seiten").textContent = ansichtZ.seiten ? `Seite ${ansichtZ.seite} von ${ansichtZ.seiten}` : "";
  if (document.activeElement !== $("w-seite")) $("w-seite").value = ansichtZ.seite;
  $("w-hoch").disabled = ansichtZ.seite <= 1;
  $("w-runter").disabled = ansichtZ.seite >= ansichtZ.seiten;
}

function wendeZoomAn() {
  document.querySelectorAll("#vorschau .seite").forEach((s) => {
    s.style.width = `${ansichtZ.zoom * 100}%`;
    const img = s.querySelector("img");
    if (ansichtZ.zoom > 1.2 && !img.dataset.scharf) { img.dataset.scharf = "1"; img.src += "&dpi=200"; }  // schärfer beim Vergrößern
  });
  $("w-zoom").textContent = `${Math.round(ansichtZ.zoom * 100)} %`;
  $("w-minus").disabled = ansichtZ.zoom <= ZOOM[0];
  $("w-plus").disabled = ansichtZ.zoom >= ZOOM[ZOOM.length - 1];
}

function zoome(richtung, mitte = null) {
  const v = $("vorschau");
  const alt = ansichtZ.zoom;
  const i = ZOOM.findIndex((z) => z >= alt - 0.001);
  const neu = richtung > 0 ? ZOOM[Math.min((ZOOM[i] > alt + 0.001 ? i : i + 1), ZOOM.length - 1)] : ZOOM[Math.max(i - 1, 0)];
  if (neu === alt) return;
  const mx = mitte ? mitte.x : v.clientWidth / 2;
  const my = mitte ? mitte.y : v.clientHeight / 2;
  const fx = (v.scrollLeft + mx) / v.scrollWidth, fy = (v.scrollTop + my) / v.scrollHeight;
  ansichtZ.zoom = neu;
  wendeZoomAn();
  v.scrollLeft = fx * v.scrollWidth - mx;
  v.scrollTop = fy * v.scrollHeight - my;
}

/* Aktuelle Seite: die Seite, die das obere Drittel der Ansicht füllt (erst wenn die Bilder Höhe haben) */
function aktuelleSeite() {
  const v = $("vorschau");
  const seiten = [...v.querySelectorAll(".seite")];
  if (!ansichtZ.seiten || seiten.some((s) => !s.offsetHeight)) return;
  const linie = v.scrollTop + v.clientHeight / 3;
  let aktuell = 1;
  seiten.forEach((s) => { if (s.offsetTop <= linie) aktuell = Number(s.dataset.seite); });
  if (aktuell !== ansichtZ.seite) { ansichtZ.seite = aktuell; zeigeSeitenzahl(); }
}

function springeZuSeite(n) {
  n = Math.max(1, Math.min(ansichtZ.seiten, n));
  const ziel = document.querySelector(`#vorschau .seite[data-seite="${n}"]`);
  if (ziel) $("vorschau").scrollTo({ top: ziel.offsetTop - 12, behavior: "smooth" });
  ansichtZ.seite = n;
  zeigeSeitenzahl();
}

function bindeWerkzeuge() {
  const v = $("vorschau");
  v.addEventListener("scroll", aktuelleSeite);
  v.addEventListener("wheel", (e) => {
    if (!e.ctrlKey || $("werkzeuge").hidden) return;
    e.preventDefault();
    const r = v.getBoundingClientRect();
    zoome(e.deltaY < 0 ? 1 : -1, { x: e.clientX - r.left, y: e.clientY - r.top });
  }, { passive: false });
  $("w-plus").addEventListener("click", () => zoome(1));
  $("w-minus").addEventListener("click", () => zoome(-1));
  $("w-passend").addEventListener("click", () => { ansichtZ.zoom = 1; wendeZoomAn(); });
  $("w-hoch").addEventListener("click", () => springeZuSeite(ansichtZ.seite - 1));
  $("w-runter").addEventListener("click", () => springeZuSeite(ansichtZ.seite + 1));
  $("w-seite").addEventListener("change", (e) => springeZuSeite(Number(e.target.value) || 1));
  $("w-seite").addEventListener("focus", (e) => e.target.select());
  // Verschieben mit gedrückter Maustaste, wenn vergrößert
  let ziehen = null;
  v.addEventListener("mousedown", (e) => {
    if (ansichtZ.zoom <= 1 || e.button !== 0 || !e.target.closest(".seite")) return;
    ziehen = { x: e.clientX, y: e.clientY, l: v.scrollLeft, t: v.scrollTop };
    v.classList.add("zieht"); e.preventDefault();
  });
  window.addEventListener("mousemove", (e) => {
    if (!ziehen) return;
    v.scrollLeft = ziehen.l - (e.clientX - ziehen.x);
    v.scrollTop = ziehen.t - (e.clientY - ziehen.y);
  });
  window.addEventListener("mouseup", () => { ziehen = null; v.classList.remove("zieht"); });
}

async function hochladen(e) {
  const datei = e.target.files[0];
  if (!datei) return;
  const form = new FormData();
  form.append("datei", datei);
  form.append("mandant", zustand.mandant);
  try {
    const r = await fetch("/api/upload", { method: "POST", body: form, headers: { "X-Nutzer": zustand.nutzer } });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail);
    toast("Rechnung wird gelesen …");
    await ladeListe();
    await oeffne(d.key);
  } catch (err) { toast(err.message, true); }
  e.target.value = "";
}

init();
