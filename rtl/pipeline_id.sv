module pipeline_id (
    input  logic        clk,
    input  logic        reset,

    input  logic        if_id_valid,
    input  logic [31:0] if_id_pc,
    input  logic [31:0] if_id_instr,
    input  logic [31:0] if_id_pc_plus_4,

    input  logic        wb_valid,
    input  logic        wb_reg_write,
    input  logic [4:0]  wb_rd_addr,
    input  logic [31:0] wb_data,

    output logic        out_valid,
    output logic [31:0] out_pc,
    output logic [31:0] out_pc_plus_4,

    output logic [4:0]  out_rs1_addr,
    output logic [4:0]  out_rs2_addr,
    output logic [4:0]  out_rd_addr,

    output logic [31:0] out_rs1_data,
    output logic [31:0] out_rs2_data,
    output logic [31:0] out_imm,
    output logic [2:0]  out_funct3,

    output logic [3:0]  out_alu_op,
    output logic        out_alu_src,
    output logic        out_alu_a_pc,
    output logic [1:0]  out_result_src,

    output logic        out_reg_write,
    output logic        out_mem_write,
    output logic        out_branch,
    output logic [2:0]  out_branch_type,
    output logic [1:0]  out_jump_type,

    output logic        out_uses_rs1,
    output logic        out_uses_rs2
);

logic [6:0] opcode;
logic [2:0] funct3;
logic [6:0] funct7;
logic [4:0] rs1_addr;
logic [4:0] rs2_addr;
logic [4:0] rd_addr;

logic       dec_reg_write;
logic       dec_alu_src;
logic       dec_mem_write;
logic [1:0] dec_result_src;
logic       dec_branch;
logic [2:0] dec_imm_type;
logic [3:0] dec_alu_op;
logic [2:0] dec_branch_type;
logic       dec_alu_a_pc;
logic [1:0] dec_jump_type;

logic [31:0] dec_imm;

logic [31:0] rf_rs1_data;
logic [31:0] rf_rs2_data;
logic        rf_write_en;

logic [31:0] id_rs1_data;
logic [31:0] id_rs2_data;

logic id_uses_rs1;
logic id_uses_rs2;

localparam logic [6:0] R_TYPE = 7'b0110011;
localparam logic [6:0] I_TYPE = 7'b0010011;
localparam logic [6:0] LW     = 7'b0000011;
localparam logic [6:0] SW     = 7'b0100011;
localparam logic [6:0] BRANCH = 7'b1100011;
localparam logic [6:0] JALR   = 7'b1100111;

assign opcode  = if_id_instr[6:0];
assign funct3  = if_id_instr[14:12];
assign funct7  = if_id_instr[31:25];
assign rs1_addr = if_id_instr[19:15];
assign rs2_addr = if_id_instr[24:20];
assign rd_addr  = if_id_instr[11:7];

assign rf_write_en = !reset && wb_valid && wb_reg_write;

always_comb begin
    id_rs1_data = rf_rs1_data;
    id_rs2_data = rf_rs2_data;

    if (wb_valid && wb_reg_write && wb_rd_addr != 5'd0 && wb_rd_addr == rs1_addr) begin
        id_rs1_data = wb_data;
    end

    if (wb_valid && wb_reg_write && wb_rd_addr != 5'd0 && wb_rd_addr == rs2_addr) begin
        id_rs2_data = wb_data;
    end
end

always_comb begin
    id_uses_rs1 = 1'b0;
    id_uses_rs2 = 1'b0;

    case (opcode)
        R_TYPE: begin
            id_uses_rs1 = 1'b1;
            id_uses_rs2 = 1'b1;
        end

        I_TYPE: begin
            id_uses_rs1 = 1'b1;
        end

        LW: begin
            id_uses_rs1 = 1'b1;
        end

        SW: begin
            id_uses_rs1 = 1'b1;
            id_uses_rs2 = 1'b1;
        end

        BRANCH: begin
            id_uses_rs1 = 1'b1;
            id_uses_rs2 = 1'b1;
        end

        JALR: begin
            id_uses_rs1 = 1'b1;
        end

        default: begin
        end
    endcase
end

always_comb begin
    out_valid      = 1'b0;
    out_pc         = 32'b0;
    out_pc_plus_4  = 32'b0;

    out_rs1_addr   = 5'b0;
    out_rs2_addr   = 5'b0;
    out_rd_addr    = 5'b0;

    out_rs1_data   = 32'b0;
    out_rs2_data   = 32'b0;
    out_imm        = 32'b0;
    out_funct3     = 3'b0;

    out_alu_op     = 4'b0;
    out_alu_src    = 1'b0;
    out_alu_a_pc   = 1'b0;
    out_result_src = 2'b0;

    out_reg_write  = 1'b0;
    out_mem_write  = 1'b0;
    out_branch     = 1'b0;
    out_branch_type = 3'b0;
    out_jump_type  = 2'b0;

    out_uses_rs1   = 1'b0;
    out_uses_rs2   = 1'b0;

    if (if_id_valid) begin
        out_valid       = 1'b1;
        out_pc          = if_id_pc;
        out_pc_plus_4   = if_id_pc_plus_4;

        out_rs1_addr    = rs1_addr;
        out_rs2_addr    = rs2_addr;
        out_rd_addr     = rd_addr;

        out_rs1_data    = id_rs1_data;
        out_rs2_data    = id_rs2_data;
        out_imm         = dec_imm;
        out_funct3      = funct3;

        out_alu_op      = dec_alu_op;
        out_alu_src     = dec_alu_src;
        out_alu_a_pc    = dec_alu_a_pc;
        out_result_src  = dec_result_src;

        out_reg_write   = dec_reg_write;
        out_mem_write   = dec_mem_write;
        out_branch      = dec_branch;
        out_branch_type = dec_branch_type;
        out_jump_type   = dec_jump_type;

        out_uses_rs1    = id_uses_rs1;
        out_uses_rs2    = id_uses_rs2;
    end
end

decoder u_decoder (
    .opcode      (opcode),
    .funct3      (funct3),
    .funct7      (funct7),

    .reg_write   (dec_reg_write),
    .alu_src     (dec_alu_src),
    .mem_write   (dec_mem_write),
    .result_src  (dec_result_src),
    .branch      (dec_branch),
    .imm_type    (dec_imm_type),
    .alu_op      (dec_alu_op),
    .branch_type (dec_branch_type),
    .alu_a_pc    (dec_alu_a_pc),
    .jump_type   (dec_jump_type)
);

immediate_generator u_immediate_generator (
    .instr    (if_id_instr),
    .imm_type (dec_imm_type),
    .imm      (dec_imm)
);

register_file u_register_file (
    .clk        (clk),
    .reg_write  (rf_write_en),
    .rs1_addr   (rs1_addr),
    .rs2_addr   (rs2_addr),
    .rd_addr    (wb_rd_addr),
    .rd_data    (wb_data),
    .rs1_data   (rf_rs1_data),
    .rs2_data   (rf_rs2_data)
);

endmodule
