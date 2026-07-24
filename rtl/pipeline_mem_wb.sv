module pipeline_mem_wb (
    input logic clk,
    input logic reset,
    input logic in_valid,
    input logic [31:0] in_pc,
    input logic [31:0] in_alu_result,
    input logic [31:0] in_load_data,
    input logic [4:0] in_rd_addr,
    input logic [1:0] in_result_src,
    input logic in_reg_write,
    input logic [31:0] in_imm,
    input logic [31:0] in_pc_plus_4,
    output logic out_valid,
    output logic [31:0] out_pc,
    output logic [31:0] out_alu_result,
    output logic [31:0] out_load_data,
    output logic [4:0] out_rd_addr,
    output logic [1:0] out_result_src,
    output logic out_reg_write,
    output logic [31:0] out_imm,
    output logic [31:0] out_pc_plus_4
);

always_ff @(posedge clk) begin
    if (reset || !in_valid) begin
        out_valid <= 1'b0;
        out_pc <= 32'b0;
        out_alu_result <= 32'b0;
        out_load_data <= 32'b0;
        out_rd_addr <= 5'b0;
        out_result_src <= 2'b0;
        out_reg_write <= 1'b0;
        out_imm <= 32'b0;
        out_pc_plus_4 <= 32'b0;
    end
    else begin
        out_valid <= in_valid;
        out_pc <= in_pc;
        out_alu_result <= in_alu_result;
        out_load_data <= in_load_data;
        out_rd_addr <= in_rd_addr;
        out_result_src <= in_result_src;
        out_reg_write <= in_reg_write;
        out_imm <= in_imm;
        out_pc_plus_4 <= in_pc_plus_4;
    end
end

endmodule
