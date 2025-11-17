# api/app/routers/constants.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1/constants", tags=["constants"])


@router.get("/thresholds")
def get_thresholds():
    """
    Return threshold constants for alerting.
    These are defaults; later can be overridden per field/crop.
    """
    return {
        "moisture30_act": 25,  # Below 25% = action needed
        "moisture30_watch": 30,  # Below 30% = watch
        "moisture30_watch_delta_6h": 2,  # Drop >2% in 6h = watch
        "temp_high": 35,  # Above 35°C = high
        "temp_low": 15,  # Below 15°C = low
    }

