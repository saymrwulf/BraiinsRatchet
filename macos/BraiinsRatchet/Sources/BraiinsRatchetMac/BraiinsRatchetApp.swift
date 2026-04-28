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
            AppRootView()
                .frame(minWidth: 1180, minHeight: 780)
        }
        .windowStyle(.hiddenTitleBar)
    }
}

@MainActor
final class RatchetStore: ObservableObject {
    @Published var appState: AppStatePayload?
    @Published var rawText = "Loading Braiins Ratchet state..."
    @Published var rawTitle = "App State"
    @Published var operation: String?
    @Published var errorMessage: String?
    @Published var manualDescription = ""
    @Published var maturityHours = "72"
    @Published var closePositionId = ""

    var isWorking: Bool { operation != nil }

    func refresh() async {
        operation = "Refreshing state"
        rawTitle = "App State"
        let result = await RatchetProcess.loadAppState()
        switch result {
        case .success(let payload):
            appState = payload
            rawText = payload.cockpit
            errorMessage = nil
        case .failure(let message):
            errorMessage = message
            rawText = message
        }
        operation = nil
    }

    func runOneFreshSample() async {
        await run(label: "Fresh Sample", arguments: ["once"], refreshAfterwards: true)
    }

    func runOnePassiveWatch() async {
        await run(label: "Passive Watch", arguments: ["watch", "2"], refreshAfterwards: true)
    }

    func startEngine() async {
        await run(label: "Start Forever Engine", arguments: ["engine", "start"], refreshAfterwards: true)
    }

    func stopEngine() async {
        await run(label: "Stop Forever Engine", arguments: ["engine", "stop"], refreshAfterwards: true)
    }

    func showEngineStatus() async {
        await run(label: "Engine Status", arguments: ["engine", "status"], refreshAfterwards: true)
    }

    func showReport() async {
        await run(label: "Latest Report", arguments: ["report"], refreshAfterwards: false)
    }

    func showLedger() async {
        await run(label: "Experiment Ledger", arguments: ["experiments"], refreshAfterwards: false)
    }

    func showCockpit() async {
        await run(label: "Raw Cockpit", arguments: ["next"], refreshAfterwards: false)
    }

    func recordManualExposure() async {
        let description = manualDescription.trimmingCharacters(in: .whitespacesAndNewlines)
        let hours = maturityHours.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !description.isEmpty else {
            errorMessage = "Enter a Braiins exposure description first."
            return
        }
        await run(
            label: "Record Exposure",
            arguments: [
                "position", "open",
                "--description", description,
                "--maturity-hours", hours.isEmpty ? "72" : hours
            ],
            refreshAfterwards: true
        )
        manualDescription = ""
    }

    func closeManualExposure() async {
        let positionId = closePositionId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !positionId.isEmpty else {
            errorMessage = "Enter a manual position ID first."
            return
        }
        await run(
            label: "Close Exposure",
            arguments: ["position", "close", positionId],
            refreshAfterwards: true
        )
        closePositionId = ""
    }

    private func run(label: String, arguments: [String], refreshAfterwards: Bool) async {
        operation = label
        rawTitle = label
        rawText = "\(label) is running..."
        let result = await RatchetProcess.run(arguments: arguments)
        rawText = result
        errorMessage = nil
        operation = nil
        if refreshAfterwards {
            await refresh()
        }
    }
}

struct AppRootView: View {
    @StateObject private var store = RatchetStore()
    @State private var selection: AppSection? = .mission
    @State private var animate = false

    var body: some View {
        NavigationSplitView {
            Sidebar(selection: $selection, store: store)
        } detail: {
            ZStack {
                AppBackdrop(animate: animate)
                Group {
                    switch selection ?? .mission {
                    case .mission:
                        MissionControlView(store: store)
                    case .stack:
                        MiningStackView(store: store)
                    case .ratchet:
                        RatchetPathView(store: store)
                    case .strategy:
                        StrategyLabView(store: store)
                    case .exposure:
                        ManualExposureView(store: store)
                    case .vault:
                        EvidenceVaultView(store: store)
                    }
                }
            }
            .toolbar {
                ToolbarItemGroup {
                    Button {
                        Task { await store.refresh() }
                    } label: {
                        Label("Refresh", systemImage: "arrow.clockwise")
                    }
                    .disabled(store.isWorking)

                    Button {
                        Task { await store.showEngineStatus() }
                    } label: {
                        Label("Engine", systemImage: "dot.radiowaves.left.and.right")
                    }
                    .disabled(store.isWorking)
                }
            }
        }
        .task {
            await store.refresh()
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 5).repeatForever(autoreverses: true)) {
                animate = true
            }
        }
    }
}

enum AppSection: String, CaseIterable, Identifiable {
    case mission
    case stack
    case ratchet
    case strategy
    case exposure
    case vault

    var id: String { rawValue }

    var title: String {
        switch self {
        case .mission: "Mission Control"
        case .stack: "Mining Stack"
        case .ratchet: "Ratchet"
        case .strategy: "Strategy Lab"
        case .exposure: "Manual Exposure"
        case .vault: "Evidence Vault"
        }
    }

    var subtitle: String {
        switch self {
        case .mission: "what to do, when, and why"
        case .stack: "Umbrel, Knots, Datum, OCEAN, Braiins"
        case .ratchet: "learning loop and future path"
        case .strategy: "shadow bids and loss bounds"
        case .exposure: "real manual positions"
        case .vault: "reports and raw diagnostics"
        }
    }

    var symbol: String {
        switch self {
        case .mission: "scope"
        case .stack: "point.3.connected.trianglepath.dotted"
        case .ratchet: "arrow.triangle.2.circlepath"
        case .strategy: "chart.xyaxis.line"
        case .exposure: "lock.shield"
        case .vault: "archivebox"
        }
    }
}

struct Sidebar: View {
    @Binding var selection: AppSection?
    @ObservedObject var store: RatchetStore

    var body: some View {
        List(AppSection.allCases, selection: $selection) { section in
            NavigationLink(value: section) {
                Label {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(section.title)
                            .font(.headline)
                        Text(section.subtitle)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } icon: {
                    Image(systemName: section.symbol)
                }
            }
            .tag(section as AppSection?)
        }
        .navigationTitle("Ratchet")
        .safeAreaInset(edge: .bottom) {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 10) {
                    Image(nsImage: AppIconFactory.makeIcon(size: 38))
                        .resizable()
                        .frame(width: 38, height: 38)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                    VStack(alignment: .leading, spacing: 2) {
                        Text(store.appState?.engineStatus.running == true ? "Engine running" : "Engine stopped")
                            .font(.caption.weight(.bold))
                        Text("monitor-only")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                if let operation = store.operation {
                    ProgressView(operation)
                        .controlSize(.small)
                }
            }
            .padding(12)
        }
    }
}

struct MissionControlView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                MissionHero(store: store)

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    ControlOwnerCard(store: store)
                    NextActionCard(store: store)
                }

                EvidenceStrip(appState: store.appState)

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    CenterOfAttentionCard(
                        number: "1",
                        title: "UX first",
                        text: "The app must tell you what is happening without making you parse logs or babysit terminals.",
                        symbol: "rectangle.3.group"
                    )
                    CenterOfAttentionCard(
                        number: "2",
                        title: "Ratchet second",
                        text: "Every run is evidence. The system blocks fake progress and changes only one knob after maturity.",
                        symbol: "arrow.triangle.2.circlepath"
                    )
                    CenterOfAttentionCard(
                        number: "3",
                        title: "Mining stack third",
                        text: "Braiins price, OCEAN luck/window, Datum routing, Knots validation, and Umbrel operations are one system.",
                        symbol: "cpu"
                    )
                }
            }
            .padding(28)
        }
    }
}

struct MissionHero: View {
    @ObservedObject var store: RatchetStore

    private var decision: Decision {
        Decision.from(store.appState, isWorking: store.isWorking)
    }

    var body: some View {
        HeroSurface {
            HStack(alignment: .top, spacing: 24) {
                VStack(alignment: .leading, spacing: 22) {
                    HStack(spacing: 14) {
                        Image(nsImage: AppIconFactory.makeIcon(size: 58))
                            .resizable()
                            .frame(width: 58, height: 58)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Braiins Ratchet")
                                .font(.system(size: 42, weight: .black, design: .rounded))
                            Text("Native autoresearch cockpit for buying hashpower smarter")
                                .font(.title3)
                                .foregroundStyle(.secondary)
                        }
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Current Decision")
                            .font(.caption.weight(.heavy))
                            .textCase(.uppercase)
                            .foregroundStyle(.secondary)
                        Text(decision.title)
                            .font(.system(size: 56, weight: .black, design: .rounded))
                            .foregroundStyle(decision.color)
                        Text(decision.explanation)
                            .font(.title3.weight(.semibold))
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    SafetyRow()
                }

                Spacer(minLength: 20)

                VStack(spacing: 16) {
                    PhaseOrb(phase: ResearchPhase.from(store.appState), running: store.appState?.engineStatus.running == true)
                        .frame(width: 230, height: 230)

                    if let watch = store.appState?.operatorState.completedWatch {
                        CooldownRing(watch: watch)
                    } else {
                        EngineBadge(status: store.appState?.engineStatus)
                    }
                }
                .frame(width: 280)
            }
        }
    }
}

struct ControlOwnerCard: View {
    @ObservedObject var store: RatchetStore

    private var owner: ControlOwner {
        ControlOwner.from(store.appState, isWorking: store.isWorking)
    }

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                Label("Who Owns Control", systemImage: owner.symbol)
                    .font(.headline)
                Text(owner.title)
                    .font(.system(size: 30, weight: .black, design: .rounded))
                Text(owner.detail)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct NextActionCard: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                Label("Next Useful Action", systemImage: "arrow.forward.circle")
                    .font(.headline)
                Text(nextTitle)
                    .font(.system(size: 30, weight: .black, design: .rounded))
                Text(nextDetail)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                HStack(spacing: 10) {
                    if store.appState?.engineStatus.running == true {
                        Button("Stop Forever Engine") {
                            Task { await store.stopEngine() }
                        }
                        .buttonStyle(.bordered)
                        .disabled(store.isWorking)
                    } else {
                        Button("Start Forever Engine") {
                            Task { await store.startEngine() }
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(engineStartBlocked || store.isWorking)
                    }

                    Button(passiveButtonTitle) {
                        Task { await runPassiveAction() }
                    }
                    .buttonStyle(.bordered)
                    .disabled(!canRunPassive || store.isWorking)
                }
            }
        }
    }

    private var nextTitle: String {
        guard let state = store.appState else { return "Load state" }
        if state.engineStatus.running { return "Let the engine work" }
        if state.operatorState.completedWatch != nil { return "Wait for cooldown" }
        if state.operatorState.activeWatch != nil { return "Wait for watch" }
        if !state.operatorState.activeManualPositions.isEmpty { return "Hold exposure" }
        return state.automationPlan.title
    }

    private var nextDetail: String {
        guard let state = store.appState else { return "The app is reading SQLite and latest reports." }
        if state.engineStatus.running {
            return "The forever monitor engine will wait, sample, watch, write evidence, and re-enter cooldown without terminal babysitting."
        }
        if let watch = state.operatorState.completedWatch {
            return "Earliest next action: \(watch.earliestActionLocal). Starting another identical watch before then is loop-chasing."
        }
        if !state.operatorState.activeManualPositions.isEmpty {
            return "A real-world Braiins/OCEAN position is active. New experiments stay blocked until you close it."
        }
        return state.automationPlan.steps.first ?? "No passive action is useful right now."
    }

    private var engineStartBlocked: Bool {
        guard let state = store.appState else { return false }
        return state.operatorState.activeWatch != nil || !state.operatorState.activeManualPositions.isEmpty
    }

    private var canRunPassive: Bool {
        guard let plan = store.appState?.automationPlan else { return false }
        switch plan.kind {
        case "once_now", "watch_2h", "report_only":
            return true
        case "wait_then_once":
            return plan.waitSeconds <= 0
        default:
            return false
        }
    }

    private var passiveButtonTitle: String {
        guard let plan = store.appState?.automationPlan else { return "Refresh" }
        switch plan.kind {
        case "once_now": return "One Fresh Sample"
        case "watch_2h": return "One Watch"
        case "wait_then_once": return plan.waitSeconds > 0 ? "Cooling Down" : "One Fresh Sample"
        case "report_only": return "Open Report"
        default: return "No Passive Step"
        }
    }

    private func runPassiveAction() async {
        guard let plan = store.appState?.automationPlan else {
            await store.refresh()
            return
        }
        switch plan.kind {
        case "once_now":
            await store.runOneFreshSample()
        case "watch_2h":
            await store.runOnePassiveWatch()
        case "wait_then_once" where plan.waitSeconds <= 0:
            await store.runOneFreshSample()
        case "report_only":
            await store.showReport()
        default:
            await store.refresh()
        }
    }
}

struct EvidenceStrip: View {
    let appState: AppStatePayload?

    var body: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 14), count: 4), spacing: 14) {
            MetricCard(
                title: "Braiins Fill Price",
                value: market("fillable_price_btc_per_eh_day", fallback: market("best_ask_btc_per_eh_day")),
                detail: "best ask \(market("best_ask_btc_per_eh_day"))",
                symbol: "bitcoinsign.circle"
            )
            MetricCard(
                title: "OCEAN Pool",
                value: "\(ocean("pool_hashrate_eh_s")) EH/s",
                detail: "difficulty \(ocean("network_difficulty_t")) T",
                symbol: "water.waves"
            )
            MetricCard(
                title: "Model Net",
                value: sats(proposal("expected_net_btc")),
                detail: "BTC \(proposal("expected_net_btc"))",
                symbol: "plus.forwardslash.minus"
            )
            MetricCard(
                title: "Evidence",
                value: appState?.operatorState.latestReport?.lastPathComponent ?? "none",
                detail: freshnessText,
                symbol: "doc.text.magnifyingglass"
            )
        }
    }

    private var freshnessText: String {
        guard let minutes = appState?.operatorState.freshnessMinutes else { return "no sample age" }
        return minutes <= 30 ? "fresh, \(minutes)m old" : "stale, \(minutes)m old"
    }

    private func market(_ key: String, fallback: String = "n/a") -> String {
        appState?.latest.market?[key]?.description ?? fallback
    }

    private func ocean(_ key: String) -> String {
        appState?.latest.ocean?[key]?.description ?? "n/a"
    }

    private func proposal(_ key: String) -> String {
        appState?.latest.proposal?[key]?.description ?? "n/a"
    }
}

struct CenterOfAttentionCard: View {
    let number: String
    let title: String
    let text: String
    let symbol: String

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text(number)
                        .font(.title.weight(.black))
                        .foregroundStyle(.white)
                        .frame(width: 46, height: 46)
                        .background(.green.gradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    Spacer()
                    Image(systemName: symbol)
                        .font(.title2)
                        .foregroundStyle(.green)
                }
                Text(title)
                    .font(.title2.weight(.black))
                Text(text)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct MiningStackView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                PageHeader(
                    title: "Mining Stack",
                    subtitle: "The system you are actually operating: your Umbrel validates and routes; Braiins supplies temporary hashers; OCEAN turns pooled work into stochastic rewards."
                )

                Card {
                    VStack(alignment: .leading, spacing: 18) {
                        Label("Two Hashpower Sources, One Reward Funnel", systemImage: "arrow.down.forward.and.arrow.up.backward")
                            .font(.headline)
                        HStack(alignment: .top, spacing: 16) {
                            StackLane(
                                title: "Your sovereign miner path",
                                accent: .cyan,
                                nodes: [
                                    StackNode("Umbrel", "local operator shell", "house"),
                                    StackNode("Knots", "validates Bitcoin rules", "checkmark.seal"),
                                    StackNode("Datum", "job routing / template work", "point.3.connected.trianglepath.dotted"),
                                    StackNode("OCEAN", "pool payout window", "water.waves")
                                ]
                            )
                            StackLane(
                                title: "Bought hashpower path",
                                accent: .green,
                                nodes: [
                                    StackNode("Braiins", "hashmarket order book", "chart.line.uptrend.xyaxis"),
                                    StackNode("Sub hashers", "temporary workers", "bolt.horizontal"),
                                    StackNode("OCEAN", "same reward funnel", "water.waves"),
                                    StackNode("Blocks", "luck dominates short windows", "cube")
                                ]
                            )
                        }
                    }
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    InterplayCard(
                        title: "Braiins pressure",
                        symbol: "cart",
                        text: "Your controllable variable is bid shape: price, size, duration, timing, and target depth. The app currently models a shadow order before any manual spend.",
                        facts: [
                            "fillable price: \(market("fillable_price_btc_per_eh_day")) BTC/EH/day",
                            "available: \(market("available_hashrate_eh_s")) EH/s",
                            "target depth: \(market("fillable_target_ph")) PH/s"
                        ]
                    )
                    InterplayCard(
                        title: "OCEAN variance",
                        symbol: "dice",
                        text: "Your bought hashpower only matters if OCEAN block discovery and the payout window cooperate. Short canaries can be scientifically useful and still lose.",
                        facts: [
                            "pool: \(ocean("pool_hashrate_eh_s")) EH/s",
                            "share window: \(ocean("share_log_window_t")) T",
                            "avg block time: \(ocean("avg_block_time_hours")) h"
                        ]
                    )
                    InterplayCard(
                        title: "Local sovereignty",
                        symbol: "lock.shield",
                        text: "Umbrel, Knots, and Datum are treated as infrastructure context, not something this app mutates. This app reads and reasons; it does not reconfigure your node.",
                        facts: [
                            "computer safety: repo-local writes",
                            "Braiins orders: manual only",
                            "watch token: optional read-only later"
                        ]
                    )
                    InterplayCard(
                        title: "Objective",
                        symbol: "target",
                        text: "The objective is not a money-printer oracle. The objective is to discover bid regimes that minimize expected loss or expose rare profitable windows.",
                        facts: [
                            "capital: \(config("capital", "available_btc")) BTC",
                            "canary budget: \(config("guardrails", "max_canary_expected_loss_btc")) BTC",
                            "spend cap: \(config("guardrails", "max_manual_order_btc")) BTC"
                        ]
                    )
                }
            }
            .padding(28)
        }
    }

    private func market(_ key: String) -> String {
        store.appState?.latest.market?[key]?.description ?? "n/a"
    }

    private func ocean(_ key: String) -> String {
        store.appState?.latest.ocean?[key]?.description ?? "n/a"
    }

    private func config(_ section: String, _ key: String) -> String {
        store.appState?.config.value(section, key) ?? "n/a"
    }
}

struct StackNode: Identifiable {
    let id = UUID()
    let title: String
    let subtitle: String
    let symbol: String

    init(_ title: String, _ subtitle: String, _ symbol: String) {
        self.title = title
        self.subtitle = subtitle
        self.symbol = symbol
    }
}

struct StackLane: View {
    let title: String
    let accent: Color
    let nodes: [StackNode]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(title)
                .font(.headline)
            ForEach(Array(nodes.enumerated()), id: \.element.id) { index, node in
                HStack(spacing: 12) {
                    Image(systemName: node.symbol)
                        .font(.title3)
                        .foregroundStyle(.white)
                        .frame(width: 44, height: 44)
                        .background(accent.gradient, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    VStack(alignment: .leading, spacing: 3) {
                        Text(node.title)
                            .font(.headline)
                        Text(node.subtitle)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if index < nodes.count - 1 {
                        Image(systemName: "arrow.down")
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(12)
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

struct InterplayCard: View {
    let title: String
    let symbol: String
    let text: String
    let facts: [String]

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                Label(title, systemImage: symbol)
                    .font(.title3.weight(.bold))
                Text(text)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(facts, id: \.self) { fact in
                        Label(fact, systemImage: "smallcircle.filled.circle")
                            .font(.caption.weight(.semibold))
                    }
                }
                .foregroundStyle(.secondary)
            }
        }
    }
}

struct RatchetPathView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                PageHeader(
                    title: "Autoresearch Ratchet",
                    subtitle: "Karpathy-style progress means one measured step forward, never a vague loop. The app should make the research path lecture-grade."
                )

                Card {
                    VStack(alignment: .leading, spacing: 18) {
                        Label("Current Learning Loop", systemImage: "arrow.triangle.2.circlepath")
                            .font(.headline)
                        RatchetStepper(phase: ResearchPhase.from(store.appState))
                        Text(phaseExplanation)
                            .font(.title3.weight(.semibold))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    PathForecastCard(
                        title: "Immediate",
                        probability: "highest confidence",
                        text: immediateForecast,
                        symbol: "1.circle"
                    )
                    PathForecastCard(
                        title: "Midterm",
                        probability: "likely to change",
                        text: midtermForecast,
                        symbol: "2.circle"
                    )
                    PathForecastCard(
                        title: "Longterm",
                        probability: "conditional",
                        text: longtermForecast,
                        symbol: "3.circle"
                    )
                }

                Card {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("One-Knob Law", systemImage: "slider.horizontal.3")
                            .font(.headline)
                        Text("A ratchet fails when multiple variables change at once. Strategy adaptation is only allowed when mature evidence repeats a pattern.")
                            .font(.title3.weight(.semibold))
                        HStack {
                            KnobPill("depth target")
                            KnobPill("overpay cushion")
                            KnobPill("canary spend")
                            KnobPill("duration")
                            KnobPill("timing window")
                        }
                    }
                }
            }
            .padding(28)
        }
    }

    private var phaseExplanation: String {
        switch ResearchPhase.from(store.appState) {
        case .loading: return "The app is loading the durable state before choosing a research stage."
        case .refresh: return "The market sample is stale or missing. One fresh sample is useful; a new watch is not yet justified."
        case .watch: return "A bounded watch is the active measurement. It buys information without spending BTC."
        case .cooldown: return "The previous watch is evidence. Cooldown prevents repeating the same experiment and pretending it was progress."
        case .manual: return "A manual Braiins exposure is active. The ratchet holds until that real-world position is closed."
        case .adapt: return "Evidence exists and the system can consider one controlled knob change later."
        }
    }

    private var immediateForecast: String {
        if let watch = store.appState?.operatorState.completedWatch {
            return "Wait until \(watch.earliestActionLocal). Workload: zero unless you are reviewing the report."
        }
        if store.appState?.engineStatus.running == true {
            return "Let the forever monitor engine own passive sampling."
        }
        return store.appState?.automationPlan.steps.first ?? "Load state."
    }

    private var midtermForecast: String {
        if store.appState?.operatorState.completedWatch != nil {
            return "After cooldown, one fresh sample compares current Braiins/OCEAN state against the last report."
        }
        return "The next report becomes the evidence artifact; it does not decide profit alone."
    }

    private var longtermForecast: String {
        "Only repeated mature evidence can justify changing one bid knob or considering a tiny manual canary."
    }
}

struct RatchetStepper: View {
    let phase: ResearchPhase
    private let stages: [ResearchStage] = [
        ResearchStage("Sense", "collect", "antenna.radiowaves.left.and.right"),
        ResearchStage("Price", "shadow market", "chart.line.uptrend.xyaxis"),
        ResearchStage("Watch", "measure", "binoculars"),
        ResearchStage("Mature", "wait", "hourglass"),
        ResearchStage("Adapt", "one knob", "slider.horizontal.3")
    ]

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Array(stages.enumerated()), id: \.element.id) { index, stage in
                StageBubble(stage: stage, state: state(for: index))
                if index < stages.count - 1 {
                    Rectangle()
                        .fill(index < phase.index ? Color.green.opacity(0.75) : Color.secondary.opacity(0.22))
                        .frame(height: 4)
                }
            }
        }
    }

    private func state(for index: Int) -> StageBubble.StateKind {
        if index < phase.index { return .done }
        if index == phase.index { return .active }
        return .future
    }
}

struct ResearchStage: Identifiable {
    let id = UUID()
    let title: String
    let subtitle: String
    let symbol: String

    init(_ title: String, _ subtitle: String, _ symbol: String) {
        self.title = title
        self.subtitle = subtitle
        self.symbol = symbol
    }
}

struct StageBubble: View {
    enum StateKind {
        case done
        case active
        case future
    }

    let stage: ResearchStage
    let state: StateKind

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: stage.symbol)
                .font(.headline)
                .foregroundStyle(.white)
                .frame(width: 50, height: 50)
                .background(fill, in: Circle())
            Text(stage.title)
                .font(.caption.weight(.bold))
            Text(stage.subtitle)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(width: 112)
    }

    private var fill: AnyShapeStyle {
        switch state {
        case .done: AnyShapeStyle(Color.green.gradient)
        case .active: AnyShapeStyle(Color.orange.gradient)
        case .future: AnyShapeStyle(Color.secondary.opacity(0.25))
        }
    }
}

struct PathForecastCard: View {
    let title: String
    let probability: String
    let text: String
    let symbol: String

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 12) {
                Label(title, systemImage: symbol)
                    .font(.title3.weight(.bold))
                Text(probability)
                    .font(.caption.weight(.heavy))
                    .textCase(.uppercase)
                    .foregroundStyle(.green)
                Text(text)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

struct KnobPill: View {
    let text: String

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        Text(text)
            .font(.caption.weight(.bold))
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(.regularMaterial, in: Capsule())
    }
}

struct StrategyLabView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                PageHeader(
                    title: "Strategy Lab",
                    subtitle: "This is the shadow bid desk. It explains what the model would study, not an owner-token execution surface."
                )

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    ShadowOrderCard(appState: store.appState)
                    RiskBoundaryCard(appState: store.appState)
                }

                Card {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Why This Is Hard", systemImage: "exclamationmark.triangle")
                            .font(.headline)
                        Text("A good Braiins price can still lose if OCEAN does not find blocks inside the payout window. A bad-looking expected value can still be useful if it maps price behavior under bounded downside. The app separates learning value from profit claims.")
                            .font(.title3.weight(.semibold))
                            .fixedSize(horizontal: false, vertical: true)
                        Text(store.appState?.latest.proposal?["reason"]?.description ?? "No proposal loaded.")
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .padding(28)
        }
    }
}

struct ShadowOrderCard: View {
    let appState: AppStatePayload?

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                Label("Shadow Order", systemImage: "doc.text.magnifyingglass")
                    .font(.headline)
                Text(actionTitle)
                    .font(.system(size: 34, weight: .black, design: .rounded))
                    .foregroundStyle(actionColor)
                VStack(spacing: 8) {
                    StrategyRow("price", proposal("order_price_btc_per_eh_day"), "BTC/EH/day")
                    StrategyRow("spend", proposal("order_spend_btc"), "BTC")
                    StrategyRow("duration", proposal("order_duration_minutes"), "minutes")
                    StrategyRow("implied speed", phText(proposal("order_implied_hashrate_eh_s")), "PH/s")
                }
            }
        }
    }

    private var actionTitle: String {
        switch proposal("action") {
        case "manual_bid": return "Manual bid review"
        case "manual_canary": return "Learning canary"
        case "observe": return "Observe only"
        default: return "No proposal"
        }
    }

    private var actionColor: Color {
        switch proposal("action") {
        case "manual_bid": return .green
        case "manual_canary": return .orange
        default: return .secondary
        }
    }

    private func proposal(_ key: String) -> String {
        appState?.latest.proposal?[key]?.description ?? "n/a"
    }
}

struct RiskBoundaryCard: View {
    let appState: AppStatePayload?

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: 14) {
                Label("Loss Boundary", systemImage: "shield.lefthalf.filled")
                    .font(.headline)
                Text(sats(proposal("expected_net_btc")))
                    .font(.system(size: 34, weight: .black, design: .rounded))
                    .foregroundStyle(netColor)
                VStack(spacing: 8) {
                    StrategyRow("expected reward", proposal("expected_reward_btc"), "BTC")
                    StrategyRow("expected net", proposal("expected_net_btc"), "BTC")
                    StrategyRow("breakeven", proposal("breakeven_btc_per_eh_day"), "BTC/EH/day")
                    StrategyRow("canary budget", config("guardrails", "max_canary_expected_loss_btc"), "BTC")
                }
            }
        }
    }

    private var netColor: Color {
        let value = Double(proposal("expected_net_btc")) ?? 0
        return value >= 0 ? .green : .orange
    }

    private func proposal(_ key: String) -> String {
        appState?.latest.proposal?[key]?.description ?? "n/a"
    }

    private func config(_ section: String, _ key: String) -> String {
        appState?.config.value(section, key) ?? "n/a"
    }
}

struct StrategyRow: View {
    let label: String
    let value: String
    let unit: String

    init(_ label: String, _ value: String, _ unit: String) {
        self.label = label
        self.value = value
        self.unit = unit
    }

    var body: some View {
        HStack {
            Text(label)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.body.monospacedDigit().weight(.semibold))
            Text(unit)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(10)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct ManualExposureView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                PageHeader(
                    title: "Manual Exposure",
                    subtitle: "If you manually place a Braiins order, record it here immediately so the ratchet stops creating competing experiments."
                )

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    Card {
                        VStack(alignment: .leading, spacing: 14) {
                            Label("Record A Real Position", systemImage: "plus.circle")
                                .font(.headline)
                            TextField("Braiins order, spend, duration, target pool", text: $store.manualDescription)
                                .textFieldStyle(.roundedBorder)
                            HStack {
                                TextField("Maturity hours", text: $store.maturityHours)
                                    .textFieldStyle(.roundedBorder)
                                    .frame(width: 150)
                                Button("Record Exposure") {
                                    Task { await store.recordManualExposure() }
                                }
                                .buttonStyle(.borderedProminent)
                                .disabled(store.isWorking)
                            }
                            Text("This does not place the order. It only records what you already did manually.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }

                    Card {
                        VStack(alignment: .leading, spacing: 14) {
                            Label("Close Finished Position", systemImage: "checkmark.circle")
                                .font(.headline)
                            TextField("Position ID", text: $store.closePositionId)
                                .textFieldStyle(.roundedBorder)
                                .frame(width: 160)
                            Button("Close Exposure") {
                                Task { await store.closeManualExposure() }
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(store.isWorking)
                            Text("Close only when the Braiins/OCEAN exposure is truly finished.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                Card {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Active Exposure Hold", systemImage: "lock.shield")
                            .font(.headline)
                        if let positions = store.appState?.operatorState.activeManualPositions, !positions.isEmpty {
                            ForEach(positions, id: \.self) { position in
                                Text(position)
                                    .font(.body.monospaced())
                                    .padding(10)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                            }
                        } else {
                            Text("No manual exposure is active.")
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .padding(28)
        }
    }
}

struct EvidenceVaultView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                PageHeader(
                    title: "Evidence Vault",
                    subtitle: "Raw artifacts live here. Mission Control stays graphical; this tab is for audit and debugging."
                )
                Spacer()
                Button("Cockpit") {
                    Task { await store.showCockpit() }
                }
                .disabled(store.isWorking)
                Button("Report") {
                    Task { await store.showReport() }
                }
                .disabled(store.isWorking)
                Button("Ledger") {
                    Task { await store.showLedger() }
                }
                .disabled(store.isWorking)
            }

            Card {
                VStack(alignment: .leading, spacing: 12) {
                    Label(store.rawTitle, systemImage: "archivebox")
                        .font(.headline)
                    ScrollView {
                        Text(store.rawText)
                            .font(.body.monospaced())
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                }
            }
        }
        .padding(28)
    }
}

struct PageHeader: View {
    let title: String
    let subtitle: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 40, weight: .black, design: .rounded))
            Text(subtitle)
                .font(.title3)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct HeroSurface<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(28)
            .background(
                RoundedRectangle(cornerRadius: 34, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .shadow(color: .green.opacity(0.18), radius: 30, x: 0, y: 18)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 34, style: .continuous)
                    .stroke(.white.opacity(0.18), lineWidth: 1)
            )
    }
}

struct Card<Content: View>: View {
    var padding: CGFloat = 20
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(padding)
            .frame(maxWidth: .infinity, alignment: .topLeading)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 26, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(.white.opacity(0.12), lineWidth: 1)
            )
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let detail: String
    let symbol: String

    var body: some View {
        Card(padding: 16) {
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
        }
    }
}

struct SafetyRow: View {
    var body: some View {
        HStack(spacing: 10) {
            Label("No hidden bids", systemImage: "lock")
            Label("Manual Braiins execution", systemImage: "hand.point.up.left")
            Label("Repo-local state", systemImage: "externaldrive")
        }
        .font(.caption.weight(.bold))
        .foregroundStyle(.secondary)
    }
}

struct EngineBadge: View {
    let status: EngineStatusPayload?

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: status?.running == true ? "dot.radiowaves.left.and.right" : "power")
                .font(.system(size: 34, weight: .bold))
                .foregroundStyle(status?.running == true ? .green : .secondary)
            Text(status?.running == true ? "engine running" : "engine stopped")
                .font(.headline)
            Text(status?.detail ?? "loading engine status")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(18)
        .frame(maxWidth: .infinity)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}

struct PhaseOrb: View {
    let phase: ResearchPhase
    let running: Bool

    var body: some View {
        ZStack {
            ForEach(0..<4) { index in
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [.green.opacity(0.14), .mint.opacity(0.74), .orange.opacity(0.54), .green.opacity(0.14)],
                            center: .center
                        ),
                        lineWidth: CGFloat(12 - index * 2)
                    )
                    .frame(width: CGFloat(170 + index * 28), height: CGFloat(170 + index * 28))
                    .rotationEffect(.degrees(running ? Double(18 * (index + 1)) : Double(-8 * (index + 1))))
                    .opacity(0.72 - Double(index) * 0.12)
            }

            Circle()
                .fill(.regularMaterial)
                .frame(width: 154, height: 154)

            VStack(spacing: 8) {
                Image(systemName: phase.symbol)
                    .font(.system(size: 40, weight: .bold))
                    .foregroundStyle(.green)
                Text(phase.title)
                    .font(.title2.weight(.black))
                Text("ratchet phase")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)
            }
        }
    }
}

struct CooldownRing: View {
    let watch: CompletedWatchPayload

    private var progress: Double {
        guard watch.cooldownMinutes > 0 else { return 1 }
        return min(1, max(0, 1 - Double(watch.remainingMinutes) / Double(watch.cooldownMinutes)))
    }

    var body: some View {
        VStack(spacing: 10) {
            ZStack {
                Circle()
                    .stroke(.secondary.opacity(0.18), lineWidth: 12)
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(.green.gradient, style: StrokeStyle(lineWidth: 12, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                Text("\(Int(progress * 100))%")
                    .font(.title2.monospacedDigit().weight(.black))
            }
            .frame(width: 120, height: 120)

            Text("cooldown")
                .font(.headline)
            Text("\(watch.remainingMinutes)m left")
                .font(.caption.weight(.bold))
                .foregroundStyle(.secondary)
            Text(watch.earliestActionLocal)
                .font(.caption2)
                .foregroundStyle(.secondary)
                .lineLimit(1)
        }
        .padding(18)
        .frame(maxWidth: .infinity)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}

struct AppBackdrop: View {
    let animate: Bool

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.025, green: 0.045, blue: 0.055),
                    Color(red: 0.045, green: 0.135, blue: 0.13),
                    Color(red: 0.20, green: 0.18, blue: 0.11)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            Circle()
                .fill(.green.opacity(animate ? 0.24 : 0.10))
                .frame(width: 620, height: 620)
                .blur(radius: 100)
                .offset(x: -380, y: -290)
            Circle()
                .fill(.orange.opacity(animate ? 0.17 : 0.07))
                .frame(width: 520, height: 520)
                .blur(radius: 120)
                .offset(x: 500, y: 300)
            RoundedRectangle(cornerRadius: 100, style: .continuous)
                .stroke(.white.opacity(0.06), lineWidth: 1)
                .frame(width: 900, height: 540)
                .rotationEffect(.degrees(-12))
                .offset(x: 270, y: -170)
        }
        .ignoresSafeArea()
    }
}

enum Decision {
    case load
    case busy(String)
    case hold
    case waitWatch
    case cooldown(String)
    case engine
    case refresh
    case watch
    case review
    case observe

    static func from(_ appState: AppStatePayload?, isWorking: Bool) -> Decision {
        if isWorking { return .busy("Working") }
        guard let appState else { return .load }
        let state = appState.operatorState
        if !state.activeManualPositions.isEmpty { return .hold }
        if state.activeWatch != nil { return .waitWatch }
        if appState.engineStatus.running { return .engine }
        if let watch = state.completedWatch { return .cooldown(watch.earliestActionLocal) }
        if !state.hasOcean || !state.hasMarket || !state.isFresh { return .refresh }
        if state.action == "manual_canary" { return .watch }
        if state.action == "manual_bid" { return .review }
        return .observe
    }

    var title: String {
        switch self {
        case .load: return "LOAD"
        case .busy: return "WORKING"
        case .hold: return "HOLD"
        case .waitWatch: return "WAIT"
        case .cooldown: return "COOLDOWN"
        case .engine: return "ENGINE ON"
        case .refresh: return "REFRESH"
        case .watch: return "WATCH"
        case .review: return "REVIEW"
        case .observe: return "OBSERVE"
        }
    }

    var explanation: String {
        switch self {
        case .load:
            return "Reading the durable SQLite state and latest evidence."
        case .busy(let operation):
            return "\(operation) is running. Do not start a competing operation."
        case .hold:
            return "A real manual Braiins exposure is active. The app must supervise, not generate new experiments."
        case .waitWatch:
            return "A passive watch is already running. Starting another would corrupt attribution."
        case .cooldown(let time):
            return "The last watch already produced evidence. Earliest useful next action: \(time)."
        case .engine:
            return "The forever monitor engine owns passive research. Your workload is zero unless a manual exposure exists."
        case .refresh:
            return "The market state is stale or missing. One fresh sample is useful before any new watch."
        case .watch:
            return "A bounded passive watch is useful. It buys information; it does not spend BTC."
        case .review:
            return "A stricter manual-bid signal exists. Read the report before any Braiins action."
        case .observe:
            return "No useful bid window is visible. Waiting is a valid action."
        }
    }

    var color: Color {
        switch self {
        case .load, .observe: return .secondary
        case .busy, .hold, .waitWatch, .cooldown: return .orange
        case .engine, .refresh, .watch, .review: return .green
        }
    }
}

enum ControlOwner {
    case app
    case engine
    case watch
    case cooldown(String)
    case manual
    case busy
    case loading

    static func from(_ appState: AppStatePayload?, isWorking: Bool) -> ControlOwner {
        if isWorking { return .busy }
        guard let appState else { return .loading }
        if !appState.operatorState.activeManualPositions.isEmpty { return .manual }
        if appState.operatorState.activeWatch != nil { return .watch }
        if appState.engineStatus.running { return .engine }
        if let watch = appState.operatorState.completedWatch { return .cooldown(watch.earliestActionLocal) }
        return .app
    }

    var title: String {
        switch self {
        case .app: return "The app is ready"
        case .engine: return "Forever engine"
        case .watch: return "Watch run"
        case .cooldown: return "Cooldown"
        case .manual: return "Manual exposure"
        case .busy: return "Current operation"
        case .loading: return "Loading"
        }
    }

    var detail: String {
        switch self {
        case .app:
            return "No active watch, no cooldown block, and no manual exposure. Use the enabled action."
        case .engine:
            return "The background monitor engine waits, samples, writes reports, and resumes after restarts when you start it again."
        case .watch:
            return "A passive watch owns the research window. Wait for its report."
        case .cooldown(let time):
            return "The latest report owns the next decision. Wait until \(time)."
        case .manual:
            return "A real-money exposure is active. Close it only after the Braiins/OCEAN position is actually finished."
        case .busy:
            return "A backend operation is running. The safe action is to wait."
        case .loading:
            return "The app is reading local state."
        }
    }

    var symbol: String {
        switch self {
        case .app: return "scope"
        case .engine: return "dot.radiowaves.left.and.right"
        case .watch: return "binoculars"
        case .cooldown: return "timer"
        case .manual: return "lock.shield"
        case .busy: return "gearshape.2"
        case .loading: return "questionmark.circle"
        }
    }
}

enum ResearchPhase {
    case loading
    case refresh
    case watch
    case cooldown
    case manual
    case adapt

    static func from(_ appState: AppStatePayload?) -> ResearchPhase {
        guard let state = appState?.operatorState else { return .loading }
        if !state.activeManualPositions.isEmpty { return .manual }
        if state.activeWatch != nil { return .watch }
        if state.completedWatch != nil { return .cooldown }
        if !state.hasOcean || !state.hasMarket || !state.isFresh { return .refresh }
        if state.action == "manual_canary" { return .watch }
        return .adapt
    }

    var title: String {
        switch self {
        case .loading: return "Loading"
        case .refresh: return "Sense"
        case .watch: return "Watch"
        case .cooldown: return "Mature"
        case .manual: return "Hold"
        case .adapt: return "Adapt"
        }
    }

    var symbol: String {
        switch self {
        case .loading: return "questionmark"
        case .refresh: return "antenna.radiowaves.left.and.right"
        case .watch: return "binoculars"
        case .cooldown: return "hourglass"
        case .manual: return "lock.shield"
        case .adapt: return "slider.horizontal.3"
        }
    }

    var index: Int {
        switch self {
        case .loading, .refresh: return 0
        case .watch: return 2
        case .cooldown, .manual: return 3
        case .adapt: return 4
        }
    }
}

struct AppStatePayload: Codable {
    let generatedAt: String
    let operatorState: OperatorStatePayload
    let automationPlan: AutomationPlanPayload
    let engineStatus: EngineStatusPayload
    let config: ConfigPayload
    let cockpit: String
    let latest: LatestPayload

    enum CodingKeys: String, CodingKey {
        case generatedAt = "generated_at"
        case operatorState = "operator_state"
        case automationPlan = "automation_plan"
        case engineStatus = "engine_status"
        case config
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

struct EngineStatusPayload: Codable {
    let running: Bool
    let pid: Int?
    let detail: String
    let logPath: String

    enum CodingKeys: String, CodingKey {
        case running
        case pid
        case detail
        case logPath = "log_path"
    }
}

struct LatestPayload: Codable {
    let ocean: [String: LooseString]?
    let market: [String: LooseString]?
    let proposal: [String: LooseString]?
}

struct ConfigPayload: Codable {
    let capital: [String: LooseString]?
    let ocean: [String: LooseString]?
    let guardrails: [String: LooseString]?
    let strategy: [String: LooseString]?

    func value(_ section: String, _ key: String) -> String? {
        switch section {
        case "capital": return capital?[key]?.description
        case "ocean": return ocean?[key]?.description
        case "guardrails": return guardrails?[key]?.description
        case "strategy": return strategy?[key]?.description
        default: return nil
        }
    }
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
            description = bool ? "true" : "false"
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

func sats(_ btcText: String) -> String {
    guard let btc = Double(btcText) else { return "n/a" }
    let sats = Int((btc * 100_000_000).rounded())
    return "\(sats) sats"
}

func phText(_ ehText: String) -> String {
    guard let eh = Double(ehText) else { return "n/a" }
    return String(format: "%.3f", eh * 1000)
}

enum AppIconFactory {
    static func makeIcon(size: CGFloat = 512) -> NSImage {
        let image = NSImage(size: NSSize(width: size, height: size))
        image.lockFocus()

        let rect = NSRect(x: 0, y: 0, width: size, height: size)
        let corner = size * 0.22
        let path = NSBezierPath(
            roundedRect: rect.insetBy(dx: size * 0.04, dy: size * 0.04),
            xRadius: corner,
            yRadius: corner
        )
        NSGradient(
            colors: [
                NSColor(red: 0.02, green: 0.08, blue: 0.09, alpha: 1),
                NSColor(red: 0.03, green: 0.30, blue: 0.26, alpha: 1),
                NSColor(red: 0.70, green: 0.95, blue: 0.48, alpha: 1)
            ]
        )?.draw(in: path, angle: -35)

        NSColor.white.withAlphaComponent(0.20).setStroke()
        path.lineWidth = size * 0.012
        path.stroke()

        let ringRect = rect.insetBy(dx: size * 0.18, dy: size * 0.18)
        let ring = NSBezierPath(ovalIn: ringRect)
        NSColor(red: 0.78, green: 1.0, blue: 0.72, alpha: 0.24).setFill()
        ring.fill()

        let core = NSBezierPath(ovalIn: rect.insetBy(dx: size * 0.31, dy: size * 0.31))
        NSColor(red: 0.01, green: 0.06, blue: 0.07, alpha: 0.88).setFill()
        core.fill()

        let ratchet = NSBezierPath()
        let teeth = 12
        let center = NSPoint(x: size * 0.5, y: size * 0.5)
        for index in 0..<(teeth * 2) {
            let angle = (Double(index) / Double(teeth * 2)) * Double.pi * 2
            let radius = size * (index.isMultiple(of: 2) ? 0.26 : 0.19)
            let point = NSPoint(
                x: center.x + CGFloat(cos(angle)) * radius,
                y: center.y + CGFloat(sin(angle)) * radius
            )
            if index == 0 {
                ratchet.move(to: point)
            } else {
                ratchet.line(to: point)
            }
        }
        ratchet.close()
        NSColor(red: 0.94, green: 0.77, blue: 0.33, alpha: 0.96).setFill()
        ratchet.fill()

        let arrow = NSBezierPath()
        arrow.move(to: NSPoint(x: size * 0.42, y: size * 0.48))
        arrow.line(to: NSPoint(x: size * 0.61, y: size * 0.66))
        arrow.line(to: NSPoint(x: size * 0.64, y: size * 0.51))
        arrow.line(to: NSPoint(x: size * 0.77, y: size * 0.54))
        arrow.line(to: NSPoint(x: size * 0.58, y: size * 0.77))
        arrow.line(to: NSPoint(x: size * 0.36, y: size * 0.60))
        arrow.close()
        NSColor(red: 0.74, green: 1.0, blue: 0.72, alpha: 0.95).setFill()
        arrow.fill()

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
            let result = runProcess(repoRoot: repoRoot, arguments: [script, "app-state"])
            guard result.status == 0 else {
                return .failure(result.text)
            }

            guard let data = result.text.data(using: .utf8) else {
                return .failure("App-state returned non-UTF8 output.")
            }

            do {
                return .success(try JSONDecoder().decode(AppStatePayload.self, from: data))
            } catch {
                return .failure("""
                Could not decode native app state.

                Decode error: \(error.localizedDescription)

                Output:
                \(result.text)
                """)
            }
        }.value
    }

    static func run(arguments: [String]) async -> String {
        await Task.detached {
            guard let repoRoot = findRepoRoot() else {
                return repoNotFoundMessage
            }
            let script = repoRoot.appendingPathComponent("scripts/ratchet").path
            let result = runProcess(repoRoot: repoRoot, arguments: [script] + arguments)
            return result.text.isEmpty ? "Operation finished with no output." : result.text
        }.value
    }

    private static func runProcess(repoRoot: URL, arguments: [String]) -> (status: Int32, text: String) {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", arguments.map(shellQuote).joined(separator: " ")]
        process.currentDirectoryURL = repoRoot

        let outputPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = outputPipe

        do {
            try process.run()
            process.waitUntilExit()
            let data = outputPipe.fileHandleForReading.readDataToEndOfFile()
            let text = String(data: data, encoding: .utf8) ?? ""
            return (process.terminationStatus, text)
        } catch {
            return (1, "Failed to run backend operation: \(error.localizedDescription)")
        }
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
