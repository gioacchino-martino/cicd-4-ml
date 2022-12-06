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


# This module is for testing the app

import pytest
from .api import load_model, generate_predictions

MODEL_PATH = 'model.json'
DATA = [{'V1': -0.356, 'V2': 0.725, 'V3': 1.972, 'V4': 0.831, 'V5': 0.37, 'V6': -0.108,
         'V7': 0.752, 'V8': -0.12, 'V9': -0.421, 'V10': -0.06, 'V11': -0.508, 'V12': 0.426,
         'V13': 0.414, 'V14': -0.698, 'V15': -1.465, 'V16': -0.119, 'V17': -0.145, 'V18': -1.332,
         'V19': -1.547, 'V20': -0.134, 'V21': 0.021, 'V22': 0.424, 'V23': -0.016, 'V24': 0.467,
         'V25': -0.81, 'V26': 0.657, 'V27': -0.043, 'V28': -0.046, 'Amount': 0.0}]


# Test load_model
@pytest.mark.parametrize("model_path", [MODEL_PATH])
def test_load_model(model_path):
    model = load_model(model_path=model_path)
    assert model is not None


# Test generate_predictions
@pytest.mark.parametrize("model, data",
                         [(load_model(model_path=MODEL_PATH), DATA)])
def test_generate_predictions(model, data):
    predictions = generate_predictions(model=model, data=data)
    assert predictions is not None
    assert len(predictions) == 1
