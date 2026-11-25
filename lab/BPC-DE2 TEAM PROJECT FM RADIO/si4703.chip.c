#include "wokwi-api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#define SI4703_ADDRESS 0x10

#define REG_POWERCFG    0x02
#define REG_CHANNEL     0x03
#define REG_SYSCONFIG1  0x04
#define REG_SYSCONFIG2  0x05

#define REG_STATUSRSSI  0x0A
#define REG_READCHAN    0x0B
#define REG_RDSA        0x0C
#define REG_RDSB        0x0D
#define REG_RDSC        0x0E
#define REG_RDSD        0x0F

#define BIT_DMUTE       14
#define BIT_TUNE        15
#define BIT_RDS         12

#define BIT_RDSR        15
#define BIT_STC         14


typedef struct {
  uint16_t reg[16];

  uint8_t write_reg;
  bool write_high;
  uint8_t high_byte;

  uint8_t read_reg;
  bool read_high;

  uint8_t rds_segment;

  float frequency;
  uint8_t volume;
  bool muted;

  pin_t rst;
} chip_state_t;


typedef struct {
  float frequency;
  const char ps[9];
  uint16_t pi;
} station_t;


static const station_t stations[] = {
  {88.2f, "EVROPA 2", 0x2201},
  {89.6f, "RADIO Z ", 0x2202},
  {90.0f, "KISS    ", 0x2203},
  {91.0f, "FREKV1  ", 0x2204},
  {96.6f, "IMPULS  ", 0x2205}
};


#define STATION_COUNT \
  (sizeof(stations) / sizeof(stations[0]))


static const station_t *find_station(float frequency) {
  for (int i = 0; i < STATION_COUNT; i++) {
    float diff = frequency - stations[i].frequency;

    if (diff < 0) {
      diff = -diff;
    }

    if (diff < 0.05f) {
      return &stations[i];
    }
  }

  return NULL;
}


static void clear_rds(chip_state_t *chip) {
  chip->reg[REG_STATUSRSSI] &= ~(1 << BIT_RDSR);

  chip->reg[REG_RDSA] = 0;
  chip->reg[REG_RDSB] = 0;
  chip->reg[REG_RDSC] = 0;
  chip->reg[REG_RDSD] = 0;
}


static void prepare_rds(chip_state_t *chip) {
  if (!(chip->reg[REG_SYSCONFIG1] & (1 << BIT_RDS))) {
    clear_rds(chip);
    return;
  }

  const station_t *station = find_station(
    chip->frequency
  );

  if (station == NULL) {
    clear_rds(chip);
    chip->rds_segment = 0;
    return;
  }

  uint8_t segment = chip->rds_segment;

  chip->reg[REG_STATUSRSSI] |= (1 << BIT_RDSR);

  // Block A - PI code
  chip->reg[REG_RDSA] = station->pi;

  // Block B - Group 0A + segment address
  chip->reg[REG_RDSB] = segment & 0x03;

  // Block C - not used in our simulation
  chip->reg[REG_RDSC] = 0;

  // Block D - two PS characters
  uint8_t char_index = segment * 2;

  chip->reg[REG_RDSD] =
    ((uint16_t)station->ps[char_index] << 8)
    |
    (uint8_t)station->ps[char_index + 1];

  chip->rds_segment++;

  if (chip->rds_segment >= 4) {
    chip->rds_segment = 0;
  }
}


static void update_register(
  chip_state_t *chip,
  uint8_t reg,
  uint16_t old_value
) {
  uint16_t value = chip->reg[reg];

  if (reg == REG_POWERCFG) {
    bool old_muted =
      (old_value & (1 << BIT_DMUTE)) == 0;

    bool new_muted =
      (value & (1 << BIT_DMUTE)) == 0;

    chip->muted = new_muted;

    if (old_muted != new_muted) {
      printf(
        "FM mute: %s\n",
        new_muted ? "ON" : "OFF"
      );
    }
  }


  if (reg == REG_CHANNEL) {
    uint16_t channel = value & 0x03FF;

    chip->reg[REG_READCHAN] = channel;

    chip->frequency =
      87.5f + ((float)channel / 10.0f);

    if (value & (1 << BIT_TUNE)) {
      chip->reg[REG_STATUSRSSI] |=
        (1 << BIT_STC);

      printf(
        "FM frequency: %.1f MHz\n",
        chip->frequency
      );

      chip->rds_segment = 0;
    }
    else {
      chip->reg[REG_STATUSRSSI] &=
        ~(1 << BIT_STC);
    }
  }


  if (reg == REG_SYSCONFIG2) {
    uint8_t new_volume = value & 0x0F;

    if (new_volume != chip->volume) {
      chip->volume = new_volume;

      printf(
        "FM volume: %u\n",
        chip->volume
      );
    }
  }
}


static bool on_i2c_connect(
  void *user_data,
  uint32_t address,
  bool read
) {
  chip_state_t *chip = user_data;

  if (read) {
    prepare_rds(chip);

    chip->read_reg = REG_STATUSRSSI;
    chip->read_high = true;
  }
  else {
    chip->write_reg = REG_POWERCFG;
    chip->write_high = true;
  }

  return true;
}


static uint8_t on_i2c_read(void *user_data) {
  chip_state_t *chip = user_data;

  uint16_t value =
    chip->reg[chip->read_reg];

  uint8_t result;

  if (chip->read_high) {
    result = (value >> 8) & 0xFF;
    chip->read_high = false;
  }
  else {
    result = value & 0xFF;

    chip->read_high = true;
    chip->read_reg++;

    if (chip->read_reg >= 0x10) {
      chip->read_reg = 0x00;
    }
  }

  return result;
}


static bool on_i2c_write(
  void *user_data,
  uint8_t data
) {
  chip_state_t *chip = user_data;

  if (chip->write_high) {
    chip->high_byte = data;
    chip->write_high = false;
  }
  else {
    uint16_t old_value =
      chip->reg[chip->write_reg];

    chip->reg[chip->write_reg] =
      ((uint16_t)chip->high_byte << 8)
      | data;

    update_register(
      chip,
      chip->write_reg,
      old_value
    );

    chip->write_reg++;

    if (chip->write_reg >= 0x0A) {
      chip->write_reg = REG_POWERCFG;
    }

    chip->write_high = true;
  }

  return true;
}


static void on_i2c_disconnect(
  void *user_data
) {
}


void chip_init() {
  chip_state_t *chip =
    calloc(1, sizeof(chip_state_t));

  chip->rst =
    pin_init("RST", INPUT_PULLUP);

  chip->frequency = 99.5f;
  chip->volume = 1;
  chip->muted = false;
  chip->rds_segment = 0;

  uint16_t channel =
    (uint16_t)((99.5f - 87.5f) * 10);

  chip->reg[REG_READCHAN] = channel;

  const i2c_config_t i2c_config = {
    .address = SI4703_ADDRESS,

    .scl =
      pin_init("SCLK", INPUT_PULLUP),

    .sda =
      pin_init("SDIO", INPUT_PULLUP),

    .connect = on_i2c_connect,
    .read = on_i2c_read,
    .write = on_i2c_write,
    .disconnect = on_i2c_disconnect,
    .user_data = chip,
  };

  i2c_init(&i2c_config);

  printf(
    "Si4703 virtual FM receiver ready\n"
  );

  printf(
    "I2C address: 0x10\n"
  );
}