"use strict";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const eur = (v) => v == null || v === "" ? "–" : Number(v).toLocaleString("de-DE", { style: "currency", currency: "EUR" });
const datum = (iso) => iso && /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso.split("-").reverse().join(".") : (iso || "–");
const AMPEL = { gruen: "Sicher", gelb: "Unsicher", rot: "Frei" };
const STATUS = { gruen: "Bereit zur Freigabe", gelb: "Bitte prüfen", rot: "Unvollständig" };

const zustand = { filter: "offen", mandant: "", suche: "", modell: "", key: null, beleg: null, liste: null, stamm: null };

async function api(url, opts = {}) {
  const r = await fetch(url, opts);
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
  toast.timer = setTimeout(() => { t.hidden = true; }, 2600);
}

/* ---------- Start ---------- */
async function init() {
  zustand.stamm = await api("/api/stammdaten");
  zustand.modell = zustand.stamm.standard_modell;
  for (const m of zustand.stamm.modelle) $("modell").add(new Option(m.kurz, m.id, false, m.id === zustand.modell));
  for (const m of zustand.stamm.mandanten) $("mandant").add(new Option(`${m.name} · ${m.branche}`, m.id));

  document.querySelectorAll(".segment button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".segment button").forEach((x) => x.classList.toggle("aktiv", x === b));
    zustand.filter = b.dataset.filter;
    zeigeListe();
  }));
  $("mandant").addEventListener("change", (e) => { zustand.mandant = e.target.value; ladeListe(); });
  $("suche").addEventListener("input", (e) => { zustand.suche = e.target.value.toLowerCase(); zeigeListe(); });
  $("modell").addEventListener("change", async (e) => {
    zustand.modell = e.target.value;
    await ladeListe();
    if (zustand.key) oeffne(zustand.key, false);
  });
  $("datei").addEventListener("change", hochladen);
  $("reset").addEventListener("click", async () => {
    if (!confirm("Alle Kreditoren, Kontoänderungen und Freigaben der Demo löschen?")) return;
    await post("/api/demo/zuruecksetzen", {});
    zustand.key = null; $("beleg").hidden = true; $("aktionsleiste").hidden = true; $("leer").hidden = false;
    await ladeListe();
    toast("Demo zurückgesetzt");
  });
  $("a-knopf").addEventListener("click", aktion);
  document.addEventListener("click", (e) => { if (!e.target.closest(".konto-feld, .dropdown")) schliesseDropdown(); });
  await ladeListe();
}

/* ---------- Liste ---------- */
async function ladeListe() {
  const q = new URLSearchParams({ modell: zustand.modell });
  if (zustand.mandant) q.set("mandant", zustand.mandant);
  zustand.liste = await api("/api/eingang?" + q);
  zeigeListe();
  if (!zustand.liste.bereit) setTimeout(ladeListe, 2000);
}

function zeigeListe() {
  const l = zustand.liste;
  if (!l) return;
  $("z-offen").textContent = l.anzahl_offen;
  $("z-erledigt").textContent = l.anzahl_erledigt;
  $("summe").innerHTML = zustand.filter === "offen"
    ? `<b>${l.anzahl_offen}</b> Rechnungen zu verbuchen · ${eur(l.summe_offen)}` + (l.bereit ? "" : " · <i>werden gelesen …</i>")
    : `<b>${l.anzahl_erledigt}</b> Rechnungen freigegeben`;
  const eintraege = l.eintraege.filter((e) => e.status === zustand.filter)
    .filter((e) => !zustand.suche || (e.lieferant || "").toLowerCase().includes(zustand.suche));
  $("liste").innerHTML = eintraege.map((e) => {
    if (!e.bereit) return `<li class="zelle"><span class="punkt grau"></span><span class="z1">${esc(e.id)} wird gelesen …</span><span></span>
      <span class="z2">${esc(e.mandant)}</span></li>`;
    const art = { xml: "E-Rechnung", scan: "Scan", foto: "Foto", pdf: "PDF" }[e.art] || e.art;
    return `<li class="zelle ${e.key === zustand.key ? "gewaehlt" : ""}" data-key="${esc(e.key)}">
      <span class="punkt ${e.status === "freigegeben" ? "grau" : e.ampel}"></span>
      <span class="z1">${esc(e.lieferant || e.id)}</span>
      <span class="z-betrag">${eur(e.brutto)}</span>
      <span class="z2"><span>${esc(e.mandant)}</span><span>· ${datum(e.datum)}</span>
        ${e.kreditor ? `<span class="marke">Kreditor ${esc(e.kreditor)}</span>` : `<span class="marke neu">Neuer Lieferant</span>`}
        <span class="marke">${art}</span>${e.frei ? `<span class="marke neu">${e.frei} ohne Konto</span>` : ""}</span>
    </li>`;
  }).join("") || `<li class="klein mitte">Keine Rechnungen</li>`;
  $("liste").querySelectorAll(".zelle[data-key]").forEach((z) => z.addEventListener("click", () => oeffne(z.dataset.key)));
  $("konto-liste").innerHTML = l.nach_konto.map((g) => `<li><b>${esc(g.nr)}</b><span>${esc(g.name)}</span>
    <span class="klein">${g.anzahl}× · ${eur(g.summe)}</span></li>`).join("") || `<li class="klein">Alles verbucht</li>`;
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
  const chip = $("b-status");
  chip.className = "status-chip " + (fertig ? "fertig" : b.ampel);
  chip.innerHTML = fertig ? "✓ Freigegeben" : `<span class="punkt ${b.ampel}"></span>${STATUS[b.ampel]}`;
  const k = b.kopf;
  $("b-lieferant").textContent = k.supplier_name || "Unbekannter Lieferant";
  $("b-meta").textContent = [b.mandant.name, k.invoice_number ? `Rechnung ${k.invoice_number}` : "ohne Rechnungsnummer",
    datum(k.invoice_date), k.document_type === "credit_note" ? "Gutschrift" : null, k.reverse_charge ? "Reverse Charge" : null]
    .filter(Boolean).join(" · ");
  $("b-brutto").textContent = eur(k.gross_total);
  $("b-steuer").textContent = `Netto ${eur(k.net_total)} · USt ${eur(k.tax_total)}`;

  zeigeKreditor(b, fertig);

  const sicher = b.positionen.filter((p) => p.ampel === "gruen").length;
  $("b-pos-info").textContent = `${b.positionen.length} Positionen · ${sicher} sicher`;
  $("positionen").innerHTML = b.positionen.map((p) => `
    <li class="position">
      <div class="p-text">${esc(p.bezeichnung || "Position " + (p.pos + 1))}
        <small>${p.menge ? esc(Number(p.menge).toLocaleString("de-DE")) + " " + esc(p.einheit || "") : ""}</small></div>
      <div class="p-betrag">${eur(p.netto)}<small>${p.steuersatz ?? "–"} % USt</small></div>
      <div class="p-konto">
        <div class="konto-feld ${p.ampel}">
          <input data-pos="${p.pos}" ${fertig ? "disabled" : ""} autocomplete="off"
            value="${p.konto ? esc(p.konto.nr + " · " + p.konto.name) : ""}"
            placeholder="Konto wählen: Nummer oder Begriff, z. B. „War“">
        </div>
        <div class="ampel ${p.ampel}" title="${esc(p.grund)}"><span class="punkt ${p.ampel}"></span>
          <span><b>${AMPEL[p.ampel]}</b><br>${esc(p.grund)}</span></div>
      </div>
    </li>`).join("");
  $("positionen").querySelectorAll("input[data-pos]").forEach(bindeKontoFeld);

  $("kopf").innerHTML = [["Lieferant", esc(k.supplier_name)], ["Rechnungsnummer", esc(k.invoice_number ?? "–")],
    ["Rechnungsdatum", datum(k.invoice_date)], ["Netto", eur(k.net_total)], ["Umsatzsteuer", eur(k.tax_total)],
    ["Brutto", eur(k.gross_total)], ["Reverse Charge / i. g. Erwerb", k.reverse_charge ? "ja" : "nein"],
    ["Steuerlogik", b.steuerlogik.ok ? "Netto + Steuer = Brutto ✓" : "Widerspruch: " + esc(b.steuerlogik.hinweise.join(", "))],
    ["Mandant", esc(b.mandant.name + " · " + b.mandant.branche)]].map(([a, c]) => `<tr><td>${a}</td><td>${c}</td></tr>`).join("");
  $("schritte").innerHTML = b.schritte.map((s) => `<li title="${esc(s.detail)}">${esc(s.name)} · ${s.dauer_s.toLocaleString("de-DE")} s</li>`).join("");
  $("ki").innerHTML = b.ki.art === "aufzeichnung"
    ? `${esc(b.ki.modell)}: Antwort aus dem Messlauf (damals ${Number(b.ki.laufzeit_s).toLocaleString("de-DE", { maximumFractionDigits: 1 })} s,
       ${(b.ki.kosten_eur * 100).toLocaleString("de-DE", { maximumFractionDigits: 2 })} Cent), heute ohne Kosten abgespielt.`
    : esc(b.ki.text);
  $("soll").innerHTML = b.soll ? `Abgleich mit dem Sollwert: Pflichtfelder ${b.soll.pflichtfelder.join("/")} · Positionen ${b.soll.positionen.join("/")}`
    + (b.soll.konten[1] ? ` · Sachkonten der KI ${b.soll.konten.join("/")}` : "") : "";
  $("pseudo").hidden = !b.pseudonymisiert;
  const n = Object.values(b.platzhalter).reduce((a, c) => a + c, 0);
  $("pseudo-zahl").textContent = n ? `${n} Angaben ersetzt` : "";
  $("pseudo-text").innerHTML = esc(b.pseudonymisiert).replace(/\[[A-Z_]+_\d+\]/g, (m) => `<mark>${m}</mark>`);
  $("verlauf").innerHTML = b.protokoll.slice().reverse().map((e) => `<li><b>${esc(e.feld)}</b>: ${esc(e.alt ?? "–")} → ${esc(e.neu ?? "–")}
    <br>${new Date(e.zeit).toLocaleString("de-DE")} · ${esc(e.nutzer)}</li>`).join("") || `<li>Noch keine Änderungen</li>`;

  const knopf = $("a-knopf");
  if (fertig) {
    knopf.textContent = "Wieder öffnen";
    knopf.className = "knopf grau gross";
    knopf.disabled = false;
    $("a-hinweis").innerHTML = `Freigegeben am ${new Date(b.freigegeben_am).toLocaleString("de-DE")} · Kreditor ${esc(b.kreditor?.nr)}`;
  } else {
    knopf.textContent = "Freigeben";
    knopf.className = "knopf blau gross";
    knopf.disabled = !b.freigabe_moeglich;
    $("a-hinweis").innerHTML = b.freigabe_moeglich
      ? (b.ampel === "gruen" ? "Alles sicher erkannt." : "Freigabe möglich – gelbe Positionen bitte kurz prüfen.")
      : "Noch offen: " + b.offen.map(esc).join(" · ");
  }
}

function zeigeKreditor(b, fertig) {
  const el = $("kreditor-karte");
  if (b.kreditor) {
    el.innerHTML = `<div class="kreditor"><div><div class="klein">Kreditor</div><div class="nr">${esc(b.kreditor.nr)}</div></div>
      <div><div>${esc(b.kreditor.name)}</div><div class="klein">fest zugeordnet für ${esc(b.mandant.name)}</div></div></div>`;
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

/* ---------- Kontoauswahl ---------- */
let dd = { input: null, eintraege: [], aktiv: 0, timer: null };

function bindeKontoFeld(input) {
  input.addEventListener("focus", () => { input.select(); zeigeDropdown(input, ""); });
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
  const q = text.includes("·") ? "" : text.trim();
  const vorschlaege = pos.vorschlaege;
  const treffer = q ? await api("/api/konten?" + new URLSearchParams({ q })) : [];
  dd = { ...dd, input, eintraege: [...(q ? [] : vorschlaege), ...treffer], aktiv: 0 };
  const zeile = (k, i) => `<div class="dd-eintrag" data-i="${i}"><b>${esc(k.nr)}</b><span>${esc(k.name)}${k.kennzeichen ? `<span class="kennz">${esc(k.kennzeichen)}</span>` : ""}</span>
    ${k.quelle ? `<small class="quelle">${esc(k.quelle)}</small>` : ""}</div>`;
  let html = "";
  if (!q) html += `<div class="dd-titel">Vorschläge</div>` + (vorschlaege.map(zeile).join("") || `<div class="dd-leer">Keine Vorschläge – tippen Sie eine Nummer oder einen Begriff</div>`);
  if (q) html += `<div class="dd-titel">Konten im SKR03</div>` + (treffer.map((k, i) => zeile(k, i)).join("") || `<div class="dd-leer">Kein Konto zu „${esc(q)}“</div>`);
  const d = $("dropdown");
  d.innerHTML = html;
  const r = input.getBoundingClientRect();
  d.style.left = r.left + "px";
  d.style.width = Math.max(r.width, 380) + "px";
  const unten = window.innerHeight - r.bottom;
  if (unten < 260) { d.style.top = ""; d.style.bottom = (window.innerHeight - r.top + 6) + "px"; }
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

function schliesseDropdown() { $("dropdown").hidden = true; dd.input = null; }

async function waehle(nr) {
  const pos = Number(dd.input.dataset.pos);
  schliesseDropdown();
  try {
    const b = await post("/api/beleg/konto", { key: zustand.key, pos, nr, modell: zustand.modell });
    zeigeBeleg(b); ladeListe();
    const naechstes = $("positionen").querySelector(".konto-feld.rot input, .konto-feld.gelb input");
    toast(`Position ${pos + 1}: Konto ${nr} übernommen`);
    if (naechstes && Number(naechstes.dataset.pos) > pos) naechstes.focus();
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
    await post("/api/beleg/freigeben", { key: b.key, modell: zustand.modell });
    toast(`${b.kopf.supplier_name}: freigegeben`);
    const offen = zustand.liste.eintraege.filter((e) => e.status === "offen" && e.bereit && e.key !== b.key);
    await ladeListe();
    if (offen.length) oeffne(offen[0].key); else oeffne(b.key);
  } catch (e) { toast(e.message, true); }
}

/* ---------- Beleg ---------- */
async function ladeVorschau(b) {
  const v = $("vorschau");
  if (b.art === "xml") {
    const t = await (await fetch(`/api/beleg/datei?${new URLSearchParams({ key: b.key })}`)).text();
    v.innerHTML = `<pre>${esc(t)}</pre>`;
    $("v-seiten").textContent = "E-Rechnung (XML)";
    return;
  }
  const { anzahl } = await api(`/api/beleg/seiten?${new URLSearchParams({ key: b.key })}`);
  $("v-seiten").textContent = `${anzahl} Seite${anzahl === 1 ? "" : "n"}`;
  v.innerHTML = [...Array(anzahl).keys()].map((i) =>
    `<img src="/api/beleg/seite?${new URLSearchParams({ key: b.key, i })}" alt="Seite ${i + 1}">`).join("");
}

async function hochladen(e) {
  const datei = e.target.files[0];
  if (!datei) return;
  const form = new FormData();
  form.append("datei", datei);
  form.append("mandant", zustand.mandant || zustand.stamm.mandanten[0].id);
  try {
    const r = await fetch("/api/upload", { method: "POST", body: form });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail);
    toast("Rechnung wird gelesen …");
    await ladeListe();
    await oeffne(d.key);
  } catch (err) { toast(err.message, true); }
  e.target.value = "";
}

init();
