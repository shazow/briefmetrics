import yaml
import os


DONE = []
TODO = []


try:
    path = os.path.join(os.path.dirname(__file__), '../../changes.yaml')
    with open(path) as fp:
        r = yaml.load(fp)

    DONE = r.get('done', [])
    TODO = r.get('todo', [])

except IOError:
    pass
