import os.path
import uuid
import logging

log = logging.getLogger(__name__)



def save_logo(fp, base_dir, replace_path=None, prefix=None):
    data = fp.read()
    fp.seek(0) # Reset just in case.

    if replace_path:
        replace_path = os.path.join(base_dir, replace_path)
    else:
        filename = '%s.png' % uuid.uuid4().hex
        replace_path = os.path.join(base_dir, filename)

    log.info('Writing logo: %s' % replace_path)
    with open(replace_path, 'wb') as out_fp:
        out_fp.write()

    # TODO: Resize

    return replace_path

