import torch as th
from torch import nn
from torch.distributions import Categorical


class MaguroModel(nn.Module):
    """
        Small Conv-1D extractor for ABR
    """
    def __init__(self, history_len: int = 10, look_ahead_horizon: int = 5, 
                n_actions: int = 10, feature_dim: int = 256):
        super(MaguroModel, self).__init__()
        self.network_net = nn.Sequential(
            nn.Conv1d(history_len, 64, kernel_size=3, stride=1),
            nn.ReLU(), nn.Conv1d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(), nn.Flatten())
        self.video_size_net = nn.Sequential(
            nn.Conv1d(look_ahead_horizon, 32, kernel_size=5, stride=1),
            nn.ReLU(), nn.Conv1d(32, 32, kernel_size=5, stride=1),
            nn.ReLU(), nn.Flatten())
        self.ssim_net = nn.Sequential(
            nn.Conv1d(look_ahead_horizon, 32, kernel_size=5, stride=1),
            nn.ReLU(), nn.Conv1d(32, 32, kernel_size=5, stride=1),
            nn.ReLU(), nn.Flatten())
        self.policy_net = nn.Sequential(nn.Linear(feature_dim, 256), nn.ReLU())
        self.action_net = nn.Linear(256, n_actions)
        
    @th.no_grad() # ideally, this should be in a wrapper        
    def forward(self, observation: dict) -> int:
        network_features = self.network_net(observation["network_data"])
        video_features = self.video_size_net(observation["video_sizes"])
        quality_features = self.ssim_net(observation["ssim_dbs"])
        features = th.cat((network_features, video_features, quality_features),
            dim=1)
        action_logits = self.action_net(self.policy_net(features))
        dist = Categorical(logits=action_logits)
        action = th.argmax(dist.probs, dim=1)
        return action.item()