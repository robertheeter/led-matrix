# type: ignore

import storage

storage.remount("/", readonly=False, disable_concurrent_write_protection=True) # disable concurrent write protection to allow writing to the filesystem
