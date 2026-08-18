#ifndef DACX_H
#define DACX_H

#include "C8051F410X.H"

extern unsigned int dacxD[2];

extern void dacxRst();
extern void dacxCopy(unsigned char i);

#endif