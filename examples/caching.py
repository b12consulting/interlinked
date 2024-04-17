"""
This example demonstrate the effect of simply adding lru_cache decorator
"""

from functools import lru_cache
from datetime import date, timedelta
import logging

from requests import get

from interlinked import run, provide, depend, default_workflow

logging.basicConfig(level="INFO")
log = logging.getLogger("example")
wkf = default_workflow


@provide('temperature_{city}')
@lru_cache
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
