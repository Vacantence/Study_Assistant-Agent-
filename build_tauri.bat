@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
set PATH=C:\Users\Lenovo\.cargo\bin;%PATH%

REM Ensure MSVC link.exe is found before Git's link.exe
set MSVC_LINK=C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64
set PATH=%MSVC_LINK%;%PATH%

cd /d "D:\VScode\Agent\Study_Assistant\frontend"
npm run tauri build 2>&1
