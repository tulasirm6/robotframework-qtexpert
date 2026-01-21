*** Settings ***
Library         qtexpert    mode=a11y
Suite Teardown  Close Application

*** Variables ***
 ${APP_COMMAND}      python tests/test_app_a11y/main.py
 ${WINDOW_TITLE}     A11yDemoApp

*** Test Cases ***
Test With A11y
    Launch Application    ${APP_COMMAND}    window_title=${WINDOW_TITLE}
    Input Text    myInput    A11y Mode
    Click Button    Click Me
    Text Should Be    myLabel    Hello, A11y Mode!