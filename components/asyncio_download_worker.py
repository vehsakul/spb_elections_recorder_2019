import asyncio
import itertools
import logging
import os
import traceback
from datetime import datetime
from pathlib import Path
from threading import Thread

import aiofiles as aiofiles
import aiohttp
from aiohttp.client_exceptions import ClientResponseError
import m3u8
import ssl
import urllib.parse

# ssl._create_default_https_context = ssl._create_unverified_context

class DownloadHandler:
    log = logging.getLogger('DownloadHandler')
    loop = asyncio.new_event_loop()
    requests_queue = asyncio.Queue()

    @classmethod
    async def async_get_text(cls, url, session=None):
        ses = session if session is not None else aiohttp.ClientSession()
        max_retries = 5
        async with ses:
            for i in range(max_retries):
                try:
                    async with ses.get(url) as response:
                        response.raise_for_status()
                        return await response.text()
                except (aiohttp.ClientConnectorError, ClientResponseError) as e:
                    if isinstance(e, ClientResponseError):
                        if e.status != 504:
                            raise
                    error_msg = f'GET {url} failed: {str(e)}'
                    cls.log.error(error_msg)
                    if i < max_retries:
                        await asyncio.sleep(1 + i * 2)
                        cls.log.info(f'retrying GET {url} after {1 + i * 2} seconds')
                    else:
                        raise

    @classmethod
    async def async_download(cls, url, filename, session=None):
        ses = session if session is not None else aiohttp.ClientSession()
        async with ses:
            async with ses.request(method="GET", url=url) as response:
                response.raise_for_status()
                async with aiofiles.open(filename, "ba") as f:
                    async for data in response.content.iter_chunked(256 * 1024):
                        # cls.log.debug("writing data to %s", filename)
                        await f.write(data)

    @classmethod
    def side_thread(cls, loop):
        cls.log.info('started loop thread')
        asyncio.set_event_loop(loop)
        loop.run_forever()
        cls.log.info('loop thread is exiting')

    @classmethod
    def init(cls):
        cls.thread = Thread(target=cls.side_thread, args=(cls.loop,), daemon=False)
        cls.thread.start()

    @classmethod
    def deinit(cls):
        pass
        cls.loop.call_soon_threadsafe(cls.loop.stop)
        cls.thread.join()


class DownloadFileWorker(DownloadHandler):
    def create_signals(self):
        pass

    def __init__(self, url, path, length, index):
        super(DownloadFileWorker, self).__init__()

        self.create_signals()

        self.url = url
        self.path = path
        self.length = length
        self.index = index

    async def run(self):
        max_retries = 5
        for i in range(max_retries):
            try:
                await self.async_download(self.url, self.path)
            except aiohttp.ClientConnectorError as e:
                error_msg = f'downloading of {self.url} to {self.path} failed: {str(e)}'
                self.log.error(error_msg)
                if i < max_retries:
                    self.log.info(f'will retry {self.url}')
                    await asyncio.sleep(2**i)
                else:
                    raise
            else:
                break


    def start(self):
        with open(Path(self.path).with_suffix('.lock'), 'wb'):
            pass

        task = self.loop.create_task(self.run())
        def on_done(f: asyncio.Future):
            try:
                if not f.cancelled():
                    f.result()
            except Exception as e:
                error_msg = f'downloading of {self.url} to {self.path} failed: {str(e)}\n'
                error_msg += traceback.format_exc()
                self.log.error(error_msg)
            else:
                self.log.info('finished downloading %s to %s', self.url, self.path)
            finally:
                os.unlink(Path(self.path).with_suffix('.lock'))


        task.add_done_callback(on_done)


class DownloadVideoWorker(DownloadHandler):
    def create_signals(self):
        pass

    def __init__(self, out_dir, index, stream_url, stream_name):
        super(DownloadVideoWorker, self).__init__()

        self.create_signals()

        self.stream_name = stream_name
        self.out_dir = out_dir
        self.index = index
        self.directory = self.last_file = ''
        self.hls_url = stream_url
        self.part_num = self.media_sequence = 0
        self.meta = self.hls = None

    def _get_available_dir(self):
        return self.out_dir

    def _dl_chunk(self, url, path, length, index):
        url = url.replace('mono.m3u8', '')

        dl_worker = DownloadFileWorker(url, path, length, index)
        dl_worker.start()

    async def load_hls(self):
        # print (self.hls_url)
        # ff = open('d:\\tmp\\#cam\\test.txt', 'wb')
        try:
        #     with tempfile.TemporaryDirectory() as dir:
        #         file_path = os.path.join(dir, 'playlist.m3u8')
        #         with open(file_path, 'wb') as f:
        #             # f.write(requests.get(self.hls_url, verify=False).content)
        #             a = requests.get(self.hls_url, verify=False).content
        #             # f.write(a.replace('2020','https://flu01.pride-net.ru/cam_60let59/tracks-v1/2020'))
        #             # print (a)
        #             f.write(a)
        #             # f.write(requests.get(self.hls_url, verify=False).content)
        #             # ff.write(requests.get(self.hls_url, verify=False).content)
        #             # ff.write(a)
        #         # return m3u8.load(file_path)
        #
        #         m3u8_obj = m3u8.load('https://flu01.pride-net.ru/cam_60let59/tracks-v1/mono.m3u8')
        #
        #         print (m3u8_obj.segments)
        #         print (m3u8_obj.target_duration)
        #
        #         # return m3u8.load('https://flu01.pride-net.ru/cam_60let59/tracks-v1/mono.m3u8')
        #         print (requests.get(self.hls_url, verify=False).text)

                self.last_hls_time = datetime.now()
                hls_playlist = await self.async_get_text(self.hls_url)
                # self.log.debug(hls_playlist)

                return m3u8.loads(hls_playlist)

        except Exception as e:
            # self.log.error(str(e))
            raise

    async def run(self):
        self.directory = self._get_available_dir()

        os.makedirs(self.directory, exist_ok=True)

        hls = await self.load_hls()
        prev_hls = None
        self.media_sequence = hls.media_sequence
        while True:
            try:
                idx = hls.files.index(self.last_file) + 1
            except ValueError:
                if self.media_sequence != hls.media_sequence:
                    self.log.error(f'{self.hls_url}: the last downloaded file is not present in the playlist, downloading the whole playlist')
                    idx = 0
                else:
                    idx = -1

            self.media_sequence = hls.media_sequence
            self.last_file = hls.files[-1]
            for i, file in enumerate(hls.files[idx:]):
                file_name = Path(os.path.join(self.directory)) / f'{self.stream_name}_{hls.media_sequence:08d}.{self.part_num:06d}.ts'
                self._dl_chunk(urllib.parse.urljoin(self.hls_url, file), file_name, hls.segments[idx+i].duration, self.part_num)
                self.part_num += 1

            await asyncio.sleep(max(0., hls.target_duration - (datetime.now() - self.last_hls_time).total_seconds()))
            prev_hls = hls
            while True:
                hls = await self.load_hls()
                if hls and hls.files[-1] != prev_hls.files[-1]:
                    break
                else:
                    await asyncio.sleep(max(0., hls.target_duration / 2 - (datetime.now() - self.last_hls_time).total_seconds()))

    def start(self):
        def on_done(f: asyncio.Future):
            try:
                if not f.cancelled():
                    f.result()
            except Exception as e:
                error_msg = f'processing of stream {self.hls_url} failed: {str(e)}\n'
                error_msg += traceback.format_exc()
                self.log.error(error_msg)
            else:
                self.log.info(f'finished processing of stream {self.hls_url}')

        f = asyncio.run_coroutine_threadsafe(self.run(), self.loop)
        f.add_done_callback(on_done)
