#include "ch376.h"
#include "main.h"
#include "usart.h"
#include "stdio.h"
#include "string.h"
#include "FILE_SYS.H"
#include "menu.h"

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
	uint8_t s,i=0;
	printf("数据长度%d...",strlen(buf));
	xWriteCH376Cmd(CMD2H_BYTE_WRITE);
	xWriteCH376Data(strlen(buf)%256);
	xWriteCH376Data(strlen(buf)>>8);
	if(xReadCH376Data()==0x1e) printf("正在写入数据...");
	xWriteCH376Cmd(CMD_WR_REQ_DATA);
	while(buf[i]!='\0')
	{
		xWriteCH376Data(buf[i]);
		printf("buf[%d]=%c\xff\xff\xff",i,buf[i]);
		i++;
	}
  xWriteCH376Cmd(CMD_BYTE_WR_GO);
	xReadCH376Data();
	s=xReadCH376Data();
	return s;
}

void ch376_init()
{
	printf( "Start\r\n" );
	if (CH376_TestConnection()) {
     printf("CH376 is connected and working!\r\n");
   } 
	else
	{
     printf("CH376 connection failed!\r\n");
  }
	//选择u盘模式
	printf("正在选择u盘模式...");
	xWriteCH376Cmd(CMD_SET_USB_MODE);
	xWriteCH376Data(0x06);
		if(xReadCH376Data()==0x51)
		{
			if(xReadCH376Data()==0x15)
			printf("设置成功\r\n");
		}		
	//判断是否连接
	printf("正在检查u盘连接...");
	CH376DiskConnect();
	if(xReadCH376Data()==USB_INT_SUCCESS) printf("连接成功\r\n");
	//初始化磁盘
	printf("正在初始化磁盘...");
	if(CH376DiskMount()==USB_INT_SUCCESS) printf("已就绪\r\n");
}

void ch376_writetest()
{
	//打开目录
	char str[200];
	sprintf(str,"/第%d组.CSV",cursor_group_num+1);
	printf("正在打开目录...");
	if(CH376FileCreate((PUINT8)str)==USB_INT_SUCCESS) printf("打开成功\xff\xff\xff");
	else printf("开启失败\xff\xff\xff");
	//获取当前文件大小
	uint32_t size=CH376GetFileSize();
	printf("size=%d\r\n",size);
	//写入表头
	if(file_writeData("序号,传感器坐标(cm),线圈电流(mA),磁场模(uT),X轴分量(uT),Y轴分量(uT),Z轴分量(uT)\n")==USB_INT_SUCCESS) printf("写入成功\xff\xff\xff");
	else printf("写入失败\xff\xff\xff");
//	if(file_writeData("序号,")==USB_INT_SUCCESS) printf("写入成功\xff\xff\xff");
//	else printf("写入失败\xff\xff\xff");
	//按行写入数据
	for(int i=0;i<table_length[cursor_group_num];i++)
	{
		sprintf(str,"%d,%.2f,%.1f,%.1f,%.1f,%.1f,%.1f\n",i+1,table[cursor_group_num][i].Pos,table[cursor_group_num][i].Current,table[cursor_group_num][i].Strength,table[cursor_group_num][i].GaX,table[cursor_group_num][i].GaY,table[cursor_group_num][i].GaZ);
		if(file_writeData(str)==USB_INT_SUCCESS) printf("写入成功\xff\xff\xff");
		else printf("写入失败\xff\xff\xff");
	}
//	//写入数据1	
//	float num=123.456;
//	sprintf(str,"%.1f,",num);
//	if(file_writeData(str)==USB_INT_SUCCESS) printf("写入成功\r\n");
//	else printf("写入失败\r\n");
//	
//	//写入数据2
//	num=234.6;
//	sprintf(str,"%.1f\n",num);
//	if(file_writeData(str)==USB_INT_SUCCESS) printf("写入成功\r\n");
//	else printf("写入失败\r\n");
////	
//	//写入数据3
//	num=456.6;
//	sprintf(str,"%.1f",num);
//	if(file_writeData(str)==USB_INT_SUCCESS) printf("写入成功\r\n");
//	else printf("写入失败\r\n");
	
	size=CH376GetFileSize();
	printf("filesize=%d\xff\xff\xff",size);
	//关闭文件
	printf("正在关闭文件\xff\xff\xff");
	
	if(CH376FileClose(1)==USB_INT_SUCCESS){ printf("关闭成功\xff\xff\xff");output_flag=1;}
	else output_flag=0;
}


