"""
Unit tests for the Cost Domain Manager
"""

import asyncio
import unittest
import time
from unittest.mock import patch

from cost_domain.cost_domain_manager import (
    CostDomainManager,
    TokenUsage,
    Budget,
    TopicBudget,
    SpendingAlert
)


class TestCostDomainManager(unittest.IsolatedAsyncioTestCase):
    """Test cases for the Cost Domain Manager"""
    
    async def asyncSetUp(self):
        """Set up the test environment"""
        self.cdm = CostDomainManager(local_mode=True)
        # Initialize the CDM
        await self.cdm.initialize()
        
        # Create a test team budget
        self.team_budget = await self.cdm.create_budget({
            "team_id": "team1",
            "total_budget": 100.0,
            "start_date": time.time(),
            "end_date": time.time() + 30 * 24 * 3600,  # 30 days from now
            "alert_threshold": 0.8,
            "tier_constraints": {
                "economy": 10.0,
                "standard": 30.0,
                "premium": 10.0
            }
        })
    
    async def test_token_usage_recording(self):
        """Test recording token usage"""
        usage = await self.cdm.record_token_usage({
            "agent_id": "agent1",
            "model": "gpt-4o",
            "prompt_tokens": 500,
            "completion_tokens": 200,
            "total_tokens": 700,
            "team_id": "team1",
            "task_id": "task-123"
        })
        
        self.assertIsNotNone(usage)
        self.assertEqual(usage.agent_id, "agent1")
        self.assertEqual(usage.model, "gpt-4o")
        self.assertEqual(usage.prompt_tokens, 500)
        self.assertEqual(usage.completion_tokens, 200)
        self.assertEqual(usage.total_tokens, 700)
        self.assertGreater(usage.estimated_cost, 0)
        
        # Get token usage for the team
        team_usage = await self.cdm.get_token_usage(
            team_id="team1",
            start_time=time.time() - 3600,  # 1 hour ago
            end_time=time.time() + 3600     # 1 hour from now
        )
        
        self.assertEqual(len(team_usage), 1)
        self.assertEqual(team_usage[0].agent_id, "agent1")
    
    async def test_topic_budget_creation(self):
        """Test creating a topic budget"""
        topic_budget = await self.cdm.create_topic_budget({
            "team_id": "team1",
            "topic_name": "user-auth-feature",
            "total_budget": 25.0,
            "start_date": time.time(),
            "end_date": time.time() + 15 * 24 * 3600,  # 15 days from now
            "alert_threshold": 0.75
        })
        
        self.assertIsNotNone(topic_budget)
        self.assertEqual(topic_budget.team_id, "team1")
        self.assertEqual(topic_budget.topic_name, "user-auth-feature")
        self.assertEqual(topic_budget.total_budget, 25.0)
        self.assertEqual(topic_budget.remaining_budget, 25.0)
        self.assertEqual(topic_budget.status, "active")
        
        # Verify the topic budget can be retrieved
        retrieved = await self.cdm.get_topic_budget("team1", "user-auth-feature")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.budget_id, topic_budget.budget_id)
        
        # Get all topic budgets for the team
        all_topics = await self.cdm.get_all_topic_budgets("team1")
        self.assertEqual(len(all_topics), 1)
    
    async def test_topic_budget_usage(self):
        """Test recording usage against a topic budget"""
        # Create a topic budget
        topic_budget = await self.cdm.create_topic_budget({
            "team_id": "team1",
            "topic_name": "database-optimization",
            "total_budget": 50.0,
            "start_date": time.time(),
            "alert_threshold": 0.8
        })
        
        # Record usage
        success, message = await self.cdm.record_topic_usage(
            team_id="team1",
            topic_name="database-optimization",
            cost=10.0
        )
        
        self.assertTrue(success)
        
        # Verify budget was updated
        updated = await self.cdm.get_topic_budget("team1", "database-optimization")
        self.assertEqual(updated.remaining_budget, 40.0)
        
        # Record usage with topic in token usage
        await self.cdm.record_token_usage({
            "agent_id": "agent2",
            "model": "claude-3-opus",
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
            "team_id": "team1",
            "task_id": "task-456",
            "topic_name": "database-optimization"
        })
        
        # Get topic spending stats
        spending = await self.cdm.get_topic_spending(
            "team1", "database-optimization", days=1
        )
        
        self.assertTrue(len(spending) > 0)
    
    async def test_topic_budget_alert(self):
        """Test topic budget alerts"""
        # Create a small topic budget to trigger alert
        topic_budget = await self.cdm.create_topic_budget({
            "team_id": "team1",
            "topic_name": "small-experiment",
            "total_budget": 10.0,
            "start_date": time.time(),
            "alert_threshold": 0.7
        })
        
        # Record usage that will trigger threshold alert (70%)
        success, message = await self.cdm.record_topic_usage(
            team_id="team1",
            topic_name="small-experiment",
            cost=7.0
        )
        
        self.assertTrue(success)
        self.assertIn("threshold", message)
        
        # Record usage that will deplete the budget
        success, message = await self.cdm.record_topic_usage(
            team_id="team1",
            topic_name="small-experiment",
            cost=3.5
        )
        
        self.assertTrue(success)
        self.assertIn("depleted", message)
        
        # Verify budget was paused automatically
        updated = await self.cdm.get_topic_budget("team1", "small-experiment")
        self.assertEqual(updated.status, "paused")
        
        # Attempt to record more usage on paused topic
        success, message = await self.cdm.record_topic_usage(
            team_id="team1",
            topic_name="small-experiment",
            cost=1.0
        )
        
        self.assertFalse(success)  # Should fail because topic is paused
    
    async def test_topic_budget_pause_resume(self):
        """Test pausing and resuming a topic budget"""
        # Create a topic budget
        topic_budget = await self.cdm.create_topic_budget({
            "team_id": "team1",
            "topic_name": "frontend-redesign",
            "total_budget": 30.0,
            "start_date": time.time(),
            "alert_threshold": 0.8
        })
        
        # Pause the budget
        paused = await self.cdm.pause_topic_budget("team1", "frontend-redesign")
        self.assertTrue(paused)
        
        # Verify it's paused
        updated = await self.cdm.get_topic_budget("team1", "frontend-redesign")
        self.assertEqual(updated.status, "paused")
        
        # Try to record usage (should fail)
        success, _ = await self.cdm.record_topic_usage(
            team_id="team1",
            topic_name="frontend-redesign",
            cost=5.0
        )
        self.assertFalse(success)
        
        # Resume the budget
        resumed = await self.cdm.resume_topic_budget("team1", "frontend-redesign")
        self.assertTrue(resumed)
        
        # Verify it's active
        updated = await self.cdm.get_topic_budget("team1", "frontend-redesign")
        self.assertEqual(updated.status, "active")
        
        # Record usage (should succeed now)
        success, _ = await self.cdm.record_topic_usage(
            team_id="team1",
            topic_name="frontend-redesign",
            cost=5.0
        )
        self.assertTrue(success)
    
    async def test_topic_budget_update(self):
        """Test updating a topic budget"""
        # Create a topic budget
        topic_budget = await self.cdm.create_topic_budget({
            "team_id": "team1",
            "topic_name": "api-integration",
            "total_budget": 20.0,
            "start_date": time.time(),
            "alert_threshold": 0.8
        })
        
        # Record some usage
        await self.cdm.record_topic_usage("team1", "api-integration", 5.0)
        
        # Verify remaining budget
        budget_before = await self.cdm.get_topic_budget("team1", "api-integration")
        self.assertEqual(budget_before.remaining_budget, 15.0)
        
        # Update the budget (increase total)
        updated = await self.cdm.update_topic_budget(
            "team1",
            "api-integration",
            {"total_budget": 30.0}
        )
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated.total_budget, 30.0)
        
        # Verify remaining budget increased by the difference
        self.assertEqual(updated.remaining_budget, 25.0)  # 15.0 + (30.0 - 20.0)
        
        # Update alert threshold
        updated = await self.cdm.update_topic_budget(
            "team1",
            "api-integration",
            {"alert_threshold": 0.9}
        )
        
        self.assertEqual(updated.alert_threshold, 0.9)
    
    async def test_budget_availability_check(self):
        """Test checking budget availability"""
        # Check general budget availability
        available, message = await self.cdm.check_budget_availability("team1", 5.0)
        self.assertTrue(available)
        
        # Check tier availability
        tier_available, tier_message = await self.cdm.check_tier_availability(
            "team1", "premium", 2.0
        )
        self.assertTrue(tier_available)
        
        # Try with an amount that exceeds the tier constraint
        tier_available, tier_message = await self.cdm.check_tier_availability(
            "team1", "premium", 15.0  # Tier limit is 10.0
        )
        self.assertFalse(tier_available)
        self.assertIn("tier", tier_message.lower())


if __name__ == '__main__':
    unittest.main() 