import os
import tempfile as tmp
from contextlib import contextmanager

import requests
from tqdm import tqdm

if not hasattr(os, 'replace'):
    os.replace = os.rename


def get_valid_filename(s: str):
    return ''.join(x if (x.isalnum() or x in '._- ()') else '_' for x in s)


# temp file funcs taken from https://stackoverflow.com/a/29491523/12946163
@contextmanager
def tempfile(suffix='', dir=None) -> str:
    """ Context for temporary file.

    Will find a free temporary filename upon entering
    and will try to delete the file on leaving, even in case of an exception.

    Parameters
    ----------
    suffix : string
        optional file suffix
    dir : string
        optional directory to save temporary file in
    """

    tf = tmp.NamedTemporaryFile(delete=False, suffix=suffix, dir=dir)
    tf.close()
    try:
        yield tf.name
    finally:
        try:
            os.remove(tf.name)
        except OSError as e:
            if e.errno == 2:
                pass
            else:
                raise


@contextmanager
def open_atomic(filepath, *args, **kwargs):
    """ Open temporary file object that atomically moves to destination upon
    exiting.

    Allows reading and writing to and from the same filename.

    The file will not be moved to destination in case of an exception.

    Parameters
    ----------
    filepath : string
        the file path to be opened
    fsync : bool
        whether to force write the file to disk
    *args : mixed
        Any valid arguments for :code:`open`
    **kwargs : mixed
        Any valid keyword arguments for :code:`open`
    """
    fsync = kwargs.get('fsync', True)

    with tempfile(dir=os.path.dirname(os.path.abspath(filepath))) as tmppath:
        with open(tmppath, *args, **kwargs) as file:
            try:
                yield file
            finally:
                if fsync:
                    file.flush()
                    os.fsync(file.fileno())
        os.rename(tmppath, filepath)


def safe_download_url(url: str, path: str):
    r = requests.get(url, stream=True)
    r.raw.decode_content = True
    with open_atomic(path, 'wb') as f, tqdm(desc=path,
                                            total=int(r.headers.get('content-length', 0)),
                                            unit='B',
                                            unit_scale=True,
                                            unit_divisor=1024) as bar:
        for data in r.iter_content(chunk_size=1024):
            bar.update(f.write(data))
