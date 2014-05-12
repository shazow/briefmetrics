import os.path, os
import uuid
import logging
import hashlib

log = logging.getLogger(__name__)

def get_cache_bust(data):
    return hashlib.md5(data).hexdigest()[:6]


def save_logo(fp, base_dir, replace_path=None, prefix=None, pretend=False):
    if not pretend and not os.path.isdir(base_dir):
        log.warning('save_logo: Base dir does not exist, making: %s' % base_dir)
        os.mkdir(base_dir)

    if not replace_path:
        replace_path = '%s.png' % uuid.uuid4().hex
    else:
        # Strip cache busting and get absolute path
        replace_path = replace_path.split('?', 1)[0]

    full_path = os.path.join(base_dir, replace_path)

    data = fp.read()

    # TODO: Resize

    if not pretend:
        log.info('Writing logo (%d bytes): %s' % (len(data), full_path))
        with open(full_path, 'wb') as out_fp:
            out_fp.write(data)


    # Append cache busting
    replace_path += '?%s' % get_cache_bust(data)

    return replace_path

