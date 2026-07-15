import anyio
from pathlib import Path
from datetime import datetime
from loguru import logger
import polars as pl

import httpx
from pydantic import BaseModel

# obstore helps us easily store metadata in the filesystem
DATA_DIR = Path("data/fingertips")
API = httpx.AsyncClient(base_url="https://fingertips.phe.org.uk", http2=True)

# Specifying the schema on read ensures users have a consistent schema
# generally, the numeric values must be floats, there are some discrepencies so using a generic type is safer for error handling
FTP_SCHEMA = {
    "Value": pl.Float64,
    "Lower CI 95.0 limit": pl.Float64,
    "Upper CI 95.0 limit": pl.Float64,
    "Lower CI 99.8 limit": pl.Float64,
    "Upper CI 99.8 limit": pl.Float64,
    "Count": pl.Float64,
    "Denominator": pl.Float64,
}


class DateUpdated(BaseModel):
    """Utility to get the latest data change date from fingertips.

    Generally this is used to ensure filesystem standards and caching occur correctly and prevent too many connections to the api.

    The caching of fingertips data loads the raw csv's

    usage:
    >>> most_recent = DateUpdated.from_fingertips(108)
    >>> date = most_recent.LastUploadedAt
    >>> most_recent.from_cache(108)
    Path(".../raw/indicator_id=108/{date:%Y%m%d_%H%M%S}.csv"
    """

    LastUploadedAt: datetime

    @classmethod
    async def afrom_fingertips(cls, indicator_id: int) -> "DateUpdated":
        logger.info(f"checking updates for indicator {indicator_id}")
        date_updated = await API.get(
            "/api/data_changes", params={"indicator_id": indicator_id}
        )
        return cls.model_validate_json(date_updated.content)

    @classmethod
    def from_fingertips(cls, indicator_id: int) -> "DateUpdated":
        return anyio.run(cls.afrom_fingertips, indicator_id)

    def from_cache(self, indicator_id: int) -> Path:
        path = DATA_DIR / f"raw/indicator_id={indicator_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path / f"{self.LastUploadedAt:%Y%m%d_%H%M%S}.csv"


async def awrite_to_cache(indicator_id: int, path: Path) -> Path:
    """runs asynchronously for imporved performance"""
    response = await API.get(
        "api/all_data/csv/for_one_indicator", params={"indicator_id": indicator_id}
    )
    response.raise_for_status()
    async with await anyio.Path(path).open(mode="wb") as open_file:
        async for byte_steam in response.aiter_bytes():
            await open_file.write(byte_steam)
    return path


async def aget_data_for_single_indicator(indicator_id: int) -> pl.DataFrame:
    """runs asynchronously for imporved performance"""
    latest = await DateUpdated.afrom_fingertips(indicator_id)
    local_path = latest.from_cache(indicator_id)
    if not local_path.exists():
        local_path = await awrite_to_cache(indicator_id, local_path)

    return pl.read_csv(local_path, infer_schema=False, schema_overrides=FTP_SCHEMA)


async def aget_data_for_indicators(*indicator_id: int) -> pl.DataFrame:
    """generally this is used as the async entrypoint.

    Params:
    indicator_id: one or more indicator id's to fetch

    Returns:
    a single dataframe combining all the indicator_id's"""
    data = []
    for i in indicator_id:
        try:
            result = await aget_data_for_single_indicator(i)
            data.append(result)
        except Exception as e:
            logger.error(
                f"indicator_id {i} encountered an error and is not included in the result",
                e,
            )
    return pl.concat(data)


def get_data_for_indicators(*indicator_id: int) -> pl.DataFrame:
    """get the latest data from the local cache, or download the raw data if it is not found or not up to date.

    it is usually faster to load multiple indicator id's at once to make use of the async performance enhancements.

    if errors are encountered, the best effort to return as much data as possible handling errors.

    subsequent runs may resolve errors due to api limiting because data will be locally cached on successful runs.

    Params:
    indicator_id: one or more indicator id's to fetch

    Returns:
    a single dataframe combining all the indicator_id's"""
    return anyio.run(aget_data_for_indicators, *indicator_id)


if __name__ == "__main__":
    result = get_data_for_indicators(108)
    print(result)
