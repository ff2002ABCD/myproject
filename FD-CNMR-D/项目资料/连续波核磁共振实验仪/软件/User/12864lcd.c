#include "main.h"

void Lcd_Init()
{
	GPIO_InitTypeDef GPIO_InitStructure;//定义结构体变量
	
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB|RCC_APB2Periph_AFIO,ENABLE);
	GPIO_PinRemapConfig(GPIO_Remap_SWJ_JTAGDisable, ENABLE);// 改变指定管脚的映射 GPIO_Remap_SWJ_JTAGDisable ，JTAG-DP 禁用 + SW-DP 使能
	
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_4|GPIO_Pin_5|GPIO_Pin_6|GPIO_Pin_7;  //选择你要设置的IO口
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_Out_PP;	 //设置推挽输出模式
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;	  //设置传输速率
	GPIO_Init(GPIOB,&GPIO_InitStructure); 	   /* 初始化GPIO */
	
	delay_ms(10);
	LCD_RST = 0;
	delay_ms(10);
	LCD_RST = 1;
	delay_ms(50);
	send_command(0x30);
	send_command(0x02);
	send_command(0x06);
	send_command(0x0c);
	send_command(0x01);//清屏
	delay_ms(5);
	send_command(0x80);	
	
	delay_ms(50);
	Lcd_Display(0x80,"----------------",16);
	Lcd_Display(0x92,"欢迎使用",8);
	Lcd_Display(0x88,"复旦天欣教学仪器",16);
	Lcd_Display(0x98,"----------------",16);
	
}
//写命令
void send_command(u8 c_data){
	u8 i,i_data;
	
	i_data = 0xf8;
	LCD_CS = 1;
	LCD_SCLK = 0;
	for(i = 0;i < 8;i++){
		LCD_SCLK = 0;
		if(i_data & 0x80){
			LCD_STD = 1;
		}else{
			LCD_STD = 0;
		}	
		LCD_SCLK = 1;
		i_data = i_data << 1;
	}
	
	i_data = c_data;
	i_data &= 0xf0;
	for(i = 0;i < 8;i++){
		LCD_SCLK = 0;
		if(i_data & 0x80){
			LCD_STD = 1;
		}else{
			LCD_STD = 0;
		}	
		LCD_SCLK = 1;
		i_data = i_data << 1;
	}
	
	i_data = c_data;
	i_data <<= 4;
	for(i = 0;i < 8;i++){
		LCD_SCLK = 0;
		if(i_data & 0x80){
			LCD_STD = 1;
		}else{
			LCD_STD = 0;
		}	
		LCD_SCLK = 1;
		i_data = i_data << 1;
	}
	
	LCD_CS = 0;
	delay_us(100);
}
//写数据
void send_data(u8 c_data){
	u8 i,i_data;
	
	i_data = 0xfa;
	LCD_CS = 1;
	LCD_SCLK = 0;
	for(i = 0;i < 8;i++){
		LCD_SCLK = 0;
		if(i_data & 0x80){
			LCD_STD = 1;
		}else{
			LCD_STD = 0;
		}	
		LCD_SCLK = 1;
		i_data = i_data << 1;
	}
	
	i_data = c_data;
	i_data &= 0xf0;
	for(i = 0;i < 8;i++){
		LCD_SCLK = 0;
		if(i_data & 0x80){
			LCD_STD = 1;
		}else{
			LCD_STD = 0;
		}	
		LCD_SCLK = 1;
		i_data = i_data << 1;
	}
	
	i_data = c_data;
	i_data <<= 4;
	for(i = 0;i < 8;i++){
		LCD_SCLK = 0;
		if(i_data & 0x80){
			LCD_STD = 1;
		}else{
			LCD_STD = 0;
		}	
		LCD_SCLK = 1;
		i_data = i_data << 1;
	}
	
	LCD_CS = 0;
	delay_us(100);
}

//显示
void Lcd_Display(u8 wzh,char a[],u8 i){
	send_command(wzh);
	u8 b;
	for(b = 0;b < i;b++){
		send_data(a[b]);
	}
}

u8 const Lcd_Con_X_Y[4][2]={{0x80,0x80},{0x80,0x90},{0x88,0x80},{0x88,0x90}};

void Disp_black(void){	//清除绘图区域
	u8 i,j;
	send_command(0x34);
	send_command(0x34);
	for(i=0;i<16;i++){
    for(j=0;j<32;j++) {                    
			send_command(128+j);
			send_command(128+i);
			send_data(0x00);
			send_data(0x00);
    }
	}
	send_command(0x30); 
}


//反白，取消反白一行
void Lcd_Inverse(u8 line,u8 enable){
	u8 i,j;
	send_command(0x34);
	send_command(0x34);
  for(j=0;j<16;j++)                                      
  {
    for(i=0;i<8;i++)                                 
    {                    
			send_command(Lcd_Con_X_Y[line][1]+j);
			send_command(Lcd_Con_X_Y[line][0]+i);
			if(enable==1)                                 
			{
				send_data(0xff);
				send_data(0xff);
			}
			else                                                
			{
				send_data(0x00);
				send_data(0x00);
			}
    }
  }
	send_command(0x36);
	send_command(0x30);       
}

//反白一个数字
void Lcd_Inverse_Number(u8 x,u8 y){
	u8 i,j;
	send_command(0x34);
	send_command(0x34);
	j = x % 2;
	for(i=0;i<16;i++)                                 
	{                  
		send_command(Lcd_Con_X_Y[y][1]+i);
		send_command(Lcd_Con_X_Y[y][0]+(x/2));
		if(j==0)                                 
		{
			send_data(0xff);
			send_data(0x00);
		}
		else                                                
		{
			send_data(0x00);
			send_data(0xff);
		}
	}
	send_command(0x36);
	send_command(0x30);  
}

//反白多个数字 x 0-15,y 0-3
void Lcd_Inverse_xNumber(u8 x1,u8 x2,u8 y){
	send_command(0x34);
	send_command(0x34);
	u8 i,j,j1,j2;
	j1 = x1 % 2;
	j2 = x2 % 2;
	for(i=0;i<16;i++)                                 
	{
		for(j=x1/2;j<(x2/2)+1;j++)
		{                   
			send_command(Lcd_Con_X_Y[y][1]+i);
			send_command(Lcd_Con_X_Y[y][0]+j);
			if(j==x1/2 && j1==1)                                 
			{
				send_data(0x00);
				send_data(0xff);
			}
			else if(j==x2/2 && j2==0)                                 
			{
				send_data(0xff);
				send_data(0x00);
			}
			else                                                
			{
				send_data(0xff);
				send_data(0xff);
			}
		}
	}
	send_command(0x36);
	send_command(0x30); 
}

