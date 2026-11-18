import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import update_fm_rush as updater

class UpdateTests(unittest.TestCase):
    def package(self,files=None,names=None):
        files=files or {'fm_rush.py':b'new app','START_FM_RUSH.bat':b'launcher','update_fm_rush.py':b'updater'}
        stream=io.BytesIO()
        with ZipFile(stream,'w') as z:
            z.writestr('app/UPDATE_MANIFEST.json',json.dumps({'version':'test','files':list(files) if names is None else names}))
            for name,body in files.items():z.writestr('app/'+name,body)
            z.writestr('app/config.json','never install this')
            z.writestr('app/Screenshot old.png','not a runtime file')
        return stream.getvalue()

    def test_update_preserves_settings_dependencies_archives_and_images(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'fm_rush.py').write_bytes(b'old app')
            personal={'config.json':b'settings','.venv/keep':b'dependencies','archives/deals.sqlite3':b'archive','Bought/item.png':b'purchase','Screenshot mine.png':b'my image'}
            for name,body in personal.items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
            version,backup=updater.install_runtime(self.package(),root)
            self.assertEqual(version,'test');self.assertEqual((root/'fm_rush.py').read_bytes(),b'new app')
            self.assertEqual((backup/'fm_rush.py').read_bytes(),b'old app')
            for name,body in personal.items():self.assertEqual((root/name).read_bytes(),body)

    def test_failed_replacement_rolls_back_previous_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'fm_rush.py').write_bytes(b'old app')
            original=updater.os.replace;calls=[]
            def replace(src,dst):
                calls.append(dst)
                if len(calls)==2:raise OSError('disk error')
                return original(src,dst)
            with patch.object(updater.os,'replace',side_effect=replace):
                with self.assertRaises(OSError):updater.install_runtime(self.package(),root)
            self.assertEqual((root/'fm_rush.py').read_bytes(),b'old app')
            self.assertFalse((root/'START_FM_RUSH.bat').exists())
            self.assertFalse(list(root.rglob('.fm_update_*')))

    def test_protected_and_traversal_manifest_entries_rejected_before_changes(self):
        for name in ['config.json','.venv/keep','archives/data','Bought/item.png','../oops.py','assets/../config.json','C:evil.py','/evil.py',r'..\evil.py']:
            with self.subTest(name=name),self.assertRaises(ValueError):
                updater.unpack_runtime(self.package(names=['fm_rush.py','START_FM_RUSH.bat','update_fm_rush.py',name]))

    def test_missing_runtime_file_fails_before_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'fm_rush.py').write_bytes(b'old app')
            with self.assertRaises(KeyError):updater.install_runtime(self.package(names=['fm_rush.py','START_FM_RUSH.bat','update_fm_rush.py','missing.py']),root)
            self.assertEqual((root/'fm_rush.py').read_bytes(),b'old app')

    def test_running_app_blocks_download_and_install(self):
        with patch.object(updater,'app_running',return_value=True),patch.object(updater,'urlopen') as download:
            self.assertEqual(updater.main(),1)
            download.assert_not_called()
