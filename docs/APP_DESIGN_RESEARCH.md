# Native App Design Research

This app is not supposed to be a prettier terminal. It is supposed to be a control room for a risky, long-running research lifecycle.

## Design Sources

Apple's Liquid Glass guidance emphasizes system-native structure before visual effects:

- Use standard SwiftUI/AppKit structure so controls, navigation, sheets, and toolbars inherit system behavior.
- Keep navigation and controls in a distinct functional layer above the content.
- Avoid overusing custom glass effects; too much glass becomes noise.
- Support arbitrary window sizes with split views.
- Preserve accessibility when transparency or motion is reduced.
- Use custom glass sparingly; standard controls and split views should carry most of the Tahoe look.

Source: <https://developer.apple.com/documentation/TechnologyOverviews/adopting-liquid-glass>

Apple's SwiftUI Liquid Glass documentation adds the implementation constraint: too many custom glass containers can degrade performance, so this app keeps the primary glass treatment on the hero and control surfaces instead of turning every content block into an effect demo.

Source: <https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views>

Microsoft's Human-AI Interaction Guidelines are directly relevant because this app makes recommendations under uncertainty:

- Make clear what the system can and cannot do.
- Make clear how well it can do it.
- Show contextually relevant information.
- Explain why the system did what it did.
- Support correction, dismissal, global controls, and cautious adaptation over time.

Source: <https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/>

Nielsen Norman's usability heuristics matter because the operator may be tired, confused, or dealing with real money:

- Show system status.
- Use real-world language.
- Prevent errors before they happen.
- Prefer recognition over recall.
- Provide clear recovery paths.

Source: <https://media.nngroup.com/media/articles/attachments/Heuristic_Summary1-compressed.pdf>

## Product Decisions

The native app now treats the Python engine as a structured state provider, not as a terminal to embed. The new `app-state` command returns JSON with:

- Current operator state.
- Passive action plan.
- Forever engine status.
- Guardrail and strategy configuration.
- Cockpit text for audit/debug.
- Latest OCEAN, Braiins, and strategy proposal payloads.

The SwiftUI app turns that into native Tahoe surfaces:

- `Flight Deck`: giant decision word, glass control pucks, reactor lens, engine controls, and key instruments.
- `Hashflow`: Umbrel, Knots, Datum, OCEAN, Braiins, and block-luck interplay.
- `Ratchet`: the observe, price, watch, mature, adapt pathway.
- `Bid Lab`: shadow order, expected net, breakeven, and loss boundary.
- `Exposure`: the ledger for real manually placed Braiins exposure.
- `Evidence`: raw artifacts kept available but no longer primary.

The UI uses real Tahoe SwiftUI APIs where available in the local SDK: `glassEffect`, `GlassEffectContainer`, `.glass`, `.glassProminent`, `backgroundExtensionEffect`, and toolbar search. These are intentionally concentrated on the shell, action controls, and reactor instruments instead of coating every paragraph in glass.

## The Ratchet UX Rule

The app must always answer these questions without forcing the user to parse logs:

1. Who is in control right now?
2. What is the earliest useful next action?
3. What evidence artifact exists?
4. What action is blocked for safety?
5. Which single knob, if any, is eligible for later adaptation?
6. How the Braiins/OCEAN/Umbrel/Datum/Knots system interacts with the recommendation.

If the app cannot answer those questions graphically and in plain language, it is failing its purpose.
