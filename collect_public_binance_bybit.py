#!/usr/bin/env python3
"""
Synapse Public Data Collector: Binance + Bybit

Collects public BTCUSDT perpetual top-of-book snapshots from:
- Binance USDT-M futures 
- Bybit linear perpetuals

Outputs normalized CSV for cross-venue state reconstruction demo.

IMPORTANT: This uses collection-time timestamps where venue event timestamps 
are unavailable. The institutional research package uses preserved venue-side 
timestamps from Synapse canonical reconstruction. This public demo is for 
workflow demonstration, not a replacement for full canonical replay.
"""

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Any

import requests


def fetch_binance_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch Binance USDT-M futures book ticker."""
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/bookTicker"
        params = {"symbol": symbol}
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        return {
            "venue": "binance",
            "best_bid": float(data["bidPrice"]),
            "best_ask": float(data["askPrice"]),
            "venue_timestamp": data.get("time")  # May not be available
        }
    except Exception as e:
        print(f"Error: Binance fetch failed: {e}")
        return None


def fetch_bybit_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch Bybit V5 linear ticker."""
    try:
        url = "https://api.bybit.com/v5/market/tickers"
        params = {"category": "linear", "symbol": symbol}
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        if data.get("retCode") != 0:
            print(f"Error: Bybit API error: {data.get('retMsg')}")
            return None
            
        tickers = data.get("result", {}).get("list", [])
        if not tickers:
            print(f"Error: No Bybit ticker data for {symbol}")
            return None
            
        ticker = tickers[0]
        return {
            "venue": "bybit", 
            "best_bid": float(ticker["bid1Price"]),
            "best_ask": float(ticker["ask1Price"]),
            "venue_timestamp": None  # Not available in this endpoint
        }
    except Exception as e:
        print(f"Error: Bybit fetch failed: {e}")
        return None


def collect_snapshot(symbol: str) -> Dict[str, Any]:
    """Collect normalized snapshot from both venues."""
    collection_time = datetime.now(timezone.utc)
    timestamp_iso = collection_time.isoformat()
    
    print(f"Timestamp: {timestamp_iso} - Collecting {symbol}...")
    
    snapshots = []
    
    # Fetch Binance
    binance_data = fetch_binance_ticker(symbol)
    if binance_data:
        snapshots.append({
            "timestamp": timestamp_iso,
            "instrument": f"{symbol}_PERP",
            "venue": binance_data["venue"],
            "best_bid": binance_data["best_bid"],
            "best_ask": binance_data["best_ask"],
            "best_bid_timestamp": binance_data.get("venue_timestamp") or timestamp_iso,
            "best_ask_timestamp": binance_data.get("venue_timestamp") or timestamp_iso
        })
        print(f"   Binance: {binance_data['best_bid']:.2f} / {binance_data['best_ask']:.2f}")
    
    # Fetch Bybit
    bybit_data = fetch_bybit_ticker(symbol)
    if bybit_data:
        snapshots.append({
            "timestamp": timestamp_iso,
            "instrument": f"{symbol}_PERP", 
            "venue": bybit_data["venue"],
            "best_bid": bybit_data["best_bid"],
            "best_ask": bybit_data["best_ask"],
            "best_bid_timestamp": bybit_data.get("venue_timestamp") or timestamp_iso,
            "best_ask_timestamp": bybit_data.get("venue_timestamp") or timestamp_iso
        })
        print(f"   Bybit: {bybit_data['best_bid']:.2f} / {bybit_data['best_ask']:.2f}")
    
    if not snapshots:
        print("   Warning: No data collected this cycle")
    
    return {
        "timestamp": timestamp_iso,
        "snapshots": snapshots,
        "success_count": len(snapshots)
    }


def main():
    """Main collection loop."""
    parser = argparse.ArgumentParser(
        description="Collect public BTCUSDT perpetual data from Binance and Bybit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 collect_public_binance_bybit.py --seconds 300
  python3 collect_public_binance_bybit.py --symbol ETHUSDT --seconds 60 --out public_data/eth_live.csv

Note: This demo uses collection-time timestamps. Institutional Synapse uses 
preserved venue-side timestamps for precise temporal coherence validation.
        """
    )
    
    parser.add_argument(
        "--symbol", 
        default="BTCUSDT",
        help="Symbol to collect (default: BTCUSDT)"
    )
    
    parser.add_argument(
        "--seconds",
        type=int,
        default=300,
        help="Collection duration in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--out",
        default="public_data/btc_binance_bybit_live.csv", 
        help="Output CSV path (default: public_data/btc_binance_bybit_live.csv)"
    )
    
    args = parser.parse_args()
    
    # Setup output
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Synapse Public Data Collector")
    print("=" * 50)
    print(f"Symbol: {args.symbol}")
    print(f"Duration: {args.seconds} seconds")
    print(f"Output: {args.out}")
    print(f"Venues: Binance USDT-M, Bybit Linear")
    print("=" * 50)
    
    # CSV headers
    fieldnames = [
        "timestamp", "instrument", "venue", 
        "best_bid", "best_ask", 
        "best_bid_timestamp", "best_ask_timestamp"
    ]
    
    total_snapshots = 0
    total_cycles = 0
    
    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            start_time = time.time()
            end_time = start_time + args.seconds
            
            while time.time() < end_time:
                cycle_start = time.time()
                
                # Collect data
                result = collect_snapshot(args.symbol)
                total_cycles += 1
                
                # Write snapshots
                for snapshot in result["snapshots"]:
                    writer.writerow(snapshot)
                    total_snapshots += 1
                
                # Flush to disk
                csvfile.flush()
                
                # Wait for next cycle (target 1 second intervals)
                elapsed = time.time() - cycle_start
                sleep_time = max(0, 1.0 - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                remaining = int(end_time - time.time())
                if remaining > 0 and total_cycles % 10 == 0:
                    print(f"Progress: {total_snapshots} snapshots, {remaining}s remaining")
    
    except KeyboardInterrupt:
        print("\nCollection stopped by user")
    
    except Exception as e:
        print(f"\nError: Collection failed: {e}")
        return 1
    
    print("\n" + "="*50)
    print("COLLECTION COMPLETE")
    print(f"Total cycles: {total_cycles}")
    print(f"Total snapshots: {total_snapshots}")
    print(f"Average snapshots per cycle: {total_snapshots/total_cycles:.1f}")
    print(f"Output: {args.out}")
    
    if total_snapshots > 0:
        print(f"\nNext step: python3 build_public_crossvenue_states.py")
    
    return 0


if __name__ == "__main__":
    exit(main())