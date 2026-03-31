#!/usr/bin/env python3
"""Run golden dataset evaluation for consultancy_fundamentals with gpt-oss-20b."""

import asyncio
import sys
import traceback
from pathlib import Path

print("DEBUG: Script started", flush=True, file=sys.stderr)

# Add backend to path
backend_src = str(Path(__file__).resolve().parents[2] / "backend" / "src")
sys.path.insert(0, backend_src)

# Load .env file before importing Settings
from pathlib import Path
env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"DEBUG: Loaded .env from {env_path}", flush=True, file=sys.stderr)

print("DEBUG: Importing modules...", flush=True, file=sys.stderr)

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    from soft_skills_backend.config import Settings
    from soft_skills_backend.modules.evaluation.domain.evaluation import (
        suite_definition,
        load_suite_dataset,
        select_cases,
        build_marking_computation,
    )
    from soft_skills_backend.modules.evaluation.contracts.commands import EvaluationRunCommand
    from soft_skills_backend.modules.evaluation.use_cases.marking_benchmark import MarkingBenchmarkRunner
    from soft_skills_backend.platform.observability.stageflow_logging import DatabaseProviderCallLogger
    from soft_skills_backend.shared.auth import Actor
    from soft_skills_backend.platform.db.repositories import SqlAlchemyProviderCallRepository
    from soft_skills_backend.platform.providers.llm.openai_compatible import build_llm_provider
    
    # Wrapper to convert positional args to keyword args
    def provider_factory(settings, provider_call_logger):
        return build_llm_provider(settings=settings, provider_call_logger=provider_call_logger)
    
    print("DEBUG: All imports successful", flush=True, file=sys.stderr)
except Exception as e:
    print(f"ERROR during import: {e}", flush=True, file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)


class SimpleContext:
    """Simple context object that provides the metadata methods needed."""
    
    def __init__(self, request_id: str, trace_id: str, workflow_id: str, pipeline_run_id: str):
        self.request_id = request_id
        self.trace_id = trace_id
        self.workflow_id = workflow_id
        self.pipeline_run_id = pipeline_run_id
        self._metadata = {
            "request_id": request_id,
            "trace_id": trace_id,
            "workflow_id": workflow_id,
            "pipeline_run_id": pipeline_run_id,
        }
        # Create a snapshot-like object to satisfy stageflow.metadata_value
        self.snapshot = SimpleSnapshot(self._metadata)
    
    def get_metadata(self, key: str, default=None):
        return self._metadata.get(key, default)


class SimpleSnapshot:
    """Mock snapshot object for SimpleContext."""
    
    def __init__(self, metadata: dict):
        self.metadata = metadata


async def main():
    # Load base settings first
    base_settings = Settings()
    
    # Override settings to use OpenRouter for gpt-oss-20b
    settings = Settings(
        provider_name="openrouter",
        provider_api_key=base_settings.openrouter_api_key,
        provider_base_url=base_settings.openrouter_base_url,
        database_url=base_settings.database_url,
        llm_marking_per_skill_model="openai/gpt-oss-20b",
        llm_marking_aggregation_model="openai/gpt-oss-20b",
    )
    
    print(f"DEBUG: Using provider: {settings.provider_name}", flush=True, file=sys.stderr)
    
    # Setup database
    print(f"DEBUG: Connecting to {settings.database_url}", flush=True, file=sys.stderr)
    engine = create_engine(settings.database_url)
    session_factory = sessionmaker(engine)
    
    # Get the suite
    suite = suite_definition("consultancy_fundamentals_v1")
    print(f"DEBUG: Found suite: {suite.suite_id}", flush=True, file=sys.stderr)
    
    # Load dataset
    dataset = load_suite_dataset(suite)
    print(f"DEBUG: Loaded dataset: {dataset.dataset_id} with {len(dataset.cases)} cases", flush=True, file=sys.stderr)
    
    # Build command
    command = EvaluationRunCommand(
        suite_id="consultancy_fundamentals_v1",
        model_slugs=["gpt-oss-20b"],
        case_ids=[],
    )
    
    # Select cases
    selected_cases = select_cases(dataset=dataset, case_ids=command.case_ids)
    print(f"DEBUG: Selected {len(selected_cases)} cases", flush=True, file=sys.stderr)
    
    # Create runner with proper provider factory
    provider_repository = SqlAlchemyProviderCallRepository(session_factory)
    provider_logger = DatabaseProviderCallLogger(provider_repository)
    runner = MarkingBenchmarkRunner(
        settings=settings,
        session_factory=session_factory,
        provider_call_logger=provider_logger,
        provider_factory=provider_factory,
    )
    
    # Create actor
    actor = Actor(user_id="eval-runner", email="eval@test.com", organisation_id=None, organisation_role=None)
    print("DEBUG: Actor created", flush=True, file=sys.stderr)
    
    # Create context
    ctx = SimpleContext(
        request_id="eval-req-001",
        trace_id="eval-trace-001",
        workflow_id="evaluation:consultancy_fundamentals_v1",
        pipeline_run_id="eval-run-001",
    )
    print("DEBUG: Context created", flush=True, file=sys.stderr)
    
    # Materialize rubrics first
    print("DEBUG: Materializing rubrics...", flush=True, file=sys.stderr)
    runner._materialize_rubrics(dataset=dataset, selected_cases=selected_cases)
    print("DEBUG: Rubrics materialized", flush=True, file=sys.stderr)
    
    # Evaluate each case
    model_slug = "gpt-oss-20b"
    marker = runner._build_marker(model_slug)
    case_results = []
    
    print(f"\n{'='*60}")
    print(f"Running evaluation: {suite.suite_id}")
    print(f"Model: {model_slug}")
    print(f"Cases: {len(selected_cases)}")
    print(f"{'='*60}")
    
    for case in selected_cases:
        print(f"\nEvaluating: {case.case_id} - {case.label}", flush=True)
        try:
            result = await runner._evaluate_case(
                ctx=ctx,
                actor=actor,
                dataset=dataset,
                case=case,
                requested_model_slug=model_slug,
                marker=marker,
            )
            case_results.append(result)
            print(f"  Status: {result.status}")
            if result.metrics:
                print(f"  Latency: {result.metrics.get('latency_ms', 0)}ms")
                print(f"  Tokens: {result.metrics.get('total_tokens', 0)}")
                print(f"  Score Error: {result.metrics.get('overall_score_abs_error', 'N/A')}")
            if result.error_code:
                print(f"  Error Code: {result.error_code}")
            if result.detail_payload:
                err_msg = result.detail_payload.get('error_message')
                if err_msg:
                    print(f"  Error Message: {err_msg}")
                # Print full detail_payload for debugging
                import json
                detail_str = json.dumps(result.detail_payload, indent=2, default=str)
                if len(detail_str) > 500:
                    print(f"  Detail Payload (truncated): {detail_str[:500]}...")
                else:
                    print(f"  Detail Payload: {detail_str}")
            # Also print raw scores if available
            if hasattr(result, 'actual_overall_score') and result.actual_overall_score is not None:
                print(f"  Actual Overall Score: {result.actual_overall_score}")
            if hasattr(result, 'expected_overall_score') and result.expected_overall_score:
                print(f"  Expected Overall Score: {result.expected_overall_score}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Build computation
    computation = build_marking_computation(
        suite=suite,
        dataset=dataset,
        selected_cases=selected_cases,
        model_slugs=[model_slug],
        case_results=case_results,
    )
    
    print(f"\n{'='*60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"PASSED: {computation.passed}")
    print(f"Suite: {computation.suite_id}")
    print(f"Suite Version: {computation.suite_version}")
    print(f"Benchmark Version: {computation.benchmark_set_version}")
    print()
    print("AGGREGATE METRICS:")
    for key, value in computation.aggregate_metrics.items():
        print(f"  {key}: {value}")
    print()
    print("CASE RESULTS:")
    for case in computation.case_results:
        print(f"  {case.case_id}: {case.status}")
        if case.error_code:
            print(f"    Error: {case.error_code}")
    
    return 0 if computation.passed else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
