import SwiftUI

@main
struct BraiinsRatchetApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 980, minHeight: 680)
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
                    Color(red: 0.05, green: 0.07, blue: 0.08),
                    Color(red: 0.08, green: 0.14, blue: 0.15),
                    Color(red: 0.17, green: 0.20, blue: 0.17)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 22) {
                header
                controls
                manualExposureControls
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
            Text("Braiins Ratchet")
                .font(.system(size: 44, weight: .black, design: .rounded))
                .foregroundStyle(.white)
            Text("Persistent monitor-only autoresearch cockpit")
                .font(.system(size: 18, weight: .medium, design: .rounded))
                .foregroundStyle(.white.opacity(0.72))
        }
    }

    private var controls: some View {
        HStack(spacing: 12) {
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
            HStack(spacing: 10) {
                TextField("Description, e.g. Braiins order abc 0.0001 BTC", text: $manualDescription)
                    .textFieldStyle(.plain)
                    .padding(10)
                    .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                TextField("Hours", text: $maturityHours)
                    .textFieldStyle(.plain)
                    .frame(width: 72)
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
                    .frame(width: 54)
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
                .padding(22)
        }
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 28, style: .continuous)
                .stroke(.white.opacity(0.16), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.35), radius: 28, x: 0, y: 18)
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

enum RatchetProcess {
    static func run(arguments: [String], input: String? = nil) async -> String {
        await Task.detached {
            let packageRoot = URL(fileURLWithPath: #filePath)
                .deletingLastPathComponent()
                .deletingLastPathComponent()
                .deletingLastPathComponent()
                .deletingLastPathComponent()
            let repoRoot = packageRoot
                .deletingLastPathComponent()
                .deletingLastPathComponent()
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

    private static func shellQuote(_ value: String) -> String {
        "'" + value.replacingOccurrences(of: "'", with: "'\\''") + "'"
    }
}
