module pipeline_mem (
    input logic reset,
    input logic in_valid,
    input logic [31:0] in_alu_result,
    input logic [31:0] in_store_data,
    input logic [4:0] in_rd_addr,
    input logic [1:0] in_result_src,
    input logic in_reg_write,
    input logic in_mem_write,
    input logic [2:0] in_funct3,
    input logic [31:0] in_imm,
    input logic [31:0] in_pc_plus_4,
    input logic [31:0] data_read_data,
    output logic [31:0] data_addr,
    output logic [31:0] data_write_data,
    output logic [3:0] data_write_strb,
    output logic data_write_en,
    output logic out_valid,
    output logic [31:0] out_alu_result,
    output logic [31:0] out_load_data,
    output logic [4:0] out_rd_addr,
    output logic [1:0] out_result_src,
    output logic out_reg_write,
    output logic [31:0] out_imm,
    output logic [31:0] out_pc_plus_4
);

logic [7:0] selected_byte;
logic [15:0] selected_half;

assign data_addr = in_alu_result;
assign selected_byte = data_read_data[8 * in_alu_result[1:0] +: 8];
assign selected_half = in_alu_result[1] ? data_read_data[31:16] : data_read_data[15:0];

always_comb begin
    out_load_data = 32'b0;
    if (in_valid && in_result_src == 2'b01) begin
        case (in_funct3)
            3'b000: out_load_data = {{24{selected_byte[7]}}, selected_byte};
            3'b001: if (!in_alu_result[0]) out_load_data = {{16{selected_half[15]}}, selected_half};
            3'b010: if (in_alu_result[1:0] == 2'b00) out_load_data = data_read_data;
            3'b100: out_load_data = {24'b0, selected_byte};
            3'b101: if (!in_alu_result[0]) out_load_data = {16'b0, selected_half};
            default: out_load_data = 32'b0;
        endcase
    end
end

always_comb begin
    data_write_data = 32'b0;
    data_write_strb = 4'b0;
    if (in_valid && in_mem_write && !reset) begin
        case (in_funct3)
            3'b000: begin
                data_write_data = {24'b0, in_store_data[7:0]} << (8 * in_alu_result[1:0]);
                data_write_strb = 4'b0001 << in_alu_result[1:0];
            end
            3'b001: if (!in_alu_result[0]) begin
                data_write_data = {16'b0, in_store_data[15:0]} << (8 * in_alu_result[1:0]);
                data_write_strb = 4'b0011 << in_alu_result[1:0];
            end
            3'b010: if (in_alu_result[1:0] == 2'b00) begin
                data_write_data = in_store_data;
                data_write_strb = 4'b1111;
            end
            default: begin
            end
        endcase
    end
end

assign data_write_en = in_valid && in_mem_write && !reset && (data_write_strb != 4'b0);
assign out_valid = in_valid;
assign out_alu_result = in_alu_result;
assign out_rd_addr = in_rd_addr;
assign out_result_src = in_result_src;
assign out_reg_write = in_valid && in_reg_write;
assign out_imm = in_imm;
assign out_pc_plus_4 = in_pc_plus_4;

endmodule
