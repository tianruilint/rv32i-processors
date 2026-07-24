module pipeline_id_ex (
    input  logic        clk,
    input  logic        reset,
    input  logic        flush,
    input  logic        bubble,

    input  logic        in_valid,
    input  logic [31:0] in_pc,
    input  logic [31:0] in_pc_plus_4,
    input  logic [4:0]  in_rs1_addr,
    input  logic [4:0]  in_rs2_addr,
    input  logic [4:0]  in_rd_addr,
    input  logic [31:0] in_rs1_data,
    input  logic [31:0] in_rs2_data,
    input  logic [31:0] in_imm,
    input  logic [2:0]  in_funct3,
    input  logic [3:0]  in_alu_op,
    input  logic        in_alu_src,
    input  logic        in_alu_a_pc,
    input  logic [1:0]  in_result_src,
    input  logic        in_reg_write,
    input  logic        in_mem_write,
    input  logic        in_branch,
    input  logic [2:0]  in_branch_type,
    input  logic [1:0]  in_jump_type,
    input  logic        in_uses_rs1,
    input  logic        in_uses_rs2,

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

    always_ff @(posedge clk) begin
        if (reset || flush || bubble || !in_valid) begin
            out_valid       <= 1'b0;
            out_pc          <= 32'b0;
            out_pc_plus_4   <= 32'b0;
            out_rs1_addr    <= 5'b0;
            out_rs2_addr    <= 5'b0;
            out_rd_addr     <= 5'b0;
            out_rs1_data    <= 32'b0;
            out_rs2_data    <= 32'b0;
            out_imm         <= 32'b0;
            out_funct3      <= 3'b0;
            out_alu_op      <= 4'b0;
            out_alu_src     <= 1'b0;
            out_alu_a_pc    <= 1'b0;
            out_result_src  <= 2'b0;
            out_reg_write   <= 1'b0;
            out_mem_write   <= 1'b0;
            out_branch      <= 1'b0;
            out_branch_type <= 3'b0;
            out_jump_type   <= 2'b0;
            out_uses_rs1    <= 1'b0;
            out_uses_rs2    <= 1'b0;
        end
        else begin
            out_valid       <= in_valid;
            out_pc          <= in_pc;
            out_pc_plus_4   <= in_pc_plus_4;
            out_rs1_addr    <= in_rs1_addr;
            out_rs2_addr    <= in_rs2_addr;
            out_rd_addr     <= in_rd_addr;
            out_rs1_data    <= in_rs1_data;
            out_rs2_data    <= in_rs2_data;
            out_imm         <= in_imm;
            out_funct3      <= in_funct3;
            out_alu_op      <= in_alu_op;
            out_alu_src     <= in_alu_src;
            out_alu_a_pc    <= in_alu_a_pc;
            out_result_src  <= in_result_src;
            out_reg_write   <= in_reg_write;
            out_mem_write   <= in_mem_write;
            out_branch      <= in_branch;
            out_branch_type <= in_branch_type;
            out_jump_type   <= in_jump_type;
            out_uses_rs1    <= in_uses_rs1;
            out_uses_rs2    <= in_uses_rs2;
        end
    end

endmodule

