import QtQuick 2.15
import QtQuick.Controls.Basic 2.15

ComboBox {
    id: control

    Theme { id: theme }

    implicitHeight: theme.controlHeight
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    leftPadding: 10
    rightPadding: 34

    contentItem: Text {
        text: control.displayText
        color: control.enabled ? theme.textPrimary : theme.textDisabled
        font.family: theme.fontUi
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Text {
        x: control.width - width - 11
        y: control.height / 2 - height / 2
        width: 12
        height: 12
        text: "⌄"
        color: theme.textSecondary
        font.family: theme.fontUi
        font.pixelSize: 12
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: theme.radiusControl
        color: control.hovered ? theme.inputHover : theme.input
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? theme.accent : theme.stroke

        Rectangle {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            width: 32
            radius: theme.radiusControl
            gradient: Gradient {
                GradientStop { position: 0; color: "#213340" }
                GradientStop { position: 1; color: "#172630" }
            }

            Rectangle {
                anchors.left: parent.left
                width: 1
                height: parent.height
                color: theme.stroke
            }
        }
    }

    delegate: ItemDelegate {
        required property var modelData
        width: control.width
        height: 34
        hoverEnabled: true
        highlighted: control.highlightedIndex === index

        contentItem: Text {
            text: control.textRole && modelData
                  ? modelData[control.textRole] : String(modelData)
            color: theme.textPrimary
            font.family: theme.fontUi
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            leftPadding: 8
        }

        background: Rectangle {
            radius: 4
            color: parent.highlighted ? theme.selected
                                      : parent.hovered ? theme.controlHover
                                                       : "transparent"
        }
    }

    popup: Popup {
        y: control.height + 4
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 260)
        padding: 4

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            radius: theme.radiusControl
            color: theme.card
            border.width: 1
            border.color: theme.stroke
        }
    }
}
