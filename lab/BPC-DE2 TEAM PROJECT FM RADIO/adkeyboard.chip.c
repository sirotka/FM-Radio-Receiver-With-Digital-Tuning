// Wokwi Custom Chip - For docs and examples see:
// https://docs.wokwi.com/chips-api/getting-started
//
// SPDX-License-Identifier: MIT
// Copyright 2023 

#include "wokwi-api.h"
#include <stdlib.h>

typedef struct {
  pin_t vol_up;
  pin_t vol_down;
  pin_t ok;
  pin_t up;
  pin_t down;
  pin_t out;
} chip_state_t;

static void update_output(chip_state_t *chip) {
  float voltage = 3.3f;

  if (pin_read(chip->vol_up) == LOW) {
    voltage = 0.4f;
  } else if (pin_read(chip->vol_down) == LOW) {
    voltage = 0.8f;
  } else if (pin_read(chip->ok) == LOW) {
    voltage = 1.2f;
  } else if (pin_read(chip->up) == LOW) {
    voltage = 1.6f;
  } else if (pin_read(chip->down) == LOW) {
    voltage = 2.0f;
  }

  pin_dac_write(chip->out, voltage);
}

static void pin_change(void *user_data, pin_t pin, uint32_t value) {
  chip_state_t *chip = (chip_state_t *)user_data;
  update_output(chip);
}

void chip_init() {
  chip_state_t *chip = malloc(sizeof(chip_state_t));

  chip->vol_up = pin_init("VOL_UP", INPUT_PULLUP);
  chip->vol_down = pin_init("VOL_DOWN", INPUT_PULLUP);
  chip->ok = pin_init("OK", INPUT_PULLUP);
  chip->up = pin_init("UP", INPUT_PULLUP);
  chip->down = pin_init("DOWN", INPUT_PULLUP);

  chip->out = pin_init("OUT", ANALOG);

  pin_watch_config_t watch = {
    .edge = BOTH,
    .pin_change = pin_change,
    .user_data = chip
  };

  pin_watch(chip->vol_up, &watch);
  pin_watch(chip->vol_down, &watch);
  pin_watch(chip->ok, &watch);
  pin_watch(chip->up, &watch);
  pin_watch(chip->down, &watch);

  update_output(chip);
}
