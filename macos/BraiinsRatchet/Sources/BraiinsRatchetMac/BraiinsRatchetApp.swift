import AppKit
import SwiftUI

@main
struct BraiinsRatchetApp: App {
    init() {
        NSApplication.shared.applicationIconImage = AppIconFactory.makeIcon()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 1120, minHeight: 760)
        }
        .windowStyle(.hiddenTitleBar)
    }
}

struct ContentView: View {
    @State private var output = "Press Refresh Cockpit."
    @State private var isRunning = false
    @State private var manualDescription = ""
    @State private var maturityHours = "72"
    @State private var closePositionId = ""

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.02, green: 0.05, blue: 0.06),
                    Color(red: 0.04, green: 0.14, blue: 0.15),
                    Color(red: 0.20, green: 0.24, blue: 0.18)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            atmosphericShapes

            HStack(alignment: .top, spacing: 22) {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    statusDeck
                    controls
                    manualExposureControls
                }
                .frame(width: 390)

                outputPanel
            }
            .padding(30)
        }
        .task {
            await runRatchet(["next"])
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                Image(nsImage: AppIconFactory.makeIcon(size: 38))
                    .resizable()
                    .frame(width: 38, height: 38)
                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                Text("Real-money monitor")
                    .font(.system(size: 13, weight: .black, design: .rounded))
                    .foregroundStyle(.black.opacity(0.72))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color(red: 0.68, green: 0.96, blue: 0.82), in: Capsule())
            }
            Text("Braiins Ratchet")
                .font(.system(size: 44, weight: .black, design: .rounded))
                .foregroundStyle(.white)
            Text("Persistent monitor-only autoresearch cockpit")
                .font(.system(size: 18, weight: .medium, design: .rounded))
                .foregroundStyle(.white.opacity(0.72))
        }
    }

    private var atmosphericShapes: some View {
        ZStack {
            Circle()
                .fill(Color(red: 0.52, green: 0.95, blue: 0.72).opacity(0.18))
                .frame(width: 420, height: 420)
                .blur(radius: 70)
                .offset(x: -360, y: -240)
            Circle()
                .fill(Color(red: 0.95, green: 0.67, blue: 0.33).opacity(0.14))
                .frame(width: 360, height: 360)
                .blur(radius: 80)
                .offset(x: 430, y: 260)
            RoundedRectangle(cornerRadius: 80, style: .continuous)
                .stroke(.white.opacity(0.06), lineWidth: 1)
                .frame(width: 780, height: 460)
                .rotationEffect(.degrees(-12))
                .offset(x: 280, y: -130)
        }
        .ignoresSafeArea()
    }

    private var statusDeck: some View {
        VStack(spacing: 12) {
            statusCard(title: "Lifecycle", value: "Durable", detail: "SQLite-backed resume after reboot")
            statusCard(title: "Execution", value: "Manual", detail: "No owner-token order placement")
            statusCard(title: "Exposure", value: "Tracked", detail: "Record long Braiins positions")
        }
    }

    private func statusCard(title: String, value: String, detail: String) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(title.uppercased())
                    .font(.system(size: 10, weight: .black, design: .rounded))
                    .foregroundStyle(.white.opacity(0.48))
                Text(value)
                    .font(.system(size: 21, weight: .heavy, design: .rounded))
                    .foregroundStyle(.white)
                Text(detail)
                    .font(.system(size: 12, weight: .medium, design: .rounded))
                    .foregroundStyle(.white.opacity(0.62))
            }
            Spacer()
        }
        .padding(16)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(.white.opacity(0.13), lineWidth: 1)
        )
    }

    private var controls: some View {
        VStack(alignment: .leading, spacing: 10) {
            glassButton("Refresh Cockpit") {
                Task { await runRatchet(["next"]) }
            }
            glassButton("Lifecycle Status") {
                Task { await runRatchet(["supervise", "--status"]) }
            }
            glassButton("Automation Plan") {
                Task { await runRatchet(["pipeline"], input: "no\n") }
            }
            glassButton("Manual Positions") {
                Task { await runRatchet(["position", "list"]) }
            }
            glassButton("Full Report") {
                Task { await runRatchet(["report"]) }
            }
            if isRunning {
                ProgressView()
                    .controlSize(.small)
                    .padding(.leading, 8)
            }
        }
    }

    private var manualExposureControls: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Manual Braiins Exposure")
                .font(.system(size: 15, weight: .bold, design: .rounded))
                .foregroundStyle(.white.opacity(0.82))
            VStack(spacing: 10) {
                TextField("Description, e.g. Braiins order abc 0.0001 BTC", text: $manualDescription)
                    .textFieldStyle(.plain)
                    .padding(10)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                TextField("Hours", text: $maturityHours)
                    .textFieldStyle(.plain)
                    .padding(10)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                glassButton("Record Exposure") {
                    let description = manualDescription.trimmingCharacters(in: .whitespacesAndNewlines)
                    let hours = maturityHours.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !description.isEmpty else {
                        output = "Enter a manual exposure description first."
                        return
                    }
                    Task {
                        await runRatchet([
                            "position", "open",
                            "--description", description,
                            "--maturity-hours", hours.isEmpty ? "72" : hours
                        ])
                    }
                }
                TextField("ID", text: $closePositionId)
                    .textFieldStyle(.plain)
                    .padding(10)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                glassButton("Close Exposure") {
                    let positionId = closePositionId.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !positionId.isEmpty else {
                        output = "Enter a manual position ID first."
                        return
                    }
                    Task { await runRatchet(["position", "close", positionId]) }
                }
            }
        }
        .padding(16)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(.white.opacity(0.14), lineWidth: 1)
        )
    }

    private var outputPanel: some View {
        ScrollView {
            Text(output)
                .font(.system(.body, design: .monospaced))
                .foregroundStyle(.white.opacity(0.92))
                .frame(maxWidth: .infinity, alignment: .leading)
                .textSelection(.enabled)
                .padding(26)
        }
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .stroke(.white.opacity(0.16), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.35), radius: 28, x: 0, y: 18)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func glassButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 14, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
        }
        .buttonStyle(.plain)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.thinMaterial, in: Capsule())
        .overlay(Capsule().stroke(.white.opacity(0.18), lineWidth: 1))
        .disabled(isRunning)
    }

    @MainActor
    private func runRatchet(_ arguments: [String], input: String? = nil) async {
        isRunning = true
        output = "Running ./scripts/ratchet \(arguments.joined(separator: " ")) ..."
        let result = await RatchetProcess.run(arguments: arguments, input: input)
        output = result
        isRunning = false
    }
}

enum AppIconFactory {
    static func makeIcon(size: CGFloat = 512) -> NSImage {
        let image = NSImage(size: NSSize(width: size, height: size))
        image.lockFocus()

        let rect = NSRect(x: 0, y: 0, width: size, height: size)
        let corner = size * 0.22
        let path = NSBezierPath(roundedRect: rect.insetBy(dx: size * 0.04, dy: size * 0.04), xRadius: corner, yRadius: corner)
        NSGradient(
            colors: [
                NSColor(red: 0.03, green: 0.09, blue: 0.10, alpha: 1),
                NSColor(red: 0.04, green: 0.27, blue: 0.26, alpha: 1),
                NSColor(red: 0.55, green: 0.86, blue: 0.50, alpha: 1)
            ]
        )?.draw(in: path, angle: -35)

        NSColor.white.withAlphaComponent(0.18).setStroke()
        path.lineWidth = size * 0.012
        path.stroke()

        let ringRect = rect.insetBy(dx: size * 0.18, dy: size * 0.18)
        let ring = NSBezierPath(ovalIn: ringRect)
        NSColor(red: 0.73, green: 1.0, blue: 0.78, alpha: 0.26).setFill()
        ring.fill()

        let inner = NSBezierPath(ovalIn: rect.insetBy(dx: size * 0.27, dy: size * 0.27))
        NSColor(red: 0.02, green: 0.07, blue: 0.08, alpha: 0.85).setFill()
        inner.fill()

        let pick = NSBezierPath()
        pick.move(to: NSPoint(x: size * 0.30, y: size * 0.30))
        pick.line(to: NSPoint(x: size * 0.68, y: size * 0.70))
        pick.line(to: NSPoint(x: size * 0.76, y: size * 0.62))
        pick.line(to: NSPoint(x: size * 0.38, y: size * 0.22))
        pick.close()
        NSColor(red: 1.0, green: 0.77, blue: 0.35, alpha: 0.98).setFill()
        pick.fill()

        let spark = NSBezierPath()
        spark.move(to: NSPoint(x: size * 0.55, y: size * 0.28))
        spark.line(to: NSPoint(x: size * 0.62, y: size * 0.42))
        spark.line(to: NSPoint(x: size * 0.76, y: size * 0.48))
        spark.line(to: NSPoint(x: size * 0.62, y: size * 0.54))
        spark.line(to: NSPoint(x: size * 0.55, y: size * 0.68))
        spark.line(to: NSPoint(x: size * 0.48, y: size * 0.54))
        spark.line(to: NSPoint(x: size * 0.34, y: size * 0.48))
        spark.line(to: NSPoint(x: size * 0.48, y: size * 0.42))
        spark.close()
        NSColor(red: 0.76, green: 1.0, blue: 0.74, alpha: 0.95).setFill()
        spark.fill()

        image.unlockFocus()
        return image
    }
}

enum RatchetProcess {
    static func run(arguments: [String], input: String? = nil) async -> String {
        await Task.detached {
            guard let repoRoot = findRepoRoot() else {
                return """
                Braiins Ratchet cannot find its repository.

                Expected to find:
                  scripts/ratchet

                Start the packaged app through:
                  ./scripts/ratchet app

                Or open this bundle from inside the BraiinsRatchet repository:
                  macos/build/Braiins Ratchet.app
                """
            }

            let script = repoRoot.appendingPathComponent("scripts/ratchet").path

            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/bin/zsh")
            process.arguments = ["-lc", ([script] + arguments).map(shellQuote).joined(separator: " ")]
            process.currentDirectoryURL = repoRoot

            let outputPipe = Pipe()
            let inputPipe = Pipe()
            process.standardOutput = outputPipe
            process.standardError = outputPipe
            process.standardInput = inputPipe

            do {
                try process.run()
                if let input {
                    inputPipe.fileHandleForWriting.write(Data(input.utf8))
                }
                inputPipe.fileHandleForWriting.closeFile()
                process.waitUntilExit()
                let data = outputPipe.fileHandleForReading.readDataToEndOfFile()
                let text = String(data: data, encoding: .utf8) ?? ""
                return text.isEmpty ? "Command finished with no output." : text
            } catch {
                return "Failed to run ratchet command: \(error.localizedDescription)"
            }
        }.value
    }

    private static func findRepoRoot() -> URL? {
        let fileManager = FileManager.default
        let candidates = [
            URL(fileURLWithPath: #filePath),
            Bundle.main.bundleURL,
            URL(fileURLWithPath: fileManager.currentDirectoryPath)
        ]

        for candidate in candidates {
            var current = candidate.hasDirectoryPath ? candidate : candidate.deletingLastPathComponent()
            for _ in 0..<16 {
                let script = current.appendingPathComponent("scripts/ratchet").path
                if fileManager.isExecutableFile(atPath: script) {
                    return current
                }

                let parent = current.deletingLastPathComponent()
                if parent.path == current.path {
                    break
                }
                current = parent
            }
        }

        return nil
    }

    private static func shellQuote(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: "'\\''") + "'"
    }
}
