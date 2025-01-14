# Flight Watcher

This script is a companion for standard installs of the [ultrafeeder](https://github.com/sdr-enthusiasts/docker-adsb-ultrafeeder) container. You also need a target [ntfy](https://ntfy.sh/) server and topic you're subscribed to.

The aircraft that can be seen by the [tar1090](https://github.com/wiedehopf/tar1090) application are available at `https://tar1090.example.com/data/aircraft.binCraft.zst`. This is a compressed binary format. In order to parse this data, I modified the [binCraft-decoder](https://github.com/acarsGuy/binCraft-decoder) library so that it calls this tar1090 API endpoint instead of reading a file.

# Usage

1. Setup environment
`pip install -r requirements.txt`

2. Set enviornment variables in `conf.yml`. The default setup is for purely selfhosted tar1090 and ntfy servers available on localhost, and the setup for St Stephen's Green in Dublin. You'll want to change all of those variables.

3. Run the script. I run it as a cron job scheduled for every minute, you can run it however you want.

# Rate Limits

`adsb.lol` has a rate limit of 1 req per second if you're not feeding data and 2 if you are. This script is setup so that it never exceeds the 1 req per second limit, leaving you space to run this script as often as you want without interfering with users on your tar1090 web app (which also depends on adsb.lol APIs).

# Useful Links

* https://github.com/sdr-enthusiasts/docker-adsb-ultrafeeder
* https://api.adsb.lol/docs#/v0/api_routeset_api_0_routeset_post
* https://github.com/acarsGuy/binCraft-decoder
* https://docs.ntfy.sh/