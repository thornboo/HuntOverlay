import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

Switch {
    id: control

    Theme { id: theme }

    implicitHeight: 30
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    spacing: 10

    indicator: Rectangle {
        implicitWidth: 40
        implicitHeight: 20
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        radius: height / 2
        color: control.checked ? theme.accent : "#424242"
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? theme.accentHover
                                                 : control.checked
                                                   ? theme.accent : "#666666"

        Rectangle {
            width: 16
            height: 16
            radius: 8
            y: 2
            x: control.checked ? parent.width - width - 2 : 2
            color: control.checked ? theme.textOnAccent : theme.textPrimary

            Behavior on x {
                NumberAnimation {
                    duration: 120
                    easing.type: Easing.OutCubic
                }
            }
        }
    }

    contentItem: Text {
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        color: control.enabled ? theme.textSecondary : theme.textDisabled
        font.family: theme.fontUi
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.WordWrap
    }
}
