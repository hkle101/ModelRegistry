from typing import Dict, Any
# Metrics are now top-level packages under `metrics`
from metrics.codequality import CodeQualityMetric
from metrics.datasetquality import DatasetQualityMetric
from metrics.datasetandcodescore import DatasetAndCodeScoreMetric
from metrics.busfactor import BusFactorMetric
from metrics.license import LicenseMetric
from metrics.rampuptime import RampUpTimeMetric
from metrics.sizescore import SizeScoreMetric
from metrics.performanceclaims import PerformanceClaimsMetric
from cli.utils.MetricDataFetcher import MetricDataFetcher  # import your fetcher


class MetricScorer:
    """
    Runs all metric scorers and returns a dictionary
    of all metric scores and latencies.
    SizeScoreMetric returns multiple device scores, which are included directly.
    """

    def __init__(self):
        self.metrics = {
            "code_quality": CodeQualityMetric(),
            "dataset_quality": DatasetQualityMetric(),
            "dataset_and_code": DatasetAndCodeScoreMetric(),
            "bus_factor": BusFactorMetric(),
            "license": LicenseMetric(),
            "size_score": SizeScoreMetric(),
            "ramp_up_time": RampUpTimeMetric(),
            "performance_claims": PerformanceClaimsMetric(),
        }
        self.results: Dict[str, Any] = {}

    def score_all_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clears previous results and updates the dictionary directly with scores
        and latencies from each metric's getScores().
        SizeScoreMetric returns multiple scores, so we include them directly.
        """
        self.results.clear()

        for name, metric in self.metrics.items():
            try:
                metric_result = metric.getScores(data)

                # If SizeScoreMetric, include all keys as-is
                if name == "size_score":
                    self.results.update(metric_result)
                else:
                    self.results[name] = metric_result.get("score", 0.0)
                    self.results[f"{name}_latency"] = metric_result.get("latency", 0.0)

            except Exception as e:
                if name == "size_score":
                    # populate all device scores as 0 on failure
                    self.results.update({
                        "raspberry_pi": 0.0,
                        "jetson_nano": 0.0,
                        "desktop_pc": 0.0,
                        "aws_server": 0.0,
                        "size_score_latency": 0.0
                    })
                    print(f"[WARN] SizeScore metric failed but still populated: {e}")
                else:
                    print(f"[WARN] Metric '{name}' failed: {e}")
                    self.results[name] = 0.0
                    self.results[f"{name}_latency"] = 0.0

        return self.results

    @staticmethod
    def main(model_url: str):
        """
        Fetches model data using MetricDataFetcher and prints all metric scores.
        """
        fetcher = MetricDataFetcher()
        model_data = fetcher.fetch_Modeldata(model_url)  # returns a dictionary

        scorer = MetricScorer()
        scores = scorer.score_all_metrics(model_data)

        print(f"Metric scores for model: {model_url}")
        for key, value in scores.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    # Example usage: replace with your Hugging Face model URL
    MetricScorer.main("https://huggingface.co/bert-base-uncased")
