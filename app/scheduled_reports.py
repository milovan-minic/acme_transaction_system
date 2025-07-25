"""
Scheduled reporting job for the ACME Transactions System.
Generates monthly reports for each user as CSV and JSON, either on a schedule or on demand.

Usage:
    python scheduled_reports.py --run-once --month 2025-07 --output-dir reports/
"""

import os
import csv
import json
import argparse
from datetime import datetime, timedelta, date
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.orm import Session
from db import get_engine
from models import User
from reporting import get_payments_by_user, get_daily_totals

DEFAULT_REPORTS_DIR = "reports"

def get_month_range(target_month=None):
    """
    Get the first and last day of the target month.

    Args:
        target_month (str, optional): Month in 'YYYY-MM' format. Defaults to current month.
    Returns:
        (date, date): (first_day, first_day_of_next_month)
    """
    if target_month:
        first_day = datetime.strptime(target_month, "%Y-%m").date().replace(day=1)
    else:
        first_day = date.today().replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year+1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month+1, day=1)
    return first_day, next_month

def generate_monthly_reports(output_dir=DEFAULT_REPORTS_DIR, target_month=None):
    """
    Generate monthly payment and daily totals reports for all users.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating output directory '{output_dir}': {e}")
        return
    print(f"Generating monthly reports at {datetime.now().isoformat()} (output_dir={output_dir}, month={target_month or date.today().strftime('%Y-%m')})")
    try:
        engine = get_engine()
        with Session(engine) as session:
            users = session.query(User).all()
            start_date, end_date = get_month_range(target_month)
            for user in users:
                payments = get_payments_by_user(user.id, start_date, end_date, session)
                daily = get_daily_totals(user.id, start_date, end_date, session)
                # Save as JSON
                json_path = os.path.join(output_dir, f"{user.id}_monthly_{start_date}.json")
                try:
                    with open(json_path, "w") as f:
                        json.dump({"payments": payments, "daily_totals": daily}, f, indent=2)
                except Exception as e:
                    print(f"Error writing JSON report for user {user.id}: {e}")
                # Save as CSV (payments)
                csv_path = os.path.join(output_dir, f"{user.id}_payments_{start_date}.csv")
                try:
                    with open(csv_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=["id", "sender_id", "receiver_id", "amount", "currency", "timestamp", "status"])
                        writer.writeheader()
                        for row in payments:
                            writer.writerow(row)
                except Exception as e:
                    print(f"Error writing payments CSV for user {user.id}: {e}")
                # Save as CSV (daily totals)
                daily_csv_path = os.path.join(output_dir, f"{user.id}_daily_totals_{start_date}.csv")
                try:
                    with open(daily_csv_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=["day", "total_sent", "total_received"])
                        writer.writeheader()
                        for row in daily:
                            writer.writerow(row)
                except Exception as e:
                    print(f"Error writing daily totals CSV for user {user.id}: {e}")
                print(f"Report generated for user {user.id}")
    except Exception as e:
        print(f"Error generating reports: {e}")

def main():
    """
    Parse command-line arguments and run the scheduled or one-off reporting job.
    """
    parser = argparse.ArgumentParser(description="Scheduled Monthly Reporting")
    parser.add_argument("--run-once", action="store_true", help="Run the report once and exit")
    parser.add_argument("--month", help="Target month for report (YYYY-MM), default is current month")
    parser.add_argument("--output-dir", default=DEFAULT_REPORTS_DIR, help="Directory to save reports")
    parser.add_argument("--interval", type=int, help="Run every N minutes (for testing)")
    args = parser.parse_args()

    try:
        if args.run_once:
            generate_monthly_reports(output_dir=args.output_dir, target_month=args.month)
            return

        scheduler = BlockingScheduler()
        if args.interval:
            # Schedule job to run every N minutes
            scheduler.add_job(lambda: generate_monthly_reports(output_dir=args.output_dir, target_month=args.month), 'interval', minutes=args.interval)
            print(f"Scheduler started. Running every {args.interval} minutes.")
        else:
            # Default: run daily at midnight
            scheduler.add_job(lambda: generate_monthly_reports(output_dir=args.output_dir, target_month=args.month), 'cron', hour=0, minute=0)
            print("Scheduler started. Running daily at midnight.")
        generate_monthly_reports(output_dir=args.output_dir, target_month=args.month)  # Run once at startup
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            print("Scheduler stopped.")
    except Exception as e:
        print(f"Error in scheduled reporting: {e}")
        exit(1)

if __name__ == "__main__":
    main() 