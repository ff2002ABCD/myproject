

#include "sys.h"
#include "delay.h"
#include "usart.h"
#include "led.h"
#include "key.h"
#include "lcd.h"
#include "sdram.h"
#include "stmflash.h"
#include "interface.h"     //底层接口函数
#include "FILE_SYS.H"      //文件系统应用层函数
//#include "iap.h"

void usrat_writ_cmd(unsigned char cmd);//带有0x57,0xAB头的发送函数
void usart_writ_date(unsigned char cmd);//发送单个字节
 
int main(void)
{
 
	u8 key = 0;
	u8 kwy_num = 0;
	u8 key_biao = 0;                 //按键标志位
	u16 oldcount=0;				    //老的串口接收数据值
 
    HAL_Init();                     //初始化HAL库   
    Stm32_Clock_Init(360,25,2,8);   //设置时钟,180Mhz
    delay_init(180);                //初始化延时函数
    uart_init(9600);              //初始化USART
    LED_Init();                     //初始化LED 
    KEY_Init();                     //初始化按键
    SDRAM_Init();                   //初始化SDRAM
    LCD_Init();                     //初始化LCD
	
	POINT_COLOR=RED;
	LCD_ShowString(30,20,200,16,16,"CH376 USRAT TO USB"); 
	

	while(1)
	{
		key = KEY_Scan(0);
		
		if(key == WKUP_PRES)
		{
			kwy_num ++;    //如果按键按下了，num++就会让事件进入下一步
			key_biao = 1;  //设置一个标志位，事件执行后清0，方便观察每一步进行情况
		   
		}
		
		if(kwy_num == 1 && key_biao ==1 )//1，测试命令，返回AA
		{
			usrat_writ_cmd(0x06);   
			usart_writ_date(0x55);
			//kwy_num ++;  //如果想要连续进行，在这里让num继续++就可以了
			key_biao = 0;
		}
		else if(kwy_num == 2 && key_biao ==1)//2,选择U盘模式，返回0x51 0x15
		{
			usrat_writ_cmd(0x15);   
			usart_writ_date(0x06);
			key_biao = 0;
		}
		else if(kwy_num == 3&& key_biao ==1)//3,判断是否连接，返回14
		{
			usrat_writ_cmd(0x30); 
			key_biao = 0;
		}
		else if(kwy_num == 4&& key_biao ==1)//4,初始化磁盘，返回14
		{
			usrat_writ_cmd(0x31); 
			key_biao = 0;
		}
		else if(kwy_num == 5&& key_biao ==1)//5,打开根目录的文件，返回14
		{
			usrat_writ_cmd(0x2F); 
			usart_writ_date(0x2F);// "/"
			usart_writ_date(0x31);// "1"
			usart_writ_date(0x2E);// "."
			usart_writ_date(0x54);// "T"
			usart_writ_date(0x58);// "x"
			usart_writ_date(0x54);// "T"
			usart_writ_date(0x00);// "O结尾
			usrat_writ_cmd(0x32);
			key_biao = 0;
		}
		else if(kwy_num == 6&& key_biao ==1)//6,发送读取数据命令，返回1D
		{
			usrat_writ_cmd(0x3A); 
			key_biao = 0;
		}
		else if(kwy_num == 7&& key_biao ==1)//7,读取数据，返回数据内容
		{
			usrat_writ_cmd(0x27); 
			key_biao = 0;
		}

		
		if(USART_RX_CNT)   //这里用来在LCD显示返回数据的内容
		{
			if(oldcount==USART_RX_CNT)//新周期内,没有收到任何数据,认为本次数据接收完成.
			{
			 
				oldcount=0;
				USART_RX_CNT=0;
				LCD_Clear(WHITE);
				if(kwy_num >= 7)
				{	//第7步进行完时，就获得1.TXT里的内容了，这里显示一下
					LCD_ShowString(30,40,200,16,16,USART_RX_BUF);
					
				}
				else{
				switch( USART_RX_BUF[0])//这里是显示每一步反馈回来的内容
					{
					case 0x14:LCD_ShowString(30,40,200,16,16,"0x14");break;
					case 0xAA:LCD_ShowString(30,40,200,16,16,"begin ok");break;
					case 0x15:LCD_ShowString(30,40,200,16,16,"0x15");break;
					case 0x51:LCD_ShowString(30,40,200,16,16,"0x51");break;
					case 0x1D:LCD_ShowString(30,40,200,16,16,"0x1D");break;
				default:	
						LCD_ShowString(30,40,200,16,16,"no err");break;//如果反馈的不是想要的数据，显示错误
					}
					}
				
				USART_RX_STA=0;
				USART_RX_BUF[0] = 0;//用完数据后记得清零，
				
			}else oldcount=USART_RX_CNT;			
		}

		delay_ms(10);
 
	 
	}  
}


void usrat_writ_cmd(unsigned char cmd)//带有0x57,0xAB头的发送函数
{

		while((USART1->SR&0X40)==0);//循环发送,直到发送完毕
		USART1->DR = 0x57;
		while((USART1->SR&0X40)==0);//循环发送,直到发送完毕   
		USART1->DR = 0xAB;	
		while((USART1->SR&0X40)==0);//循环发送,直到发送完毕   
		USART1->DR = cmd;	
	    USART1->SR = ~(0x20);          //清除RXNE
}

void usart_writ_date(unsigned char cmd)//发送单个字节
{
		while((USART1->SR&0X40)==0);//循环发送,直到发送完毕   
		USART1->DR = cmd;	
	    USART1->SR = ~(0x20);          //清除RXNE

}

