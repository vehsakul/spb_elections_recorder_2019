import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import click

suffix = '-concat'

@click.command()
@click.option('--root', required=True)
@click.option('--period', type=int, required=True)
def run(root, period):
    logging.basicConfig(format='%(asctime)s--%(levelname)s--%(message)s', stream=sys.stdout, level=logging.DEBUG)

    subdirs = [f.name for f in os.scandir(root) if f.is_dir() and not f.name.endswith(suffix)]
    current_time = datetime.now().timestamp()

    for subdir in subdirs:
        logging.info(f'processing {subdir}')
        files = [f for f in os.scandir(Path(root) / subdir) if f.is_file() and (current_time > f.stat().st_ctime > (current_time - (period * 1.02) * 60))]
        files.sort(key=lambda f: int(f.name.split('.')[-2]))

        # logging.debug(str(files))
        if len(files) == 0:
            continue

        result_name = subdir + f'_{files[0].stat().st_ctime:.2f}-{files[-1].stat().st_ctime:.2f}.ts'

        result_path = Path(root) / (subdir + suffix) / result_name
        result_path.parent.mkdir(exist_ok=True)

        with open(result_path, 'wb') as f:
            for chunk in (f.path for f in files):
                try:
                    with open(chunk, 'rb') as chunk_f:
                        f.write(chunk_f.read())
                except:
                    logging.error(traceback.format_exc())

        for chunk in (f.path for f in files):
            try:
                os.unlink(chunk)
            except:
                logging.error(traceback.format_exc())


if __name__ == '__main__':
    run()
