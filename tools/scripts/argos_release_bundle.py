#!/usr/bin/env python3
"""Reproducible allowlisted source candidate from Git objects, never live files."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

LIST = 'tools/scripts/argos-release-files.txt'
MANIFEST = 'RELEASE_MANIFEST.json'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p) != name or '\\' in name:
        return False
    if any(part.startswith('.') for part in p.parts) and name != 'wa-intelligence/.env.example':
        return False
    return not any(x in name.lower() for x in ('.sqlite', '.db', 'session-', 'node_modules', '.pem', '.key', '.bak'))


def build(repo, sha, output):
    if not re.fullmatch('[0-9a-f]{40}', sha):
        raise ValueError('full commit SHA required')
    actual = git(repo, 'rev-parse', sha + '^{commit}').decode().strip()
    if actual != sha:
        raise ValueError('commit identity mismatch')
    names = [line.strip() for line in git(repo, 'show', f'{sha}:{LIST}').decode().splitlines()
             if line.strip() and not line.lstrip().startswith('#')]
    if len(names) != len(set(names)) or not names:
        raise ValueError('empty or duplicate release inventory')
    names = sorted(names)
    contents = {}
    inventory = []
    for name in names:
        if not safe_path(name) or name == MANIFEST:
            raise ValueError('forbidden release path')
        entry = git(repo, 'ls-tree', sha, '--', name).decode().strip().split()
        if len(entry) < 4 or entry[0] not in ('100644', '100755') or entry[1] != 'blob':
            raise ValueError('missing, nonregular or symlink release entry')
        data = git(repo, 'show', f'{sha}:{name}')
        contents[name] = data
        inventory.append({'path': name, 'mode': entry[0], 'blob': entry[2], 'sha256': digest(data), 'bytes': len(data)})
    package = json.loads(contents['wa-intelligence/package.json'])
    lock = json.loads(contents['wa-intelligence/package-lock.json'])
    if lock['lockfileVersion'] != 3:
        raise ValueError('canonical lockfile v3 required')
    for group in ('dependencies', 'optionalDependencies'):
        if package.get(group, {}) != lock['packages'][''].get(group, {}):
            raise ValueError('package/lock disagreement')
    manifest = {
        'format': 1, 'kind': 'SOURCE_CANDIDATE_NOT_PRODUCTION',
        'repository': 'lukeeterna/europeanautoscout', 'source_sha': sha,
        'source_tree': git(repo, 'rev-parse', sha + '^{tree}').decode().strip(),
        'security_gate': 'OPEN_REQUIRES_WORK_SECURITY_REVIEW',
        'machine_gate': 'NOT_CERTIFIED', 'production_gate': 'NOT_CERTIFIED',
        'runtime_version': package['version'], 'node_engine': package['engines']['node'],
        'dependencies': package.get('dependencies', {}),
        'optional_dependencies': package.get('optionalDependencies', {}),
        'lock_sha256': digest(contents['wa-intelligence/package-lock.json']),
        'files': inventory,
        'manifest_note': 'Inventory covers source files; manifest is not self-hashed. External checksum covers the archive.',
    }
    contents[MANIFEST] = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / f'argos-source-{sha}.zip'
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', compression=zipfile.ZIP_STORED) as z:
        for name in sorted(contents):
            item = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            item.create_system = 3
            modes = {entry['path']: int(entry['mode'], 8) for entry in inventory}
            item.external_attr = modes.get(name, 0o100644) << 16
            z.writestr(item, contents[name])
    raw = data.getvalue()
    if target.exists() and target.read_bytes() != raw:
        raise ValueError('immutable output collision')
    target.write_bytes(raw)
    target.with_suffix('.sha256').write_text(digest(raw) + '  ' + target.name + '\n')
    verify(target)
    return target


def verify(archive):
    archive = Path(archive)
    expected = archive.with_suffix('.sha256').read_text().split()[0]
    if digest(archive.read_bytes()) != expected:
        raise ValueError('archive checksum mismatch')
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate archive entries')
        manifest = json.loads(z.read(MANIFEST))
        if set(names) != {MANIFEST, *(entry['path'] for entry in manifest['files'])}:
            raise ValueError('unexpected archive files')
        for entry in manifest['files']:
            name = entry['path']
            if (not safe_path(name) or digest(z.read(name)) != entry['sha256']
                    or len(z.read(name)) != entry['bytes']
                    or z.getinfo(name).external_attr >> 16 != int(entry['mode'], 8)):
                raise ValueError('source inventory mismatch')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--sha')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        m = verify(args.verify)
        print('SOURCE_BUNDLE_VERIFY=PASS SHA=' + m['source_sha'])
    else:
        if not args.sha or not args.output:
            parser.error('--sha and --output required')
        print(build(args.repo, args.sha, args.output))
