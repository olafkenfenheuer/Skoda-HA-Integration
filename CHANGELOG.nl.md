# Changelog

[🇬🇧 English](CHANGELOG.md) | [🇳🇱 Nederlands](CHANGELOG.nl.md)

Alle relevante wijzigingen aan deze integratie staan hier gedocumenteerd. De indeling volgt
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.3]

### Toegevoegd

- **Herconfiguratie**: een nieuwe API-sleutel (en de VIN-lijst) kan op elk moment worden ingevoerd via
  *Opnieuw configureren* bij de integratie, bijv. voordat de huidige sleutel verloopt. De sleutel wordt
  eerst gevalideerd; entiteiten, geschiedenis en opties blijven behouden.

## [0.3.2]

### Toegevoegd

- Škoda-pictogram voor de integratie, meegeleverd als `brand/icon.png` (zichtbaar in Home Assistant 2026.3 of nieuwer).

## [0.3.1]

### Toegevoegd

- **Pollinginterval per voertuig**: elk voertuig krijgt `number`-entiteiten "Pollinginterval" en
  "Pollinginterval tijdens laden" (5-120 min). Tijdens het laden wordt het kortere interval gebruikt.
  Wijzigingen werken direct zonder herladen. Nieuwe optie "Pollinginterval tijdens laden"
  (standaard 5 min) stelt de standaardwaarde in.
- Een commando ververst nu alleen het voertuig waarvoor het bedoeld was.

## [0.3.0]

### Gewijzigd

- **Gemigreerd naar de officiële MyŠkoda Public API**
  (<https://public.api.connect.skoda-auto.cz/docs>). Authenticatie gebeurt nu met een API-sleutel
  uit de MyŠkoda-app in plaats van e-mail en wachtwoord; de `myskoda`-afhankelijkheid is
  verwijderd. Bestaande configuraties vragen om opnieuw te verifiëren (API-sleutel en VIN(s)).
- Pollen kost nu één verzoek per voertuig (was 10-13). Standaardinterval 10 minuten (minimaal 5),
  omdat de API 20 verzoeken per uur en VIN toestaat.
- Commando's verversen niet meer direct; één verversing volgt 30 seconden na het laatste commando.
- De vergrendeling is nu een alleen-lezen `binary_sensor` (`unlocked`).

### Toegevoegd

- `select`-entiteit voor de laadmodus.
- Diagnostics maskeren API-sleutel, VIN's, kenteken, positie en adres.

### Verwijderd

- Functies zonder publiek API-endpoint: vergrendelen/ontgrendelen (en S-PIN-optie), toeteren &
  knipperen, knipperen, wakker maken, ruitverwarming, accuzorgmodus, gereduceerde laadstroom,
  buitentemperatuur en softwareversie.

## [0.2.0]

### Toegevoegd

- **Laadlocatie-sensoren**: een nieuwe `sensor.charging_location_profile` toont de naam van de
  opgeslagen laadlocatie (bv. "Home") waar het voertuig momenteel aan gekoppeld is, en
  `binary_sensor.vehicle_in_saved_location` geeft aan of het voertuig überhaupt op een
  opgeslagen laadlocatie staat. De waarde van de sensor is gekoppeld aan de binary sensor, zodat
  hij geen verouderde locatienaam blijft tonen nadat het voertuig is weggereden.
- **Adres-sensor**: `sensor.location_address` toont een leesbaar adres voor de laatst bekende
  positie van het voertuig, opgebouwd uit het adres van de live positie of, als dat niet
  beschikbaar is, de laatst bekende parkeerlocatie — een tekstuele aanvulling op de bestaande
  `device_tracker.vehicle_location`, die de entiteit blijft die het voertuig op de
  Kaart-dashboardkaart zet.
- **Rate-limit-afhandeling**: de coordinator herkent nu expliciet HTTP 429/430-responses van de
  Škoda Connect API, respecteert de `Retry-After`-header (met een terugval naar een begrensde
  pauze van 15 minuten tot 1 uur als deze ontbreekt), en pauzeert precies één cyclus via het
  ingebouwde retry-mechanisme van Home Assistant, in plaats van de API meteen weer te
  bestoken. Dezelfde situatie toont nu ook een aparte, vertaalde "rate limited"-foutmelding
  tijdens het inloggen en opnieuw aanmelden.

### Gewijzigd

- Het minimaal instelbare vernieuwingsinterval is verlaagd van 1 minuut naar 15 minuten, en de
  standaardwaarde van 30 naar 15 minuten. Het ophalen van de volledige status van één voertuig
  kost ongeveer 10–13 losse API-requests, en de API hanteert een strikt quotum per
  account — bij een interval van 1 minuut liep je zo tegen een rate limit aan, of erger, een
  geblokkeerd account. Zie de sectie "Over de API" in de README voor meer uitleg als je meerdere
  voertuigen op één account hebt.

## [0.1.0] - 2026-08-28

Eerste release: een Home Assistant-integratie voor Škoda-voertuigen, gebouwd op de
MySkoda-app-API, via de [`myskoda`](https://github.com/skodaconnect/myskoda)
Python-client.

### Toegevoegd

- Config flow die volledig via de UI werkt (e-mail/wachtwoord + optionele S-PIN) met
  ondersteuning voor opnieuw aanmelden, en een opties-flow voor het vernieuwingsinterval en een
  alleen-lezen modus.
- `sensor`: batterijniveau, laadvermogen, laadsnelheid, resterende laadtijd, actieradius
  (batterij/totaal), brandstofniveau, AdBlue-bereik, kilometerstand, buiten-/doeltemperatuur,
  softwareversie.
- `binary_sensor`: portieren, ramen, kofferbak, motorkap, verlichting, aan het laden, laadkabel
  aangesloten.
- `lock`: centrale vergrendeling (vereist S-PIN).
- `device_tracker`: laatst bekende GPS-locatie van het voertuig.
- `climate`: airconditioning op afstand (aan/uit, ventilatie, doeltemperatuur).
- `switch`: ruitverwarming, laden, batterijbeschermingsmodus, verminderde laadstroom.
- `button`: claxon en knipperlichten, lichten laten knipperen, voertuig wekken.
- `number`: AC-laadlimiet.
- Diagnostics-download met redactie van gevoelige gegevens.
- Vertalingen voor de config flow, de opties-flow en de entiteitsnamen in het Engels,
  Nederlands, Duits, Frans, Tsjechisch en Slowaaks.
