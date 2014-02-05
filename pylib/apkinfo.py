#!/usr/bin/env python3

import os
import sys
import tempfile
from subprocess import check_call as run
from subprocess import Popen, PIPE, CalledProcessError
from xml.etree import ElementTree as ET
from collections import namedtuple

from myutils import at_dir, firstExistentPath

VER_ATTR = '{http://schemas.android.com/apk/res/android}versionName'
ICON_ATTR = '{http://schemas.android.com/apk/res/android}icon'
NAME_ATTR = '{http://schemas.android.com/apk/res/android}label'

ApkInfo = namedtuple('ApkInfo', 'id version name icon')
class ApktoolFailed(Exception): pass

def apkinfo(apk):
  with tempfile.TemporaryDirectory('apk') as tempdir:
    try:
      run(["apktool", "d", "-f", apk, tempdir])
    except CalledProcessError:
      raise ApktoolFailed

    with at_dir(tempdir):
      manifest = ET.parse('AndroidManifest.xml').getroot()
      package_id = manifest.get('package')
      package_ver = manifest.get(VER_ATTR)

      app = manifest.find('application')
      icon = app.get(ICON_ATTR)
      name = app.get(NAME_ATTR)

      if os.path.isdir('res'):
        with at_dir('res'):
          if name and name.startswith('@string/'):
            sid = name.split('/', 1)[1]
            d = firstExistentPath(('values-zh-rCN', 'values-zh-rTM', 'values'))
            strings = ET.parse(os.path.join(d, 'strings.xml')).getroot()
            name = strings.findtext('string[@name="%s"]' % sid)

          if icon and icon.startswith('@drawable/'):
            iconname = icon.split('/', 1)[1]
            iconfile = firstExistentPath(
              '%s/%s.png' % (d, iconname) for d in
              ['drawable-xxhdpi', 'drawable-xhdpi', 'drawable-hdpi', 'drawable']
            )
            with open(iconfile, 'rb') as f:
              icon = f.read()

    return ApkInfo(package_id, package_ver, name, icon)

def showInfo(apks):
  for apk in apks:
    try:
      info = apkinfo(apk)
    except ApktoolFailed:
      print('E: apktool failed.')
      continue

    print('I: displaying info as image...')
    display = Popen(['display', '-'], stdin=PIPE)
    convert = Popen([
      'convert', '-alpha', 'remove',
      '-font', '文泉驿正黑', '-pointsize', '12', '-gravity', 'center',
      'label:' + info.id,
      'label:' + info.version,
      '-' if info.icon else 'label:(No Icon)',
      'label:' + (info.name or '(None)'),
      '-append', 'png:-',
    ], stdin=PIPE, stdout=display.stdin)
    if info.icon:
      convert.stdin.write(info.icon)
    convert.stdin.close()
    convert.wait()
    display.stdin.close()
    display.wait()

if __name__ == '__main__':
  showInfo(sys.argv[1:])