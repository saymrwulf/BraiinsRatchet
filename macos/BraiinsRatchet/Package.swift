// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "BraiinsRatchetMac",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        .executable(name: "BraiinsRatchetMac", targets: ["BraiinsRatchetMac"])
    ],
    targets: [
        .executableTarget(
            name: "BraiinsRatchetMac"
        )
    ]
)
