import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

CheckBox {
    id: control

    Theme { id: theme }

    implicitHeight: 30
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    spacing: 10

    indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: 20
        x: control.leftPadding
        y: parent.height / 2 - height / 2
        radius: 4
        color: control.checked ? theme.accent : theme.input
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? theme.accentHover
                                         : control.checked
                                           ? theme.accent : theme.strokeStrong

        Text {
            anchors.centerIn: parent
            visible: control.checked
            text: "✓"
            color: theme.textOnAccent
            font.family: theme.fontUi
            font.pixelSize: 14
            font.weight: Font.Bold
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
