"""Make the OpenCV loader work inside a macOS application bundle.

OpenCV does not ship a plain extension module. Its `cv2/__init__.py` is a
loader that puts the directory holding the real extension at the front of
`sys.path`, drops itself from `sys.modules`, and imports `cv2` again to pick up
the native module.

It decides whether to insert that directory at position 0 or position 1 by
checking whether `sys.path[0]` is the parent of its own directory. In a plain
PyInstaller directory build that test passes. In a macOS application bundle it
cannot: PyInstaller puts data files in `Contents/Resources` and binaries in
`Contents/Frameworks`, so the loader resolves its own location to
`Contents/Resources/cv2` while `sys.path[0]` is `Contents/Frameworks`. The
directory is then inserted at position 1, `Contents/Frameworks/cv2` still wins,
and the loader imports itself instead of the extension. OpenCV detects the
recursion and raises:

    ERROR: recursion is detected during loading of "cv2" binary extensions.

`sys.OpenCV_REPLACE_SYS_PATH_0` is the switch OpenCV provides for exactly this
situation. Setting it before the first import of cv2 forces the insertion at
position 0. The loader restores the original `sys.path` when it is done, so
nothing else is affected.
"""

import sys


if not hasattr(sys, "OpenCV_REPLACE_SYS_PATH_0"):
    sys.OpenCV_REPLACE_SYS_PATH_0 = True
