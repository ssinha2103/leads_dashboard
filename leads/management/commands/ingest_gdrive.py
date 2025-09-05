from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
import zipfile
import tarfile

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = "Download a dataset from a Google Drive link, extract if needed, ingest via ingest_local, then optionally cleanup."

    def add_arguments(self, parser):
        parser.add_argument('--url', required=True, help='Google Drive share link or file/folder id URL')
        parser.add_argument('--glob', type=str, default='all', help='Glob passed to ingest_local (default: all)')
        parser.add_argument('--cleanup', dest='cleanup', action='store_true', default=True, help='Delete downloaded/extracted data after ingest (default)')
        parser.add_argument('--no-cleanup', dest='cleanup', action='store_false', help='Keep downloaded/extracted data')
        parser.add_argument('--out-dir', type=str, default='data', help='Base directory to store temporary download (default: data)')

    def handle(self, *args, **opts):
        try:
            import gdown  # type: ignore
        except Exception as e:
            raise CommandError("gdown is required. Add to requirements and reinstall.") from e

        url: str = opts['url']
        base_dir = Path(opts['out-dir']).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)

        tmp_dir = Path(tempfile.mkdtemp(prefix='gdrive_', dir=str(base_dir)))
        self.stdout.write(f"Downloading to {tmp_dir}...")

        downloaded_paths: list[Path] = []

        # Try file download first; if that fails, try folder
        file_path = None
        try:
            file_path = gdown.download(url, output=str(tmp_dir), quiet=False, fuzzy=True)
        except Exception:
            file_path = None

        if file_path:
            downloaded_paths = [Path(file_path)]
        else:
            try:
                items = gdown.download_folder(url, output=str(tmp_dir), quiet=False, use_cookies=False)
            except TypeError:
                # Older gdown versions may not support use_cookies kw
                items = gdown.download_folder(url, output=str(tmp_dir), quiet=False)
            if not items:
                raise CommandError('No files downloaded from Google Drive link.')
            downloaded_paths = [Path(p) for p in items]

        # Determine root for ingest
        root_path = tmp_dir

        # If single archive file, extract it
        if len(downloaded_paths) == 1 and downloaded_paths[0].is_file():
            p = downloaded_paths[0]
            extracted_dir = tmp_dir / 'extracted'
            extracted_dir.mkdir(parents=True, exist_ok=True)
            if p.suffix.lower() == '.zip':
                with zipfile.ZipFile(p, 'r') as zf:
                    zf.extractall(extracted_dir)
                root_path = extracted_dir
            elif p.suffix.lower() in {'.tar', '.gz', '.tgz', '.bz2', '.xz'} or ''.join(p.suffixes[-2:]).lower() in {'.tar.gz', '.tar.bz2', '.tar.xz'}:
                # Best-effort handle common tarballs
                with tarfile.open(p, 'r:*') as tf:
                    tf.extractall(extracted_dir)
                root_path = extracted_dir
            else:
                # Treat as a single CSV/XLSX; keep root as tmp_dir
                root_path = tmp_dir

        # If the extracted dir contains a single top-level dir, use that as root
        try:
            entries = [e for e in root_path.iterdir() if not e.name.startswith('.')]
            if len(entries) == 1 and entries[0].is_dir():
                root_path = entries[0]
        except Exception:
            pass

        self.stdout.write(f"Ingest root: {root_path}")

        # Call ingest_local with discovered root
        call_command('ingest_local', root=str(root_path), glob=opts['glob'])

        if opts['cleanup']:
            self.stdout.write("Cleaning up downloaded data...")
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                self.stderr.write(f"Cleanup failed: {e}")

