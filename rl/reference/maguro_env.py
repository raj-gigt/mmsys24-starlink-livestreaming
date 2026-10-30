from base_env import BaseEnv
from utils import (
    make_reward_function, ssim_index_to_db, normalize, make_norm_function)
from typing import Callable, Union
import numpy as np
import torch as th
from collections import deque
from maguro_model import MaguroModel
from dataclasses import dataclass

HISTORY_LEN = 10
REBUF_HISTORY_LEN = 30

@dataclass
class Channel:
    name: str = ""
    chunks_sent: int = 0


class MaguroEnv(BaseEnv):
    """
        ABR Env for a PyTorch model trained using A2C
    """
    def setup_env(self, model_path: str) -> Callable:
        self.network_history = deque(maxlen=HISTORY_LEN)
        self.rebuf_history = deque(maxlen=REBUF_HISTORY_LEN)
        self.past_ssim_db = 0
        self.past_cum_rebuf = 0
        self.channel = Channel()
        self.min_reward = -5
        self.max_reward = 5
        reward_norm_function = make_norm_function(
            "sqrt_clip", self.min_reward, self.max_reward)
        self.reward_func = make_reward_function(norm_function=reward_norm_function)
        self.max_quality = 25 # SSIM dB
        self.max_video_size = 3 # s
        self.max_rebuf = 3 # s
        self.max_network_data = np.array(
            [self.max_quality, self.max_video_size, 20, 15, 
            self.max_reward - self.min_reward])
            # quality (SSIM dB), video size (MB),  delay (s), buffer (s), reward                 
        for _ in range(self.network_history.maxlen):
            self.network_history.append(np.zeros(shape=(5)))
        for _ in range(self.rebuf_history.maxlen):
            self.rebuf_history.append(0)
        model = MaguroModel()
        model.load_state_dict(th.load(model_path))
        model.eval()
        return model

    def rebuf_history_to_input(self) -> np.ndarray:
        rebuf_history = np.array(self.rebuf_history)
        rebuf_history = rebuf_history.reshape(
            (self.network_history.maxlen,
            self.rebuf_history.maxlen // self.network_history.maxlen))
        rebuf_history = np.sum(rebuf_history, axis=1, keepdims=True)
        rebuf_history = normalize(rebuf_history, max=self.max_rebuf)
        return rebuf_history

    def process_env_info(self, env_info: dict) -> dict:
        if self.channel.name == env_info["channel_name"]:
            self.channel.chunks_sent += 1
        else:
            self.channel.name = env_info["channel_name"]
            self.channel.chunks_sent = 0
        is_init = self.channel.chunks_sent <= 1 # first or second chunk

        if self.past_action is not None:
            env_info["past_chunk"]["ssim_db"] = ssim_index_to_db(
                env_info["past_chunk"]["ssim"])
            if not is_init:
                rebuf = max(0, env_info["cum_rebuf"] - self.past_cum_rebuf)
                quality_change = abs(
                    self.past_ssim_db - env_info["past_chunk"]["ssim_db"])
            else:
                # first or second action in the environment
                rebuf = 0 # ignore start-up delay
                quality_change = 0 # quality change penalty for first action
            reward = self.reward_func(
                env_info["past_chunk"]["ssim_db"], rebuf, quality_change)
            reward -= self.min_reward
            self.past_ssim_db = env_info["past_chunk"]["ssim_db"]
            self.past_cum_rebuf = env_info["cum_rebuf"]
            network_data = np.array(    
                [self.past_ssim_db, env_info["past_chunk"]["size"], 
                env_info["past_chunk"]["delay"], env_info["buffer"], reward])
            self.network_history.append(
                normalize(network_data, max=self.max_network_data))
            self.rebuf_history.append(rebuf)        

        network_data = np.concatenate(
            (np.array(self.network_history), self.rebuf_history_to_input()),
            axis=1)
        video_sizes = normalize(
            np.array(env_info["sizes"]), max=self.max_video_size)
        ssim_dbs = [
            [ssim_index_to_db(ssim) for ssim in timestamp] 
            for timestamp in env_info["ssims"]]
        ssim_dbs = normalize(np.array(ssim_dbs), max=self.max_quality)

        obs = {"network_data": network_data, 
                "video_sizes": video_sizes,
                "ssim_dbs": ssim_dbs}
        obs = {key: th.as_tensor(val, dtype=th.float32).unsqueeze_(0)
            for key, val in obs.items()}

        return obs