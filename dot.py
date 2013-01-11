#!/usr/bin/env python

import re
import collections

header_regex = re.compile(r'"(?P<name>[^"]+)" \[label="(?P<label>[^"]+)"\]')
line_regex = re.compile(r'"(?P<src>[^"]+)" -> "(?P<dest>[^"]+)"( \[style=dashed\])?')

def parse_depends(dotfile):
    depends = collections.defaultdict(set)
    dotfile = open(dotfile, "rU")
    for line in dotfile:
        header = re.match(header_regex, line)
        if header:
            continue

        depline = re.match(line_regex, line)
        if depline:
            depends[depline.group('src')].add(depline.group('dest'))
    return depends

def _get_all_depends(depends, target, seen):
    for node in depends[target]:
        if node in seen:
            continue
        seen.add(node)

        for depend in _get_all_depends(depends, node, seen):
            yield depend

        yield tuple(node.split('.'))


def get_all_depends(depends, target):
    return _get_all_depends(depends, target, set())


if __name__ == '__main__':
    import sys
    try:
        dotfile = sys.argv[1]
        target = sys.argv[2]
    except IndexError:
        sys.exit("Usage: python %s DOTFILE TARGET" % __file__)

    depends = parse_depends(dotfile)
    for recipe, task in get_all_depends(depends, target):
        print("%s.%s" % (recipe, task))
