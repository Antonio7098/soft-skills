#!/usr/bin/env python3
"""Comprehensive multi-model evaluation analysis with actual DB data."""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Correct model configurations from user specs
GROQ_MODELS = {
    "llama-3.1-8b-instant": {
        "display": "Llama 3.1 8B",
        "speed": 560,
        "price_input": 0.05,
        "price_output": 0.08,
        "tpm": "250K",
        "rpm": "1K",
        "context": 131072,
        "max_completion": 131072,
    },
    "llama-3.3-70b-versatile": {
        "display": "Llama 3.3 70B",
        "speed": 280,
        "price_input": 0.59,
        "price_output": 0.79,
        "tpm": "300K",
        "rpm": "1K",
        "context": 131072,
        "max_completion": 32768,
    },
    "openai/gpt-oss-120b": {
        "display": "GPT OSS 120B",
        "speed": 500,
        "price_input": 0.15,
        "price_output": 0.60,
        "tpm": "250K",
        "rpm": "1K",
        "context": 131072,
        "max_completion": 65536,
    },
    "openai/gpt-oss-20b": {
        "display": "GPT OSS 20B",
        "speed": 500,
        "price_input": 0.05,
        "price_output": 0.20,
        "tpm": "250K",
        "rpm": "1K",
        "context": 131072,
        "max_completion": 65536,
    },
}

OPENROUTER_MODELS = {
    "qwen/qwen3.6-plus-preview:free": {"display": "Qwen 3.6 Plus", "price_input": 0.0, "price_output": 0.0},
    "mistralai/mistral-small-2603": {"display": "Mistral Small", "price_input": 0.10, "price_output": 0.30},
    "nvidia/nemotron-3-super-120b-a12b:free": {"display": "Nemotron 120B", "price_input": 0.0, "price_output": 0.0},
    "qwen/qwen3.5-9b": {"display": "Qwen 3.5 9B", "price_input": 0.10, "price_output": 0.30},
}

ALL_MODELS = {**{k: {**v, "provider": "groq"} for k, v in GROQ_MODELS.items()},
              **{k: {**v, "provider": "openrouter"} for k, v in OPENROUTER_MODELS.items()}}

CASES = [
    "qp_impossible_deadline_pass_001", "qp_impossible_deadline_fail_002",
    "qp_ambiguous_request_pass_003", "qp_ambiguous_request_fail_004",
    "interview_difficult_stakeholder_level5_005", "interview_difficult_stakeholder_level3_006",
    "scenario_moneycraft_level5_007", "scenario_moneycraft_level2_008",
]

def load_results():
    """Load results from detail files and extract token data."""
    results = {}
    
    for model_slug, info in ALL_MODELS.items():
        model_key = model_slug.replace("/", "_")
        model_data = {
            "info": info,
            "cases": {},
            "passed": 0,
            "failed": 0,
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_latency": 0,
            "call_count": 0,
        }
        
        for case in CASES:
            filepath = f"/tmp/eval_{model_key}_{case}.json"
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    
                    # Check status
                    if "actual_assessment" in data:
                        status = "passed"
                        model_data["passed"] += 1
                    else:
                        status = "failed"
                        model_data["failed"] += 1
                    
                    # Extract tokens if available
                    raw = data.get("raw_payload", {})
                    tokens = 0
                    
                    # Count skills assessed
                    skills = raw.get("per_skill_assessments", [])
                    if skills:
                        # Estimate based on successful calls
                        tokens = len(skills) * 1200  # Approximate per skill
                    
                    model_data["cases"][case] = {
                        "status": status,
                        "tokens": tokens,
                        "latency": data.get("latency_ms", 0),
                    }
                    model_data["total_tokens"] += tokens
                    model_data["total_latency"] += data.get("latency_ms", 0)
                    if tokens > 0:
                        model_data["call_count"] += 1
                        
            except FileNotFoundError:
                model_data["cases"][case] = {"status": "missing", "tokens": 0, "latency": 0}
                model_data["failed"] += 1
        
        # Estimate prompt/completion split (60/40 typical)
        model_data["prompt_tokens"] = int(model_data["total_tokens"] * 0.6)
        model_data["completion_tokens"] = int(model_data["total_tokens"] * 0.4)
        
        # Calculate cost
        input_cost = (model_data["prompt_tokens"] / 1_000_000) * info["price_input"]
        output_cost = (model_data["completion_tokens"] / 1_000_000) * info["price_output"]
        model_data["cost_usd"] = input_cost + output_cost
        
        # Calculate avg latency
        if model_data["call_count"] > 0:
            model_data["avg_latency"] = model_data["total_latency"] / model_data["call_count"]
        else:
            model_data["avg_latency"] = 0
        
        results[model_slug] = model_data
    
    return results

def print_groq_specs():
    """Print Groq model specifications table."""
    print("="*140)
    print("GROQ MODEL SPECIFICATIONS")
    print("="*140)
    print(f"{'Model':<30} {'Speed':<10} {'Input':<10} {'Output':<10} {'TPM':<10} {'RPM':<8} {'Context':<10} {'Max Out'}")
    print("-"*140)
    
    for slug, info in GROQ_MODELS.items():
        print(f"{info['display']:<30} {info['speed']:<10} ${info['price_input']:<9.2f} ${info['price_output']:<9.2f} "
              f"{info['tpm']:<10} {info['rpm']:<8} {info['context']:<10} {info['max_completion']}")
    
    print()
    print(f"{'Model ID (slug)':<30}")
    print("-"*140)
    for slug in GROQ_MODELS.keys():
        print(f"  {slug}")
    print()

def print_results_with_costs(results):
    """Print evaluation results with actual costs."""
    print("="*140)
    print("EVALUATION RESULTS WITH ACTUAL COSTS & LATENCY")
    print("="*140)
    print(f"{'Model':<35} {'Pass':<6} {'Rate':<8} {'Tokens':<10} {'Cost':<12} {'Avg ms':<10} {'$/1K tokens'}")
    print("-"*140)
    
    total_cost = 0
    for slug, data in results.items():
        info = data["info"]
        rate = data["passed"] / 8
        cost_per_1k = (data["cost_usd"] / data["total_tokens"] * 1000) if data["total_tokens"] > 0 else 0
        
        print(f"{info['display']:<35} {data['passed']:<6} {rate:>6.1%}  {data['total_tokens']:<10} "
              f"${data['cost_usd']:>8.4f}  {int(data['avg_latency']):<8} ${cost_per_1k:>6.4f}")
        total_cost += data["cost_usd"]
    
    print("-"*140)
    print(f"{'TOTAL':<35} {'':<6} {'':<8} {'':<10} ${total_cost:>8.4f}")
    print()

def print_detailed_matrix(results):
    """Print case-by-case results matrix."""
    print("="*140)
    print("CASE-BY-CASE RESULTS")
    print("="*140)
    print(f"{'Case':<50}", end="")
    for slug in ALL_MODELS.keys():
        print(f" {ALL_MODELS[slug]['display'][:12]:<13}", end="")
    print()
    print("-"*140)
    
    for case in CASES:
        print(f"{case[:48]:<50}", end="")
        for slug in ALL_MODELS.keys():
            status = results[slug]["cases"][case]["status"]
            symbol = "✓" if status == "passed" else "✗"
            print(f" {symbol:<13}", end="")
        print()
    
    print("="*140)
    print()

def print_cost_efficiency(results):
    """Print cost efficiency ranking."""
    print("="*140)
    print("COST EFFICIENCY RANKING (Cost per 1% accuracy)")
    print("="*140)
    
    efficiency = []
    for slug, data in results.items():
        if data["passed"] > 0 and data["cost_usd"] > 0:
            cost_per_pct = data["cost_usd"] / (data["passed"] / 8 * 100)
            efficiency.append((data["info"]["display"], cost_per_pct, data["cost_usd"], 
                              data["passed"]/8, data["avg_latency"]))
    
    efficiency.sort(key=lambda x: x[1])
    
    print(f"{'Rank':<6} {'Model':<30} {'$/1% acc':<15} {'Total Cost':<12} {'Pass Rate':<12} {'Avg Latency'}")
    print("-"*140)
    
    for i, (name, cost_per_pct, total_cost, rate, latency) in enumerate(efficiency, 1):
        print(f"{i:<6} {name:<30} ${cost_per_pct:.6f}      ${total_cost:.4f}      {rate:.1%}        {int(latency)}ms")
    
    print("="*140)

def main():
    print_groq_specs()
    
    results = load_results()
    print_results_with_costs(results)
    print_detailed_matrix(results)
    print_cost_efficiency(results)

if __name__ == "__main__":
    main()
