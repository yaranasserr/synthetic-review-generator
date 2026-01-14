#!/usr/bin/env python3
"""Unified CLI for synthetic review generation"""

import argparse
import os
import sys
from dotenv import load_dotenv

sys.path.append('src')

from generator import ReviewGenerator
from reports import generate_quality_report, generate_comparison_report
from logger import get_logger


def check_env():
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not found in .env")
        sys.exit(1)


def cmd_generate(args):
    """Generate reviews"""
    check_env()
    
    logger = get_logger(verbose=args.verbose)
    gen = ReviewGenerator(args.config, verbose=args.verbose)
    result = gen.generate_all(count=args.count)
    
    logger.info(f"\nGeneration complete!")
    logger.info(f"Clean reviews: {result['clean_path']}")
    logger.info(f"With models: {result['with_models_path']}")
    logger.info(f"CSV log: {result['csv_log']}")
    
    # Auto-generate reports
    if args.with_reports:
        logger.info(f"\nGenerating reports...")
        
        # Quality report
        quality_path, _ = generate_quality_report(
            result['csv_log'],
            include_charts=args.charts,
            synthetic_path=result['clean_path'],
            real_path=args.real_reviews
        )
        logger.success(f"Quality report: {quality_path}")
        
        # Comparison report
        if args.real_reviews:
            comp_path, _ = generate_comparison_report(
                args.real_reviews,
                result['clean_path'],
                include_charts=args.charts
            )
            logger.success(f"Comparison report: {comp_path}")


def cmd_quality_report(args):
    """Generate quality report from CSV"""
    report_path, text = generate_quality_report(
        args.csv, 
        args.output,
        include_charts=args.charts,
        synthetic_path=args.synthetic,
        real_path=args.real
    )
    print(f"Quality report saved: {report_path}")
    if args.show:
        print(f"\n{text}")


def cmd_compare(args):
    """Compare real vs synthetic"""
    report_path, text = generate_comparison_report(
        args.real,
        args.synthetic,
        args.output,
        include_charts=args.charts
    )
    print(f"Comparison report saved: {report_path}")
    if args.show:
        print(f"\n{text}")


def main():
    parser = argparse.ArgumentParser(
        description='Synthetic Review Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/cli.py generate --count 400
  python src/cli.py generate --count 100 --with-reports --real-reviews data/raw/real_reviews.json
  python src/cli.py generate --count 10 --quiet
  python src/cli.py quality-report --csv data/synthetic/logs/generation_log_*.csv
  python src/cli.py compare --real data/raw/real_reviews.json --synthetic data/synthetic/reviews/reviews_clean_*.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # GENERATE
    gen_parser = subparsers.add_parser('generate', help='Generate synthetic reviews')
    gen_parser.add_argument('--count', type=int, default=400, help='Number of reviews')
    gen_parser.add_argument('--config', default='config/config.yaml', help='Config file')
    gen_parser.add_argument('--with-reports', action='store_true', help='Auto-generate reports')
    gen_parser.add_argument('--real-reviews', help='Real reviews for comparison')
    gen_parser.add_argument('--quiet', action='store_true', help='Minimal output')
    gen_parser.add_argument('--verbose', action='store_true', default=True, help='Verbose output (default)')
    gen_parser.add_argument('--charts', action='store_true', help='Generate visualization charts')

    gen_parser.set_defaults(func=cmd_generate)
    
    # QUALITY-REPORT
    quality_parser = subparsers.add_parser('quality-report', help='Generate quality report')
    quality_parser.add_argument('--csv', required=True, help='CSV log path')
    quality_parser.add_argument('--output', help='Output markdown path')
    quality_parser.add_argument('--show', action='store_true', help='Print to console')
    quality_parser.add_argument('--charts', action='store_true', help='Include charts')
    quality_parser.add_argument('--synthetic', help='Synthetic reviews JSON (for charts)')
    quality_parser.add_argument('--real', help='Real reviews JSON (for charts)')
    quality_parser.set_defaults(func=cmd_quality_report)
    
    # COMPARE
    compare_parser = subparsers.add_parser('compare', help='Compare real vs synthetic')
    compare_parser.add_argument('--real', required=True, help='Real reviews JSON')
    compare_parser.add_argument('--synthetic', required=True, help='Synthetic reviews JSON')
    compare_parser.add_argument('--output', help='Output markdown path')
    compare_parser.add_argument('--show', action='store_true', help='Print to console')
    compare_parser.add_argument('--charts', action='store_true', help='Include charts')
    compare_parser.set_defaults(func=cmd_compare)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Handle quiet flag
    if hasattr(args, 'quiet') and args.quiet:
        args.verbose = False
    
    args.func(args)


if __name__ == "__main__":
    main()