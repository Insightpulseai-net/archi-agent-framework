#!/usr/bin/env python3
"""
Demo Data Seeder for Concur-Style T&E Suite
============================================

This script seeds realistic demo data for testing and UAT:
- Companies and chart of accounts
- Employees, managers, and approvers
- Expense categories and policies
- Per-diem rules and project codes
- Cash advance rules
- Sample trips, expense reports, and approvals

Usage:
    python seed_demo_data.py              # Seed demo data
    python seed_demo_data.py --reset      # Reset and reseed
    python seed_demo_data.py --prod       # Seed production baseline only
    python seed_demo_data.py --dry-run    # Show what would be created

Environment Variables:
    ODOO_URL        - Odoo server URL (default: http://localhost:8069)
    ODOO_DB         - Database name (default: odoo)
    ODOO_USER       - Admin username (default: admin)
    ODOO_PASSWORD   - Admin password (required)
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any

try:
    import odoorpc
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

# Load environment
load_dotenv()

# Configuration
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")

# Console for rich output
console = Console()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("seed_demo_data.log"),
    ]
)
logger = logging.getLogger(__name__)


# ===========================================================================
# DEMO DATA DEFINITIONS
# ===========================================================================

DEMO_COMPANIES = [
    {
        "name": "InsightPulseAI Philippines",
        "country_code": "PH",
        "currency": "PHP",
        "street": "BGC Corporate Center",
        "city": "Taguig City",
        "zip": "1634",
    },
    {
        "name": "InsightPulseAI APAC",
        "country_code": "SG",
        "currency": "SGD",
        "street": "Marina Bay Financial Centre",
        "city": "Singapore",
        "zip": "018983",
    },
]

DEMO_DEPARTMENTS = [
    {"name": "Executive", "code": "EXEC"},
    {"name": "Finance", "code": "FIN"},
    {"name": "Operations", "code": "OPS"},
    {"name": "Sales", "code": "SALES"},
    {"name": "Engineering", "code": "ENG"},
    {"name": "Marketing", "code": "MKT"},
]

DEMO_EMPLOYEES = [
    # Executives
    {
        "name": "Maria Santos",
        "work_email": "maria.santos@insightpulseai.net",
        "department": "Executive",
        "job_title": "CEO",
        "is_manager": True,
        "is_approver": True,
    },
    # Finance
    {
        "name": "Juan Dela Cruz",
        "work_email": "juan.delacruz@insightpulseai.net",
        "department": "Finance",
        "job_title": "CFO",
        "is_manager": True,
        "is_approver": True,
    },
    {
        "name": "Ana Reyes",
        "work_email": "ana.reyes@insightpulseai.net",
        "department": "Finance",
        "job_title": "Finance Manager",
        "is_manager": True,
        "is_approver": True,
    },
    {
        "name": "Pedro Garcia",
        "work_email": "pedro.garcia@insightpulseai.net",
        "department": "Finance",
        "job_title": "Accountant",
        "is_manager": False,
        "is_approver": False,
    },
    # Operations
    {
        "name": "Luz Bautista",
        "work_email": "luz.bautista@insightpulseai.net",
        "department": "Operations",
        "job_title": "Operations Director",
        "is_manager": True,
        "is_approver": True,
    },
    # Sales
    {
        "name": "Carlos Mendoza",
        "work_email": "carlos.mendoza@insightpulseai.net",
        "department": "Sales",
        "job_title": "Sales Director",
        "is_manager": True,
        "is_approver": True,
    },
    {
        "name": "Rosa Villanueva",
        "work_email": "rosa.villanueva@insightpulseai.net",
        "department": "Sales",
        "job_title": "Account Executive",
        "is_manager": False,
        "is_approver": False,
    },
    # Engineering
    {
        "name": "Miguel Torres",
        "work_email": "miguel.torres@insightpulseai.net",
        "department": "Engineering",
        "job_title": "VP Engineering",
        "is_manager": True,
        "is_approver": True,
    },
    {
        "name": "Elena Cruz",
        "work_email": "elena.cruz@insightpulseai.net",
        "department": "Engineering",
        "job_title": "Senior Developer",
        "is_manager": False,
        "is_approver": False,
    },
]

EXPENSE_CATEGORIES = [
    {"name": "Transportation - Taxi/Grab", "code": "TRANS_TAXI", "account_code": "6210"},
    {"name": "Transportation - Airfare", "code": "TRANS_AIR", "account_code": "6211"},
    {"name": "Transportation - Fuel", "code": "TRANS_FUEL", "account_code": "6212"},
    {"name": "Accommodation - Hotel", "code": "ACCOM_HOTEL", "account_code": "6220"},
    {"name": "Meals - Client Entertainment", "code": "MEALS_CLIENT", "account_code": "6230"},
    {"name": "Meals - Working Lunch", "code": "MEALS_WORK", "account_code": "6231"},
    {"name": "Per Diem - Domestic", "code": "PERDIEM_DOM", "account_code": "6240"},
    {"name": "Per Diem - International", "code": "PERDIEM_INTL", "account_code": "6241"},
    {"name": "Communication - Mobile", "code": "COMM_MOBILE", "account_code": "6250"},
    {"name": "Supplies - Office", "code": "SUPPLY_OFFICE", "account_code": "6260"},
    {"name": "Professional Development", "code": "PROF_DEV", "account_code": "6270"},
    {"name": "Miscellaneous", "code": "MISC", "account_code": "6290"},
]

PER_DIEM_RULES = [
    {"destination": "Metro Manila", "rate": 1500.00, "currency": "PHP"},
    {"destination": "Cebu City", "rate": 1800.00, "currency": "PHP"},
    {"destination": "Davao City", "rate": 1600.00, "currency": "PHP"},
    {"destination": "Singapore", "rate": 250.00, "currency": "SGD"},
    {"destination": "Hong Kong", "rate": 2000.00, "currency": "HKD"},
    {"destination": "Tokyo", "rate": 15000.00, "currency": "JPY"},
    {"destination": "Sydney", "rate": 300.00, "currency": "AUD"},
]

PROJECT_CODES = [
    {"code": "PROJ-001", "name": "Scout AI Platform", "budget": 5000000.00},
    {"code": "PROJ-002", "name": "Sari AI Assistant", "budget": 2000000.00},
    {"code": "PROJ-003", "name": "Finance Automation", "budget": 1500000.00},
    {"code": "PROJ-004", "name": "Client Engagement - TBWA", "budget": 3000000.00},
    {"code": "PROJ-005", "name": "Data Engineering Platform", "budget": 4000000.00},
    {"code": "ADMIN", "name": "General Administration", "budget": 1000000.00},
]

CASH_ADVANCE_RULES = {
    "max_amount": 50000.00,
    "max_duration_days": 30,
    "approval_threshold": 20000.00,  # Above this needs higher approval
    "liquidation_grace_days": 5,
}

# Sample trips and expenses for demo
DEMO_TRIPS = [
    {
        "employee": "Carlos Mendoza",
        "destination": "Cebu City",
        "purpose": "Client meeting - SM Retail",
        "start_date": datetime.now() + timedelta(days=7),
        "end_date": datetime.now() + timedelta(days=9),
        "project": "PROJ-004",
        "expenses": [
            {"category": "TRANS_AIR", "amount": 8500.00, "description": "Round trip MNL-CEB"},
            {"category": "ACCOM_HOTEL", "amount": 4500.00, "description": "2 nights at Radisson"},
            {"category": "MEALS_CLIENT", "amount": 3500.00, "description": "Client dinner"},
            {"category": "TRANS_TAXI", "amount": 1200.00, "description": "Airport transfers"},
        ],
    },
    {
        "employee": "Miguel Torres",
        "destination": "Singapore",
        "purpose": "Tech conference - AWS Summit",
        "start_date": datetime.now() + timedelta(days=14),
        "end_date": datetime.now() + timedelta(days=17),
        "project": "PROJ-001",
        "expenses": [
            {"category": "TRANS_AIR", "amount": 25000.00, "description": "Round trip MNL-SIN"},
            {"category": "ACCOM_HOTEL", "amount": 18000.00, "description": "3 nights at Marina Bay Sands"},
            {"category": "PROF_DEV", "amount": 5000.00, "description": "Conference registration"},
            {"category": "PERDIEM_INTL", "amount": 12000.00, "description": "Per diem 3 days"},
        ],
    },
    {
        "employee": "Rosa Villanueva",
        "destination": "Metro Manila",
        "purpose": "Client visits - Multiple accounts",
        "start_date": datetime.now() - timedelta(days=3),
        "end_date": datetime.now() - timedelta(days=1),
        "project": "PROJ-004",
        "status": "approved",
        "expenses": [
            {"category": "TRANS_TAXI", "amount": 2500.00, "description": "Grab rides"},
            {"category": "MEALS_CLIENT", "amount": 5500.00, "description": "Client lunches x3"},
            {"category": "COMM_MOBILE", "amount": 500.00, "description": "Data roaming"},
        ],
    },
]

DEMO_CASH_ADVANCES = [
    {
        "employee": "Carlos Mendoza",
        "amount": 25000.00,
        "purpose": "Cebu client trip expenses",
        "project": "PROJ-004",
        "status": "approved",
    },
    {
        "employee": "Elena Cruz",
        "amount": 10000.00,
        "purpose": "Office supplies and equipment",
        "project": "PROJ-001",
        "status": "pending",
    },
]


class OdooSeeder:
    """Seeds demo data into Odoo."""

    def __init__(self, url: str, db: str, user: str, password: str):
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.odoo: Optional[odoorpc.ODOO] = None
        self.created_ids: Dict[str, Dict[str, int]] = {}

    def connect(self) -> bool:
        """Establish connection to Odoo."""
        try:
            # Parse URL
            if self.url.startswith("https://"):
                host = self.url.replace("https://", "")
                port = 443
                protocol = "jsonrpc+ssl"
            elif self.url.startswith("http://"):
                host = self.url.replace("http://", "")
                port = 8069
                protocol = "jsonrpc"
            else:
                host = self.url
                port = 8069
                protocol = "jsonrpc"

            if ":" in host:
                host, port_str = host.split(":")
                port = int(port_str)

            console.print(f"[cyan]Connecting to {host}:{port}...[/cyan]")

            self.odoo = odoorpc.ODOO(host, port=port, protocol=protocol)
            self.odoo.login(self.db, self.user, self.password)

            console.print(f"[green]Connected to Odoo {self.odoo.version}[/green]")
            logger.info(f"Connected to Odoo at {self.url}")
            return True

        except Exception as e:
            console.print(f"[red]Failed to connect: {e}[/red]")
            logger.error(f"Connection failed: {e}")
            return False

    def _get_or_create(self, model: str, domain: List, vals: Dict) -> int:
        """Get existing record or create new one."""
        Model = self.odoo.env[model]
        ids = Model.search(domain)
        if ids:
            return ids[0]
        return Model.create(vals)

    def seed_departments(self, dry_run: bool = False) -> Dict[str, int]:
        """Create demo departments."""
        console.print("[cyan]Seeding departments...[/cyan]")
        dept_ids = {}

        for dept in DEMO_DEPARTMENTS:
            if dry_run:
                console.print(f"  Would create department: {dept['name']}")
                continue

            try:
                dept_id = self._get_or_create(
                    "hr.department",
                    [("name", "=", dept["name"])],
                    {"name": dept["name"], "code": dept.get("code", "")},
                )
                dept_ids[dept["name"]] = dept_id
                logger.info(f"Created/found department: {dept['name']} (ID: {dept_id})")
            except Exception as e:
                console.print(f"[yellow]  Warning: Could not create {dept['name']}: {e}[/yellow]")

        self.created_ids["departments"] = dept_ids
        return dept_ids

    def seed_employees(self, dry_run: bool = False) -> Dict[str, int]:
        """Create demo employees with users."""
        console.print("[cyan]Seeding employees...[/cyan]")
        emp_ids = {}
        dept_ids = self.created_ids.get("departments", {})

        for emp in DEMO_EMPLOYEES:
            if dry_run:
                console.print(f"  Would create employee: {emp['name']}")
                continue

            try:
                # Create user first
                User = self.odoo.env["res.users"]
                user_ids = User.search([("login", "=", emp["work_email"])])

                if user_ids:
                    user_id = user_ids[0]
                else:
                    user_vals = {
                        "name": emp["name"],
                        "login": emp["work_email"],
                        "email": emp["work_email"],
                        "password": "demo123",  # For testing only
                    }
                    user_id = User.create(user_vals)

                # Create employee
                Employee = self.odoo.env["hr.employee"]
                emp_domain = [("name", "=", emp["name"])]
                existing = Employee.search(emp_domain)

                if existing:
                    emp_id = existing[0]
                else:
                    emp_vals = {
                        "name": emp["name"],
                        "work_email": emp["work_email"],
                        "job_title": emp.get("job_title", ""),
                        "user_id": user_id,
                    }

                    # Add department if available
                    dept_name = emp.get("department")
                    if dept_name and dept_name in dept_ids:
                        emp_vals["department_id"] = dept_ids[dept_name]

                    emp_id = Employee.create(emp_vals)

                emp_ids[emp["name"]] = emp_id
                logger.info(f"Created/found employee: {emp['name']} (ID: {emp_id})")

            except Exception as e:
                console.print(f"[yellow]  Warning: Could not create {emp['name']}: {e}[/yellow]")

        self.created_ids["employees"] = emp_ids
        return emp_ids

    def seed_expense_categories(self, dry_run: bool = False) -> Dict[str, int]:
        """Create expense categories as products."""
        console.print("[cyan]Seeding expense categories...[/cyan]")
        cat_ids = {}

        for cat in EXPENSE_CATEGORIES:
            if dry_run:
                console.print(f"  Would create expense category: {cat['name']}")
                continue

            try:
                # Create as product for hr.expense
                Product = self.odoo.env["product.product"]
                domain = [("name", "=", cat["name"])]
                existing = Product.search(domain)

                if existing:
                    cat_id = existing[0]
                else:
                    vals = {
                        "name": cat["name"],
                        "default_code": cat["code"],
                        "type": "service",
                        "can_be_expensed": True,
                    }
                    cat_id = Product.create(vals)

                cat_ids[cat["code"]] = cat_id
                logger.info(f"Created/found expense category: {cat['name']} (ID: {cat_id})")

            except Exception as e:
                console.print(f"[yellow]  Warning: Could not create {cat['name']}: {e}[/yellow]")

        self.created_ids["expense_categories"] = cat_ids
        return cat_ids

    def seed_projects(self, dry_run: bool = False) -> Dict[str, int]:
        """Create demo projects."""
        console.print("[cyan]Seeding projects...[/cyan]")
        project_ids = {}

        for proj in PROJECT_CODES:
            if dry_run:
                console.print(f"  Would create project: {proj['name']}")
                continue

            try:
                Project = self.odoo.env["project.project"]
                domain = [("name", "=", proj["name"])]
                existing = Project.search(domain)

                if existing:
                    proj_id = existing[0]
                else:
                    vals = {
                        "name": proj["name"],
                        "code": proj.get("code", ""),
                    }
                    proj_id = Project.create(vals)

                project_ids[proj["code"]] = proj_id
                logger.info(f"Created/found project: {proj['name']} (ID: {proj_id})")

            except Exception as e:
                console.print(f"[yellow]  Warning: Could not create {proj['name']}: {e}[/yellow]")

        self.created_ids["projects"] = project_ids
        return project_ids

    def seed_expenses(self, dry_run: bool = False) -> List[int]:
        """Create demo expense reports."""
        console.print("[cyan]Seeding expense reports...[/cyan]")
        expense_ids = []
        emp_ids = self.created_ids.get("employees", {})
        cat_ids = self.created_ids.get("expense_categories", {})

        for trip in DEMO_TRIPS:
            if dry_run:
                console.print(f"  Would create expense report for: {trip['employee']}")
                continue

            emp_name = trip["employee"]
            if emp_name not in emp_ids:
                console.print(f"[yellow]  Skipping - employee not found: {emp_name}[/yellow]")
                continue

            try:
                Expense = self.odoo.env["hr.expense"]

                for exp in trip.get("expenses", []):
                    cat_code = exp["category"]
                    product_id = cat_ids.get(cat_code)

                    if not product_id:
                        console.print(f"[yellow]  Skipping - category not found: {cat_code}[/yellow]")
                        continue

                    vals = {
                        "name": exp["description"],
                        "employee_id": emp_ids[emp_name],
                        "product_id": product_id,
                        "unit_amount": exp["amount"],
                        "quantity": 1,
                        "date": trip["start_date"].strftime("%Y-%m-%d"),
                    }

                    exp_id = Expense.create(vals)
                    expense_ids.append(exp_id)
                    logger.info(f"Created expense: {exp['description']} (ID: {exp_id})")

            except Exception as e:
                console.print(f"[yellow]  Warning: Could not create expense: {e}[/yellow]")

        self.created_ids["expenses"] = expense_ids
        return expense_ids

    def seed_all(self, dry_run: bool = False, prod_only: bool = False) -> Dict:
        """Seed all demo data."""
        results = {
            "departments": 0,
            "employees": 0,
            "expense_categories": 0,
            "projects": 0,
            "expenses": 0,
        }

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # Always seed these (baseline)
            task = progress.add_task("Seeding departments...", total=1)
            dept_ids = self.seed_departments(dry_run)
            results["departments"] = len(dept_ids)
            progress.advance(task)

            task = progress.add_task("Seeding employees...", total=1)
            emp_ids = self.seed_employees(dry_run)
            results["employees"] = len(emp_ids)
            progress.advance(task)

            task = progress.add_task("Seeding expense categories...", total=1)
            cat_ids = self.seed_expense_categories(dry_run)
            results["expense_categories"] = len(cat_ids)
            progress.advance(task)

            task = progress.add_task("Seeding projects...", total=1)
            proj_ids = self.seed_projects(dry_run)
            results["projects"] = len(proj_ids)
            progress.advance(task)

            # Only seed demo data if not prod mode
            if not prod_only:
                task = progress.add_task("Seeding demo expenses...", total=1)
                expense_ids = self.seed_expenses(dry_run)
                results["expenses"] = len(expense_ids)
                progress.advance(task)

        return results

    def reset_demo_data(self) -> None:
        """Remove demo data (careful with this!)."""
        console.print("[yellow]Resetting demo data...[/yellow]")

        # Only reset demo employees and their data
        try:
            # Delete demo expenses
            Expense = self.odoo.env["hr.expense"]
            demo_emp_emails = [e["work_email"] for e in DEMO_EMPLOYEES]

            Employee = self.odoo.env["hr.employee"]
            demo_emp_ids = Employee.search([("work_email", "in", demo_emp_emails)])

            if demo_emp_ids:
                expense_ids = Expense.search([("employee_id", "in", demo_emp_ids)])
                if expense_ids:
                    Expense.browse(expense_ids).unlink()
                    console.print(f"  Deleted {len(expense_ids)} demo expenses")

            logger.info("Demo data reset complete")

        except Exception as e:
            console.print(f"[yellow]  Warning during reset: {e}[/yellow]")


def print_results(results: Dict):
    """Print seeding results."""
    console.print("\n[bold]Seeding Results[/bold]\n")

    for key, count in results.items():
        console.print(f"  {key}: {count} records")

    total = sum(results.values())
    console.print(f"\n  [green]Total: {total} records[/green]")


def main():
    parser = argparse.ArgumentParser(description="Seed demo data for Concur Suite")
    parser.add_argument("--reset", action="store_true", help="Reset demo data first")
    parser.add_argument("--prod", action="store_true", help="Seed production baseline only")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would be created")
    parser.add_argument("--url", default=ODOO_URL, help=f"Odoo URL (default: {ODOO_URL})")
    parser.add_argument("--db", default=ODOO_DB, help=f"Database name (default: {ODOO_DB})")
    parser.add_argument("--user", "-u", default=ODOO_USER, help=f"Username (default: {ODOO_USER})")
    parser.add_argument("--password", "-p", default=ODOO_PASSWORD, help="Password")

    args = parser.parse_args()

    if not args.password:
        console.print("[red]ERROR: ODOO_PASSWORD environment variable or --password required[/red]")
        sys.exit(1)

    seeder = OdooSeeder(args.url, args.db, args.user, args.password)

    if not seeder.connect():
        sys.exit(1)

    if args.reset and not args.dry_run:
        seeder.reset_demo_data()

    results = seeder.seed_all(dry_run=args.dry_run, prod_only=args.prod)
    print_results(results)

    console.print("\n[green]Demo data seeding complete![/green]")


if __name__ == "__main__":
    main()
