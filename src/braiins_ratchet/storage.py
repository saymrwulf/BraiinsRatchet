from __future__ import annotations

from pathlib import Path
import sqlite3

from .config import REPO_ROOT
from .models import MarketSnapshot, OceanSnapshot, StrategyProposal


DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "ratchet.sqlite"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ocean_snapshots (
            id INTEGER PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            pool_hashrate_eh_s TEXT,
            network_difficulty_t TEXT,
            share_log_window_t TEXT,
            avg_block_time_hours TEXT,
            source TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS market_snapshots (
            id INTEGER PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            best_price_btc_per_eh_day TEXT,
            available_hashrate_eh_s TEXT,
            source TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY,
            timestamp_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            price_btc_per_eh_day TEXT,
            spend_btc TEXT,
            duration_minutes INTEGER,
            breakeven_btc_per_eh_day TEXT,
            expected_reward_btc TEXT NOT NULL,
            expected_net_btc TEXT NOT NULL,
            score_btc TEXT NOT NULL,
            maturity_note TEXT NOT NULL
        );
        """
    )
    conn.commit()


def save_ocean_snapshot(conn: sqlite3.Connection, snapshot: OceanSnapshot) -> None:
    conn.execute(
        """
        INSERT INTO ocean_snapshots (
            timestamp_utc, pool_hashrate_eh_s, network_difficulty_t,
            share_log_window_t, avg_block_time_hours, source
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot.timestamp_utc,
            str(snapshot.pool_hashrate_eh_s) if snapshot.pool_hashrate_eh_s is not None else None,
            str(snapshot.network_difficulty_t) if snapshot.network_difficulty_t is not None else None,
            str(snapshot.share_log_window_t) if snapshot.share_log_window_t is not None else None,
            str(snapshot.avg_block_time_hours) if snapshot.avg_block_time_hours is not None else None,
            snapshot.source,
        ),
    )
    conn.commit()


def save_market_snapshot(conn: sqlite3.Connection, snapshot: MarketSnapshot) -> None:
    conn.execute(
        """
        INSERT INTO market_snapshots (
            timestamp_utc, best_price_btc_per_eh_day, available_hashrate_eh_s, source
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            snapshot.timestamp_utc,
            str(snapshot.best_price_btc_per_eh_day)
            if snapshot.best_price_btc_per_eh_day is not None
            else None,
            str(snapshot.available_hashrate_eh_s)
            if snapshot.available_hashrate_eh_s is not None
            else None,
            snapshot.source,
        ),
    )
    conn.commit()


def latest_ocean_snapshot(conn: sqlite3.Connection) -> OceanSnapshot | None:
    row = conn.execute(
        """
        SELECT timestamp_utc, pool_hashrate_eh_s, network_difficulty_t,
               share_log_window_t, avg_block_time_hours, source
        FROM ocean_snapshots
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    from decimal import Decimal

    return OceanSnapshot(
        timestamp_utc=row[0],
        pool_hashrate_eh_s=Decimal(row[1]) if row[1] else None,
        network_difficulty_t=Decimal(row[2]) if row[2] else None,
        share_log_window_t=Decimal(row[3]) if row[3] else None,
        avg_block_time_hours=Decimal(row[4]) if row[4] else None,
        source=row[5],
    )


def latest_market_snapshot(conn: sqlite3.Connection) -> MarketSnapshot | None:
    row = conn.execute(
        """
        SELECT timestamp_utc, best_price_btc_per_eh_day, available_hashrate_eh_s, source
        FROM market_snapshots
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    from decimal import Decimal

    return MarketSnapshot(
        timestamp_utc=row[0],
        best_price_btc_per_eh_day=Decimal(row[1]) if row[1] else None,
        available_hashrate_eh_s=Decimal(row[2]) if row[2] else None,
        source=row[3],
    )


def save_proposal(conn: sqlite3.Connection, proposal: StrategyProposal) -> None:
    order = proposal.order
    conn.execute(
        """
        INSERT INTO proposals (
            action, reason, price_btc_per_eh_day, spend_btc, duration_minutes,
            breakeven_btc_per_eh_day, expected_reward_btc, expected_net_btc,
            score_btc, maturity_note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            proposal.action,
            proposal.reason,
            str(order.price_btc_per_eh_day) if order else None,
            str(order.spend_btc) if order else None,
            order.duration_minutes if order else None,
            str(proposal.breakeven_btc_per_eh_day)
            if proposal.breakeven_btc_per_eh_day is not None
            else None,
            str(proposal.expected_reward_btc),
            str(proposal.expected_net_btc),
            str(proposal.score_btc),
            proposal.maturity_note,
        ),
    )
    conn.commit()
