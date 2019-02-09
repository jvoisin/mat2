"""
Wrapper around a subset of the subprocess module,
that uses bwrap (bubblewrap) when it is available.

Instead of importing subprocess, other modules should use this as follows:

  from . import subprocess
"""

import os
import shutil
import subprocess
import tempfile
from typing import List, Optional


__all__ = ['PIPE', 'run', 'CalledProcessError']
PIPE = subprocess.PIPE
CalledProcessError = subprocess.CalledProcessError


def _get_bwrap_path() -> str:
    bwrap_path = '/usr/bin/bwrap'
    if os.path.isfile(bwrap_path):
        if os.access(bwrap_path, os.X_OK):
            return bwrap_path

    raise RuntimeError("Unable to find bwrap")  # pragma: no cover


# pylint: disable=bad-whitespace
def _get_bwrap_args(tempdir: str,
                    input_filename: str,
                    output_filename: Optional[str] = None) -> List[str]:
    ro_bind_args = []
    cwd = os.getcwd()

    # XXX: use --ro-bind-try once all supported platforms
    # have a bubblewrap recent enough to support it.
    ro_bind_dirs = ['/usr', '/lib', '/lib64', '/bin', '/sbin', cwd]
    for bind_dir in ro_bind_dirs:
        if os.path.isdir(bind_dir):  # pragma: no cover
            ro_bind_args.extend(['--ro-bind', bind_dir, bind_dir])

    ro_bind_files = ['/etc/ld.so.cache']
    for bind_file in ro_bind_files:
        if os.path.isfile(bind_file):  # pragma: no cover
            ro_bind_args.extend(['--ro-bind', bind_file, bind_file])

    args = ro_bind_args + \
        ['--dev', '/dev',
         '--chdir', cwd,
         '--unshare-all',
         '--new-session',
         # XXX: enable --die-with-parent once all supported platforms have
         # a bubblewrap recent enough to support it.
         # '--die-with-parent',
        ]

    if output_filename:
        # Mount an empty temporary directory where the sandboxed
        # process will create its output file
        output_dirname = os.path.dirname(os.path.abspath(output_filename))
        args.extend(['--bind', tempdir, output_dirname])

    absolute_input_filename = os.path.abspath(input_filename)
    args.extend(['--ro-bind', absolute_input_filename, absolute_input_filename])

    return args


# pylint: disable=bad-whitespace
def run(args: List[str],
        input_filename: str,
        output_filename: Optional[str] = None,
        **kwargs) -> subprocess.CompletedProcess:
    """Wrapper around `subprocess.run`, that uses bwrap (bubblewrap) if it
    is available.

    Extra supported keyword arguments:

     - `input_filename`, made available read-only in the sandbox
     - `output_filename`, where the file created by the sandboxed process
       is copied upon successful completion; an empty temporary directory
       is made visible as the parent directory of this file in the sandbox.
       Optional: one valid use case is to invoke an external process
       to inspect metadata present in a file.
    """
    try:
        bwrap_path = _get_bwrap_path()
    except RuntimeError:  # pragma: no cover
        # bubblewrap is not installed ⇒ short-circuit
        return subprocess.run(args, **kwargs)

    with tempfile.TemporaryDirectory() as tempdir:
        prefix_args = [bwrap_path] + \
            _get_bwrap_args(input_filename=input_filename,
                            output_filename=output_filename,
                            tempdir=tempdir)
        completed_process = subprocess.run(prefix_args + args, **kwargs)
        if output_filename and completed_process.returncode == 0:
            shutil.copy(os.path.join(tempdir, os.path.basename(output_filename)),
                        output_filename)

        return completed_process
