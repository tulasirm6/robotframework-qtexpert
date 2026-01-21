*** Settings ***
Library         qtexpert    mode=agent
Suite Teardown  Close Application

*** Variables ***
 ${APP_COMMAND}      python tests/test_app_agent/main.py
 ${PORT_FILE_PATH}   ${TEMPDIR}/qt_agent_port.txt

*** Test Cases ***
Test With Agent
    Launch Application    ${APP_COMMAND}    port_file_path=${PORT_FILE_PATH}
    Input Text    myInput    Agent Mode
    Click Button    myButton
    Text Should Be    myLabel    Hello, Agent Mode!