"""
Raw API Pipeline Example

A pure Python pipeline demonstrating AgentWire without any framework.
Uses only the AgentWire SDK (wrap, session, emit).

Pipeline: Data Fetcher → Processor → Analyzer → Reporter
"""

import time
import json
import agentwire as aw


class DataFetcher:
    """Fetches data from a source."""
    
    def run(self, source: str) -> dict:
        """Fetch data from source."""
        time.sleep(0.2)
        
        # Mock data
        return {
            "source": source,
            "records": [
                {"id": 1, "value": 42, "status": "active"},
                {"id": 2, "value": 17, "status": "active"},
                {"id": 3, "value": 99, "status": "inactive"},
                {"id": 4, "value": 23, "status": "active"},
                {"id": 5, "value": 56, "status": "active"},
            ],
            "timestamp": "2024-01-15T10:30:00Z",
        }


class DataProcessor:
    """Processes and transforms data."""
    
    def run(self, data: dict) -> dict:
        """Process data."""
        time.sleep(0.3)
        
        # Filter active records
        active_records = [
            r for r in data["records"]
            if r["status"] == "active"
        ]
        
        # Calculate statistics
        values = [r["value"] for r in active_records]
        
        return {
            "source": data["source"],
            "total_records": len(data["records"]),
            "active_records": len(active_records),
            "values": values,
            "sum": sum(values),
            "avg": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
        }


class DataAnalyzer:
    """Analyzes processed data."""
    
    def run(self, processed: dict) -> dict:
        """Analyze data."""
        time.sleep(0.2)
        
        avg = processed["avg"]
        
        # Classify based on average
        if avg > 50:
            classification = "high"
            recommendation = "Monitor closely"
        elif avg > 30:
            classification = "medium"
            recommendation = "Standard monitoring"
        else:
            classification = "low"
            recommendation = "Minimal monitoring"
        
        return {
            "classification": classification,
            "recommendation": recommendation,
            "confidence": 0.95,
            "metrics": {
                "total": processed["total_records"],
                "active": processed["active_records"],
                "average": processed["avg"],
            }
        }


class Reporter:
    """Generates final report."""
    
    def run(self, analysis: dict) -> str:
        """Generate report."""
        time.sleep(0.1)
        
        report = f"""
DATA ANALYSIS REPORT
{'=' * 50}

Classification: {analysis['classification'].upper()}
Confidence: {analysis['confidence'] * 100:.1f}%

Metrics:
  - Total Records: {analysis['metrics']['total']}
  - Active Records: {analysis['metrics']['active']}
  - Average Value: {analysis['metrics']['average']:.2f}

Recommendation:
  {analysis['recommendation']}

{'=' * 50}
"""
        return report.strip()


def main():
    """Run the data pipeline."""
    print("📊 Raw API Pipeline Example")
    print("=" * 60)
    print()
    
    # Configure AgentWire
    aw.configure(bus_url="http://localhost:8000")
    print("✓ Configured AgentWire")
    
    # Create agents (no framework, just wrap)
    fetcher = aw.wrap(DataFetcher(), name="fetcher")
    processor = aw.wrap(DataProcessor(), name="processor")
    analyzer = aw.wrap(DataAnalyzer(), name="analyzer")
    reporter = aw.wrap(Reporter(), name="reporter")
    
    print("✓ Created 4 agents: fetcher, processor, analyzer, reporter")
    print()
    
    # Run pipeline within a session
    source = "production-database"
    
    with aw.session("raw-api-demo", name="Raw API Pipeline"):
        print(f"📝 Source: {source}")
        print()
        
        # Step 1: Fetch data
        print("1️⃣  Fetcher retrieving data...")
        data = fetcher.run(source)
        print(f"   ✓ Fetched {len(data['records'])} records")
        print()
        
        # Step 2: Process data
        print("2️⃣  Processor transforming data...")
        processed = processor.run(data)
        print(f"   ✓ Processed {processed['active_records']}/{processed['total_records']} active records")
        print(f"   Stats: sum={processed['sum']}, avg={processed['avg']:.2f}")
        print()
        
        # Step 3: Analyze data
        print("3️⃣  Analyzer evaluating data...")
        analysis = analyzer.run(processed)
        print(f"   ✓ Classification: {analysis['classification']}")
        print(f"   Confidence: {analysis['confidence'] * 100:.1f}%")
        print()
        
        # Step 4: Generate report
        print("4️⃣  Reporter generating final report...")
        report = reporter.run(analysis)
        print(f"   ✓ Report generated")
        print()
        
        print(report)
    
    print()
    print("✅ Pipeline complete!")
    print()
    print("=" * 60)
    print("View in AgentWire Dashboard:")
    print("  1. Open http://localhost:8000")
    print("  2. See linear pipeline in Feed view")
    print("  3. Switch to Graph view:")
    print("     fetcher → processor → analyzer → reporter")
    print("  4. Use Replay to see data flow")
    print("=" * 60)


if __name__ == "__main__":
    main()
