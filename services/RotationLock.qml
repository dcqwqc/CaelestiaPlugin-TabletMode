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
    property bool keyboardOverride: false
    property bool keyboardOverrideChanging: false
    property bool rotationChanging: false
    property int transform: 0
    property int degrees: 0
    property string autoRotate: "always"
    property bool autoRotationActive: false

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

    function holdCurrent(): void {
        if (rotationChanging)
            return;
        rotationChanging = true;
        rotationAction.command = [root.bin, "lock"];
        rotationAction.running = true;
    }

    function toggleAutomatic(): void {
        if (root.locked)
            setAutomatic();
        else
            holdCurrent();
    }

    function forceNext(): void {
        runRotationAction("next");
    }

    function forceTransform(value): void {
        let normalized = ((Number(value) % 4) + 4) % 4;
        runRotationAction(normalized);
    }

    function toggleKeyboardOverride(): void {
        if (keyboardOverrideChanging)
            return;
        keyboardOverrideChanging = true;
        keyboardToggler.command = [root.bin, "keyboard-override", root.keyboardOverride ? "off" : "on"];
        keyboardToggler.running = true;
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
                root.keyboardOverride = data.keyboard_override ?? root.keyboardOverride;
                root.transform = data.transform ?? root.transform;
                root.degrees = data.degrees ?? root.degrees;
                root.autoRotate = data.auto_rotate ?? root.autoRotate;
                root.autoRotationActive = data.auto_rotation_active ?? root.autoRotationActive;
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
        id: keyboardToggler
        running: false
        onExited: code => {
            root.keyboardOverrideChanging = false;
            if (code === 0)
                root.refresh();
            else
                root.available = false;
        }
    }

    Component.onCompleted: root.refresh()
}
