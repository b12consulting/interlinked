from collections import namedtuple, defaultdict
import re

Match = namedtuple('Match', ['value', 'kw'])
ID_PATTERN = "[a-zA-Z][a-zA-Z0-9_]*"
PARAM_REGEX = re.compile("{(" + ID_PATTERN + ")}")


class Router:

    def __init__(self, **routes):
        self.routes = defaultdict(set)
        for path, value in routes.items():
            self.add(path, value)

    def clone(self):
        '''
        Return a proper copy of the current router.
        '''
        # Unpack value tuples and pass results to constructor
        routes = {path: item for path, (_, item) in self.routes.items()}
        return Router(**routes)

    def add(self, path, value):
        '''
        Add the given value under the key containing the parameterized
        path.
        '''
        if "{}" in path:
            msg = "Anonymous pattern '{}' is not supported (in %s)"
            raise ValueError(msg % path)

        idx = 0
        path_regex = "^"
        for match in PARAM_REGEX.finditer(path):
            param_name, = match.groups()
            path_regex += re.escape(path[idx: match.start()])
            path_regex += f"(?P<{param_name}>{ID_PATTERN})"
            idx = match.end()

        path_regex += re.escape(path[idx:].split(":")[0]) + "$"
        self.routes[path] = (re.compile(path_regex), value)

    def match(self, key):
        """
        Return a tuple (value, match dict) if key is found. Return None if
        not.
        """
        # Test for exact match
        res = self.routes.get(key)
        if res is not None:
            _, value = res
            return Match(value, {})
        # Test pattern
        for route, (regex, value) in self.routes.items():
            m = regex.match(key)
            if not m:
                continue
            return Match(value, m.groupdict())
        return None

    def get(self, key, default=None):
        """
        Helper method that simply return value associated to the matched
        key, or default if the key is not known.
        """
        res = self.match(key)
        if res is None:
            return default
        return res[0]

    def __contains__(self, key):
        return key in self.routes
