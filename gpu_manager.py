import gc
import os
import threading
import time
from typing import Callable, Optional

import torch
from loguru import logger


class GPUManager:
    def __init__(self, idle_timeout: int = 60):
        self.idle_timeout = idle_timeout
        self.last_used = time.time()
        self.model = None
        self.lock = threading.Lock()
        self.timer = None
        self.load_func = None

    def get_model(self, load_func: Callable):
        with self.lock:
            self.last_used = time.time()
            if self.model is None:
                logger.info("Loading model to GPU...")
                self.model = load_func()
                self.load_func = load_func
            self._reset_timer()
            return self.model

    def _reset_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.idle_timeout, self._offload)
        self.timer.daemon = True
        self.timer.start()

    def _offload(self):
        with self.lock:
            if time.time() - self.last_used >= self.idle_timeout:
                logger.info("Offloading model from GPU...")
                self.model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

    def force_offload(self):
        with self.lock:
            if self.model is not None:
                logger.info("Force offloading model...")
                self.model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

    def get_status(self):
        with self.lock:
            if torch.cuda.is_available():
                mem_used = torch.cuda.memory_allocated() / 1024**3
                mem_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                return {
                    "loaded": self.model is not None,
                    "gpu_memory_used": f"{mem_used:.2f}GB",
                    "gpu_memory_total": f"{mem_total:.2f}GB",
                    "last_used": time.time() - self.last_used,
                }
            return {"loaded": self.model is not None, "device": "cpu"}


gpu_manager = GPUManager(idle_timeout=int(os.getenv("GPU_IDLE_TIMEOUT", "60")))
