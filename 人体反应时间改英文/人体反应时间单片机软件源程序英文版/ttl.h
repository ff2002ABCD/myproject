#ifndef TTL_H
#define TTL_H

#include "RSP.H"
#include "KEY.H"
#include "DISPLCD.H"
#include "MATHFUN.H"

#define TTLDATAN 20

extern void ttlSt();
extern void ttlRst();
extern void ttlPush(unsigned int x);

extern unsigned int ttlData[TTLDATAN];
extern unsigned char ttlErr;

#endif