import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    objectName: "controlCenterRoot"

    property int currentPage: 0
    readonly property int pageCount: 4
    readonly property var pageTitles: [
        panelBridge.uiText("Map & Tools"),
        panelBridge.uiText("Official POIs"),
        panelBridge.uiText("Boss Reference"),
        panelBridge.uiText("Settings")
    ]
    readonly property var pageDescriptions: [
        panelBridge.uiText("Map controls, custom POIs and measurement."),
        panelBridge.uiText(
            "Visibility and marker colors for official data."
        ),
        panelBridge.uiText("Combat resistances and practical notes."),
        panelBridge.uiText(
            "Keybinds, overlay behavior and application recovery."
        )
    ]

    function selectPage(index) {
        if (index >= 0 && index < pageCount)
            currentPage = index
    }

    Theme { id: theme }

    color: theme.window

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: Math.max(
                196, Math.min(theme.sidebarWidth, root.width * 0.26)
            )
            Layout.fillHeight: true
            color: theme.sidebar
            gradient: Gradient {
                GradientStop { position: 0; color: "#111D26" }
                GradientStop { position: 1; color: "#0C151C" }
            }

            Rectangle {
                anchors.right: parent.right
                width: 1
                height: parent.height
                color: theme.strokeSubtle
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 13
                anchors.rightMargin: 13
                anchors.topMargin: 20
                anchors.bottomMargin: 16
                spacing: 7

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Item {
                        Layout.preferredWidth: 31
                        Layout.preferredHeight: 31

                        Repeater {
                            model: 3

                            delegate: Rectangle {
                                required property int index
                                x: 2 + index * 4
                                y: 3 + index * 7
                                width: 22
                                height: 7
                                radius: 2
                                color: Qt.lighter(
                                    theme.accent, 1.12 - index * 0.08
                                )
                                rotation: -8
                            }
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "HuntOverlay"
                        color: theme.textPrimary
                        font.family: theme.fontUi
                        font.pixelSize: 21
                        font.weight: Font.DemiBold
                    }
                }

                Text {
                    text: panelBridge.uiText("Control Center")
                    color: theme.textTertiary
                    font.family: theme.fontUi
                    font.pixelSize: 12
                }

                Item { Layout.preferredHeight: 9 }

                NavItem {
                    Layout.fillWidth: true
                    text: root.pageTitles[0]
                    iconKind: "map"
                    selected: root.currentPage === 0
                    onClicked: root.selectPage(0)
                }

                NavItem {
                    Layout.fillWidth: true
                    text: root.pageTitles[1]
                    iconKind: "poi"
                    selected: root.currentPage === 1
                    onClicked: root.selectPage(1)
                }

                NavItem {
                    Layout.fillWidth: true
                    text: root.pageTitles[2]
                    iconKind: "boss"
                    selected: root.currentPage === 2
                    onClicked: root.selectPage(2)
                }

                NavItem {
                    Layout.fillWidth: true
                    text: root.pageTitles[3]
                    iconKind: "settings"
                    selected: root.currentPage === 3
                    onClicked: root.selectPage(3)
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 118
                    radius: theme.radiusCard
                    gradient: Gradient {
                        GradientStop { position: 0; color: "#192833" }
                        GradientStop { position: 1; color: "#142029" }
                    }
                    border.width: 1
                    border.color: theme.stroke

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 7

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 7

                            Rectangle {
                                Layout.preferredWidth: 8
                                Layout.preferredHeight: 8
                                radius: 4
                                color: theme.success
                            }

                            Text {
                                Layout.fillWidth: true
                                text: panelBridge.uiText("Data Status")
                                color: theme.textPrimary
                                font.family: theme.fontUi
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: panelBridge.statusText
                            color: theme.textTertiary
                            font.family: theme.fontUi
                            font.pixelSize: 10
                            elide: Text.ElideRight
                        }

                        FluentButton {
                            objectName: "refreshButton"
                            Layout.fillWidth: true
                            text: panelBridge.uiText("Refresh Data")
                            compact: true
                            enabled: panelBridge.forceRefreshEnabled
                            onClicked: panelBridge.requestForceRefreshFromUi()
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: theme.content
            gradient: Gradient {
                GradientStop { position: 0; color: "#14212A" }
                GradientStop { position: 1; color: "#0E171E" }
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: theme.topbarHeight
                    Layout.leftMargin: 18
                    Layout.rightMargin: 18
                    Layout.topMargin: 16
                    radius: theme.radiusCard
                    gradient: Gradient {
                        GradientStop { position: 0; color: "#1A2A35" }
                        GradientStop { position: 1; color: "#14212A" }
                    }
                    border.width: 1
                    border.color: theme.stroke

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 18
                        anchors.rightMargin: 18
                        spacing: 12

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                Layout.fillWidth: true
                                text: root.pageTitles[root.currentPage]
                                color: theme.textPrimary
                                font.family: theme.fontUi
                                font.pixelSize: 23
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: root.pageDescriptions[root.currentPage]
                                color: theme.textTertiary
                                font.family: theme.fontUi
                            font.pixelSize: 12
                                elide: Text.ElideRight
                            }
                        }

                        RowLayout {
                            visible: root.width >= 900
                            spacing: 7

                            Rectangle {
                                Layout.preferredWidth: 8
                                Layout.preferredHeight: 8
                                radius: 4
                                color: theme.success
                            }

                            Text {
                                text: panelBridge.statusText
                                color: theme.textSecondary
                                font.family: theme.fontUi
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }
                        }

                        Text {
                            text: "v" + panelBridge.configVersion
                            color: theme.textTertiary
                            font.family: theme.fontMono
                            font.pixelSize: 10
                        }

                        Rectangle {
                            Layout.preferredHeight: 36
                            Layout.preferredWidth: mapBadge.implicitWidth + 22
                            radius: theme.radiusControl
                            gradient: Gradient {
                                GradientStop {
                                    position: 0
                                    color: "#223746"
                                }
                                GradientStop {
                                    position: 1
                                    color: "#182A35"
                                }
                            }
                            border.width: 1
                            border.color: theme.stroke

                            Text {
                                id: mapBadge
                                anchors.centerIn: parent
                                text: panelBridge.currentMapLabel
                                color: theme.accent
                                font.family: theme.fontUi
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                            }
                        }

                    }
                }

                StackLayout {
                    id: pageStack
                    objectName: "pageStack"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 18
                    Layout.rightMargin: 18
                    Layout.topMargin: 14
                    Layout.bottomMargin: 18
                    currentIndex: root.currentPage

                    MapToolsPage { }
                    OfficialPoisPage { }
                    BossReferencePage { }
                    SettingsPage { }
                }
            }
        }
    }
}
