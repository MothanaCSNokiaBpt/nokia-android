[app]
title = Nokia Status
package.name = nokiastatus
package.domain = com.ict18.nokia
source.dir = .
source.include_exts = py,kv,json,png,jpg,atlas
version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
