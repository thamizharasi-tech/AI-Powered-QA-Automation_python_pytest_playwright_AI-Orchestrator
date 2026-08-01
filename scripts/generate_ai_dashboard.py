import argparse
from pathlib import Path

from ai_orchestrator.agents.ai_dashboard_agent import AIDashboardAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the AI dashboard HTML from Allure results.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    project_root = Path(__file__).resolve().parent.parent
    default_results = project_root / "testReport" / "Execution_Backup" / "report" / "allure-results"
    default_output = project_root / "testReport" / "Execution_Backup" / "report" / "ai_dashboard_report.html"

    parser.add_argument(
        "--allure-results-dir",
        default=default_results,
        type=Path,
        help="Path to the Allure results directory containing raw result JSON files.",
    )
    parser.add_argument(
        "--output-path",
        default=default_output,
        type=Path,
        help="Destination HTML file for the generated AI dashboard.",
    )
    parser.add_argument(
        "--report-title",
        default="Executive QA Dashboard",
        help="Title to display at the top of the generated report.",
    )
    parser.add_argument(
        "--application-name",
        default="QA Application",
        help="Name of the application under test.",
    )
    parser.add_argument(
        "--suite-name",
        default="Smoke Regression",
        help="Name of the test suite or execution scope.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.allure_results_dir.exists():
        raise FileNotFoundError(f"Allure results directory not found: {args.allure_results_dir}")

    result_files = sorted(args.allure_results_dir.glob('*-result.json'))
    print(f"Found {len(result_files)} Allure result file(s) in: {args.allure_results_dir}")

    agent = AIDashboardAgent()
    output_file = agent.generate_dashboard_from_allure_results(
        allure_results_dir=args.allure_results_dir,
        output_path=args.output_path,
        report_title=args.report_title,
        application_name=args.application_name,
        suite_name=args.suite_name,
    )

    print(f"Generated AI dashboard at: {output_file}")


if __name__ == "__main__":
    main()
