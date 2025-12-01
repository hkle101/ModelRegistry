import json
from typing import Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, ROUND_HALF_UP

try:
    from ModelRegistry.metrics.codequality import CodeQualityMetric
    from ModelRegistry.metrics.datasetquality import DatasetQualityMetric
    from ModelRegistry.metrics.datasetandcodescore import DatasetAndCodeScoreMetric
    from ModelRegistry.metrics.busfactor import BusFactorMetric
    from ModelRegistry.metrics.license import LicenseMetric
    from ModelRegistry.metrics.rampuptime import RampUpTimeMetric
    from ModelRegistry.metrics.sizescore import SizeScoreMetric
    from ModelRegistry.metrics.performanceclaims import PerformanceClaimsMetric
    from ModelRegistry.cli.utils.MetadataFetcher import MetadataFetcher
    from ModelRegistry.cli.utils.MetricDataFetcher import MetricDataFetcher
except ModuleNotFoundError:
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
import json
import time

logger = logging.getLogger(__name__)


class MetricScorer:
    """
    Runs all 8 metrics for any artifact type.
    Returns scores, latencies, and a weighted net score as **strings**.
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

        self.weights = {
            "code_quality": Decimal("0.15"),
            "dataset_quality": Decimal("0.15"),
            "dataset_and_code": Decimal("0.10"),
            "bus_factor": Decimal("0.10"),
            "license": Decimal("0.10"),
            "size_score": Decimal("0.10"),
            "ramp_up_time": Decimal("0.15"),
            "performance_claims": Decimal("0.15"),
        }

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        """Helper: convert numeric values to Decimal rounded to 2 decimals"""
        try:
            return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (ValueError, TypeError):
            return Decimal("0.00")

    def score_artifact(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Run metrics and return ALL scores + latencies + net score
        as **strings** instead of Decimals.
        """
        results: Dict[str, Decimal] = {}

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
                        "latency": 0.0,
                    }
                else:
                    res = {"score": 0.0, "latency": 0.0}
            return name, res

        start_time = time.time()

        # Run metrics concurrently
        with ThreadPoolExecutor(max_workers=len(self.metrics)) as executor:
            futures = {
                executor.submit(run_metric, name, metric): name
                for name, metric in self.metrics.items()
            }

            for future in as_completed(futures):
                name, metric_result = future.result()

                if name == "size_score":
                    for dev in [
                        "raspberry_pi",
                        "jetson_nano",
                        "desktop_pc",
                        "aws_server",
                        "latency",
                    ]:
                        results[dev] = self._to_decimal(metric_result.get(dev, 0.0))
                else:
                    results[name] = self._to_decimal(metric_result.get("score", 0.0))
                    results[f"{name}_latency"] = self._to_decimal(
                        metric_result.get("latency", 0.0)
                    )

        # Compute net latency
        net_latency = Decimal(str((time.time() - start_time) * 1000)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Compute weighted net score
        net_score = Decimal("0.00")
        for metric_name, weight in self.weights.items():
            if metric_name == "size_score":
                device_scores = [
                    results.get(dev, Decimal("0.00"))
                    for dev in [
                        "raspberry_pi",
                        "jetson_nano",
                        "desktop_pc",
                        "aws_server",
                    ]
                ]
                avg_device_score = sum(device_scores) / Decimal(len(device_scores))
                net_score += avg_device_score * weight
            else:
                net_score += results.get(metric_name, Decimal("0.00")) * weight

        results["net_score"] = net_score.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        results["net_latency"] = net_latency

        # --------------------------------------------------
        # 🔥 Convert ALL Decimal results → string
        # --------------------------------------------------
        results = {k: str(v) for k, v in results.items()}
        # --------------------------------------------------
        return results

    def ndjson_style_scores(self, scores: Dict[str, str]) -> json:
        """Print scores in a readable format."""
        return json.dumps(scores, indent=4)

    @staticmethod
    def main():
        # (unchanged exactly as requested)
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        artifact_url = input("Enter HuggingFace model, dataset, or GitHub repo URL: ")

        metadata_fetcher = MetadataFetcher(github_token=None)
        try:
            meta_info = metadata_fetcher.fetch(artifact_url)
            logger.info(f"Fetched metadata for {artifact_url}")
        except Exception as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return

        data_fetcher = MetricDataFetcher()
        try:
            artifact_data = data_fetcher.fetch_artifact_data(meta_info)
            logger.info("Fetched structured artifact data")
        except Exception as e:
            logger.error(f"Failed to fetch artifact data: {e}")
            return

        scorer = MetricScorer()
        start_time = time.time()
        scores = scorer.score_artifact(artifact_data)
        total_time = time.time() - start_time

        logger.info(f"Scoring completed in {total_time:.2f}s")
        print("\nScores & Net Score:")
        for key, value in scores.items():
            print(f"{key}: {value}")

        float_keys = [k for k, v in scores.items() if isinstance(v, float)]
        if float_keys:
            print("\nWARNING: These keys are still floats (should be string):")
            for k in float_keys:
                print(f"- {k}")
        else:
            print("\nAll scores are strings. Ready for DynamoDB upload.")


if __name__ == "__main__":
    MetricScorer.main()
