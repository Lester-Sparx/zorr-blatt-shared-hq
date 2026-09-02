from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
RUNTIME_CONTRACT = ROOT / "docs" / "DUNCAN_RUNTIME_LEARNING_CONTEXT_R01.md"


class DuncanRuntimeLearningConsumptionTests(unittest.TestCase):
    def test_agents_bootstrap_consumes_validated_duncan_context(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        self.assertIn(
            "zb-archive-v1:hq/archive-v1/derived/duncan-night-v1/DUNCAN_CONTEXT_NEXT.json",
            text,
        )
        self.assertIn("DUNCAN_RUNTIME_LEARNING_CONTEXT_R01", text)
        self.assertIn(
            "OWNER_INTENT -> DURABLE_STATE -> RELEVANT_LEARNING -> ANTI_REGRESSION_CHECK -> ACTION",
            text,
        )

    def test_runtime_contract_distinguishes_persistence_from_consumption(self) -> None:
        text = RUNTIME_CONTRACT.read_text(encoding="utf-8")
        self.assertIn("persistence/rebuildability guarantee", text)
        self.assertIn("does not by itself prove", text)
        self.assertIn("Immediate OWNER correction law", text)
        self.assertIn("IMAGE_GENERATION_FOR_NON_IMAGE_TASK", text)
        self.assertIn("OVERFORMALIZE_SIMPLE_GOAL", text)
        self.assertIn("3-4 KEY DRAWINGS/POSES", text)


if __name__ == "__main__":
    unittest.main()
