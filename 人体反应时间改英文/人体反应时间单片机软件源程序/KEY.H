#ifndef KEY_H 
#define KEY_H

#include "DISPLCD.h"

#define keyNumN 1
#define keySNN0 50		//
#define keySNN1 5
#define keySNN2 30
#define keySNN3 200
#define keyAutoTN1 50
#define keyAutoTN2 20
#define keyAutoTN3 2
#define keyAutoTN4 3

//#define PKUP P23		//low enable
//#define PKDN P24
//#define PKFN P25
//#define PKET P26
#define PKUP P23		//low enable
#define PKDN P24
#define PKFN P25
#define PKET P26

extern void (* keyUpSv)();
extern void (* keyDownSv)();
extern void (* keyFunSv)();
extern void (* keyEntSv)();

extern void keySvNull();
extern void keyRst();
extern void keyProc();			//10ms

#endif
