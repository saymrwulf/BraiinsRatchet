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
