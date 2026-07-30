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
        contentHeight: Math.max(height, content.implicitHeight)
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

        ColumnLayout {
            id: content
            width: parent.width - 12
            spacing: 10

            GridLayout {
                Layout.fillWidth: true
                columns: width >= 680 ? 2 : 1
                columnSpacing: 10
                rowSpacing: 10

                Repeater {
                    model: panelBridge.bossItems

                    delegate: FluentCard {
                        required property var modelData

                        Layout.fillWidth: true
                        Layout.preferredHeight: 208
                        title: modelData.name
                        iconKind: "boss"

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                radius: theme.radiusControl
                                color: theme.input
                                border.width: 1
                                border.color: theme.strokeSubtle

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 9
                                    anchors.rightMargin: 9

                                    Text {
                                        text: panelBridge.uiText("Fire")
                                        color: theme.textTertiary
                                        font.family: theme.fontUi
                                        font.pixelSize: 11
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        text: modelData.fireLabel
                                        color: modelData.fireColor
                                        font.family: theme.fontUi
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                radius: theme.radiusControl
                                color: theme.input
                                border.width: 1
                                border.color: theme.strokeSubtle

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 9
                                    anchors.rightMargin: 9

                                    Text {
                                        text: panelBridge.uiText("Poison")
                                        color: theme.textTertiary
                                        font.family: theme.fontUi
                                        font.pixelSize: 11
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        text: modelData.poisonLabel
                                        color: modelData.poisonColor
                                        font.family: theme.fontUi
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                    }
                                }
                            }
                        }

                        Repeater {
                            model: modelData.tips

                            delegate: Text {
                                required property string modelData

                                Layout.fillWidth: true
                                text: "•  " + modelData
                                color: theme.textSecondary
                                font.family: theme.fontUi
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }

                        Item { Layout.fillHeight: true }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: panelBridge.uiText(
                    "Banish time and exact HP vary by patch and are omitted."
                )
                color: theme.textTertiary
                font.family: theme.fontUi
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }
        }
    }
}
