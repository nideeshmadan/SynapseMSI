#!/usr/bin/env python3
"""
Synapse Public Cross-Venue State Builder

Processes raw venue snapshots into cross-venue market states for validation.

Input: public_data/btc_binance_bybit_live.csv (from collect_public_binance_bybit.py)
Output: public_data/btc_binance_bybit_states.csv (compatible with synapse_validate.py)

Logic:
- Groups snapshots by collection timestamp
- Selects best cross-venue bid (highest) and ask (lowest) 
- Computes temporal coherence metrics for Synapse validation
"""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd


def parse_timestamp(value) -> datetime:
    """
    Robust timestamp parser handling multiple formats.
    
    Supports:
    - ISO format strings (2026-05-11T15:50:00.000Z)
    - Epoch milliseconds (1778515433510) 
    - Epoch seconds (1778515433)
    - null/empty values (returns None)
    
    Returns timezone-aware UTC datetime object.
    """
    if value is None or value == "":
        return None
        
    # Convert to string
    value_str = str(value).strip()
    if not value_str:
        return None
    
    try:
        # Check if it's all digits (epoch timestamp)
        if value_str.isdigit():
            timestamp_num = int(value_str)
            
            # Milliseconds (13+ digits) or seconds (10 digits)
            if len(value_str) >= 13:
                # Epoch milliseconds
                dt = datetime.fromtimestamp(timestamp_num / 1000, tz=timezone.utc)
            elif len(value_str) == 10:
                # Epoch seconds
                dt = datetime.fromtimestamp(timestamp_num, tz=timezone.utc)
            else:
                raise ValueError(f"Unexpected epoch timestamp length: {len(value_str)}")
            
            return dt
        
        else:
            # Try parsing as ISO format using pandas (more robust)
            import pandas as pd
            return pd.to_datetime(value_str, utc=True).to_pydatetime()
            
    except Exception as e:
        print(f"⚠️  Failed to parse timestamp '{value_str}': {e}")
        return None


def compute_cross_venue_state(group: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute cross-venue state from venue snapshots at same timestamp."""
    
    if not group:
        return None
    
    # Extract timestamp info
    collection_timestamp = group[0]["timestamp"]
    collection_dt = parse_timestamp(collection_timestamp)
    instrument = group[0]["instrument"]
    
    # Fallback if collection timestamp unparseable
    if collection_dt is None:
        collection_dt = datetime.now(timezone.utc)
        collection_timestamp = collection_dt.isoformat()
    
    # Find best bid (highest) and best ask (lowest) across venues
    best_bid_row = max(group, key=lambda x: float(x["best_bid"]))
    best_ask_row = min(group, key=lambda x: float(x["best_ask"]))
    
    best_bid = float(best_bid_row["best_bid"])
    best_ask = float(best_ask_row["best_ask"])
    best_bid_venue = best_bid_row["venue"]
    best_ask_venue = best_ask_row["venue"]
    
    # Parse venue timestamps with fallback to collection timestamp
    best_bid_ts_str = best_bid_row["best_bid_timestamp"]
    best_ask_ts_str = best_ask_row["best_ask_timestamp"]
    
    best_bid_dt = parse_timestamp(best_bid_ts_str)
    best_ask_dt = parse_timestamp(best_ask_ts_str)
    
    # Fall back to collection timestamp if venue timestamps unparseable
    if best_bid_dt is None:
        best_bid_dt = collection_dt
        best_bid_ts_str = collection_timestamp
        print(f"⚠️  Using collection timestamp for best_bid from {best_bid_venue}")
    
    if best_ask_dt is None:
        best_ask_dt = collection_dt  
        best_ask_ts_str = collection_timestamp
        print(f"⚠️  Using collection timestamp for best_ask from {best_ask_venue}")
    
    # Public REST ticker timestamps are not guaranteed to represent venue-side quote 
    # event time, so future timestamps are clamped to collection time for demo safety
    if best_bid_dt > collection_dt:
        print(f"⚠️  Clamping future best_bid timestamp from {best_bid_venue} to collection time")
        best_bid_dt = collection_dt
        best_bid_ts_str = collection_timestamp
    
    if best_ask_dt > collection_dt:
        print(f"⚠️  Clamping future best_ask timestamp from {best_ask_venue} to collection time")
        best_ask_dt = collection_dt
        best_ask_ts_str = collection_timestamp
    
    # Compute temporal coherence metrics
    sync_gap_ms = abs((best_bid_dt - best_ask_dt).total_seconds()) * 1000
    
    # Age from collection time to oldest venue timestamp (ensure non-negative)
    oldest_venue_dt = min(best_bid_dt, best_ask_dt)
    best_pair_age_ms = max(0, (collection_dt - oldest_venue_dt).total_seconds() * 1000)
    
    # Compute observed cross-venue spread in basis points
    mid_price = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    observed_cross_venue_spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 0
    
    # Ensure output timestamps are ISO format strings
    best_bid_output_ts = best_bid_dt.isoformat() if best_bid_dt else collection_timestamp
    best_ask_output_ts = best_ask_dt.isoformat() if best_ask_dt else collection_timestamp
    
    return {
        "timestamp": collection_timestamp,
        "instrument": instrument,
        "best_bid": best_bid,
        "best_bid_venue": best_bid_venue,
        "best_bid_timestamp": best_bid_output_ts,
        "best_ask": best_ask,
        "best_ask_venue": best_ask_venue,
        "best_ask_timestamp": best_ask_output_ts,
        "observed_cross_venue_spread_bps": round(observed_cross_venue_spread_bps, 2),
        "sync_gap_ms": round(sync_gap_ms, 1),
        "best_pair_age_ms": round(best_pair_age_ms, 1)
    }


def main():
    """Main processing function."""
    parser = argparse.ArgumentParser(
        description="Build cross-venue market states from venue snapshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 build_public_crossvenue_states.py

Reads: public_data/btc_binance_bybit_live.csv
Writes: public_data/btc_binance_bybit_states.csv

Output is compatible with synapse_validate.py for temporal coherence analysis.
        """
    )
    
    parser.add_argument(
        "--input",
        default="public_data/btc_binance_bybit_live.csv",
        help="Input CSV from collector (default: public_data/btc_binance_bybit_live.csv)"
    )
    
    parser.add_argument(
        "--output", 
        default="public_data/btc_binance_bybit_states.csv",
        help="Output CSV path (default: public_data/btc_binance_bybit_states.csv)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        print("Run collect_public_binance_bybit.py first to generate data.")
        return 1
    
    print("🔄 Synapse Cross-Venue State Builder")
    print("=" * 50)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print("=" * 50)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Read raw snapshots
        print(f"📂 Reading venue snapshots...")
        
        snapshots = []
        with open(input_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                snapshots.append(row)
        
        print(f"   Loaded {len(snapshots)} venue snapshots")
        
        if not snapshots:
            print("❌ No snapshots found in input file")
            return 1
        
        # Group by timestamp
        print(f"🔍 Grouping by collection timestamp...")
        
        timestamp_groups = {}
        for snapshot in snapshots:
            ts = snapshot["timestamp"]
            if ts not in timestamp_groups:
                timestamp_groups[ts] = []
            timestamp_groups[ts].append(snapshot)
        
        print(f"   Found {len(timestamp_groups)} unique timestamps")
        
        # Build cross-venue states
        print(f"⚙️ Computing cross-venue states...")
        
        cross_venue_states = []
        for timestamp, group in timestamp_groups.items():
            state = compute_cross_venue_state(group)
            if state:
                cross_venue_states.append(state)
        
        print(f"   Generated {len(cross_venue_states)} cross-venue states")
        
        if not cross_venue_states:
            print("❌ No valid cross-venue states generated")
            return 1
        
        # Write output CSV
        print(f"💾 Writing cross-venue states...")
        
        fieldnames = [
            "timestamp", "instrument",
            "best_bid", "best_bid_venue", "best_bid_timestamp",
            "best_ask", "best_ask_venue", "best_ask_timestamp", 
            "observed_cross_venue_spread_bps",
            "sync_gap_ms", "best_pair_age_ms"
        ]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cross_venue_states)
        
        # Summary statistics
        spreads = [float(s["observed_cross_venue_spread_bps"]) for s in cross_venue_states]
        sync_gaps = [float(s["sync_gap_ms"]) for s in cross_venue_states]
        ages = [float(s["best_pair_age_ms"]) for s in cross_venue_states]
        
        print("\n" + "="*50)
        print("📊 CROSS-VENUE STATE SUMMARY")
        print(f"States generated: {len(cross_venue_states)}")
        print(f"Avg spread: {sum(spreads)/len(spreads):.2f} bps")
        print(f"Avg sync gap: {sum(sync_gaps)/len(sync_gaps):.1f}ms")
        print(f"Avg pair age: {sum(ages)/len(ages):.1f}ms")
        print(f"Output: {args.output}")
        
        print(f"\nNext step: python3 synapse_validate.py {args.output}")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())