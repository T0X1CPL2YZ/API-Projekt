import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
import requests


def buecher_suchen(such_eingabe, tabelle, status_label, fenster):
  """Sucht Bücher über die OpenLibrary API und zeigt sie in der Tabelle an."""
  suchbegriff = such_eingabe.get().strip()

  if not suchbegriff:
    status_label.config(
        text="⚠️ Bitte gib zuerst einen Suchbegriff ein.", foreground="#d9534f"
    )
    return

  # Ladehinweis anzeigen und alte Tabelleneinträge löschen
  status_label.config(
      text="🔍 Suche nach Büchern auf OpenLibrary...", foreground="#0275d8"
  )
  fenster.update()

  for eintrag in tabelle.get_children():
    tabelle.delete(eintrag)

  try:
    url = f"https://openlibrary.org/search.json?q={suchbegriff}&limit=20"
    #URL wird aufgerufen und sofort in json umgewandelt, jedoch wurde ein timeout von 10 sekunden angegeben wenn die suche zulange dauert.
    daten = requests.get(url, timeout=15).json()
    #Sammelt die Bücherliste in "docs".
    treffer = daten.get("docs", [])

    #wenn keine Buchtreffer vorhanden sind, soll es "Keine Bücher gefunden" als label in der GUI angeben.
    if not treffer:
      status_label.config(
          text="❌ Keine Bücher gefunden.", foreground="#d9534f"
      )
      return

    # Gefundene Bücher Zeile für Zeile in die Tabelle eintragen
    for buch in treffer:
      #Hier wird von einem Buch der in treffer drin ist der TITEL, AUTOR_NAME und das VERÖFFENTLICHUNGSDATUM und die COVER ID für die Leseprobe.
      #Zusätzlich wurde ein ja/nein für die Leseprobe angegeben
      titel = buch.get("title", "Unbekannter Titel")
      autor = buch.get("author_name", ["Unbekannt"])[0]
      jahr = buch.get("first_publish_year", "-")
      edition_key = buch.get("cover_edition_key", "")
      #Wenn eine Leseprobe vorhanden ist soll es "ja" ausgeben, ansonsten "Nein"
      hat_vorschau = "Ja" if edition_key else "Nein"

      # Der edition_key wird in der 5. Spalte unsichtbar mitgespeichert
      tabelle.insert(
          "", "end", values=(titel, autor, jahr, hat_vorschau, edition_key)
      )

    status_label.config(
        text=(
            f"✅ {len(treffer)} Bücher gefunden. Doppelklick auf ein Buch"
            " öffnet die Leseprobe."
        ),
        foreground="#5cb85c",
    )

  except requests.RequestException as fehler:
    status_label.config(
        text="❌ Verbindungsfehler zur OpenLibrary API.", foreground="#d9534f"
    )
    messagebox.showerror(
        "Netzwerkfehler", f"Fehler bei der Anfrage:\n{fehler}"
    )


def leseprobe_oeffnen(tabelle, status_label, fenster):
  """Liest die ID der ausgewählten Zeile aus und öffnet die Leseprobe im Browser."""
  auswahl = tabelle.selection()
  if not auswahl:
    messagebox.showinfo(
        "Hinweis", "Bitte wähle zuerst ein Buch aus der Liste aus."
    )
    return

  # Werte aus der angeklickten Zeile holen (Index 4 = unsichtbarer edition_key)
  zeilen_werte = tabelle.item(auswahl[0], "values")
  edition_key = zeilen_werte[4]

  if not edition_key:
    status_label.config(
        text="⚠️ Keine passende Ausgabe für eine Vorschau gefunden.",
        foreground="#f0ad4e",
    )
    messagebox.showwarning(
        "Keine Vorschau",
        "Für dieses Buch ist leider keine Ausgabe mit ID hinterlegt.",
    )
    return

  status_label.config(
      text="⏳ Prüfe Verfügbarkeit der Leseprobe...", foreground="#0275d8"
  )
  fenster.update()

  try:
    bib_key = f"OLID:{edition_key}"
    books_url = f"https://openlibrary.org/api/books?bibkeys={bib_key}&format=json&jscmd=viewapi"
    buch_info = requests.get(books_url, timeout=20).json().get(bib_key, {})

    status = buch_info.get("preview")
    lese_link = buch_info.get("preview_url")

    if status in ["full", "restricted"] and lese_link:
      status_label.config(
          text=f"📖 Leseprobe geöffnet (Status: {status}).", foreground="#5cb85c"
      )
      webbrowser.open(lese_link)
    else:
      status_label.config(
          text="❌ Für diese Ausgabe ist leider keine Leseprobe verfügbar.",
          foreground="#d9534f",
      )
      messagebox.showinfo(
          "Nicht verfügbar",
          "Für diese Ausgabe ist leider keine Leseprobe verfügbar.",
      )

  except requests.RequestException as fehler:
    status_label.config(
        text="❌ Fehler beim Abrufen der Leseprobe.", foreground="#d9534f"
    )
    messagebox.showerror(
        "Fehler", f"Vorschau konnte nicht geladen werden:\n{fehler}"
    )


def main():
  """Erstellt das Hauptfenster und verbindet alle Buttons mit den Funktionen."""
  fenster = tk.Tk()
  fenster.title("📚 OpenLibrary Buchsuche")
  fenster.geometry("780x500")
  fenster.configure(bg="#f4f6f9")

  # Design-Einstellungen (Theme & Schriftarten)
  style = ttk.Style()
  style.theme_use("clam")
  style.configure("TFrame", background="#f4f6f9")
  style.configure(
      "Header.TLabel",
      font=("Segoe UI", 16, "bold"),
      background="#f4f6f9",
      foreground="#2c3e50",
  )
  style.configure(
      "Status.TLabel", font=("Segoe UI", 10), background="#f4f6f9", padding=5
  )
  style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
  style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
  style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)

  # Hauptbereich mit Innenabstand
  haupt_frame = ttk.Frame(fenster, padding="20")
  haupt_frame.pack(fill="both", expand=True)

  # 1. Überschrift
  titel_label = ttk.Label(
      haupt_frame,
      text="📚 OpenLibrary Buchsuche & Leseprobe",
      style="Header.TLabel",
  )
  titel_label.pack(anchor="w", pady=(0, 15))

  # 2. Suchleiste
  such_frame = ttk.Frame(haupt_frame)
  such_frame.pack(fill="x", pady=(0, 15))

  such_eingabe = ttk.Entry(such_frame, font=("Segoe UI", 11))
  such_eingabe.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=4)
  such_eingabe.focus()

  # 3. Ergebnistabelle mit Scrollbar
  tabellen_frame = ttk.Frame(haupt_frame)
  tabellen_frame.pack(fill="both", expand=True)

  scrollbar = ttk.Scrollbar(tabellen_frame)
  scrollbar.pack(side="right", fill="y")

  # 5 Spalten definieren, aber mit 'displaycolumns' nur die ersten 4 anzeigen
  alle_spalten = ("titel", "autor", "jahr", "vorschau", "edition_key")
  sichtbare_spalten = ("titel", "autor", "jahr", "vorschau")

  tabelle = ttk.Treeview(
      tabellen_frame,
      columns=alle_spalten,
      displaycolumns=sichtbare_spalten,
      show="headings",
      yscrollcommand=scrollbar.set,
      selectmode="browse",
  )
  scrollbar.config(command=tabelle.yview)

  tabelle.heading("titel", text="Buchtitel")
  tabelle.heading("autor", text="Autor")
  tabelle.heading("jahr", text="Jahr")
  tabelle.heading("vorschau", text="Edition-ID")

  tabelle.column("titel", width=340)
  tabelle.column("autor", width=210)
  tabelle.column("jahr", width=70, anchor="center")
  tabelle.column("vorschau", width=80, anchor="center")
  tabelle.pack(fill="both", expand=True)

  # 4. Unterer Bereich (Statusleiste + Button)
  unten_frame = ttk.Frame(haupt_frame)
  unten_frame.pack(fill="x", pady=(15, 0))

  status_label = ttk.Label(
      unten_frame,
      text="Bereit. Gib einen Buchtitel oder Autor ein.",
      style="Status.TLabel",
  )
  status_label.pack(side="left")

  # Funktionen über lambda mit den benötigten GUI-Elementen verknüpfen
  suche_starten = lambda event=None: buecher_suchen(
      such_eingabe, tabelle, status_label, fenster
  )
  vorschau_starten = lambda event=None: leseprobe_oeffnen(
      tabelle, status_label, fenster
  )

  such_eingabe.bind("<Return>", suche_starten)
  such_button = ttk.Button(
      such_frame, text="🔍 Suchen", command=suche_starten, style="Accent.TButton"
  )
  such_button.pack(side="right")

  tabelle.bind("<Double-1>", vorschau_starten)
  vorschau_button = ttk.Button(
      unten_frame,
      text="📖 Leseprobe im Browser öffnen",
      command=vorschau_starten,
      style="Accent.TButton",
  )
  vorschau_button.pack(side="right")

  fenster.mainloop()


# Programmstart
if __name__ == "__main__":
  main()
