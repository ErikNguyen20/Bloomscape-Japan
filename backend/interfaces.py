from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


# Define data structure for a heatmap point
class HeatmapPoint(BaseModel):
    city: str
    city_jp: str
    lat: float
    lng: float
    value: float
    is_prediction: bool


class BloomHistoryPoint(BaseModel):
    year: int
    value: int


class BloomHistory(BaseModel):
    points: List[BloomHistoryPoint]
    prediction_year: int
    prediction_q10: float
    prediction_q50: float
    prediction_q90: float


class DataService(ABC):
    """Abstract interface for any data source providing heatmap points."""

    @abstractmethod
    def is_first_time_initialized(self) -> bool:
        """
        Flag for if it is first time initialized yet.
        """

    @abstractmethod
    def get_heatmap_points(self, year: int) -> List[HeatmapPoint]:
        """
        Retrieve heatmap points for a given year.

        Args:
            year (int): The year to query.

        Returns:
            List[HeatmapPoint]: List of geographic points with values.
        """

    @abstractmethod
    def get_city_history(self, city: str) -> BloomHistory:
        """
        Retrieve history of the city.

        Args:
            city (str): The historic city data.

        Returns:
            BloomHistory: History of the city.
        """

    @abstractmethod
    def set_history(self, data_directory: str):
        """
        Sets the history & metadata of cities
        :param data_directory:
        """

    @abstractmethod
    def set_predictions(self, data_directory: str, predictions):
        """
        Set the predictions from the model
        :param data_directory:
        :param predictions:
        """