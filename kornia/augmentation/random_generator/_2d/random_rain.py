from __future__ import annotations

import torch
from torch.distributions import Uniform

from kornia.augmentation.random_generator.base import RandomGeneratorBase
from kornia.augmentation.utils import _adapted_rsampling, _common_param_check, _range_bound
from kornia.core import Tensor


class RainGenerator(RandomGeneratorBase):
    def __init__(
        self, number_of_drops: tuple[int, int], drop_height: tuple[int, int], drop_width: tuple[int, int]
    ) -> None:
        super().__init__()
        self.number_of_drops = number_of_drops
        self.drop_height = drop_height
        self.drop_width = drop_width

    def __repr__(self) -> str:
        repr = f"number_of_drops={self.number_of_drops}, drop_height={self.drop_height}, drop_width={self.drop_width}"
        return repr

    def make_samplers(self, device: torch.device, dtype: torch.dtype) -> None:
        number_of_drops = _range_bound(
            self.number_of_drops,
            'number_of_drops',
            center=self.number_of_drops[0] / 2 + self.number_of_drops[1] / 2,
            bounds=(self.number_of_drops[0], self.number_of_drops[1] + 1),
        ).to(device=device, dtype=dtype)
        drop_height = _range_bound(
            self.drop_height,
            'drop_height',
            center=self.drop_height[0] / 2 + self.drop_height[1] / 2,
            bounds=(self.drop_height[0], self.drop_height[1] + 1),
        ).to(device=device, dtype=dtype)
        drop_width = _range_bound(
            self.drop_width,
            'drop_width',
            center=self.drop_width[0] / 2 + self.drop_width[1] / 2,
            bounds=(self.drop_width[0], self.drop_width[1] + 1),
        ).to(device=device, dtype=dtype)

        drop_coordinates = _range_bound((0, 1), 'drops_coordinate', center=0.5, bounds=(0, 1)).to(device=device)

        self.number_of_drops_sampler = Uniform(number_of_drops[0], number_of_drops[1], validate_args=False)
        self.drop_height_sampler = Uniform(drop_height[0], drop_height[1], validate_args=False)
        self.drop_width_sampler = Uniform(drop_width[0], drop_width[1], validate_args=False)
        self.coordinates_sampler = Uniform(drop_coordinates[0], drop_coordinates[1], validate_args=False)

    def forward(self, batch_shape: tuple[int, ...], same_on_batch: bool = False) -> dict[str, Tensor]:
        batch_size = batch_shape[0]
        _common_param_check(batch_size, same_on_batch)
        # self.ksize_factor.expand((batch_size, -1))
        number_of_drops_factor = _adapted_rsampling((batch_size,), self.number_of_drops_sampler, same_on_batch).to(
            dtype=torch.int32
        )
        drop_height_factor = _adapted_rsampling((batch_size,), self.drop_height_sampler, same_on_batch).to(
            dtype=torch.int32
        )
        drop_width_factor = _adapted_rsampling((batch_size,), self.drop_width_sampler, same_on_batch).to(
            dtype=torch.int32
        )
        if not same_on_batch:
            coordinates_factor = [
                _adapted_rsampling((number_of_drops, 2), self.coordinates_sampler, False)
                for number_of_drops in number_of_drops_factor
            ]
        else:
            coordinates_factor = _adapted_rsampling((number_of_drops_factor[0], 2), self.coordinates_sampler, False)
            coordinates_factor = [coordinates_factor] * batch_size

        return dict(
            coordinates_factor=coordinates_factor,
            drop_height_factor=drop_height_factor,
            drop_width_factor=drop_width_factor,
        )
