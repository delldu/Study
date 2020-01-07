import collections


class Args(collections.OrderedDict):
    """Behaves like a dict but allow access with the attribute."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]


if __name__ == '__main__':
    abc = Args()
    abc.fff = 'fff'
    abc.ggg = 'ggg'
    abc.abc = '123'
