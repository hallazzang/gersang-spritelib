# gersang-spritelib

Note
----
Compile [`cspritelib.c`](spritelib/cspritelib.c) and build C extension for better performance.

Basic Usage
-----------
Convert sprite file(with `.spr` extension) to bitmap files.
```python
from spritelib.sprite import open_sprite

magicball = open_sprite('./example_sprites/magicball.spr')

# print sprite informations
print 'width: {} pixels, height: {} pixels'.format(sprite.width, sprite.height)
print 'frame count: {}'.format(sprite.frame_count)

sprite.save_dir('./output/magicball')
```

Convert bitmap files to sprite file.
```python
from spritelib.sprite import open_sprite

magicball = open_sprite('./output/magicball')
sprite.save_file('./output/magicball.spr')
```

That's it.
