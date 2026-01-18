#!/usr/bin/env python3
"""
Interactive database query tool
Usage: python scripts/interactive_query.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.services.plant_database import DatabaseManager
from agent.config import settings
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


async def run_query(query: str):
    """Run a SQL query and display results"""
    db_manager = DatabaseManager(settings.database_url)

    async with db_manager.get_session() as session:
        try:
            result = await session.execute(text(query))

            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                if rows:
                    # Print column names
                    print("\n" + "-" * 80)
                    if result.keys():
                        print(" | ".join(result.keys()))
                        print("-" * 80)

                    # Print rows
                    for row in rows:
                        print(" | ".join(str(val) for val in row))

                    print("-" * 80)
                    print(f"Total rows: {len(rows)}\n")
                else:
                    print("\nNo results found.\n")
            else:
                # For non-SELECT queries, commit and show rowcount
                await session.commit()
                print(f"\nQuery executed successfully. Rows affected: {result.rowcount}\n")

        except Exception as e:
            print(f"\nError executing query: {e}\n")


async def interactive_mode():
    """Run interactive query mode"""
    print("="*80)
    print("SMARTCANOPY INTERACTIVE DATABASE QUERY TOOL")
    print("="*80)
    print("\nUseful queries:")
    print("  - SELECT * FROM plant_species;")
    print("  - SELECT common_name, co2_sequestration_kg_year FROM plant_species ORDER BY co2_sequestration_kg_year DESC;")
    print("  - SELECT * FROM plant_species WHERE hardiness_zone_min <= 7 AND hardiness_zone_max >= 7;")
    print("  - SELECT COUNT(*) FROM plant_species;")
    print("  - SELECT * FROM planting_sites;")
    print("\nType 'exit' or 'quit' to exit.\n")

    while True:
        try:
            # Get query from user
            query = input("SQL> ").strip()

            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!\n")
                break

            if not query:
                continue

            # Run the query
            await run_query(query)

        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            break
        except EOFError:
            print("\n\nGoodbye!\n")
            break


if __name__ == "__main__":
    try:
        asyncio.run(interactive_mode())
    except Exception as e:
        logger.error(f"Error: {e}")
        print("\nMake sure:")
        print("1. Database is running (docker-compose up -d postgres)")
        print("2. .env file is configured with correct DATABASE_URL")
