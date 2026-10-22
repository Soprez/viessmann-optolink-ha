# Chauffage intelligent avec une chaudière Viessmann (guide d'utilisation)

English: [smart-heating.md](smart-heating.md)

Ce guide décrit un **chauffage intelligent** construit sur ce kit : Home Assistant pilote les consignes de la Vitotronic 200 (Vitorondens, fioul) à la place de son programme horaire, apprend la vitesse de chauffe de la maison, coupe quand tout le monde est parti, respecte la priorité de l'eau chaude et estime la consommation de fioul. Tout est **gratuit** et reproductible avec les fichiers du dépôt : [`ha/smart-heating/package_chauffage_intelligent.yaml`](../ha/smart-heating/package_chauffage_intelligent.yaml) (package unique : helpers, capteurs, automatisations) et [`ha/dhw_running.yaml`](../ha/dhw_running.yaml).

> Les YAML viennent d'une installation réelle (Vitorondens 222-F) et ont été généralisés (noms et calendriers d'exemple). **Testez automatisations désactivées**, surveillez le journal, et gardez l'afficheur de la chaudière comme référence.

## Ce que ça apporte
- **Confort** : la maison est à la bonne température *à l'heure voulue* (pré-chauffe), pas 2 h après.
- **Économies** : consigne réduite quand personne n'est là, coupure en vacances, pas de surchauffe inutile ; fioul visible par jour/semaine/mois/année.
- **Visibilité** : ce que fait la chaudière (brûleur, eau chaude en cours, pertes du ballon) est lisible d'un coup d'œil, sans aller devant la régulation.

## Comment ça marche, brique par brique

### 1. Planning Confort / Réduit dans Home Assistant
Un helper `schedule` (`schedule.chauffage_confort`) remplace le programme horaire de la chaudière : *allumé* = Confort, *éteint* = Réduit. Vous l'éditez dans l'interface (plusieurs plages par jour). L'automatisation **« Chauffage intelligent - planning »** calcule la cible du moment et écrit **les deux** consignes de la chaudière (normale 0x2306 et réduite 0x2307), car la chaudière suit la consigne de sa propre phase horaire : il faut qu'elles soient identiques, sinon la phase « réduit » interne de la Vitotronic reprend la main.

> ⚠️ La Vitotronic n'accepte que des **degrés entiers** pour ces consignes. La cible exacte (19,5) est arrondie au degré supérieur (20) avant écriture.

### 2. Pré-chauffe anticipée
La vitesse de chauffe mesurée (°C/h) sert à calculer *combien de temps avant* la plage Confort il faut démarrer : `(cible − ambiante) / vitesse`. Un **verrou** (« pré-chauffe en cours ») évite les basculements quand la température frôle la cible : la pré-chauffe démarre si l'écart dépasse 0,2 °C dans la fenêtre d'avance, puis reste active jusqu'à la plage Confort. Le capteur `sensor.chauffage_avance_pre_chauffe` donne l'avance calculée (plafonnée par « avance maximum »).

La vitesse est **apprise** par l'automatisation « mesure vitesse de chauffe » : à chaque montée de consigne d'au moins 0,5 °C, elle mesure la montée réelle jusqu'à la cible (6 h max) et met à jour la vitesse par moyenne exponentielle 70/30. Au début, la valeur initiale (0,5 °C/h) est approximative : laissez quelques jours tourner.

### 3. Maison vide et vacances
Deux cas coupent le Confort (la cible redevient « Réduit », pré-chauffe comprise) :
- **présence** : `zone.home` à 0 (aucune personne dans la zone domicile) ;
- **calendriers de vacances** : un calendrier par personne (Google, local…) où un événement « toute la journée » signifie *absent*. La maison est « vide » quand **tous** les calendriers sont allumés. Le kit fournit deux calendriers d'exemple (`calendar.vacances_occupant_1`, `_2`) à remplacer par les vôtres.

### 4. Dérogation
Changer à la main la **consigne du moment** (widget, application ou interface) pose une *dérogation* : la cible devient cette valeur jusqu'au **prochain changement de créneau** Confort/Réduit, ou jusqu'à ce que vous coupiez le booléen « Dérogation en cours ». Pendant une pré-chauffe, la cible est le maximum entre la dérogation et le Confort. La dérogation est ignorée quand la maison est vide.

### 5. Priorité à l'eau chaude et indicateur « Eau chaude en cours »
La Vitotronic donne par défaut la **priorité à la production d'eau chaude** (paramètre de la régulation, à vérifier chez vous) : pendant que le ballon se charge (pompe de charge 0x6513 à 1, brûleur allumé), le circuit de chauffage est en retrait. C'est pourquoi une montée de consigne le soir (quand le ballon chauffe souvent) paraît « sans effet » pendant un moment. Le capteur [`binary_sensor.production_d_eau_chaude_en_cours`](../ha/dhw_running.yaml) l'affiche, avec une **heure de fin estimée** (`fin_estimee`, calculée avec la consigne 0x6300 et la vitesse de montée du ballon). Vous pouvez en faire une carte conditionnelle en haut du tableau de bord ([exemple](../ha/lovelace-example.yaml)).

Autres automatisations eau chaude du package : planning de la consigne ECS (0x6300 = température voulue, ou 10 °C pour couper), **relance automatique** si le ballon chute vite pendant une plage coupée (gros puisage), fin de marche forcée.

### 6. Courbe de chauffe laissée à la chaudière
La pente (0x27D3) et le niveau (0x27D4) de la **courbe de chauffe** restent gérés par la chaudière (régulation en fonction de la température extérieure). Le kit les expose en lecture/écriture pour le réglage fin, mais le chauffage intelligent ne les modifie pas : il agit seulement sur les consignes ambiantes. Règle pratique : si la maison est trop froide *par grand froid* alors qu'elle est bonne par temps doux, augmentez la pente ; si elle est trop chaude/froide partout, changez le niveau.

### 7. Consommation de fioul et compteurs par période
Le compteur de fioul de la chaudière (0x7574) reste à 0 sans débitmètre. Le kit l'**estime** : heures de brûleur (0x08A7) × débit nominal du brûleur (plaque signalétique, en kg/h) ÷ densité (0,84 kg/L), voir [`ha/fuel_estimate.yaml`](../ha/fuel_estimate.yaml). Le package ajoute des compteurs jour / semaine / mois / année (`utility_meter`). Recalez l'estimation avec vos livraisons réelles (± 15 % typique).

### 8. Perte du ballon mesurée
`sensor.eau_chaude_bilan_ballon` (°C/h) = montée pendant la charge − pertes. Les pertes dépendent de l'écart avec l'ambiance et se règlent avec `input_number.ecs_pertes_ballon` (°C/h perdus quand le ballon est à 32 °C au-dessus de la pièce). Pour la mesurer : coupez la production la nuit, notez la baisse de température entre minuit et le matin sans puisage, et ajustez jusqu'à ce que le bilan nocturne soit proche de la baisse réelle. `sensor.eau_chaude_tiree_estimee` estime les litres tirés (chute de température depuis minuit, volume du ballon, températures robinet et eau froide).
**Conseils** : ordre de grandeur pour un ballon bien isolé : 0,3–0,6 °C/h (mesurez le vôtre) ; baisser la consigne ECS de 5 °C réduit les pertes et le fioul ; couper l'ECS la nuit n'économise que si les pertes sont importantes (la relance du matin compense).

## Mise en route pas à pas
1. Installez le kit ([guide](guide.fr.md)) : les entités `*.chaudiere_*` doivent exister.
2. Ajoutez [`ha/dhw_running.yaml`](../ha/dhw_running.yaml) et [`ha/fuel_estimate.yaml`](../ha/fuel_estimate.yaml).
3. Copiez le package dans `packages/` (voir l'en-tête du fichier pour activer les packages), remplacez les calendriers, redémarrez Home Assistant.
4. **Désactivez** les automatisations du package, réglez les cibles Confort / Réduit et le planning.
5. Notez les consignes d'origine de la chaudière (0x2306 / 0x2307) pour pouvoir revenir.
6. Activez « Chauffage intelligent actif », observez le journal pendant 2–3 jours, puis activez la mesure de vitesse.

## Pièges
- **Mode de fonctionnement (betriebsart)** : seules les valeurs 1 (eau chaude seule) et 2 (chauffage + eau chaude) sont sûres sur 0x2323. **Jamais 3** (coupe tout). Le chauffage intelligent ne touche pas au mode.
- **Spar / Party** (0x2302 / 0x2303) : l'écriture est acquittée mais **ignorée** sur 20CB (openv issue 377). N'en faites pas une fonction « économie » ou « fête ».
- Consignes **entières** seulement ; écho de lecture périmé juste après une écriture (le pont relit l'ancienne valeur ~30 s) : ne déclenchez pas de logique « réglage manuel » sur une valeur qui vient de changer sans la stabiliser 60 s.
- 0x6500 (consigne ECS courante) peu fiable : utilisez 0x6300.
- La pompe de charge 0x6513 est lue toutes les ~30 min par défaut : placez-la dans le groupe `OFTEN` (voir la poll list du kit).
- Sécurité : lecture seule d'abord ; voir [la section sécurité](guide.fr.md#8-sécurité--à-lire-avant-toute-écriture).

## FAQ
**Pourquoi pas le programme de la chaudière ?** Il ne connaît ni la présence, ni les vacances, ni la vitesse de chauffe réelle de la maison.
**Ça marche sur ma Vitodens / ma chaudière gaz ?** Le principe oui ; les adresses sont celles de la régulation Vitotronic 200 KO1B/KO2B (20CB) et peuvent différer : validez-les en lecture.
**Et si Home Assistant plante ?** Les consignes restent écrites dans la chaudière (régulation autonome), qui continue avec la dernière valeur.
**Puis-je garder mon programme d'origine ?** Oui : désactivez « Chauffage intelligent actif » et remettez les consignes d'origine.
**L'eau chaude passe avant le chauffage, est-ce un défaut ?** Non, c'est la priorité normale de la Vitotronic ; l'indicateur le rend visible.
**Combien de temps avant que la pré-chauffe soit juste ?** Quelques mesures (quelques jours) pour apprendre la vitesse.
