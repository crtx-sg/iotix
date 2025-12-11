*** Settings ***
Documentation     Basic device simulation tests for IoTix platform
Library           IotixLibrary    base_url=%{DEVICE_ENGINE_URL=http://localhost:8080}
Suite Setup       Register Test Model
Suite Teardown    Cleanup Test Resources

*** Variables ***
${MODEL_ID}       test-sensor-v1
${GROUP_SIZE}     5

*** Test Cases ***
Create And Start Single Device
    [Documentation]    Verify a single device can be created and started
    [Tags]    smoke    device
    ${device}=    Create Device    model_id=${MODEL_ID}
    Should Not Be Empty    ${device}[id]
    Should Be Equal    ${device}[status]    created

    ${started}=    Start Device    ${device}[id]
    Should Be Equal    ${started}[status]    running

    Device Should Be Running    ${device}[id]
    Device Should Be Connected    ${device}[id]

    [Teardown]    Delete Device    ${device}[id]

Device Generates Telemetry
    [Documentation]    Verify device generates and sends telemetry data
    [Tags]    telemetry    device
    ${device}=    Create Device    model_id=${MODEL_ID}
    Start Device    ${device}[id]

    ${metrics}=    Wait For Telemetry    ${device}[id]    min_messages=3    timeout=30
    Should Be Greater Than    ${metrics}[messagesSent]    0
    Should Not Be Empty    ${metrics}[lastTelemetry]

    [Teardown]    Delete Device    ${device}[id]

Create And Start Device Group
    [Documentation]    Verify a group of devices can be created and started
    [Tags]    group    device
    ${group}=    Create Device Group    model_id=${MODEL_ID}    count=${GROUP_SIZE}
    Should Not Be Empty    ${group}[groupId]
    Should Be Equal As Integers    ${group}[deviceCount]    ${GROUP_SIZE}

    ${started}=    Start Device Group    ${group}[groupId]
    Should Be Equal As Integers    ${started}[devicesStarted]    ${GROUP_SIZE}

    [Teardown]    Delete Device Group    ${group}[groupId]

Stop And Restart Device
    [Documentation]    Verify device can be stopped and restarted
    [Tags]    lifecycle    device
    ${device}=    Create Device    model_id=${MODEL_ID}
    Start Device    ${device}[id]
    Device Should Be Running    ${device}[id]

    ${stopped}=    Stop Device    ${device}[id]
    Should Be Equal    ${stopped}[status]    stopped

    ${restarted}=    Start Device    ${device}[id]
    Should Be Equal    ${restarted}[status]    running

    [Teardown]    Delete Device    ${device}[id]

Get Device Metrics
    [Documentation]    Verify device metrics can be retrieved
    [Tags]    metrics    device
    ${device}=    Create Device    model_id=${MODEL_ID}
    Start Device    ${device}[id]
    Sleep    2s    Wait for some telemetry

    ${metrics}=    Get Device Metrics    ${device}[id]
    Should Be True    ${metrics}[messagesSent] >= 0
    Should Be True    ${metrics}[bytesSent] >= 0
    Dictionary Should Contain Key    ${metrics}    lastTelemetry

    [Teardown]    Delete Device    ${device}[id]

*** Keywords ***
Register Test Model
    [Documentation]    Register the test device model
    ${model}=    Create Dictionary
    ...    id=${MODEL_ID}
    ...    name=Test Sensor
    ...    type=sensor
    ...    protocol=mqtt
    ${telemetry}=    Create List
    ${temp_gen}=    Create Dictionary    type=random    min=18    max=28
    ${temp}=    Create Dictionary    name=temperature    type=number    generator=${temp_gen}    intervalMs=1000
    Append To List    ${telemetry}    ${temp}
    Set To Dictionary    ${model}    telemetry=${telemetry}

    ${result}=    Register Device Model    ${model}
    Log    Registered model: ${result}

Cleanup Test Resources
    [Documentation]    Clean up any remaining test resources
    ${stats}=    Get Stats
    Log    Final stats: ${stats}
