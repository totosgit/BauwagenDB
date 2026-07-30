<template>
  <div class="rechtsseite">
    <div class="zettel-blatt">
      <h1>Datenschutz &amp; Verantwortlicher</h1>
      <p class="stand">Stand: {{ stand }}</p>

      <!-- ══ Verantwortlicher ══ -->
      <h2>Wer betreibt diese Anwendung</h2>
      <p>
        Diese Anwendung wird privat betrieben und läuft auf einem eigenen Server
        im Privathaushalt des Betreibers. Sie ist nicht öffentlich nutzbar,
        sondern nur für Helferinnen und Helfer des Zeltlagers – ein Konto muss
        freigegeben werden.
      </p>
      <div class="ausfuellen">
        <p class="ausfuellen-titel">Vom Betreiber zu ergänzen</p>
        <p>
          {{ PLATZHALTER.name }}<br />
          {{ PLATZHALTER.strasse }}<br />
          {{ PLATZHALTER.ort }}<br />
          E-Mail: {{ PLATZHALTER.mail }}
        </p>
      </div>

      <!-- ══ Welche Daten ══ -->
      <h2>Welche Daten verarbeitet werden</h2>
      <p>Die Anwendung speichert ausschließlich, was für ihren Zweck nötig ist:</p>
      <table class="daten">
        <thead>
          <tr><th>Daten</th><th>Wofür</th><th>Wie lange</th></tr>
        </thead>
        <tbody>
          <tr>
            <td>Benutzername, Anzeigename, Passwort (nur als Argon2-Hashwert, nie im Klartext)</td>
            <td>Anmeldung und Zuordnung von Einträgen</td>
            <td>bis das Konto gelöscht wird</td>
          </tr>
          <tr>
            <td>E-Mail-Adresse</td>
            <td>freiwillig, nur zur Kontaktaufnahme durch die Lagerleitung</td>
            <td>bis sie entfernt oder das Konto gelöscht wird</td>
          </tr>
          <tr>
            <td>Sitzungsmerkmal (Zufallswert) mit Zeitstempel</td>
            <td>Angemeldet-Bleiben</td>
            <td>7 Tage nach der letzten Nutzung</td>
          </tr>
          <tr>
            <td>Gruppenzugehörigkeit (z.&nbsp;B. Küche, Bauwagentrupp)</td>
            <td>zeigt anderen, wer im Lager was macht</td>
            <td>bis zum Austritt oder Kontolöschung</td>
          </tr>
          <tr>
            <td>Notizen und Einkaufsliste: Text, Name, Zeitpunkt</td>
            <td>gemeinsame Absprachen im Lager</td>
            <td>bis jemand den Eintrag löscht</td>
          </tr>
          <tr>
            <td>Strichliste: wer wann welches Getränk genommen hat</td>
            <td>Abrechnung der Getränke</td>
            <td>bis zur Abrechnung, dann wird sie geleert</td>
          </tr>
          <tr>
            <td>Fotos von Gegenständen</td>
            <td>Wiedererkennen im Lager</td>
            <td>bis der Gegenstand oder das Foto gelöscht wird</td>
          </tr>
          <tr>
            <td>Server-Protokolle (IP-Adresse, Zeitpunkt, aufgerufene Adresse)</td>
            <td>Betrieb und Fehlersuche</td>
            <td>{{ PLATZHALTER.logdauer }}</td>
          </tr>
        </tbody>
      </table>

      <p class="warnhinweis">
        Bitte keine Fotos hochladen, auf denen Personen erkennbar sind – die
        Anwendung ist für Werkzeug und Material gedacht, nicht für Bilder von
        Menschen.
      </p>

      <!-- ══ Rechtsgrundlage ══ -->
      <h2>Auf welcher Grundlage</h2>
      <ul>
        <li>
          <strong>Art. 6 Abs. 1 lit. b DSGVO</strong> – für Konto, Anmeldung und
          alles, was zur Nutzung selbst gehört.
        </li>
        <li>
          <strong>Art. 6 Abs. 1 lit. f DSGVO</strong> – berechtigtes Interesse an
          einer funktionierenden Lagerverwaltung und an einer nachvollziehbaren
          Getränkeabrechnung, sowie am sicheren Betrieb des Servers.
        </li>
      </ul>
      <p>
        Die Angabe einer E-Mail-Adresse ist freiwillig. Ohne sie funktioniert
        alles – ein vergessenes Passwort setzt dann ein Admin zurück.
      </p>

      <!-- ══ Weitergabe ══ -->
      <h2>Wer die Daten außerdem sieht</h2>
      <ul>
        <li>
          <strong>Andere angemeldete Personen</strong> sehen Anzeigename,
          Benutzername und Gruppen sowie die Einträge, die jemand in Notizen und
          Einkaufsliste geschrieben hat. Die eigene Strichliste sieht jeder nur
          selbst; die Gesamtübersicht ist der Lagerleitung vorbehalten.
        </li>
        <li>
          <strong>Cloudflare</strong> ({{ PLATZHALTER.cloudflare }}) liegt als
          Zwischenstation vor dem Server und verarbeitet dabei technisch
          notwendige Verbindungsdaten wie die IP-Adresse. Ohne diese
          Zwischenstation wäre die Anwendung von außen nicht erreichbar.
        </li>
      </ul>
      <p>
        Es gibt <strong>keine Zugriffsmessung, kein Tracking und keine Werbung</strong>.
        Die Anwendung lädt keine Schriften, Symbole oder Skripte von fremden
        Servern nach – alles ist mitgeliefert, damit sie auch ohne Netz
        funktioniert. Gesetzt wird ein einziges Cookie, das die Anmeldung
        aufrechterhält; ohne dieses ist keine Nutzung möglich.
      </p>

      <!-- ══ Rechte ══ -->
      <h2>Deine Rechte</h2>
      <p>
        Du kannst Auskunft über die zu dir gespeicherten Daten verlangen sowie
        deren Berichtigung, Löschung oder eine Einschränkung der Verarbeitung.
        Ebenso besteht ein Recht auf Datenübertragbarkeit und ein
        Widerspruchsrecht gegen eine Verarbeitung auf Grundlage berechtigter
        Interessen. Wende dich dafür an die oben genannte Adresse.
      </p>
      <p>
        Anzeigename und E-Mail kannst du jederzeit selbst im Profil ändern,
        ebenso das Passwort. Eine vollständige Löschung des Kontos nimmt ein
        Admin vor – dabei verschwinden auch deine Striche. Notizen und
        Einkaufseinträge bleiben mit dem zum Zeitpunkt des Schreibens
        gespeicherten Namen erhalten, damit Absprachen nachvollziehbar bleiben;
        auf Wunsch werden sie mitgelöscht.
      </p>
      <p>
        Außerdem steht dir ein Beschwerderecht bei einer Aufsichtsbehörde zu.
        Zuständig ist die Behörde des Bundeslandes, in dem der Betreiber wohnt:
        {{ PLATZHALTER.behoerde }}
      </p>

      <!-- ══ Sicherheit ══ -->
      <h2>Sicherheit</h2>
      <p>
        Die Verbindung ist durchgehend verschlüsselt (HTTPS). Passwörter werden
        als Argon2-Hashwert gespeichert und sind auch für den Betreiber nicht
        lesbar. Vom Datenbestand werden Sicherungskopien angelegt, damit bei
        einem Defekt nichts verloren geht; diese liegen auf demselben Server.
      </p>

      <div class="fusszeile">
        <router-link to="/login">Zur Anmeldung</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Rechtliche Hinweise. Bewusst ohne Login erreichbar -- eine
 * Datenschutzerklärung, die man erst nach der Anmeldung lesen kann, hilft
 * niemandem.
 *
 * Die Platzhalter unten muss der Betreiber ausfüllen. Sie stehen absichtlich
 * sichtbar im Text, damit nicht übersehen wird, dass hier noch etwas fehlt.
 */
const PLATZHALTER = {
  name: '[Vor- und Nachname des Betreibers]',
  strasse: '[Straße und Hausnummer]',
  ort: '[PLZ und Ort]',
  mail: '[E-Mail-Adresse für Anfragen]',
  logdauer: '[z. B. 14 Tage – bitte an die tatsächliche Einstellung anpassen]',
  cloudflare: 'Cloudflare, Inc., USA – Angemessenheitsbeschluss der EU-Kommission',
  behoerde: '[zuständige Landesdatenschutzbehörde eintragen]',
}

const stand = new Date().toLocaleDateString('de-DE', {
  day: '2-digit', month: 'long', year: 'numeric',
})
</script>

<style scoped>
.rechtsseite {
  min-height: 100vh;
  background: var(--pergament);
  background-image: var(--pergament-flaeche);
  padding: 22px 16px 48px;
}
.zettel-blatt {
  max-width: 680px;
  margin: 0 auto;
  background: var(--blatt);
  border-radius: var(--radius-sm);
  box-shadow: var(--schatten);
  padding: 28px 24px;
}

h1 {
  font-family: var(--schrift-stempel);
  font-size: 23px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--gebrannt);
  margin-bottom: 4px;
  text-wrap: balance;
}
.stand { font-size: 13.5px; color: var(--tinte-blass); margin-bottom: 22px; }

h2 {
  font-family: var(--schrift-stempel);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.11em;
  color: var(--tinte-blass);
  margin: 26px 0 8px;
}
p { margin-bottom: 11px; max-width: 62ch; line-height: 1.5; }
ul { margin: 0 0 11px 20px; }
li { margin-bottom: 7px; max-width: 60ch; line-height: 1.5; }
strong { color: var(--gebrannt); }

/* Tabelle scrollt für sich, damit die Seite nicht seitlich wandert */
.daten {
  display: block;
  overflow-x: auto;
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0 14px;
  font-size: 14.5px;
}
.daten thead, .daten tbody, .daten tr { display: table; width: 100%; table-layout: fixed; }
.daten th {
  text-align: left;
  font-family: var(--schrift-stempel);
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--tinte-blass);
  padding: 7px 8px 7px 0;
  border-bottom: 1.5px solid var(--linie-stark);
}
.daten td {
  padding: 9px 8px 9px 0;
  border-bottom: 1px solid var(--linie);
  vertical-align: top;
  line-height: 1.4;
}
.daten th:first-child, .daten td:first-child { width: 44%; }

/* Was der Betreiber noch eintragen muss -- sichtbar markiert */
.ausfuellen {
  border-left: 3px solid var(--rot);
  background: var(--rot-blass);
  padding: 12px 0 12px 14px;
  margin: 12px 0 4px;
}
.ausfuellen-titel {
  font-family: var(--schrift-stempel);
  font-size: 10.5px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--rot);
  margin-bottom: 6px;
}
.ausfuellen p:last-child { margin-bottom: 0; line-height: 1.6; }

.warnhinweis {
  border-left: 3px solid var(--rot);
  padding: 10px 0 10px 14px;
  background: var(--rot-blass);
  font-size: 15px;
}

.fusszeile {
  margin-top: 30px;
  padding-top: 16px;
  border-top: 1px solid var(--linie);
}
.fusszeile a {
  font-family: var(--schrift-stempel);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--gebrannt);
  text-decoration: none;
}

@media (max-width: 390px) {
  .zettel-blatt { padding: 22px 16px; }
  h1 { font-size: 20px; }
  .daten { font-size: 13.5px; }
  .daten th:first-child, .daten td:first-child { width: 40%; }
}
</style>
