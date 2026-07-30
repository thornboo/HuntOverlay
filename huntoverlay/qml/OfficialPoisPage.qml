import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Item {
    id: page

    Theme { id: theme }

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        FluentCard {
            Layout.fillWidth: true
            Layout.preferredHeight: 112
            title: panelBridge.uiText("Official Filters")
            subtitle: panelBridge.uiText(
                "Toggle categories and tune their marker colors."
            )
            iconKind: "poi"

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                FluentButton {
                    text: panelBridge.uiText("Select All")
                    primary: true
                    onClicked: panelBridge.setAllTypesFromUi(true)
                }

                FluentButton {
                    text: panelBridge.uiText("Deselect All")
                    onClicked: panelBridge.setAllTypesFromUi(false)
                }

                Item { Layout.fillWidth: true }

                FluentButton {
                    text: panelBridge.uiText("Reset Colors")
                    onClicked: panelBridge.requestResetColorsFromUi()
                }
            }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: Math.max(height, poiGrid.implicitHeight)
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                width: 6
                contentItem: Rectangle {
                    radius: 3
                    color: theme.strokeStrong
                    opacity: 0.65
                }
            }

            GridLayout {
                id: poiGrid
                width: parent.width - 12
                columns: width >= 680 ? 2 : 1
                columnSpacing: 10
                rowSpacing: 8

                Repeater {
                    model: panelBridge.typeItems

                    delegate: Rectangle {
                        required property var modelData

                        Layout.fillWidth: true
                        Layout.preferredHeight: 58
                        radius: theme.radiusControl
                        color: hoverArea.containsMouse
                               ? theme.cardHover : theme.card
                        border.width: 1
                        border.color: theme.strokeSubtle

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 11
                            spacing: 10

                            FluentSwitch {
                                Layout.fillWidth: true
                                text: modelData.label
                                checked: modelData.enabled
                                onToggled: {
                                    if (checked !== modelData.enabled)
                                        panelBridge.setTypeEnabledFromUi(
                                            modelData.key, checked
                                        )
                                }
                            }

                            Rectangle {
                                Layout.preferredWidth: 24
                                Layout.preferredHeight: 24
                                radius: 12
                                color: modelData.fill
                                border.width: 2
                                border.color: modelData.border

                                MouseArea {
                                    id: colorArea
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    Accessible.name: panelBridge.uiText(
                                        "Choose marker color"
                                    )
                                    onClicked: panelBridge.chooseTypeColor(
                                        modelData.key
                                    )
                                }
                            }
                        }

                        MouseArea {
                            id: hoverArea
                            anchors.fill: parent
                            acceptedButtons: Qt.NoButton
                            hoverEnabled: true
                            propagateComposedEvents: true
                        }
                    }
                }
            }
        }
    }
}
