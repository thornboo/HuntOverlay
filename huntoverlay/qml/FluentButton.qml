import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

Button {
    id: control

    property bool primary: false
    property bool destructive: false
    property bool compact: false

    Theme { id: theme }

    implicitHeight: compact ? 30 : theme.controlHeight
    implicitWidth: Math.max(76, contentItem.implicitWidth + 28)
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus

    contentItem: Text {
        text: control.text
        color: {
            if (!control.enabled) return theme.textDisabled
            if (control.primary) return theme.textPrimary
            if (control.destructive && control.hovered) return "#FFB4AB"
            return theme.textPrimary
        }
        font.family: theme.fontUi
        font.pixelSize: 12
        font.weight: control.primary ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: theme.radiusControl
        color: {
            if (!control.enabled) return "#252525"
            if (control.down) {
                return control.primary ? "#1A3342" : theme.controlPressed
            }
            if (control.hovered) {
                return control.primary ? "#203B4A" : theme.controlHover
            }
            return control.primary ? "#192F3B" : "#17252E"
        }
        border.width: control.activeFocus ? 2 : 1
        border.color: {
            if (control.activeFocus) return theme.accent
            if (control.destructive && control.hovered) return theme.danger
            if (control.primary) return "#355363"
            if (control.hovered) return theme.strokeStrong
            return theme.stroke
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            height: 1
            color: "#A8DAF0"
            opacity: control.enabled ? 0.18 : 0
        }

        Behavior on color {
            ColorAnimation { duration: 100 }
        }
    }
}
