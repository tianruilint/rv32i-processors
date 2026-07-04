module rv32i_core (
    input  logic clk,
    input  logic reset,
    input  logic [31:0] instr,
    input  logic [31:0] data_read_data,
    output logic [31:0] current_pc,
    output logic [31:0] data_write_data,
    output logic [31:0] data_addr,
    output logic data_write_en
);


logic [6:0]  opcode;
logic [2:0]  funct3;
logic [6:0]  funct7;
logic        reg_write_dec;
logic        alu_src;
logic        mem_write;
logic        result_src;
logic        branch;
logic [1:0]  imm_type;
logic [3:0]  alu_op;
logic        rf_we;
logic [4:0]  rs1_addr;
logic [4:0]  rs2_addr;
logic [4:0]  rd_addr;
logic [31:0] wb_data;
logic [31:0] rs1_data;
logic [31:0] rs2_data;
logic [31:0] imm;
logic [31:0] alu_b;
logic [31:0] alu_result;
logic        take_target;
logic [31:0] target_pc;
logic        branch_taken;

assign opcode = instr[6:0];
assign funct3 = instr[14:12];
assign funct7 = instr[31:25];
assign rf_we = (reset) ? 1'b0 : reg_write_dec;
assign rs1_addr = instr[19:15];
assign rs2_addr = instr[24:20];
assign rd_addr = instr[11:7];
assign alu_b = (alu_src) ? imm : rs2_data;
assign wb_data = (result_src) ? data_read_data : alu_result;
assign data_addr = alu_result;
assign data_write_data = rs2_data;
assign data_write_en = (reset) ? 1'b0 : mem_write;
assign branch_taken = branch && (rs1_data == rs2_data);
assign take_target = branch_taken;
assign target_pc = current_pc + imm;

pc u_pc (
    .clk        (clk),
    .reset      (reset),
    .take_target(take_target),
    .target_pc  (target_pc),
    .current_pc (current_pc)
);

decoder u_decoder (
    .opcode     (opcode),
    .funct3     (funct3),
    .funct7     (funct7),
    .reg_write  (reg_write_dec),
    .alu_src    (alu_src),
    .mem_write  (mem_write),
    .result_src (result_src),
    .branch     (branch),
    .imm_type   (imm_type),
    .alu_op     (alu_op)
);

register_file u_register_file (
    .clk        (clk),
    .reg_write  (rf_we),
    .rs1_addr   (rs1_addr),
    .rs2_addr   (rs2_addr),
    .rd_addr    (rd_addr),
    .rd_data    (wb_data),
    .rs1_data   (rs1_data),
    .rs2_data   (rs2_data)
);

immediate_generator u_immediate_generator (
    .instr      (instr),
    .imm_type   (imm_type),
    .imm        (imm)
);

alu u_alu (
    .a          (rs1_data),
    .b          (alu_b),
    .alu_op     (alu_op),
    .result     (alu_result)
);


endmodule
