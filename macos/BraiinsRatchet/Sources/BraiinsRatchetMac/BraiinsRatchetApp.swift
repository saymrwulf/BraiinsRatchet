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
            FlightDeckApp()
                .frame(minWidth: 1240, minHeight: 820)
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
    @Published var query = ""
    @Published var manualDescription = ""
    @Published var maturityHours = "72"
    @Published var closePositionId = ""

    var isWorking: Bool { operation != nil }

    func refresh() async {
        operation = "Refreshing"
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

    func writeRealitySnapshot(section: AppSection?) {
        let reality = RenderedReality.make(
            section: section ?? .deck,
            appState: appState,
            isWorking: isWorking,
            operation: operation,
            errorMessage: errorMessage
        )
        RealitySnapshotWriter.write(reality)
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

struct FlightDeckApp: View {
    @StateObject private var store = RatchetStore()
    @State private var selection: AppSection? = .deck
    @State private var pulse = false

    var body: some View {
        root
            .task {
                await store.refresh()
                store.writeRealitySnapshot(section: selection)
            }
            .onAppear {
                withAnimation(.easeInOut(duration: 4.8).repeatForever(autoreverses: true)) {
                    pulse = true
                }
            }
            .onChange(of: selection) { _, newValue in
                store.writeRealitySnapshot(section: newValue)
            }
            .onChange(of: store.appState?.generatedAt) { _, _ in
                store.writeRealitySnapshot(section: selection)
            }
            .onChange(of: store.operation) { _, _ in
                store.writeRealitySnapshot(section: selection)
            }
    }

    private var root: some View {
        NavigationSplitView {
            LiquidSidebar(selection: $selection, store: store)
                .backgroundExtensionEffect()
        } detail: {
            detail
        }
    }

    private var detail: some View {
        ZStack {
            HashfieldBackdrop(pulse: pulse)
            selectedView
                .safeAreaPadding(.horizontal, 30)
                .safeAreaPadding(.vertical, 24)
            VStack {
                Spacer()
                HStack {
                    Spacer()
                    RealityHUD(store: store, section: selection ?? .deck) {
                        selection = .mirror
                    }
                    .padding(.trailing, 24)
                    .padding(.bottom, 20)
                }
            }
        }
        .toolbar { toolbarContent }
        .searchable(text: $store.query, placement: .toolbar, prompt: "Search reports, prices, OCEAN, Braiins")
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem {
            Button {
                Task { await store.refresh() }
            } label: {
                Label("Refresh", systemImage: "arrow.clockwise")
            }
            .buttonStyle(.glass)
            .disabled(store.isWorking)
        }

        ToolbarItem {
            engineToolbarButton
        }
    }

    @ViewBuilder
    private var engineToolbarButton: some View {
        if store.appState?.engineStatus.running == true {
            Button {
                Task { await store.stopEngine() }
            } label: {
                Label("Stop Engine", systemImage: "stop.circle")
            }
            .buttonStyle(.glass)
            .tint(.orange)
            .disabled(store.isWorking)
        } else {
            Button {
                Task { await store.startEngine() }
            } label: {
                Label("Start Engine", systemImage: "dot.radiowaves.left.and.right")
            }
            .buttonStyle(.glassProminent)
            .tint(.green)
            .disabled(store.isWorking)
        }
    }

    @ViewBuilder
    private var selectedView: some View {
        switch selection ?? .deck {
        case .deck:
            FlightDeckView(store: store, pulse: pulse)
        case .hashflow:
            HashflowView(store: store)
        case .ratchet:
            RatchetMapView(store: store)
        case .bidlab:
            BidLabView(store: store)
        case .exposure:
            ExposureView(store: store)
        case .vault:
            EvidenceVaultView(store: store)
        case .mirror:
            RealityMirrorView(store: store, section: selection ?? .mirror)
        }
    }
}

enum AppSection: String, CaseIterable, Identifiable {
    case deck
    case hashflow
    case ratchet
    case bidlab
    case exposure
    case vault
    case mirror

    var id: String { rawValue }

    var title: String {
        switch self {
        case .deck: "Flight Deck"
        case .hashflow: "Hashflow"
        case .ratchet: "Ratchet"
        case .bidlab: "Bid Lab"
        case .exposure: "Exposure"
        case .vault: "Evidence"
        case .mirror: "Reality Mirror"
        }
    }

    var subtitle: String {
        switch self {
        case .deck: "decision and control"
        case .hashflow: "Braiins to OCEAN"
        case .ratchet: "autoresearch path"
        case .bidlab: "shadow order optics"
        case .exposure: "manual position lock"
        case .vault: "reports and raw state"
        case .mirror: "BED: app sees itself"
        }
    }

    var symbol: String {
        switch self {
        case .deck: "sparkles.rectangle.stack"
        case .hashflow: "point.3.connected.trianglepath.dotted"
        case .ratchet: "arrow.triangle.2.circlepath"
        case .bidlab: "slider.horizontal.3"
        case .exposure: "lock.shield"
        case .vault: "archivebox"
        case .mirror: "eye.square"
        }
    }
}

struct LiquidSidebar: View {
    @Binding var selection: AppSection?
    @ObservedObject var store: RatchetStore

    var body: some View {
        VStack(spacing: 14) {
            HStack(spacing: 12) {
                Image(nsImage: AppIconFactory.makeIcon(size: 42))
                    .resizable()
                    .frame(width: 42, height: 42)
                    .clipShape(RoundedRectangle(cornerRadius: 13, style: .continuous))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Ratchet")
                        .font(.title3.weight(.black))
                    Text(store.appState?.engineStatus.running == true ? "engine live" : "engine idle")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(store.appState?.engineStatus.running == true ? .green : .secondary)
                }
                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.top, 18)

            List(AppSection.allCases, selection: $selection) { item in
                NavigationLink(value: item) {
                    Label {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(item.title)
                                .font(.headline)
                            Text(item.subtitle)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    } icon: {
                        Image(systemName: item.symbol)
                            .symbolRenderingMode(.monochrome)
                    }
                    .padding(.vertical, 5)
                }
                .tag(item as AppSection?)
            }
            .scrollContentBackground(.hidden)

            Spacer(minLength: 0)

            LiquidGlassSurface(tint: store.appState?.engineStatus.running == true ? .green : .white.opacity(0.08), cornerRadius: 24) {
                VStack(alignment: .leading, spacing: 10) {
                    Label("Real-money safe", systemImage: "hand.raised.fill")
                        .font(.headline)
                    Text("Monitor-only. Owner-token execution is not implemented.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let operation = store.operation {
                        ProgressView(operation)
                            .controlSize(.small)
                    }
                }
                .padding(14)
            }
            .padding(12)
        }
        .navigationTitle("")
    }
}

struct FlightDeckView: View {
    @ObservedObject var store: RatchetStore
    let pulse: Bool

    private var decision: Decision { Decision.from(store.appState, isWorking: store.isWorking) }

    var body: some View {
        GeometryReader { proxy in
            HStack(spacing: 26) {
                VStack(alignment: .leading, spacing: 18) {
                    LiquidTitleBlock(
                        eyebrow: "Braiins Ratchet Flight Deck",
                        title: decision.title,
                        subtitle: decision.explanation,
                        color: decision.color
                    )

                    GlassEffectContainer(spacing: 14) {
                        HStack(spacing: 14) {
                            DecisionPuck(title: "control", value: controlOwner.title, detail: controlOwner.detail, symbol: controlOwner.symbol, tint: decision.color)
                            DecisionPuck(title: "next", value: nextTitle, detail: nextDetail, symbol: "arrow.forward.circle", tint: .cyan)
                        }
                    }

                    InstrumentRibbon(appState: store.appState)

                    EngineConsole(store: store)
                }
                .frame(width: max(430, proxy.size.width * 0.38))

                ReactorLens(appState: store.appState, decision: decision, pulse: pulse)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private var controlOwner: ControlOwner {
        ControlOwner.from(store.appState, isWorking: store.isWorking)
    }

    private var nextTitle: String {
        guard let state = store.appState else { return "Load state" }
        if state.engineStatus.running { return "Engine owns it" }
        if state.operatorState.activeWatch != nil { return "Wait for watch" }
        if let watch = state.operatorState.completedWatch { return "Wait \(watch.remainingMinutes)m" }
        if !state.operatorState.activeManualPositions.isEmpty { return "Hold exposure" }
        return state.automationPlan.title
    }

    private var nextDetail: String {
        guard let state = store.appState else { return "Reading durable SQLite state." }
        if state.engineStatus.running { return "No babysitting. The background engine waits, samples, watches, and writes evidence." }
        if let watch = state.operatorState.completedWatch { return "Earliest useful action: \(watch.earliestActionLocal)." }
        return state.automationPlan.steps.first ?? "No passive action is useful right now."
    }
}

struct LiquidTitleBlock: View {
    let eyebrow: String
    let title: String
    let subtitle: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(eyebrow)
                .font(.caption.weight(.heavy))
                .textCase(.uppercase)
                .foregroundStyle(.secondary)
                .tracking(1.6)
            Text(title)
                .font(.system(size: 78, weight: .black, design: .rounded))
                .foregroundStyle(
                    LinearGradient(colors: [color, .white.opacity(0.92)], startPoint: .topLeading, endPoint: .bottomTrailing)
                )
                .shadow(color: color.opacity(0.45), radius: 24, x: 0, y: 12)
            Text(subtitle)
                .font(.title2.weight(.semibold))
                .foregroundStyle(.primary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct DecisionPuck: View {
    let title: String
    let value: String
    let detail: String
    let symbol: String
    let tint: Color

    var body: some View {
        LiquidGlassSurface(tint: tint.opacity(0.22), cornerRadius: 30) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Label(title, systemImage: symbol)
                        .font(.caption.weight(.heavy))
                        .textCase(.uppercase)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
                Text(value)
                    .font(.title.weight(.black))
                    .lineLimit(2)
                Text(detail)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .lineLimit(4)
            }
            .padding(18)
        }
    }
}

struct EngineConsole: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        LiquidGlassSurface(tint: store.appState?.engineStatus.running == true ? .green.opacity(0.28) : .blue.opacity(0.14), cornerRadius: 36) {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Forever Engine")
                            .font(.title2.weight(.black))
                        Text(store.appState?.engineStatus.detail ?? "Loading engine state")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    EngineBeacon(running: store.appState?.engineStatus.running == true)
                }

                HStack(spacing: 12) {
                    Button {
                        Task { await store.startEngine() }
                    } label: {
                        Label("Start Forever Engine", systemImage: "dot.radiowaves.left.and.right")
                    }
                    .buttonStyle(.glassProminent)
                    .tint(.green)
                    .disabled(store.appState?.engineStatus.running == true || store.isWorking)

                    Button {
                        Task { await store.stopEngine() }
                    } label: {
                        Label("Stop", systemImage: "stop.circle")
                    }
                    .buttonStyle(.glass)
                    .tint(.orange)
                    .disabled(store.appState?.engineStatus.running != true || store.isWorking)

                    Button {
                        Task { await store.runOneFreshSample() }
                    } label: {
                        Label("One Sample", systemImage: "camera.metering.center.weighted")
                    }
                    .buttonStyle(.glass)
                    .disabled(store.isWorking)
                }
            }
            .padding(20)
        }
    }
}

struct ReactorLens: View {
    let appState: AppStatePayload?
    let decision: Decision
    let pulse: Bool

    var body: some View {
        ZStack {
            LensRings(color: decision.color, pulse: pulse)

            HashflowPath()
                .padding(70)

            VStack(spacing: 12) {
                Text(decision.title)
                    .font(.system(size: 40, weight: .black, design: .rounded))
                    .foregroundStyle(decision.color)
                Text(centerMetric)
                    .font(.system(size: 24, weight: .bold, design: .monospaced))
                    .foregroundStyle(.primary)
                Text("expected net")
                    .font(.caption.weight(.heavy))
                    .textCase(.uppercase)
                    .foregroundStyle(.secondary)
            }
            .padding(28)
            .glassEffect(.regular.tint(decision.color.opacity(0.25)).interactive(), in: Circle())
        }
        .frame(minHeight: 620)
        .accessibilityLabel("Mining reactor lens, current decision \(decision.title)")
    }

    private var centerMetric: String {
        sats(appState?.latest.proposal?["expected_net_btc"]?.description ?? "n/a")
    }
}

struct LensRings: View {
    let color: Color
    let pulse: Bool

    var body: some View {
        ZStack {
            ForEach(0..<6) { index in
                Circle()
                    .stroke(
                        AngularGradient(
                            colors: [
                                color.opacity(0.04),
                                .cyan.opacity(0.45),
                                .green.opacity(0.60),
                                .orange.opacity(0.42),
                                color.opacity(0.04)
                            ],
                            center: .center
                        ),
                        lineWidth: CGFloat(max(2, 14 - index * 2))
                    )
                    .frame(width: CGFloat(230 + index * 76), height: CGFloat(230 + index * 76))
                    .rotationEffect(.degrees(pulse ? Double(index * 16 + 38) : Double(-index * 12)))
                    .opacity(0.86 - Double(index) * 0.09)
            }

            Circle()
                .fill(RadialGradient(colors: [color.opacity(0.20), .clear], center: .center, startRadius: 30, endRadius: 360))
                .blur(radius: 8)
        }
    }
}

struct HashflowPath: View {
    private let nodes = [
        FlowNode("Braiins", "bid market", .green, CGPoint(x: 0.15, y: 0.30), "bitcoinsign.circle"),
        FlowNode("Hashers", "sub workers", .cyan, CGPoint(x: 0.35, y: 0.62), "bolt.horizontal"),
        FlowNode("OCEAN", "pool window", .blue, CGPoint(x: 0.62, y: 0.35), "water.waves"),
        FlowNode("Blocks", "luck", .orange, CGPoint(x: 0.82, y: 0.58), "cube.transparent")
    ]

    var body: some View {
        GeometryReader { proxy in
            Canvas { context, size in
                var path = Path()
                let points = nodes.map { CGPoint(x: $0.position.x * size.width, y: $0.position.y * size.height) }
                guard let first = points.first else { return }
                path.move(to: first)
                for index in 1..<points.count {
                    let previous = points[index - 1]
                    let current = points[index]
                    let c1 = CGPoint(x: previous.x + 120, y: previous.y - 60)
                    let c2 = CGPoint(x: current.x - 120, y: current.y + 60)
                    path.addCurve(to: current, control1: c1, control2: c2)
                }
                context.stroke(path, with: .linearGradient(
                    Gradient(colors: [.green.opacity(0.85), .cyan.opacity(0.85), .orange.opacity(0.85)]),
                    startPoint: CGPoint(x: 0, y: 0),
                    endPoint: CGPoint(x: size.width, y: size.height)
                ), style: StrokeStyle(lineWidth: 5, lineCap: .round, dash: [14, 10]))
            }

            ForEach(nodes) { node in
                FlowNodeView(node: node)
                    .position(x: node.position.x * proxy.size.width, y: node.position.y * proxy.size.height)
            }
        }
    }
}

struct FlowNode: Identifiable {
    let id = UUID()
    let title: String
    let subtitle: String
    let color: Color
    let position: CGPoint
    let symbol: String

    init(_ title: String, _ subtitle: String, _ color: Color, _ position: CGPoint, _ symbol: String) {
        self.title = title
        self.subtitle = subtitle
        self.color = color
        self.position = position
        self.symbol = symbol
    }
}

struct FlowNodeView: View {
    let node: FlowNode

    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: node.symbol)
                .font(.title2.weight(.bold))
            Text(node.title)
                .font(.headline)
            Text(node.subtitle)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(width: 112, height: 92)
        .glassEffect(.regular.tint(node.color.opacity(0.26)).interactive(), in: RoundedRectangle(cornerRadius: 28, style: .continuous))
    }
}

struct InstrumentRibbon: View {
    let appState: AppStatePayload?

    var body: some View {
        GlassEffectContainer(spacing: 12) {
            HStack(spacing: 12) {
                InstrumentChip("Braiins", market("fillable_price_btc_per_eh_day", fallback: market("best_ask_btc_per_eh_day")), "BTC/EH/day", "chart.line.uptrend.xyaxis", .green)
                InstrumentChip("OCEAN", "\(ocean("pool_hashrate_eh_s"))", "EH/s pool", "water.waves", .cyan)
                InstrumentChip("Window", ocean("avg_block_time_hours"), "h/block avg", "hourglass", .orange)
                InstrumentChip("Net", sats(proposal("expected_net_btc")), "model EV", "plus.forwardslash.minus", .pink)
            }
        }
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

struct InstrumentChip: View {
    let title: String
    let value: String
    let unit: String
    let symbol: String
    let color: Color

    init(_ title: String, _ value: String, _ unit: String, _ symbol: String, _ color: Color) {
        self.title = title
        self.value = value
        self.unit = unit
        self.symbol = symbol
        self.color = color
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: symbol)
                .font(.caption.weight(.heavy))
                .textCase(.uppercase)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title3.monospacedDigit().weight(.black))
                .lineLimit(1)
            Text(unit)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassEffect(.regular.tint(color.opacity(0.18)).interactive(), in: RoundedRectangle(cornerRadius: 24, style: .continuous))
    }
}

struct HashflowView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                SectionHeader("Hashflow", "The real system: Braiins buys temporary workers; your Umbrel/Knots/Datum path routes sovereign mining; OCEAN decides payout variance.")
                LiquidGlassSurface(tint: .cyan.opacity(0.14), cornerRadius: 40) {
                    HStack(spacing: 24) {
                        FlowLane(title: "Your node path", tint: .cyan, steps: [
                            ("Umbrel", "operator host", "house"),
                            ("Knots", "validates rules", "checkmark.seal"),
                            ("Datum", "template/routing", "point.3.connected.trianglepath.dotted"),
                            ("OCEAN", "share window", "water.waves")
                        ])
                        FlowLane(title: "Bought hashpower path", tint: .green, steps: [
                            ("Braiins", "spot hashmarket", "bitcoinsign.circle"),
                            ("Hashers", "temporary workers", "bolt.horizontal"),
                            ("OCEAN", "same pool", "water.waves"),
                            ("Blocks", "stochastic payout", "cube.transparent")
                        ])
                    }
                    .padding(24)
                }
                InstrumentRibbon(appState: store.appState)
            }
        }
    }
}

struct FlowLane: View {
    let title: String
    let tint: Color
    let steps: [(String, String, String)]

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(title)
                .font(.title2.weight(.black))
            ForEach(Array(steps.enumerated()), id: \.offset) { index, step in
                HStack(spacing: 14) {
                    Image(systemName: step.2)
                        .font(.title3.weight(.bold))
                        .frame(width: 42, height: 42)
                        .glassEffect(.regular.tint(tint.opacity(0.25)), in: Circle())
                    VStack(alignment: .leading) {
                        Text(step.0)
                            .font(.headline)
                        Text(step.1)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if index < steps.count - 1 {
                        Image(systemName: "arrow.down")
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(12)
                .background(.black.opacity(0.12), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            }
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

struct RatchetMapView: View {
    @ObservedObject var store: RatchetStore

    private let stages = [
        ("Sense", "collect live OCEAN and Braiins data", "antenna.radiowaves.left.and.right"),
        ("Price", "model executable depth", "chart.line.uptrend.xyaxis"),
        ("Watch", "measure without spending", "binoculars"),
        ("Mature", "respect pool variance", "hourglass"),
        ("Adapt", "change one knob", "slider.horizontal.3")
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                SectionHeader("Ratchet", "The learning wheel is the product. It prevents loop-chasing and forces every bid idea to earn its next step.")
                LiquidGlassSurface(tint: .green.opacity(0.14), cornerRadius: 44) {
                    HStack(spacing: 0) {
                        ForEach(Array(stages.enumerated()), id: \.offset) { index, stage in
                            RatchetStage(index: index, active: index == ResearchPhase.from(store.appState).index, done: index < ResearchPhase.from(store.appState).index, title: stage.0, text: stage.1, symbol: stage.2)
                            if index < stages.count - 1 {
                                Rectangle()
                                    .fill(index < ResearchPhase.from(store.appState).index ? .green.opacity(0.7) : .white.opacity(0.14))
                                    .frame(height: 4)
                            }
                        }
                    }
                    .padding(24)
                }
                HStack(spacing: 16) {
                    ForecastCapsule("Immediate", immediateForecast, .green)
                    ForecastCapsule("Midterm", "Compare the next fresh state against the last evidence artifact.", .cyan)
                    ForecastCapsule("Longterm", "Only repeated mature reports can justify changing one bid knob.", .orange)
                }
            }
        }
    }

    private var immediateForecast: String {
        if let watch = store.appState?.operatorState.completedWatch {
            return "Wait \(watch.remainingMinutes)m. Earliest action \(watch.earliestActionLocal)."
        }
        if store.appState?.engineStatus.running == true { return "Engine owns passive observation." }
        return store.appState?.automationPlan.steps.first ?? "Load state."
    }
}

struct RatchetStage: View {
    let index: Int
    let active: Bool
    let done: Bool
    let title: String
    let text: String
    let symbol: String

    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: symbol)
                .font(.title2.weight(.bold))
                .frame(width: 62, height: 62)
                .glassEffect(.regular.tint(tint.opacity(0.35)).interactive(), in: Circle())
            Text(title)
                .font(.headline)
            Text(text)
                .font(.caption)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
        }
        .frame(width: 142)
        .scaleEffect(active ? 1.08 : 1)
        .animation(.spring(response: 0.35, dampingFraction: 0.82), value: active)
    }

    private var tint: Color {
        active ? .orange : (done ? .green : .white.opacity(0.18))
    }
}

struct ForecastCapsule: View {
    let title: String
    let text: String
    let color: Color

    init(_ title: String, _ text: String, _ color: Color) {
        self.title = title
        self.text = text
        self.color = color
    }

    var body: some View {
        LiquidGlassSurface(tint: color.opacity(0.16), cornerRadius: 30) {
            VStack(alignment: .leading, spacing: 10) {
                Text(title)
                    .font(.title3.weight(.black))
                Text(text)
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
            .padding(18)
        }
    }
}

struct BidLabView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                SectionHeader("Bid Lab", "A shadow order desk. It can tell you what it would study; it cannot spend BTC.")
                HStack(alignment: .top, spacing: 18) {
                    ShadowTicket(appState: store.appState)
                    LossLens(appState: store.appState)
                }
                LiquidGlassSurface(tint: .orange.opacity(0.12), cornerRadius: 36) {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Hard truth", systemImage: "exclamationmark.triangle")
                            .font(.title2.weight(.black))
                        Text(store.appState?.latest.proposal?["reason"]?.description ?? "No proposal loaded.")
                            .font(.title3.weight(.semibold))
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(22)
                }
            }
        }
    }
}

struct ShadowTicket: View {
    let appState: AppStatePayload?

    var body: some View {
        LiquidGlassSurface(tint: actionColor.opacity(0.22), cornerRadius: 38) {
            VStack(alignment: .leading, spacing: 16) {
                Label("Shadow ticket", systemImage: "ticket")
                    .font(.title2.weight(.black))
                Text(actionTitle)
                    .font(.system(size: 42, weight: .black, design: .rounded))
                    .foregroundStyle(actionColor)
                ValueGrid(rows: [
                    ("price", proposal("order_price_btc_per_eh_day"), "BTC/EH/day"),
                    ("spend", proposal("order_spend_btc"), "BTC"),
                    ("duration", proposal("order_duration_minutes"), "min"),
                    ("speed", phText(proposal("order_implied_hashrate_eh_s")), "PH/s")
                ])
            }
            .padding(24)
        }
    }

    private var actionTitle: String {
        switch proposal("action") {
        case "manual_bid": "manual review"
        case "manual_canary": "learning canary"
        case "observe": "observe"
        default: "no proposal"
        }
    }

    private var actionColor: Color {
        switch proposal("action") {
        case "manual_bid": .green
        case "manual_canary": .orange
        default: .secondary
        }
    }

    private func proposal(_ key: String) -> String {
        appState?.latest.proposal?[key]?.description ?? "n/a"
    }
}

struct LossLens: View {
    let appState: AppStatePayload?

    var body: some View {
        LiquidGlassSurface(tint: netColor.opacity(0.20), cornerRadius: 38) {
            VStack(alignment: .leading, spacing: 16) {
                Label("Loss lens", systemImage: "shield.lefthalf.filled")
                    .font(.title2.weight(.black))
                Text(sats(proposal("expected_net_btc")))
                    .font(.system(size: 42, weight: .black, design: .rounded))
                    .foregroundStyle(netColor)
                ValueGrid(rows: [
                    ("reward", proposal("expected_reward_btc"), "BTC"),
                    ("net", proposal("expected_net_btc"), "BTC"),
                    ("breakeven", proposal("breakeven_btc_per_eh_day"), "BTC/EH/day"),
                    ("budget", config("guardrails", "max_canary_expected_loss_btc"), "BTC")
                ])
            }
            .padding(24)
        }
    }

    private var netColor: Color {
        (Double(proposal("expected_net_btc")) ?? 0) >= 0 ? .green : .orange
    }

    private func proposal(_ key: String) -> String {
        appState?.latest.proposal?[key]?.description ?? "n/a"
    }

    private func config(_ section: String, _ key: String) -> String {
        appState?.config.value(section, key) ?? "n/a"
    }
}

struct ValueGrid: View {
    let rows: [(String, String, String)]

    var body: some View {
        Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 10) {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, row in
                GridRow {
                    Text(row.0)
                        .foregroundStyle(.secondary)
                    Text(row.1)
                        .font(.body.monospacedDigit().weight(.semibold))
                    Text(row.2)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}

struct ExposureView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                SectionHeader("Exposure Lock", "When you manually place a Braiins order, record it. The app then blocks new experiments until you close the position.")
                HStack(alignment: .top, spacing: 18) {
                    LiquidGlassSurface(tint: .green.opacity(0.12), cornerRadius: 34) {
                        VStack(alignment: .leading, spacing: 14) {
                            Label("Record manual order", systemImage: "plus.circle")
                                .font(.title2.weight(.black))
                            TextField("Braiins order, spend, duration, target pool", text: $store.manualDescription)
                                .textFieldStyle(.roundedBorder)
                            TextField("Maturity hours", text: $store.maturityHours)
                                .textFieldStyle(.roundedBorder)
                                .frame(width: 170)
                            Button("Record Exposure") {
                                Task { await store.recordManualExposure() }
                            }
                            .buttonStyle(.glassProminent)
                            .tint(.green)
                            .disabled(store.isWorking)
                        }
                        .padding(22)
                    }
                    LiquidGlassSurface(tint: .orange.opacity(0.12), cornerRadius: 34) {
                        VStack(alignment: .leading, spacing: 14) {
                            Label("Close finished order", systemImage: "checkmark.circle")
                                .font(.title2.weight(.black))
                            TextField("Position ID", text: $store.closePositionId)
                                .textFieldStyle(.roundedBorder)
                                .frame(width: 170)
                            Button("Close Exposure") {
                                Task { await store.closeManualExposure() }
                            }
                            .buttonStyle(.glass)
                            .tint(.orange)
                            .disabled(store.isWorking)
                        }
                        .padding(22)
                    }
                }
                LiquidGlassSurface(tint: .white.opacity(0.08), cornerRadius: 34) {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Active exposure", systemImage: "lock.shield")
                            .font(.title2.weight(.black))
                        if let positions = store.appState?.operatorState.activeManualPositions, !positions.isEmpty {
                            ForEach(positions, id: \.self) { position in
                                Text(position)
                                    .font(.body.monospaced())
                                    .textSelection(.enabled)
                            }
                        } else {
                            Text("No manual exposure is active.")
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(22)
                }
            }
        }
    }
}

struct EvidenceVaultView: View {
    @ObservedObject var store: RatchetStore

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .bottom) {
                SectionHeader("Evidence", "Audit trail, raw reports, and diagnostics. This is intentionally not the main UX.")
                Spacer()
                Button("Cockpit") { Task { await store.showCockpit() } }
                    .buttonStyle(.glass)
                Button("Report") { Task { await store.showReport() } }
                    .buttonStyle(.glass)
                Button("Ledger") { Task { await store.showLedger() } }
                    .buttonStyle(.glass)
            }
            LiquidGlassSurface(tint: .white.opacity(0.08), cornerRadius: 34) {
                VStack(alignment: .leading, spacing: 12) {
                    Label(store.rawTitle, systemImage: "archivebox")
                        .font(.title2.weight(.black))
                    ScrollView {
                        Text(store.rawText)
                            .font(.body.monospaced())
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .textSelection(.enabled)
                    }
                }
                .padding(22)
            }
        }
    }
}

struct RealityHUD: View {
    @ObservedObject var store: RatchetStore
    let section: AppSection
    let openMirror: () -> Void

    private var reality: RenderedReality {
        RenderedReality.make(
            section: section,
            appState: store.appState,
            isWorking: store.isWorking,
            operation: store.operation,
            errorMessage: store.errorMessage
        )
    }

    var body: some View {
        LiquidGlassSurface(tint: .white.opacity(0.10), cornerRadius: 24) {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Label("Reality Mirror", systemImage: "eye")
                        .font(.caption.weight(.heavy))
                        .textCase(.uppercase)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Button("Open") {
                        openMirror()
                    }
                    .buttonStyle(.glass)
                    .controlSize(.small)
                }
                Text(reality.decisionTitle)
                    .font(.title2.weight(.black))
                    .foregroundStyle(reality.decisionTint)
                Text(reality.currentInstruction)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(3)
                Text("writes data/app_visual_state.md")
                    .font(.caption2.monospaced())
                    .foregroundStyle(.tertiary)
            }
            .padding(14)
            .frame(width: 330, alignment: .leading)
        }
        .accessibilityLabel("Reality Mirror heads-up display, current decision \(reality.decisionTitle)")
    }
}

struct RealityMirrorView: View {
    @ObservedObject var store: RatchetStore
    let section: AppSection

    private var reality: RenderedReality {
        RenderedReality.make(
            section: section,
            appState: store.appState,
            isWorking: store.isWorking,
            operation: store.operation,
            errorMessage: store.errorMessage
        )
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                SectionHeader("Reality Mirror", "BED: Backstage Evidence Deck. This is the app reflecting the concrete state it is rendering now, not generic advice.")

                HStack(alignment: .top, spacing: 18) {
                    LiquidGlassSurface(tint: reality.decisionTint.opacity(0.22), cornerRadius: 38) {
                        VStack(alignment: .leading, spacing: 14) {
                            Label("What I am showing", systemImage: "eye.fill")
                                .font(.title2.weight(.black))
                            Text(reality.decisionTitle)
                                .font(.system(size: 56, weight: .black, design: .rounded))
                                .foregroundStyle(reality.decisionTint)
                            Text(reality.decisionExplanation)
                                .font(.title3.weight(.semibold))
                                .fixedSize(horizontal: false, vertical: true)
                            Text(reality.currentInstruction)
                                .font(.callout)
                                .foregroundStyle(.secondary)
                        }
                        .padding(24)
                    }

                    LiquidGlassSurface(tint: .cyan.opacity(0.16), cornerRadius: 38) {
                        VStack(alignment: .leading, spacing: 14) {
                            Label("Snapshot artifact", systemImage: "doc.text.magnifyingglass")
                                .font(.title2.weight(.black))
                            Text("The SwiftUI app writes exactly this semantic view state into the repo.")
                                .font(.callout)
                                .foregroundStyle(.secondary)
                            Button {
                                store.writeRealitySnapshot(section: section)
                            } label: {
                                Label("Write Snapshot Now", systemImage: "square.and.arrow.down")
                            }
                            .buttonStyle(.glassProminent)
                            .tint(.cyan)
                            Text("data/app_visual_state.md\n data/app_visual_state.json")
                                .font(.body.monospaced())
                                .foregroundStyle(.secondary)
                                .textSelection(.enabled)
                        }
                        .padding(24)
                    }
                }

                LiquidGlassSurface(tint: .white.opacity(0.08), cornerRadius: 34) {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Current visible facts", systemImage: "list.bullet.rectangle")
                            .font(.title2.weight(.black))
                        ValueGrid(rows: reality.factGridRows)
                    }
                    .padding(22)
                }

                LiquidGlassSurface(tint: .green.opacity(0.12), cornerRadius: 34) {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Buttons I believe are visible", systemImage: "cursorarrow.click.2")
                            .font(.title2.weight(.black))
                        ForEach(reality.visibleButtons, id: \.self) { button in
                            Text(button)
                                .font(.body.monospaced())
                                .textSelection(.enabled)
                        }
                    }
                    .padding(22)
                }

                LiquidGlassSurface(tint: .orange.opacity(0.12), cornerRadius: 34) {
                    VStack(alignment: .leading, spacing: 14) {
                        Label("Operator truth", systemImage: "exclamationmark.shield")
                            .font(.title2.weight(.black))
                        ForEach(reality.operatorTruths, id: \.self) { truth in
                            Text(truth)
                                .font(.callout)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                    .padding(22)
                }
            }
        }
        .onAppear {
            store.writeRealitySnapshot(section: section)
        }
    }
}

struct SectionHeader: View {
    let title: String
    let subtitle: String

    init(_ title: String, _ subtitle: String) {
        self.title = title
        self.subtitle = subtitle
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.system(size: 54, weight: .black, design: .rounded))
            Text(subtitle)
                .font(.title3.weight(.semibold))
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct LiquidGlassSurface<Content: View>: View {
    let tint: Color
    let cornerRadius: CGFloat
    @ViewBuilder let content: Content

    var body: some View {
        content
            .glassEffect(.regular.tint(tint).interactive(), in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}

struct EngineBeacon: View {
    let running: Bool

    var body: some View {
        ZStack {
            Circle()
                .fill((running ? Color.green : Color.secondary).opacity(0.18))
                .frame(width: 62, height: 62)
            Image(systemName: running ? "dot.radiowaves.left.and.right" : "power")
                .font(.title2.weight(.black))
                .foregroundStyle(running ? .green : .secondary)
        }
        .glassEffect(.regular.tint((running ? Color.green : Color.secondary).opacity(0.18)), in: Circle())
    }
}

struct HashfieldBackdrop: View {
    let pulse: Bool

    var body: some View {
        TimelineView(.animation) { timeline in
            Canvas { context, size in
                let seconds = timeline.date.timeIntervalSinceReferenceDate
                let base = CGRect(origin: .zero, size: size)
                context.fill(Path(base), with: .linearGradient(
                    Gradient(colors: [
                        Color(red: 0.015, green: 0.018, blue: 0.025),
                        Color(red: 0.015, green: 0.075, blue: 0.07),
                        Color(red: 0.16, green: 0.12, blue: 0.05)
                    ]),
                    startPoint: .zero,
                    endPoint: CGPoint(x: size.width, y: size.height)
                ))

                for index in 0..<36 {
                    let t = Double(index) * 0.37 + seconds * 0.08
                    let x = (sin(t) * 0.5 + 0.5) * size.width
                    let y = (cos(t * 0.73) * 0.5 + 0.5) * size.height
                    let radius = CGFloat(28 + (index % 7) * 12)
                    let rect = CGRect(x: x - radius, y: y - radius, width: radius * 2, height: radius * 2)
                    context.fill(
                        Path(ellipseIn: rect),
                        with: .radialGradient(
                            Gradient(colors: [.green.opacity(0.10), .clear]),
                            center: CGPoint(x: x, y: y),
                            startRadius: 0,
                            endRadius: radius
                        )
                    )
                }
            }
            .overlay {
                AngularGradient(
                    colors: [.clear, .white.opacity(0.035), .clear, .green.opacity(0.06), .clear],
                    center: .center
                )
                .opacity(pulse ? 1 : 0.55)
                .animation(.easeInOut(duration: 4.8).repeatForever(autoreverses: true), value: pulse)
            }
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
        case .load: "LOAD"
        case .busy: "WORKING"
        case .hold: "HOLD"
        case .waitWatch: "WAIT"
        case .cooldown: "COOLDOWN"
        case .engine: "ENGINE LIVE"
        case .refresh: "REFRESH"
        case .watch: "WATCH"
        case .review: "REVIEW"
        case .observe: "OBSERVE"
        }
    }

    var explanation: String {
        switch self {
        case .load:
            "Reading the durable SQLite state and latest evidence."
        case .busy(let operation):
            "\(operation) is running. Do not start a competing operation."
        case .hold:
            "A real Braiins/OCEAN exposure is active. The ratchet must hold."
        case .waitWatch:
            "A passive watch already owns the research window."
        case .cooldown(let time):
            "The latest watch is evidence. Earliest useful action: \(time)."
        case .engine:
            "The background engine owns passive research. You do not babysit it."
        case .refresh:
            "The market state is stale or missing. Take one fresh sample."
        case .watch:
            "A bounded passive watch is useful. It buys information, not BTC exposure."
        case .review:
            "A stricter bid signal exists. Read evidence before any manual Braiins action."
        case .observe:
            "No useful window is visible. Waiting is valid."
        }
    }

    var color: Color {
        switch self {
        case .load, .observe: .secondary
        case .busy, .hold, .waitWatch, .cooldown: .orange
        case .engine, .refresh, .watch, .review: .green
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
        case .app: "App ready"
        case .engine: "Forever engine"
        case .watch: "Watch run"
        case .cooldown: "Cooldown"
        case .manual: "Manual exposure"
        case .busy: "Operation"
        case .loading: "Loading"
        }
    }

    var detail: String {
        switch self {
        case .app:
            "No active watch, cooldown, or manual exposure. Use the enabled action."
        case .engine:
            "The background monitor loop owns passive sampling and report writing."
        case .watch:
            "Wait for the watch report. Duplicate watches destroy attribution."
        case .cooldown(let time):
            "The latest report owns the decision until \(time)."
        case .manual:
            "Real money is active. Close only when the position is truly finished."
        case .busy:
            "A backend operation is running. Wait."
        case .loading:
            "Reading local state."
        }
    }

    var symbol: String {
        switch self {
        case .app: "scope"
        case .engine: "dot.radiowaves.left.and.right"
        case .watch: "binoculars"
        case .cooldown: "timer"
        case .manual: "lock.shield"
        case .busy: "gearshape.2"
        case .loading: "questionmark.circle"
        }
    }
}

struct RealityRow: Codable, Hashable {
    let label: String
    let value: String
    let unit: String
}

struct RenderedReality: Codable {
    let snapshotGeneratedAt: String
    let source: String
    let visibleSection: String
    let visibleSectionSubtitle: String
    let decisionTitle: String
    let decisionExplanation: String
    let controlTitle: String
    let controlDetail: String
    let nextTitle: String
    let nextDetail: String
    let currentInstruction: String
    let engineRunning: Bool
    let engineDetail: String
    let operation: String
    let errorMessage: String
    let latestStrategyAction: String
    let latestReport: String
    let activeWatch: String
    let completedWatch: String
    let activeManualExposure: String
    let braiinsFreshness: String
    let latestOceanSample: String
    let latestBraiinsSample: String
    let instrumentRows: [RealityRow]
    let visibleButtons: [String]
    let operatorTruths: [String]

    var factRows: [RealityRow] {
        [
            RealityRow(label: "visible section", value: visibleSection, unit: "screen"),
            RealityRow(label: "decision", value: decisionTitle, unit: "giant word"),
            RealityRow(label: "control", value: controlTitle, unit: "owner"),
            RealityRow(label: "next", value: nextTitle, unit: "action"),
            RealityRow(label: "engine", value: engineRunning ? "running" : "stopped", unit: "state"),
            RealityRow(label: "strategy", value: latestStrategyAction, unit: "proposal"),
            RealityRow(label: "braiins", value: braiinsFreshness, unit: "freshness"),
            RealityRow(label: "manual exposure", value: activeManualExposure, unit: "blocker"),
        ] + instrumentRows
    }

    var factGridRows: [(String, String, String)] {
        factRows.map { ($0.label, $0.value, $0.unit) }
    }

    var decisionTint: Color {
        switch decisionTitle {
        case "ENGINE LIVE", "REFRESH", "WATCH", "REVIEW":
            .green
        case "WORKING", "HOLD", "WAIT", "COOLDOWN":
            .orange
        default:
            .secondary
        }
    }

    static func make(
        section: AppSection,
        appState: AppStatePayload?,
        isWorking: Bool,
        operation: String?,
        errorMessage: String?
    ) -> RenderedReality {
        let decision = Decision.from(appState, isWorking: isWorking)
        let control = ControlOwner.from(appState, isWorking: isWorking)
        let next = nextAction(appState)
        let latest = appState?.latest
        let operatorState = appState?.operatorState
        let engineStatus = appState?.engineStatus
        let activePositions = operatorState?.activeManualPositions ?? []
        let completedWatch = operatorState?.completedWatch
        let buttons = visibleButtons(section: section, appState: appState, isWorking: isWorking)
        let truths = operatorTruths(
            decision: decision,
            appState: appState,
            activePositions: activePositions,
            completedWatch: completedWatch
        )

        return RenderedReality(
            snapshotGeneratedAt: ISO8601DateFormatter().string(from: Date()),
            source: "SwiftUI rendered semantic state; this is not a screenshot or generic documentation.",
            visibleSection: section.title,
            visibleSectionSubtitle: section.subtitle,
            decisionTitle: decision.title,
            decisionExplanation: decision.explanation,
            controlTitle: control.title,
            controlDetail: control.detail,
            nextTitle: next.title,
            nextDetail: next.detail,
            currentInstruction: next.instruction,
            engineRunning: engineStatus?.running == true,
            engineDetail: engineStatus?.detail ?? "engine state not loaded",
            operation: operation ?? "none",
            errorMessage: errorMessage ?? "none",
            latestStrategyAction: operatorState?.action ?? "none",
            latestReport: operatorState?.latestReport ?? "none",
            activeWatch: operatorState?.activeWatch ?? "none",
            completedWatch: completedWatch.map { "\($0.reportPath), remaining \($0.remainingMinutes)m, earliest \($0.earliestActionLocal)" } ?? "none",
            activeManualExposure: activePositions.isEmpty ? "none" : activePositions.joined(separator: "; "),
            braiinsFreshness: freshnessText(operatorState),
            latestOceanSample: operatorState?.latestOceanTimestamp ?? "none",
            latestBraiinsSample: operatorState?.latestMarketTimestamp ?? "none",
            instrumentRows: [
                RealityRow(label: "braiins price", value: marketValue(latest, "fillable_price_btc_per_eh_day", fallback: marketValue(latest, "best_ask_btc_per_eh_day")), unit: "BTC/EH/day"),
                RealityRow(label: "ocean hashrate", value: oceanValue(latest, "pool_hashrate_eh_s"), unit: "EH/s"),
                RealityRow(label: "pool window", value: oceanValue(latest, "avg_block_time_hours"), unit: "h/block"),
                RealityRow(label: "expected net", value: sats(proposalValue(latest, "expected_net_btc")), unit: "model"),
            ],
            visibleButtons: buttons,
            operatorTruths: truths
        )
    }

    private static func nextAction(_ appState: AppStatePayload?) -> (title: String, detail: String, instruction: String) {
        guard let state = appState else {
            return ("Load state", "Reading durable SQLite state.", "Wait for the app-state load to finish.")
        }
        if state.engineStatus.running {
            return (
                "Engine owns it",
                "No babysitting. The background engine waits, samples, watches, and writes evidence.",
                "Do nothing unless you intentionally want to stop the engine or record manual exposure."
            )
        }
        if state.operatorState.activeWatch != nil {
            return (
                "Wait for watch",
                "A passive watch is already running.",
                "Do not start another watch. Wait for the current run report."
            )
        }
        if let watch = state.operatorState.completedWatch {
            return (
                "Wait \(watch.remainingMinutes)m",
                "Earliest useful action: \(watch.earliestActionLocal).",
                "Cooldown is active. Do not repeat the same experiment yet."
            )
        }
        if !state.operatorState.activeManualPositions.isEmpty {
            return (
                "Hold exposure",
                "A manually recorded Braiins position blocks new experiments.",
                "Supervise the real position. Close it only when it is truly finished."
            )
        }
        let step = state.automationPlan.steps.first ?? "No passive action is useful right now."
        return (state.automationPlan.title, step, step)
    }

    private static func visibleButtons(section: AppSection, appState: AppStatePayload?, isWorking: Bool) -> [String] {
        var buttons = ["Toolbar: Refresh"]
        if appState?.engineStatus.running == true {
            buttons.append("Toolbar: Stop Engine")
        } else {
            buttons.append("Toolbar: Start Engine")
        }
        switch section {
        case .deck:
            buttons.append(contentsOf: ["Flight Deck: Start Forever Engine", "Flight Deck: Stop", "Flight Deck: One Sample"])
        case .exposure:
            buttons.append(contentsOf: ["Exposure: Record Exposure", "Exposure: Close Exposure"])
        case .vault:
            buttons.append(contentsOf: ["Evidence: Cockpit", "Evidence: Report", "Evidence: Ledger"])
        case .mirror:
            buttons.append("Reality Mirror: Write Snapshot Now")
        default:
            break
        }
        if isWorking {
            buttons.append("State: some buttons are disabled because an operation is running")
        }
        return buttons
    }

    private static func operatorTruths(
        decision: Decision,
        appState: AppStatePayload?,
        activePositions: [String],
        completedWatch: CompletedWatchPayload?
    ) -> [String] {
        if appState == nil {
            return ["The app has not loaded structured backend state yet."]
        }
        if !activePositions.isEmpty {
            return [
                "Real manual exposure is recorded.",
                "New watch experiments should remain blocked until the exposure is closed."
            ]
        }
        if appState?.engineStatus.running == true {
            return [
                "The forever engine owns passive research.",
                "The safest operator workload is zero unless you need to record real exposure."
            ]
        }
        if let completedWatch {
            return [
                "A watch already produced evidence.",
                "Earliest useful next action is \(completedWatch.earliestActionLocal)."
            ]
        }
        switch decision {
        case .watch:
            return ["A passive watch or the forever engine is the current research action; no BTC is spent by the app."]
        case .review:
            return ["Manual review is required before any Braiins action; the app still cannot spend BTC."]
        case .observe:
            return ["No useful action window is visible; doing nothing is the intended action."]
        default:
            return [decision.explanation]
        }
    }

    private static func freshnessText(_ state: OperatorStatePayload?) -> String {
        guard let minutes = state?.freshnessMinutes else { return "unknown" }
        return minutes <= 30 ? "fresh (\(minutes)m)" : "stale (\(minutes)m)"
    }

    private static func marketValue(_ latest: LatestPayload?, _ key: String, fallback: String = "n/a") -> String {
        latest?.market?[key]?.description ?? fallback
    }

    private static func oceanValue(_ latest: LatestPayload?, _ key: String) -> String {
        latest?.ocean?[key]?.description ?? "n/a"
    }

    private static func proposalValue(_ latest: LatestPayload?, _ key: String) -> String {
        latest?.proposal?[key]?.description ?? "n/a"
    }
}

enum RealitySnapshotWriter {
    static func write(_ reality: RenderedReality) {
        guard let repoRoot = RatchetProcess.repoRootURL() else { return }
        let dataDir = repoRoot.appendingPathComponent("data", isDirectory: true)
        do {
            try FileManager.default.createDirectory(at: dataDir, withIntermediateDirectories: true)
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            let jsonData = try encoder.encode(reality)
            try jsonData.write(to: dataDir.appendingPathComponent("app_visual_state.json"), options: .atomic)
            try renderMarkdown(reality).write(
                to: dataDir.appendingPathComponent("app_visual_state.md"),
                atomically: true,
                encoding: .utf8
            )
        } catch {
            // This is diagnostic output only. UI operation must never fail because the mirror file cannot be written.
        }
    }

    private static func renderMarkdown(_ reality: RenderedReality) -> String {
        var lines = [
            "# App Visual State",
            "",
            "This file is written by the SwiftUI app. It records the app's semantic rendered state, not generic documentation.",
            "",
            "- snapshot_generated_at: \(reality.snapshotGeneratedAt)",
            "- visible_section: \(reality.visibleSection)",
            "- decision: \(reality.decisionTitle)",
            "- decision_explanation: \(reality.decisionExplanation)",
            "- control: \(reality.controlTitle)",
            "- control_detail: \(reality.controlDetail)",
            "- next: \(reality.nextTitle)",
            "- next_detail: \(reality.nextDetail)",
            "- current_instruction: \(reality.currentInstruction)",
            "- engine_running: \(reality.engineRunning ? "yes" : "no")",
            "- engine_detail: \(reality.engineDetail)",
            "- operation: \(reality.operation)",
            "- error_message: \(reality.errorMessage)",
            "- latest_strategy_action: \(reality.latestStrategyAction)",
            "- braiins_freshness: \(reality.braiinsFreshness)",
            "- latest_ocean_sample: \(reality.latestOceanSample)",
            "- latest_braiins_sample: \(reality.latestBraiinsSample)",
            "- latest_report: \(reality.latestReport)",
            "- active_watch: \(reality.activeWatch)",
            "- completed_watch: \(reality.completedWatch)",
            "- active_manual_exposure: \(reality.activeManualExposure)",
            "",
            "## Instruments",
            "",
        ]
        lines.append(contentsOf: reality.instrumentRows.map { "- \($0.label): \($0.value) \($0.unit)" })
        lines.append(contentsOf: ["", "## Visible Buttons", ""])
        lines.append(contentsOf: reality.visibleButtons.map { "- \($0)" })
        lines.append(contentsOf: ["", "## Operator Truths", ""])
        lines.append(contentsOf: reality.operatorTruths.map { "- \($0)" })
        lines.append("")
        return lines.joined(separator: "\n")
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

    var index: Int {
        switch self {
        case .loading, .refresh: 0
        case .watch: 2
        case .cooldown, .manual: 3
        case .adapt: 4
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
        case "capital": capital?[key]?.description
        case "ocean": ocean?[key]?.description
        case "guardrails": guardrails?[key]?.description
        case "strategy": strategy?[key]?.description
        default: nil
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
        let path = NSBezierPath(roundedRect: rect.insetBy(dx: size * 0.04, dy: size * 0.04), xRadius: size * 0.24, yRadius: size * 0.24)
        NSGradient(colors: [
            NSColor(red: 0.01, green: 0.04, blue: 0.05, alpha: 1),
            NSColor(red: 0.00, green: 0.36, blue: 0.30, alpha: 1),
            NSColor(red: 0.78, green: 1.00, blue: 0.46, alpha: 1)
        ])?.draw(in: path, angle: -35)

        NSColor.white.withAlphaComponent(0.24).setStroke()
        path.lineWidth = size * 0.014
        path.stroke()

        let center = NSPoint(x: size * 0.5, y: size * 0.5)
        let ring = NSBezierPath(ovalIn: rect.insetBy(dx: size * 0.18, dy: size * 0.18))
        NSColor.white.withAlphaComponent(0.16).setFill()
        ring.fill()

        let ratchet = NSBezierPath()
        for index in 0..<24 {
            let angle = (Double(index) / 24.0) * Double.pi * 2
            let radius = size * (index.isMultiple(of: 2) ? 0.29 : 0.20)
            let point = NSPoint(x: center.x + CGFloat(cos(angle)) * radius, y: center.y + CGFloat(sin(angle)) * radius)
            index == 0 ? ratchet.move(to: point) : ratchet.line(to: point)
        }
        ratchet.close()
        NSColor(red: 0.96, green: 0.75, blue: 0.28, alpha: 0.98).setFill()
        ratchet.fill()

        let core = NSBezierPath(ovalIn: rect.insetBy(dx: size * 0.39, dy: size * 0.39))
        NSColor(red: 0.02, green: 0.09, blue: 0.08, alpha: 1).setFill()
        core.fill()

        image.unlockFocus()
        return image
    }
}

enum RatchetProcess {
    static func repoRootURL() -> URL? {
        findRepoRoot()
    }

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
