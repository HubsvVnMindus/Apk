[app]
title = TST-TOOL NOVA
package.name = tsttoolnova
package.domain = vn.tsttool
source.dir = .
source.include_exts = py,kv,png,jpg,json,txt,enc
version = 3.0.0
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.ndk = 26b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = False

# Bắt buộc pin cùng version cho hostpython3 và python3
requirements = hostpython3==3.11.9,python3==3.11.9,kivy==2.3.1,requests,pytz,websocket-client,rich,cryptography==41.0.7

[buildozer]
log_level = 2
warn_on_root = 1
