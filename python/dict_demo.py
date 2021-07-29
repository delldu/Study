# https://docs.python.org/2/library/collections.html#collections.defaultdict


from collections import defaultdict

s = "mississippi"
d = defaultdict(int)
for k in s:
    d[k] += 1

print(d.items())
