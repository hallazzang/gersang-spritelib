import os
import sys
import time
from spritelib.sprite import open_sprite

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: python bmps2spr.py spr_name'
        sys.exit(0)

    spr_name = sys.argv[1]
    if not os.path.isdir(spr_name):
        print 'Error: invalid sprite directory name.'
        sys.exit(1)

    start = time.clock()

    sprite = open_sprite(spr_name)

    print '[Sprite information]'
    print '  name: {}'.format(spr_name)
    print '  width: {} pixels, height: {} pixels'.format(
        sprite.width, sprite.height)
    print '  frame count: {}'.format(sprite.frame_count)
    print 'Zipping sprite file ...',
    sys.stdout.flush()

    sprite.save_file(spr_name + '.spr')

    elapsed = time.clock() - start

    print 'Finished (Elapsed {} seconds)'.format(elapsed)