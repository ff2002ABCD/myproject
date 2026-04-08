#ifndef __DAC_CONTROLLER_H
#define __DAC_CONTROLLER_H
#include "main.h"

#define MCP4725_ADDR 0xC0  // MCP4725 I2C??
#define CMD_WRITE_DAC 0x40  // ??DAC?????

void dac_controller_init(void);
void update_frequency(uint16_t freq);
void dac_update_handler(void) ;

#endif
