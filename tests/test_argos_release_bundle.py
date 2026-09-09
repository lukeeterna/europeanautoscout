"""Source candidate reproducibility, contamination exclusion and integrity."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bundle', ROOT/'tools/scripts/argos_release_bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class SourceBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root/'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.names = ['wa-intelligence/package.json', 'wa-intelligence/package-lock.json', 'wa-intelligence/main.py']
        self.write('wa-intelligence/package.json', json.dumps({'version':'1.0.0','engines':{'node':'>=22'},'dependencies':{}}))
        self.write('wa-intelligence/package-lock.json', json.dumps({'lockfileVersion':3,'packages':{'':{'dependencies':{}}}}))
        self.write('wa-intelligence/main.py', "print('fixture')\n")
        self.write(bundle.LIST, '\n'.join(self.names)+'\n')
        self.commit()

    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL).decode().strip()

    def write(self, name, data):
        p = self.repo/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(data)

    def commit(self):
        self.git('add','.')
        self.git('-c','user.name=Offline Test','-c','user.email=test@example.invalid','commit','-qm','fixture')
        self.sha = self.git('rev-parse','HEAD')

    def test_exact_git_objects_are_reproducible_despite_dirty_files(self):
        first = bundle.build(self.repo,self.sha,self.root/'one')
        self.write('wa-intelligence/main.py','dirty')
        self.write('wa-intelligence/.env','MUST_NOT_EXPORT=fixture')
        self.write('wa-intelligence/state.sqlite','MUST_NOT_EXPORT')
        second = bundle.build(self.repo,self.sha,self.root/'two')
        self.assertEqual(first.read_bytes(),second.read_bytes())
        with zipfile.ZipFile(second) as z:
            self.assertEqual(z.read('wa-intelligence/main.py'),b"print('fixture')\n")
            self.assertEqual(set(z.namelist()),set(self.names)|{bundle.MANIFEST})
        self.assertEqual(bundle.verify(second)['source_sha'],self.sha)

    def test_archive_tampering_fails_checksum(self):
        archive = bundle.build(self.repo,self.sha,self.root/'out')
        archive.write_bytes(archive.read_bytes()+b'tamper')
        with self.assertRaises(ValueError): bundle.verify(archive)

    def test_localauth_and_database_paths_cannot_be_allowlisted(self):
        for name in ['wa-intelligence/state.sqlite','wa-intelligence/session-argos-business/profile','wa-intelligence/.env','../outside']:
            self.assertFalse(bundle.safe_path(name), name)

    def test_symlink_in_inventory_fails_closed(self):
        (self.repo/'wa-intelligence/main.py').unlink()
        (self.repo/'wa-intelligence/main.py').symlink_to('package.json')
        self.commit()
        with self.assertRaises(ValueError): bundle.build(self.repo,self.sha,self.root/'out')

    def test_duplicate_inventory_fails_closed(self):
        self.write(bundle.LIST,'\n'.join(self.names+self.names)+'\n')
        self.commit()
        with self.assertRaises(ValueError): bundle.build(self.repo,self.sha,self.root/'out')

    def test_lock_disagreement_fails_closed(self):
        self.write('wa-intelligence/package.json',json.dumps({'version':'1','engines':{'node':'>=22'},'dependencies':{'unlocked':'1.0.0'}}))
        self.commit()
        with self.assertRaises(ValueError): bundle.build(self.repo,self.sha,self.root/'out')
