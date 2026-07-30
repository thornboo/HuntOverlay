import QtQuick 2.15

QtObject {
    readonly property int sidebarWidth: 216
    readonly property int topbarHeight: 86
    readonly property int controlHeight: 36

    readonly property int radiusControl: 6
    readonly property int radiusCard: 10

    readonly property color window: "#0D151C"
    readonly property color sidebar: "#101920"
    readonly property color content: "#111A21"
    readonly property color card: "#17232C"
    readonly property color cardHover: "#1C2B36"
    readonly property color control: "#1C2A35"
    readonly property color controlHover: "#243745"
    readonly property color controlPressed: "#15232D"
    readonly property color input: "#101920"
    readonly property color inputHover: "#15212A"
    readonly property color selected: "#1D3040"

    readonly property color strokeSubtle: "#22313A"
    readonly property color stroke: "#2D414E"
    readonly property color strokeStrong: "#435A69"
    readonly property color accent: "#60CDFF"
    readonly property color accentHover: "#8CDDFF"
    readonly property color accentPressed: "#4CB4E7"
    readonly property color accentSoft: "#173446"

    readonly property color textPrimary: "#F3F3F3"
    readonly property color textSecondary: "#CFCFCF"
    readonly property color textTertiary: "#9D9D9D"
    readonly property color textDisabled: "#6D6D6D"
    readonly property color textOnAccent: "#00131A"

    readonly property color success: "#6CCB5F"
    readonly property color warning: "#F2C94C"
    readonly property color danger: "#FF6B5F"

    readonly property string fontUi: Qt.application.font.family
    readonly property string fontFallback: Qt.application.font.family
    readonly property string fontMono: Qt.application.font.family
}
