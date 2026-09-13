"""
SwinIR: Image Restoration Using Swin Transformer
Architecture implementation compatible with official pretrained weights.

Reference: Liang et al., "SwinIR: Image Restoration Using Swin Transformer", ICCV 2021
Weights source: https://github.com/JingyunLiang/SwinIR

This file implements the SwinIR-M architecture for classical image super-resolution.
The layer naming and structure exactly match the official implementation to ensure
pretrained weight compatibility.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.checkpoint as checkpoint
from typing import Optional, Tuple


def drop_path(x: torch.Tensor, drop_prob: float = 0.0, training: bool = False) -> torch.Tensor:
    """Drop paths (Stochastic Depth) per sample."""
    if drop_prob == 0.0 or not training:
        return x
    keep_prob = 1 - drop_prob
    shape = (x.shape[0],) + (1,) * (x.ndim - 1)
    random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
    random_tensor.floor_()
    output = x.div(keep_prob) * random_tensor
    return output


class DropPath(nn.Module):
    """Drop paths (Stochastic Depth) per sample."""
    def __init__(self, drop_prob: float = 0.0):
        super().__init__()
        self.drop_prob = drop_prob

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return drop_path(x, self.drop_prob, self.training)


class Mlp(nn.Module):
    """MLP as used in Vision Transformer and SwinIR."""
    def __init__(self, in_features: int, hidden_features: Optional[int] = None,
                 out_features: Optional[int] = None, act_layer=nn.GELU, drop: float = 0.0):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x


def window_partition(x: torch.Tensor, window_size: int) -> torch.Tensor:
    """Partition feature map into non-overlapping windows.

    Args:
        x: (B, H, W, C)
        window_size: window size

    Returns:
        windows: (num_windows*B, window_size, window_size, C)
    """
    B, H, W, C = x.shape
    x = x.view(B, H // window_size, window_size, W // window_size, window_size, C)
    windows = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(-1, window_size, window_size, C)
    return windows


def window_reverse(windows: torch.Tensor, window_size: int, H: int, W: int) -> torch.Tensor:
    """Reverse window partition.

    Args:
        windows: (num_windows*B, window_size, window_size, C)
        window_size: window size
        H, W: spatial dimensions

    Returns:
        x: (B, H, W, C)
    """
    B = int(windows.shape[0] / (H * W / window_size / window_size))
    x = windows.view(B, H // window_size, W // window_size, window_size, window_size, -1)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(B, H, W, -1)
    return x


class WindowAttention(nn.Module):
    """Window based multi-head self attention (W-MSA) with relative position bias.

    Args:
        dim: Number of input channels.
        window_size: The height and width of the window.
        num_heads: Number of attention heads.
        qkv_bias: If True, add a learnable bias to query, key, value.
        qk_scale: Override default qk scale of head_dim ** -0.5 if set.
        attn_drop: Dropout ratio of attention weight.
        proj_drop: Dropout ratio of output.
    """
    def __init__(self, dim: int, window_size: Tuple[int, int], num_heads: int,
                 qkv_bias: bool = True, qk_scale: Optional[float] = None,
                 attn_drop: float = 0.0, proj_drop: float = 0.0):
        super().__init__()
        self.dim = dim
        self.window_size = window_size
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** -0.5

        # Relative position bias table
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), num_heads)
        )

        # Compute relative position index
        coords_h = torch.arange(self.window_size[0])
        coords_w = torch.arange(self.window_size[1])
        coords = torch.stack(torch.meshgrid([coords_h, coords_w], indexing='ij'))
        coords_flatten = torch.flatten(coords, 1)
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()
        relative_coords[:, :, 0] += self.window_size[0] - 1
        relative_coords[:, :, 1] += self.window_size[1] - 1
        relative_coords[:, :, 0] *= 2 * self.window_size[1] - 1
        relative_position_index = relative_coords.sum(-1)
        self.register_buffer("relative_position_index", relative_position_index)

        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

        nn.init.trunc_normal_(self.relative_position_bias_table, std=0.02)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: input features (num_windows*B, N, C)
            mask: (0/-inf) attention mask (num_windows, Wh*Ww, Wh*Ww) or None
        """
        B_, N, C = x.shape
        qkv = self.qkv(x).reshape(B_, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        q = q * self.scale
        attn = (q @ k.transpose(-2, -1))

        relative_position_bias = self.relative_position_bias_table[
            self.relative_position_index.view(-1)
        ].view(self.window_size[0] * self.window_size[1], self.window_size[0] * self.window_size[1], -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()
        attn = attn + relative_position_bias.unsqueeze(0)

        if mask is not None:
            nW = mask.shape[0]
            attn = attn.view(B_ // nW, nW, self.num_heads, N, N) + mask.unsqueeze(1).unsqueeze(0)
            attn = attn.view(-1, self.num_heads, N, N)
            attn = self.softmax(attn)
        else:
            attn = self.softmax(attn)

        attn = self.attn_drop(attn)
        x = (attn @ v).transpose(1, 2).reshape(B_, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x


class SwinTransformerBlock(nn.Module):
    """Swin Transformer Block.

    Args:
        dim: Number of input channels.
        input_resolution: Input resolution.
        num_heads: Number of attention heads.
        window_size: Window size.
        shift_size: Shift size for SW-MSA.
        mlp_ratio: Ratio of mlp hidden dim to embedding dim.
        qkv_bias: If True, add a learnable bias to query, key, value.
        qk_scale: Override default qk scale of head_dim ** -0.5 if set.
        drop: Dropout rate.
        attn_drop: Attention dropout rate.
        drop_path: Stochastic depth rate.
        act_layer: Activation layer.
        norm_layer: Normalization layer.
    """
    def __init__(self, dim: int, input_resolution: Tuple[int, int], num_heads: int,
                 window_size: int = 7, shift_size: int = 0, mlp_ratio: float = 4.0,
                 qkv_bias: bool = True, qk_scale: Optional[float] = None,
                 drop: float = 0.0, attn_drop: float = 0.0, drop_path: float = 0.0,
                 act_layer=nn.GELU, norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.num_heads = num_heads
        self.window_size = window_size
        self.shift_size = shift_size
        self.mlp_ratio = mlp_ratio

        if min(self.input_resolution) <= self.window_size:
            self.shift_size = 0
            self.window_size = min(self.input_resolution)
        assert 0 <= self.shift_size < self.window_size, "shift_size must be in [0, window_size)"

        self.norm1 = norm_layer(dim)
        self.attn = WindowAttention(
            dim, window_size=(self.window_size, self.window_size),
            num_heads=num_heads, qkv_bias=qkv_bias, qk_scale=qk_scale,
            attn_drop=attn_drop, proj_drop=drop
        )
        self.drop_path = DropPath(drop_path) if drop_path > 0.0 else nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)

        # Calculate attention mask for shifted window MSA
        if self.shift_size > 0:
            attn_mask = self._calculate_mask(self.input_resolution)
        else:
            attn_mask = None
        self.register_buffer("attn_mask", attn_mask)

    def _calculate_mask(self, input_resolution: Tuple[int, int]) -> torch.Tensor:
        H, W = input_resolution
        img_mask = torch.zeros((1, H, W, 1))
        h_slices = (
            slice(0, -self.window_size),
            slice(-self.window_size, -self.shift_size),
            slice(-self.shift_size, None),
        )
        w_slices = (
            slice(0, -self.window_size),
            slice(-self.window_size, -self.shift_size),
            slice(-self.shift_size, None),
        )
        cnt = 0
        for h in h_slices:
            for w in w_slices:
                img_mask[:, h, w, :] = cnt
                cnt += 1

        mask_windows = window_partition(img_mask, self.window_size)
        mask_windows = mask_windows.view(-1, self.window_size * self.window_size)
        attn_mask = mask_windows.unsqueeze(1) - mask_windows.unsqueeze(2)
        attn_mask = attn_mask.masked_fill(attn_mask != 0, float(-100.0)).masked_fill(attn_mask == 0, float(0.0))
        return attn_mask

    def forward(self, x: torch.Tensor, x_size: Tuple[int, int]) -> torch.Tensor:
        H, W = x_size
        B, L, C = x.shape

        shortcut = x
        x = self.norm1(x)
        x = x.view(B, H, W, C)

        # Cyclic shift
        if self.shift_size > 0:
            shifted_x = torch.roll(x, shifts=(-self.shift_size, -self.shift_size), dims=(1, 2))
        else:
            shifted_x = x

        # Partition windows
        x_windows = window_partition(shifted_x, self.window_size)
        x_windows = x_windows.view(-1, self.window_size * self.window_size, C)

        # W-MSA/SW-MSA (recompute mask for variable input sizes)
        if self.input_resolution == x_size:
            attn_windows = self.attn(x_windows, mask=self.attn_mask)
        else:
            attn_windows = self.attn(
                x_windows,
                mask=self._calculate_mask(x_size).to(x.device) if self.shift_size > 0 else None
            )

        # Merge windows
        attn_windows = attn_windows.view(-1, self.window_size, self.window_size, C)
        shifted_x = window_reverse(attn_windows, self.window_size, H, W)

        # Reverse cyclic shift
        if self.shift_size > 0:
            x = torch.roll(shifted_x, shifts=(self.shift_size, self.shift_size), dims=(1, 2))
        else:
            x = shifted_x

        x = x.view(B, H * W, C)

        # FFN
        x = shortcut + self.drop_path(x)
        x = x + self.drop_path(self.mlp(self.norm2(x)))

        return x


class PatchEmbed(nn.Module):
    """Image to Patch Embedding (flatten + optional norm)."""
    def __init__(self, img_size: int = 224, patch_size: int = 4, in_chans: int = 3,
                 embed_dim: int = 96, norm_layer: Optional[type] = None):
        super().__init__()
        img_size = (img_size, img_size) if isinstance(img_size, int) else img_size
        patch_size = (patch_size, patch_size) if isinstance(patch_size, int) else patch_size
        patches_resolution = [img_size[0] // patch_size[0], img_size[1] // patch_size[1]]
        self.img_size = img_size
        self.patch_size = patch_size
        self.patches_resolution = patches_resolution
        self.num_patches = patches_resolution[0] * patches_resolution[1]
        self.in_chans = in_chans
        self.embed_dim = embed_dim
        if norm_layer is not None:
            self.norm = norm_layer(embed_dim)
        else:
            self.norm = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.flatten(2).transpose(1, 2)  # B C H W -> B (H*W) C
        if self.norm is not None:
            x = self.norm(x)
        return x


class PatchUnEmbed(nn.Module):
    """Patch Unembedding: reshape back to feature map."""
    def __init__(self, img_size: int = 224, patch_size: int = 4, in_chans: int = 3,
                 embed_dim: int = 96, norm_layer: Optional[type] = None):
        super().__init__()
        img_size = (img_size, img_size) if isinstance(img_size, int) else img_size
        patch_size = (patch_size, patch_size) if isinstance(patch_size, int) else patch_size
        patches_resolution = [img_size[0] // patch_size[0], img_size[1] // patch_size[1]]
        self.img_size = img_size
        self.patch_size = patch_size
        self.patches_resolution = patches_resolution
        self.num_patches = patches_resolution[0] * patches_resolution[1]
        self.in_chans = in_chans
        self.embed_dim = embed_dim

    def forward(self, x: torch.Tensor, x_size: Tuple[int, int]) -> torch.Tensor:
        B, HW, C = x.shape
        x = x.transpose(1, 2).view(B, self.embed_dim, x_size[0], x_size[1])  # B (H*W) C -> B C H W
        return x


class BasicLayer(nn.Module):
    """A basic Swin Transformer layer for one stage (contains multiple transformer blocks).

    Args:
        dim: Number of input channels.
        input_resolution: Input resolution.
        depth: Number of blocks.
        num_heads: Number of attention heads.
        window_size: Local window size.
        mlp_ratio: Ratio of mlp hidden dim to embedding dim.
        qkv_bias: If True, add a learnable bias to query, key, value.
        qk_scale: Override default qk scale of head_dim ** -0.5 if set.
        drop: Dropout rate.
        attn_drop: Attention dropout rate.
        drop_path: Stochastic depth rate.
        norm_layer: Normalization layer.
    """
    def __init__(self, dim: int, input_resolution: Tuple[int, int], depth: int,
                 num_heads: int, window_size: int, mlp_ratio: float = 4.0,
                 qkv_bias: bool = True, qk_scale: Optional[float] = None,
                 drop: float = 0.0, attn_drop: float = 0.0,
                 drop_path: float = 0.0, norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.depth = depth

        # Build blocks - alternate between W-MSA and SW-MSA
        self.blocks = nn.ModuleList([
            SwinTransformerBlock(
                dim=dim, input_resolution=input_resolution,
                num_heads=num_heads, window_size=window_size,
                shift_size=0 if (i % 2 == 0) else window_size // 2,
                mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, qk_scale=qk_scale,
                drop=drop, attn_drop=attn_drop,
                drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path,
                norm_layer=norm_layer
            )
            for i in range(depth)
        ])

    def forward(self, x: torch.Tensor, x_size: Tuple[int, int]) -> torch.Tensor:
        for blk in self.blocks:
            x = blk(x, x_size)
        return x


class RSTB(nn.Module):
    """Residual Swin Transformer Block (RSTB).

    Contains a BasicLayer (sequence of SwinTransformerBlocks),
    a convolution, and patch embed/unembed for residual connection.
    """
    def __init__(self, dim: int, input_resolution: Tuple[int, int], depth: int,
                 num_heads: int, window_size: int, mlp_ratio: float = 4.0,
                 qkv_bias: bool = True, qk_scale: Optional[float] = None,
                 drop: float = 0.0, attn_drop: float = 0.0,
                 drop_path: float = 0.0, norm_layer=nn.LayerNorm,
                 img_size: int = 224, patch_size: int = 4,
                 resi_connection: str = '1conv'):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution

        self.residual_group = BasicLayer(
            dim=dim, input_resolution=input_resolution, depth=depth,
            num_heads=num_heads, window_size=window_size,
            mlp_ratio=mlp_ratio, qkv_bias=qkv_bias, qk_scale=qk_scale,
            drop=drop, attn_drop=attn_drop, drop_path=drop_path,
            norm_layer=norm_layer
        )

        if resi_connection == '1conv':
            self.conv = nn.Conv2d(dim, dim, 3, 1, 1)
        elif resi_connection == '3conv':
            self.conv = nn.Sequential(
                nn.Conv2d(dim, dim // 4, 3, 1, 1),
                nn.LeakyReLU(negative_slope=0.2, inplace=True),
                nn.Conv2d(dim // 4, dim // 4, 1, 1, 0),
                nn.LeakyReLU(negative_slope=0.2, inplace=True),
                nn.Conv2d(dim // 4, dim, 3, 1, 1),
            )

        self.patch_embed = PatchEmbed(
            img_size=img_size, patch_size=patch_size, in_chans=0,
            embed_dim=dim, norm_layer=None
        )
        self.patch_unembed = PatchUnEmbed(
            img_size=img_size, patch_size=patch_size, in_chans=0,
            embed_dim=dim, norm_layer=None
        )

    def forward(self, x: torch.Tensor, x_size: Tuple[int, int]) -> torch.Tensor:
        return self.patch_embed(
            self.conv(self.patch_unembed(self.residual_group(x, x_size), x_size))
        ) + x


class Upsample(nn.Sequential):
    """Upsample module using PixelShuffle.

    Args:
        scale: Upsample scale factor. Supported: 2, 3, 4, 8.
        num_feat: Number of intermediate channels.
    """
    def __init__(self, scale: int, num_feat: int):
        m = []
        if (scale & (scale - 1)) == 0:  # scale = 2^n
            for _ in range(int(math.log(scale, 2))):
                m.append(nn.Conv2d(num_feat, 4 * num_feat, 3, 1, 1))
                m.append(nn.PixelShuffle(2))
        elif scale == 3:
            m.append(nn.Conv2d(num_feat, 9 * num_feat, 3, 1, 1))
            m.append(nn.PixelShuffle(3))
        else:
            raise ValueError(f"Unsupported scale factor: {scale}. Supported: 2, 3, 4, 8.")
        super().__init__(*m)


class SwinIR(nn.Module):
    """SwinIR: Image Restoration Using Swin Transformer.

    This implements the SwinIR-M variant for classical super-resolution.
    Architecture matches the official implementation for pretrained weight compatibility.

    CURRENT PROTOTYPE MODEL:
        SwinIR-M pretrained on DIV2K for classical SR (x4).
        Input: 3 channels (RGB). Output: 3 channels (RGB) at scale×.

    INTENDED RESEARCH MODEL:
        Reliability-aware multispectral transformer with 4-channel (B,G,R,NIR) input,
        joint spectral processing, and integrated uncertainty estimation.

    Args:
        img_size: Input image size (used to compute resolution for attention).
        patch_size: Patch size (1 for SR tasks).
        in_chans: Number of input image channels.
        embed_dim: Patch embedding dimension.
        depths: Depth of each Swin Transformer layer.
        num_heads: Number of attention heads in each layer.
        window_size: Window size.
        mlp_ratio: Ratio of mlp hidden dim to embedding dim.
        qkv_bias: If True, add a learnable bias to query, key, value.
        qk_scale: Override default qk scale.
        drop_rate: Dropout rate.
        attn_drop_rate: Attention dropout rate.
        drop_path_rate: Stochastic depth rate.
        norm_layer: Normalization layer.
        ape: If True, add absolute position embedding.
        patch_norm: If True, add normalization after patch embedding.
        upscale: Upscale factor (2, 3, 4).
        img_range: Image range (1.0 or 255.0).
        upsampler: Upsampler type ('pixelshuffle', 'pixelshuffledirect', 'nearest+conv', '').
        resi_connection: Residual connection type ('1conv', '3conv').
    """
    def __init__(self, img_size: int = 64, patch_size: int = 1, in_chans: int = 3,
                 embed_dim: int = 180, depths=(6, 6, 6, 6, 6, 6),
                 num_heads=(6, 6, 6, 6, 6, 6), window_size: int = 8,
                 mlp_ratio: float = 2.0, qkv_bias: bool = True,
                 qk_scale: Optional[float] = None, drop_rate: float = 0.0,
                 attn_drop_rate: float = 0.0, drop_path_rate: float = 0.1,
                 norm_layer=nn.LayerNorm, ape: bool = False,
                 patch_norm: bool = True, upscale: int = 4,
                 img_range: float = 1.0, upsampler: str = 'pixelshuffle',
                 resi_connection: str = '1conv', **kwargs):
        super().__init__()
        num_in_ch = in_chans
        num_out_ch = in_chans
        num_feat = 64
        self.img_range = img_range
        if in_chans == 3:
            rgb_mean = (0.4488, 0.4371, 0.4040)
            self.mean = torch.Tensor(rgb_mean).view(1, 3, 1, 1)
        else:
            self.mean = torch.zeros(1, 1, 1, 1)
        self.upscale = upscale
        self.upsampler = upsampler
        self.window_size = window_size

        # -- Shallow feature extraction --
        self.conv_first = nn.Conv2d(num_in_ch, embed_dim, 3, 1, 1)

        # -- Deep feature extraction --
        self.num_layers = len(depths)
        self.embed_dim = embed_dim
        self.ape = ape
        self.patch_norm = patch_norm
        self.num_features = embed_dim
        self.mlp_ratio = mlp_ratio

        # Patch embedding / unembedding
        self.patch_embed = PatchEmbed(
            img_size=img_size, patch_size=patch_size, in_chans=embed_dim,
            embed_dim=embed_dim,
            norm_layer=norm_layer if self.patch_norm else None
        )
        num_patches = self.patch_embed.num_patches
        patches_resolution = self.patch_embed.patches_resolution
        self.patches_resolution = patches_resolution

        self.patch_unembed = PatchUnEmbed(
            img_size=img_size, patch_size=patch_size, in_chans=embed_dim,
            embed_dim=embed_dim, norm_layer=None
        )

        # Absolute position embedding
        if self.ape:
            self.absolute_pos_embed = nn.Parameter(torch.zeros(1, num_patches, embed_dim))
            nn.init.trunc_normal_(self.absolute_pos_embed, std=0.02)

        self.pos_drop = nn.Dropout(p=drop_rate)

        # Stochastic depth
        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]

        # Build RSTB layers
        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            layer = RSTB(
                dim=embed_dim,
                input_resolution=(patches_resolution[0], patches_resolution[1]),
                depth=depths[i_layer],
                num_heads=num_heads[i_layer],
                window_size=window_size,
                mlp_ratio=self.mlp_ratio,
                qkv_bias=qkv_bias, qk_scale=qk_scale,
                drop=drop_rate, attn_drop=attn_drop_rate,
                drop_path=dpr[sum(depths[:i_layer]):sum(depths[:i_layer + 1])],
                norm_layer=norm_layer,
                img_size=img_size,
                patch_size=patch_size,
                resi_connection=resi_connection
            )
            self.layers.append(layer)
        self.norm = norm_layer(self.num_features)

        # -- Image reconstruction --
        if self.upsampler == 'pixelshuffle':
            # Classical SR
            self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1)
            self.conv_before_upsample = nn.Sequential(
                nn.Conv2d(embed_dim, num_feat, 3, 1, 1),
                nn.LeakyReLU(inplace=True)
            )
            self.upsample = Upsample(upscale, num_feat)
            self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=0.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    @torch.jit.ignore
    def no_weight_decay(self):
        return {'absolute_pos_embed'}

    @torch.jit.ignore
    def no_weight_decay_keywords(self):
        return {'relative_position_bias_table'}

    def check_image_size(self, x: torch.Tensor) -> torch.Tensor:
        """Pad input to be divisible by window_size."""
        _, _, h, w = x.size()
        mod_pad_h = (self.window_size - h % self.window_size) % self.window_size
        mod_pad_w = (self.window_size - w % self.window_size) % self.window_size
        x = F.pad(x, (0, mod_pad_w, 0, mod_pad_h), 'reflect')
        return x

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        x_size = (x.shape[2], x.shape[3])
        x = self.patch_embed(x)
        if self.ape:
            x = x + self.absolute_pos_embed
        x = self.pos_drop(x)
        for layer in self.layers:
            x = layer(x, x_size)
        x = self.norm(x)
        x = self.patch_unembed(x, x_size)
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        H, W = x.shape[2:]
        x = self.check_image_size(x)

        self.mean = self.mean.type_as(x)
        x = (x - self.mean) * self.img_range

        if self.upsampler == 'pixelshuffle':
            # Classical SR
            x = self.conv_first(x)
            x = self.conv_after_body(self.forward_features(x)) + x
            x = self.conv_before_upsample(x)
            x = self.conv_last(self.upsample(x))

        x = x / self.img_range + self.mean

        return x[:, :, :H * self.upscale, :W * self.upscale]


def build_swinir(upscale: int = 4, in_chans: int = 3) -> SwinIR:
    """Build SwinIR-M model for classical super-resolution.

    This factory function creates a SwinIR model with parameters matching
    the official pretrained weights for classical SR.

    Args:
        upscale: Scale factor (2, 3, or 4).
        in_chans: Number of input channels (3 for RGB).

    Returns:
        SwinIR model instance.
    """
    model = SwinIR(
        upscale=upscale,
        in_chans=in_chans,
        img_size=48,
        window_size=8,
        img_range=1.0,
        depths=[6, 6, 6, 6, 6, 6],
        embed_dim=180,
        num_heads=[6, 6, 6, 6, 6, 6],
        mlp_ratio=2.0,
        upsampler='pixelshuffle',
        resi_connection='1conv',
    )
    return model
