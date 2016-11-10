import os
import struct
from PIL import Image
from images2gif import writeGif

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

from _util import *

try:
    from cspritelib import *
    _C_LIB_LOADED = True
except ImportError:
    _C_LIB_LOADED = False

MODE_SPRITE = 0
MODE_DIR = 1

class Sprite(object):
    def __init__(self, mode, width, height, frame_count):
        self._mode = mode

        self.width = width
        self.height = height
        self.frame_count = frame_count

        self.uk_1 = None
        self.uk_2 = None
        self.size_dummy = None

        self.frames = None

    def __del__(self):
        if self.mode == MODE_SPRITE and not self.fp.closed:
            self.fp.close()

    @property
    def mode(self):
        return self._mode

    def load_frame(self, index):
        if not self.mode == MODE_SPRITE:
            raise SpriteError('Cannot call `load_frame` method on '\
                              '`Sprite` without mode `MODE_SPRITE`')

        if index < 0 or index >= self.frame_count:
            raise IndexError('Invalid index - {}'.format(index))

        if not self.frames[index]:
            if _C_LIB_LOADED:
                self.frames[index] = c_parse_frame(
                    self.fp, self.width, self.height, self.offsets[index])
            else:
                self.frames[index] = _parse_frame(
                    self.fp, self.width, self.height, self.offsets[index])

        return self.frames[index]

    def load_all_frames(self):
        if not self.mode == MODE_SPRITE:
            raise SpriteError('Cannot call `load_all_frames` method on '\
                              '`Sprite` without mode `MODE_SPRITE`')

        for index in range(self.frame_count):
            self.load_frame(index)

    def is_loaded(self):
        return all(self.frames)

    def save_dir(self, path):
        if not self.is_loaded():
            raise SpriteError('Not enough frame data')

        path = _convert_path(path)
        if path and not os.path.isdir(path):
            os.makedirs(path)

        spr_name = os.path.split(path)[-1]

        info_file_path = os.path.join(path, spr_name + '.info')
        self._write_info_file(info_file_path)

        for index, frame in enumerate(self.frames):
            image = Image.frombytes('P', (self.width, self.height), frame)
            image.putpalette(palette)
            image.save(os.path.join(path, spr_name + str(index) + '.bmp'))
            image.close()

    def save_file(self, path):
        if not self.is_loaded():
            raise SpriteError('Not enough frame data')

        dir = os.path.split(_convert_path(path))[0]
        if dir and not os.path.isdir(dir):
            os.makedirs(dir)

        if _C_LIB_LOADED:
            if os.name == 'nt':
                encoding = 'euc-kr'
            else:
                encoding = 'utf-8'
            path = path.encode(encoding)

            c_save_file(
                path, self.width, self.height, self.frame_count,
                self.uk_1, self.uk_2, map(bytearray, self.frames),
                self.size_dummy)

        else:
            with builtins.open(path, 'wb') as fp:
                total_size = 0

                fp.seek(0)
                _write_ints(fp, 9, self.width, self.height, self.frame_count)
                fp.seek(0xbcc)
                _write_ints(fp, self.uk_1, self.uk_2)

                for index, frame in enumerate(self.frames):
                    fp.seek(0x4c0 + index * 4)
                    _write_int(fp, total_size)

                    fp.seek(0xbf4 + total_size)
                    size = 0
                    for i in range(self.height):
                        j = 0
                        while j < self.width:
                            if frame[i * self.width + j] == '\xfe':
                                k = 0
                                while k < 255 and j + k < self.width and \
                                    frame[i * self.width + j + k] == '\xfe':
                                    k += 1
                                fp.write(frame[i * self.width + j])
                                fp.write(chr(k))

                                size += 2
                                j += k - 1
                            else:
                                fp.write(frame[i * self.width + j])
                                size += 1
                            j += 1

                    if not self.size_dummy:
                        fp.seek(0x970 + index * 2)
                        _write_short(fp, size - ((size >> 8) << 8))

                    total_size += size

                if self.size_dummy:
                    fp.seek(0x970)
                    fp.write(self.size_dummy)

                fp.seek(0xbc8)
                _write_int(fp, total_size)

    def save_gif_file(self, path, interval=0.1):
        if not self.is_loaded():
            raise SpriteError('Not enough frame data')

        path = _convert_path(path)

        dir = os.path.split(path)[0]
        if dir and not os.path.isdir(dir):
            os.makedirs(dir)

        images = []
        for frame in self.frames:
            image = Image.frombytes('P', (self.width, self.height), frame)
            image.putpalette(palette)
            images.append(image)

        writeGif(path, images, duration=interval, subRectangles=False)

        for image in images:
            image.close()

    def _write_info_file(self, path):
        with builtins.open(_convert_path(path), 'wb') as fp:
            _write_ints(
                fp, self.width, self.height, self.frame_count,
                self.uk_1, self.uk_2, len(self.size_dummy))
            fp.write(self.size_dummy)

def open_sprite(path, lazy_load=False):
    path = _convert_path(path)

    if os.path.isdir(path):
        spr_name = os.path.split(path)[-1]

        info_file_path = os.path.join(path, spr_name + '.info')
        if not os.path.isfile(info_file_path):
            raise SpriteError('Cannot open info file')

        try:
            info = _read_info_file(info_file_path)
        except struct.error:
            raise SpriteError('Invalid info file')
        width, height, frame_count, uk_1, uk_2, size_dummy = info

        file_list = _get_file_list(path, spr_name)
        if len(file_list) != frame_count:
            raise SpriteError('Not enough bitmap files')

        frames = []
        for file in file_list:
            if isinstance(file, unicode):
                file = file.encode('euc-kr')
            image = Image.open(file)
            frames.append(image.tobytes())
            image.close()

        sprite = Sprite(MODE_DIR, width, height, frame_count)
        sprite.uk_1 = uk_1
        sprite.uk_2 = uk_2
        sprite.size_dummy = size_dummy
        sprite.frames = frames

        return sprite
    elif os.path.isfile(path):
        fp = builtins.open(path, 'rb')

        try:
            if _C_LIB_LOADED:
                header = c_parse_header(fp)
            else:
                header = _parse_header(fp)
        except struct.error:
            raise SpriteError('Invalid sprite file')
        width, height, frame_count, uk_1, uk_2, size_dummy, offsets = header

        frames = [''] * frame_count
        if not lazy_load:
            for index in range(frame_count):
                if _C_LIB_LOADED:
                    frames[index] = c_parse_frame(
                        fp, width, height, offsets[index])
                else:
                    frames[index] = _parse_frame(
                        fp, width, height, offsets[index])

        sprite = Sprite(MODE_SPRITE, width, height, frame_count)
        sprite.uk_1 = uk_1
        sprite.uk_2 = uk_2
        sprite.size_dummy = size_dummy
        sprite.frames = frames

        sprite.fp = fp
        sprite.offsets = offsets

        return sprite
    else:
        raise IOError('Invalid path - {}'.format(repr(path)))

def _read_info_file(path):
    with builtins.open(path, 'rb') as fp:
        width, height, frame_count, uk_1, uk_2 = _read_ints(fp, 5)
        size_dummy_len = _read_int(fp)
        size_dummy = fp.read(size_dummy_len)

    return width, height, frame_count, uk_1, uk_2, size_dummy

def _parse_header(fp):
    fp.seek(0)

    signature = _read_int(fp)
    if signature != 9:
        raise SpriteError('Invalid sprite file')

    width, height, frame_count = _read_ints(fp, 3)

    offsets = []
    for index in range(frame_count):
        fp.seek(0x4c0 + index * 4)
        offsets.append(_read_int(fp))

    fp.seek(0xbc8)
    offsets.append(_read_int(fp))

    store_size_dummy = False
    size_dummy = []
    for index in range(frame_count):
        size = offsets[index + 1] - offsets[index]
        small_size = size - ((size >> 8) << 8)

        fp.seek(0x970 + index * 2)
        size_dummy.append(_read_short(fp))

        if small_size != size_dummy[-1] and not store_size_dummy:
            store_size_dummy = True

        size_dummy[-1] = struct.pack('<H', size_dummy[-1])

    del offsets[-1]

    fp.seek(0xbcc)
    uk_1, uk_2 = _read_ints(fp, 2)

    if store_size_dummy:
        size_dummy = ''.join(size_dummy)
    else:
        size_dummy = ''

    return width, height, frame_count, uk_1, uk_2, size_dummy, offsets

def _parse_frame(fp, width, height, offset):
    fp.seek(0xbf4 + offset)

    frame = ''
    for i in range(height):
        j = 0
        while j < width:
            byte = fp.read(1)
            if byte == '\xfe':
                repeat = ord(fp.read(1))
                while repeat > 0:
                    frame += '\xfe'
                    j += 1
                    repeat -= 1
            else:
                frame += byte
                j += 1

    return frame

class SpriteError(Exception):
    '''Sprite Error abstract class'''