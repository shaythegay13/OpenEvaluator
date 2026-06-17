#!/usr/bin/env python3
"""
Property Database Manager - Phase 5.1

Manages the property database with:
- Persistent storage (JSON file)
- Import/export capabilities
- Multi-town support
- Easy property addition and lookup

Database file: property_database.json
Structure: { "town_name": { "map,lot": {...property_data...}, ... }, ... }
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
import csv
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_FILE = Path(__file__).parent / "property_database.json"


class PropertyDatabaseManager:
    """Manage persistent property database"""

    def __init__(self, db_file: Path = DATABASE_FILE):
        self.db_file = db_file
        self.properties = self._load_database()

    def _load_database(self) -> Dict:
        """Load properties from JSON file, or return empty dict if file doesn't exist"""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded property database from {self.db_file}")
                return data
            except Exception as e:
                logger.warning(f"Error loading database: {e}, starting fresh")
                return {}
        return {}

    def _save_database(self) -> None:
        """Save properties to JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.properties, f, indent=2)
            logger.info(f"Saved property database to {self.db_file}")
        except Exception as e:
            logger.error(f"Error saving database: {e}")

    def add_property(
        self,
        town: str,
        map_num: str,
        lot_num: str,
        property_data: Dict,
    ) -> None:
        """Add or update a property in the database"""
        if town not in self.properties:
            self.properties[town] = {}

        key = f"{map_num},{lot_num}"
        self.properties[town][key] = property_data
        self._save_database()
        logger.info(f"✓ Added property: {town} Map {map_num} Lot {lot_num}")

    def get_property(self, town: str, map_num: str, lot_num: str) -> Optional[Dict]:
        """Retrieve a property from the database"""
        if town not in self.properties:
            return None
        key = f"{map_num},{lot_num}"
        return self.properties[town].get(key)

    def list_towns(self) -> List[str]:
        """List all towns with properties in database"""
        return sorted(self.properties.keys())

    def count_properties(self, town: Optional[str] = None) -> int:
        """Count properties, optionally by town"""
        if town:
            return len(self.properties.get(town, {}))
        return sum(len(props) for props in self.properties.values())

    def list_properties(self, town: str) -> List[Dict]:
        """List all properties in a town"""
        if town not in self.properties:
            return []
        return [
            {**data, "map": key.split(",")[0], "lot": key.split(",")[1]}
            for key, data in self.properties[town].items()
        ]

    def import_from_csv(self, csv_file: Path) -> int:
        """
        Import properties from CSV file

        CSV format (with headers):
        town,map,lot,address,owner,acreage,road_name,road_type,confidence

        Returns: number of properties imported
        """
        count = 0
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    town = row.get("town", "").strip()
                    map_num = row.get("map", "").strip()
                    lot_num = row.get("lot", "").strip()

                    if not (town and map_num and lot_num):
                        logger.warning(f"Skipping row with missing identifiers: {row}")
                        continue

                    property_data = {
                        "map": map_num,
                        "lot": lot_num,
                        "town": town,
                        "address": row.get("address", "").strip(),
                        "owner": row.get("owner", "").strip(),
                        "acreage": float(row.get("acreage", 0)) if row.get("acreage") else None,
                        "road_name": row.get("road_name", "").strip(),
                        "road_type": row.get("road_type", "").strip(),
                        "confidence": row.get("confidence", "medium").strip(),
                        "sources": [f"CSV import from {csv_file.name}"],
                        "research_date": datetime.now().isoformat(),
                    }

                    # Remove None/empty values
                    property_data = {k: v for k, v in property_data.items() if v}

                    self.add_property(town, map_num, lot_num, property_data)
                    count += 1

            logger.info(f"✓ Imported {count} properties from {csv_file}")
            return count

        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return count

    def export_to_csv(self, csv_file: Path, town: Optional[str] = None) -> int:
        """
        Export properties to CSV file

        Args:
            csv_file: Path to output CSV file
            town: Optional - export only this town (or all if None)

        Returns: number of properties exported
        """
        try:
            towns_to_export = [town] if town else self.list_towns()
            count = 0

            with open(csv_file, 'w', newline='') as f:
                fieldnames = [
                    "town", "map", "lot", "address", "owner", "acreage",
                    "road_name", "road_type", "confidence", "research_date"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for t in towns_to_export:
                    for key, data in self.properties.get(t, {}).items():
                        map_num, lot_num = key.split(",")
                        row = {
                            "town": t,
                            "map": map_num,
                            "lot": lot_num,
                            "address": data.get("address", ""),
                            "owner": data.get("owner", ""),
                            "acreage": data.get("acreage", ""),
                            "road_name": data.get("road_name", ""),
                            "road_type": data.get("road_type", ""),
                            "confidence": data.get("confidence", ""),
                            "research_date": data.get("research_date", ""),
                        }
                        writer.writerow(row)
                        count += 1

            logger.info(f"✓ Exported {count} properties to {csv_file}")
            return count

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return 0

    def get_summary(self) -> str:
        """Get a summary of database contents"""
        lines = ["Property Database Summary", "=" * 50]

        towns = self.list_towns()
        total = self.count_properties()

        lines.append(f"Total towns: {len(towns)}")
        lines.append(f"Total properties: {total}")
        lines.append("")

        for town in towns:
            count = self.count_properties(town)
            lines.append(f"  {town}: {count} properties")

        return "\n".join(lines)


def main():
    """CLI for property database management"""
    import argparse

    parser = argparse.ArgumentParser(description="Property Database Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Summary command
    subparsers.add_parser("summary", help="Show database summary")

    # Add property command
    add_parser = subparsers.add_parser("add", help="Add a property")
    add_parser.add_argument("town", help="Maine town name")
    add_parser.add_argument("map", help="Tax map number")
    add_parser.add_argument("lot", help="Lot number")
    add_parser.add_argument("--address", help="Property address")
    add_parser.add_argument("--owner", help="Owner name")
    add_parser.add_argument("--acreage", type=float, help="Acreage")
    add_parser.add_argument("--road-name", help="Road name")
    add_parser.add_argument("--road-type", help="Road type (Public/Private)")
    add_parser.add_argument("--confidence", default="medium", help="Confidence (high/medium/low)")

    # List command
    list_parser = subparsers.add_parser("list", help="List properties in a town")
    list_parser.add_argument("town", help="Maine town name")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import from CSV")
    import_parser.add_argument("csv_file", type=Path, help="CSV file to import")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export to CSV")
    export_parser.add_argument("csv_file", type=Path, help="CSV file to create")
    export_parser.add_argument("--town", help="Optional: export only this town")

    args = parser.parse_args()
    manager = PropertyDatabaseManager()

    if args.command == "summary":
        print(manager.get_summary())

    elif args.command == "add":
        property_data = {
            "map": args.map,
            "lot": args.lot,
            "town": args.town,
            "address": args.address,
            "owner": args.owner,
            "acreage": args.acreage,
            "road_name": args.road_name,
            "road_type": args.road_type,
            "confidence": args.confidence,
            "sources": ["Manual entry"],
            "research_date": datetime.now().isoformat(),
        }
        property_data = {k: v for k, v in property_data.items() if v is not None}
        manager.add_property(args.town, args.map, args.lot, property_data)

    elif args.command == "list":
        props = manager.list_properties(args.town)
        if not props:
            print(f"No properties found for {args.town}")
        else:
            print(f"\nProperties in {args.town}:")
            for prop in props:
                print(f"  Map {prop['map']} Lot {prop['lot']}: {prop.get('address', 'N/A')}")

    elif args.command == "import":
        count = manager.import_from_csv(args.csv_file)
        print(manager.get_summary())

    elif args.command == "export":
        count = manager.export_to_csv(args.csv_file, args.town)
        print(f"Exported {count} properties to {args.csv_file}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
