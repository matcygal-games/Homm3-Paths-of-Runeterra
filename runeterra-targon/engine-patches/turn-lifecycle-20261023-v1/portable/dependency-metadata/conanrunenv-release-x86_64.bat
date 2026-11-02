@echo off
chcp 65001 > nul
@echo off


setlocal
echo @echo off > "%~dp0/deactivate_conanrunenv-release-x86_64.bat"
echo echo Restoring environment for conanrunenv-release-x86_64.bat >> "%~dp0/deactivate_conanrunenv-release-x86_64.bat"
for %%v in (PATH) do (
    set foundenvvar=
    for /f "delims== tokens=1,2" %%a in ('set') do (
        if /I "%%a" == "%%v" (
            echo set "%%a=%%b">> "%~dp0/deactivate_conanrunenv-release-x86_64.bat"
            set foundenvvar=1
        )
    )
    if not defined foundenvvar (
        echo set %%v=>> "%~dp0/deactivate_conanrunenv-release-x86_64.bat"
    )
)
endlocal




if defined PATH (
    set "PATH=<SDK_ROOT>\conan-home\p\minizf455d3a92e5f9\p\bin;<SDK_ROOT>\conan-home\p\onetbeec24a0b9e43d\p\bin;<SDK_ROOT>\conan-home\p\sdl_i44042adf09a1b\p\bin;<SDK_ROOT>\conan-home\p\sdl_ma71c9f6f2fcfe\p\bin;<SDK_ROOT>\conan-home\p\ogg5ed6d81817e4c\p\bin;<SDK_ROOT>\conan-home\p\sdl_td9fee9bb38b98\p\bin;<SDK_ROOT>\conan-home\p\boost2daea649742b4\p\bin;<SDK_ROOT>\conan-home\p\ffmpe58f6e49b85723\p\bin;<SDK_ROOT>\conan-home\p\bzip229180355bba12\p\bin;<SDK_ROOT>\conan-home\p\xz_ut74796b4afa323\p\bin;<SDK_ROOT>\conan-home\p\opusa6deb694451ce\p\bin;<SDK_ROOT>\conan-home\p\sdl0eecc6fcfc36a\p\bin;<SDK_ROOT>\conan-home\p\libica3ca054de0149\p\bin;<SDK_ROOT>\conan-home\p\qtde84f76087842\p\bin;<SDK_ROOT>\conan-home\p\libpnea4a3e718b3d7\p\bin;<SDK_ROOT>\conan-home\p\zlib705a7ddfe2543\p\bin;%PATH%"
) else (
    set "PATH=<SDK_ROOT>\conan-home\p\minizf455d3a92e5f9\p\bin;<SDK_ROOT>\conan-home\p\onetbeec24a0b9e43d\p\bin;<SDK_ROOT>\conan-home\p\sdl_i44042adf09a1b\p\bin;<SDK_ROOT>\conan-home\p\sdl_ma71c9f6f2fcfe\p\bin;<SDK_ROOT>\conan-home\p\ogg5ed6d81817e4c\p\bin;<SDK_ROOT>\conan-home\p\sdl_td9fee9bb38b98\p\bin;<SDK_ROOT>\conan-home\p\boost2daea649742b4\p\bin;<SDK_ROOT>\conan-home\p\ffmpe58f6e49b85723\p\bin;<SDK_ROOT>\conan-home\p\bzip229180355bba12\p\bin;<SDK_ROOT>\conan-home\p\xz_ut74796b4afa323\p\bin;<SDK_ROOT>\conan-home\p\opusa6deb694451ce\p\bin;<SDK_ROOT>\conan-home\p\sdl0eecc6fcfc36a\p\bin;<SDK_ROOT>\conan-home\p\libica3ca054de0149\p\bin;<SDK_ROOT>\conan-home\p\qtde84f76087842\p\bin;<SDK_ROOT>\conan-home\p\libpnea4a3e718b3d7\p\bin;<SDK_ROOT>\conan-home\p\zlib705a7ddfe2543\p\bin"
)