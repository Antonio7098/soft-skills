#!/usr/bin/env python3
"""Run multi-model golden dataset evaluation for consultancy_fundamentals."""

import asyncio
import sys
import traceback
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

# Add backend to path
backend_src = str(Path(__file__).resolve().parents[2] / "backend" / "src")
sys.path.insert(0, backend_src)

# Load .env file before importing Settings
env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

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
    
    def provider_factory(settings, provider_call_logger):
        return build_llm_provider(settings=settings, provider_call_logger=provider_call_logger)
        
except Exception as e:
    print(f"ERROR during import: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)


@dataclass
class ModelConfig:
    slug: str
    provider: str  # "groq" or "openrouter"
    display_name: str


# Model configurations
GROQ_MODELS = [
    ModelConfig("llama-3.1-8b-instant", "groq", "Llama 3.1 8B"),
    ModelConfig("llama-3.3-70b-versatile", "groq", "Llama 3.3 70B"),
    ModelConfig("openai/gpt-oss-120b", "groq", "GPT OSS 120B"),
]

OPENROUTER_MODELS = [
    ModelConfig("qwen/qwen3.6-plus-preview:free", "openrouter", "Qwen 3.6 Plus"),
    ModelConfig("mistralai/mistral-small-2603", "openrouter", "Mistral Small"),
    ModelConfig("nvidia/nemotron-3-super-120b-a12b:free", "openrouter", "Nemotron 120B"),
    ModelConfig("qwen/qwen3.5-9b", "openrouter", "Qwen 3.5 9B"),
]


class SimpleContext:
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
        self.snapshot = SimpleSnapshot(self._metadata)
    
    def get_metadata(self, key: str, default=None):
        return self._metadata.get(key, default)


class SimpleSnapshot:
    def __init__(self, metadata: dict):
        self.metadata = metadata


def build_settings_for_model(base_settings: Settings, model: ModelConfig) -> Settings:
    """Build Settings for a specific model and provider."""
    if model.provider == "groq":
        return Settings(
            provider_name="groq",
            provider_api_key=base_settings.groq_api_key,
            provider_base_url=base_settings.groq_base_url,
            database_url=base_settings.database_url,
            llm_marking_per_skill_model=model.slug,
            llm_marking_aggregation_model=model.slug,
        )
    else:  # openrouter
        return Settings(
            provider_name="openrouter",
            provider_api_key=base_settings.openrouter_api_key,
            provider_base_url=base_settings.openrouter_base_url,
            database_url=base_settings.database_url,
            llm_marking_per_skill_model=model.slug,
            llm_marking_aggregation_model=model.slug,
        )


async def evaluate_model(
    model: ModelConfig,
    base_settings: Settings,
    session_factory,
    suite,
    dataset,
    selected_cases,
) -> Dict:
    """Evaluate a single model against all cases."""
    print(f"\n{'='*70}")
    print(f"Evaluating: {model.display_name} ({model.slug})")
    print(f"Provider: {model.provider}")
    print(f"{'='*70}")
    
    settings = build_settings_for_model(base_settings, model)
    
    provider_repository = SqlAlchemyProviderCallRepository(session_factory)
    provider_logger = DatabaseProviderCallLogger(provider_repository)
    
    runner = MarkingBenchmarkRunner(
        settings=settings,
        session_factory=session_factory,
        provider_call_logger=provider_logger,
        provider_factory=provider_factory,
    )
    
    actor = Actor(user_id="eval-runner", email="eval@test.com", organisation_id=None, organisation_role=None)
    
    ctx = SimpleContext(
        request_id=f"eval-req-{model.slug.replace('/', '-')}",
        trace_id=f"eval-trace-{model.slug.replace('/', '-')}",
        workflow_id=f"evaluation:consultancy_fundamentals_v1",
        pipeline_run_id=f"eval-run-{model.slug.replace('/', '-')}",
    )
    
    # Materialize rubrics
    runner._materialize_rubrics(dataset=dataset, selected_cases=selected_cases)
    
    marker = runner._build_marker(model.slug)
    case_results = []
    
    for case in selected_cases:
        print(f"  {case.case_id}...", end=" ", flush=True)
        try:
            result = await runner._evaluate_case(
                ctx=ctx,
                actor=actor,
                dataset=dataset,
                case=case,
                requested_model_slug=model.slug,
                marker=marker,
            )
            case_results.append(result)
            
            # Save detail payload
            if result.detail_payload:
                detail_file = f"/tmp/eval_{model.slug.replace('/', '_')}_{case.case_id}.json"
                with open(detail_file, 'w') as f:
                    json.dump(result.detail_payload, f, indent=2, default=str)
            
            status_str = "✓" if result.status == "passed" else "✗"
            error_info = f" ({result.error_code})" if result.error_code else ""
            latency = result.metrics.get('latency_ms', 0) if result.metrics else 0
            tokens = result.metrics.get('total_tokens', 0) if result.metrics else 0
            print(f"{status_str} {latency}ms {tokens}tok{error_info}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
    
    # Build computation
    computation = build_marking_computation(
        suite=suite,
        dataset=dataset,
        selected_cases=selected_cases,
        model_slugs=[model.slug],
        case_results=case_results,
    )
    
    return {
        "model": model,
        "computation": computation,
        "case_results": case_results,
        "metrics": computation.aggregate_metrics,
    }


def print_results_table(results: List[Dict]):
    """Print formatted results table."""
    print(f"\n{'='*100}")
    print("EVALUATION RESULTS SUMMARY")
    print(f"{'='*100}")
    
    # Header
    print(f"{'Model':<35} {'Provider':<12} {'Pass Rate':<10} {'Avg Latency':<12} {'Tokens':<10} {'Cases':<8}")
    print("-" * 100)
    
    for result in results:
        model = result["model"]
        metrics = result["metrics"]
        
        pass_rate = metrics.get('pass_rate', 0)
        avg_latency = metrics.get('average_latency_ms', 0)
        total_tokens = metrics.get('total_tokens', 0)
        case_count = metrics.get('case_count', 0)
        passed_cases = metrics.get('passed_case_count', 0)
        
        print(f"{model.display_name:<35} {model.provider:<12} {pass_rate:>6.1%}    {avg_latency:>6.0f}ms    {total_tokens:>6}  {passed_cases}/{case_count}")
    
    print(f"{'='*100}\n")
    
    # Detailed results
    print("DETAILED CASE RESULTS")
    print(f"{'='*100}")
    
    # Get all unique case IDs
    all_cases = set()
    for result in results:
        for case_result in result["case_results"]:
            all_cases.add(case_result.case_id)
    
    # Header with model names
    header = f"{'Case ID':<45}"
    for result in results:
        header += f" {result['model'].display_name[:15]:<16}"
    print(header)
    print("-" * 100)
    
    # Results per case
    for case_id in sorted(all_cases):
        line = f"{case_id:<45}"
        for result in results:
            case_result = next((cr for cr in result["case_results"] if cr.case_id == case_id), None)
            if case_result:
                status = "✓" if case_result.status == "passed" else "✗"
                error = f" ({case_result.error_code})" if case_result.error_code else ""
                line += f" {status + error:<16}"
            else:
                line += f" {'N/A':<16}"
        print(line)
    
    print(f"{'='*100}\n")


async def main():
    base_settings = Settings()
    
    # Setup database
    engine = create_engine(base_settings.database_url)
    session_factory = sessionmaker(engine)
    
    # Get suite and dataset
    suite = suite_definition("consultancy_fundamentals_v1")
    dataset = load_suite_dataset(suite)
    selected_cases = select_cases(dataset=dataset, case_ids=[])
    
    print(f"Loaded dataset: {dataset.dataset_id} with {len(dataset.cases)} cases")
    print(f"Selected {len(selected_cases)} cases for evaluation")
    
    results = []
    
    # Run Groq models
    print("\n" + "="*70)
    print("RUNNING GROQ MODELS")
    print("="*70)
    for model in GROQ_MODELS:
        try:
            result = await evaluate_model(
                model=model,
                base_settings=base_settings,
                session_factory=session_factory,
                suite=suite,
                dataset=dataset,
                selected_cases=selected_cases,
            )
            results.append(result)
        except Exception as e:
            print(f"ERROR evaluating {model.slug}: {e}")
            traceback.print_exc()
    
    # Run OpenRouter models
    print("\n" + "="*70)
    print("RUNNING OPENROUTER MODELS")
    print("="*70)
    for model in OPENROUTER_MODELS:
        try:
            result = await evaluate_model(
                model=model,
                base_settings=base_settings,
                session_factory=session_factory,
                suite=suite,
                dataset=dataset,
                selected_cases=selected_cases,
            )
            results.append(result)
        except Exception as e:
            print(f"ERROR evaluating {model.slug}: {e}")
            traceback.print_exc()
    
    # Print summary
    print_results_table(results)
    
    # Save full results to file
    output_file = "/tmp/multi_model_eval_results.json"
    with open(output_file, 'w') as f:
        # Convert to serializable format
        serializable_results = []
        for r in results:
            serializable_results.append({
                "model": {
                    "slug": r["model"].slug,
                    "provider": r["model"].provider,
                    "display_name": r["model"].display_name,
                },
                "metrics": r["metrics"],
                "case_results": [
                    {
                        "case_id": cr.case_id,
                        "status": cr.status,
                        "error_code": cr.error_code,
                        "metrics": cr.metrics,
                    }
                    for cr in r["case_results"]
                ],
            })
        json.dump(serializable_results, f, indent=2, default=str)
    
    print(f"Full results saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"FATAL ERROR: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
