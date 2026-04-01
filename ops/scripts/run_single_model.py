#!/usr/bin/env python3
"""Run single model evaluation - designed to be called multiple times."""

import asyncio
import sys
import json
import traceback
from pathlib import Path

backend_src = str(Path(__file__).resolve().parents[2] / "backend" / "src")
sys.path.insert(0, backend_src)

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
    from soft_skills_backend.modules.evaluation.use_cases.marking_benchmark import MarkingBenchmarkRunner
    from soft_skills_backend.platform.observability.stageflow_logging import DatabaseProviderCallLogger
    from soft_skills_backend.shared.auth import Actor
    from soft_skills_backend.platform.db.repositories import SqlAlchemyProviderCallRepository
    from soft_skills_backend.platform.providers.llm.openai_compatible import build_llm_provider
    
    def provider_factory(settings, provider_call_logger):
        return build_llm_provider(settings=settings, provider_call_logger=provider_call_logger)
        
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)


class SimpleContext:
    def __init__(self, request_id, trace_id, workflow_id, pipeline_run_id):
        self.request_id = request_id
        self.trace_id = trace_id
        self.workflow_id = workflow_id
        self.pipeline_run_id = pipeline_run_id
        self._metadata = {"request_id": request_id, "trace_id": trace_id, 
                         "workflow_id": workflow_id, "pipeline_run_id": pipeline_run_id}
        self.snapshot = type('obj', (object,), {'metadata': self._metadata})()
    
    def get_metadata(self, key, default=None):
        return self._metadata.get(key, default)


def build_settings(base, model_slug, provider):
    if provider == "groq":
        return Settings(
            provider_name="groq",
            provider_api_key=base.groq_api_key,
            provider_base_url=base.groq_base_url,
            database_url=base.database_url,
            llm_marking_per_skill_model=model_slug,
            llm_marking_aggregation_model=model_slug,
        )
    else:
        return Settings(
            provider_name="openrouter",
            provider_api_key=base.openrouter_api_key,
            provider_base_url=base.openrouter_base_url,
            database_url=base.database_url,
            llm_marking_per_skill_model=model_slug,
            llm_marking_aggregation_model=model_slug,
        )


async def main():
    if len(sys.argv) < 3:
        print("Usage: python3 run_single_model.py <provider> <model_slug>", file=sys.stderr)
        print("Example: python3 run_single_model.py groq llama-3.1-8b-instant", file=sys.stderr)
        sys.exit(1)
    
    provider = sys.argv[1]
    model_slug = sys.argv[2]
    
    base_settings = Settings()
    engine = create_engine(base_settings.database_url)
    session_factory = sessionmaker(engine)
    
    suite = suite_definition("consultancy_fundamentals_v1")
    dataset = load_suite_dataset(suite)
    selected_cases = select_cases(dataset=dataset, case_ids=[])
    
    settings = build_settings(base_settings, model_slug, provider)
    
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
        request_id=f"eval-{model_slug.replace('/', '-')}",
        trace_id=f"trace-{model_slug.replace('/', '-')}",
        workflow_id="evaluation:consultancy_fundamentals_v1",
        pipeline_run_id=f"run-{model_slug.replace('/', '-')}",
    )
    
    runner._materialize_rubrics(dataset=dataset, selected_cases=selected_cases)
    marker = runner._build_marker(model_slug)
    
    results = []
    for case in selected_cases:
        try:
            result = await runner._evaluate_case(
                ctx=ctx, actor=actor, dataset=dataset, case=case,
                requested_model_slug=model_slug, marker=marker,
            )
            results.append({
                "case_id": result.case_id,
                "status": result.status,
                "error_code": result.error_code,
                "metrics": result.metrics,
            })
        except Exception as e:
            results.append({
                "case_id": case.case_id,
                "status": "failed",
                "error_code": "EXCEPTION",
                "error": str(e),
            })
    
    # Save results
    output_file = f"/tmp/eval_result_{provider}_{model_slug.replace('/', '_')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "model_slug": model_slug,
            "provider": provider,
            "results": results,
        }, f, indent=2, default=str)
    
    # Print summary
    passed = sum(1 for r in results if r["status"] == "passed")
    total = len(results)
    print(f"{model_slug}: {passed}/{total} passed")
    for r in results:
        status = "✓" if r["status"] == "passed" else "✗"
        err = f" ({r['error_code']})" if r.get('error_code') else ""
        print(f"  {r['case_id']}: {status}{err}")


if __name__ == "__main__":
    asyncio.run(main())
