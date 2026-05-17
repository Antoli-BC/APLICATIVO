[app]

title = CONTROL DE OBRA
package.name = controlobra
package.domain = org.obra.control

source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,svg,xlsx,txt,sqlite

version = 1.2.0

requirements = python3,kivy==2.3.1,plyer==2.1.0,openpyxl==3.1.5
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

android.permissions = CAMERA, INTERNET, READ_MEDIA_IMAGES, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.window_softinput_mode = adjustResize
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1
android.add_src = javasrc
android.add_res = res
android.extra_manifest_application_arguments = <provider android:name="org.obra.control.controlobra.GenericFileProvider" android:authorities="org.obra.control.controlobra.fileprovider" android:exported="false" android:grantUriPermissions="true"><meta-data android:name="android.support.FILE_PROVIDER_PATHS" android:resource="@xml/file_paths"/></provider>

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
