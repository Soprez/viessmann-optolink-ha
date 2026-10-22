# Datapoint addresses / Adresses de données — Vitotronic 200 KO1B/KO2B (device ID 20CB…)

Protocol VS2 / "300", 4800 baud, 8E2. Sources: [openv wiki – Adressen](https://github.com/openv/openv/wiki/Adressen),
[vcontrold `xml/300/vito.xml`](https://github.com/openv/vcontrold). "Validated" = read and checked against the
regulation display on a Vitorondens 222-F. Scale = multiplier applied to the raw value.

## Validated (read)

| Address | Entity (`chaudiere_…`) | Len | Scale | Meaning |
|---|---|---|---|---|
| 0x0800 | aussentemperatur | 2 | 0.1 | Outside temperature |
| 0x0802 | kesseltemperatur | 2 | 0.1 | Boiler water temperature |
| 0x0804 | warmwassertemperatur | 2 | 0.1 | DHW tank temperature (actual) |
| 0x0808 | abgastemperatur | 2 | 0.1 | Flue gas temperature |
| 0x0810 | vorlauftemperature_a1m1 | 2 | 0.1 | Flow temperature, heating circuit A1M1 |
| 0x0812 | speichertemperature_tiefpass | 2 | 0.1 | Tank temperature, low-pass filtered |
| 0x0842 | zustand_1_stufe | 1 | 1 | Burner stage 1 on/off |
| 0x0884 | brennerstoerung | 1 | 1 | Burner fault code (0 = none) |
| 0x088A | brennerstarts | 4 | 1 | Burner start counter |
| 0x0896 | temperature_ambiante | 2 | 0.1 | Room temperature (remote/room sensor) |
| 0x08A7 | betriebsstunden | 4 | 1/3600 | Burner operating hours |
| 0x2544 | vorlaufsolltemperature_a1m1 | 2 | 0.1 | Flow setpoint (0 when no heat demand — normal) |
| 0x6513 | speicherladepumpe | 1 | 1 | **DHW tank charge pump** — 1 while the tank is charged |
| 0xA152 | status | 2 | 1 | Status word |
| 0xA38F | brennerleistung | 1 | 0.5 | Burner modulation (%) |
| 0x00F8 | geraetekennung | 8 | – | Device ID (read once; keep it private) |
| 0x2301 | betriebsart_2301_ro | 1 | 1 | Operating mode, **read side only** |
| 0x2306 / 0x2307 | temp_confort / temp_reduite | 1 | 1 | Comfort / reduced room setpoint (writable) |
| 0x27D3 / 0x27D4 | neigung / niveau | 1 | 0.1 / 1 | Heating curve slope / level (writable) |
| 0x6300 | ecs_consigne | 1 | 1 | DHW setpoint (writable, max 60 °C) |
| 0x2323 | betriebsart_mode | 1 | 1 | Operating mode, **write side** (see below) |

## Invalid, unreliable or trap addresses

| Address | Status | Detail |
|---|---|---|
| 0x2304 / 0x2305 | **Invalid on 20CB** | No usable answer. |
| 0x5502 | Rejected | Alternative boiler setpoint: answer is 1 byte instead of 2 and implausible. |
| 0x6500 | Unreliable | "DHW setpoint, current" — often stale or off; use 0x6300 for the setpoint. |
| 0x7574 | Always 0 | Fuel consumption needs a physical flow meter (vcontrold issue 131). Estimate from hours instead ([`ha/fuel_estimate.yaml`](../ha/fuel_estimate.yaml)). |
| 0x2302 / 0x2303 | Read-only in practice | Spar / Party write is ACKed but ignored on 20CB (openv issue 377). |
| 0x6515 | Meaningless | Read with length 2 returns a constant (25601 here) — not a circulation pump status. |
| 0x2301 | Write fails | Write returns RetCode 3. Write the mode through 0x2323. |
| 0x6300 > 60 | Rejected | 61/65/70 °C all return RetCode 3: the regulation caps DHW at 60 °C. |

## Mode values (0x2323)

| Value | Effect |
|---|---|
| 1 | Hot water only |
| 2 | Heating + hot water |
| **3** | **Do not use**: switches everything off (tested). |

0x2301 uses its own enumeration (it reads `3` while 0x2323 is set to 2 here): do not map it with the 0x2323 labels. The poll list reads and writes the mode through 0x2323.
