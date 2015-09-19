import os
import sys
import time
from spritelib.sprite import open_sprite

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: python spr2gif.py spr_file'
        sys.exit(0)

    spr_file = sys.argv[1]
    if not os.path.exists(spr_file):
        print 'Error: invalid path for sprite file.'
        sys.exit(1)

    spr_name = os.path.splitext(os.path.split(spr_file)[-1])[0]

    start = time.clock()

    sprite = open_sprite(spr_file, True)

    print '[Sprite information]'
    print '  name: {}'.format(spr_name)
    print '  width: {} pixels, height: {} pixels'.format(
        sprite.width, sprite.height)
    print '  frame count: {}'.format(sprite.frame_count)
    print 'Writing gif file ...',
    sys.stdout.flush()

    sprite.load_all_frames()
    sprite.save_gif_file(spr_name + '.gif')

    elapsed = time.clock() - start

    print 'Finished (Elapsed {} seconds)'.format(elapsed)