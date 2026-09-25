*** Settings ***
Documentation     Robot Framework Test Suite for Qt5 Linux Application inside Docker Container
Library           qtexpert    mode=agent
Suite Teardown    Close Application

*** Variables ***
${APP_CMD}        python3 tests/test_qt5_app/main.py
${PORT_FILE}      ${TEMPDIR}/qt5_agent_port.txt

*** Test Cases ***
Launch Application And Login
    [Documentation]    Start Qt5 application, test links, checkboxes, text fields, and login
    Launch Application    ${APP_CMD}    port_file_path=${PORT_FILE}
    Wait For Object       usernameInput    timeout=10
    Sleep                 1.5s

    # Test Clickable Hyperlink & Text Verification
    Click Link            name=docLinkLabel
    Sleep                 1s
    Object Property Should Be      name=docStatusLabel      text    Safety Protocol: Reviewed & Interlock Accepted
    Text Should Contain            name=docStatusLabel      Reviewed & Interlock Accepted

    # Test Checkbox controls
    Select Checkbox       name=rememberMeCheck
    Checkbox Should Be Checked     name=rememberMeCheck
    Sleep                 0.5s

    # Type credentials with realistic visual delay
    Type Text Into Object          name=usernameInput    admin
    Sleep                 0.8s
    Type Text Into Object          name=passwordInput    secret123
    Sleep                 0.8s
    Click Object                   name=loginButton
    Object Property Should Be      name=statusLabel      text    Login Successful!
    Sleep                 1.5s

Test Route Alignment With Dropdown Radios And Checkboxes
    [Documentation]    Test QRadioButton priority tiers, QComboBox dropdown options, and safety QCheckBoxes
    # Test Radio Buttons
    Select Radio Button            name=radioHazmat
    Radio Button Should Be Selected        name=radioHazmat
    Radio Button Should Not Be Selected    name=radioExpress
    Object Property Should Be      name=priorityStatusLabel    text    Priority Tier: Hazmat Cargo
    Sleep                 1s

    # Test Safety Verification Checkboxes
    Select Checkbox                name=chkCatenary
    Checkbox Should Be Checked     name=chkCatenary
    Unselect Checkbox              name=chkRetarders
    Checkbox Should Not Be Checked    name=chkRetarders
    Sleep                 1s

    # Test Dropdown / ComboBox Option Selection
    Select Combo Option            name=optionsCombo    Track 3 - Intermodal Container Yard
    Combo Option Should Be         name=optionsCombo    Track 3 - Intermodal Container Yard
    Sleep                 1s

    # Align Route and Verify Signal Status
    Clear And Type Text            name=trainIdInput     HZ-7710
    Sleep                 1s
    Click Object                   name=alignSwitchBtn
    Sleep                 1.5s
    Object Property Should Be      name=signalStatusLabel    text    SIGNAL STATUS: CLEAR / GREEN - TRACK 3
    Text Should Contain            name=routeStatusLabel     aligned to Track 3
    Sleep                 1.5s

Test Yard Operations With Slider SpinBox Progress And TextEdit
    [Documentation]    Switch to Yard Operations tab and test QSlider, QSpinBox, QProgressBar, and QTextEdit
    Select Tab                     name=mainTabWidget    Yard Operations
    Sleep                 1.5s

    # Test Slider Control
    Set Slider Value               name=humpSpeedSlider    40
    Slider Value Should Be         name=humpSpeedSlider    40
    Object Property Should Be      name=sliderValLabel     text    Hump Shunting Speed: 40 km/h
    Sleep                 1s

    # Test SpinBox Control
    Set Spinbox Value              name=wagonCountSpin     35
    Spinbox Value Should Be        name=wagonCountSpin     35
    Object Property Should Be      name=wagonValLabel      text    Total Wagons in Cut: 35 cars
    Sleep                 1s

    # Test Progress Bar Property
    Object Property Should Be      name=yardCapacityBar    value    68

    # Test Multi-line TextEdit Input & Containment
    Clear And Type Text            name=shiftNotesEdit     Intermodal consist inspection cleared on track 3. Handover verified.
    Sleep                 1s
    Text Should Contain            name=shiftNotesEdit     inspection cleared on track 3

    # Test Shunting Counter Button
    Click Object                   type=QPushButton text="Increment Counter"
    Object Property Should Be      name=counterLabel       text    Clicks: 1
    Sleep                 1s
    Click Object                   type=QPushButton text="Increment Counter"
    Object Property Should Be      name=counterLabel       text    Clicks: 2
    Sleep                 1s

Test Text Field Input And Response
    [Documentation]    Test generic cargo manifest input field and response label
    Clear And Type Text            name=myInput          Locomotive Manifest 904-Eastbound
    Sleep                 1s
    Click Object                   name=myButton
    Text Should Be                 name=myLabel          Hello, Locomotive Manifest 904-Eastbound!
    Sleep                 1.5s

Test Emergency Yard Halt Control
    [Documentation]    Trigger emergency yard halt and verify interlocked signals
    Click Object                   name=emergencyHaltBtn
    Sleep                 1.5s
    Object Property Should Be      name=signalStatusLabel    text    SIGNAL STATUS: EMERGENCY RED - HALT
    Object Property Should Be      name=yardBannerLabel      text    YARD STATUS: EMERGENCY STOP ACTIVE - ALL SIGNALS RED
    Sleep                 2s
    # Clear emergency halt to restore operations
    Click Object                   name=emergencyHaltBtn
    Sleep                 1.5s
    Object Property Should Be      name=yardBannerLabel      text    YARD STATUS: NORMAL OPERATIONS
    Sleep                 1.5s

Export UI Hierarchy
    [Documentation]    Dump the live QObject hierarchy to JSON (Squish Object Spy)
    ${tree}=    Dump Object Tree   output_file=${CURDIR}/../results/docker_qt5_ui_tree.json
    Log         UI Tree exported successfully
    Sleep                 2s
