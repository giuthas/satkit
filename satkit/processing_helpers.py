
import itertools


def product_dict(**kwargs):
    """
    Produce a list of dicts of the cartesian product of lists in a dict.

    ```python
    options = {"number": [1,2,3], "color": ["orange","blue"] }
    print(list(product_dict(options)))

    [ {"number": 1, "color": "orange"},
    {"number": 1, "color": "blue"},
    {"number": 2, "color": "orange"},
    {"number": 2, "color": "blue"},
    {"number": 3, "color": "orange"},
    {"number": 3, "color": "blue"}
    ]
    ```

    Yields
    ------
    list of dicts
        See example above.
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))
