import logging
from logging.handlers import QueueListener
from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
import os
import datetime
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.time_utils.dateParser import parse_dates
from utils.time_utils.timeOffsetToTimezone import convert_to_timezone

def _predict_videos_worker(filenames, threshold, timezone, LANG, log_queue, is_video):
    """
    Runs in a separate process and sends log messages to the parent via a queue.
    """
    import logging
    from logging.handlers import QueueHandler
    import sys

    # Configure logging to use the queue
    queue_handler = QueueHandler(log_queue)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # remove any default handlers
    root_logger.addHandler(queue_handler)

    # Import predictor inside subprocess
    if is_video:
        logging.info("Loading video predictor...")
        from models.predictTools import PredictorVideo
        predictor = PredictorVideo(filenames, threshold, LANG)
        logging.info("Starting video predictions...")
        while True:
            batch, _, _ = predictor.nextBatch()
            logging.info(f"Making prediction for video {batch} / {len(filenames)}")
            if batch == len(filenames):
                break
        logging.info("Video predictions completed")
    else:
        logging.info("Loading photo predictor...")
        from models.predictTools import PredictorImage
        predictor = PredictorImage(filenames, threshold, 10, LANG)
        logging.info("Starting photos predictions...")
        while True:
            batch, _, _, _, _ = predictor.nextBatch()
            logging.info(f"Making prediction for photo {batch} / {len(filenames)}")
            if batch == len(filenames):
                break
        logging.info("Photo predictions completed")

    predictions, scores, _, counts = predictor.getPredictions()
    dates_raw = predictor.getDates()

    # Parse any string-formatted dates (e.g., EXIF format "YYYY:MM:DD HH:MM:SS") into datetime objects
    parsed_dates: list[datetime.datetime | None] = parse_dates(dates_raw)

    # Assume dates are in UTC, convert them to timezone_to_use
    logging.info(f"Using timezone: {timezone}")
    logging.info(f"Exemple date before timezone adjustment: {parsed_dates[-1] if parsed_dates else 'No dates available'}")
    dates: list[datetime.datetime | None] = [
        convert_to_timezone(d, timezone) if isinstance(d, datetime.datetime) else None
        for d in parsed_dates
    ]
    logging.info(f"Exemple date after timezone adjustment: {dates[-1] if dates else 'No dates available'}")

    number_no_date = dates.count(None)
    if number_no_date > 0:
        logging.warning(f"Warning: {number_no_date} files have no creation date information.")

    if is_video:
        logging.info(f"Date conversions completed for videos.")
    else:
        logging.info(f"Date conversions completed for photos.")

    return {
        "predictions": predictions,
        "scores": scores,
        "dates": dates,
        "counts": counts
    }

def predict_videos(video_filenames, photo_filenames, threshold, timezone, LANG="en"):
    logging.info("Lauching predictors subprocess...")
    manager = Manager()
    log_queue = manager.Queue()

    # Parent logging setup
    logging.basicConfig(level=logging.INFO,
                        format="PARENT %(asctime)s - %(levelname)s - %(message)s")

    class InfoForwarder(logging.Handler):
        def emit(self, record):
            # Forward child message to the parent's logger
            logging.info(self.format(record))

    forwarder = InfoForwarder()
    forwarder.setFormatter(logging.Formatter("%(message)s"))

    listener = QueueListener(log_queue, forwarder)
    listener.start()

    try:
        with ProcessPoolExecutor(max_workers=1) as executor:
            result = {
                "predictions": [],
                "scores": [],
                "dates": [],
                "counts": []
            }
            if len(video_filenames) > 0:
                video_future = executor.submit(_predict_videos_worker,
                                        video_filenames, threshold, timezone, LANG, log_queue, is_video=True)
                video_result = video_future.result()
                result["predictions"].extend(video_result["predictions"])
                result["scores"].extend(video_result["scores"])
                result["dates"].extend(video_result["dates"])
                result["counts"].extend(video_result["counts"])
            if len(photo_filenames) > 0:
                image_future = executor.submit(_predict_videos_worker,
                                        photo_filenames, threshold, timezone, LANG, log_queue, is_video=False)
                image_result = image_future.result()
                result["predictions"].extend(image_result["predictions"])
                result["scores"].extend(image_result["scores"])
                result["dates"].extend(image_result["dates"])
                result["counts"].extend(image_result["counts"])
    finally:
        listener.stop()

    return result
