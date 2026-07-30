import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: card

    property string title: ""
    property string subtitle: ""
    property string iconKind: ""
    property bool highlighted: false
    default property alias content: body.data

    Theme { id: theme }

    radius: theme.radiusCard
    color: theme.card
    gradient: Gradient {
        GradientStop {
            position: 0.0
            color: card.highlighted ? "#1B2D38" : "#192630"
        }
        GradientStop {
            position: 1.0
            color: card.highlighted ? "#15232C" : "#142029"
        }
    }
    border.width: 1
    border.color: highlighted ? "#3A586A" : theme.stroke
    implicitHeight: layout.implicitHeight + 30

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 10
        anchors.rightMargin: 10
        height: 1
        color: "#8DCEEA"
        opacity: card.highlighted ? 0.26 : 0.13
    }

    ColumnLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 15
        spacing: 9

        RowLayout {
            Layout.fillWidth: true
            spacing: 9

            LineIcon {
                visible: card.iconKind.length > 0
                kind: card.iconKind
                color: theme.accent
                Layout.preferredWidth: 23
                Layout.preferredHeight: 23
            }

            Text {
                Layout.fillWidth: true
                text: card.title
                color: theme.textPrimary
                font.family: theme.fontUi
                font.pixelSize: 17
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
        }

        Text {
            visible: card.subtitle.length > 0
            Layout.fillWidth: true
            text: card.subtitle
            color: theme.textTertiary
            font.family: theme.fontUi
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }

        Rectangle {
            visible: card.title.length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: theme.strokeSubtle
        }

        ColumnLayout {
            id: body
            Layout.fillWidth: true
            spacing: 9
        }
    }
}
