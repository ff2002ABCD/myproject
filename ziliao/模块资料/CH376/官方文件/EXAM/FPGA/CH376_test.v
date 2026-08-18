///////////////////////////////////////////////////////////////////////
//测试平台：ALTERA Cyclone EP1C12Q240C6
//晶振频率：12MHz
//测试芯片：CH376S
//完成日期：2013/10/01
//实现功能：
//（1）  使用FPGA的硬件描述语言控制CH376S操作USB存储设备（U盘、SD卡）
//（2）  使用芯片的并行接口，控制CH376完成初始化（参考CH376手册）
//（3）  控制USB存储设备实现简单的文件创建、文件的写入、文件关闭等功能。
///////////////////////////////////////////////////////////////////////
module	test376(
			pin_a0,				//引脚CH376_A0
			pin_data,			//引脚CH376_D0-D7
			pin_wr,				//引脚CH376_WR#
			pin_rd,				//引脚CH376_RD#
			pin_cs,				//引脚CH376_PCS#，如只是单一芯片可以直接接地；如需片选可根据实际情况接译码器
			pin_int,			//引脚CH376_INT#
			pin_clk,			//FPGA晶振12MHz
			pin_rst,			//FPGA复位键
			pin_led				//FPGA指示灯，用于检测状态
			);

//--------port-----------------
output			pin_a0;
inout	[7:0]	pin_data;
output			pin_wr;
output			pin_rd;
output			pin_cs;
input			pin_int;
input			pin_clk;
input			pin_rst;
output	[3:0]	pin_led;

//------output type-----------
reg		[7:0]	reg_tx;
reg				reg_a0;
reg				reg_wr;
reg				reg_rd;
reg				reg_cs;

reg				reg_oe;

assign	pin_data	=	reg_oe?reg_tx:8'hzz;
assign	pin_a0		=	reg_a0;
assign	pin_wr		=	reg_wr;													//引脚分配时，尽量使用较小电流，如4mA
assign	pin_rd		=	reg_rd;													//引脚分配时，尽量使用较小电流，如4mA
assign	pin_cs		=	reg_cs;

//----------------syn-----------
reg		[7:0]	reg_rst_timer;

always	@(posedge pin_clk or negedge pin_rst) begin
	if(!pin_rst)				reg_rst_timer<=8'h80;
	else if(reg_rst_timer[7])	reg_rst_timer<=reg_rst_timer+8'h01;
end
wire	wire_rst	=	reg_rst_timer[7];

reg		reg_div2;
reg		reg_div4;
reg		reg_div8;
reg		reg_div16;
reg		reg_div32;
reg		reg_div64;
reg		reg_div128;

always	@(posedge pin_clk or posedge wire_rst) begin
	if(wire_rst)	reg_div2<=1'b0;
	else			reg_div2<=!reg_div2;
end
always	@(posedge reg_div2 or posedge wire_rst) begin
	if(wire_rst)	reg_div4<=1'b0;
	else			reg_div4<=!reg_div4;
end
always	@(posedge reg_div4 or posedge wire_rst) begin
	if(wire_rst)	reg_div8<=1'b0;
	else			reg_div8<=!reg_div8;
end
always	@(posedge reg_div8 or posedge wire_rst) begin
	if(wire_rst)	reg_div16<=1'b0;
	else			reg_div16<=!reg_div16;
end
always	@(posedge reg_div16 or posedge wire_rst) begin
	if(wire_rst)	reg_div32<=1'b0;
	else			reg_div32<=!reg_div32;
end
always	@(posedge reg_div32 or posedge wire_rst) begin
	if(wire_rst)	reg_div64<=1'b0;
	else			reg_div64<=!reg_div64;
end
always	@(posedge reg_div64 or posedge wire_rst) begin
	if(wire_rst)	reg_div128<=1'b0;
	else			reg_div128<=!reg_div128;
end

reg		reg_clk;

always	@(negedge reg_div2 or posedge wire_rst) begin
	if(wire_rst)			reg_clk<=1'b0;
	else					reg_clk<=reg_div128;
end

wire	wire_clk	=	reg_clk;

reg		[19:0]	reg_ini_wait;
reg					reg_wait;

always	@(posedge reg_div2 or posedge wire_rst) begin
	if(wire_rst)				reg_ini_wait<=20'h80000;
	else if(reg_wait)			reg_ini_wait<=20'h80000;
	else if(reg_ini_wait[19])	reg_ini_wait<=reg_ini_wait+20'h00001;
end
//****************************
reg		reg_int0;
reg		reg_int1;

always	@(posedge wire_clk) begin
	reg_int0<=!pin_int;
end
always	@(posedge wire_clk) begin
	reg_int1<=reg_int0;
end

//****************************
reg		reg_op1;
reg		reg_op2;
reg		reg_op3;
reg		reg_op4;
//reg_op4=1: clk上升沿，更新输出数据reg_tx、控制信号reg_a0、三态控制reg_oe；clk下降沿，更新状态reg_state、reg_i
//reg_op1=1: clk上升沿，更新读写信号reg_wr、reg_rd
//reg_op2=1: clk上升沿，上拉reg_wr和reg_rd为默认值1
//reg_op3=1：clk上升沿，更新读回的中断状态reg_err和等待中断信号reg_inc
always	@(posedge wire_clk or posedge wire_rst) begin							
	if(wire_rst)	{reg_op4,reg_op3,reg_op2,reg_op1}<=4'b0000;
	else			{reg_op4,reg_op3,reg_op2,reg_op1}<={reg_op3,reg_op2,reg_op1,!reg_op3&!reg_op2&!reg_op1};
end
//-------------Internal Constant-------------
parameter	WR_IDLE			=	4'b0000;
parameter	WR_CHK1			=	4'b0001;
parameter	SET_USB_MODE	=	4'b0010;
parameter	DISK_CONNECT	=	4'b0011;
parameter	DISK_MOUNT		=	4'b0100;
parameter	CREATE_FILE		=	4'b0101;
parameter	BYTE_WRITE		=	4'b0110;
parameter	WR_REQ_DATA		=	4'b0111;
parameter	BYTE_WR_GO		=	4'b1000;
parameter	CLOSE_FILE		=	4'b1010;
parameter	DISK_DISCONNECT	=	4'b1011;
parameter	WAIT_DISCONNECT	=	4'b1100;

reg		[3:0]	reg_wr_state;
reg		[7:0]	reg_rx;
reg		[7:0]	reg_i;
reg		[7:0]	buffer;
reg		[15:0]	reg_data_cnt;
reg				reg_inc;
reg				reg_err;
reg				reg_go;
reg				reg_i_8;


always	@(negedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	begin reg_wr_state<=WR_IDLE; reg_wait<=1'b0;end
	else if(reg_op4) begin
		case(reg_wr_state)
			WR_IDLE:if(!reg_ini_wait[19])	reg_wr_state<=WR_CHK1;
			WR_CHK1:case(reg_i)
						8'h02:if(!reg_err)	reg_wr_state<=SET_USB_MODE;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h03:if(!reg_err)	reg_wr_state<=DISK_CONNECT;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h03:if(!reg_err)	reg_wr_state<=DISK_MOUNT;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h03:if(!reg_err)	reg_wr_state<=CREATE_FILE;
					endcase
			CREATE_FILE:case(reg_i)
						8'h0d:if(!reg_err)	reg_wr_state<=BYTE_WRITE;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h05:if(!reg_err)	reg_wr_state<=WR_REQ_DATA;
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h000:begin end
						9'h001:if(reg_go)			reg_wr_state<=CLOSE_FILE;	//写入数据字节数为零时，此处返回零，只更新文件长度，关闭文件
						default:if(!reg_err)	reg_wr_state<=BYTE_WR_GO;
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h03:begin
							if(reg_go)			reg_wr_state<=WR_REQ_DATA;
							else if(!reg_err)	reg_wr_state<=CLOSE_FILE;
							else				reg_wr_state<=BYTE_WRITE;
						end
					endcase
			CLOSE_FILE:case(reg_i)
						8'h04:if(!reg_err)	reg_wr_state<=DISK_DISCONNECT;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h03:begin
							reg_wr_state<=WAIT_DISCONNECT;
							reg_wait<=1'b1;
						end
					endcase
			WAIT_DISCONNECT:begin
						reg_wait<=1'b0;
						
						if(!reg_ini_wait[19]) begin
							if(reg_err) reg_wr_state<=DISK_DISCONNECT;
							else			reg_wr_state<=DISK_CONNECT;
						end
						else reg_wr_state<=WAIT_DISCONNECT;
					end
		endcase
	end
end

always	@(negedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	reg_cs<=1'b1;
	else case(reg_wr_state)
			WR_CHK1:reg_cs<=1'b0;
		endcase
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	begin reg_tx<=8'h00; reg_data_cnt<=16'h0000;end
	else if(reg_op4) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h00:reg_tx<=8'h06;									//CMD_CHECK_EXIST		0x06	/* 测试工作状态 */
						8'h01:reg_tx<=8'h65;									//随机数
					endcase
			SET_USB_MODE:case(reg_i)
						8'h00:reg_tx<=8'h15;									//CMD_SET_USB_MODE		0x15	/* 设置USB工作模式 */
						8'h02:reg_tx<=8'h06;									//00H=未启用的设备方式, 01H=已启用的设备方式并且使用外部固件模式(串口不支持), 02H=已启用的设备方式并且使用内置固件模式
																				//03H=SD卡主机模式/未启用的主机模式,用于管理和存取SD卡中的文件
																				//04H=未启用的主机方式, 05H=已启用的主机方式, 06H=已启用的主机方式并且自动产生SOF包, 07H=已启用的主机方式并且复位USB总线
					endcase
			DISK_CONNECT:case(reg_i)
						8'h00:reg_tx<=8'h30;									//CMD0H_DISK_CONNECT	0x30	/* 主机文件模式/不支持SD卡: 检查磁盘是否连接 */
						8'h02:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
			DISK_MOUNT:case(reg_i)
						8'h00:reg_tx<=8'h31;									//CMD0H_DISK_MOUNT		0x31	/* 主机文件模式: 初始化磁盘并测试磁盘是否就绪 */
						8'h02:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
			CREATE_FILE:case(reg_i)
						8'h00:reg_tx<=8'h2f;									//CMD10_SET_FILE_NAME	0x2F	/* 主机文件模式: 设置将要操作的文件的文件名 */
						8'h01:reg_tx<=8'h5c;									//ascii:'\'
						8'h02:reg_tx<=8'h57;									//ascii:'W'
						8'h03:reg_tx<=8'h43;									//ascii:'C'
						8'h04:reg_tx<=8'h48;									//ascii:'H'
						8'h05:reg_tx<=8'h2e;									//ascii:'.'
						8'h06:reg_tx<=8'h54;									//ascii:'T'
						8'h07:reg_tx<=8'h58;									//ascii:'X'
						8'h08:reg_tx<=8'h54;									//ascii:'T'
						8'h09:reg_tx<=8'h00;									//ascii:'NULL'
						8'h0a:reg_tx<=8'h34;									//CMD0H_FILE_CREATE		0x34	/* 主机文件模式: 新建文件,如果文件已经存在那么先删除 */
						8'h0c:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
			BYTE_WRITE:case(reg_i)
						8'h00:reg_tx<=8'h3c;									//CMD2H_BYTE_WRITE		0x3C	/* 主机文件模式: 以字节为单位向当前位置写入数据块 */
						8'h01:reg_tx<=8'h10;									//发送字节数，低8位
						8'h02:reg_tx<=8'h04;									//发送字节数，高8位	
						8'h04:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h000:reg_tx<=8'h2d;									//CMD01_WR_REQ_DATA		0x2D	/* 向内部指定缓冲区写入请求的数据块 */
						9'h001:begin end										//读CH376返回可写字节数
						default:begin 
							reg_data_cnt<=reg_data_cnt+16'h0001;				//计发送数据字节数
							reg_tx<=buffer;										//发送数据			
						end
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h00:reg_tx<=8'h3d;									//CMD0H_BYTE_WR_GO		0x3D	/* 主机文件模式: 继续字节写 */
						8'h02:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
			CLOSE_FILE:case(reg_i)
						8'h00:begin
							reg_tx<=8'h36;										//CMD1H_FILE_CLOSE		0x36	/* 主机文件模式: 关闭当前已经打开的文件或者目录(文件夹) */
							reg_data_cnt<=16'h0000;	
						end
						8'h01:reg_tx<=8'h01;									//00H=禁止更新长度, 01H=允许更新长度
						8'h03:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h00:reg_tx<=8'h30;									//CMD0H_DISK_CONNECT	0x30	/* 主机文件模式/不支持SD卡: 检查磁盘是否连接 */
						8'h02:reg_tx<=8'h22;									//CMD01_GET_STATUS		0x22	/* 获取中断状态并取消中断请求 */
					endcase
		endcase
	end
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	reg_wr<=1'b1;
	else if(reg_op2) reg_wr<=1'b1;												//默认wr为1
	else if(reg_op1) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h01:reg_wr<=1'b0;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
					endcase
			CREATE_FILE:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h01:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
						8'h03:reg_wr<=1'b0;
						8'h04:reg_wr<=1'b0;
						8'h05:reg_wr<=1'b0;
						8'h06:reg_wr<=1'b0;
						8'h07:reg_wr<=1'b0;
						8'h08:reg_wr<=1'b0;
						8'h09:reg_wr<=1'b0;
						8'h0a:reg_wr<=1'b0;
						8'h0c:reg_wr<=1'b0;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h01:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
						8'h04:reg_wr<=1'b0;
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h001:begin end
						default:reg_wr<=1'b0;
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
					endcase
			CLOSE_FILE:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h01:reg_wr<=1'b0;
						8'h03:reg_wr<=1'b0;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h00:reg_wr<=1'b0;
						8'h02:reg_wr<=1'b0;
					endcase
		endcase
	end
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)		reg_oe<=1'b0;
	else if(reg_op4) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h01:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			CREATE_FILE:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h01:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						8'h03:reg_oe<=1'b1;
						8'h04:reg_oe<=1'b1;
						8'h05:reg_oe<=1'b1;
						8'h06:reg_oe<=1'b1;
						8'h07:reg_oe<=1'b1;
						8'h08:reg_oe<=1'b1;
						8'h09:reg_oe<=1'b1;
						8'h0a:reg_oe<=1'b1;
						8'h0c:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h01:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						8'h04:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h001:reg_oe<=1'b0;
						default:reg_oe<=1'b1;
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			CLOSE_FILE:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h01:reg_oe<=1'b1;
						8'h03:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h00:reg_oe<=1'b1;
						8'h02:reg_oe<=1'b1;
						default:reg_oe<=1'b0;
					endcase
		endcase
	end
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	reg_rd<=1'b1;
	else if(reg_op2) reg_rd<=1'b1;												//默认rd为1
	else if(reg_op1) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h02:reg_rd<=1'b0;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h03:reg_rd<=1'b0;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h03:reg_rd<=1'b0;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h03:reg_rd<=1'b0;
					endcase
			CREATE_FILE:case(reg_i)
						8'h0d:reg_rd<=1'b0;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h05:reg_rd<=1'b0;
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h001:reg_rd<=1'b0;
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h03:reg_rd<=1'b0;
					endcase
			CLOSE_FILE:case(reg_i)
						8'h04:reg_rd<=1'b0;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h03:reg_rd<=1'b0;
					endcase
		endcase
	end
end

always	@(posedge reg_rd or posedge wire_rst) begin
	if(wire_rst)	reg_rx<=8'h00;
	else			reg_rx<=pin_data;
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	reg_err<=1'b0;
	else if(reg_op3) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h02:reg_err<=!(reg_rx==8'h9a);						//随机数取反
					endcase
			SET_USB_MODE:case(reg_i)
						8'h03:reg_err<=!(reg_rx==8'h51);						//51H:CMD_RET_SUCCESS
					endcase
			DISK_CONNECT:case(reg_i)
						8'h03:reg_err<=!(reg_rx==8'h14);						//中断状态，USB_INT_SUCCESS		0x14	/* USB事务或者传输操作成功 */
					endcase
			DISK_MOUNT:case(reg_i)
						8'h03:reg_err<=!(reg_rx==8'h14);						//中断状态，USB_INT_SUCCESS		0x14	/* USB事务或者传输操作成功 */
					endcase
			CREATE_FILE:case(reg_i)
						8'h0d:reg_err<=!(reg_rx==8'h14);						//中断状态，USB_INT_SUCCESS		0x14	/* USB事务或者传输操作成功 */
					endcase
			BYTE_WRITE:case(reg_i)
						8'h05:reg_err<=!(reg_rx==8'h1e);						//中断状态，USB_INT_DISK_WRITE	0x1E	/* USB存储器请求数据写入 */
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h000:begin end
						9'h001:reg_go<=(reg_rx==8'h00);							//CH376返回可写字节数为零
						default:reg_err<=!({reg_i_8,reg_i}==({1'b0,reg_rx}+9'h001));	//计数至CH376返回可写字节数
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h03:begin
							reg_err<=!(reg_rx==8'h14);							//中断状态，USB_INT_SUCCESS		0x14	/* USB事务或者传输操作成功 */
							reg_go<=(reg_rx==8'h1e);	
						end
					endcase
			CLOSE_FILE:case(reg_i)
						8'h04:reg_err<=!(reg_rx==8'h14);						//中断状态，USB_INT_SUCCESS		0x14	/* USB事务或者传输操作成功 */
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h03:reg_err<=(reg_rx==8'h14);							//中断状态，USB_INT_SUCCESS		0x14	/* USB事务或者传输操作成功 */
					endcase
		endcase
	end
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	reg_a0<=1'b0;
	else if(reg_op4) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h01:reg_a0<=1'b0;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h01:reg_a0<=1'b0;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h03:reg_a0<=1'b0;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h03:reg_a0<=1'b0;
					endcase
			CREATE_FILE:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h01:reg_a0<=1'b0;
						8'h0a:reg_a0<=1'b1;
						8'h0d:reg_a0<=1'b0;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h01:reg_a0<=1'b0;
						8'h03:reg_a0<=1'b1;
						8'h05:reg_a0<=1'b0;
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h000:reg_a0<=1'b1;
						9'h001:reg_a0<=1'b0;
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h03:reg_a0<=1'b0;
					endcase
			CLOSE_FILE:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h01:reg_a0<=1'b0;
						8'h02:reg_a0<=1'b1;
						8'h04:reg_a0<=1'b0;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h00:reg_a0<=1'b1;
						8'h03:reg_a0<=1'b0;
					endcase
		endcase
	end
end

always	@(posedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	reg_inc<=1'b0;												//reg_inc=0，等待中断int到来；reg_inc=1，无需等待中断
	else if(reg_op3) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h00:reg_inc<=1'b1;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h00:reg_inc<=1'b1;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h01:reg_inc<=1'b0;
						8'h02:reg_inc<=1'b1;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h01:reg_inc<=1'b0;
						8'h02:reg_inc<=1'b1;
					endcase
			CREATE_FILE:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h0b:reg_inc<=1'b0;
						8'h0c:reg_inc<=1'b1;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h03:reg_inc<=1'b0;
						8'h04:reg_inc<=1'b1;
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h01:reg_inc<=1'b0;
						8'h02:reg_inc<=1'b1;
					endcase
			CLOSE_FILE:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h02:reg_inc<=1'b0;
						8'h03:reg_inc<=1'b1;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h00:reg_inc<=1'b1;
						8'h01:reg_inc<=1'b0;
						8'h02:reg_inc<=1'b1;
					endcase
		endcase
	end
end

always	@(negedge wire_clk or posedge wire_rst) begin
	if(wire_rst)	begin reg_i<=8'h00;reg_i_8<=1'b0;end
	else if(reg_op4) begin
		case(reg_wr_state)
			WR_CHK1:case(reg_i)
						8'h02:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			SET_USB_MODE:case(reg_i)
						8'h03:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			DISK_CONNECT:case(reg_i)
						8'h03:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			DISK_MOUNT:case(reg_i)
						8'h03:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			CREATE_FILE:case(reg_i)
						8'h0d:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			BYTE_WRITE:case(reg_i)
						8'h05:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			WR_REQ_DATA:case({reg_i_8,reg_i})
						9'h000:reg_i<=reg_i+8'h01;
						9'h001:begin 
							if(reg_go) begin
								reg_i<=8'h00; 
								reg_i_8<=1'b0;
							end
							else 
								reg_i<=reg_i+8'h01;
						end
						9'h0ff:begin 
								reg_i<=8'h00;
								reg_i_8<=1'b1;
						end
						default:begin
							if(!reg_err) begin 
								reg_i<=8'h00;
								reg_i_8<=1'b0;
							end
							else 
								reg_i<=reg_i+8'h01;
						end
					endcase
			BYTE_WR_GO:case(reg_i)
						8'h03:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			CLOSE_FILE:case(reg_i)
						8'h04:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
			DISK_DISCONNECT:case(reg_i)
						8'h03:reg_i<=8'h00;
						default:if(reg_inc|reg_int1) reg_i<=reg_i+8'h01;
					endcase
		endcase
	end
end

always @(reg_data_cnt) begin													//此处最多写入65535个字节
	case(reg_data_cnt)
		16'h0040:buffer=8'h0d;
		16'h0081:buffer=8'h0d;
		16'h00c2:buffer=8'h0d;
		16'h0103:buffer=8'h0d;
		16'h0144:buffer=8'h0d;
		16'h0185:buffer=8'h0d;
		16'h01c6:buffer=8'h0d;
		16'h0207:buffer=8'h0d;
		16'h0248:buffer=8'h0d;
		16'h0289:buffer=8'h0d;
		16'h02ca:buffer=8'h0d;
		16'h030b:buffer=8'h0d;
		16'h034c:buffer=8'h0d;
		16'h038d:buffer=8'h0d;
		16'h03ce:buffer=8'h0d;
		16'h040f:buffer=8'h0d;													//ascii：换行符
		default:buffer=8'h31;													//ascii：'1'
	endcase
end

//****************************
assign	pin_led	=	reg_wr_state;
//****************************

endmodule
