from PIL import Image
from io import BytesIO
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

    # Resize
    try:
        image = Image.open(BytesIO(data))
    except IOError, e:
        log.error("save_logo: Failed to open image '%s' (%d bytes): %r" % (file.path, len(data), e))
        raise ValueError("Failed to read image: %s" % fp.filename)

    if image.mode == 'P':
        # Some people have uploaded jpeg images that are actually PNGs -- deal with this
        image = image.convert('RGB')

    original_x, original_y = image.size
    x, y = resize_dimensions(original_x, original_y, max_width=560)
    image.thumbnail([x, y], Image.ANTIALIAS)

    if not pretend:
        log.info('Writing logo (%d bytes): %s' % (len(data), full_path))
        with open(full_path, 'wb') as out_fp:
            image.save(out_fp, format="PNG")

    # Append cache busting
    replace_path += '?%s' % get_cache_bust(data)

    return replace_path


def resize_dimensions(x, y, max_width=None, max_height=None, min_side=None, max_side=None):
    if not any([max_width, max_height, min_side, max_side]):
        return x, y

    if max_width and x > max_width:
        ratio = max_width / float(x)
        x *= ratio
        y *= ratio

    if max_height and y > max_height:
        ratio = max_height / float(y)
        y *= ratio
        x *= ratio

    biggest_side = max(x, y)
    if max_side and biggest_side > max_side:
        ratio = float(max_side) / biggest_side
        x *= ratio
        y *= ratio

    smallest_side = min(x, y)
    if min_side and smallest_side > min_side:
        ratio = float(min_side) / smallest_side
        x *= ratio
        y *= ratio

    return int(round(x)), int(round(y))
