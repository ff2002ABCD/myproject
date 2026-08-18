//SPI in MASTER 3 wires MODE 1 200Kbps
//TIMER 2 25us overflow	with interrupt
//TIMER 3 1ms overflow no interrupt

#ifndef F410INIT_H
#define F410INIT_H

#include "C8051F410X.H"

// Initialization function for device,
// Call Init_Device() from your main program
extern void Init_Device(void);

#endif
