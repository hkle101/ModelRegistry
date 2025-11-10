from typing import Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from metrics.codequality import CodeQualityMetric
from metrics.datasetquality import DatasetQualityMetric
from metrics.datasetandcodescore import DatasetAndCodeScoreMetric
from metrics.busfactor import BusFactorMetric
from metrics.license import LicenseMetric
from metrics.rampuptime import RampUpTimeMetric
from metrics.sizescore import SizeScoreMetric
from metrics.performanceclaims import PerformanceClaimsMetric
from cli.utils.MetadataFetcher import MetadataFetcher
from cli.utils.MetricDataFetcher import MetricDataFetcher
import time

logger = logging.getLogger(__name__)


class MetricScorer:
    """
    Runs all 8 metrics for any artifact type.
    Returns scores, latencies, and a weighted net score.
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

        # Weights for net score calculation (example, sum doesn't have to be 1)
        self.weights = {
            "code_quality": 0.15,
            "dataset_quality": 0.15,
            "dataset_and_code": 0.1,
            "bus_factor": 0.1,
            "license": 0.1,
            "size_score": 0.1,
            "ramp_up_time": 0.15,
            "performance_claims": 0.15,
        }

    def score_artifact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        def run_metric(name: str, metric):
            try:
                res = metric.getScores(data)
            except Exception as e:
                logger.debug("Metric %s failed: %s", name, e)
                if name == "size_score":
                    res = {
                        "raspberry_pi": 0.0,
                        "jetson_nano": 0.0,
                        "desktop_pc": 0.0,
                        "aws_server": 0.0,
                        "size_score_latency": 0.0,
                    }
                else:
                    res = {"score": 0.0, "latency": 0.0}
            return name, res

        # Measure the start time of parallel execution
        start_time = time.time()

        # Run all metrics in parallel
        with ThreadPoolExecutor(max_workers=len(self.metrics)) as executor:
            futures = {
                executor.submit(run_metric, name, metric): name
                for name, metric in self.metrics.items()
            }

            for future in as_completed(futures):
                name, metric_result = future.result()
                if name == "size_score":
                    results.update(metric_result)
                else:
                    results[name] = metric_result.get("score", 0.0)
                    results[f"{name}_latency"] = metric_result.get(
                        "latency", 0.0
                    )

        # Measure the end time for the parallel execution
        net_latency = round((time.time() - start_time) * 1000.0, 2)

        # Compute net score as weighted sum
        net_score = 0.0
        for metric_name, weight in self.weights.items():
            if metric_name == "size_score":
                device_scores = [
                    results.get(dev, 0.0)
                    for dev in [
                        "raspberry_pi",
                        "jetson_nano",
                        "desktop_pc",
                        "aws_server",
                    ]
                ]
                net_score += (sum(device_scores) / len(device_scores)) * weight
            else:
                net_score += results.get(metric_name, 0.0) * weight

        results["net_score"] = round(net_score, 2)
        results["net_latency"] = round(net_latency, 2)
        return results

    @staticmethod
    def main():
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Step 1: Input URL for artifact
        prompt = (
            "Enter HuggingFace model, dataset, or GitHub "
            "repo URL: "
        )
        artifact_url = input(prompt)

        # Step 2: Fetch metadata
        metadata_fetcher = MetadataFetcher(github_token=None)
        try:
            meta_info = metadata_fetcher.fetch(artifact_url)
            logger.info(f"Fetched metadata for {artifact_url}")
        except Exception as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return

        # Step 3: Fetch structured artifact data
        data_fetcher = MetricDataFetcher()
        try:
            artifact_data = data_fetcher.fetch_artifact_data(meta_info)
            logger.info("Fetched structured artifact data")
        except Exception as e:
            logger.error(f"Failed to fetch artifact data: {e}")
            return

        # Step 4: Score the artifact
        scorer = MetricScorer()
        start_time = time.time()
        scores = scorer.score_artifact(artifact_data)
        total_time = time.time() - start_time

        # Step 5: Print results
        logger.info(f"Scoring completed in {total_time:.2f}s")
        print("Scores & Net Score:")
        for key, value in scores.items():
            print(f"{key}: {value}")


# Allow running as script
if __name__ == "__main__":
    MetricScorer.main()
