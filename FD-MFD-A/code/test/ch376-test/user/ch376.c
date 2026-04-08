#include "ch376.h"
#include "main.h"
#include "usart.h"
#include "spi.h"
#include "stdio.h"
#include "string.h"

//#define CMD_CHECK_EXIST 0x06
extern int fputc(int ch, FILE* file);
//#define CH376_CS_GPIO_PORT GPIOD


void xWriteCH376Cmd( unsigned char cmd ) { 
	uint8_t command[3]={0x57,0xAB,cmd};
	HAL_UART_Transmit(&huart2, command, 3,HAL_MAX_DELAY);
}

void xWriteCH376Data( unsigned char dat ) {
	uint8_t *data=&dat;
	HAL_UART_Transmit(&huart2, data, 1,HAL_MAX_DELAY);
}

/* 串口方式未用到 */
void xEndCH376Cmd(void)
{
}

unsigned char xReadCH376Data(void) { 
	uint8_t buffer[1];
	HAL_UART_Receive(&huart2, buffer, 1,HAL_MAX_DELAY);
	return buffer[0];
}

uint8_t CH376_TestConnection(void) { 
    uint8_t response;
		uint8_t test_data=0x53;
		xWriteCH376Cmd(CMD_CHECK_EXIST);
		xWriteCH376Data(test_data);
		response=xReadCH376Data();
//		xWriteCH376Data(response);
//		printf("res=%x\r\n",response);
    if (response == (uint8_t)(~test_data)) {
        return 1;  
    } else {
        return 0;  
    }
}

/* 查询CH376中断(INT#低电平) */
UINT8	Query376Interrupt( void )
{
	#ifdef	CH376_INT_WIRE                  /* 如果连接了CH376的中断引脚则直接查询中断引脚 */
		if(CH376_INT_WIRE) return FALSE ;
		else{
			//xReadCH376Data();               //产生中断的同时，串口会收到一个数据，直接读出来丢掉
			return TRUE ;
		}
	#else
		if ( USART2->SR&0x20 ) {             /* 如果未连接CH376的中断引脚则查询串口中断状态码 */
			USART2->SR = ~(0x20);          //清除RXNE	
			return( TRUE );
		}
		else return( FALSE );
	#endif	
}

uint8_t file_writeData(char* buf)
{
	uint8_t s,i;
	printf("数据长度%d...",strlen(buf));
	xWriteCH376Cmd(CMD2H_BYTE_WRITE);
	xWriteCH376Data(strlen(buf));
	xWriteCH376Data(0x00);
	if(xReadCH376Data()==0x1e) printf("正在写入数据...");
	xWriteCH376Cmd(CMD_WR_REQ_DATA);
	while(buf[i]!='\0')
	{
		xWriteCH376Data(buf[i]);
		printf("buf[%d]=%c ",i,buf[i]);
		i++;
	}
  xWriteCH376Cmd(CMD_BYTE_WR_GO);
	xReadCH376Data();
	s=xReadCH376Data();
	return s;
}




