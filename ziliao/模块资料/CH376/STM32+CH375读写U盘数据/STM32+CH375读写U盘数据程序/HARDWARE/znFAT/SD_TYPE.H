#ifndef _SD_TYPE_H_
#define _SD_TYPE_H_



//加入类型相关头文件 比如AVR GCC中的 ROM类型在<AVR/pgmspace.h>中定义

#define UINT8   unsigned char
#define UINT16  unsigned int
#define UINT32  unsigned long 

#define INT8    char 
#define INT16   int
#define INT32   long

#define ROM_TYPE_UINT8  const unsigned char   
#define ROM_TYPE_UINT16 const unsigned int 
#define ROM_TYPE_UINT32 const unsigned long 	

#endif
