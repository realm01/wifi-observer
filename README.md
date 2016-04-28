wifi-observer
=============
Description
-----------
With this software you can observe *n* wifi *ssids*

checks
------
There are following checks implemented:
  - time needed to connect to ssid
  - average time needed for *n* pings in the connected wifi
  - dbm

this data with *ssid*, *bssid* and *start time* are logged into a sqlite database.

Deployment
----------
```sh
$ sqlite3 wifi-observer.db < wifi-observer.db.sql
$ vim wifi-observer.conf
  # adapt to your needed

$ python3.4 observer.py   # run observer
```