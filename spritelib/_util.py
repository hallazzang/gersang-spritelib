import os
import sys
import struct
from binascii import hexlify, unhexlify
import re
import glob
import chardet

palette = unhexlify('\
000000345f2c34512c344a3f2c3f372c42342c4237295425254a29293b292534\
3025343721343421421e1e341e1a3429d1af74884d1e775f37a88854997b4abd\
9c5f4a3b134d3f163b290b2c4d2c427437427434426a3b3f663b3b5b34375f30\
d19c6db2771ad1bdb2c39521b87e16c9ac70ccbdb5c39f51b87413c08f1ac099\
46ccb592b2660bac51079930048f2104770b00857e70887763b2a89c8c82709f\
9585b2a89cbbb8af928f82999288bbaf9f8c7b6a8f826d373b663437582c3051\
928c7b3b30302916075f544d00af00af0000afaf0063584d3f37255b584a4d4a\
215846259c886d8274517463426d5f3f8f7e5f544a376d63547b705f4d4a3b77\
6d637e6a66706a5f6a63583b37295b54424a463b6a6351706a5b4d4230423b29\
5f5442421e1a46341354421a66423b51342c82584d74583085461e8f6d30855f\
29995b256a3b1a663b1a70371a5f371677461a6613134d251eceb5995b30256a\
3b2c703f30774234854d518c514292584d99634dcec09fa8745bb5856ab88c70\
668c8c5f827e5470775177704d666d4a6a704266664a6a664a587e3f4a703f63\
5f3f585f374266344a5b30375b252c46b5c0cc34425f303f5b775f51584a3b51\
4234584637af994dac954a6354137b6a13857013545f5f3f4a4a85b5af709c9c\
4a51587b291a8834219c4229ac4d34bb633fc98558822c1e923b25a2462cb55b\
3bc3704ad1a56dd4d4b8d4c99fd4c092d4b588d4af82d4c695c97b51ce8c5fd1\
a574d1af74d19c6d3451375125044a2104421e00371a003416002c13001e0b00\
632c045166854a587b466d664251743b4666374d5b2c3754252c4d1e21461a1e\
421a1e42161a3b1616370f0f345829042525254646466d6d6d8f8f8f25130046\
2c006d4d008f5f002500253f003f5b005b770077002525003f3f005b5b007777\
2525004646006d6d008f8f00002500003f00005b000077002500004a00006d00\
008f000000002500004a00006d00008fc9c9c90f0f0f1e1e1e2c2c2c3f3f3f4d\
4d4d5b5b5b6a6a6a7b7b7b888888959595a2a2a2b2b2b2bdbdbdd4c0d4d4d4d4')

def _read_short(fp):
    return struct.unpack('<H', fp.read(2))[0]

def _read_int(fp):
    return struct.unpack('<I', fp.read(4))[0]

def _read_ints(fp, n):
    return struct.unpack('<{}'.format('I' * n), fp.read(4 * n))

def _write_short(fp, x):
    fp.write(struct.pack('<H', x))

def _write_int(fp, x):
    fp.write(struct.pack('<I', x))

def _write_ints(fp, *x):
    fp.write(struct.pack('<{}'.format('I' * len(x)), *x))

def _convert_path(path, encoding=None):
    if not isinstance(path, unicode):
        path = path.decode(chardet.detect(path)['encoding'])
    path = os.path.relpath(path).replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]
    if encoding:
        path = path.encode(encoding)
    return path

def _get_file_list(dir, spr_name):
    def __cmp_func(a, b):
        return int(ptn.search(a).group(1)) - int(ptn.search(b).group(1))

    dir = _convert_path(dir)
    ptn = re.compile(r'(?i){}(\d+)\.bmp$'.format(spr_name))
    file_list = glob.glob(os.path.join(dir, '{}[0-9]*.bmp'.format(spr_name)))
    file_list = map(_convert_path, sorted(file_list, cmp=__cmp_func))
    for index, file in enumerate(file_list):
        if int(ptn.search(file).group(1)) != index:
            return None

    return file_list

__all__ = [
    'palette',
    '_read_short',
    '_read_int',
    '_read_ints',
    '_write_short',
    '_write_int',
    '_write_ints',
    '_convert_path',
    '_get_file_list'
]