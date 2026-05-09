# Zyxel NWA Access Point – Home Assistant Integration

Unterstützt **NWA50AX, NWA50BE, NWA90AX, NWA90BE** und kompatible Modelle im **Standalone-Modus**.

---

## Voraussetzungen

### AP muss im Standalone-Modus sein (nicht Nebula)

Wenn dein AP über die Nebula Cloud verwaltet wird, funktioniert diese Integration **nicht**, weil Nebula die lokale API sperrt.

**So wechselst du zu Standalone:**
1. Öffne [nebula.zyxel.com](https://nebula.zyxel.com)
2. Gehe zu **Organization-wide → License & inventory → Devices**
3. Wähle deinen AP → **Actions → Remove from organization**
4. Der AP setzt sich zurück und startet im Standalone-Modus neu
5. Standard-IP: `192.168.1.2`, Login: `admin` / Passwort auf dem Geräteaufkleber

---

## Installation (HACS – empfohlen)

1. HACS öffnen → **Integrations → Custom Repositories**
2. Repository-URL eintragen → Kategorie: **Integration**
3. Integration **"Zyxel NWA Access Point"** installieren
4. Home Assistant neu starten

## Manuelle Installation

```bash
# Im HA config-Verzeichnis:
mkdir -p custom_components/zyxel_nwa
# Alle Dateien aus diesem Ordner dorthin kopieren
cp -r ha_zyxel_nwa/* config/custom_components/zyxel_nwa/
```

Dann HA neu starten.

---

## Konfiguration

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Suche nach **"Zyxel NWA"**
3. Eingeben:
   - **Host**: IP-Adresse des APs (z. B. `192.168.1.2`)
   - **Username**: `admin`
   - **Password**: dein AP-Passwort

---

## Bereitgestellte Entitäten

### Sensoren
| Entität | Beschreibung |
|---|---|
| `sensor.zyxel_nwa_connected_clients` | Anzahl verbundener WLAN-Clients |
| `sensor.zyxel_nwa_cpu_usage` | CPU-Auslastung in % |
| `sensor.zyxel_nwa_memory_usage` | Speichernutzung in % |
| `sensor.zyxel_nwa_uptime` | Betriebszeit in Sekunden |
| `sensor.zyxel_nwa_temperature` | Gerätetemperatur (falls verfügbar) |
| `sensor.zyxel_nwa_firmware_version` | Aktuelle Firmware-Version |
| `sensor.zyxel_nwa_model` | Gerätemodell |
| `sensor.zyxel_nwa_active_ssids` | Anzahl aktiver SSIDs |

### Binary Sensor
| Entität | Beschreibung |
|---|---|
| `binary_sensor.zyxel_nwa_..._online` | AP erreichbar (ja/nein) |

### Button
| Entität | Beschreibung |
|---|---|
| `button.zyxel_nwa_reboot_...` | AP neu starten |

---

## Mehrere APs

Die Integration kann beliebig oft hinzugefügt werden – einmal pro AP.  
Jeder AP erscheint als eigenes Gerät in Home Assistant.

---

## Fehlerbehebung

### "Cannot connect"
- AP erreichbar? Browser öffnen → `https://192.168.1.2`
- AP im Standalone-Modus? Dashboard → Management Mode = `Standalone`
- SSL-Fehler werden ignoriert (Zyxel nutzt selbst-signierte Zertifikate)

### Sensoren zeigen `unavailable`
- Manche Endpunkte (CPU, Temperatur) sind modellabhängig
- Ältere Firmware-Versionen unterstützen ggf. nicht alle API-Felder
- HA-Logs prüfen: **Einstellungen → System → Logs**

### Passwort nach Nebula-Reset
- Standard-Passwort steht auf dem Aufkleber auf der Geräterückseite (NWA50BE/NWA90BE)
- Bei NWA50AX: Standard ist `1234` oder auf dem Aufkleber

---

## Unterstützte Modelle

NWA50AX · NWA50AX PRO · NWA50BE · NWA50BE PRO  
NWA90AX · NWA90AX PRO · NWA90BE · NWA90BE PRO  
NWA55AXE · NWA55BE · NWA110AX · NWA210AX  
WAX510D · WAX610D · WAX630S · WAC500 · WAC500H
