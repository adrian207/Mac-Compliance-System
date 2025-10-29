"""
Integration Tests for Security Tool Connectors

Author: Adrian Johnson <adrian207@gmail.com>

Tests integration connectors with mock or live APIs.
"""

import asyncio
import sys
import os
from datetime import datetime, UTC

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from integrations.models import Integration, IntegrationType
from integrations.connectors import (
    KandjiConnector,
    ZscalerConnector,
    SeraphicConnector,
    OktaConnector,
    CrowdStrikeConnector
)


class IntegrationTestRunner:
    """
    Test runner for integration connectors.
    
    Can run against mock APIs or live credentials.
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize test runner.
        
        Args:
            use_mock: Use mock APIs instead of live credentials
        """
        self.use_mock = use_mock
        self.results = {}
    
    def create_mock_kandji_integration(self) -> Integration:
        """Create mock Kandji integration."""
        return Integration(
            integration_id="TEST-KANDJI-001",
            name="Test Kandji",
            integration_type=IntegrationType.KANDJI,
            endpoint="http://localhost:8001",  # Mock server
            auth_type="bearer",
            api_key="mock-kandji-token-123",
            sync_enabled=True,
            sync_devices=True,
            sync_users=True,
            sync_policies=True,
            enabled=True
        )
    
    def create_live_kandji_integration(self) -> Integration:
        """Create live Kandji integration from environment."""
        return Integration(
            integration_id="LIVE-KANDJI-001",
            name="Live Kandji",
            integration_type=IntegrationType.KANDJI,
            endpoint=os.getenv("KANDJI_ENDPOINT", "https://yourtenant.api.kandji.io"),
            auth_type="bearer",
            api_key=os.getenv("KANDJI_API_KEY", ""),
            sync_enabled=True,
            sync_devices=True,
            sync_users=True,
            sync_policies=True,
            enabled=True
        )
    
    async def test_kandji(self) -> dict:
        """Test Kandji connector."""
        print("\n" + "="*60)
        print("TESTING KANDJI MDM CONNECTOR")
        print("="*60)
        
        integration = (
            self.create_mock_kandji_integration() 
            if self.use_mock 
            else self.create_live_kandji_integration()
        )
        
        connector = KandjiConnector(integration)
        results = {
            "integration_type": "kandji",
            "mode": "mock" if self.use_mock else "live",
            "tests": {}
        }
        
        try:
            # Test 1: Connection test
            print("\n[1/5] Testing connection...")
            connection_result = await connector.test_connection()
            results["tests"]["connection"] = connection_result
            print(f"  ✓ Connection: {connection_result.get('success')}")
            if connection_result.get("success"):
                print(f"    API Version: {connection_result.get('api_version')}")
            else:
                print(f"    Error: {connection_result.get('message')}")
            
            # Test 2: Sync devices
            print("\n[2/5] Syncing devices...")
            devices_result = await connector.sync_devices()
            results["tests"]["devices"] = devices_result
            if devices_result.get("success"):
                device_count = devices_result.get("devices_synced", 0)
                print(f"  ✓ Devices synced: {device_count}")
                if device_count > 0:
                    device = devices_result["devices"][0]
                    print(f"    Sample: {device.get('device_name')} ({device.get('serial_number')})")
                    print(f"    Compliance: {device.get('compliance_status')}")
            else:
                print(f"  ✗ Sync failed: {devices_result.get('error')}")
            
            # Test 3: Sync users
            print("\n[3/5] Syncing users...")
            users_result = await connector.sync_users()
            results["tests"]["users"] = users_result
            if users_result.get("success"):
                user_count = users_result.get("users_synced", 0)
                print(f"  ✓ Users synced: {user_count}")
                if user_count > 0:
                    user = users_result["users"][0]
                    print(f"    Sample: {user.get('name')} ({user.get('email')})")
            else:
                print(f"  ✗ Sync failed: {users_result.get('error')}")
            
            # Test 4: Sync policies
            print("\n[4/5] Syncing policies...")
            policies_result = await connector.sync_policies()
            results["tests"]["policies"] = policies_result
            if policies_result.get("success"):
                policy_count = policies_result.get("policies_synced", 0)
                print(f"  ✓ Policies synced: {policy_count}")
                if policy_count > 0:
                    policy = policies_result["policies"][0]
                    print(f"    Sample: {policy.get('name')}")
            else:
                print(f"  ✗ Sync failed: {policies_result.get('error')}")
            
            # Test 5: Webhook processing
            print("\n[5/5] Testing webhook processing...")
            mock_webhook = {
                "event_type": "device.enrolled",
                "device": {
                    "device_id": "test-device-123",
                    "serial_number": "C02TEST123",
                    "device_name": "Test-MacBook",
                    "user": {"email": "test@example.com"}
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
            webhook_result = connector.process_webhook(mock_webhook, {})
            results["tests"]["webhook"] = webhook_result
            if webhook_result.get("processed"):
                print(f"  ✓ Webhook processed: {webhook_result.get('event_type')}")
            else:
                print(f"  ✗ Webhook processing failed")
            
            # Clean up
            await connector.close()
            
            # Overall result
            all_success = all(
                test.get("success", test.get("processed", False))
                for test in results["tests"].values()
            )
            results["overall_success"] = all_success
            
            print(f"\n{'='*60}")
            print(f"KANDJI TEST RESULT: {'✓ PASSED' if all_success else '✗ FAILED'}")
            print(f"{'='*60}")
            
            return results
        
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results["error"] = str(e)
            results["overall_success"] = False
            return results
    
    async def test_all_integrations(self) -> dict:
        """Test all integration connectors."""
        print("\n")
        print("█" * 70)
        print("  INTEGRATION CONNECTORS TEST SUITE")
        print(f"  Mode: {'MOCK' if self.use_mock else 'LIVE'}")
        print(f"  Started: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("█" * 70)
        
        # Test Kandji
        self.results["kandji"] = await self.test_kandji()
        
        # TODO: Add other integrations when mock servers are ready
        # self.results["zscaler"] = await self.test_zscaler()
        # self.results["seraphic"] = await self.test_seraphic()
        # self.results["okta"] = await self.test_okta()
        # self.results["crowdstrike"] = await self.test_crowdstrike()
        
        # Summary
        print("\n" + "█" * 70)
        print("  TEST SUMMARY")
        print("█" * 70)
        
        total_integrations = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get("overall_success"))
        failed = total_integrations - passed
        
        print(f"\nTotal Integrations Tested: {total_integrations}")
        print(f"  ✓ Passed: {passed}")
        print(f"  ✗ Failed: {failed}")
        
        for integration_name, result in self.results.items():
            status = "✓ PASSED" if result.get("overall_success") else "✗ FAILED"
            print(f"\n{integration_name.upper()}: {status}")
            if not result.get("overall_success") and result.get("error"):
                print(f"  Error: {result.get('error')}")
        
        print("\n" + "█" * 70)
        print(f"  Completed: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("█" * 70 + "\n")
        
        return {
            "total": total_integrations,
            "passed": passed,
            "failed": failed,
            "results": self.results
        }


async def main():
    """Main test function."""
    import argparse
    import io
    
    # Fix Windows encoding issues
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(description="Test Integration Connectors")
    parser.add_argument(
        "--mode",
        choices=["mock", "live"],
        default="mock",
        help="Test mode: mock (local mock servers) or live (real APIs)"
    )
    parser.add_argument(
        "--integration",
        choices=["all", "kandji", "zscaler", "seraphic", "okta", "crowdstrike"],
        default="all",
        help="Which integration to test"
    )
    
    args = parser.parse_args()
    
    use_mock = args.mode == "mock"
    
    if use_mock:
        print("\n[!] MOCK MODE: Using local mock servers")
        print("   Make sure mock servers are running:")
        print("   python tests/mocks/mock_kandji.py")
    else:
        print("\n[!] LIVE MODE: Using real API credentials")
        print("   Make sure environment variables are set:")
        print("   KANDJI_ENDPOINT, KANDJI_API_KEY, etc.")
    
    runner = IntegrationTestRunner(use_mock=use_mock)
    
    if args.integration == "all":
        results = await runner.test_all_integrations()
    elif args.integration == "kandji":
        results = {"kandji": await runner.test_kandji()}
    else:
        print(f"Integration {args.integration} test not yet implemented")
        return
    
    # Exit with appropriate code
    if results.get("failed", 0) == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

