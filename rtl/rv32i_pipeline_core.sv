module rv32i_pipeline_core (
    input logic clk,
    input logic reset,
    input logic [31:0] instr,
    input logic [31:0] data_read_data,
    output logic [31:0] current_pc,
    output logic [31:0] data_addr,
    output logic [31:0] data_write_data,
    output logic [3:0] data_write_strb,
    output logic data_write_en,
    output logic retire_valid,
    output logic [31:0] retire_pc,
    output logic [31:0] cycle_count,
    output logic [31:0] retired_count
);

logic if_id_valid;
logic [31:0] if_id_pc, if_id_instr, if_id_pc_plus_4;

logic id_valid;
logic [31:0] id_pc, id_pc_plus_4, id_rs1_data, id_rs2_data, id_imm;
logic [4:0] id_rs1_addr, id_rs2_addr, id_rd_addr;
logic [2:0] id_funct3, id_branch_type;
logic [3:0] id_alu_op;
logic [1:0] id_result_src, id_jump_type;
logic id_alu_src, id_alu_a_pc, id_reg_write, id_mem_write, id_branch;
logic id_uses_rs1, id_uses_rs2;

logic id_ex_valid;
logic [31:0] id_ex_pc, id_ex_pc_plus_4, id_ex_rs1_data, id_ex_rs2_data, id_ex_imm;
logic [4:0] id_ex_rs1_addr, id_ex_rs2_addr, id_ex_rd_addr;
logic [2:0] id_ex_funct3, id_ex_branch_type;
logic [3:0] id_ex_alu_op;
logic [1:0] id_ex_result_src, id_ex_jump_type;
logic id_ex_alu_src, id_ex_alu_a_pc, id_ex_reg_write, id_ex_mem_write, id_ex_branch;
logic id_ex_uses_rs1, id_ex_uses_rs2;

logic ex_valid, ex_reg_write, ex_mem_write, redirect;
logic [31:0] ex_alu_result, ex_store_data, ex_imm, ex_pc_plus_4, redirect_pc;
logic [4:0] ex_rd_addr;
logic [1:0] ex_result_src;
logic [2:0] ex_funct3;

logic ex_mem_valid, ex_mem_reg_write, ex_mem_mem_write;
logic [31:0] ex_mem_pc, ex_mem_alu_result, ex_mem_store_data, ex_mem_imm, ex_mem_pc_plus_4;
logic [4:0] ex_mem_rd_addr;
logic [1:0] ex_mem_result_src;
logic [2:0] ex_mem_funct3;

logic mem_valid, mem_reg_write;
logic [31:0] mem_alu_result, mem_load_data, mem_imm, mem_pc_plus_4;
logic [4:0] mem_rd_addr;
logic [1:0] mem_result_src;

logic wb_valid, wb_reg_write;
logic [31:0] wb_pc, wb_alu_result, wb_load_data, wb_imm, wb_pc_plus_4, wb_data;
logic [4:0] wb_rd_addr;
logic [1:0] wb_result_src;

logic stall, bubble, flush;
logic [31:0] ex_mem_forward_data;

pipeline_frontend u_frontend (
    .clk(clk), .reset(reset), .stall(stall),
    .redirect(redirect), .redirect_pc(redirect_pc), .instr(instr),
    .current_pc(current_pc), .if_id_valid(if_id_valid),
    .if_id_instr(if_id_instr), .if_id_pc_plus_4(if_id_pc_plus_4),
    .if_id_pc(if_id_pc)
);

pipeline_id u_id (
    .clk(clk), .reset(reset),
    .if_id_valid(if_id_valid), .if_id_pc(if_id_pc),
    .if_id_instr(if_id_instr), .if_id_pc_plus_4(if_id_pc_plus_4),
    .wb_valid(wb_valid), .wb_reg_write(wb_reg_write),
    .wb_rd_addr(wb_rd_addr), .wb_data(wb_data),
    .out_valid(id_valid), .out_pc(id_pc), .out_pc_plus_4(id_pc_plus_4),
    .out_rs1_addr(id_rs1_addr), .out_rs2_addr(id_rs2_addr), .out_rd_addr(id_rd_addr),
    .out_rs1_data(id_rs1_data), .out_rs2_data(id_rs2_data), .out_imm(id_imm),
    .out_funct3(id_funct3), .out_alu_op(id_alu_op), .out_alu_src(id_alu_src),
    .out_alu_a_pc(id_alu_a_pc), .out_result_src(id_result_src),
    .out_reg_write(id_reg_write), .out_mem_write(id_mem_write), .out_branch(id_branch),
    .out_branch_type(id_branch_type), .out_jump_type(id_jump_type),
    .out_uses_rs1(id_uses_rs1), .out_uses_rs2(id_uses_rs2)
);

pipeline_hazard u_hazard (
    .id_valid(id_valid), .id_rs1_addr(id_rs1_addr), .id_rs2_addr(id_rs2_addr),
    .id_uses_rs1(id_uses_rs1), .id_uses_rs2(id_uses_rs2),
    .ex_valid(id_ex_valid), .ex_reg_write(id_ex_reg_write),
    .ex_result_src(id_ex_result_src), .ex_rd_addr(id_ex_rd_addr),
    .redirect(redirect), .stall(stall), .bubble(bubble), .flush(flush)
);

pipeline_id_ex u_id_ex (
    .clk(clk), .reset(reset), .flush(flush), .bubble(bubble),
    .in_valid(id_valid), .in_pc(id_pc), .in_pc_plus_4(id_pc_plus_4),
    .in_rs1_addr(id_rs1_addr), .in_rs2_addr(id_rs2_addr), .in_rd_addr(id_rd_addr),
    .in_rs1_data(id_rs1_data), .in_rs2_data(id_rs2_data), .in_imm(id_imm),
    .in_funct3(id_funct3), .in_alu_op(id_alu_op), .in_alu_src(id_alu_src),
    .in_alu_a_pc(id_alu_a_pc), .in_result_src(id_result_src),
    .in_reg_write(id_reg_write), .in_mem_write(id_mem_write), .in_branch(id_branch),
    .in_branch_type(id_branch_type), .in_jump_type(id_jump_type),
    .in_uses_rs1(id_uses_rs1), .in_uses_rs2(id_uses_rs2),
    .out_valid(id_ex_valid), .out_pc(id_ex_pc), .out_pc_plus_4(id_ex_pc_plus_4),
    .out_rs1_addr(id_ex_rs1_addr), .out_rs2_addr(id_ex_rs2_addr), .out_rd_addr(id_ex_rd_addr),
    .out_rs1_data(id_ex_rs1_data), .out_rs2_data(id_ex_rs2_data), .out_imm(id_ex_imm),
    .out_funct3(id_ex_funct3), .out_alu_op(id_ex_alu_op), .out_alu_src(id_ex_alu_src),
    .out_alu_a_pc(id_ex_alu_a_pc), .out_result_src(id_ex_result_src),
    .out_reg_write(id_ex_reg_write), .out_mem_write(id_ex_mem_write), .out_branch(id_ex_branch),
    .out_branch_type(id_ex_branch_type), .out_jump_type(id_ex_jump_type),
    .out_uses_rs1(id_ex_uses_rs1), .out_uses_rs2(id_ex_uses_rs2)
);

always_comb begin
    case (ex_mem_result_src)
        2'b00: ex_mem_forward_data = ex_mem_alu_result;
        2'b10: ex_mem_forward_data = ex_mem_imm;
        2'b11: ex_mem_forward_data = ex_mem_pc_plus_4;
        default: ex_mem_forward_data = 32'b0;
    endcase
end

pipeline_ex u_ex (
    .in_valid(id_ex_valid), .in_pc(id_ex_pc), .in_pc_plus_4(id_ex_pc_plus_4),
    .in_rs1_addr(id_ex_rs1_addr), .in_rs2_addr(id_ex_rs2_addr), .in_rd_addr(id_ex_rd_addr),
    .in_rs1_data(id_ex_rs1_data), .in_rs2_data(id_ex_rs2_data), .in_imm(id_ex_imm),
    .in_funct3(id_ex_funct3), .in_alu_op(id_ex_alu_op), .in_alu_src(id_ex_alu_src),
    .in_alu_a_pc(id_ex_alu_a_pc), .in_result_src(id_ex_result_src),
    .in_reg_write(id_ex_reg_write), .in_mem_write(id_ex_mem_write), .in_branch(id_ex_branch),
    .in_branch_type(id_ex_branch_type), .in_jump_type(id_ex_jump_type),
    .in_uses_rs1(id_ex_uses_rs1), .in_uses_rs2(id_ex_uses_rs2),
    .fwd_ex_mem_valid(ex_mem_valid), .fwd_ex_mem_reg_write(ex_mem_reg_write),
    .fwd_ex_mem_rd_addr(ex_mem_rd_addr), .fwd_ex_mem_result_src(ex_mem_result_src),
    .fwd_ex_mem_data(ex_mem_forward_data),
    .fwd_mem_wb_valid(wb_valid), .fwd_mem_wb_reg_write(wb_reg_write),
    .fwd_mem_wb_rd_addr(wb_rd_addr), .fwd_mem_wb_data(wb_data),
    .out_valid(ex_valid), .out_alu_result(ex_alu_result), .out_store_data(ex_store_data),
    .out_rd_addr(ex_rd_addr), .out_result_src(ex_result_src),
    .out_reg_write(ex_reg_write), .out_mem_write(ex_mem_write), .out_funct3(ex_funct3),
    .out_imm(ex_imm), .out_pc_plus_4(ex_pc_plus_4),
    .out_redirect(redirect), .out_redirect_pc(redirect_pc)
);

pipeline_ex_mem u_ex_mem (
    .clk(clk), .reset(reset), .in_valid(ex_valid),
    .in_alu_result(ex_alu_result), .in_store_data(ex_store_data), .in_rd_addr(ex_rd_addr),
    .in_result_src(ex_result_src), .in_reg_write(ex_reg_write), .in_mem_write(ex_mem_write),
    .in_funct3(ex_funct3), .in_imm(ex_imm), .in_pc_plus_4(ex_pc_plus_4),
    .out_valid(ex_mem_valid), .out_alu_result(ex_mem_alu_result),
    .out_store_data(ex_mem_store_data), .out_rd_addr(ex_mem_rd_addr),
    .out_result_src(ex_mem_result_src), .out_reg_write(ex_mem_reg_write),
    .out_mem_write(ex_mem_mem_write), .out_funct3(ex_mem_funct3),
    .out_imm(ex_mem_imm), .out_pc_plus_4(ex_mem_pc_plus_4)
);

always_ff @(posedge clk) begin
    if (reset || !ex_valid)
        ex_mem_pc <= 32'b0;
    else
        ex_mem_pc <= id_ex_pc;
end

pipeline_mem u_mem (
    .reset(reset), .in_valid(ex_mem_valid), .in_alu_result(ex_mem_alu_result),
    .in_store_data(ex_mem_store_data), .in_rd_addr(ex_mem_rd_addr),
    .in_result_src(ex_mem_result_src), .in_reg_write(ex_mem_reg_write),
    .in_mem_write(ex_mem_mem_write), .in_funct3(ex_mem_funct3),
    .in_imm(ex_mem_imm), .in_pc_plus_4(ex_mem_pc_plus_4),
    .data_read_data(data_read_data), .data_addr(data_addr),
    .data_write_data(data_write_data), .data_write_strb(data_write_strb),
    .data_write_en(data_write_en), .out_valid(mem_valid),
    .out_alu_result(mem_alu_result), .out_load_data(mem_load_data),
    .out_rd_addr(mem_rd_addr), .out_result_src(mem_result_src),
    .out_reg_write(mem_reg_write), .out_imm(mem_imm), .out_pc_plus_4(mem_pc_plus_4)
);

pipeline_mem_wb u_mem_wb (
    .clk(clk), .reset(reset), .in_valid(mem_valid), .in_pc(ex_mem_pc),
    .in_alu_result(mem_alu_result), .in_load_data(mem_load_data),
    .in_rd_addr(mem_rd_addr), .in_result_src(mem_result_src),
    .in_reg_write(mem_reg_write), .in_imm(mem_imm), .in_pc_plus_4(mem_pc_plus_4),
    .out_valid(wb_valid), .out_pc(wb_pc), .out_alu_result(wb_alu_result),
    .out_load_data(wb_load_data), .out_rd_addr(wb_rd_addr),
    .out_result_src(wb_result_src), .out_reg_write(wb_reg_write),
    .out_imm(wb_imm), .out_pc_plus_4(wb_pc_plus_4)
);

always_comb begin
    case (wb_result_src)
        2'b00: wb_data = wb_alu_result;
        2'b01: wb_data = wb_load_data;
        2'b10: wb_data = wb_imm;
        2'b11: wb_data = wb_pc_plus_4;
        default: wb_data = 32'b0;
    endcase
end

assign retire_valid = wb_valid && !reset;
assign retire_pc = wb_pc;

always_ff @(posedge clk) begin
    if (reset) begin
        cycle_count <= 32'b0;
        retired_count <= 32'b0;
    end
    else begin
        cycle_count <= cycle_count + 32'd1;
        if (retire_valid)
            retired_count <= retired_count + 32'd1;
    end
end

endmodule
