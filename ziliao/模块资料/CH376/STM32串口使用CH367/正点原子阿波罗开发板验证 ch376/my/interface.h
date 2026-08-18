#ifndef _INTERFACE_H_
#define _INTERFACE_H_

#include "CH376INC.H"
#include "sys.h"
#include "delay.h"


#define ERR_USB_UNKNOWN  0xFA


void	CH376_PORT_INIT( void );  		/* CH376通讯接口初始化 */

void	xEndCH376Cmd( void );			/* 结束CH376命令,仅用于SPI接口方式 */

void	xWriteCH376Cmd( unsigned char mCmd );	/* 向CH376写命令 */

void	xWriteCH376Data( unsigned char mData );	/* 向CH376写数据 */

unsigned char	xReadCH376Data( void );			/* 从CH376读数据 */

unsigned char	Query376Interrupt( void );		/* 查询CH376中断(INT#引脚为低电平) */

unsigned char	mInitCH376Host( void );			/* 初始化CH376 */



#endif

