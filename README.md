# VCMI Project mods repository

Check detailed description of [mods respository on our wiki](https://wiki.vcmi.eu/Mods_repository).

## Adding mod

If you have a mod you'd like to include into deafult VCMI Launcher mod list,
please submit [request](https://github.com/vcmi/vcmi-mods-repository/issues/new/choose) in the following format with "new mod" or "update" label
```JSON
"vcmi": {
  "name" : "VCMI essential files", 
	"description" : "Essential files required for VCMI to run correctly",
	"version" : "1.03",
	"author" : "VCMI Team",
	"contact" : "http://forum.vcmi.eu/index.php", //optional
	"modType" : "Graphical",
  "screenshots": //optional
  [
	  "https://raw.githubusercontent.com/vcmi-mods/vcmi-essential-files/master/screenshot01.png"
	],
  "changelog" : //optional
	{
		"0.1" : [ "Initial release", "Some features added" ]
	},
	"download": "https://github.com/vcmi-mods/vcmi-essential-files/archive/refs/heads/master.zip"	
},
```

### Mod compliance

Official repository, available in VCMI by default, shall not contain links, leading to external storages and web sites.
We support only the links to GitHub archive service.
Also, mod or it's parts shall not contain any of archives (except natively supported by VCMI engine but not zip).
Non compiant mods will be added into experimental repositories which are not available from the launcer by default.

## Other links

 * Homepage:   https://vcmi.eu/
 * Wiki:       https://wiki.vcmi.eu/
 * Forums:     https://forum.vcmi.eu/
 * Bugtracker: https://bugs.vcmi.eu/
 * Slack:      https://slack.vcmi.eu/
