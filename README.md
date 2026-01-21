# robotframework-qtexpert

A unified Robot Framework library for testing Qt applications. It provides a powerful and flexible API to automate your GUIs, whether they are open-source or closed-source, running on Linux, Windows, or macOS.

This library uniquely supports two distinct approaches to automation, allowing you to choose the best tool for your specific use case.

## Key Features

- **Dual-Mode Operation**: Choose between the powerful Agent Mode or the non-invasive Accessibility Mode.
- **Cross-Platform**: Test your applications on Windows, Linux, and macOS with a single test suite.
- **Unified API**: The same keywords work regardless of the backend mode or operating system.
- **Backward Compatible**: Agent mode supports multiple Qt bindings (PyQt5/6, PySide2/6).
- **Robot Framework Native**: Seamlessly integrates with your existing Robot Framework test infrastructure.

## The Core Concept: Agent vs. Accessibility

The fundamental challenge in GUI automation is that your test script runs in a different process than your application. This library solves this in two different ways.

### 1. Agent Mode (The "In-Process" Approach)

In this mode, a tiny agent server is started inside your application's process. The library (the client) communicates with this agent over a local network connection.

**How it Works:** You add a few lines of code to your application to start the agent. The agent has full, direct access to all Qt objects. The library sends commands like "click button X" to the agent, which executes them using the real Qt API.

**Pros:**
- **Extremely Reliable**: Direct access to the Qt object model.
- **Full Power**: Can access any Qt property or method.
- **Stable Locators**: Uses Qt's objectName, which is the most reliable way to identify elements.

**Cons:**
- **Minimal Integration**: Requires a small, conditional code change in the application under test.

**Best For:** Applications you are building yourself or where you can influence the source code.

### 2. Accessibility (A11y) Mode (The "OS-Level" Approach)

This mode uses the operating system's native accessibility APIs, which are designed for tools like screen readers.

**How it Works:** The library connects to your application as an external assistive technology. It inspects the application's accessibility tree to find buttons, text fields, and other controls.

**Pros:**
- **No Code Changes**: Works with any application that has accessibility enabled (which is the default for most Qt apps).
- **Ideal for Closed-Source**: Perfect for testing third-party applications where you cannot modify the code.

**Cons:**
- **Less Powerful**: Limited to what the OS API exposes.
- **More Brittle**: Locators like text or position can change more easily than an objectName.

**Best For:** Closed-source, third-party, or legacy applications where code integration is not possible.

### Comparison Summary

| Feature | Agent Mode | Accessibility Mode |
|---------|------------|-------------------|
| Reliability | Very High | Medium |
| Power | Full Qt API Access | Limited to OS API |
| Locator Stability | Excellent (objectName) | Medium (Text, Control Type, Position) |
| Code Change Required? | Minimal & Conditional | None |
| Use Case | Testable, open-source, or in-house apps | Closed-source, third-party, or legacy apps |

## Installation

Install the library from PyPI:

```bash
pip install robotframework-qtexpert
```

You must also install the dependencies for the mode(s) you plan to use.

### For Agent Mode

Choose one or more Qt bindings:

```bash
pip install robotframework-qtexpert[agent-pyqt6]
# or
pip install robotframework-qtexpert[agent-all]
```

### For Accessibility Mode

Install the dependencies for your target OS:

```bash
# For Windows
pip install robotframework-qtexpert[a11y-windows]

# For Linux
pip install robotframework-qtexpert[a11y-linux]

# For macOS
pip install robotframework-qtexpert[a11y-macos]
```

### For Everything (Recommended for Development)

```bash
pip install robotframework-qtexpert[all]
```

## Quick Start & Usage Examples

### Example 1: Using Agent Mode

**Prerequisite:** Your application must be set up to launch the agent. See the `tests/test_app_agent/main.py` file in this repository for a minimal example.

```robotframework
*** Settings ***
Library         qtexpert    mode=agent
Suite Teardown  Close Application

*** Variables ***
${APP_COMMAND}      python /path/to/your/agent_enabled_app.py
${PORT_FILE_PATH}   ${TEMPDIR}/qt_agent_port.txt

*** Test Cases ***
Test User Login With Agent
    # Launch the app. The library will wait for the agent to write its port to the file.
    Launch Application    ${APP_COMMAND}    port_file_path=${PORT_FILE_PATH}

    # Use the stable 'objectName' as a locator
    Input Text    username_field    testuser
    Input Text    password_field    password123
    Click Button    login_button

    # Verify the result
    Text Should Be    status_label    Login Successful!
```

### Example 2: Using Accessibility Mode

**Prerequisite:** Your application must be accessible. This is the default for most standard Qt widgets.

```robotframework
*** Settings ***
Library         qtexpert    mode=a11y
Suite Teardown  Close Application

*** Variables ***
${APP_COMMAND}      C:/Program Files/MyQtApp/MyQtApp.exe
${WINDOW_TITLE}     MyQtApp Main Window

*** Test Cases ***
Test User Login With A11y
    # Launch the app. The library will find it by its window title.
    Launch Application    ${APP_COMMAND}    window_title=${WINDOW_TITLE}

    # Use visible text or control types as locators
    Input Text    Username    testuser
    Input Text    Password    password123
    Click Button    Login

    # Verify the result
    Text Should Be    Login Successful!    # Locates a label with this text
```

## Keyword Reference

The library is organized into logical keyword groups:

- **Application**: `Launch Application`, `Close Application`
- **Generic**: `Click Button`, `Input Text`, `Text Should Be`

For a full list of keywords and their arguments, please refer to the Keyword Documentation.

## Development & Publishing

To build the package for PyPI:

1. Install build tools:
   ```bash
   pip install build twine
   ```
2. Build the source distribution and wheel:
   ```bash
   python -m build
   ```
3. Upload to PyPI (requires credentials):
   ```bash
   python -m twine upload dist/*
   ```

## Contributing

Contributions are welcome! If you have a bug report, feature request, or want to submit a pull request, please visit our GitHub Issues page.

For major changes, please open an issue first to discuss what you would like to change.

Please ensure you add tests for any new features and that all existing tests pass.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
