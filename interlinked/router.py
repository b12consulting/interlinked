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
    "str": "[a-z0-9:._-]+",
    "int": "[-+]?[0-9]+",
    "path": "[a-z0-9./_-]+",
    "uuid": "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[a-f0-9]{4}-?[a-f0-9]{12}",
}
PARAM_REGEX = re.compile("{(" + ID_PATTERN + ")}", re.I)


@dataclass
class Match:
    route: str
    value: Any
    kw: dict


class Router:
    def __init__(self, **routes: dict[str, Any]):
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
        for match in PARAM_REGEX.finditer(path):
            (param_name,) = match.groups()
            if ":" in param_name:
                param_name, param_type = param_name.split(":")
            else:
                param_type = "str"

            ptrn = VALUE_PATTERNS.get(param_type, VALUE_PATTERNS["str"])

            path_regex += re.escape(path[idx : match.start()])
            path_regex += f"(?P<{param_name}>{ptrn})"
            idx = match.end()

        path_regex += re.escape(path[idx:].split(":")[0]) + "$"
        self.routes[path] = (re.compile(path_regex, re.I), value)

    def match(self, key: str) -> Optional[Match]:
        """
        Return a tuple (value, match dict) if key is found. Return None if
        not.
        """
        # Test for exact match
        res = self.routes.get(key)
        if res is not None:
            _, value = res
            return Match(key, value, {})
        # Test pattern
        for route, (regex, value) in self.routes.items():
            m = regex.match(key)
            if not m:
                continue
            return Match(route, value, m.groupdict())
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
