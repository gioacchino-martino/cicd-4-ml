#!/usr/bin/env python3
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# This module is used to generate predictions from the model


from fastapi.logger import logger
from fastapi import FastAPI, Request

import pandas as pd
from xgboost import XGBClassifier

import logging

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
logger.setLevel(logging.DEBUG)

# Configuration
MODEL_PATH = 'model.json'


# Helpers
def load_model(model_path: str) -> XGBClassifier:
    """
    Load model from server
    Args:
        model_path: path of the model
    Returns:
        model: XGBClassifier model instance
    """
    logger.info(f'Loading model from {model_path}')
    classifier = XGBClassifier()
    classifier.load_model(model_path)
    return classifier


def generate_predictions(model: XGBClassifier, data: dict) -> list:
    """
    Generate predictions from model
    Args:
        model: XGBClassifier model instance
        data: data to make predictions on
    Returns:
        predictions: predictions from model
    """
    logger.info("Reading data to make predictions")
    inputs = pd.DataFrame.from_records(data)
    logger.info("Generating predictions")
    predictions = model.predict(inputs).tolist()
    return predictions


# Initiate server
app = FastAPI()

# Load model
clf = load_model(model_path=MODEL_PATH)


# Routes
@app.get('/health', status_code=200)
async def health():
    """Return health status"""
    return {"status": "healthy"}


@app.post('/predict')
async def predict(request: Request):
    body = await request.json()
    data = body["instances"]
    predictions = generate_predictions(model=clf, data=data)
    return {"predictions": predictions}
