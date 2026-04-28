import AppKit
import Foundation
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
    @State private var selectedSection: AppSection? = .mission
    @State private var appState: AppStatePayload?
    @State private var transcript = "Loading native app state..."
    @State private var lastCommand = "app-state"
    @State private var errorMessage: String?
    @State private var isRunning = false
    @State private var glow = false
    @State private var manualDescription = ""
    @State private var maturityHours = "72"
    @State private var closePositionId = ""

    var body: some View {
        NavigationSplitView {
            List(AppSection.allCases, selection: $selectedSection) { section in
                Label(section.title, systemImage: section.systemImage)
                    .tag(section as AppSection?)
                    .padding(.vertical, 4)
            }
            .navigationTitle("Ratchet")
            .safeAreaInset(edge: .bottom) {
                sidebarFooter
            }
        } detail: {
            ZStack {
                AppBackground(glow: glow)
                detailView
            }
            .toolbar {
                ToolbarItemGroup {
                    Button {
                        Task { await refreshAppState() }
                    } label: {
                        Label("Refresh", systemImage: "arrow.clockwise")
                    }
                    .disabled(isRunning)

                    Button {
                        Task { await runTextCommand(label: "supervise --status", ["supervise", "--status"]) }
                    } label: {
                        Label("Supervisor", systemImage: "waveform.path.ecg")
                    }
                    .disabled(isRunning)
                }
            }
        }
        .task {
            await refreshAppState()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 3.2).repeatForever(autoreverses: true)) {
                glow = true
            }
        }
    }

    @ViewBuilder
    private var detailView: some View {
        switch selectedSection ?? .mission {
        case .mission:
            MissionControlView(
                appState: appState,
                transcript: transcript,
                isRunning: isRunning,
                glow: glow,
                refresh: { Task { await refreshAppState() } },
                runPassiveAction: runPassiveAction
            )
        case .map:
            ResearchMapView(appState: appState, glow: glow)
        case .exposure:
            ManualExposureView(
                appState: appState,
                manualDescription: $manualDescription,
                maturityHours: $maturityHours,
                closePositionId: $closePositionId,
                isRunning: isRunning,
                record: recordManualExposure,
                close: closeManualExposure,
                list: { Task { await runTextCommand(label: "position list", ["position", "list"], refreshAfterwards: true) } }
            )
        case .reports:
            ReportsView(
                transcript: transcript,
                lastCommand: lastCommand,
                isRunning: isRunning,
                loadReport: { Task { await runTextCommand(label: "report", ["report"]) } },
                loadLedger: { Task { await runTextCommand(label: "experiments", ["experiments"]) } },
                loadCockpit: { Task { await runTextCommand(label: "next", ["next"]) } }
            )
        case .lecture:
            RatchetLectureView()
        }
    }

    private var sidebarFooter: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Image(nsImage: AppIconFactory.makeIcon(size: 34))
                    .resizable()
                    .frame(width: 34, height: 34)
                    .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Monitor-only")
                        .font(.caption.weight(.bold))
                    Text("No owner-token execution")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            if isRunning {
                ProgressView("Working")
                    .controlSize(.small)
            }
        }
        .padding(12)
    }

    @MainActor
    private func refreshAppState() async {
        isRunning = true
        errorMessage = nil
        lastCommand = "app-state"
        let result = await RatchetProcess.loadAppState()
        switch result {
        case .success(let payload):
            appState = payload
            transcript = payload.cockpit
        case .failure(let message):
            errorMessage = message
            transcript = message
        }
        isRunning = false
    }

    @MainActor
    private func runTextCommand(
        label: String,
        _ arguments: [String],
        input: String? = nil,
        refreshAfterwards: Bool = false
    ) async {
        isRunning = true
        lastCommand = label
        transcript = "Running ./scripts/ratchet \(arguments.joined(separator: " ")) ..."
        let result = await RatchetProcess.run(arguments: arguments, input: input)
        transcript = result
        isRunning = false
        if refreshAfterwards {
            await refreshAppState()
        }
    }

    private func recordManualExposure() {
        let description = manualDescription.trimmingCharacters(in: .whitespacesAndNewlines)
        let hours = maturityHours.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !description.isEmpty else {
            transcript = "Enter a manual exposure description first."
            return
        }

        Task {
            await runTextCommand(
                label: "position open",
                ["position", "open", "--description", description, "--maturity-hours", hours.isEmpty ? "72" : hours],
                refreshAfterwards: true
            )
        }
    }

    private func closeManualExposure() {
        let positionId = closePositionId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !positionId.isEmpty else {
            transcript = "Enter a manual position ID first."
            return
        }

        Task {
            await runTextCommand(label: "position close", ["position", "close", positionId], refreshAfterwards: true)
        }
    }

    private func runPassiveAction() {
        guard let plan = appState?.automationPlan else {
            Task { await refreshAppState() }
            return
        }

        switch plan.kind {
        case "once_now":
            Task { await runTextCommand(label: "once", ["once"], refreshAfterwards: true) }
        case "watch_2h":
            Task { await runTextCommand(label: "watch 2", ["watch", "2"], refreshAfterwards: true) }
        case "wait_then_once" where plan.waitSeconds <= 0:
            Task { await runTextCommand(label: "once", ["once"], refreshAfterwards: true) }
        case "report_only":
            Task { await runTextCommand(label: "report", ["report"]) }
        default:
            Task { await refreshAppState() }
        }
    }
}

enum AppSection: String, CaseIterable, Identifiable {
    case mission
    case map
    case exposure
    case reports
    case lecture

    var id: String { rawValue }

    var title: String {
        switch self {
        case .mission: "Mission Control"
        case .map: "Research Map"
        case .exposure: "Manual Exposure"
        case .reports: "Reports"
        case .lecture: "Ratchet Lecture"
        }
    }

    var systemImage: String {
        switch self {
        case .mission: "scope"
        case .map: "point.3.connected.trianglepath.dotted"
        case .exposure: "lock.shield"
        case .reports: "doc.text.magnifyingglass"
        case .lecture: "graduationcap"
        }
    }
}

struct MissionControlView: View {
    let appState: AppStatePayload?
    let transcript: String
    let isRunning: Bool
    let glow: Bool
    let refresh: () -> Void
    let runPassiveAction: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack(alignment: .top, spacing: 22) {
                    HeroPanel(appState: appState, glow: glow)
                        .frame(minWidth: 420)

                    VStack(spacing: 14) {
                        AutoresearchOrb(phase: ResearchPhase.from(appState), glow: glow)
                            .frame(height: 250)
                        PassiveRunCard(
                            plan: appState?.automationPlan,
                            isRunning: isRunning,
                            run: runPassiveAction
                        )
                    }
                    .frame(width: 350)
                }

                MetricsDeck(appState: appState)
                ResearchTimeline(appState: appState, compact: false)
                PlainEnglishCard(appState: appState, transcript: transcript)
            }
            .padding(28)
        }
    }
}

struct HeroPanel: View {
    let appState: AppStatePayload?
    let glow: Bool

    private var directive: Directive {
        Directive.from(appState)
    }

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 22) {
                HStack(spacing: 12) {
                    Image(nsImage: AppIconFactory.makeIcon(size: 46))
                        .resizable()
                        .frame(width: 46, height: 46)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    VStack(alignment: .leading, spacing: 3) {
                        Text("Braiins Ratchet")
                            .font(.largeTitle.weight(.black))
                        Text("Autoresearch control room for real-money mining experiments")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                }

                VStack(alignment: .leading, spacing: 10) {
                    Text("Do This Now")
                        .font(.caption.weight(.heavy))
                        .textCase(.uppercase)
                        .foregroundStyle(.secondary)
                    Text(directive.title)
                        .font(.system(size: 44, weight: .black, design: .rounded))
                        .foregroundStyle(directive.color)
                    Text(directive.detail)
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(.primary)

                    if let command = directive.command {
                        HStack(spacing: 10) {
                            Image(systemName: "terminal")
                            Text(command)
                                .font(.system(.body, design: .monospaced).weight(.semibold))
                        }
                        .padding(12)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(.black.opacity(0.18), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    }
                }

                if let watch = appState?.operatorState.completedWatch {
                    CooldownGauge(watch: watch)
                }

                SafetyStrip()
            }
        }
    }
}

struct PassiveRunCard: View {
    let plan: AutomationPlanPayload?
    let isRunning: Bool
    let run: () -> Void

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 14) {
                Label("Watch-only Control", systemImage: "binoculars")
                    .font(.headline)
                Text(title)
                    .font(.title3.weight(.bold))
                Text(detail)
                    .font(.callout)
                    .foregroundStyle(.secondary)

                Button(buttonTitle) {
                    run()
                }
                .buttonStyle(.borderedProminent)
                .disabled(!canRun || isRunning)

                VStack(alignment: .leading, spacing: 6) {
                    Label("No owner-token order placement", systemImage: "lock")
                    Label("Manual Braiins actions stay outside the app", systemImage: "hand.point.up.left")
                    Label("Watch runs only collect public/OCEAN data", systemImage: "antenna.radiowaves.left.and.right")
                }
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            }
        }
    }

    private var title: String {
        guard let plan else { return "Load state" }
        switch plan.kind {
        case "once_now": return "Refresh one sample"
        case "watch_2h": return "Start passive 2-hour watch"
        case "wait_then_once": return plan.waitSeconds > 0 ? "Cooldown in progress" : "Cooldown complete"
        case "report_only": return "Read report"
        case "external_wait": return "Existing watch owns control"
        case "manual_exposure_hold": return "Manual exposure hold"
        default: return "No passive action"
        }
    }

    private var detail: String {
        guard let plan else { return "The app is reading the lifecycle state." }
        switch plan.kind {
        case "once_now":
            return "This collects exactly one fresh monitor sample, then stops."
        case "watch_2h":
            return "This starts one bounded watch-only run. It does not spend BTC or place Braiins orders."
        case "wait_then_once":
            if plan.waitSeconds > 0 {
                return "The previous watch is still maturing. Do not run another identical watch yet."
            }
            return "The cooldown has ended; one fresh sample is now useful."
        case "report_only":
            return "The next useful step is reading the full report."
        case "external_wait":
            return "A watch is already running elsewhere. Starting another one would create duplicate state."
        case "manual_exposure_hold":
            return "A real manual position is active. The app should supervise, not create new experiments."
        default:
            return "No watch-only action is useful right now."
        }
    }

    private var buttonTitle: String {
        guard let plan else { return "Refresh State" }
        switch plan.kind {
        case "once_now": return "Refresh Now"
        case "watch_2h": return "Start Watch-only Run"
        case "wait_then_once": return plan.waitSeconds > 0 ? "Wait" : "Refresh Now"
        case "report_only": return "Open Report"
        default: return "Refresh State"
        }
    }

    private var canRun: Bool {
        guard let plan else { return true }
        switch plan.kind {
        case "once_now", "watch_2h", "report_only":
            return true
        case "wait_then_once":
            return plan.waitSeconds <= 0
        default:
            return false
        }
    }
}

struct MetricsDeck: View {
    let appState: AppStatePayload?

    var body: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 14), count: 4), spacing: 14) {
            MetricTile(
                title: "Market Freshness",
                value: freshnessText,
                detail: appState?.operatorState.latestMarketTimestamp ?? "no sample",
                symbol: "clock"
            )
            MetricTile(
                title: "Strategy Action",
                value: appState?.operatorState.action ?? "none",
                detail: actionDetail,
                symbol: "target"
            )
            MetricTile(
                title: "Manual Exposure",
                value: exposureText,
                detail: "Blocks new experiments while active",
                symbol: "shield.lefthalf.filled"
            )
            MetricTile(
                title: "Latest Report",
                value: appState?.operatorState.latestReport?.lastPathComponent ?? "none",
                detail: appState?.operatorState.latestReport ?? "No artifact yet",
                symbol: "doc.text"
            )
        }
    }

    private var freshnessText: String {
        guard let state = appState?.operatorState else { return "loading" }
        if state.isFresh { return "fresh" }
        if let minutes = state.freshnessMinutes { return "stale \(minutes)m" }
        return "unknown"
    }

    private var actionDetail: String {
        guard let action = appState?.operatorState.action else { return "No proposal loaded" }
        if action == "manual_canary" { return "Learning opportunity, not profit proof" }
        if action == "manual_bid" { return "Profit-seeking signal; manual review required" }
        return "No useful market action"
    }

    private var exposureText: String {
        let count = appState?.operatorState.activeManualPositions.count ?? 0
        return count == 0 ? "none" : "\(count) active"
    }
}

struct MetricTile: View {
    let title: String
    let value: String
    let detail: String
    let symbol: String

    var body: some View {
        GlassPanel(padding: 16) {
            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: symbol)
                    .font(.title2)
                    .foregroundStyle(.green)
                Text(title)
                    .font(.caption.weight(.heavy))
                    .textCase(.uppercase)
                    .foregroundStyle(.secondary)
                Text(value)
                    .font(.title2.weight(.black))
                    .lineLimit(1)
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

struct ResearchTimeline: View {
    let appState: AppStatePayload?
    let compact: Bool

    private let steps = ResearchStep.allCases

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Label("Ratchet Pathway", systemImage: "arrow.triangle.2.circlepath")
                        .font(.headline)
                    Spacer()
                    Text("One knob at a time")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.secondary)
                }

                HStack(spacing: 0) {
                    ForEach(Array(steps.enumerated()), id: \.element.id) { index, step in
                        TimelineNode(step: step, state: state(for: index))
                        if index < steps.count - 1 {
                            Rectangle()
                                .fill(index < activeIndex ? Color.green.opacity(0.75) : Color.secondary.opacity(0.24))
                                .frame(height: 3)
                        }
                    }
                }

                if !compact {
                    Text(explanation)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var activeIndex: Int {
        ResearchPhase.from(appState).timelineIndex
    }

    private func state(for index: Int) -> TimelineNode.StateKind {
        if index < activeIndex { return .done }
        if index == activeIndex { return .active }
        return .future
    }

    private var explanation: String {
        switch ResearchPhase.from(appState) {
        case .setup: "The system needs baseline data before it can reason. First goal: establish a trustworthy local state."
        case .refresh: "The market sample is stale. The next useful move is one fresh sample, not another watch loop."
        case .watch: "A bounded watch buys information. It measures price action without forcing a real-money bid."
        case .cooldown: "The previous watch is evidence. Cooldown prevents loop-chasing and gives the result time to mature."
        case .exposure: "Manual Braiins exposure is active. The system should supervise, not create competing experiments."
        case .adapt: "Only after repeated mature evidence should one strategy knob change. This is the anti-chaos rule."
        }
    }
}

struct TimelineNode: View {
    enum StateKind {
        case done
        case active
        case future
    }

    let step: ResearchStep
    let state: StateKind

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(fill)
                    .frame(width: 44, height: 44)
                Image(systemName: step.systemImage)
                    .foregroundStyle(.white)
                    .font(.headline)
            }
            Text(step.title)
                .font(.caption.weight(.bold))
                .foregroundStyle(state == .future ? .secondary : .primary)
                .frame(width: 86)
        }
    }

    private var fill: Color {
        switch state {
        case .done: .green.opacity(0.82)
        case .active: .orange.opacity(0.92)
        case .future: .secondary.opacity(0.25)
        }
    }
}

struct PlainEnglishCard: View {
    let appState: AppStatePayload?
    let transcript: String

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 12) {
                Label("Noob Translation", systemImage: "quote.bubble")
                    .font(.headline)
                Text(summary)
                    .font(.title3.weight(.semibold))
                Text("This app separates observation from execution. It can tell you what the research engine currently thinks; it cannot secretly spend BTC.")
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var summary: String {
        let directive = Directive.from(appState)
        if let watch = appState?.operatorState.completedWatch {
            return "You are in cooldown. The earliest useful next action is \(watch.earliestActionLocal), about \(watch.remainingMinutes) minutes from the last refresh."
        }
        return "\(directive.title): \(directive.detail)"
    }
}

struct ResearchMapView: View {
    let appState: AppStatePayload?
    let glow: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                HStack(alignment: .center, spacing: 24) {
                    AutoresearchOrb(phase: ResearchPhase.from(appState), glow: glow)
                        .frame(width: 320, height: 320)
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Autoresearch Is A Ratchet")
                            .font(.system(size: 38, weight: .black, design: .rounded))
                        Text("A ratchet is a one-way learning machine: it allows progress when evidence matures, and blocks fake progress when you are just repeating the same loop.")
                            .font(.title3)
                            .foregroundStyle(.secondary)
                    }
                }

                ResearchTimeline(appState: appState, compact: false)
                HypothesisBoard(appState: appState)
            }
            .padding(28)
        }
    }
}

struct HypothesisBoard: View {
    let appState: AppStatePayload?

    var body: some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
            PrincipleCard(
                title: "Current Hypothesis",
                symbol: "lightbulb",
                text: appState?.automationPlan.title ?? "Load state first."
            )
            PrincipleCard(
                title: "Evidence Artifact",
                symbol: "archivebox",
                text: appState?.operatorState.latestReport ?? "No report exists yet."
            )
            PrincipleCard(
                title: "Allowed Intervention",
                symbol: "slider.horizontal.3",
                text: "Change exactly one knob only after mature reports repeat the same pattern."
            )
            PrincipleCard(
                title: "Blocked Failure Mode",
                symbol: "hand.raised",
                text: "No loop-chasing. No untracked manual exposure. No automated Braiins owner-token execution."
            )
        }
    }
}

struct PrincipleCard: View {
    let title: String
    let symbol: String
    let text: String

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 12) {
                Label(title, systemImage: symbol)
                    .font(.headline)
                Text(text)
                    .font(.body)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

struct ManualExposureView: View {
    let appState: AppStatePayload?
    @Binding var manualDescription: String
    @Binding var maturityHours: String
    @Binding var closePositionId: String
    let isRunning: Bool
    let record: () -> Void
    let close: () -> Void
    let list: () -> Void

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                Text("Manual Exposure Ledger")
                    .font(.system(size: 38, weight: .black, design: .rounded))
                Text("If you manually place a Braiins bid, record it here. The app then holds the research lifecycle so it does not start a competing experiment while real hashpower may still be maturing.")
                    .font(.title3)
                    .foregroundStyle(.secondary)

                GlassPanel {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Record Active Braiins Exposure", systemImage: "plus.circle")
                            .font(.headline)
                        TextField("Description, e.g. Braiins order abc, 0.00010 BTC, 180 min", text: $manualDescription)
                            .textFieldStyle(.roundedBorder)
                        HStack {
                            TextField("Maturity hours", text: $maturityHours)
                                .textFieldStyle(.roundedBorder)
                                .frame(width: 160)
                            Button("Record Exposure", action: record)
                                .buttonStyle(.borderedProminent)
                                .disabled(isRunning)
                        }
                    }
                }

                GlassPanel {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Close Finished Exposure", systemImage: "checkmark.circle")
                            .font(.headline)
                        TextField("Position ID", text: $closePositionId)
                            .textFieldStyle(.roundedBorder)
                            .frame(width: 180)
                        HStack {
                            Button("Close Exposure", action: close)
                                .buttonStyle(.borderedProminent)
                                .disabled(isRunning)
                            Button("List Positions", action: list)
                                .buttonStyle(.bordered)
                                .disabled(isRunning)
                        }
                    }
                }

                ActiveExposureList(positions: appState?.operatorState.activeManualPositions ?? [])
            }
            .padding(28)
        }
    }
}

struct ActiveExposureList: View {
    let positions: [String]

    var body: some View {
        GlassPanel {
            VStack(alignment: .leading, spacing: 12) {
                Label("Active Exposure", systemImage: "shield")
                    .font(.headline)
                if positions.isEmpty {
                    Text("No manual positions recorded.")
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(positions, id: \.self) { position in
                        Text(position)
                            .font(.system(.body, design: .monospaced))
                    }
                }
            }
        }
    }
}

struct ReportsView: View {
    let transcript: String
    let lastCommand: String
    let isRunning: Bool
    let loadReport: () -> Void
    let loadLedger: () -> Void
    let loadCockpit: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Reports")
                        .font(.system(size: 36, weight: .black, design: .rounded))
                    Text("Raw artifacts remain here, away from the noob cockpit.")
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Button("Cockpit", action: loadCockpit).disabled(isRunning)
                Button("Report", action: loadReport).disabled(isRunning)
                Button("Ledger", action: loadLedger).disabled(isRunning)
            }

            GlassPanel {
                VStack(alignment: .leading, spacing: 10) {
                    Label(lastCommand, systemImage: "terminal")
                        .font(.headline)
                    ScrollView {
                        Text(transcript)
                            .font(.system(.body, design: .monospaced))
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                }
            }
        }
        .padding(28)
    }
}

struct RatchetLectureView: View {
    private let lessons = [
        ("Observe", "Collect state without acting. Public Braiins price action and OCEAN context are measurements, not commands.", "eye"),
        ("Hypothesize", "State one reason a window might be useful. If the reason is vague, the experiment is not ready.", "lightbulb"),
        ("Bound", "Keep downside bounded. Canary means buying information, not pretending there is a money printer.", "shippingbox"),
        ("Mature", "Wait long enough for mining luck, share windows, and pool variance to mean something.", "hourglass"),
        ("Adapt", "Change one knob. If you change many knobs, you destroy attribution and learn nothing.", "dial.medium")
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                Text("The General Ratchet Principle")
                    .font(.system(size: 40, weight: .black, design: .rounded))
                Text("Autoresearch is not automation for its own sake. It is a disciplined loop that prevents mode collapse in a noisy, non-convex search space.")
                    .font(.title3)
                    .foregroundStyle(.secondary)

                ForEach(Array(lessons.enumerated()), id: \.offset) { index, lesson in
                    GlassPanel {
                        HStack(alignment: .top, spacing: 16) {
                            Text("\(index + 1)")
                                .font(.title.weight(.black))
                                .foregroundStyle(.white)
                                .frame(width: 54, height: 54)
                                .background(.green.gradient, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                            VStack(alignment: .leading, spacing: 8) {
                                Label(lesson.0, systemImage: lesson.2)
                                    .font(.title2.weight(.bold))
                                Text(lesson.1)
                                    .font(.body)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .padding(28)
        }
    }
}

struct AutoresearchOrb: View {
    let phase: ResearchPhase
    let glow: Bool

    var body: some View {
        ZStack {
            ForEach(0..<4) { index in
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [.green.opacity(0.15), .mint.opacity(0.75), .orange.opacity(0.55), .green.opacity(0.15)],
                            center: .center
                        ),
                        lineWidth: CGFloat(12 - index * 2)
                    )
                    .frame(width: CGFloat(210 + index * 28), height: CGFloat(210 + index * 28))
                    .rotationEffect(.degrees(glow ? Double(24 * (index + 1)) : Double(-18 * (index + 1))))
                    .opacity(0.72 - Double(index) * 0.12)
            }

            Circle()
                .fill(.ultraThinMaterial)
                .frame(width: 178, height: 178)
                .shadow(color: .green.opacity(glow ? 0.35 : 0.12), radius: glow ? 32 : 14)

            VStack(spacing: 8) {
                Image(systemName: phase.symbol)
                    .font(.system(size: 42, weight: .bold))
                    .foregroundStyle(.green)
                Text(phase.title)
                    .font(.title2.weight(.black))
                Text("current phase")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Current autoresearch phase: \(phase.title)")
    }
}

struct CooldownGauge: View {
    let watch: CompletedWatchPayload

    var progress: Double {
        guard watch.cooldownMinutes > 0 else { return 1 }
        return min(1, max(0, 1 - Double(watch.remainingMinutes) / Double(watch.cooldownMinutes)))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Label("Cooldown", systemImage: "timer")
                    .font(.headline)
                Spacer()
                Text("\(Int(progress * 100))%")
                    .font(.headline.monospacedDigit())
            }
            ProgressView(value: progress)
                .tint(.green)
            Text("Earliest next action: \(watch.earliestActionLocal). Remaining: \(watch.remainingMinutes) minutes.")
                .font(.callout)
                .foregroundStyle(.secondary)
        }
    }
}

struct SafetyStrip: View {
    var body: some View {
        HStack(spacing: 10) {
            Label("No hidden bids", systemImage: "lock")
            Label("Manual execution", systemImage: "hand.point.up.left")
            Label("Repo-local state", systemImage: "externaldrive")
        }
        .font(.caption.weight(.bold))
        .foregroundStyle(.secondary)
    }
}

struct GlassPanel<Content: View>: View {
    var padding: CGFloat = 22
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(padding)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 28, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 28, style: .continuous)
                    .stroke(.white.opacity(0.16), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.16), radius: 24, x: 0, y: 16)
    }
}

struct AppBackground: View {
    let glow: Bool

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.03, green: 0.06, blue: 0.07),
                    Color(red: 0.07, green: 0.16, blue: 0.15),
                    Color(red: 0.22, green: 0.21, blue: 0.14)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            Circle()
                .fill(.green.opacity(glow ? 0.22 : 0.11))
                .frame(width: 560, height: 560)
                .blur(radius: 90)
                .offset(x: -360, y: -280)
            Circle()
                .fill(.orange.opacity(glow ? 0.16 : 0.08))
                .frame(width: 440, height: 440)
                .blur(radius: 100)
                .offset(x: 460, y: 260)
            RoundedRectangle(cornerRadius: 90, style: .continuous)
                .stroke(.white.opacity(0.07), lineWidth: 1)
                .frame(width: 860, height: 520)
                .rotationEffect(.degrees(-13))
                .offset(x: 280, y: -170)
        }
        .ignoresSafeArea()
    }
}

enum ResearchStep: String, CaseIterable, Identifiable {
    case sense
    case price
    case watch
    case mature
    case adapt

    var id: String { rawValue }

    var title: String {
        switch self {
        case .sense: "Sense"
        case .price: "Price"
        case .watch: "Watch"
        case .mature: "Mature"
        case .adapt: "Adapt"
        }
    }

    var systemImage: String {
        switch self {
        case .sense: "antenna.radiowaves.left.and.right"
        case .price: "chart.line.uptrend.xyaxis"
        case .watch: "binoculars"
        case .mature: "hourglass"
        case .adapt: "slider.horizontal.3"
        }
    }
}

enum ResearchPhase {
    case setup
    case refresh
    case watch
    case cooldown
    case exposure
    case adapt

    static func from(_ appState: AppStatePayload?) -> ResearchPhase {
        guard let state = appState?.operatorState else { return .setup }
        if !state.activeManualPositions.isEmpty { return .exposure }
        if state.activeWatch != nil { return .watch }
        if state.completedWatch != nil { return .cooldown }
        if !state.hasOcean || !state.hasMarket || !state.isFresh { return .refresh }
        if state.action == "manual_canary" { return .watch }
        return .adapt
    }

    var title: String {
        switch self {
        case .setup: "Setup"
        case .refresh: "Refresh"
        case .watch: "Watch"
        case .cooldown: "Mature"
        case .exposure: "Hold"
        case .adapt: "Adapt"
        }
    }

    var symbol: String {
        switch self {
        case .setup: "wrench.and.screwdriver"
        case .refresh: "arrow.clockwise"
        case .watch: "binoculars"
        case .cooldown: "timer"
        case .exposure: "lock.shield"
        case .adapt: "slider.horizontal.3"
        }
    }

    var timelineIndex: Int {
        switch self {
        case .setup: 0
        case .refresh: 1
        case .watch: 2
        case .cooldown, .exposure: 3
        case .adapt: 4
        }
    }
}

struct Directive {
    let title: String
    let detail: String
    let command: String?
    let color: Color

    static func from(_ appState: AppStatePayload?) -> Directive {
        guard let appState else {
            return Directive(title: "LOAD STATE", detail: "The app is reading the ratchet lifecycle database.", command: nil, color: .secondary)
        }
        if let watch = appState.operatorState.completedWatch {
            return Directive(
                title: "STOP",
                detail: "Wait until \(watch.earliestActionLocal). Repeating the same watch now would be loop-chasing.",
                command: "./scripts/ratchet once",
                color: .orange
            )
        }
        if appState.operatorState.activeWatch != nil {
            return Directive(title: "WAIT", detail: "A watch is already running. Do not start another one.", command: nil, color: .orange)
        }
        if !appState.operatorState.activeManualPositions.isEmpty {
            return Directive(title: "HOLD", detail: "Manual Braiins exposure is active. Supervise it; do not start new experiments.", command: "./scripts/ratchet supervise --status", color: .orange)
        }
        if !appState.operatorState.hasOcean || !appState.operatorState.hasMarket || !appState.operatorState.isFresh {
            return Directive(title: "REFRESH", detail: "The latest market state is stale or missing. Collect exactly one fresh sample.", command: "./scripts/ratchet once", color: .green)
        }
        if appState.operatorState.action == "manual_canary" {
            return Directive(title: "WATCH", detail: "Run one bounded passive watch. This buys information, not a promise of profit.", command: "./scripts/ratchet watch 2", color: .green)
        }
        if appState.operatorState.action == "manual_bid" {
            return Directive(title: "REVIEW", detail: "Read the full report before any manual Braiins action.", command: "./scripts/ratchet report", color: .green)
        }
        return Directive(title: "OBSERVE", detail: "No useful action window is visible right now.", command: nil, color: .secondary)
    }
}

struct AppStatePayload: Codable {
    let generatedAt: String
    let operatorState: OperatorStatePayload
    let automationPlan: AutomationPlanPayload
    let cockpit: String
    let latest: LatestPayload

    enum CodingKeys: String, CodingKey {
        case generatedAt = "generated_at"
        case operatorState = "operator_state"
        case automationPlan = "automation_plan"
        case cockpit
        case latest
    }
}

struct OperatorStatePayload: Codable {
    let hasOcean: Bool
    let hasMarket: Bool
    let action: String?
    let activeWatch: String?
    let completedWatch: CompletedWatchPayload?
    let isFresh: Bool
    let freshnessMinutes: Int?
    let latestReport: String?
    let runningRuns: [String]
    let latestOceanTimestamp: String?
    let latestMarketTimestamp: String?
    let activeManualPositions: [String]

    enum CodingKeys: String, CodingKey {
        case hasOcean = "has_ocean"
        case hasMarket = "has_market"
        case action
        case activeWatch = "active_watch"
        case completedWatch = "completed_watch"
        case isFresh = "is_fresh"
        case freshnessMinutes = "freshness_minutes"
        case latestReport = "latest_report"
        case runningRuns = "running_runs"
        case latestOceanTimestamp = "latest_ocean_timestamp"
        case latestMarketTimestamp = "latest_market_timestamp"
        case activeManualPositions = "active_manual_positions"
    }
}

struct CompletedWatchPayload: Codable {
    let reportPath: String
    let ageMinutes: Int
    let remainingMinutes: Int
    let cooldownMinutes: Int
    let earliestActionUtc: String
    let earliestActionLocal: String

    enum CodingKeys: String, CodingKey {
        case reportPath = "report_path"
        case ageMinutes = "age_minutes"
        case remainingMinutes = "remaining_minutes"
        case cooldownMinutes = "cooldown_minutes"
        case earliestActionUtc = "earliest_action_utc"
        case earliestActionLocal = "earliest_action_local"
    }
}

struct AutomationPlanPayload: Codable {
    let kind: String
    let title: String
    let steps: [String]
    let waitSeconds: Int

    enum CodingKeys: String, CodingKey {
        case kind
        case title
        case steps
        case waitSeconds = "wait_seconds"
    }
}

struct LatestPayload: Codable {
    let ocean: [String: LooseString]?
    let market: [String: LooseString]?
    let proposal: [String: LooseString]?
}

struct LooseString: Codable, CustomStringConvertible {
    let description: String

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            description = "n/a"
        } else if let string = try? container.decode(String.self) {
            description = string
        } else if let int = try? container.decode(Int.self) {
            description = String(int)
        } else if let double = try? container.decode(Double.self) {
            description = String(double)
        } else if let bool = try? container.decode(Bool.self) {
            description = String(bool)
        } else {
            description = "n/a"
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(description)
    }
}

enum AppStateLoadResult {
    case success(AppStatePayload)
    case failure(String)
}

extension String {
    var lastPathComponent: String {
        URL(fileURLWithPath: self).lastPathComponent
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
    static func loadAppState() async -> AppStateLoadResult {
        await Task.detached {
            guard let repoRoot = findRepoRoot() else {
                return .failure(repoNotFoundMessage)
            }

            let script = repoRoot.appendingPathComponent("scripts/ratchet").path
            let process = Process()
            process.executableURL = URL(fileURLWithPath: "/bin/zsh")
            process.arguments = ["-lc", ([script, "app-state"]).map(shellQuote).joined(separator: " ")]
            process.currentDirectoryURL = repoRoot

            let outputPipe = Pipe()
            let errorPipe = Pipe()
            process.standardOutput = outputPipe
            process.standardError = errorPipe

            do {
                try process.run()
                process.waitUntilExit()
                let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
                let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
                let output = String(data: outputData, encoding: .utf8) ?? ""
                let errors = String(data: errorData, encoding: .utf8) ?? ""

                guard process.terminationStatus == 0 else {
                    return .failure(errors.isEmpty ? output : errors)
                }

                do {
                    let payload = try JSONDecoder().decode(AppStatePayload.self, from: outputData)
                    return .success(payload)
                } catch {
                    return .failure("""
                    Could not decode native app state.

                    Decode error: \(error.localizedDescription)

                    Output:
                    \(output)
                    \(errors)
                    """)
                }
            } catch {
                return .failure("Failed to load app state: \(error.localizedDescription)")
            }
        }.value
    }

    static func run(arguments: [String], input: String? = nil) async -> String {
        await Task.detached {
            guard let repoRoot = findRepoRoot() else {
                return repoNotFoundMessage
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

    private static var repoNotFoundMessage: String {
        """
        Braiins Ratchet cannot find its repository.

        Expected to find:
          scripts/ratchet

        Start the packaged app through:
          ./scripts/ratchet app

        Or open this bundle from inside the BraiinsRatchet repository:
          macos/build/Braiins Ratchet.app
        """
    }
}
