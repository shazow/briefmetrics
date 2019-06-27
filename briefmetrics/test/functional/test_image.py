# TODO: Put this in a lib test submodule?

from io import BytesIO

from briefmetrics import test
from briefmetrics.lib import image

LOGO_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

class TestLibImage(test.TestCase):
    def test_save_logo(self):
        fp = BytesIO(LOGO_BYTES)
        replace_path = '1-foo.png'
        expected_name = replace_path + '?' + image.get_cache_bust(LOGO_BYTES)

        new_path = image.save_logo(fp=fp, base_dir='/does/not/exist', replace_path=replace_path, prefix='1-', pretend=True)
        self.assertEqual(new_path, expected_name)

        fp.seek(0)
        new_path = image.save_logo(fp=fp, base_dir='/does/not/exist', prefix='1-', pretend=True)
        self.assertEqual(new_path[-11:], expected_name[-11:])
