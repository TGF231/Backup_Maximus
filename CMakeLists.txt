cmake_minimum_required(VERSION 3.16)
project(BackupMaximus VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT WIN32)
  message(FATAL_ERROR "Backup Maximus e uma aplicacao Windows (Win32 API).")
endif()

set(SOURCES
  src/main.cpp
  src/common.cpp
  src/logger.cpp
  src/config.cpp
  src/network.cpp
  src/sysinfo.cpp
  src/filecopy.cpp
  src/zip.cpp
  src/dbbackup.cpp
  src/email.cpp
  src/engine.cpp
  src/ui_progress.cpp
  src/ui_config.cpp
  src/app.rc
)

add_executable(BackupMaximus WIN32 ${SOURCES})
target_compile_definitions(BackupMaximus PRIVATE UNICODE _UNICODE)

target_link_libraries(BackupMaximus PRIVATE
  comctl32 shlwapi crypt32 bcrypt mpr ole32 uuid shell32 advapi32 user32 gdi32)

if(MSVC)
  target_compile_options(BackupMaximus PRIVATE /W4 /EHsc)
  set_property(TARGET BackupMaximus PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded")
else()
  target_compile_options(BackupMaximus PRIVATE -Wall -Wextra -Wno-unused-parameter -municode)
  target_link_options(BackupMaximus PRIVATE -municode -static)
endif()

# Testes do nucleo (sem UI) — ver tests/test_core.cpp
enable_testing()
add_executable(bm_tests
  tests/test_core.cpp
  src/common.cpp src/logger.cpp src/config.cpp src/sysinfo.cpp
  src/filecopy.cpp src/dbbackup.cpp src/zip.cpp)
target_include_directories(bm_tests PRIVATE src)
target_compile_definitions(bm_tests PRIVATE UNICODE _UNICODE)
target_link_libraries(bm_tests PRIVATE shlwapi crypt32 bcrypt ole32 shell32 advapi32)
add_test(NAME core COMMAND bm_tests)
