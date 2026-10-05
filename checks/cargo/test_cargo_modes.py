"""Cargo consumer contracts for native and protoc-free modes."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('flax', ROOT / 'scripts/flax.py')
flax = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flax)


class CargoModes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='flax cargo modes ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'integration').mkdir()
        (self.root / 'third_party').mkdir()
        (self.root / 'integration/rust-packages.json').write_text('{}')
        (self.root / 'third_party/rust-registry.json').write_text(
            json.dumps({'packages': []}))
        self.build = self.root / 'output'
        self.build.mkdir()

    def test_database_config_works_without_native_tools_and_enforces_offline_sources(self):
        with patch.object(flax, 'ROOT', self.root):
            config = flax.cargo_config(self.build, with_protoc=False)
        data = tomllib.loads(config.read_text())
        self.assertEqual(data['source']['crates-io']['replace-with'], 'flax-vendored')
        self.assertEqual(data['source']['flax-vendored']['directory'],
                         str(self.build / 'cargo-registry'))
        self.assertTrue(data['net']['offline'])
        self.assertNotIn('PROTOC', data.get('env', {}))
        self.assertNotIn('PROTOC_INCLUDE', data.get('env', {}))
        self.assertFalse((self.build / 'install').exists())

    def test_existing_mode_still_requires_protoc(self):
        with patch.object(flax, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'Build protoc first'):
                flax.cargo_config(self.build)

    def test_native_and_database_configs_do_not_overwrite_each_other(self):
        protoc = self.build / 'install/bin/protoc'
        protoc.parent.mkdir(parents=True)
        protoc.write_text('test fixture')
        with patch.object(flax, 'ROOT', self.root):
            native = flax.cargo_config(self.build)
            native_text = native.read_text()
            database = flax.cargo_config(self.build, with_protoc=False)
        self.assertNotEqual(native, database)
        self.assertEqual(native.read_text(), native_text)
        data = tomllib.loads(native_text)
        self.assertEqual(data['env']['PROTOC'], {'value': str(protoc), 'force': True})
        self.assertNotIn('env', tomllib.loads(database.read_text()))

    def test_database_cli_forwards_cargo_arguments_from_a_path_with_spaces(self):
        result = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts/flax.py'),
             '--build-dir', str(self.build), 'cargo-db', 'version', '--verbose'],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r'^cargo [0-9]')
        self.assertTrue((self.build / 'cargo-db-config.toml').is_file())
        self.assertFalse((self.build / 'install').exists())


if __name__ == '__main__':
    unittest.main()
