[app]
title = VAC
package.name = vac
package.domain = org.sasi
source.dir = .
source.include_exts = py,ttf,otf,txt
source.include_patterns = assets/fonts/*
source.exclude_dirs = tests, tools, bin, venv, .venv, .github, .buildozer, __pycache__
version = 0.1.0

# Kivy 2.3.0 is the version the pinned p4a release (p4a.branch below) was tested with.
# Upgrade kivy and p4a.branch together.
requirements = python3,kivy==2.3.0,pyjnius,android,sqlite3,openssl,plyer,requests,urllib3,certifi,charset-normalizer,idna

orientation = portrait
fullscreen = 0

# Internet for the AI team, microphone for speaking, camera for handwriting and objects
android.permissions = INTERNET,RECORD_AUDIO,CAMERA
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
# Android 11+ only lets an app see the text-to-speech engine if the manifest asks for it
android.extra_manifest_xml = ./android_manifest_extra.xml

# Pinned: an unpinned p4a follows master, which can break builds without any change here.
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
