# Škoda Connect voor Home Assistant

[🇬🇧 English](README.md) | [🇳🇱 Nederlands](README.nl.md)

Een meertalige [Home Assistant](https://www.home-assistant.io/) custom integration voor
Škoda-voertuigen, gebouwd op de MySkoda-app-API via de
actief onderhouden [`myskoda`](https://github.com/skodaconnect/myskoda) Python-client.

> **Niet-officieel project.** Deze integratie is niet verbonden met, onderschreven door, of
> geassocieerd met Škoda Auto. Ze gebruikt dezelfde (ongedocumenteerde) backend-API als de officiële MySkoda-app.
> Gebruik op eigen risico.

## Functies

Gebouwd volgens de huidige best practices voor Home Assistant-integraties: een config flow die
volledig via de UI werkt, een `DataUpdateCoordinator` voor efficiënte polling,
entity-descriptions, vertalingen per entiteit, een opties-flow, ondersteuning voor
opnieuw-aanmelden, en een diagnostics-download.

| Platform | Entiteiten |
|---|---|
| `sensor` | Batterijniveau, laadvermogen, laadsnelheid, resterende laadtijd, actieradius (batterij/totaal), brandstofniveau, AdBlue-bereik, kilometerstand, buiten-/doeltemperatuur, softwareversie, adres van de laatst bekende locatie, naam van het momenteel actieve laadlocatieprofiel |
| `binary_sensor` | Portieren, ramen, kofferbak, motorkap, verlichting, aan het laden, laadkabel aangesloten, voertuig bij opgeslagen laadlocatie |
| `lock` | Centrale vergrendeling (vereist S-PIN) |
| `device_tracker` | Laatst bekende GPS-locatie van het voertuig (zichtbaar op de Kaart-dashboardkaart) |
| `climate` | Airconditioning op afstand (aan/uit, ventilatie, doeltemperatuur) |
| `switch` | Ruitverwarming, laden, batterijbeschermingsmodus, verminderde laadstroom |
| `button` | Claxon en knipperlichten, lichten laten knipperen, voertuig wekken |
| `number` | AC-laadlimiet (state of charge) |

Sensoren en bedieningselementen worden alleen aangemaakt voor data die jouw specifieke voertuig
ook daadwerkelijk levert. De entiteitenlijst past zich dus automatisch aan de mogelijkheden van
je auto aan (elektrisch, plug-in hybride, of verbrandingsmotor).

Er is een **alleen-lezen modus** die je in de opties van de integratie kunt inschakelen om alle
bedieningsfuncties (vergrendelen, klimaatregeling, laden, knoppen) uit te schakelen, terwijl alle
sensoren actief blijven.

## Ondersteunde talen

De integratie bevat vertalingen voor de config flow, de opties-flow en de entiteitsnamen in:

- English (`en`)
- Nederlands (`nl`)
- Deutsch (`de`)
- Français (`fr`)
- Čeština (`cs`)
- Slovenčina (`sk`)

Home Assistant kiest automatisch de vertaling die overeenkomt met de taalinstelling van je
installatie, met Engels als terugvaloptie. Bijdragen voor extra talen zijn welkom — voeg een
nieuw bestand toe onder `custom_components/skoda_connect/translations/`.

Ook deze documentatie is beschikbaar in het [Engels](README.md) en het
[Nederlands](README.nl.md).

## Installatie

### HACS (aanbevolen)

1. Ga in HACS naar **Integraties** → menu (⋮) → **Aangepaste repositories**.
2. Voeg de URL van deze repository toe
   (`https://github.com/max1weber/Skoda-HA-Integration`) met categorie **Integration**.
3. Zoek in HACS naar "Škoda Connect", klik op **Downloaden** en installeer de integratie.
4. Herstart Home Assistant.

### Handmatig

1. Download of clone deze repository.
2. Kopieer de map `custom_components/skoda_connect` naar de map
   `config/custom_components/` van je Home Assistant-installatie, zodat je uitkomt op
   `config/custom_components/skoda_connect/manifest.json`.
3. Herstart Home Assistant.

## Configuratie

1. Ga naar **Instellingen → Apparaten en diensten → Integratie toevoegen** en zoek naar
   "Škoda Connect".
2. Vul het e-mailadres en wachtwoord in dat je ook gebruikt in de MySkoda-app.
3. Vul optioneel je S-PIN in — dit is nodig om de vergrendel-entiteit te kunnen gebruiken.
4. Home Assistant controleert de inloggegevens en maakt bij succes één apparaat aan per
   voertuig op het account, met alle van toepassing zijnde entiteiten.
5. Open na het instellen het **Configureren**-dialoogvenster van de integratie om het
   vernieuwingsinterval aan te passen (15–1440 minuten, standaard 15) of de alleen-lezen modus
   in te schakelen.

Als je sessie verloopt, toont Home Assistant een melding om "opnieuw aan te melden" — klik
erop en voer je wachtwoord opnieuw in om de verbinding te herstellen zonder de geschiedenis
van je entiteiten te verliezen.

## Over de API

Deze integratie maakt bewust gebruik van het door de community onderhouden `myskoda`
PyPI-pakket, in plaats van zelf een OAuth2/REST/MQTT-client voor Škoda te bouwen. Zo profiteert
de integratie van updates en dekking van de steeds veranderende voertuigmogelijkheden van de
API. Data wordt alleen ververst via polling — MQTT-pushmeldingen van de API worden
niet gebruikt, wat de integratie eenvoudig houdt en een extra faalpunt vermijdt.

### Officiële publieke API (nog niet gebruikt)

Škoda biedt inmiddels ook een officiële
[MySkoda Public API](https://public.api.connect.skoda-auto.cz/docs) voor externe ontwikkelaars
(authenticatie via een `X-API-Key`-header; sleutels worden in de MySkoda-app aangemaakt, zijn
aan gekozen voertuigen gebonden en verlopen). **Deze integratie gebruikt die niet.** `myskoda`
praat met de app-backend (`mysmob.api.connect.skoda-auto.cz`) en logt in met e-mail/wachtwoord
via `identity.vwgroup.io`. Migreren vraagt om een nieuwe client en een andere config flow
(API-sleutel in plaats van inloggegevens).

### Rate limits

De MySkoda API hanteert een quotum per account en geeft HTTP 429 (Too Many Requests)
terug zodra dat wordt overschreden — de `myskoda`-client zelf doet daar geen retry of backoff
op. Uit meldingen van de community (zie
[skodaconnect/homeassistant-myskoda#1053](https://github.com/skodaconnect/homeassistant-myskoda/issues/1053))
blijkt dat te agressief pollen kan leiden tot een tijdelijke rate limit, of in het ergste geval
een geblokkeerd account — vooral omdat het ophalen van de volledige status van één voertuig al
gauw 10–13 losse API-requests kost (één per ondersteunde capability, plus voertuiginfo en
onderhoudsgegevens).

Om ruim binnen het quotum te blijven, doet deze integratie het volgende:

- Standaard een vernieuwingsinterval van 15 minuten, wat ook het afgedwongen minimum is in de
  opties-flow — je kunt dus niet per ongeluk een nog korter, risicovoller interval instellen.
  Heb je meerdere voertuigen op één account, overweeg dan om dit te verhogen.
- HTTP 429/430-responses worden expliciet herkend, waarna het pollen wordt gepauzeerd. De
  `Retry-After`-header van de API wordt gerespecteerd indien aanwezig (met een terugval naar
  15 minuten, met een maximum van 1 uur, als deze ontbreekt of niet te lezen is), in plaats van
  meteen bij de volgende cyclus opnieuw te proberen.
- Er wordt een duidelijke waarschuwing gelogd wanneer dit gebeurt, zichtbaar onder
  **Instellingen → Systeem → Logboeken**, zodat het niet stilletjes te snel opnieuw probeert.

## Changelog

Zie [CHANGELOG.nl.md](CHANGELOG.nl.md) voor de release notes.

## Disclaimer

Aangeboden zoals het is, zonder garantie. Škoda Auto kan zijn API op elk moment wijzigen,
waardoor deze integratie kan stoppen met werken. Gebruik van de MySkoda API valt
onder de eigen gebruiksvoorwaarden van Škoda.
