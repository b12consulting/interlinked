from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Any
from collections import defaultdict
import re


# From the re module doc:
#     Ranges of characters can be indicated by giving two characters and
#     separating them by a '-', for example [a-z] will match any lowercase
#     ASCII letter, [0-5][0-9] will match all the two-digits numbers from 00
#     to 59, and [0-9A-Fa-f] will match any hexadecimal digit. If - is
#     escaped (e.g. [a\-z]) or if it’s placed as the first or last character
#     (e.g. [-a] or [a-]), it will match a literal '-'.

ID_PATTERN = "[a-z][a-z0-9:_]+"
VALUE_PATTERNS = {
    "identifier": "[a-z][a-z0-9_]*",
    "str": "[a-z0-9:+._ -]+",
    "int": "[-+]?[0-9]+",
    "path": "[a-z0-9./_-]+",
    # ISO 8601 datetime format
    # from https://www.oreilly.com/library/view/regular-expressions-cookbook/9781449327453/ch04s07.html
    "datetime": (
        r"(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])"
        r"T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(.[0-9]+)?"
        r"(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?"
    ),
    "date": (
        r"(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])"
    ),
    "uuid": "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[a-f0-9]{4}-?[a-f0-9]{12}",
}
PARAM_REGEX = re.compile("{(" + ID_PATTERN + ")}", re.I)


@dataclass
class RouteInfo:
    route: str
    regex: re.Pattern
    value: Any
    types: dict[str, str]
    kw: dict[str, str]

    def clone(self, kw: dict):
        """
        Return an object copy with added kw.
        """
        return RouteInfo(
            route=self.route,
            regex=self.regex,
            value=self.value,
            types=self.types,
            kw=kw,
        )

    @property
    def typed_kw(self):
        """
        Return a dictionary with the kw values converted to the proper type.
        """
        if not self.kw:
            return {}
        return {key: self.auto_type(key) for key in self.kw}

    def auto_type(self, key):
        value = self.kw[key]
        kw_type = self.types[key]

        match kw_type:
            case "int":
                return int(value)
            case "datetime":
                return datetime.fromisoformat(value)
            case "date":
                return datetime.fromisoformat(value).date()
        return value



class Router:
    def __init__(self, **routes: Any):
        self.routes = defaultdict(set)
        self.add_routes(routes)

    def add_routes(self, routes: dict[str, Any]):
        for path, value in routes.items():
            self.add(path, value)

    def clone(self):
        """
        Return a proper copy of the current router.
        """
        # Unpack value tuples and pass results to constructor
        router = Router()
        router.routes = self.routes.copy()
        return router

    def add(self, path: str, value: Any):
        """
        Add the given value under the key containing the parameterized
        path.
        """
        if "{}" in path:
            msg = "Anonymous pattern '{}' is not supported (in %s)"
            raise ValueError(msg % path)

        idx = 0
        path_regex = "^"
        types = {}
        for match in PARAM_REGEX.finditer(path):
            (param_name,) = match.groups()
            if ":" in param_name:
                param_name, param_type = param_name.split(":")
            else:
                param_type = "str"

            ptrn = VALUE_PATTERNS[param_type]
            types[param_name] = param_type

            path_regex += re.escape(path[idx : match.start()])
            path_regex += f"(?P<{param_name}>{ptrn})"
            idx = match.end()

        path_regex += re.escape(path[idx:].split(":")[0]) + "$"
        self.routes[path] = RouteInfo(
            route=path,
            regex=re.compile(path_regex, re.I),
            value=value,
            types=types,
            kw={},
        )

    def match(self, key: str) -> Optional[RouteInfo]:
        """
        Return a tuple (value, match dict) if key is found. Return None if
        not.
        """
        # Test for exact match
        res = self.routes.get(key)
        if res is not None:
            return res

        # Test patterns
        for route, route_info in self.routes.items():
            if res := route_info.regex.match(key):
                return route_info.clone(kw=res.groupdict())
        return None

    def get(self, key: str, default: Any = None):
        """
        Helper method that simply return the value associated to the matched
        key, or default if the key is not known.
        """
        res = self.match(key)
        if res is None:
            return default
        return res.value

    def __contains__(self, key: str):
        return key in self.routes
