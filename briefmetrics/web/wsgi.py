import os
here = os.path.dirname(__file__)

ini_path = os.path.join(here, '../../production.ini')

from paste.deploy import loadapp
application = loadapp('config:%s' % ini_path, relative_to='.')

import logging
import logging.config
logging.config.fileConfig(ini_path)
