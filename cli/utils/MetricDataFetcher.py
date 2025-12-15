"""Metric data aggregation.

Builds the structured input required by the metric scorers by delegating to
individual data fetchers.
"""

from typing import Any, Dict
import logging
try:
    from ModelRegistry.cli.utils.MetadataFetcher import MetadataFetcher
except ModuleNotFoundError:
    from cli.utils.MetadataFetcher import MetadataFetcher

try:
    from ModelRegistry.datafetchers.licensedata_fetcher import LicenseDataFetcher
    from ModelRegistry.datafetchers.busfactordata_fetcher import BusFactorDataFetcher
    from ModelRegistry.datafetchers.datasetdata_fetcher import DatasetDataFetcher
    from ModelRegistry.datafetchers.codequalitydata_fetcher import CodeQualityDataFetcher
    from ModelRegistry.datafetchers.sizedata_fetcher import SizeDataFetcher
    from ModelRegistry.datafetchers.performanceClaimsdata_fetcher import PerformanceClaimsDataFetcher
    from ModelRegistry.datafetchers.rampuptimedata_fetcher import RampUpTimeDataFetcher
    from ModelRegistry.datafetchers.datasetnCodedata_fetcher import DatasetAndCodeDataFetcher
except ModuleNotFoundError:
    from datafetchers.licensedata_fetcher import LicenseDataFetcher
    from datafetchers.busfactordata_fetcher import BusFactorDataFetcher
    from datafetchers.datasetdata_fetcher import DatasetDataFetcher
    from datafetchers.codequalitydata_fetcher import CodeQualityDataFetcher
    from datafetchers.sizedata_fetcher import SizeDataFetcher
    from datafetchers.performanceClaimsdata_fetcher import PerformanceClaimsDataFetcher
    from datafetchers.rampuptimedata_fetcher import RampUpTimeDataFetcher
    from datafetchers.datasetnCodedata_fetcher import DatasetAndCodeDataFetcher

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MetricDataFetcher:
    """
    Fetches structured data from HuggingFace models, datasets, and GitHub code.
    Always gathers all 8 metrics, any missing values will default to 0.
    """

    def __init__(self):
        self.metadata_fetcher = MetadataFetcher()
        self.fetchers = [
            LicenseDataFetcher(),
            BusFactorDataFetcher(),
            DatasetDataFetcher(),
            CodeQualityDataFetcher(),
            SizeDataFetcher(),
            PerformanceClaimsDataFetcher(),
            RampUpTimeDataFetcher(),
            DatasetAndCodeDataFetcher()
        ]

    def fetch_artifact_data(self, meta_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch structured data for all metrics from pre-fetched meta."""
        artifact_type = meta_info.get("artifact_type", "unknown")
        raw = meta_info
        artifact_data: Dict[str, Any] = {}
        for fetcher in self.fetchers:
            try:
                if artifact_type == "model":
                    artifact_data.update(fetcher.fetch_Modeldata(raw))
                elif artifact_type == "dataset":
                    artifact_data.update(fetcher.fetch_Datasetdata(raw))
                elif artifact_type == "code":
                    artifact_data.update(fetcher.fetch_Codedata(raw))
                else:
                    # Unknown type: try all, best-effort
                    artifact_data.update(fetcher.fetch_Modeldata(raw))
                    artifact_data.update(fetcher.fetch_Datasetdata(raw))
                    artifact_data.update(fetcher.fetch_Codedata(raw))
            except Exception as e:
                logger.debug(
                    "Fetcher %s failed: %s",
                    fetcher.__class__.__name__,
                    e,
                )
                continue
        artifact_data["download_url"] = meta_info.get("download_url")
        return artifact_data

    def run(self):
        """Interactive main method to test metadata and metrics fetching."""
        url = input("Enter a model/dataset/repo URL: ").strip()
        if not url:
            print("No URL provided. Exiting.")
            return

        try:
            # Fetch metadata
            meta_info = self.metadata_fetcher.fetch(url)
            artifact_type = meta_info.get("artifact_type", "unknown")
            logger.info("Fetched metadata for artifact_type: %s", artifact_type)

            # Fetch metrics
            metricsdata = self.fetch_artifact_data(meta_info)

            # Display results
            print("\n=== Metadata ===")
            for k, v in meta_info.items():
                print(f"{k}: {v}")

            print("\n=== Extracted Metrics ===")
            print(metricsdata)

        except Exception as e:
            logger.exception("Error processing URL: %s", url)
            print(f"Failed to fetch metadata/metrics: {e}")


if __name__ == "__main__":
    fetcher = MetricDataFetcher()
    fetcher.run()

