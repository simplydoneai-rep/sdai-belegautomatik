"use strict";

const $ = (id) => document.getElementById(id);
const eur = (v) => v == null || v === "" ? "–" :
  Number(v).toLocaleString("de-DE", { style: "currency", currency: "EUR" });
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const datum = (iso) => iso && /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso.split("-").reverse().join(".") : (iso || "–");
const AMPEL_TEXT = {
  gruen: "Vorschlag schlüssig – kann geprüft und freigegeben werden",
  gelb: "Vorschlag mit Hinweisen – bitte gezielt prüfen",
  rot: "Unvollständig oder widersprüchlich – Nacharbeit nötig",
};

let stammdaten = null;
let upload = null;

async function init() {
  stammdaten = await (await fetch("/api/stammdaten")).json();
  const gruppen = { synthetisch: "Synthetische Rechnungen", kosit: "KoSIT-Testsuite (E-Rechnung und Sichtbeleg)" };
  for (const [quelle, titel] of Object.entries(gruppen)) {
    const og = document.createElement("optgroup");
    og.label = titel;
    for (const b of stammdaten.testbelege.filter((x) => x.datei.startsWith(quelle))) {
      const o = document.createElement("option");
      o.value = b.nr;
      const art = { xml: "E-Rechnung XML", pdf: "PDF", scan: "Scan", foto: "Foto" }[b.art] || b.art;
      o.textContent = `${b.id} · ${art} · ${b.merkmale.join(", ")}`;
      og.appendChild(o);
    }
    $("beleg").appendChild(og);
  }
  for (const m of stammdaten.modelle) $("modell").add(new Option(m.label, m.id));
  for (const m of stammdaten.mandanten) $("mandant").add(new Option(`${m.name} (${m.branche})`, m.id));
  $("los").addEventListener("click", verarbeiten);
  $("beleg").addEventListener("change", () => { upload = null; $("datei").value = ""; });
  const drop = $("drop");
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("aktiv"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("aktiv"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault(); drop.classList.remove("aktiv");
    if (e.dataTransfer.files[0]) waehleDatei(e.dataTransfer.files[0]);
  });
  $("datei").addEventListener("change", (e) => e.target.files[0] && waehleDatei(e.target.files[0]));
}

function waehleDatei(file) {
  upload = file;
  verarbeiten();
}

function zeigeSeiten(urls) {
  const v = $("vorschau");
  v.className = "vorschau seiten";
  v.innerHTML = urls.map((u, i) => `<img src="${u}" alt="Seite ${i + 1}">`).join("");
}

async function vorschauTestbeleg(nr, art) {
  const v = $("vorschau");
  if (art === "xml") {
    v.className = "vorschau";
    const t = await (await fetch(`/api/testbelege/${nr}/datei`)).text();
    v.innerHTML = `<pre>${esc(t)}</pre>`;
    return;
  }
  const { anzahl } = await (await fetch(`/api/testbelege/${nr}/seiten`)).json();
  zeigeSeiten([...Array(anzahl).keys()].map((i) => `/api/testbelege/${nr}/seite/${i}`));
}

function vorschauUpload(file) {
  const v = $("vorschau");
  v.className = "vorschau leer";
  if (/\.xml$/i.test(file.name)) file.text().then((t) => { v.className = "vorschau"; v.innerHTML = `<pre>${esc(t)}</pre>`; });
  else v.textContent = "Vorschau wird erstellt …";
}

async function verarbeiten() {
  const knopf = $("los");
  knopf.disabled = true;
  knopf.textContent = "Verarbeite …";
  const form = new FormData();
  form.append("modell", $("modell").value);
  let url;
  if (upload) {
    form.append("datei", upload);
    form.append("mandant", $("mandant").value);
    url = "/api/upload";
    vorschauUpload(upload);
  } else {
    const nr = $("beleg").value;
    const b = stammdaten.testbelege[nr];
    url = `/api/testbelege/${nr}/verarbeiten`;
    vorschauTestbeleg(nr, b.art);
  }
  try {
    const r = await fetch(url, { method: "POST", body: form });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Fehler");
    if (upload && data.seiten && data.seiten.length) zeigeSeiten(data.seiten);
    zeige(data);
  } catch (e) {
    $("leer").hidden = false; $("ergebnis").hidden = true;
    $("leer").textContent = "Fehler: " + e.message;
  } finally {
    knopf.disabled = false;
    knopf.textContent = "Verarbeiten";
  }
}

function zeige(d) {
  $("leer").hidden = true;
  $("ergebnis").hidden = false;
  const st = $("status");
  st.className = `status ${d.ampel}`;
  st.innerHTML = `<span class="punkt ${d.ampel}"></span>${AMPEL_TEXT[d.ampel]}`;
  $("schritte").innerHTML = d.schritte.map((s) =>
    `<li title="${esc(s.detail)}"><b>${esc(s.name)}</b> ${s.dauer_s.toLocaleString("de-DE")} s</li>`).join("");

  const k = d.kopf;
  const zeilen = [
    ["Lieferant", esc(k.supplier_name)], ["Rechnungsnummer", esc(k.invoice_number ?? "– (keine)")],
    ["Rechnungsdatum", datum(k.invoice_date)],
    ["Belegart", k.document_type === "credit_note" ? "Gutschrift" : "Rechnung"],
    ["Netto", eur(k.net_total)], ["Umsatzsteuer", eur(k.tax_total)], ["Brutto", `<b>${eur(k.gross_total)}</b>`],
    ["Reverse Charge / i. g. Erwerb", k.reverse_charge ? "ja – Leistungsempfänger schuldet die Steuer" : "nein"],
  ];
  $("kopf").innerHTML = zeilen.map(([a, b]) => `<tr><td>${a}</td><td>${b}</td></tr>`).join("");

  $("positionen").querySelector("tbody").innerHTML = d.positionen.map((p) => `
    <tr>
      <td><span class="punkt ${p.ampel}" title="${esc(p.hinweise.join("; ") || "schlüssig")}"></span></td>
      <td>${esc(p.description)}${p.hinweise.length ? `<div class="hinw">${esc(p.hinweise.join("; "))}</div>` : ""}</td>
      <td class="r">${eur(p.net_amount)}</td>
      <td class="r">${p.tax_rate ?? "–"} %</td>
      <td class="konto">${esc(p.account_skr03 ?? "–")}<small>${esc(p.konto_name)}</small></td>
    </tr>`).join("");

  $("steuerlogik").innerHTML = d.steuerlogik.ok
    ? `<span class="punkt gruen"></span> Netto + Steuer = Brutto, Steuersätze zulässig`
    : `<span class="punkt rot"></span> ${esc(d.steuerlogik.hinweise.join(", "))}`;
  if (d.steuerlogik.ok && d.steuerlogik.hinweise.length)
    $("steuerlogik").innerHTML += `<div class="hinw">${esc(d.steuerlogik.hinweise.join(", "))}</div>`;

  const ki = d.ki;
  if (ki.art === "aufzeichnung") {
    $("ki").innerHTML = `${esc(ki.modell)}<div class="klein">Antwort aus dem Messlauf: damals
      ${Number(ki.laufzeit_s).toLocaleString("de-DE", { maximumFractionDigits: 1 })} s,
      ${(ki.kosten_eur * 100).toLocaleString("de-DE", { maximumFractionDigits: 2 })} Cent
      (${ki.token_ein} Token rein, ${ki.token_aus} raus). Heute ohne Kosten abgespielt.</div>`;
  } else {
    $("ki").innerHTML = `<div class="klein">${esc(ki.text)}</div>`;
  }

  const soll = $("soll");
  if (d.soll) {
    soll.hidden = false;
    const [pf, pfg] = d.soll.pflichtfelder, [ps, psg] = d.soll.positionen, [ko, kog] = d.soll.konten;
    soll.innerHTML = `<b>Abgleich mit dem Sollwert (Goldstandard):</b> Pflichtfelder ${pf}/${pfg} ·
      Positionen ${ps}/${psg}` + (kog ? ` · Sachkonten ${ko}/${kog}` : "") +
      (d.soll.abweichend.length ? `<div class="klein">Abweichend: ${esc(d.soll.abweichend.join(", "))}</div>` : "");
  } else {
    soll.hidden = true;
  }

  const pseudo = $("pseudo");
  if (d.pseudonymisiert) {
    pseudo.hidden = false;
    const n = Object.values(d.platzhalter).reduce((a, b) => a + b, 0);
    $("pseudo-zahl").textContent = `(${n} Angaben ersetzt)`;
    $("pseudo-typen").innerHTML = Object.entries(d.platzhalter).map(([t, c]) => `<span>${esc(t)} × ${c}</span>`).join("");
    $("pseudo-text").innerHTML = esc(d.pseudonymisiert).replace(/\[[A-Z_]+_\d+\]/g, (m) => `<mark>${m}</mark>`);
  } else {
    pseudo.hidden = true;
  }
}

init();
