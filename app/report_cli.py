"""
CLI reporting tool for the ACME Transactions System.
Generates payments and daily totals reports for a user, with options for date range and output format (console, CSV, JSON).

Usage examples:
    python report_cli.py payments user1 --format csv --output user1_payments.csv
    python report_cli.py daily_totals user1 --start_date 2025-05-01 --end_date 2025-05-31 --format json
"""

import argparse
import sys
import csv
import json
from reporting import get_payments_by_user, get_daily_totals
from datetime import datetime
from db import get_engine
from sqlalchemy.orm import Session

def main():
    """
    Command-line interface for generating user payment and daily totals reports.

    Arguments (via argparse):
        report_type (str): 'payments' or 'daily_totals'
        user_id (str): User ID to report on
        --start_date (str, optional): Start date (YYYY-MM-DD)
        --end_date (str, optional): End date (YYYY-MM-DD)
        --format (str): Output format: 'console', 'csv', or 'json' (default: console)
        --output (str, optional): Output file path for CSV or JSON output

    Behavior:
        - Calls reporting functions to fetch data for the user and date range.
        - Outputs to console, CSV, or JSON as specified.
    """
    parser = argparse.ArgumentParser(description="Transaction Reporting CLI")
    parser.add_argument("report_type", choices=["payments", "daily_totals"], help="Type of report")
    parser.add_argument("user_id", help="User ID")
    parser.add_argument("--start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--format", choices=["console", "csv", "json"], default="console", help="Output format")
    parser.add_argument("--output", help="Output file (for csv or json)")
    args = parser.parse_args()

    engine = get_engine()
    with Session(engine) as session:
        # Parse date arguments if provided
        try:
            s_date = datetime.fromisoformat(args.start_date).date() if args.start_date else None
            e_date = datetime.fromisoformat(args.end_date).date() if args.end_date else None
        except ValueError as e:
            print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}")
            exit(1)

        try:
            # Select the report type and fieldnames
            if args.report_type == "payments":
                data = get_payments_by_user(args.user_id, s_date, e_date, session)
                fieldnames = ["id", "sender_id", "receiver_id", "amount", "currency", "timestamp", "status"]
            else:
                data = get_daily_totals(args.user_id, s_date, e_date, session)
                fieldnames = ["day", "total_sent", "total_received"]

            # Output the report in the requested format
            if args.format == "console":
                for row in data:
                    print(row)
            elif args.format == "json":
                output = json.dumps(data, indent=2)
                if args.output:
                    try:
                        with open(args.output, "w") as f:
                            f.write(output)
                    except Exception as e:
                        print(f"Error writing JSON to file: {e}")
                        exit(1)
                else:
                    print(output)
            elif args.format == "csv":
                if args.output:
                    try:
                        with open(args.output, "w", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            for row in data:
                                writer.writerow(row)
                    except Exception as e:
                        print(f"Error writing CSV to file: {e}")
                        exit(1)
                else:
                    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in data:
                        writer.writerow(row)
        except Exception as e:
            print(f"Error generating report: {e}")
            exit(1)

if __name__ == "__main__":
    main() 