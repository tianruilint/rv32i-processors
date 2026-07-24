module pipeline_ex_mem (
    input  logic        clk,
    input  logic        reset,

    input  logic        in_valid,
    input  logic [31:0] in_alu_result,
    input  logic [31:0] in_store_data,
    input  logic [4:0]  in_rd_addr,

    input  logic [1:0]  in_result_src,
    input  logic        in_reg_write,
    input  logic        in_mem_write,
    input  logic [2:0]  in_funct3,

    input  logic [31:0] in_imm,
    input  logic [31:0] in_pc_plus_4,

    output logic        out_valid,
    output logic [31:0] out_alu_result,
    output logic [31:0] out_store_data,
    output logic [4:0]  out_rd_addr,

    output logic [1:0]  out_result_src,
    output logic        out_reg_write,
    output logic        out_mem_write,
    output logic [2:0]  out_funct3,

    output logic [31:0] out_imm,
    output logic [31:0] out_pc_plus_4
);

always_ff @(posedge clk) begin
    if (reset || !in_valid) begin
        out_valid       <= 1'b0;
        out_alu_result  <= 32'b0;
        out_store_data  <= 32'b0;
        out_rd_addr     <= 5'b0;
        out_result_src  <= 2'b0;
        out_reg_write   <= 1'b0;
        out_mem_write   <= 1'b0;
        out_funct3      <= 3'b0;
        out_imm         <= 32'b0;
        out_pc_plus_4   <= 32'b0;
    end
    else begin
        out_valid       <= in_valid;
        out_alu_result  <= in_alu_result;
        out_store_data  <= in_store_data;
        out_rd_addr     <= in_rd_addr;
        out_result_src  <= in_result_src;
        out_reg_write   <= in_reg_write;
        out_mem_write   <= in_mem_write;
        out_funct3      <= in_funct3;
        out_imm         <= in_imm;
        out_pc_plus_4   <= in_pc_plus_4;
    end
end

endmodule
