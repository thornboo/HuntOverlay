import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

Button {
    id: control

    property bool selected: false
    property string iconKind: "map"

    Theme { id: theme }

    implicitHeight: 48
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    contentItem: Row {
        spacing: 12

        Item {
            width: 15
            height: 1
        }

        LineIcon {
            anchors.verticalCenter: parent.verticalCenter
            width: 22
            height: 22
            kind: control.iconKind
            color: control.selected ? theme.accent : theme.textSecondary
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            color: control.selected ? theme.textPrimary : theme.textSecondary
            font.family: theme.fontUi
            font.pixelSize: 14
            font.weight: control.selected ? Font.DemiBold : Font.Normal
        }
    }

    background: Rectangle {
        radius: 6
        color: "transparent"
        gradient: Gradient {
            GradientStop {
                position: 0
                color: control.selected ? "#20394A"
                                        : control.hovered
                                          ? "#1A2B36" : "transparent"
            }
            GradientStop {
                position: 1
                color: control.selected ? "#182B37"
                                        : control.hovered
                                          ? "#16232C" : "transparent"
            }
        }
        border.width: control.activeFocus || control.selected ? 1 : 0
        border.color: control.activeFocus ? theme.accent : theme.stroke

        Rectangle {
            visible: control.selected
            anchors.left: parent.left
            anchors.leftMargin: 1
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: 20
            radius: 2
            color: theme.accent
        }
    }
}
