from src.evaluation.mlflow_eval import run

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
