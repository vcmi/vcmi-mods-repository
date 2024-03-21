# VCMI mods repository

For a detailed description of this repository, see the [VCMI wiki](https://github.com/vcmi/vcmi/blob/develop/docs/modders/Readme.md#publishing-mods-in-vcmi-repository).

## Adding a mod

If you have a mod you'd like included in the default list of mods in the VCMI launcher,
please submit a [pull request](https://github.com/vcmi/vcmi-mods-repository/compare).
The PR needs to add a JSON object to the `vcmi-x.y.json` file corresponding to the version your mod is targeting.
Tag the PR with with either the `new mod` or `improvement` label.
```jsonc
{
	[...]
	"refugee-town" : {
		"mod" : "https://raw.githubusercontent.com/vcmi-mods/refugee-town/vcmi-1.4/refugee-town/mod.json",
		"download" : "https://github.com/vcmi-mods/refugee-town/archive/refs/heads/vcmi-1.4.zip",
		"screenshots" : [ // optional
			"https://raw.githubusercontent.com/vcmi-mods/refugee-town/main/screenshots/screen1.png",
			"https://raw.githubusercontent.com/vcmi-mods/refugee-town/main/screenshots/screen2.png",
			"https://raw.githubusercontent.com/vcmi-mods/refugee-town/main/screenshots/screen3.png",
			"https://raw.githubusercontent.com/vcmi-mods/refugee-town/main/screenshots/screen4.png",
			"https://raw.githubusercontent.com/vcmi-mods/refugee-town/main/screenshots/screen5.png"
		]
	},
	[...]
}
```

The `mod.json` referenced in the entry in vcmi-x.y.json should be structured like this:
```jsonc
{
  "name": "Refugee Town (release)",
  "description": "Refugee Town is a new town created by Yuya that takes its inspiration from WoG's Neutral Town and Heroes3's Refugee Camp. The common point of its creatures is their nonbelonging to the other factions. Thus, this castle sports concepts such as nomadism, motley armies and makeshift solutions. The town also takes elements from the Mesopotamian/Sumerian/Akkadian mythologies. Official VCMI Forum https://forum.vcmi.eu/t/new-town-mod-refugee/5002",
  "author": "Yuya Noboru (v0.1-v0.4, v0.8-v1.0), VCMI Community (v0.5-v0.7, v0.8.1-v0.8.5)",
  "version": "1.0",
  "contact": "mail: yuya.noboru@gmail.com", // optional
  "modType": "Town",
  "compatibility": {
    "min": "1.4.0"
  },
  "changelog": { // optional
    "Note": [
      "See 'RefugeeTown-Changelog.txt' file inside the mod to see the full changelog. Or go to the VCMI forum on the official thread: https://forum.vcmi.eu/t/new-town-mod-refugee/5002"
    ],
    "v1.0.1 (11/02/2024)": [
      "Udated chinese translation. - by Rindlit."
    ],
    "v1.0 (09/01/2024)": [
      "BRAND NEW VISUALS FOR TOWN-SCREEN, SIEGE-SCREEN, ADV.MAP VISUALS, ETC.!",
    ]
  },
  "french": {
    "name": "Réfugiés",
    "description": "Réfugiés est une ville créée par Yuya qui s'inspire de la ville neutre de WoG, ainsi que des camps de réfugiés d'Heroes 3. Le point commun de ses créatures est leur non-appartenance aux autres factions. Ainsi, ce château arbore des concepts tels que le nomadisme, les armées hétéroclites et les solutions de fortune. La ville reprend également des éléments des mythologies mésopotamiennes, sumériennes et akkadiennes. Forum officiel VCMI https://forum.vcmi.eu/t/new-town-mod-refugee/5002",
    "translations": [
      "translation/refugee/french.json"
    ]
  },
  "german": {
    "name": "Flüchtlings-Stadt",
    "description": "Flüchtlings-Stadt ist eine von Yuya erschaffene Stadt, die von WoG's Neutral Town und Heroes3's Refugee Camp inspiriert wurde. Der gemeinsame Punkt seiner Kreaturen ist ihre Nicht-Zugehörigkeit zu den anderen Fraktionen. So finden sich in dieser Burg Konzepte wie Nomadentum, bunt zusammengewürfelte Armeen und Behelfslösungen. Die Stadt nimmt auch Elemente aus der mesopotamischen/sumerischen/akkadischen Mythologie auf. Offizielles VCMI-Forum https://forum.vcmi.eu/t/new-town-mod-refugee/5002",
    "translations": [
      "translation/refugee/german.json"
    ]
  },
  "factions": [
    "config/town/buildings.json"
  ],
  "creatures": [
    "config/creatures/RFGCL1L.json"
  ],
  "heroClasses": [
    "config/classes/RFGHC-EnchanterF.json"
  ],
  "heroes": [
    "config/heroes/RFGH-Leyla.json",
    "config/heroes/RFGH-Niusha.json",
    "config/heroes/RFGH-Kiana.json"
  ],
  "spells": [
    "config/spells/RFGS-Emet.json",
    "config/spells/RFGS-Met.json"
  ],
  "objects": [
    "config/town/dwellings.json"
  ]
}
```

### Mod compliance

The official mods repository, available in VCMI by default, shall not contain links leading to domains other than GitHub.
Also, mods shall not contain any archives (except those that are natively supported by VCMI but not zip).
Non-compliant mods can be added into experimental repositories which are not available in the launcher by default.

## Other links

 * Homepage:   https://vcmi.eu/
 * Wiki:       https://github.com/vcmi/vcmi/blob/develop/docs/Readme.md
 * Forums:     https://forum.vcmi.eu/
 * Bugtracker: https://bugs.vcmi.eu/
 * Discord:    https://discord.gg/chBT42V
 * Slack:      https://slack.vcmi.eu/
