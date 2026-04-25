from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.example.toml"


def _decimal(value: object, default: str) -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


@dataclass(frozen=True)
class CapitalConfig:
    available_btc: Decimal


@dataclass(frozen=True)
class OceanConfig:
    fee_rate: Decimal
    block_subsidy_btc: Decimal
    default_tx_fees_btc: Decimal
    dashboard_url: str

    @property
    def expected_block_reward_btc(self) -> Decimal:
        return self.block_subsidy_btc + self.default_tx_fees_btc


@dataclass(frozen=True)
class GuardrailsConfig:
    max_manual_order_btc: Decimal
    max_daily_spend_btc: Decimal
    max_price_btc_per_eh_day: Decimal
    max_canary_price_btc_per_eh_day: Decimal
    max_canary_expected_loss_btc: Decimal
    min_discount_to_breakeven: Decimal
    min_duration_minutes: int
    max_duration_minutes: int
    recommend_only: bool


@dataclass(frozen=True)
class StrategyConfig:
    target_duration_minutes: int
    target_spend_btc: Decimal
    risk_lambda: Decimal
    shadow_target_ph: Decimal
    shadow_overpay_btc_per_eh_day: Decimal


@dataclass(frozen=True)
class AppConfig:
    capital: CapitalConfig
    ocean: OceanConfig
    guardrails: GuardrailsConfig
    strategy: StrategyConfig


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or DEFAULT_CONFIG_PATH
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    capital = raw.get("capital", {})
    ocean = raw.get("ocean", {})
    guardrails = raw.get("guardrails", {})
    strategy = raw.get("strategy", {})

    return AppConfig(
        capital=CapitalConfig(
            available_btc=_decimal(capital.get("available_btc"), "0"),
        ),
        ocean=OceanConfig(
            fee_rate=_decimal(ocean.get("fee_rate"), "0.01"),
            block_subsidy_btc=_decimal(ocean.get("block_subsidy_btc"), "3.125"),
            default_tx_fees_btc=_decimal(ocean.get("default_tx_fees_btc"), "0"),
            dashboard_url=str(ocean.get("dashboard_url", "https://ocean.xyz/dashboard")),
        ),
        guardrails=GuardrailsConfig(
            max_manual_order_btc=_decimal(guardrails.get("max_manual_order_btc"), "0.0001"),
            max_daily_spend_btc=_decimal(guardrails.get("max_daily_spend_btc"), "0.0002"),
            max_price_btc_per_eh_day=_decimal(guardrails.get("max_price_btc_per_eh_day"), "0"),
            max_canary_price_btc_per_eh_day=_decimal(
                guardrails.get("max_canary_price_btc_per_eh_day"), "0"
            ),
            max_canary_expected_loss_btc=_decimal(
                guardrails.get("max_canary_expected_loss_btc"), "0"
            ),
            min_discount_to_breakeven=_decimal(guardrails.get("min_discount_to_breakeven"), "0.05"),
            min_duration_minutes=int(guardrails.get("min_duration_minutes", 30)),
            max_duration_minutes=int(guardrails.get("max_duration_minutes", 720)),
            recommend_only=bool(guardrails.get("recommend_only", True)),
        ),
        strategy=StrategyConfig(
            target_duration_minutes=int(strategy.get("target_duration_minutes", 180)),
            target_spend_btc=_decimal(strategy.get("target_spend_btc"), "0.0001"),
            risk_lambda=_decimal(strategy.get("risk_lambda"), "0.25"),
            shadow_target_ph=_decimal(strategy.get("shadow_target_ph"), "10"),
            shadow_overpay_btc_per_eh_day=_decimal(
                strategy.get("shadow_overpay_btc_per_eh_day"), "0.01"
            ),
        ),
    )
