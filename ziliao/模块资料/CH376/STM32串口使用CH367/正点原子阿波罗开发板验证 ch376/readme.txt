实验器材:
	阿波罗STM32F429开发板
	
实验目的:
	学习STM32串口驱动CH376
	
硬件资源:
	1,沁恒官方验证版
	2,串口1(波特率:115200,PA9/PA10连接在板载USB转串口芯片CH340上面)  
	3,ALIENTEK 2.8/3.5/4.3/7寸LCD模块(包括MCU屏和RGB屏,都支持) 
	4,按键KEY0(PH3)/KEY1(PH2)/KEY2(PC13)/KEY_UP(PA0,也称之为WK_UP)
	
	
实验现象:
	本实验开机的时候先显示提示信息，然后等待串口输入接收APP程序（无校验，一次性接收），在串口接收
	到APP程序之后，即可执行IAP。如果是SRAM APP，通过按下KEY0即可执行这个收到的SRAM APP程序。如果
	是FLASH APP，则需要先按下KEY_UP按键，将串口接收到的APP程序存放到STM32的FLASH，之后再按KEY2即
	可以执行这个FLASH APP程序。通过KEY1按键，可以手动清除串口接收到的APP程序。
	
注意事项:
	stm32 io口是3.3V，与CH376连接时调到3.3V模式
	 

