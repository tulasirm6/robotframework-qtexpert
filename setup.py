from setuptools import setup, find_packages

setup(
    name="robotframework-qtexpert",
    version="2.0.0",
    description="A unified Robot Framework library for testing Qt applications via Agent, Injected C++ Agent (Squish alternative), or Accessibility APIs.",
    author="Thulasi Siripireddy",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"robotframework_qtexpert": ["bin/*", "bin/*.so"]},
    include_package_data=True,
    install_requires=[
        "robotframework",
    ],
    entry_points={
        "console_scripts": [
            "qtexpert-spy=robotframework_qtexpert.spy_gui:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Robot Framework",
        "Topic :: Software Development :: Testing",
        "Operating System :: OS Independent",
    ],
)
