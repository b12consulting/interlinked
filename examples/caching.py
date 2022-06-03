from datetime import date, timedelta
import logging

from requests import get

from interlinked import run, provide, depend, default_workflow

logging.basicConfig(level="INFO")
log = logging.getLogger("example")
wkf = default_workflow


@provide('temperature_{city}')
def temperature(for_date, city):
    log.info('Fetching temperature for %s @ %s', city, for_date)
    url = f"http://wttr.in/{city}?format=j1"
    resp = get(url).json()
    res = 0
    for item in resp["weather"]:
        if item["date"] == for_date.isoformat():
            res = int(item["avgtempC"])
    return res


@depend(t_bru='temperature_brussels', t_par='temperature_paris')
@provide('temperature_average')
def average(t_bru, t_par, for_date):
    log.info('Compute avg @ %s', for_date)
    return t_par, t_bru


custom_cache = {}
def runner(ressource, for_date):
    if (ressource, for_date) in custom_cache:
        return custom_cache[ressource, for_date]

    res = wkf.run(ressource, for_date=for_date)
    custom_cache[ressource, for_date] = res
    return res


# Use custom resolver
wkf.resolve = runner
today = date.today()
tomorrow = today + timedelta(days=1)
run("temperature_average", for_date=today)
run("temperature_average", for_date=today)
run("temperature_average", for_date=tomorrow)

## Output (dependecies are cached)
# INFO:example:Fetching temperature for brussels @ 2022-06-02
# INFO:example:Fetching temperature for paris @ 2022-06-02
# INFO:example:Compute avg @ 2022-06-02
# INFO:example:Compute avg @ 2022-06-02
# INFO:example:Fetching temperature for brussels @ 2022-06-03
# INFO:example:Fetching temperature for paris @ 2022-06-03
# INFO:example:Compute avg @ 2022-06-03

# Call custom resolver directly (second call is cached)
runner("temperature_average", for_date=today)
runner("temperature_average", for_date=today)

## Output
# INFO:example:Compute avg @ 2022-06-02
