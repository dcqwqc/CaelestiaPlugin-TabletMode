pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io
import qs.utils

// Rotation state/control, owned by the TabletMode runtime. The daemon remains
// authoritative so sensor, hotkey, hinge and quick-toggle changes cannot drift.
Singleton {
    id: root

    readonly property string bin: Paths.toLocalFile(Qt.resolvedUrl("../scripts/yoga-tablet"))

    property bool available: false
    property bool locked: false
    property bool tabletMode: false
    property bool tabletModeChanging: false
    property bool rotationChanging: false
    property int transform: 0
    property int degrees: 0
    property string autoRotate: "always"

    function refresh(): void {
        if (!status.running)
            status.running = true;
    }

    // Compatibility for old callers. The quick toggle itself now exposes
    // explicit Auto and Force actions instead of one ambiguous lock button.
    function toggle(): void {
        if (!toggler.running)
            toggler.running = true;
    }

    function runRotationAction(arg): void {
        if (rotationChanging)
            return;
        rotationChanging = true;
        rotationAction.command = [root.bin, "rotate", String(arg)];
        rotationAction.running = true;
    }

    function setAutomatic(): void {
        runRotationAction("auto");
    }

    function forceNext(): void {
        runRotationAction("next");
    }

    function forceTransform(value): void {
        let normalized = ((Number(value) % 4) + 4) % 4;
        runRotationAction(normalized);
    }

    function toggleTabletMode(): void {
        if (tabletModeChanging)
            return;
        tabletModeChanging = true;
        tabletToggler.command = [root.bin, "mode", root.tabletMode ? "laptop" : "tablet"];
        tabletToggler.running = true;
    }

    Process {
        id: status
        command: [root.bin, "status"]

        stdout: StdioCollector {
            onStreamFinished: {
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    root.available = false;
                    return;
                }
                if (!data || data.ok === false) {
                    root.available = false;
                    return;
                }
                root.available = true;
                root.locked = data.rotation_locked ?? root.locked;
                root.tabletMode = data.tablet_mode ?? root.tabletMode;
                root.transform = data.transform ?? root.transform;
                root.degrees = data.degrees ?? root.degrees;
                root.autoRotate = data.auto_rotate ?? root.autoRotate;
            }
        }

        onExited: code => {
            if (code !== 0)
                root.available = false;
        }
    }

    Process {
        id: toggler
        command: [root.bin, "toggle-lock"]
        onExited: code => {
            if (code === 0)
                root.refresh();
            else
                root.available = false;
        }
    }

    Process {
        id: rotationAction
        running: false
        onExited: code => {
            root.rotationChanging = false;
            if (code === 0)
                root.refresh();
            else
                root.available = false;
        }
    }

    Process {
        id: tabletToggler
        running: false
        onExited: code => {
            root.tabletModeChanging = false;
            if (code === 0)
                root.refresh();
            else
                root.available = false;
        }
    }

    Component.onCompleted: root.refresh()
}
