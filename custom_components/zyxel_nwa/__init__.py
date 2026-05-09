{
  "config": {
    "step": {
      "user": {
        "title": "Zyxel NWA Access Point",
        "description": "Verbindung zu deinem Zyxel NWA Access Point im Standalone-Modus. Stelle sicher, dass er NICHT über Nebula Cloud verwaltet wird.",
        "data": {
          "host": "Host / IP-Adresse (z. B. 192.168.1.2)",
          "username": "Benutzername (meistens 'admin')",
          "password": "Passwort"
        }
      }
    },
    "error": {
      "cannot_connect": "Verbindung zum Access Point fehlgeschlagen. Prüfe die IP-Adresse und stelle sicher, dass der AP im Standalone-Modus betrieben wird (nicht Nebula-verwaltet).",
      "invalid_auth": "Ungültiger Benutzername oder Passwort.",
      "unknown": "Unerwarteter Fehler. Bitte die Logs prüfen."
    },
    "abort": {
      "already_configured": "Dieser Access Point ist bereits konfiguriert."
    }
  }
}
