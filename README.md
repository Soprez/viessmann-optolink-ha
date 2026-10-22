# Viessmann Vitorondens / Vitotronic 200 in Home Assistant — free Optolink + MQTT kit and smart heating

🇫🇷 [Lire en français](README.fr.md)

**A free, effective way to connect a Viessmann oil boiler to Home Assistant.** Read and (carefully) drive a **Viessmann Vitorondens 222-F** with a **Vitotronic 200 KO1B/KO2B** regulation (device ID `20CB…`) through an **Optolink** USB adapter, a Raspberry Pi, **MQTT** and [optolink-splitter](https://github.com/philippoo66/optolink-splitter) — then add a real **smart heating** layer (planning, pre-heating, presence, holidays, hot-water indicator, oil-consumption estimate).

> This is **not a fork** and contains none of optolink-splitter's code. It is a ready-to-use poll list, a table of validated / invalid addresses, Home Assistant YAML and step-by-step guides.

![Home Assistant dashboard: burner state, room temperature, setpoint, mode, pre-heating forecast and oil tank level](docs/images/01-vue-ensemble.png)
*The boiler overview dashboard built with this kit: burner, room temperature, current setpoint, planning mode, pre-heating forecast and estimated oil level. (Heating is paused here because the house is warm enough.)*

## ☕ Support this project

This kit is free. If it saved you time, a coffee is very welcome: **[buymeacoffee.com/soprez](https://buymeacoffee.com/soprez)**.

**Heating installers and professionals (installateurs, chauffagistes):** this kit saves you hours per site — address table already validated, wiring, service, MQTT and Home Assistant ready to paste. If it helps your business, a coffee (or a few) is appreciated and keeps the project maintained.

## What you get

| | |
|---|---|
| [`optolink/poll_list.py.example`](optolink/poll_list.py.example) | Home Assistant poll list for 20CB: ~30 entities (temperatures, burner, counters, pumps, mode, heating curve, setpoints) |
| [`docs/addresses.md`](docs/addresses.md) | Which addresses work, which are invalid on 20CB, and the traps (writes ACKed but ignored, always-0 fuel counter, forbidden mode value…) |
| [`docs/guide.md`](docs/guide.md) | Hardware, Optolink wiring, udev, systemd, MQTT, Home Assistant, safety |
| [`docs/smart-heating.md`](docs/smart-heating.md) | **Smart heating** guide: planning, pre-heating, presence/holidays, override, hot-water priority, oil estimate, tank losses, FAQ |
| [`ha/smart-heating/package_chauffage_intelligent.yaml`](ha/smart-heating/package_chauffage_intelligent.yaml) | One Home Assistant package: helpers, sensors, automations |
| [`ha/dhw_running.yaml`](ha/dhw_running.yaml) | **"Hot water being produced"** binary sensor (burner + charge pump 0x6513) with an estimated end time |
| [`ha/fuel_estimate.yaml`](ha/fuel_estimate.yaml) | Oil consumption estimate from burner hours (the boiler's own counter always reads 0) |
| [`ha/publish_climate.py`](ha/publish_climate.py) | MQTT discovery of two thermostats (comfort / reduced setpoints) |
| [`ha/lovelace-example.yaml`](ha/lovelace-example.yaml) | Example dashboard view |

## Smart heating at a glance
- **Planning in Home Assistant** (Comfort / Reduced) instead of the boiler's timer.
- **Early pre-heating** from the measured heating speed of your house.
- **Cut when the house is empty** (presence) and with **holiday calendars**; manual **override** until the next slot.
- **Hot-water priority** made visible: the *"Hot water in progress"* indicator with an estimated end time.
- Heating curve (slope/level) left to the boiler; **oil estimate** with day/week/month/year counters; **tank loss** measurement.

→ Full guide with setup steps, pitfalls and FAQ: [docs/smart-heating.md](docs/smart-heating.md).

## Compatible models
- **Validated:** Viessmann **Vitorondens 222-F** (oil) with **Vitotronic 200 KO1B/KO2B**, device ID `20CB…`, protocol VS2 / "300".
- **Probably compatible** (same regulation family in the [openv address tables](https://github.com/openv/openv/wiki/Adressen), *not tested here*): other boilers fitted with a Vitotronic 200 KO1B/KO2B (for example Vitorondens 200-T, Vitoladens 300-C).
- **Other Vitotronic generations** (e.g. gas **Vitodens** with HO1B/HO2B/B2HA…): the Optolink wiring, optolink-splitter, MQTT and the Home Assistant layer all apply, but datapoint addresses differ — validate them read-only with the openv tables before writing anything.
- Check your device ID at 0x00F8 first. Tell us what works on your model by opening an issue.

## Quick start
1. Follow the [guide](docs/guide.md) up to the splitter running with the provided poll list.
2. Entities appear as `sensor.chaudiere_*`. Add [`ha/dhw_running.yaml`](ha/dhw_running.yaml) for the hot-water indicator.
3. Start **read-only**; add writes (mode, setpoints) once you trust the readings, then try the [smart heating](docs/smart-heating.md).

## ⚠️ Safety
Writing to the regulation can switch the heating off or change safety-relevant setpoints. Mode value `3` on 0x2323 switches everything off; the DHW setpoint is capped at 60 °C by the regulation. Read [the safety section](docs/guide.md#8-safety--read-before-writing-anything). Use at your own risk. Not affiliated with Viessmann.

## Credits and links
- [philippoo66/optolink-splitter](https://github.com/philippoo66/optolink-splitter) — the Optolink ↔ MQTT bridge doing all the real work (GPL-3.0). Its poll list format is used here.
- [openv/openv wiki — Adressen](https://github.com/openv/openv/wiki/Adressen) — community address tables (issue 377: Spar/Party writes on 20CB).
- [openv/vcontrold](https://github.com/openv/vcontrold) (`xml/300/vito.xml`; issue 131: fuel consumption datapoint).

## License
[GPL-3.0-or-later](LICENSE). optolink-splitter is GPL-3.0; the poll list is written in its format and is therefore distributed under the same license. The other files are released under the same license for simplicity.
