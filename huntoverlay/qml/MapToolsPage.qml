import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: page

    Theme { id: theme }

    Flickable {
        anchors.fill: parent
        clip: true
        contentWidth: width
        contentHeight: Math.max(height, cards.implicitHeight)
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {
            policy: page.height >= 430 ? ScrollBar.AlwaysOff
                                       : ScrollBar.AsNeeded
            width: 6
            contentItem: Rectangle {
                radius: 3
                color: theme.strokeStrong
                opacity: 0.65
            }
        }

        GridLayout {
            id: cards
            width: parent.width - 12
            columns: width >= 680 ? 2 : 1
            columnSpacing: 12
            rowSpacing: 12

            FluentCard {
                Layout.fillWidth: true
                Layout.preferredHeight: 236
                title: panelBridge.uiText("Map Controls")
                subtitle: panelBridge.uiText(
                    "Choose the active map and marker scale."
                )
                iconKind: "map"
                highlighted: true

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: panelBridge.uiText("Map:")
                        color: theme.textSecondary
                        font.family: theme.fontUi
                        font.pixelSize: 12
                    }

                    FluentComboBox {
                        id: mapSelector
                        objectName: "mapSelector"
                        Layout.fillWidth: true
                        model: panelBridge.mapOptions
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: panelBridge.currentMapIndex
                        onActivated: panelBridge.selectMap(index)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Scale:")
                        color: theme.textSecondary
                        font.family: theme.fontUi
                        font.pixelSize: 12
                    }

                    FluentButton {
                        text: "−"
                        compact: true
                        implicitWidth: 34
                        Accessible.name: panelBridge.uiText(
                            "Decrease marker scale"
                        )
                        onClicked: panelBridge.adjustScale(-0.05)
                    }

                    Rectangle {
                        Layout.preferredWidth: 88
                        Layout.preferredHeight: 32
                        radius: theme.radiusControl
                        color: theme.input
                        border.width: 1
                        border.color: theme.stroke

                        Text {
                            anchors.left: parent.left
                            anchors.right: stepper.left
                            anchors.verticalCenter: parent.verticalCenter
                            text: Number(panelBridge.scaleValue).toFixed(2)
                            color: theme.textPrimary
                            font.family: theme.fontMono
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Rectangle {
                            id: stepper
                            anchors.top: parent.top
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            width: 22
                            radius: theme.radiusControl
                            color: "#1A2A34"

                            Rectangle {
                                anchors.left: parent.left
                                width: 1
                                height: parent.height
                                color: theme.stroke
                            }

                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width
                                height: 1
                                color: theme.stroke
                            }

                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.top: parent.top
                                text: "⌃"
                                color: theme.textSecondary
                                font.family: theme.fontUi
                                font.pixelSize: 9
                            }

                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.bottom: parent.bottom
                                text: "⌄"
                                color: theme.textSecondary
                                font.family: theme.fontUi
                                font.pixelSize: 9
                            }
                        }
                    }

                    FluentButton {
                        text: "+"
                        compact: true
                        implicitWidth: 34
                        Accessible.name: panelBridge.uiText(
                            "Increase marker scale"
                        )
                        onClicked: panelBridge.adjustScale(0.05)
                    }
                }

                FluentCheckBox {
                    objectName: "numberSwitch"
                    Layout.fillWidth: true
                    text: panelBridge.uiText("1-4 map switch keys")
                    checked: panelBridge.numberSwitchEnabled
                    onToggled: {
                        if (checked !== panelBridge.numberSwitchEnabled)
                            panelBridge.setNumberSwitchFromUi(checked)
                    }
                }

                Item { Layout.fillHeight: true }
            }

            FluentCard {
                Layout.fillWidth: true
                Layout.preferredHeight: 236
                title: panelBridge.uiText("Official Visibility")
                subtitle: panelBridge.uiText(
                    "Show or hide the complete official POI layer."
                )
                iconKind: "poi"

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    radius: theme.radiusControl
                    color: theme.input
                    border.width: 1
                    border.color: theme.strokeSubtle

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12

                        Rectangle {
                            Layout.preferredWidth: 8
                            Layout.preferredHeight: 8
                            radius: 4
                            color: theme.success
                        }

                        Text {
                            Layout.fillWidth: true
                            text: panelBridge.uiText(
                                "Official categories available: {count}"
                            ).replace("{count}", panelBridge.typeCount)
                            color: theme.textSecondary
                            font.family: theme.fontUi
                            font.pixelSize: 12
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    FluentButton {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Show All POIs")
                        primary: true
                        onClicked: panelBridge.setAllTypesFromUi(true)
                    }

                    FluentButton {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Hide All POIs")
                        onClicked: panelBridge.setAllTypesFromUi(false)
                    }
                }

                Item { Layout.fillHeight: true }
            }

            FluentCard {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                title: panelBridge.uiText("Custom POIs")
                subtitle: panelBridge.uiText(
                    "Create local markers without changing official data."
                )
                iconKind: "flag"

                FluentCheckBox {
                    objectName: "userPoisSwitch"
                    Layout.fillWidth: true
                    text: panelBridge.uiText("Show custom POIs")
                    checked: panelBridge.userPoisEnabled
                    onToggled: {
                        if (checked !== panelBridge.userPoisEnabled)
                            panelBridge.setUserPoisFromUi(checked)
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: panelBridge.uiText("POI type:")
                        color: theme.textSecondary
                        font.family: theme.fontUi
                        font.pixelSize: 12
                    }

                    FluentComboBox {
                        id: customPoiSelector
                        objectName: "customPoiSelector"
                        Layout.fillWidth: true
                        model: panelBridge.customPoiOptions
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: panelBridge.currentPoiTypeIndex
                        onActivated: panelBridge.selectPoiType(index)
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: panelBridge.customPoiCountText
                    color: theme.textTertiary
                    font.family: theme.fontUi
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    FluentButton {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Add from Map")
                        primary: true
                        onClicked: panelBridge.requestPoiPickFromUi()
                    }

                    FluentButton {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Manage POIs")
                        onClicked: panelBridge.requestPoiEditorFromUi()
                    }
                }
            }

            FluentCard {
                Layout.fillWidth: true
                Layout.preferredHeight: 260
                title: panelBridge.uiText("Measurement")
                subtitle: panelBridge.uiText(
                    "Measure distances or clear stored rulers."
                )
                iconKind: "measure"

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    radius: theme.radiusControl
                    color: theme.input
                    border.width: 1
                    border.color: theme.strokeSubtle

                    Text {
                        anchors.fill: parent
                        anchors.margins: 11
                        text: panelBridge.uiText(
                            "Choose Ruler, then click two points on the map."
                        )
                        color: theme.textTertiary
                        font.family: theme.fontUi
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    FluentButton {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Ruler")
                        primary: true
                        onClicked: panelBridge.requestRulerFromUi()
                    }

                    FluentButton {
                        Layout.fillWidth: true
                        text: panelBridge.uiText("Clear Rulers")
                        onClicked: panelBridge.requestClearRulersFromUi()
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }
    }
}
