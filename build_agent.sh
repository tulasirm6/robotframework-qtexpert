#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== [1/2] Building C++ Qt5 Injected Agent (libqt_test_agent.so) ==="
mkdir -p "${SCRIPT_DIR}/cpp_agent/build"
cd "${SCRIPT_DIR}/cpp_agent/build"
cmake ..
make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)

if [ -f "${SCRIPT_DIR}/cpp_agent/build/libqt_test_agent.so" ]; then
    mkdir -p "${SCRIPT_DIR}/src/robotframework_qtexpert/bin"
    cp "${SCRIPT_DIR}/cpp_agent/build/libqt_test_agent.so" "${SCRIPT_DIR}/src/robotframework_qtexpert/bin/libqt_test_agent.so"
    echo " -> Bundled libqt_test_agent.so into src/robotframework_qtexpert/bin/"
fi

if [ -d "${SCRIPT_DIR}/tests/mock_app" ]; then
    echo "=== [2/2] Building Mock Qt5 Application ==="
    mkdir -p "${SCRIPT_DIR}/tests/mock_app/build"
    cd "${SCRIPT_DIR}/tests/mock_app/build"
    cmake ..
    make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
    echo " -> Built mock application: ${SCRIPT_DIR}/tests/mock_app/build/qt5_mock_app"
fi

echo "=== Build Complete! ==="
