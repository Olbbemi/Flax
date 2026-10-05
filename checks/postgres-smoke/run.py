#!/usr/bin/env python3
"""Run offline Rust consumption against disposable PostgreSQL 16 clusters."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


class Execution:
    def __init__(self, logs, password):
        self.logs = logs
        self.password = password

    def safe(self, value):
        value = value.replace(self.password, '[REDACTED]')
        return re.sub(
            r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----',
            '[PRIVATE KEY REDACTED]', value, flags=re.DOTALL)

    def run(self, command, *, input=None, env=None, timeout=60, check=True):
        command = [str(part) for part in command]
        try:
            result = subprocess.run(
                command, input=input, env=env, cwd=ROOT,
                capture_output=True, text=True, errors='replace', timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f'{Path(command[0]).name} exceeded {timeout}s') from error
        with (self.logs / 'commands.log').open('a') as log:
            log.write(self.safe('$ ' + shlex.join(command) + '\n'))
            log.write(self.safe(result.stdout + result.stderr))
            log.write(f'Exit: {result.returncode}\n\n')
        if check and result.returncode:
            raise RuntimeError(f'{Path(command[0]).name} failed; see {self.logs / "commands.log"}')
        return result


def certificates(execution, folder):
    folder.mkdir(mode=0o700)
    def openssl(*arguments):
        execution.run(['openssl', *arguments])

    openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', folder / 'ca.key', '-out', folder / 'ca.pem',
            '-days', '7', '-sha256', '-subj', '/CN=Flax isolated test CA',
            '-addext', 'basicConstraints=critical,CA:TRUE',
            '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
    openssl('req', '-new', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', folder / 'server.key', '-out', folder / 'server.csr',
            '-subj', '/CN=localhost')
    extensions = folder / 'extensions.cnf'
    extensions.write_text(
        'basicConstraints=critical,CA:FALSE\n'
        'keyUsage=critical,digitalSignature,keyEncipherment\n'
        'extendedKeyUsage=serverAuth\n'
        'subjectAltName=DNS:localhost,IP:127.0.0.1\n')
    openssl('x509', '-req', '-in', folder / 'server.csr',
            '-CA', folder / 'ca.pem', '-CAkey', folder / 'ca.key',
            '-CAcreateserial', '-out', folder / 'server.pem',
            '-days', '1', '-sha256', '-extfile', extensions)
    (folder / 'index.txt').write_text('')
    (folder / 'serial').write_text('1000\n')
    (folder / 'newcerts').mkdir()
    signing = folder / 'signing.cnf'
    signing.write_text(
        '[ca]\ndefault_ca=issuer\n[issuer]\n'
        f'database={folder / "index.txt"}\nserial={folder / "serial"}\n'
        f'new_certs_dir={folder / "newcerts"}\n'
        f'certificate={folder / "ca.pem"}\nprivate_key={folder / "ca.key"}\n'
        'default_md=sha256\npolicy=policy\nx509_extensions=server\n'
        '[policy]\ncommonName=supplied\n[server]\n'
        'basicConstraints=critical,CA:FALSE\n'
        'keyUsage=critical,digitalSignature,keyEncipherment\n'
        'extendedKeyUsage=serverAuth\n'
        'subjectAltName=DNS:localhost,IP:127.0.0.1\n')
    openssl('ca', '-batch', '-notext', '-config', signing,
            '-in', folder / 'server.csr', '-out', folder / 'expired.pem',
            '-startdate', '20200101000000Z', '-enddate', '20200102000000Z')
    openssl('req', '-x509', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', folder / 'wrong-ca.key', '-out', folder / 'wrong-ca.pem',
            '-days', '7', '-sha256', '-subj', '/CN=Flax unrelated test CA')
    openssl('verify', '-CAfile', folder / 'ca.pem', folder / 'server.pem')
    result = execution.run(
        ['openssl', 'verify', '-CAfile', folder / 'ca.pem', folder / 'expired.pem'],
        check=False)
    if result.returncode == 0 or 'error 10 at 0 depth' not in result.stderr:
        raise RuntimeError('Expired certificate fixture did not fail expiry validation')


def configuration_value(value):
    return "'" + str(value).replace('\\', '\\\\').replace("'", "''") + "'"


class Cluster:
    def __init__(self, execution, binary, work, name):
        self.execution = execution
        self.binary = binary
        self.name = name
        self.folder = work / name
        self.folder.mkdir(mode=0o700)
        self.data = self.folder / 'data'
        self.log = self.folder / 'server.log'
        with socket.socket() as available:
            available.bind(('127.0.0.1', 0))
            self.port = available.getsockname()[1]

    def start(self, certificates_folder, encrypted, expired=False):
        self.execution.run([
            self.binary / 'initdb', '-D', self.data, '--username=flax_admin',
            '--auth-local=trust', '--auth-host=scram-sha-256',
            '--encoding=UTF8', '--locale=C'])
        # Use the short per-cluster directory for the Unix socket path.
        settings = {
            'listen_addresses': configuration_value('127.0.0.1'),
            'port': str(self.port),
            'unix_socket_directories': configuration_value(self.folder),
            'password_encryption': configuration_value('scram-sha-256'),
            'max_connections': '20', 'shared_buffers': configuration_value('16MB'),
            'log_statement': configuration_value('none'),
            'log_parameter_max_length': '0', 'log_parameter_max_length_on_error': '0',
            'log_min_error_statement': configuration_value('panic'),
            'ssl': 'on' if encrypted else 'off',
        }
        if encrypted:
            settings.update({
                'ssl_cert_file': configuration_value(certificates_folder / ('expired.pem' if expired else 'server.pem')),
                'ssl_key_file': configuration_value(certificates_folder / 'server.key'),
                'ssl_min_protocol_version': configuration_value('TLSv1.2'),
                'ssl_max_protocol_version': configuration_value('TLSv1.3'),
            })
        with (self.data / 'postgresql.conf').open('a') as config:
            config.write('\n# Flax disposable check configuration\n')
            config.writelines(f'{name} = {value}\n' for name, value in settings.items())
        self.execution.run([
            self.binary / 'pg_ctl', '-D', self.data, '-l', self.log, '-w', '-t', '15', 'start'])

    def accounts(self, password):
        sql = (
            f"CREATE ROLE flax_consumer LOGIN PASSWORD '{password}' "
            'NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION;\n'
            'CREATE DATABASE flax_check OWNER flax_admin;\n'
            '\\connect flax_check\n'
            'CREATE SCHEMA flax_check AUTHORIZATION flax_consumer;\n'
            'ALTER ROLE flax_consumer IN DATABASE flax_check SET search_path=flax_check;\n'
            "SELECT rolpassword LIKE 'SCRAM-SHA-256$%', "
            'NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication '
            "FROM pg_authid WHERE rolname='flax_consumer';\n"
            "SELECT bool_and(auth_method='scram-sha-256') FROM pg_hba_file_rules "
            "WHERE type IN ('host','hostssl','hostnossl');\n")
        result = self.execution.run([
            self.binary / 'psql', '-X', '-h', self.folder, '-p', self.port,
            '-U', 'flax_admin', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1',
            '--quiet', '--tuples-only', '--no-align'], input=sql)
        if result.stdout.strip().splitlines()[-2:] != ['t|t', 't']:
            raise RuntimeError(f'{self.name}: SCRAM or limited-account setup failed')
        print(f'OK {self.name}: SCRAM TCP rules and restricted SCRAM account')

    def stop(self):
        if not self.data.is_dir():
            return
        result = self.execution.run(
            [self.binary / 'pg_ctl', '-D', self.data, 'status'], check=False)
        if result.returncode == 0:
            self.execution.run([self.binary / 'pg_ctl', '-D', self.data, '-m', 'fast', '-w', 'stop'])
        elif result.returncode != 3:
            raise RuntimeError(f'Cannot determine whether {self.name} stopped')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/postgres-smoke')
    parser.add_argument('--pg-bin', type=Path, default=Path('/usr/lib/postgresql/16/bin'))
    args = parser.parse_args()
    build = args.build_dir.resolve()
    binary = args.pg_bin.resolve()
    build.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(3)
    logs = build / 'logs' / stamp
    logs.mkdir(parents=True)
    password = secrets.token_urlsafe(32)
    execution = Execution(logs, password)
    os.umask(0o077)
    # Unix sockets have a short path limit; /tmp also keeps credentials outside sources.
    work = Path(tempfile.mkdtemp(prefix='flax-pg-'))
    clusters = []
    status = 1
    cleanup_ok = True
    try:
        if os.geteuid() == 0:
            raise RuntimeError('Run this check as a regular user, not root')
        versions = {}
        for name, command in {
            'postgres': [binary / 'postgres', '--version'],
            'psql': [binary / 'psql', '--version'],
            'rustc': ['rustc', '--version'], 'cargo': ['cargo', '--version'],
            'cc': ['cc', '--version'], 'openssl': ['openssl', 'version'],
        }.items():
            versions[name] = execution.run(command).stdout.strip().splitlines()[0]
        if not versions['postgres'].startswith('postgres (PostgreSQL) 16.'):
            raise RuntimeError('PostgreSQL 16 is required')
        if not versions['rustc'].startswith('rustc 1.89.0 ') or not versions['cargo'].startswith('cargo 1.89.0 '):
            raise RuntimeError('Rust/Cargo 1.89.0 is required')
        versions.update({'machine': platform.machine(), 'os_release': Path('/etc/os-release').read_text()})
        (logs / 'environment.json').write_text(json.dumps(versions, indent=2) + '\n')
        certificates_folder = work / 'certificates'
        certificates(execution, certificates_folder)
        for name, encrypted, expired in [('normal', True, False), ('expired', True, True), ('plain', False, False)]:
            cluster = Cluster(execution, binary, work, name)
            clusters.append(cluster)
            cluster.start(certificates_folder, encrypted, expired)
            cluster.accounts(password)
        env = os.environ.copy()
        env.update({
            'FLAX_PG_HOST': 'localhost', 'FLAX_PG_HOSTADDR': '127.0.0.1',
            'FLAX_PG_PORT': str(clusters[0].port),
            'FLAX_PG_EXPIRED_PORT': str(clusters[1].port),
            'FLAX_PG_PLAIN_PORT': str(clusters[2].port),
            'FLAX_PG_USER': 'flax_consumer', 'FLAX_PG_DATABASE': 'flax_check',
            'FLAX_PG_PASSWORD': password,
            'FLAX_PG_CA': str(certificates_folder / 'ca.pem'),
            'FLAX_PG_WRONG_CA': str(certificates_folder / 'wrong-ca.pem'),
            'PROTOC': str(work / 'protoc-must-not-be-used'),
            'PROTOC_INCLUDE': str(work / 'protoc-include-must-not-be-used'),
        })
        cargo = [sys.executable, '-B', ROOT / 'scripts/flax.py',
                 '--build-dir', build / 'cargo', 'cargo-db']
        manifest = ROOT / 'checks/postgres-smoke/Cargo.toml'
        result = execution.run(cargo + [
            'test', '--manifest-path', manifest, '--locked', '--offline',
            '--', '--test-threads=1'], env=env, timeout=300)
        (logs / 'tests.log').write_text(execution.safe(result.stdout + result.stderr))
        print(execution.safe(result.stdout).strip())
        result = execution.run(cargo + [
            'metadata', '--manifest-path', manifest, '--locked', '--offline',
            '--format-version', '1', '--filter-platform', 'x86_64-unknown-linux-gnu'],
            env=env)
        metadata = json.loads(result.stdout)
        nodes = {node['id']: node for node in metadata['resolve']['nodes']}
        features = [
            {'name': package['name'], 'version': package['version'],
             'features': nodes[package['id']]['features']}
            for package in metadata['packages'] if package['id'] in nodes
        ]
        forbidden = {'aws-lc-rs', 'aws-lc-sys', 'rustls-native-certs', 'webpki-roots'}
        if any(package['name'] in forbidden for package in features):
            raise RuntimeError('A forbidden TLS package is active')
        (logs / 'features.json').write_text(json.dumps(features, indent=2) + '\n')
        status = 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f'FAIL {execution.safe(str(error))}', file=sys.stderr)
    except KeyboardInterrupt:
        status = 130
        print('FAIL interrupted', file=sys.stderr)
    finally:
        for cluster in reversed(clusters):
            try:
                cluster.stop()
            except (OSError, RuntimeError) as error:
                cleanup_ok = False
                print(f'FAIL cleanup: {execution.safe(str(error))}', file=sys.stderr)
            if cluster.log.is_file():
                (logs / f'{cluster.name}-server.log').write_text(execution.safe(cluster.log.read_text()))
        if cleanup_ok:
            shutil.rmtree(work)
            print('OK cleanup: disposable servers stopped; databases, passwords and private keys removed')
        else:
            status = 1
            print(f'FAIL retained unfinished cluster at {work}', file=sys.stderr)
        (logs / 'result.json').write_text(json.dumps({
            'exit_code': status, 'cleanup_ok': cleanup_ok,
            'work_removed': not work.exists(),
        }, indent=2) + '\n')
        print(f'Logs: {logs}')
    return status


if __name__ == '__main__':
    sys.exit(main())
