import torch
import torch.nn as nn
import torchvision.models as models

class VideoResNetLSTM(nn.Module):
    def __init__(self, pretrained=True, num_classes=2, lstm_hidden_size=256, lstm_layers=1, bidirectional=False):
        super(VideoResNetLSTM, self).__init__()

        # CNN backbone
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT if pretrained else None)
        self.feature_extractor = nn.Sequential(*list(backbone.children())[:-1])
        self.feature_dim = backbone.fc.in_features

        # LSTM
        self.lstm = nn.LSTM(
            input_size=self.feature_dim,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=bidirectional
        )

        self.classifier = nn.Linear(
            lstm_hidden_size * (2 if bidirectional else 1),
            num_classes
        )

    def forward(self, videos):
        B, T, C, H, W = videos.shape
        videos = videos.view(B * T, C, H, W)
        features = self.feature_extractor(videos)
        features = features.view(B, T, -1)
        lstm_out, (h_n, _) = self.lstm(features)
        final_feat = torch.cat((h_n[-2], h_n[-1]), dim=1) if self.lstm.bidirectional else h_n[-1]
        return self.classifier(final_feat)
