#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import warnings
from abc import ABC, abstractmethod
from threading import Thread
from time import sleep


class MLBaseModel(ABC):
    def __init__(self):
        print("Initializing model asynchronously")
        self.init_thread = Thread(target=self.init_model)
        self.init_thread.start()

    def __wait_until_ready__(self):
        """Only use this method for testing as it negates the benefits of having an asynchronous initialization"""
        warnings.warn("Waiting for model to be ready. Only use this method for testing as it negates the benefits of having an asynchronous initialization")
        while not self.is_ready():
            sleep(1)

    @abstractmethod
    def init_model(self):
        raise NotImplemented

    def is_ready(self) -> bool:
        """ Returns true only if the model is initialized and ready to perform inference. Defaults to checking the init_model() method has completed asynchronously. """
        return not self.init_thread.is_alive()

    @abstractmethod
    def inference(self, *args, **kwargs):
        raise NotImplemented
