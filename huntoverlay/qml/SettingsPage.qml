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
            policy: ScrollBar.AsNeeded
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
                Layout.rowSpan: cards.columns === 2 ? 2 : 1
                Layout.preferredHeight: Math.max(
                    260, keybindColumn.implicitHeight + 88
                )
                title: panelBridge.uiText("Keybinds")
                subtitle: panelBridge.uiText(
                    "Keep common overlay actions within easy reach."
                )
                iconKind: "keyboard"
                highlighted: true

                ColumnLayout {
                    id: keybindColumn
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: panelBridge.keybindItems

                        delegate: RowLayout {
                            required property var modelData

                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                color: theme.textSecondary
                                font.family: theme.fontUi
                                font.pixelSize: 12
                                elide: Text.ElideRight
                            }

                            Rectangle {
                                Layout.preferredWidth: 64
                                Layout.preferredHeight: 30
                                radius: theme.radiusControl
                                color: theme.input
                                border.width: 1
                                border.color: theme.stroke

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.value
                                    color: theme.textPrimary
                                    font.family: theme.fontMono
                                    font.pixelSize: 11
                                }
                            }

                            FluentButton {
                                text: panelBridge.uiText("Set")
                                compact: true
                                implicitWidth: 54
                                onClicked: panelBridge.requestBindEditFromUi(
                                    modelData.action
                                )
                            }
                        }
                    }
                }
            }

            FluentCard {
                Layout.fillWidth: true
                Layout.preferredHeight: 220
                title: panelBridge.uiText("Overlay Behavior")
                subtitle: panelBridge.uiText(
                    "Choose how the overlay and control center appear during play."
                )
                iconKind: "overlay"

                FluentSwitch {
                    Layout.fillWidth: true
                    text: panelBridge.uiText("Hold Tab to show overlay")
                    checked: panelBridge.holdTabModeEnabled
                    onToggled: {
                        if (checked !== panelBridge.holdTabModeEnabled)
                            panelBridge.setHoldTabModeFromUi(checked)
                    }
                }

                FluentSwitch {
                    Layout.fillWidth: true
                    text: panelBridge.uiText(
                        "Panel follows Tab (show/hide with overlay)"
                    )
                    checked: panelBridge.panelFollowTabEnabled
                    onToggled: {
                        if (checked !== panelBridge.panelFollowTabEnabled)
                            panelBridge.setPanelFollowTabFromUi(checked)
                    }
                }

                FluentSwitch {
                    Layout.fillWidth: true
                    text: panelBridge.uiText("Block Shift+Tab")
                    checked: panelBridge.blockShiftTabEnabled
                    onToggled: {
                        if (checked !== panelBridge.blockShiftTabEnabled)
                            panelBridge.setBlockShiftTabFromUi(checked)
                    }
                }
            }

            FluentCard {
                Layout.fillWidth: true
                Layout.preferredHeight: 276
                title: panelBridge.uiText("Application")
                subtitle: panelBridge.uiText(
                    "Language and notification-area behavior."
                )
                iconKind: "settings"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        text: panelBridge.uiText("Language:")
                        color: theme.textSecondary
                        font.family: theme.fontUi
                        font.pixelSize: 12
                    }

                    FluentComboBox {
                        Layout.fillWidth: true
                        model: panelBridge.languageOptions
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: panelBridge.currentLanguageIndex
                        onActivated: panelBridge.selectLanguage(index)
                    }
                }

                Text {
                    visible: panelBridge.languageHintVisible
                    Layout.fillWidth: true
                    text: panelBridge.uiText(
                        "Restart to apply the language change."
                    )
                    color: theme.warning
                    font.family: theme.fontUi
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                FluentSwitch {
                    Layout.fillWidth: true
                    text: panelBridge.uiText("Show notification area icon")
                    checked: panelBridge.trayIconEnabled
                    onToggled: {
                        if (checked !== panelBridge.trayIconEnabled)
                            panelBridge.setTrayIconFromUi(checked)
                    }
                }

                FluentSwitch {
                    Layout.fillWidth: true
                    text: panelBridge.uiText(
                        "Minimize panel to notification area"
                    )
                    checked: panelBridge.minimizeToTrayEnabled
                    onToggled: {
                        if (checked !== panelBridge.minimizeToTrayEnabled)
                            panelBridge.setMinimizeToTrayFromUi(checked)
                    }
                }

                FluentSwitch {
                    Layout.fillWidth: true
                    text: panelBridge.uiText(
                        "Start hidden in notification area"
                    )
                    checked: panelBridge.startHiddenToTrayEnabled
                    onToggled: {
                        if (checked !== panelBridge.startHiddenToTrayEnabled)
                            panelBridge.setStartHiddenToTrayFromUi(checked)
                    }
                }
            }

            FluentCard {
                Layout.fillWidth: true
                Layout.columnSpan: cards.columns
                Layout.preferredHeight: 176
                title: panelBridge.uiText("Data & Storage")
                subtitle: panelBridge.uiText(
                    "Inspect local storage or restore the default configuration."
                )
                iconKind: "storage"

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 5

                        Text {
                            text: panelBridge.uiText("Aspect:")
                                  + panelBridge.aspectLabel
                                  + "  ·  v" + panelBridge.configVersion
                            color: theme.textSecondary
                            font.family: theme.fontUi
                            font.pixelSize: 11
                        }

                        Text {
                            text: "%LOCALAPPDATA%\\HuntOverlay"
                            color: theme.textTertiary
                            font.family: theme.fontMono
                            font.pixelSize: 11
                        }
                    }

                    FluentButton {
                        text: panelBridge.uiText("Open Data Folder")
                        onClicked: panelBridge.requestOpenDataDirFromUi()
                    }

                    FluentButton {
                        text: panelBridge.uiText("Reset to Default Config")
                        destructive: true
                        onClicked: panelBridge.requestResetConfigFromUi()
                    }
                }
            }
        }
    }
}
