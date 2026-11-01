"use strict";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const eur = (v) => v == null || v === "" ? "–" : Number(v).toLocaleString("de-DE", { style: "currency", currency: "EUR" });
const datum = (iso) => iso && /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso.split("-").reverse().join(".") : (iso || "–");
const prozent = (x) => `${Math.round((x || 0) * 100)} %`;
const AMPEL = { gruen: "Sicher", gelb: "Unsicher", rot: "Frei" };
const anzahl = (n, eins, mehr) => `${n} ${n === 1 ? eins : mehr}`;
const BEREICH_TEXT = {
  sicher: (n, s) => `<b>${anzahl(n, "Rechnung", "Rechnungen")}</b> sicher vorkontiert · ${eur(s)}`,
  pruefen: (n, s) => `<b>${anzahl(n, "Rechnung", "Rechnungen")}</b> zur Prüfung · ${eur(s)}`,
  erledigt: (n) => `<b>${anzahl(n, "Rechnung", "Rechnungen")}</b> freigegeben`,
};

const zustand = { filter: "sicher", mandant: "", suche: "", modell: "", key: null, beleg: null, liste: null, stamm: null, erstesLaden: true };

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
  toast.timer = setTimeout(() => { t.hidden = true; }, 2800);
}

/* ---------- Start ---------- */
async function init() {
  zustand.stamm = await api("/api/stammdaten");
  zustand.modell = zustand.stamm.standard_modell;
  for (const m of zustand.stamm.modelle) $("modell").add(new Option(m.kurz, m.id, false, m.id === zustand.modell));
  for (const m of zustand.stamm.mandanten) $("mandant").add(new Option(`${m.name} · ${m.branche}`, m.id));

  document.querySelectorAll(".segment button").forEach((b) => b.addEventListener("click", () => setzeFilter(b.dataset.filter)));
  $("mandant").addEventListener("change", (e) => { zustand.mandant = e.target.value; ladeListe(); });
  $("suche").addEventListener("input", (e) => { zustand.suche = e.target.value.toLowerCase(); zeigeListe(); });
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
  $("demo-knopf").addEventListener("click", (e) => { e.stopPropagation(); $("demo-liste").hidden = !$("demo-liste").hidden; });
  document.querySelectorAll("#demo-liste button").forEach((b) => b.addEventListener("click", () => demoAktion(b.dataset.demo)));
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".konto-feld, .dropdown")) schliesseDropdown();
    if (!e.target.closest(".demo-menue")) $("demo-liste").hidden = true;
  });
  await ladeListe();
}

function setzeFilter(f) {
  zustand.filter = f;
  document.querySelectorAll(".segment button").forEach((x) => x.classList.toggle("aktiv", x.dataset.filter === f));
  zeigeListe();
}

/* ---------- Liste ---------- */
async function ladeListe() {
  const q = new URLSearchParams({ modell: zustand.modell });
  if (zustand.mandant) q.set("mandant", zustand.mandant);
  zustand.liste = await api("/api/eingang?" + q);
  if (zustand.erstesLaden && zustand.liste.bereit) {
    zustand.erstesLaden = false;
    if (!zustand.liste.anzahl.sicher) setzeFilter("pruefen");
  }
  zeigeListe();
  if (!zustand.liste.bereit) setTimeout(ladeListe, 2000);
}

function zelle(e) {
  if (!e.bereit) return `<li class="zelle"><span class="punkt grau"></span><span class="z1">${esc(e.id)} wird gelesen …</span><span></span>
    <span class="z2">${esc(e.mandant)}</span></li>`;
  const art = { xml: "E-Rechnung", scan: "Scan", foto: "Foto", pdf: "PDF" }[e.art] || e.art;
  const marken = [];
  if (e.bereich === "sicher") marken.push(`<span class="marke gruen">Sicher ${prozent(e.sicherheit)}</span>`);
  for (const a of e.ausnahmen || []) marken.push(`<span class="marke orange">${esc(a.split(" (")[0])}</span>`);
  if (e.gelernt) marken.push(`<span class="marke blau">${e.gelernt}/${e.positionen} gelernt</span>`);
  if (e.frei) marken.push(`<span class="marke orange">${e.frei} ohne Konto</span>`);
  if (e.kreditor) marken.push(`<span class="marke">Kreditor ${esc(e.kreditor)}</span>`);
  marken.push(`<span class="marke">${art}</span>`);
  return `<li class="zelle ${e.key === zustand.key ? "gewaehlt" : ""}" data-key="${esc(e.key)}">
    <span class="punkt ${e.bereich === "erledigt" ? "grau" : e.ampel}"></span>
    <span class="z1">${esc(e.lieferant || e.id)}</span>
    <span class="z-betrag">${eur(e.brutto)}</span>
    <span class="z2"><span>${esc(e.mandant)} · ${datum(e.datum)}</span>${marken.join("")}</span>
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
  const sammel = $("sammel");
  sammel.hidden = !(f === "sicher" && l.anzahl.sicher > 0);
  $("sammel-zahl").textContent = `${l.anzahl.sicher} sicher vorkontiert`;
  $("sammel-text").textContent = "Nur ansehen und freigeben";

  const eintraege = l.eintraege.filter((e) => e.bereich === f)
    .filter((e) => !zustand.suche || (e.lieferant || "").toLowerCase().includes(zustand.suche));
  const leer = { sicher: "Keine sicher vorkontierten Rechnungen.", pruefen: "Nichts zu prüfen.", erledigt: "Noch nichts freigegeben." }[f];
  $("liste").innerHTML = eintraege.map(zelle).join("") || `<li class="klein mitte">${leer}</li>`;
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
  if (fertig) { chip.className = "status-chip fertig"; chip.innerHTML = "✓ Freigegeben"; }
  else if (b.bereich === "sicher") { chip.className = "status-chip gruen"; chip.innerHTML = `<span class="punkt gruen"></span>Sicher vorkontiert · ${prozent(b.sicherheit)}`; }
  else { chip.className = `status-chip ${b.ampel === "rot" ? "rot" : "gelb"}`; chip.innerHTML = `<span class="punkt ${b.ampel === "rot" ? "rot" : "gelb"}"></span>Bitte prüfen`; }

  const k = b.kopf;
  $("b-lieferant").textContent = k.supplier_name || "Unbekannter Lieferant";
  $("b-meta").textContent = [b.mandant.name, k.invoice_number ? `Rechnung ${k.invoice_number}` : "ohne Rechnungsnummer",
    datum(k.invoice_date), k.document_type === "credit_note" ? "Gutschrift" : null, k.reverse_charge ? "Reverse Charge" : null]
    .filter(Boolean).join(" · ");
  $("b-brutto").textContent = eur(k.gross_total);
  $("b-steuer").textContent = `Netto ${eur(k.net_total)} · USt ${eur(k.tax_total)}`;

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
    ["Sicherheit des Belegs", prozent(b.sicherheit)],
    ["Mandant", esc(b.mandant.name + " · " + b.mandant.branche)]].map(([a, c]) => `<tr><td>${a}</td><td>${c}</td></tr>`).join("");
  $("schritte").innerHTML = b.schritte.map((s) => `<li title="${esc(s.detail)}">${esc(s.name)} · ${s.dauer_s.toLocaleString("de-DE")} s</li>`).join("");
  $("ki").innerHTML = b.ki.art === "aufzeichnung"
    ? `${esc(b.ki.modell)}: Antwort aus dem Messlauf (damals ${Number(b.ki.laufzeit_s).toLocaleString("de-DE", { maximumFractionDigits: 1 })} s,
       ${(b.ki.kosten_eur * 100).toLocaleString("de-DE", { maximumFractionDigits: 2 })} Cent), heute ohne Kosten abgespielt.`
    : esc(b.ki.text) + (b.gelernt ? " Die Konten kommen aus den gelernten Regeln." : "");
  $("soll").innerHTML = b.soll ? `Abgleich mit dem Sollwert: Pflichtfelder ${b.soll.pflichtfelder.join("/")} · Positionen ${b.soll.positionen.join("/")}` : "";
  $("pseudo").hidden = !b.pseudonymisiert;
  const n = Object.values(b.platzhalter).reduce((a, c) => a + c, 0);
  $("pseudo-zahl").textContent = n ? `${n} Angaben ersetzt` : "";
  $("pseudo-text").innerHTML = esc(b.pseudonymisiert).replace(/\[[A-Z_]+_\d+\]/g, (m) => `<mark>${m}</mark>`);
  $("verlauf").innerHTML = b.protokoll.slice().reverse().map((e) => `<li><b>${esc(e.feld)}</b>: ${esc(e.alt ?? "–")} → ${esc(e.neu ?? "–")}
    <br>${new Date(e.zeit).toLocaleString("de-DE")} · ${esc(e.quelle || e.nutzer)}</li>`).join("") || `<li>Noch keine Änderungen</li>`;

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
      <span><b>${esc(e.lieferant)}</b><small>${esc(e.mandant)} · Kreditor ${esc(e.kreditor)} · ${datum(e.datum)} · ${e.gelernt}/${e.positionen} gelernt</small></span>
      <span class="z-betrag">${eur(e.brutto)}</span>
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
  $("blatt-summe").textContent = `${gewaehlt.length} ausgewählt · ${eur(summe)}`;
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
      if (!confirm("Alle Kreditoren, Lernregeln, Kontoänderungen und Freigaben der Demo löschen?")) return;
      await post("/api/demo/zuruecksetzen", {});
      zustand.key = null; $("beleg").hidden = true; $("aktionsleiste").hidden = true; $("leer").hidden = false;
      await ladeListe(); setzeFilter("pruefen");
      toast("Demo zurückgesetzt");
    }
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
