"""
End-to-End User Journey Test

This test simulates a complete user flow through the SmartCanopy system:
1. User analyzes an address for planting sites
2. Views recommended species for a site
3. Asks about environmental benefits
4. Checks safety/hazards
5. Gets pricing information
6. Receives planting instructions

This is the "Science Fair Demo" scenario.
"""

import pytest
import asyncio
from agent.agent import SmartCanopyAgent
from agent.services.plant_database import DatabaseManager, PlantSpecies, PlantingSite
from agent.services.cache_service import CacheService
from agent.tools import (
    SpeciesRecommenderTool,
    PricingCalculatorTool,
    EnvironmentalCalculatorTool,
    HazardCheckerTool,
    MaintenanceGuideTool,
    PlantingInstructionsTool
)
from unittest.mock import patch, AsyncMock, Mock
import uuid


@pytest.mark.asyncio
class TestEndToEndUserJourney:
    """
    Complete end-to-end test of user journey through the system
    """

    @pytest.fixture
    async def full_system_setup(self, db_manager, cache_service):
        """
        Set up a complete system with database, cache, and sample data
        """
        # Create sample species
        async with db_manager.get_session() as session:
            species = PlantSpecies(
                species_id="PLAC",
                common_name="American Sycamore",
                scientific_name="Platanus occidentalis",
                tree_type="deciduous",
                hardiness_zone_min=4,
                hardiness_zone_max=9,
                mature_height_ft=75,
                mature_spread_ft=50,
                growth_rate="fast",
                drought_tolerant=False,
                native_regions=["Eastern US", "Midwest"],
                environmental_benefits={
                    "co2_sequestration_kg_year": 95.2,
                    "air_quality_improvement_kg_year": 12.4,
                    "stormwater_interception_gallons_year": 775.62,
                    "energy_savings_kwh_year": 124.8
                },
                pricing={
                    "sapling": 25.0,
                    "6ft": 125.0,
                    "8ft": 185.0,
                    "10ft": 275.0
                },
                maintenance_notes={
                    "watering": "Regular watering for first 2 years",
                    "pruning": "Prune in late winter"
                },
                planting_instructions={
                    "soil_type": "Moist, well-drained",
                    "sunlight": "Full sun"
                }
            )
            session.add(species)
            await session.commit()

        # Create sample planting site
        site_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())

        async with db_manager.get_session() as session:
            site = PlantingSite(
                site_id=site_id,
                analysis_id=analysis_id,
                address="123 Main St, San Jose, CA 95123",
                latitude=37.2948,
                longitude=-121.8700,
                location_pixels={"x": 256, "y": 256},
                avg_ndvi=0.45,
                ndvi_category="moderate_vegetation",
                avg_slope=3.2,
                slope_category="flat",
                area_pixels=250,
                suitability_score=0.78,
                osm_data={"roads": False, "buildings": False}
            )
            session.add(site)
            await session.commit()

        # Create tools
        tools = [
            SpeciesRecommenderTool(db_manager, cache_service),
            PricingCalculatorTool(db_manager),
            EnvironmentalCalculatorTool(db_manager, cache_service),
            HazardCheckerTool(db_manager),
            MaintenanceGuideTool(db_manager),
            PlantingInstructionsTool(db_manager)
        ]

        # Create agent
        agent = SmartCanopyAgent(tools=tools)

        return {
            "agent": agent,
            "db_manager": db_manager,
            "cache_service": cache_service,
            "site_id": site_id,
            "analysis_id": analysis_id
        }

    async def test_complete_user_journey(self, full_system_setup, mock_hardiness_zone_api):
        """
        Test the complete user journey from site analysis to planting instructions
        """
        setup = await full_system_setup
        agent = setup["agent"]
        site_id = setup["site_id"]

        # Mock Claude API responses
        with patch.object(agent, 'client') as mock_client:
            conversation_history = []

            # ===== STEP 1: User asks for species recommendation =====
            print("\n===== STEP 1: Species Recommendation =====")

            # Mock Claude response that uses species_recommender tool
            mock_response_1 = Mock()
            mock_response_1.content = [
                type('obj', (object,), {
                    'type': 'tool_use',
                    'id': 'tool_001',
                    'name': 'species_recommender',
                    'input': {
                        'planting_site_id': site_id,
                        'zip_code': '95123',
                        'purpose': ['shade']
                    }
                })()
            ]
            mock_response_1.stop_reason = "tool_use"
            mock_response_1.model = "claude-opus-4-5-20251101"
            mock_response_1.usage = type('obj', (object,), {'input_tokens': 100, 'output_tokens': 50})()

            # Mock final response after tool execution
            mock_response_1_final = Mock()
            mock_response_1_final.content = [
                type('obj', (object,), {
                    'type': 'text',
                    'text': 'I recommend the American Sycamore for your site. It provides excellent shade and is well-suited to your conditions.'
                })()
            ]
            mock_response_1_final.stop_reason = "end_turn"
            mock_response_1_final.model = "claude-opus-4-5-20251101"
            mock_response_1_final.usage = type('obj', (object,), {'input_tokens': 200, 'output_tokens': 100})()

            mock_client.messages.create = AsyncMock(side_effect=[mock_response_1, mock_response_1_final])

            result_1 = await agent.chat(
                message=f"What tree should I plant at site {site_id}?",
                conversation_history=conversation_history
            )

            assert result_1 is not None
            assert "Sycamore" in result_1["response"]
            assert len(result_1["tool_calls"]) > 0
            assert result_1["tool_calls"][0]["tool"] == "species_recommender"

            conversation_history = result_1["conversation_history"]
            print(f"✓ Species recommended: American Sycamore")

            # ===== STEP 2: User asks about environmental benefits =====
            print("\n===== STEP 2: Environmental Benefits =====")

            mock_response_2 = Mock()
            mock_response_2.content = [
                type('obj', (object,), {
                    'type': 'tool_use',
                    'id': 'tool_002',
                    'name': 'environmental_calculator',
                    'input': {
                        'species_id': 'PLAC',
                        'quantity': 1,
                        'years_projection': 20
                    }
                })()
            ]
            mock_response_2.stop_reason = "tool_use"
            mock_response_2.model = "claude-opus-4-5-20251101"
            mock_response_2.usage = type('obj', (object,), {'input_tokens': 100, 'output_tokens': 50})()

            mock_response_2_final = Mock()
            mock_response_2_final.content = [
                type('obj', (object,), {
                    'type': 'text',
                    'text': 'Over 20 years, one American Sycamore will sequester approximately 1,904 kg of CO2 and intercept about 15,512 gallons of stormwater.'
                })()
            ]
            mock_response_2_final.stop_reason = "end_turn"
            mock_response_2_final.model = "claude-opus-4-5-20251101"
            mock_response_2_final.usage = type('obj', (object,), {'input_tokens': 200, 'output_tokens': 100})()

            mock_client.messages.create = AsyncMock(side_effect=[mock_response_2, mock_response_2_final])

            result_2 = await agent.chat(
                message="How much CO2 will an American Sycamore capture over 20 years?",
                conversation_history=conversation_history
            )

            assert "CO2" in result_2["response"] or "carbon" in result_2["response"].lower()
            assert len(result_2["tool_calls"]) > 0
            assert result_2["tool_calls"][0]["tool"] == "environmental_calculator"

            conversation_history = result_2["conversation_history"]
            print(f"✓ Environmental benefits calculated")

            # ===== STEP 3: User asks about safety =====
            print("\n===== STEP 3: Safety Check =====")

            mock_response_3 = Mock()
            mock_response_3.content = [
                type('obj', (object,), {
                    'type': 'tool_use',
                    'id': 'tool_003',
                    'name': 'hazard_checker',
                    'input': {
                        'planting_site_id': site_id,
                        'mature_tree_height_ft': 75,
                        'mature_spread_ft': 50
                    }
                })()
            ]
            mock_response_3.stop_reason = "tool_use"
            mock_response_3.model = "claude-opus-4-5-20251101"
            mock_response_3.usage = type('obj', (object,), {'input_tokens': 100, 'output_tokens': 50})()

            mock_response_3_final = Mock()
            mock_response_3_final.content = [
                type('obj', (object,), {
                    'type': 'text',
                    'text': 'Your site is safe for planting. Make sure to call 811 before digging to locate underground utilities.'
                })()
            ]
            mock_response_3_final.stop_reason = "end_turn"
            mock_response_3_final.model = "claude-opus-4-5-20251101"
            mock_response_3_final.usage = type('obj', (object,), {'input_tokens': 200, 'output_tokens': 100})()

            mock_client.messages.create = AsyncMock(side_effect=[mock_response_3, mock_response_3_final])

            result_3 = await agent.chat(
                message="Is it safe to plant here?",
                conversation_history=conversation_history
            )

            assert "safe" in result_3["response"].lower() or "811" in result_3["response"]
            assert len(result_3["tool_calls"]) > 0
            assert result_3["tool_calls"][0]["tool"] == "hazard_checker"

            conversation_history = result_3["conversation_history"]
            print(f"✓ Safety check complete")

            # ===== STEP 4: User asks about pricing =====
            print("\n===== STEP 4: Pricing =====")

            mock_response_4 = Mock()
            mock_response_4.content = [
                type('obj', (object,), {
                    'type': 'tool_use',
                    'id': 'tool_004',
                    'name': 'pricing_calculator',
                    'input': {
                        'species_id': 'PLAC',
                        'quantity': 1,
                        'tree_size': '6ft',
                        'include_planting': True,
                        'zip_code': '95123'
                    }
                })()
            ]
            mock_response_4.stop_reason = "tool_use"
            mock_response_4.model = "claude-opus-4-5-20251101"
            mock_response_4.usage = type('obj', (object,), {'input_tokens': 100, 'output_tokens': 50})()

            mock_response_4_final = Mock()
            mock_response_4_final.content = [
                type('obj', (object,), {
                    'type': 'text',
                    'text': 'A 6-foot American Sycamore with professional planting will cost approximately $425.'
                })()
            ]
            mock_response_4_final.stop_reason = "end_turn"
            mock_response_4_final.model = "claude-opus-4-5-20251101"
            mock_response_4_final.usage = type('obj', (object,), {'input_tokens': 200, 'output_tokens': 100})()

            mock_client.messages.create = AsyncMock(side_effect=[mock_response_4, mock_response_4_final])

            result_4 = await agent.chat(
                message="How much will a 6-foot tree cost with planting?",
                conversation_history=conversation_history
            )

            assert "$" in result_4["response"] or "cost" in result_4["response"].lower()
            assert len(result_4["tool_calls"]) > 0
            assert result_4["tool_calls"][0]["tool"] == "pricing_calculator"

            conversation_history = result_4["conversation_history"]
            print(f"✓ Pricing calculated")

            # ===== STEP 5: User asks for planting instructions =====
            print("\n===== STEP 5: Planting Instructions =====")

            mock_response_5 = Mock()
            mock_response_5.content = [
                type('obj', (object,), {
                    'type': 'tool_use',
                    'id': 'tool_005',
                    'name': 'planting_instructions',
                    'input': {
                        'species_id': 'PLAC',
                        'planting_site_id': site_id,
                        'tree_size': '6ft'
                    }
                })()
            ]
            mock_response_5.stop_reason = "tool_use"
            mock_response_5.model = "claude-opus-4-5-20251101"
            mock_response_5.usage = type('obj', (object,), {'input_tokens': 100, 'output_tokens': 50})()

            mock_response_5_final = Mock()
            mock_response_5_final.content = [
                type('obj', (object,), {
                    'type': 'text',
                    'text': 'Here are step-by-step planting instructions for your American Sycamore...'
                })()
            ]
            mock_response_5_final.stop_reason = "end_turn"
            mock_response_5_final.model = "claude-opus-4-5-20251101"
            mock_response_5_final.usage = type('obj', (object,), {'input_tokens': 200, 'output_tokens': 100})()

            mock_client.messages.create = AsyncMock(side_effect=[mock_response_5, mock_response_5_final])

            result_5 = await agent.chat(
                message="How do I plant it?",
                conversation_history=conversation_history
            )

            assert "plant" in result_5["response"].lower() or "instructions" in result_5["response"].lower()
            assert len(result_5["tool_calls"]) > 0
            assert result_5["tool_calls"][0]["tool"] == "planting_instructions"

            print(f"✓ Planting instructions provided")

            # ===== VERIFY COMPLETE JOURNEY =====
            print("\n===== JOURNEY COMPLETE =====")
            print(f"Total conversation turns: {len(result_5['conversation_history'])}")
            print(f"✓ All 5 steps completed successfully")

            # Verify that all required tools were used
            all_tool_calls = []
            for result in [result_1, result_2, result_3, result_4, result_5]:
                all_tool_calls.extend([tc["tool"] for tc in result["tool_calls"]])

            assert "species_recommender" in all_tool_calls
            assert "environmental_calculator" in all_tool_calls
            assert "hazard_checker" in all_tool_calls
            assert "pricing_calculator" in all_tool_calls
            assert "planting_instructions" in all_tool_calls

            # Verify conversation continuity
            assert len(result_5["conversation_history"]) >= 10  # At least 5 user + 5 assistant messages

            return True

    async def test_journey_with_multiple_species(self, full_system_setup, mock_hardiness_zone_api):
        """
        Test comparing multiple species
        """
        setup = await full_system_setup
        db_manager = setup["db_manager"]

        # Add another species for comparison
        async with db_manager.get_session() as session:
            oak = PlantSpecies(
                species_id="QURU",
                common_name="Red Oak",
                scientific_name="Quercus rubra",
                tree_type="deciduous",
                hardiness_zone_min=4,
                hardiness_zone_max=8,
                mature_height_ft=60,
                mature_spread_ft=40,
                growth_rate="medium",
                drought_tolerant=False,
                native_regions=["Eastern US"],
                environmental_benefits={
                    "co2_sequestration_kg_year": 85.0,
                    "air_quality_improvement_kg_year": 10.0,
                    "stormwater_interception_gallons_year": 650.0,
                    "energy_savings_kwh_year": 110.0
                },
                pricing={"sapling": 30.0, "6ft": 150.0, "8ft": 220.0, "10ft": 320.0},
                maintenance_notes={},
                planting_instructions={}
            )
            session.add(oak)
            await session.commit()

        # Now user can compare both species
        print("✓ Multiple species available for comparison")
