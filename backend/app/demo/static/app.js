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

/* Symbole (Linien) */
const PFADE = {
  person: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  liste: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
  buchung: '<path d="M4 8h15l-4-4M20 16H5l4 4"/>',
  beleg: '<path d="M6 2h8l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z"/><path d="M14 2v5h5M8 13h8M8 17h5"/>',
  hoch: '<path d="M6 15l6-6 6 6"/>',
  runter: '<path d="M6 9l6 6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  vollbild: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
  vollbild_aus: '<path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/>',
  haken: '<path d="M9 11l3 3 8-8"/><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9"/>',
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

  $("nutzer-knopf").addEventListener("click", (e) => { e.stopPropagation(); waehleNutzer(); });
  $("mandant-knopf").addEventListener("click", (e) => { e.stopPropagation(); waehleMandant(); });
  document.querySelectorAll(".segment.drei button").forEach((b) => b.addEventListener("click", () => setzeFilter(b.dataset.filter)));
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
    if (!e.target.closest(".auswahl")) schliesseAuswahl();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { document.querySelectorAll(".blatt-hintergrund").forEach((b) => { b.hidden = true; }); schliesseAuswahl(); }
  });
  $("ue-neu").addEventListener("click", () => oeffneMandant(null));
  $("ue-rechte").addEventListener("click", oeffneRechte);
  $("ue-kanzlei").addEventListener("click", oeffneBerater);
  $("berater-form").addEventListener("submit", sichereBerater);
  // Beleg ein- und ausblenden (gemerkt): ausgeblendet hat die Bearbeitung die volle Breite
  const belegZeigen = (an) => { $("seite-belege").classList.toggle("ohne-beleg", !an); merke("beleg", an ? "an" : "aus"); };
  $("v-zu").addEventListener("click", () => belegZeigen(false));
  $("v-auf").addEventListener("click", () => belegZeigen(true));
  $("seite-belege").classList.toggle("ohne-beleg", lies("beleg") === "aus");
  $("mandant-form").addEventListener("submit", sichereMandant);
  document.querySelectorAll("#f-kontenrahmen button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("#f-kontenrahmen button").forEach((x) => x.classList.toggle("aktiv", x === b));
  }));
  $("sb-form").addEventListener("submit", sichereSachbearbeiter);
  $("rechte-suche").addEventListener("input", zeigeRechte);
  bindeWerkzeuge();
  bindeAbschnitte();
  window.addEventListener("hashchange", route);
  route();
}

async function ladeStamm() {
  zustand.stamm = await api("/api/stammdaten");
  if (!zustand.bus) zustand.bus = await api("/api/steuerschluessel");
  const s = zustand.stamm;
  if (!s.nutzer) { zustand.nutzer = s.sachbearbeiter[0].kuerzel; merke("nutzer", zustand.nutzer); return ladeStamm(); }
  zustand.modell = zustand.modell || s.standard_modell;
  $("nutzer-avatar").textContent = s.nutzer.kuerzel;
  $("nutzer-name").textContent = s.nutzer.name;
  $("nutzer-rolle").textContent = s.rollen[s.nutzer.rolle];
  $("modell").innerHTML = s.modelle.map((m) => `<option value="${m.id}" ${m.id === zustand.modell ? "selected" : ""}>${esc(m.kurz)}</option>`).join("");
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
  $("ue-titel").textContent = s.leitung ? "Alle Mandanten" : "Meine Mandanten";
  const q = $("ue-suche").value.trim().toLowerCase();
  const zeilen = u.mandanten.filter((m) => !q || `${m.name} ${m.nummer} ${m.ansprechpartner}`.toLowerCase().includes(q));
  $("ue-tabelle").innerHTML = zeilen.map((m) => `
    <div class="ue-zeile" data-mandant="${esc(m.id)}" tabindex="0">
      <span class="m-avatar">${esc(initialen(m.name))}</span>
      <span class="m-name"><b>${esc(m.name)}</b><small>${esc(m.ansprechpartner || "Kein Ansprechpartner")}</small></span>
      <span class="m-nr">${esc(m.nummer)}${mehrereBerater() ? `<small>Berater ${esc(m.beraternummer)}</small>` : ""}</span>
      <span><span class="marke">${esc(m.kontenrahmen)}</span></span>
      <span class="m-team">${team(m.team)}</span>
      <span class="m-zuletzt">${m.zuletzt_bearbeitet ? esc(monatText(m.zuletzt_bearbeitet)) : `<span class="klein">noch nichts gebucht</span>`}</span>
      <span class="m-offen">${m.lesen ? `<span class="klein">wird gelesen …</span>` : m.offen
        ? m.offen_je_monat.slice(0, 3).map((g) => `<div class="offen-monat"><b>${g.monat ? esc(monatText(g.monat)) : "ohne Datum"}:</b>
            <span class="offen-zahl">${anzahl(g.offen, "Beleg", "Belege")} offen</span>
            <small>${[g.sicher && `${g.sicher} sicher`, g.pruefen && `${g.pruefen} prüfen`].filter(Boolean).join(" · ")}</small></div>`).join("")
          + (m.offen_je_monat.length > 3 ? `<div class="offen-monat"><small>+ ${m.offen_je_monat.slice(3).reduce((s, g) => s + g.offen, 0)} Belege
            aus ${m.offen_je_monat.length - 3} älteren Monaten (ab ${esc(monatText(m.offen_je_monat.at(-1).monat))})</small></div>` : "")
        : `<span class="erledigt-haken">✓ nichts offen</span>`}</span>
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
  const k = s.kanzlei;
  const berater = Number(m?.beraternummer || k.standard);
  f.beraternummer.innerHTML = k.beraternummern.map((b) => `<option value="${b.nr}" ${b.nr === berater ? "selected" : ""}>
    ${b.nr} · ${esc(b.bezeichnung)}${b.nr === k.standard ? " (Standard)" : ""}</option>`).join("");
  f.beraternummer.onchange = () => { if (!id) f.nummer.value = naechsteNummer(Number(f.beraternummer.value)); };
  f.nummer.value = m?.nummer || naechsteNummer(berater);
  f.ansprechpartner.value = m?.ansprechpartner || "";
  f.ustid.value = m?.ustid || "";
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

/* Nächste freie Mandantennummer – Mandantennummern sind je Beraternummer eindeutig */
function naechsteNummer(berater) {
  const vergeben = new Set(zustand.stamm.alle_mandanten.filter((m) => Number(m.beraternummer) === berater).map((m) => Number(m.nummer)));
  let n = 10001;
  while (vergeben.has(n)) n++;
  return n;
}

async function sichereMandant(e) {
  e.preventDefault();
  const f = e.target;
  const daten = {
    id: f.dataset.id || null, name: f.name.value, beraternummer: f.beraternummer.value, nummer: f.nummer.value, ansprechpartner: f.ansprechpartner.value, ustid: f.ustid.value,
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

/* ---------- Beraternummern der Kanzlei (nur Kanzleileitung) ---------- */
const mehrereBerater = () => (zustand.stamm.kanzlei?.beraternummern.length || 0) > 1;

function oeffneBerater() {
  zeigeBerater();
  $("kanzlei-blatt").hidden = false;
}

function zeigeBerater() {
  const k = zustand.stamm.kanzlei;
  $("berater-liste").innerHTML = k.beraternummern.map((b) => `<li data-nr="${b.nr}">
      <span><b>${b.nr}</b> · ${esc(b.bezeichnung)}<small>${anzahl(b.mandanten, "Mandant", "Mandanten")}</small></span>
      ${b.nr === k.standard ? `<span class="marke">Standard</span>` : `<button class="link blau-link klein-link" data-standard>Als Standard</button>`}
      ${b.nr !== k.standard && !b.mandanten ? `<button class="link gefahr-link klein-link" data-entfernen>Entfernen</button>` : "<span></span>"}
    </li>`).join("");
  $("berater-liste").querySelectorAll("li").forEach((li) => {
    const b = k.beraternummern.find((x) => String(x.nr) === li.dataset.nr);
    li.querySelector("[data-standard]")?.addEventListener("click", () =>
      beraterSenden("/api/kanzlei/beraternummer", { nr: b.nr, bezeichnung: b.bezeichnung, standard: true }, `${b.nr} ist jetzt Standard`));
    li.querySelector("[data-entfernen]")?.addEventListener("click", () =>
      beraterSenden("/api/kanzlei/beraternummer/entfernen", { nr: b.nr }, `Beraternummer ${b.nr} entfernt`));
  });
}

async function beraterSenden(url, daten, meldung) {
  try {
    zustand.stamm = { ...zustand.stamm, ...(await post(url, daten)) };
    zeigeBerater();
    if (zustand.seite === "uebersicht") zeigeUebersicht();
    toast(meldung);
    return true;
  } catch (e) { toast(e.message, true); return false; }
}

async function sichereBerater(e) {
  e.preventDefault();
  const f = e.target;
  if (await beraterSenden("/api/kanzlei/beraternummer", { nr: f.nr.value, bezeichnung: f.bezeichnung.value },
    `Beraternummer ${f.nr.value.trim()} angelegt`)) f.reset();
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

/* ---------- Aufklappbare Abschnitte (Zustand je Abschnitt gemerkt) ---------- */
const KLAPP_START = { pruefung: false, kreditor: false, positionen: true, buchungen: false, daten: false };
let klapp = { ...KLAPP_START };

function bindeAbschnitte() {
  try { klapp = { ...KLAPP_START, ...JSON.parse(lies("klapp") || "{}") }; } catch { klapp = { ...KLAPP_START }; }
  document.querySelectorAll("details[data-klapp]").forEach((d) => {
    d.open = klapp[d.dataset.klapp];
    d.querySelector("summary").addEventListener("click", () => setTimeout(() => {
      klapp[d.dataset.klapp] = d.open; merke("klapp", JSON.stringify(klapp));
    }, 0));
  });
}

function setzeKlapp(name, offen) {
  document.querySelector(`details[data-klapp="${name}"]`).open = offen;
}

/* ---------- Belegverarbeitung: Liste ---------- */
function initialen(name) {
  return name.replace(/[^A-Za-zÄÖÜäöü ]/g, "").split(" ").filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
}

/* ---------- Auswahl im iOS-Stil (Person, Mandant): Liste mit Häkchen, Suche, Tastatur ---------- */
let auswahl = null;

function schliesseAuswahl() {
  $("auswahl").hidden = true;
  document.querySelectorAll(".nutzer-knopf, .mandant-knopf").forEach((k) => k.classList.remove("offen"));
  auswahl = null;
}

function zeigeAuswahl(anker, { titel, eintraege, gewaehlt, suche = false, rechts = false, onWahl }) {
  if (auswahl && auswahl.anker === anker) return schliesseAuswahl();
  schliesseAuswahl();
  const el = $("auswahl");
  auswahl = { anker, eintraege, onWahl, aktiv: Math.max(0, eintraege.findIndex((e) => e.id === gewaehlt)) };
  el.innerHTML = `<div class="aw-titel">${esc(titel)}</div>
    ${suche ? `<input class="feld suchfeld aw-suche" placeholder="Suchen" autocomplete="off">` : ""}
    <ul class="aw-liste"></ul>`;
  const zeichne = (q = "") => {
    const treffer = eintraege.filter((e) => !q || `${e.titel} ${e.untertitel || ""}`.toLowerCase().includes(q.toLowerCase()));
    auswahl.sichtbar = treffer;
    auswahl.aktiv = Math.min(auswahl.aktiv, Math.max(0, treffer.length - 1));
    el.querySelector(".aw-liste").innerHTML = treffer.map((e, i) => `
      <li class="aw-eintrag ${e.id === gewaehlt ? "gewaehlt" : ""} ${i === auswahl.aktiv ? "aktiv" : ""}" data-i="${i}" role="option">
        <span class="${e.rund ? "avatar" : "m-avatar"}">${esc(e.avatar)}</span>
        <span class="aw-text"><b>${esc(e.titel)}</b>${e.untertitel ? `<small>${esc(e.untertitel)}</small>` : ""}</span>
        ${e.rechts ? `<span class="aw-rechts">${e.rechts}</span>` : ""}
        <span class="aw-haken">${e.id === gewaehlt ? "✓" : ""}</span>
      </li>`).join("") || `<li class="aw-leer">Keine Treffer</li>`;
    el.querySelectorAll(".aw-eintrag").forEach((li) => li.addEventListener("click", () => {
      const e = treffer[Number(li.dataset.i)]; schliesseAuswahl(); onWahl(e.id);
    }));
  };
  zeichne();
  const r = anker.getBoundingClientRect();
  el.style.top = `${r.bottom + 6}px`;
  el.style.left = rechts ? "" : `${r.left}px`;
  el.style.right = rechts ? `${window.innerWidth - r.right}px` : "";
  el.hidden = false;
  anker.classList.add("offen");
  const feld = el.querySelector(".aw-suche");
  feld?.addEventListener("input", () => zeichne(feld.value));
  (feld || el).focus?.();
  el.onkeydown = (ev) => {
    if (!auswahl) return;
    const n = auswahl.sichtbar.length;
    if (ev.key === "ArrowDown") { auswahl.aktiv = Math.min(auswahl.aktiv + 1, n - 1); zeichne(feld?.value || ""); ev.preventDefault(); }
    else if (ev.key === "ArrowUp") { auswahl.aktiv = Math.max(auswahl.aktiv - 1, 0); zeichne(feld?.value || ""); ev.preventDefault(); }
    else if (ev.key === "Enter" && n) { const e = auswahl.sichtbar[auswahl.aktiv]; schliesseAuswahl(); onWahl(e.id); }
  };
}

function waehleNutzer() {
  const s = zustand.stamm;
  zeigeAuswahl($("nutzer-knopf"), {
    titel: "Angemeldet als (Demo)", gewaehlt: zustand.nutzer, rechts: true,
    eintraege: s.sachbearbeiter.map((p) => {
      const n = Object.values(p.zugriff || {}).filter((w) => w === "an").length;
      return { id: p.kuerzel, avatar: p.kuerzel, rund: true, titel: p.name,
        untertitel: `${s.rollen[p.rolle]} · ${p.rolle === "leitung" ? "alle Mandanten" : anzahl(n, "Mandant", "Mandanten")}` };
    }),
    onWahl: async (kuerzel) => {
      if (kuerzel === zustand.nutzer) return;
      zustand.nutzer = kuerzel; merke("nutzer", kuerzel);
      await ladeStamm();
      toast(`Angemeldet als ${zustand.stamm.nutzer.name}`);
      route();
    },
  });
}

async function waehleMandant() {
  const s = zustand.stamm;
  const offen = {};
  try {  // offene Belege je Mandant aus der Übersicht (schon berechnet, daher schnell)
    const u = zustand.uebersicht || await api(`/api/uebersicht?${new URLSearchParams({ modell: zustand.modell })}`);
    for (const m of u.mandanten) offen[m.id] = m;
  } catch { /* ohne Zahlen weiter */ }
  zeigeAuswahl($("mandant-knopf"), {
    titel: "Mandant wechseln", gewaehlt: zustand.mandant, suche: s.mandanten.length > 5,
    eintraege: s.mandanten.map((m) => ({
      id: m.id, avatar: initialen(m.name), titel: m.name, untertitel: `${m.nummer} · ${m.kontenrahmen}`,
      rechts: offen[m.id] ? (offen[m.id].offen ? `<span class="aw-offen">${offen[m.id].offen} offen</span>` : `<span class="aw-fertig">erledigt</span>`) : "",
    })),
    onWahl: (id) => { location.hash = `#/belege/${id}`; },
  });
}

function zeigeMandantKopf() {
  const m = zustand.stamm.mandanten.find((x) => x.id === zustand.mandant);
  if (!m) return;
  $("mandant-name").textContent = m.name;
  $("mandant-avatar").textContent = initialen(m.name);
  $("mandant-info").innerHTML = `<span title="Beraternummer / Mandantennummer (DATEV)">${esc(m.beraternummer)} / ${esc(m.nummer)}</span>`
    + ` · ${esc(m.kontenrahmen)} · ${team(m.team)}`;
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
  // Ruhige Liste: der Punkt zeigt den Status, Marken nur für das, was zu tun ist
  const marken = [];
  const gruende = (e.ausnahmen || []).map((a) => a.split(" (")[0].split(" – ")[0]);
  if (gruende.length) marken.push(`<span class="marke orange" title="${esc(gruende.join(" · "))}">${esc(gruende[0])}${gruende.length > 1 ? ` +${gruende.length - 1}` : ""}</span>`);
  if (e.frei) marken.push(`<span class="marke orange">${e.frei} ohne Konto</span>`);
  if (e.art === "xml") marken.push(`<span class="marke">${art}</span>`);
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
  $("b-summen").textContent = b.steuerlogik.ok ? "" : "Summen passen nicht zusammen";
  $("b-summen").className = "summen-fehler";
  $("b-summen").hidden = b.steuerlogik.ok;
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
  aus.innerHTML = `<b>Prüfen:</b>${b.ausnahmen.map((a) => `<span class="grund">${esc(a)}</span>`).join("")}`;

  zeigeKreditor(b, fertig);

  const sicher = b.positionen.filter((p) => p.ampel === "gruen").length;
  const unsicher = b.positionen.length - sicher;
  $("b-pos-info").innerHTML = `${anzahl(b.positionen.length, "Position", "Positionen")} · ${sicher} sicher`
    + (unsicher ? ` · <span class="kurz-warn">${unsicher} prüfen</span>` : "") + (b.gelernt ? ` · ${b.gelernt} gelernt` : "");
  $("positionen").innerHTML = b.positionen.map((p) => `
    <li class="position" data-pos="${p.pos}">
      <div class="p-text">${esc(p.bezeichnung || "Position " + (p.pos + 1))}
        ${p.menge ? `<small>${esc(Number(p.menge).toLocaleString("de-DE"))} ${esc(p.einheit || "")}</small>` : ""}</div>
      <div class="p-betrag">${geld(p.netto, w)} ${satzWahl(p, fertig)}</div>
      <div class="p-konto">
        <div class="konto-feld ${p.ampel}">
          <input data-pos="${p.pos}" ${fertig ? "disabled" : ""} autocomplete="off"
            value="${p.konto ? esc(p.konto.nr + " · " + p.konto.name) : ""}"
            placeholder="Konto: Nummer oder Begriff">
        </div>
        ${buWahl(p, fertig)}
        <div class="ampel ${p.ampel}" title="${esc(p.grund)}"><span class="punkt ${p.ampel}"></span><b>${AMPEL[p.ampel]}</b></div>
      </div>
      ${p.ampel !== "gruen" && p.grund ? `<div class="p-grund">${esc(p.grund)}</div>` : ""}
      ${satzKorrektur(p, fertig)}
      ${aufteilungZeile(p, w, fertig)}
    </li>`).join("");
  $("positionen").querySelectorAll("input[data-pos]").forEach(bindeKontoFeld);
  bindePositionsWahl(b);

  zeigeBuchungen(b);
  zeigePruefung(b);

  const lief = `${HERKUNFT[k.herkunft] || "–"}${k.lieferant_ustid ? ` · USt-IdNr. ${k.lieferant_ustid}` : ""}`;
  $("kopf").innerHTML = [["Lieferant", esc(k.supplier_name)], ["Sitz des Lieferanten", esc(lief)],
    ["Rechnungsnummer", esc(k.invoice_number ?? "–")], ["Rechnungsdatum", datum(k.invoice_date)],
    ["Leistungsdatum / -zeitraum", esc(leistungText(k.leistung, true))], ["Währung", esc(w)],
    ["Netto", geld(k.net_total, w)], ["Umsatzsteuer", geld(k.tax_total, w)], ["Brutto", geld(k.gross_total, w)],
    ["Steuerfall", esc(b.steuerfall.text)],
    ["Mandant", esc(`${b.mandant.name} · ${b.mandant.nummer} · ${b.mandant.kontenrahmen}`)]]
    .map(([a, c]) => `<tr><td>${a}</td><td>${c}</td></tr>`).join("");
  $("kurz-daten").textContent = [k.invoice_number && `Nr. ${k.invoice_number}`, HERKUNFT[k.herkunft],
    k.lieferant_ustid && `USt-IdNr. ${k.lieferant_ustid}`].filter(Boolean).join(" · ");
  $("verlauf").innerHTML = b.protokoll.slice().reverse().map((e) => `<li><span><b>${esc(e.feld)}</b>: ${esc(e.alt ?? "–")} → ${esc(e.neu ?? "–")}
    <small>${new Date(e.zeit).toLocaleString("de-DE")} · ${esc(e.nutzer)} · ${esc(e.quelle)}</small></span></li>`).join("")
    || `<li><span class="klein">Noch keine Änderungen</span></li>`;

  const knopf = $("a-knopf");
  if (fertig) {
    knopf.textContent = "Wieder öffnen";
    knopf.className = "knopf grau gross";
    knopf.disabled = false;
    $("a-hinweis").innerHTML = `Freigegeben am ${new Date(b.freigegeben_am).toLocaleString("de-DE")} · Kreditor ${esc(b.kreditor?.nr)}.
`;
    knopf.title = "Wieder öffnen nimmt auch das dabei Gelernte zurück";
  } else {
    knopf.textContent = "Freigeben";
    knopf.className = "knopf blau gross";
    knopf.disabled = !b.freigabe_moeglich;
    $("a-hinweis").innerHTML = !b.freigabe_moeglich ? "Noch offen: " + b.offen.map(esc).join(" · ")
      : b.bereich === "sicher" ? "" : "Gelb markierte Positionen prüfen";
  }
}

/* Steuerschlüssel je Position: Vorschlag oder von Hand (alle belegten DATEV-Schlüssel). Die Steuerlogik prüft beides. */
function buBeschriftung(st) {
  if (!st || (!st.bu && !st.text)) return ["BU –", "Steuerschlüssel folgt mit dem Konto", "leer"];
  if (st.automatik) return ["Automatik", `${st.text} – DATEV rechnet die Steuer aus dem Konto, kein Steuerschlüssel`, "auto"];
  if (!st.bu) return ["ohne BU", st.text, "leer"];
  return [`BU ${st.bu}`, `DATEV-Steuerschlüssel ${st.bu}: ${st.text}`, ""];
}

function buWahl(p, fertig) {
  const st = p.teile[0]?.steuer || p.steuer;
  const [text, titel, art] = buBeschriftung(st);
  const gruppen = {};
  for (const e of zustand.bus || []) (gruppen[e.gruppe] ||= []).push(e);
  const optionen = Object.entries(gruppen).map(([g, es]) => `<optgroup label="${esc(g)}">${es.map((e) =>
    `<option value="${esc(e.bu)}" ${p.bu_manuell && e.bu === st.bu ? "selected" : ""}>${e.bu ? `BU ${esc(e.bu)} – ` : ""}${esc(e.text)}</option>`).join("")}</optgroup>`).join("");
  return `<label class="bu-chip ${art} ${p.bu_manuell ? "manuell" : ""}" title="${esc(titel)}${p.bu_manuell ? " (von Hand gewählt)" : ""}">
    <span>${esc(text)}${p.bu_manuell ? " ✎" : ""}</span>
    <select data-bu="${p.pos}" ${fertig || !p.konto ? "disabled" : ""} aria-label="Steuerschlüssel ändern">
      <option value="__vorschlag" ${p.bu_manuell ? "" : "selected"}>Vorschlag übernehmen</option>${optionen}</select></label>`;
}

/* Steuersatz der Rechnung: nur Anzeige. Geändert wird über den Steuerschlüssel; eine falsch gelesene Rechnung
   korrigiert der Knopf im Hinweis (satzKorrektur), eine Korrektur lässt sich hier zurücknehmen. */
function satzWahl(p, fertig) {
  if (!p.satz_manuell) return `<span class="satz-anzeige" title="Steuersatz laut Rechnung">· ${esc(p.steuersatz ?? "–")} %</span>`;
  return `<span class="satz-anzeige manuell" title="Korrigiert, laut Erkennung ${esc(p.steuersatz_beleg)} %">· ${esc(p.steuersatz)} % ✎
    ${fertig ? "" : `<button class="link blau-link klein-link" data-satz-zurueck="${p.pos}">zurück auf ${esc(p.steuersatz_beleg)} %</button>`}</span>`;
}

/* Gewählter Schlüssel passt nicht zum Satz der Rechnung: Angebot, die Rechnung als falsch gelesen zu korrigieren */
function satzKorrektur(p, fertig) {
  const st = p.teile[0]?.steuer;
  if (fertig || !p.bu_manuell || !st || st.satz == null || st.automatik || (st.fall && st.fall !== "inland")
      || String(Number(st.satz)) === String(Number(p.steuersatz)) || Number(st.satz) === 0) return "";
  const neu = esc(String(Number(st.satz)));
  return `<div class="satz-korrektur" title="Sonst bleibt es bei ${esc(p.steuersatz)} % laut Rechnung und ${neu} % Vorsteuer">Rechnung falsch gelesen?
    <button class="link blau-link klein-link" data-satz-auf="${p.pos}" data-satz="${neu}">Auf ${neu} % korrigieren</button></div>`;
}

/* Aufteilung einer Position auf mehrere Konten, z. B. Bewirtung 70 % abziehbar / 30 % nicht abziehbar */
function aufteilungZeile(p, w, fertig) {
  if (!p.konto) return "";
  const geteilt = p.teile.length > 1;
  const liste = geteilt ? p.teile.map((t) => `<span class="teil"><b>${esc(t.konto.nr)}</b> ${esc(t.konto.name)} · ${esc(t.prozent)} % · ${geld(t.netto, w)}</span>`).join("") : "";
  return `<div class="aufteilung ${geteilt ? "aktiv" : ""}">
    ${geteilt ? liste : ""}
    ${fertig ? "" : `<button class="link blau-link klein-link" data-aufteilen="${p.pos}">${geteilt ? "Aufteilung ändern" : "Aufteilen"}</button>`}
  </div><div class="aufteilen-editor" data-editor="${p.pos}" hidden></div>`;
}

function aufteilungEditor(b, p, li) {
  const ed = li.querySelector("[data-editor]");
  const zeilen = (teile) => teile.map((t) => `<div class="ae-zeile">
      <input class="feld ae-konto" value="${esc(t.konto)}" placeholder="Konto" inputmode="numeric">
      <input class="feld ae-prozent" value="${esc(t.prozent)}" placeholder="%" inputmode="decimal"><span>%</span></div>`).join("");
  // Ohne Vorbelegung: bisheriges Konto und ein leeres Feld. 70/30 nur bei einem erkannten Bewirtungsbeleg.
  const start = p.teile.length > 1 ? p.teile.map((t) => ({ konto: t.konto.nr, prozent: t.prozent }))
    : [{ konto: p.konto.nr, prozent: "" }, { konto: "", prozent: "" }];
  ed.innerHTML = `<div class="ae-liste">${zeilen(start)}</div>
    <div class="ae-knoepfe">
      ${b.bewirtung ? `<button class="link blau-link" data-ae="bewirtung">Bewirtung 70 / 30</button>` : ""}
      <button class="link blau-link" data-ae="plus">＋ Konto</button>
      <span class="ae-rechts">
        ${p.teile.length > 1 ? `<button class="link gefahr-link" data-ae="keine">Aufteilung entfernen</button>` : ""}
        <button class="link" data-ae="abbrechen">Abbrechen</button>
        <button class="knopf blau klein-knopf" data-ae="ok">Übernehmen</button></span></div>
    <p class="klein">Prozent vom Nettobetrag, zusammen 100 %.</p>`;
  ed.hidden = false;
  const senden = async (teile) => {
    try {
      zeigeBeleg(await post("/api/beleg/aufteilung", { key: b.key, pos: p.pos, teile, modell: zustand.modell }));
      ladeListe(); toast(teile && teile.length ? "Aufteilung übernommen" : "Aufteilung entfernt");
    } catch (e) { toast(e.message, true); }
  };
  ed.querySelectorAll("[data-ae]").forEach((k) => k.addEventListener("click", () => {
    const art = k.dataset.ae;
    if (art === "abbrechen") { ed.hidden = true; return; }
    if (art === "keine") return senden([]);
    if (art === "bewirtung") { ed.querySelector(".ae-liste").innerHTML = zeilen([{ konto: "4650", prozent: "70" }, { konto: "4654", prozent: "30" }]); return; }
    if (art === "plus") { ed.querySelector(".ae-liste").insertAdjacentHTML("beforeend", zeilen([{ konto: "", prozent: "" }])); return; }
    const teile = [...ed.querySelectorAll(".ae-zeile")].map((z) => ({ konto: z.querySelector(".ae-konto").value.trim(),
      prozent: z.querySelector(".ae-prozent").value.trim().replace(",", ".") })).filter((t) => t.konto || t.prozent);
    senden(teile);
  }));
}

function bindePositionsWahl(b) {
  const pos = (i) => b.positionen[Number(i)];
  document.querySelectorAll("#positionen select[data-bu]").forEach((s) => s.addEventListener("change", async () => {
    try {
      zeigeBeleg(await post("/api/beleg/steuerschluessel", { key: b.key, pos: Number(s.dataset.bu), wert: s.value === "__vorschlag" ? null : s.value, modell: zustand.modell }));
      ladeListe(); toast(s.value === "__vorschlag" ? "Steuerschlüssel: Vorschlag" : `Steuerschlüssel ${s.value || "keiner"} übernommen`);
    } catch (e) { toast(e.message, true); }
  }));
  const satzSenden = async (p, wert) => {
    try {
      zeigeBeleg(await post("/api/beleg/steuersatz", { key: b.key, pos: p.pos, wert, modell: zustand.modell }));
      ladeListe(); toast(wert == null ? `Steuersatz wieder laut Rechnung (${p.steuersatz_beleg} %)` : `Steuersatz auf ${wert} % korrigiert`);
    } catch (e) { toast(e.message, true); }
  };
  document.querySelectorAll("#positionen [data-satz-auf]").forEach((k) => k.addEventListener("click", () => satzSenden(pos(k.dataset.satzAuf), k.dataset.satz)));
  document.querySelectorAll("#positionen [data-satz-zurueck]").forEach((k) => k.addEventListener("click", () => satzSenden(pos(k.dataset.satzZurueck), null)));
  document.querySelectorAll("#positionen [data-aufteilen]").forEach((k) => k.addEventListener("click", () =>
    aufteilungEditor(b, pos(k.dataset.aufteilen), k.closest(".position"))));
  // Überfahren einer Position: Zeile im Beleg hervorheben
  document.querySelectorAll("#positionen .position").forEach((li) => {
    li.addEventListener("mouseenter", () => markiere_position(Number(li.dataset.pos)));
    li.addEventListener("mouseleave", () => markiere_position(null));
  });
}

function markiere_position(pos) {
  document.querySelectorAll("#vorschau .markierung").forEach((m) => m.remove());
  // E-Rechnung: Zeile im Belegbild hervorheben
  document.querySelectorAll("#vorschau .eb-pos tr.markiert").forEach((z) => z.classList.remove("markiert"));
  const ebZeile = pos == null ? null : document.querySelector(`#vorschau .eb-pos tr[data-pos="${pos}"]`);
  if (ebZeile) { ebZeile.classList.add("markiert"); ebZeile.scrollIntoView({ block: "nearest", behavior: "smooth" }); }
  const rahmen = pos == null ? [] : (zustand.markierungen || [])[pos] || [];
  for (const r of rahmen) {
    const seite = document.querySelector(`#vorschau .seite[data-seite="${r.seite + 1}"]`);
    if (!seite) continue;
    const m = document.createElement("div");
    m.className = "markierung";
    Object.assign(m.style, { left: `${r.x0 * 100}%`, width: `${(r.x1 - r.x0) * 100}%`, top: `${r.y0 * 100}%`, height: `${(r.y1 - r.y0) * 100}%` });
    seite.appendChild(m);
    const v = $("vorschau");
    const oben = seite.offsetTop + seite.offsetHeight * r.y0, unten = seite.offsetTop + seite.offsetHeight * r.y1;
    if (oben < v.scrollTop || unten > v.scrollTop + v.clientHeight) v.scrollTo({ top: oben - v.clientHeight / 3, behavior: "smooth" });
  }
}

// Kontonamen sagen schon „Vorsteuer“ / „Umsatzsteuer“; markiert wird nur der Kreditor
const ART_MARKE = { kreditor: "Kreditor" };

function zeigeBuchungen(b) {
  const bu = b.buchungen;
  const w = bu.waehrung;
  // 1. Vollständiger Buchungssatz: Soll an Haben, mit Vorsteuer (und Umsatzsteuer bei § 13b / i. g. Erwerb)
  const zeile = (z, ersteHaben) => `<tr class="${z.seite === "Haben" ? "haben" : ""} ${ersteHaben ? "an" : ""}">
      <td class="bs-seite">${z.seite === "Soll" ? "Soll" : ersteHaben ? "an Haben" : "Haben"}</td>
      <td><b>${esc(z.konto)}</b></td>
      <td>${esc(z.name)}${ART_MARKE[z.art] ? ` <span class="bs-marke ${z.art}">${ART_MARKE[z.art]}</span>` : ""}${z.aus && z.aus.length
        ? `<small class="bs-aus">aus Automatikkonto ${esc(z.aus.join(", "))}</small>` : ""}</td>
      <td class="zahl-sp">${z.seite === "Soll" ? geld(z.betrag, w) : ""}</td>
      <td class="zahl-sp">${z.seite === "Haben" ? geld(z.betrag, w) : ""}</td></tr>`;
  let erstesHaben = true;
  const zeilen = bu.satz.map((z) => { const an = z.seite === "Haben" && erstesHaben; if (an) erstesHaben = false; return zeile(z, an); }).join("");
  $("buchungssatz").innerHTML = `<thead><tr><th></th><th>Konto</th><th>Bezeichnung</th><th class="zahl-sp">Soll</th><th class="zahl-sp">Haben</th></tr></thead>
    <tbody>${zeilen || `<tr><td colspan="5" class="klein">Noch keine Konten gewählt</td></tr>`}</tbody>
    <tfoot><tr><td colspan="3">${bu.ausgeglichen ? "Summe" : `<span class="kurz-warn">Soll und Haben weichen ab</span>`}</td>
      <td class="zahl-sp">${geld(bu.summe_soll, w)}</td><td class="zahl-sp">${geld(bu.summe_haben, w)}</td></tr></tfoot>`;

  // 2. Zeilen im DATEV-Buchungsstapel: Konto = Kreditor, Gegenkonto = Sachkonto, S/H bezogen auf das Konto
  const stapel = bu.stapel.map((z) => `<tr>
      <td class="zahl-sp">${geld(z.umsatz, z.waehrung)}</td>
      <td title="${z.soll_haben === "H" ? "Kreditor im Haben (Rechnung)" : "Kreditor im Soll (Gutschrift)"}">${z.soll_haben}</td>
      <td>${z.konto ? `<b>${esc(z.konto)}</b><small>${esc(z.konto_name)}</small>` : `<span class="fehlt">Kreditor fehlt</span>`}${z.eu_ustid ? `<small>USt-IdNr. ${esc(z.eu_ustid)}</small>` : ""}</td>
      <td><b>${esc(z.gegenkonto)}</b><small>${esc(z.gegenkonto_name)}</small></td>
      <td>${z.bu ? `<b>${esc(z.bu)}</b>` : "–"}<small>${z.vorsteuer ? `VSt ${geld(z.vorsteuer, z.waehrung)} → ${esc(z.vorsteuer_konto)}` : esc(z.steuer)}</small></td>
      <td>${datum(z.belegdatum)}<small>Leistung ${z.leistungsdatum ? datum(z.leistungsdatum) : "fehlt"}</small></td>
      <td>${esc(z.belegfeld1 || "–")}</td>
    </tr>`).join("");
  $("buchungen").innerHTML = `<thead><tr><th class="zahl-sp">Umsatz</th><th>S/H</th><th>Konto</th><th>Gegenkonto</th><th>BU</th><th>Belegdatum</th><th>Belegfeld 1</th></tr></thead>
    <tbody>${stapel || `<tr><td colspan="7" class="klein">Noch keine Konten gewählt</td></tr>`}</tbody>`;

  const hinweise = {
    "13b": "Umsatz netto: DATEV bucht Vorsteuer und Umsatzsteuer nach § 13b gleichzeitig; im Saldo keine Zahllast.",
    ige: "Umsatz netto: DATEV bucht Vorsteuer und Umsatzsteuer aus dem innergemeinschaftlichen Erwerb gleichzeitig.",
    ausland: "Ausländische Umsatzsteuer ist in Deutschland keine Vorsteuer: Brutto in den Aufwand. Erstattung nur über das Vorsteuer-Vergütungsverfahren (BZSt).",
  };
  $("buchungen-hinweis").textContent = (hinweise[b.steuerfall.id] || "")
    + (w !== "EUR" ? ` Beträge in ${w}: vor dem Export in Euro umrechnen (Kurs zum Leistungsdatum).` : "");
  const bus = [...new Set(bu.stapel.map((z) => z.bu ? `BU ${z.bu}` : "ohne BU"))];
  $("kurz-buchungen").innerHTML = bu.stapel.length
    ? `Soll ${geld(bu.summe_soll, w)} = Haben ${geld(bu.summe_haben, w)} · ${esc(bus.join(", "))}`
      + (b.kreditor ? "" : ` · <span class="kurz-warn">Kreditor fehlt</span>`)
    : `<span class="kurz-warn">noch keine Konten</span>`;
}

/* Rechnungsprüfung: Pflichtangaben nach § 14 UStG, §§ 31, 33 UStDV, § 14a UStG */
const PFLICHT_STATUS = { ok: ["✓", "ok", ""], fehlt: ["!", "fehlt", "fehlt"], hinweis: ["i", "hinweis", "fehlt (nur Hinweis)"],
  entfaellt: ["–", "entfaellt", "nicht nötig"] };

function zeigePruefung(b) {
  const pf = b.pflichtangaben;
  $("pflicht-liste").innerHTML = pf.punkte.map((p) => {
    // Kurz: Punkt, Haken, „vorhanden“ – die Rechtsgrundlage nur beim Überfahren
    const [zeichen, klasse, wort] = PFLICHT_STATUS[p.status];
    const wert = p.status !== "ok" ? "" : p.key === "datum" ? datum(p.detail) : p.detail;
    return `<li class="${klasse}" title="${esc(p.grundlage)}"><span class="pf-zeichen">${zeichen}</span>
      <span>${esc(p.text)} <span class="pf-wort">${wort}</span></span><span class="pf-wert">${esc(wert)}</span></li>`;
  }).join("");
  const fehlt = pf.punkte.filter((p) => p.status === "fehlt").length;
  const hinweis = pf.punkte.filter((p) => p.status === "hinweis").length;
  const val = b.validierung;
  const quelle = pf.e_rechnung ? "E-Rechnung, strukturiert geprüft" : "aus dem Belegtext geprüft";
  zeigeValidierung(val);
  const valKurz = !val ? "" : val.gueltig ? `<span class="kurz-ok">✓ XRechnung gültig</span> · `
    : val.gueltig === false ? `<span class="kurz-fehler">✗ E-Rechnung ungültig</span> · ` : "";
  $("kurz-pruefung").innerHTML = valKurz + (fehlt ? `<span class="kurz-warn">${anzahl(fehlt, "Angabe fehlt", "Angaben fehlen")}</span>`
    : `<span class="kurz-ok">✓ ${pf.art === "kleinbetrag" ? "Kleinbetragsrechnung vollständig" : "Alle Pflichtangaben vorhanden"}</span>`
      + (hinweis ? ` · ${anzahl(hinweis, "Hinweis", "Hinweise")}` : "") + (val ? "" : ` · ${quelle}`));
  $("pflicht-hinweis").textContent = [pf.art === "kleinbetrag" ? "Kleinbetragsrechnung bis 250 €: weniger Angaben nötig." : "",
    b.steuerfall.id === "13b" ? "Reverse Charge: fehlende Angaben gefährden den Vorsteuerabzug nicht." : "",
    fehlt ? "Was tun? Beim Lieferanten eine berichtigte Rechnung anfordern." : ""].filter(Boolean).join(" ");
  if ((fehlt || (val && val.gueltig === false)) && b.status !== "freigegeben") setzeKlapp("pruefung", true);  // offen lassen
}

/* XRechnung-Validierung mit den offiziellen KoSIT-Prüfregeln (Schema, EN 16931, XRechnung) */
function zeigeValidierung(val) {
  const el = $("validierung");
  el.hidden = !val;
  if (!val) return;
  if (!val.verfuegbar) { el.className = "validierung grau"; el.innerHTML = `<b>XRechnung-Validierung nicht eingerichtet</b><small>${esc(val.hinweis)}</small>`; return; }
  // Für Sachbearbeiter: kurze deutsche Sätze, jeder nur einmal. Regelnummern und Originaltext unter „Technische Details“.
  const saetze = (eintraege) => [...new Set(eintraege.map((e) => e.klartext || e.text))];
  const punkte = (eintraege, art) => saetze(eintraege).map((s) => `<li class="${art}">${esc(s)}</li>`).join("");
  const technik = [...val.fehler.map((e) => ["Fehler", e]), ...val.warnungen.map((e) => ["Hinweis", e])]
    .map(([art, e]) => `<li><b>${esc(e.regel)}</b> <span class="klein">${art}</span><br>${esc(e.text)}${e.ort ? `<small>${esc(e.ort)}</small>` : ""}</li>`).join("");
  el.className = `validierung ${val.gueltig ? "gut" : "schlecht"}`;
  el.innerHTML = `<div class="val-kopf"><span class="val-zeichen">${val.gueltig ? "✓" : "✗"}</span>
      <span><b>${val.gueltig ? "E-Rechnung ist gültig" : "E-Rechnung ist ungültig"}</b>
      <small>${val.gueltig ? "Geprüft nach den offiziellen Regeln für XRechnung 3.0" : "Das ist fehlerhaft:"}</small></span></div>
    ${val.fehler.length ? `<ul class="val-liste">${punkte(val.fehler, "fehler")}</ul>` : ""}
    ${val.warnungen.length ? `<div class="val-hinweise">Hinweise (kein Fehler):</div><ul class="val-liste">${punkte(val.warnungen, "warnung")}</ul>` : ""}
    ${val.gueltig ? "" : `<p class="val-tun"><b>Was tun?</b> Beim Lieferanten eine korrigierte E-Rechnung anfordern.</p>`}
    ${technik ? `<details class="val-technik"><summary>Technische Details</summary>
      <p class="klein">${esc(val.szenario || "kein passendes Prüfszenario")} · ${esc(val.regelwerk)}</p><ul>${technik}</ul></details>` : ""}`;
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
    $("kurz-kreditor").innerHTML = `<b>${esc(b.kreditor.nr)}</b> · ${esc(b.kreditor.name)}` + (b.kreditor.ustid ? ` · ${esc(b.kreditor.ustid)}` : "")
      + (b.regeln.length ? ` · ${anzahl(b.regeln.length, "Regel", "Regeln")}` : "");
    const kr = b.kreditor, ausRechnung = b.kopf.lieferant_ustid && b.kopf.lieferant_ustid !== kr.ustid;
    el.innerHTML = `<div class="kreditor-ustid">
        <span><span class="klein">USt-IdNr.</span> <b>${esc(kr.ustid || "–")}</b> <span class="klein">· Land</span> <b>${esc(kr.land || "–")}</b></span>
        ${fertig ? "" : `<button class="link blau-link klein-link" id="k-ustid-aendern">ändern</button>`}
        ${ausRechnung && !fertig ? `<button class="link blau-link klein-link" id="k-ustid-uebernehmen">${esc(b.kopf.lieferant_ustid)} aus der Rechnung übernehmen</button>` : ""}
      </div>
      <div class="kreditor-ustid-form" hidden>
        <input class="feld" id="k-ustid" value="${esc(kr.ustid || "")}" placeholder="USt-IdNr., z. B. NL999999042B01">
        <input class="feld" id="k-land" value="${esc(kr.land || "")}" placeholder="Land" maxlength="2">
        <button class="knopf blau klein-knopf" id="k-ustid-ok">Sichern</button>
      </div>
      <div class="unter-titel">${b.regeln.length ? "Gelernte Regeln" : `Gelernte Regeln <span class="klein">noch keine</span>`}</div>
      <div class="regeln">${regeln}</div>`;
    el.querySelectorAll("input[data-regel]").forEach((i) => i.addEventListener("change", async () => {
      try {
        const neu = await post("/api/regel/aktiv", { key: b.key, regel: i.dataset.regel, aktiv: i.checked, modell: zustand.modell });
        zeigeBeleg(neu); setzeKlapp("kreditor", true); ladeListe();
        toast(i.checked ? "Regel eingeschaltet" : "Regel abgeschaltet – Konto kommt wieder von der KI");
      } catch (e) { toast(e.message, true); }
    }));
    const ustidSenden = async (ustid, land) => {
      try {
        zeigeBeleg(await post("/api/beleg/kreditor/daten", { key: b.key, ustid, land, modell: zustand.modell }));
        setzeKlapp("kreditor", true); ladeListe(); toast("USt-IdNr. und Land beim Kreditor gespeichert");
      } catch (e) { toast(e.message, true); }
    };
    el.querySelector("#k-ustid-aendern")?.addEventListener("click", () => { el.querySelector(".kreditor-ustid-form").hidden = false; });
    el.querySelector("#k-ustid-ok")?.addEventListener("click", () => ustidSenden($("k-ustid").value, $("k-land").value));
    el.querySelector("#k-ustid-uebernehmen")?.addEventListener("click", () => ustidSenden(b.kopf.lieferant_ustid, b.kopf.lieferant_ustid.slice(0, 2)));
    return;
  }
  const v = b.kreditor_vorschlag;
  $("kurz-kreditor").innerHTML = `<span class="kurz-warn">Kreditor anlegen</span>`;
  if (!fertig) setzeKlapp("kreditor", true);  // braucht eine Aktion: immer offen
  el.innerHTML = `<div class="kreditor-neu">
      <label title="Nummernkreis ${v.von}–${v.bis}. Vorgeschlagen ist die nächste freie Nummer.">Kreditorennummer<input id="k-nr" class="feld" inputmode="numeric" value="${v.nr}" ${fertig ? "disabled" : ""}></label>
      <label>Name<input id="k-name" class="feld" value="${esc(v.name || "")}" ${fertig ? "disabled" : ""}></label>
      <button id="k-knopf" class="knopf blau" ${fertig ? "disabled" : ""}>Anlegen</button>
    </div>`;
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

function vollbild(an) {
  document.querySelector(".vorschau-rahmen").classList.toggle("vollbild", an);
  $("w-vollbild").innerHTML = svg(an ? "vollbild_aus" : "vollbild");
  $("w-vollbild").title = an ? "Vollbild beenden (Esc)" : "Vollbild";
}

function leereVorschau() {
  vollbild(false);
  $("vorschau").innerHTML = `<p class="klein mitte">Keine Rechnung gewählt</p>`;
  $("v-seiten").textContent = "";
  $("werkzeuge").hidden = true;
}

async function ladeVorschau(b) {
  const v = $("vorschau");
  ansichtZ.zoom = 1;
  v.classList.toggle("xml", b.art === "xml");  // ohne Werkzeugleiste: volle Breite
  if (b.art === "xml") {
    // Belegbild aus dem XML; das Original-XML bleibt aufklappbar darunter (maßgeblich ist das XML)
    const q = new URLSearchParams({ key: b.key });
    const [bild, xml] = await Promise.all([api(`/api/beleg/belegbild?${q}`).catch(() => null),
      fetch(`/api/beleg/datei?${q}`, { headers: { "X-Nutzer": zustand.nutzer } }).then((r) => r.text())]);
    if (zustand.key !== b.key) return;  // inzwischen andere Rechnung gewählt
    v.innerHTML = (bild ? belegbildHtml(bild) : `<p class="klein">Belegbild nicht verfügbar.</p>`)
      + `<details class="eb-xml" ${bild ? "" : "open"}><summary>Original-XML</summary><pre>${esc(xml)}</pre></details>`;
    $("v-seiten").textContent = bild ? bild.format : "E-Rechnung (XML)";
    $("werkzeuge").hidden = true;
    return;
  }
  const { anzahl: n } = await api(`/api/beleg/seiten?${new URLSearchParams({ key: b.key })}`);
  zustand.markierungen = [];
  api(`/api/beleg/markierungen?${new URLSearchParams({ key: b.key, modell: zustand.modell })}`)
    .then((m) => { if (zustand.key === b.key) zustand.markierungen = m; }).catch(() => {});
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

/* Belegbild einer E-Rechnung: aus dem XML aufbereitet wie eine Papierrechnung, für die Sichtprüfung */
function belegbildHtml(e) {
  const w = e.waehrung;
  const v = e.verkaeufer, k = e.kaeufer, z = e.zahlung;
  const anschrift = (p) => [p.street, [p.postcode, p.city].filter(Boolean).join(" "), p.country && p.country !== "DE" ? p.country : ""]
    .filter(Boolean).map(esc).join("<br>");
  const zeile = (label, wert) => wert ? `<tr><td>${label}</td><td>${wert}</td></tr>` : "";
  const kontakt = [v.contact, v.phone, v.email].filter(Boolean).map(esc).join(" · ");
  const positionen = e.positionen.map((p, i) => `<tr data-pos="${i}">
      <td>${esc(p.nr && p.nr !== p.bezeichnung && p.nr.length <= 8 ? p.nr : i + 1)}</td>
      <td><b>${esc(p.bezeichnung || "–")}</b>${p.beschreibung && p.beschreibung !== p.bezeichnung ? `<small>${esc(p.beschreibung)}</small>` : ""}</td>
      <td class="zahl-sp">${p.menge ? `${esc(Number(p.menge).toLocaleString("de-DE"))} ${esc(p.einheit || "")}` : ""}</td>
      <td class="zahl-sp">${geld(p.einzelpreis, w)}</td>
      <td class="zahl-sp">${esc(p.satz)} %</td>
      <td class="zahl-sp">${geld(p.netto, w)}</td></tr>`).join("");
  const zuschlaege = e.zuschlaege.map((a) => `<tr><td></td><td>${esc(a.art)}${a.grund ? `: ${esc(a.grund)}` : ""}</td><td></td><td></td>
      <td class="zahl-sp">${esc(a.satz)} %</td><td class="zahl-sp">${a.art === "Abschlag" ? "− " : ""}${geld(a.betrag, w)}</td></tr>`).join("");
  const zahlung = [z.art && `<b>${esc(z.art)}</b>`, z.bedingungen && esc(z.bedingungen),
    z.iban && `IBAN ${esc(z.iban)}${z.bic ? ` · BIC ${esc(z.bic)}` : ""}`, z.inhaber && `Kontoinhaber ${esc(z.inhaber)}`,
    z.verwendungszweck && `Verwendungszweck ${esc(z.verwendungszweck)}`].filter(Boolean);
  const fuss = [v.vat_id && `USt-IdNr. ${esc(v.vat_id)}`, v.steuernummer && `Steuernummer ${esc(v.steuernummer)}`, v.register && esc(v.register)]
    .filter(Boolean).join(" · ");
  return `<article class="eb-blatt">
    <header class="eb-kopf">
      <div><b class="eb-name">${esc(v.name || "–")}</b><div>${anschrift(v)}</div>${kontakt ? `<small>${kontakt}</small>` : ""}</div>
      <div class="eb-art"><b>${esc(e.art)}</b><small>E-Rechnung</small></div>
    </header>
    <div class="eb-empfaenger"><small>Rechnungsempfänger</small><b>${esc(k.name || "–")}</b><div>${anschrift(k)}</div></div>
    <table class="eb-daten">
      ${zeile("Rechnungsnummer", esc(e.nummer))}${zeile("Rechnungsdatum", datum(e.datum))}
      ${zeile("Leistung", e.leistung ? esc(leistungText(e.leistung, true)) : "")}${zeile("Fällig am", e.faellig ? datum(e.faellig) : "")}
      ${e.referenzen.map((r) => zeile(esc(r.label), esc(r.wert))).join("")}${w !== "EUR" ? zeile("Währung", esc(w)) : ""}
    </table>
    <table class="eb-pos"><thead><tr><th>Pos.</th><th>Bezeichnung</th><th class="zahl-sp">Menge</th><th class="zahl-sp">Einzelpreis</th>
      <th class="zahl-sp">USt</th><th class="zahl-sp">Netto</th></tr></thead><tbody>${positionen}${zuschlaege}</tbody></table>
    <table class="eb-summen">${e.summen.map((s) => `<tr class="${s.fett ? "fett" : ""}"><td>${esc(s.label)}</td>
      <td class="zahl-sp">${geld(s.betrag, w)}</td></tr>`).join("")}</table>
    <table class="eb-steuern"><thead><tr><th>Umsatzsteuer</th><th class="zahl-sp">Satz</th><th class="zahl-sp">Grundlage</th><th class="zahl-sp">Steuer</th></tr></thead>
      <tbody>${e.steuern.map((s) => `<tr><td>${esc(s.kategorie)}${s.grund ? `<small>${esc(s.grund)}</small>` : ""}</td>
        <td class="zahl-sp">${esc(s.satz)} %</td><td class="zahl-sp">${geld(s.basis, w)}</td><td class="zahl-sp">${geld(s.betrag, w)}</td></tr>`).join("")}</tbody></table>
    ${zahlung.length ? `<div class="eb-block"><small>Zahlung</small>${zahlung.map((t) => `<div>${t}</div>`).join("")}</div>` : ""}
    ${e.hinweise.length ? `<div class="eb-block"><small>Hinweise</small>${e.hinweise.map((h) => `<p>${esc(h)}</p>`).join("")}</div>` : ""}
    ${fuss ? `<footer class="eb-fuss">${fuss}</footer>` : ""}
  </article>`;
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
  $("w-zoom").addEventListener("click", () => { ansichtZ.zoom = 1; wendeZoomAn(); });
  // Vollbild: Beleg über das ganze Fenster (ohne Fullscreen-API, die eingebettete Browser oft sperren); Esc beendet es
  $("w-vollbild").addEventListener("click", () => vollbild(!document.querySelector(".vorschau-rahmen.vollbild")));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && document.querySelector(".vorschau-rahmen.vollbild")) vollbild(false); });
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
