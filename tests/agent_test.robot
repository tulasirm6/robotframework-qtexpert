*** Settings ***
Library         qtexpert    mode=agent
Suite Teardown  Close Application

*** Variables ***
${APP_COMMAND}      python3 tests/test_app_agent/main.py
${PORT_FILE_PATH}   ${TEMPDIR}/qt_agent_port.txt

*** Test Cases ***
Test Basic In-Process Agent Interaction
    Launch Application    ${APP_COMMAND}    port_file_path=${PORT_FILE_PATH}
    Wait For Object       myInput    timeout=10
    Input Text            myInput    Qt5 Agent Mode
    Click Button          myButton
    Text Should Be        myLabel    Hello, Qt5 Agent Mode!

Test Squish Style Multi Criteria Locators
    Clear And Type Text   name=myInput    Squish Syntax
    Click Object          type=QPushButton text="Click Me"
    Object Property Should Be    name=myLabel    text    Hello, Squish Syntax!

Test Object Tree Dump
    ${tree}=    Dump Object Tree    output_file=${CURDIR}/../results/agent_ui_tree.json