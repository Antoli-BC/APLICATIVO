[app]

title = CONTROL DE OBRA
package.name = controlobra
package.domain = org.obra.control

source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,svg,xlsx,txt,sqlite

version = 1.2.0
version.filename = %(source.dir)s/main.py

requirements = python3,kivy==2.3.0,plyer==2.1.1,python-docx==1.1.2,openpyxl==3.1.5
orientation = portrait
fullscreen = 0

osx.python_version = 3
osx.kivy_version = 2.3.0

android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

android.permissions = CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, INTERNET, READ_MEDIA_IMAGES
android.window_softinput_mode = adjustResize
android.gradle_dependencies = androidx.core:core:1.10.1,androidx.activity:activity:1.7.2,androidx.appcompat:appcompat:1.6.1
android.add_src =

#presplash.filename = %(source.dir)s/presplash.png
#icon.filename = %(source.dir)s/icon.png
presplash_color = #101010

android.wakelock = False
android.copy_libs = 1
android.debug = True
android.ndk_verbose = False
android.rename_apk = yes
android.keyalias = 
android.keystore = 

ios.codesign.allowed = False
