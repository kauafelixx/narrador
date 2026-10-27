"""Controle de instância única no Windows, sem ler bytes bloqueados."""

import errno
import msvcrt
from contextlib import contextmanager
from pathlib import Path

from narrador.paths import ROOT


class AppAlreadyRunningError(RuntimeError):
    """Outra instância mantém o bloqueio deste projeto."""


@contextmanager
def instanceLock(lockPath: Path = ROOT / ".app.lock"):
    """Bloqueia o byte zero, inclusive quando o arquivo ainda está vazio."""
    with lockPath.open("a+b", buffering=0) as lockFile:
        lockFile.seek(0)
        try:
            msvcrt.locking(lockFile.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise AppAlreadyRunningError from error
            raise
        try:
            yield
        finally:
            lockFile.seek(0)
            msvcrt.locking(lockFile.fileno(), msvcrt.LK_UNLCK, 1)
