# Guide pas à pas (français)

English: [guide.md](guide.md)

## 1. Matériel
- Une chaudière Viessmann avec régulation **Vitotronic 200 KO1B/KO2B** (testé sur une Vitorondens 222-F, fioul). Lisez l'identifiant d'appareil en 0x00F8 : ce kit vise les identifiants commençant par `20CB`.
- Un **adaptateur Optolink USB** (tête infrarouge qui se fixe sur le hublot optique de la régulation). Celui utilisé ici a une puce USB-série CH340. Toute tête Optolink-USB équivalente convient.
- Un petit ordinateur Linux toujours allumé (Raspberry Pi) près de la chaudière, et une instance Home Assistant avec l'add-on Mosquitto.

## 2. Câblage
1. Fixez la tête Optolink sur le hublot optique de la Vitotronic (aimant/anneau, câble vers le bas).
2. Branchez le côté USB sur le Pi. `dmesg | grep -i ch341` doit montrer un `ttyUSB0`.
3. Paramètres série : **4800 bauds, 8 bits, parité paire, 2 bits d'arrêt (8E2)**, protocole VS2 (« 300 »).

## 3. Nom de port stable (udev)
`/etc/udev/rules.d/99-optolink.rules` :
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="vitocom"
```
Puis `sudo udevadm control --reload && sudo udevadm trigger` : le port est `/dev/vitocom`.

## 4. Installer optolink-splitter (non inclus)
```
git clone https://github.com/philippoo66/optolink-splitter.git
cd optolink-splitter
python3 -m venv venv && venv/bin/pip install -r requirements.txt
cp settings_ini.py.example settings_ini.py
```
Éditez `settings_ini.py` en suivant les commentaires du projet : port `/dev/vitocom`, 4800 8E2 / VS2, broker MQTT (`hôte:port`) et identifiants (`utilisateur:mot_de_passe`) de votre Mosquitto, préfixe des topics. Utilisez **un utilisateur MQTT dédié**, jamais votre compte HA.

## 5. Poll list
Copiez [`optolink/poll_list.py.example`](../optolink/poll_list.py.example) dans le dossier du splitter sous le nom attendu par votre `settings_ini.py` (ex. `homeassistant_poll_list.py`). Gardez seulement les entrées voulues ; **supprimez les blocs `number` / `select` pour rester en lecture seule**. La liste utilise la découverte MQTT de Home Assistant : les entités apparaissent seules en `sensor.chaudiere_*`.

## 6. Service systemd
`/etc/systemd/system/optolink-splitter.service` :
```
[Unit]
Description=Optolink splitter
After=network-online.target
Wants=network-online.target

[Service]
User=<votre-utilisateur-linux>
WorkingDirectory=/home/<votre-utilisateur-linux>/optolink-splitter
ExecStart=/home/<votre-utilisateur-linux>/optolink-splitter/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
`sudo systemctl daemon-reload && sudo systemctl enable --now optolink-splitter`, suivi avec `journalctl -fu optolink-splitter`. (Nom du script d'entrée : voir le README du projet.)

## 7. MQTT et Home Assistant
1. Dans HA : add-on Mosquitto + intégration MQTT, et un utilisateur MQTT dédié.
2. Vérifiez avec MQTT Explorer ou *Paramètres > Appareils > MQTT > Configurer* que `chaudiere/#` reçoit des valeurs.
3. Thermostats facultatifs : `MQTT_PASSWORD=… python3 ha/publish_climate.py` (publie deux configs climate retenues).
4. Ajoutez les éléments de [`ha/`](../ha) : `dhw_running.yaml` (indicateur eau chaude), `fuel_estimate.yaml`, et la vue d'exemple `lovelace-example.yaml`.

![Carte de réglages Home Assistant : mode de fonctionnement de la chaudière, consigne eau chaude, pente et niveau de la courbe de chauffe](images/03-reglages-chaudiere.png)
*Une carte de réglages pour les données modifiables : mode (0x2323), consigne eau chaude (0x6300), pente (0x27D3) et niveau (0x27D4) de la courbe de chauffe. Écriture : voir la section sécurité ci-dessous.*

![Page appareil MQTT dans Home Assistant : capteurs découverts depuis la poll list (températures, heures et démarrages du brûleur, modulation, départs)](images/08-entites-mqtt-capteurs.png)
*Capteurs découverts automatiquement : températures des fumées, extérieure, chaudière et eau chaude, heures du brûleur (0x08A7), démarrages (0x088A), modulation (0xA38F), départ réel/cible.*

![Page appareil MQTT dans Home Assistant : contrôles découverts depuis la poll list (mode, consigne eau chaude, pente et niveau de la courbe, consignes confort et réduite, deux thermostats)](images/07-entites-mqtt-controles.png)
*Contrôles découverts automatiquement par MQTT : mode de fonctionnement, consigne eau chaude (0x6300), pente et niveau de la courbe de chauffe (0x27D3/0x27D4), consignes confort/réduite (0x2306/0x2307) et les deux thermostats. (Le mode indique « eau chaude seule » car le chauffage était en pause par le chauffage intelligent.)*

## 8. Sécurité — à lire avant toute écriture
- **Commencez en lecture seule.** Lire est sans risque ; écrire modifie la régulation d'un chauffage.
- Mode (0x2323) : seulement **1** (eau chaude seule) et **2** (chauffage + eau chaude). **Jamais 3** (coupe tout).
- Consigne ECS (0x6300) : 60 °C maximum (la régulation refuse plus). Attention légionelles et brûlures.
- Les écritures Spar/Party (0x2302/0x2303) ne font rien sur 20CB ; ne comptez pas dessus.
- Ne scrutez pas plus vite que le défaut du splitter : l'Optolink est une liaison série lente partagée avec la régulation.
- L'afficheur de la Vitotronic reste la référence ; une automatisation HA fautive ne doit jamais être seule entre vous et une maison froide.
- À vos risques ; aucun lien avec Viessmann.
