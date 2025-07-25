#!/usr/bin python3
"""
ACME Transactions System - Complete Setup and Testing Script

This script automates the entire setup, testing, and demo process for the ACME Transactions System.
Run this script to:
1. Build and start all Docker containers
2. Apply database migrations
3. Seed initial data
4. Run all automated tests
5. Perform manual testing of all features
6. Generate a comprehensive test report

Usage:
    python setup_and_test.py

Requirements:
    - Docker and Docker Compose installed
    - Python 3.11+ (for running this script)
    - .env file configured (copy from .env.example)
"""

import os
import sys
import time
import subprocess
import json
import requests
from datetime import datetime
from pathlib import Path

# Colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_step(message):
    """Print a step message."""
    print(f"{Colors.OKBLUE}▶ {message}{Colors.ENDC}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def run_command(command, description, check=True, capture_output=False):
    """Run a shell command and handle the result."""
    print_step(f"Running: {description}")
    print(f"  Command: {command}")
    
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
            return result
        else:
            result = subprocess.run(command, shell=True, check=check)
            return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {e}")
            return None
        else:
            print_warning(f"Command completed with warnings: {e}")
            return e

def wait_for_service(url, service_name, max_attempts=30):
    """Wait for a service to be ready."""
    print_step(f"Waiting for {service_name} to be ready...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{service_name} is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"  Attempt {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print_error(f"{service_name} failed to start within {max_attempts * 2} seconds")
    return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print_success(f"{description} found: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False

def test_api_endpoint(url, description, expected_status=200):
    """Test an API endpoint."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == expected_status:
            print_success(f"API Test: {description}")
            return True
        else:
            print_error(f"API Test Failed: {description} (Status: {response.status_code})")
            return False
    except Exception as e:
        print_error(f"API Test Error: {description} - {e}")
        return False

def main():
    """Main setup and testing function."""
    print_header("ACME Transactions System - Complete Setup & Testing")
    
    # Initialize test results
    test_results = {
        "setup": {},
        "automated_tests": {},
        "manual_tests": {},
        "overall_status": "PASSED"
    }
    
    # Check prerequisites
    print_header("1. Checking Prerequisites")
    
    # Check Docker
    docker_result = run_command("docker --version", "Checking Docker installation", capture_output=True)
    if docker_result and docker_result.returncode == 0:
        print_success("Docker is installed")
        test_results["setup"]["docker"] = "PASSED"
    else:
        print_error("Docker is not installed or not accessible")
        test_results["setup"]["docker"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        return
    
    # Check Docker Compose
    compose_result = run_command("docker-compose --version", "Checking Docker Compose installation", capture_output=True)
    if compose_result and compose_result.returncode == 0:
        print_success("Docker Compose is installed")
        test_results["setup"]["docker_compose"] = "PASSED"
    else:
        print_error("Docker Compose is not installed or not accessible")
        test_results["setup"]["docker_compose"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        return
    
    # Check .env file
    if check_file_exists(".env", ".env file"):
        test_results["setup"]["env_file"] = "PASSED"
    else:
        print_warning(".env file not found. Please copy .env.example to .env and configure it.")
        test_results["setup"]["env_file"] = "WARNING"
    
    # Check required files
    required_files = [
        ("docker-compose.yml", "Docker Compose configuration"),
        ("Makefile", "Makefile"),
        ("app/requirements.txt", "Python requirements"),
        ("app/main.py", "FastAPI application"),
        ("app/models.py", "Database models"),
        ("app/alembic.ini", "Alembic configuration")
    ]
    
    for filepath, description in required_files:
        if check_file_exists(filepath, description):
            test_results["setup"][description.lower().replace(" ", "_")] = "PASSED"
        else:
            test_results["setup"][description.lower().replace(" ", "_")] = "FAILED"
            test_results["overall_status"] = "FAILED"
    
    if test_results["overall_status"] == "FAILED":
        print_error("Prerequisites check failed. Please fix the issues above and try again.")
        return
    
    # Build and start containers
    print_header("2. Building and Starting Containers")
    
    # Stop any existing containers
    run_command("docker-compose down -v", "Stopping existing containers", check=False)
    
    # Build and start
    build_result = run_command("docker-compose up --build -d", "Building and starting containers")
    if build_result:
        test_results["setup"]["containers"] = "PASSED"
        print_success("Containers started successfully")
    else:
        test_results["setup"]["containers"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        return
    
    # Wait for services to be ready
    print_header("3. Waiting for Services")
    
    # Wait for API
    if wait_for_service("http://localhost:8000/", "FastAPI Application"):
        test_results["setup"]["api_ready"] = "PASSED"
    else:
        test_results["setup"]["api_ready"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        return
    
    # Wait for RabbitMQ management
    if wait_for_service("http://localhost:15672/", "RabbitMQ Management"):
        test_results["setup"]["rabbitmq_ready"] = "PASSED"
    else:
        test_results["setup"]["rabbitmq_ready"] = "WARNING"
    
    # Apply migrations
    print_header("4. Database Setup")
    
    migrate_result = run_command("docker-compose run --rm app alembic upgrade head", "Applying database migrations")
    if migrate_result:
        test_results["setup"]["migrations"] = "PASSED"
        print_success("Database migrations applied successfully")
    else:
        test_results["setup"]["migrations"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        return
    
    # Seed data
    seed_result = run_command("docker-compose run --rm app python seed.py", "Seeding initial data")
    if seed_result:
        test_results["setup"]["seeding"] = "PASSED"
        print_success("Initial data seeded successfully")
    else:
        test_results["setup"]["seeding"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        return
    
    # Run automated tests
    print_header("5. Running Automated Tests")
    
    test_result = run_command("docker-compose run --rm app pytest -v", "Running automated tests")
    if test_result:
        test_results["automated_tests"]["pytest"] = "PASSED"
        print_success("All automated tests passed")
    else:
        test_results["automated_tests"]["pytest"] = "FAILED"
        test_results["overall_status"] = "FAILED"
        print_warning("Some automated tests failed, but continuing with manual tests...")
    
    # Manual API testing
    print_header("6. Manual API Testing")
    
    api_tests = [
        ("http://localhost:8000/", "Root endpoint"),
        ("http://localhost:8000/docs", "API documentation"),
        ("http://localhost:8000/users", "List users"),
        ("http://localhost:8000/currencies", "List currencies"),
        ("http://localhost:8000/reports/payments/user1", "User payments report"),
        ("http://localhost:8000/reports/daily_totals/user1", "User daily totals report")
    ]
    
    for url, description in api_tests:
        if test_api_endpoint(url, description):
            test_results["manual_tests"][description.lower().replace(" ", "_")] = "PASSED"
        else:
            test_results["manual_tests"][description.lower().replace(" ", "_")] = "FAILED"
            test_results["overall_status"] = "FAILED"
    
    # Test CSV import
    print_header("7. Testing CSV Import")
    
    # Create sample CSV if it doesn't exist
    sample_csv = "app/data/in/sample_transactions.csv"
    if not Path(sample_csv).exists():
        os.makedirs("app/data/in", exist_ok=True)
        csv_content = """transaction_id,sender_id,receiver_id,amount,currency,timestamp,status
csv_tx1,user1,user2,12000,USD,2025-05-01T12:00:00Z,completed
csv_tx2,user2,user3,500,EUR,2025-05-02T13:00:00Z,pending
csv_tx3,user3,user1,150,USD,2025-05-03T09:30:00Z,completed
csv_tx4,user2,user1,20000,USD,2025-05-04T10:00:00Z,completed
csv_tx5,user1,user3,50,EUR,2025-05-05T11:00:00Z,failed"""
        
        with open(sample_csv, 'w') as f:
            f.write(csv_content)
        print_success("Created sample CSV file")
    
    csv_result = run_command("docker-compose exec app python csv_importer.py data/in/sample_transactions.csv", "Importing CSV data")
    if csv_result:
        test_results["manual_tests"]["csv_import"] = "PASSED"
        print_success("CSV import completed successfully")
    else:
        test_results["manual_tests"]["csv_import"] = "FAILED"
        test_results["overall_status"] = "FAILED"
    
    # Test CLI commands
    print_header("8. Testing CLI Commands")
    
    cli_tests = [
        ("docker-compose exec app python manage_cli.py list-users", "List users CLI"),
        ("docker-compose exec app python manage_cli.py list-currencies", "List currencies CLI"),
        ("docker-compose exec app python report_cli.py payments user1", "Report CLI - payments"),
        ("docker-compose exec app python report_cli.py daily_totals user1", "Report CLI - daily totals")
    ]
    
    for command, description in cli_tests:
        result = run_command(command, description, check=False, capture_output=True)
        if result and result.returncode == 0:
            test_results["manual_tests"][description.lower().replace(" ", "_").replace("-", "_")] = "PASSED"
            print_success(f"CLI Test: {description}")
        else:
            test_results["manual_tests"][description.lower().replace(" ", "_").replace("-", "_")] = "FAILED"
            test_results["overall_status"] = "FAILED"
            print_error(f"CLI Test Failed: {description}")
    
    # Test queue functionality
    print_header("9. Testing Queue Functionality")
    
    # Start consumer in background
    print_step("Starting queue consumer...")
    consumer_process = subprocess.Popen(
        "docker-compose exec app python queue_consumer.py",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a moment for consumer to start
    time.sleep(3)
    
    # Send test messages
    producer_result = run_command("docker-compose exec app python queue_producer.py", "Sending test queue messages", check=False)
    if producer_result:
        test_results["manual_tests"]["queue_producer"] = "PASSED"
        print_success("Queue producer test completed")
    else:
        test_results["manual_tests"]["queue_producer"] = "FAILED"
        test_results["overall_status"] = "FAILED"
    
    # Stop consumer
    consumer_process.terminate()
    consumer_process.wait()
    
    # Generate test report
    print_header("10. Test Report")
    
    print(f"{Colors.BOLD}Overall Status: {test_results['overall_status']}{Colors.ENDC}")
    
    print(f"\n{Colors.UNDERLINE}Setup Results:{Colors.ENDC}")
    for test, status in test_results["setup"].items():
        color = Colors.OKGREEN if status == "PASSED" else Colors.FAIL if status == "FAILED" else Colors.WARNING
        print(f"  {color}{status}{Colors.ENDC} - {test}")
    
    print(f"\n{Colors.UNDERLINE}Automated Tests:{Colors.ENDC}")
    for test, status in test_results["automated_tests"].items():
        color = Colors.OKGREEN if status == "PASSED" else Colors.FAIL
        print(f"  {color}{status}{Colors.ENDC} - {test}")
    
    print(f"\n{Colors.UNDERLINE}Manual Tests:{Colors.ENDC}")
    for test, status in test_results["manual_tests"].items():
        color = Colors.OKGREEN if status == "PASSED" else Colors.FAIL
        print(f"  {color}{status}{Colors.ENDC} - {test}")
    
    # Save detailed report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n{Colors.OKCYAN}Detailed test report saved to: {report_file}{Colors.ENDC}")
    
    # Final instructions
    print_header("Setup Complete!")
    
    if test_results["overall_status"] == "PASSED":
        print_success("🎉 All tests passed! Your ACME Transactions System is ready.")
    else:
        print_warning("⚠️  Some tests failed. Please check the report above for details.")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
    print("1. Access the API documentation: http://localhost:8000/docs")
    print("2. Explore the CLI tools: docker-compose exec app python manage_cli.py --help")
    print("3. Check the database: docker-compose exec db psql -U fc_user -d fc_transactions")
    print("4. View logs: docker-compose logs -f app")
    print("5. Stop the system: docker-compose down")
    
    print(f"\n{Colors.OKCYAN}Happy coding! 🚀{Colors.ENDC}")

if __name__ == "__main__":
    main() 