FROM rockylinux:9

ENV TZ=Etc/UTC \
    DISPLAY=:99

# Install build tools, native Linux 9 Qt5 development libraries (Qt5Core, Gui, Widgets, Network, Test), and Xvfb
RUN dnf install -y epel-release dnf-plugins-core \
    && crb enable \
    && dnf install -y \
        gcc-c++ \
        cmake \
        make \
        git \
        qt5-qtbase-devel \
        qt5-qtbase-gui \
        xcb-util-cursor \
        xorg-x11-server-Xvfb \
        x11vnc \
        procps-ng \
        python3 \
        python3-pip \
        python3-devel \
        which \
    && dnf clean all

EXPOSE 5900 9988

WORKDIR /workspace

# Upgrade packaging tools and install requirements
COPY requirements.txt setup.py ./
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel build \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir "PyQt6<6.8"

# Copy workspace sources
COPY . .

# Build the C++ agent (libqt_test_agent.so) and mock C++ Qt5 application
RUN chmod +x ./build_agent.sh ./entrypoint.sh && ./build_agent.sh

# Install robotframework-qtexpert in editable mode
RUN pip3 install -e .

ENTRYPOINT ["/workspace/entrypoint.sh"]
CMD ["robot", "--pythonpath", "src", "--outputdir", "results", "tests/preload_test.robot"]
