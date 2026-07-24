module pipeline_ex (
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

    input  logic        fwd_ex_mem_valid,
    input  logic        fwd_ex_mem_reg_write,
    input  logic [4:0]  fwd_ex_mem_rd_addr,
    input  logic [1:0]  fwd_ex_mem_result_src,
    input  logic [31:0] fwd_ex_mem_data,

    input  logic        fwd_mem_wb_valid,
    input  logic        fwd_mem_wb_reg_write,
    input  logic [4:0]  fwd_mem_wb_rd_addr,
    input  logic [31:0] fwd_mem_wb_data,

    output logic        out_valid,
    output logic [31:0] out_alu_result,
    output logic [31:0] out_store_data,
    output logic [4:0]  out_rd_addr,

    output logic [1:0]  out_result_src,
    output logic        out_reg_write,
    output logic        out_mem_write,
    output logic [2:0]  out_funct3,

    output logic [31:0] out_imm,
    output logic [31:0] out_pc_plus_4,

    output logic        out_redirect,
    output logic [31:0] out_redirect_pc
);

    localparam logic [2:0] BR_BEQ  = 3'd1;
    localparam logic [2:0] BR_BNE  = 3'd2;
    localparam logic [2:0] BR_BLT  = 3'd3;
    localparam logic [2:0] BR_BGE  = 3'd4;
    localparam logic [2:0] BR_BLTU = 3'd5;
    localparam logic [2:0] BR_BGEU = 3'd6;

    localparam logic [1:0] JMP_JAL  = 2'd1;
    localparam logic [1:0] JMP_JALR = 2'd2;

    localparam logic [1:0] RES_LOAD = 2'b01;

    logic [31:0] rs1_fwd;
    logic [31:0] rs2_fwd;

    always_comb begin
        rs1_fwd = in_rs1_data;
        if (in_uses_rs1 && in_rs1_addr != 5'd0) begin
            if (fwd_ex_mem_valid &&
                fwd_ex_mem_reg_write &&
                fwd_ex_mem_result_src != RES_LOAD &&
                fwd_ex_mem_rd_addr == in_rs1_addr) begin
                rs1_fwd = fwd_ex_mem_data;
            end
            else if (fwd_mem_wb_valid &&
                     fwd_mem_wb_reg_write &&
                     fwd_mem_wb_rd_addr == in_rs1_addr) begin
                rs1_fwd = fwd_mem_wb_data;
            end
        end
    end

    always_comb begin
        rs2_fwd = in_rs2_data;
        if (in_uses_rs2 && in_rs2_addr != 5'd0) begin
            if (fwd_ex_mem_valid &&
                fwd_ex_mem_reg_write &&
                fwd_ex_mem_result_src != RES_LOAD &&
                fwd_ex_mem_rd_addr == in_rs2_addr) begin
                rs2_fwd = fwd_ex_mem_data;
            end
            else if (fwd_mem_wb_valid &&
                     fwd_mem_wb_reg_write &&
                     fwd_mem_wb_rd_addr == in_rs2_addr) begin
                rs2_fwd = fwd_mem_wb_data;
            end
        end
    end

    logic [31:0] alu_a;
    logic [31:0] alu_b;
    logic [31:0] alu_result;

    assign alu_a = in_alu_a_pc ? in_pc  : rs1_fwd;
    assign alu_b = in_alu_src  ? in_imm : rs2_fwd;

    alu u_alu (
        .a      (alu_a),
        .b      (alu_b),
        .alu_op (in_alu_op),
        .result (alu_result)
    );

    logic branch_taken;

    always_comb begin
        branch_taken = 1'b0;
        if (in_valid && in_branch) begin
            case (in_branch_type)
                BR_BEQ:  branch_taken = (rs1_fwd == rs2_fwd);
                BR_BNE:  branch_taken = (rs1_fwd != rs2_fwd);
                BR_BLT:  branch_taken = ($signed(rs1_fwd) <  $signed(rs2_fwd));
                BR_BGE:  branch_taken = ($signed(rs1_fwd) >= $signed(rs2_fwd));
                BR_BLTU: branch_taken = (rs1_fwd <  rs2_fwd);
                BR_BGEU: branch_taken = (rs1_fwd >= rs2_fwd);
                default: branch_taken = 1'b0;
            endcase
        end
    end

    always_comb begin
        out_redirect    = 1'b0;
        out_redirect_pc = 32'b0;

        if (in_valid) begin
            if (in_jump_type == JMP_JAL) begin
                out_redirect    = 1'b1;
                out_redirect_pc = in_pc + in_imm;
            end
            else if (in_jump_type == JMP_JALR) begin
                out_redirect    = 1'b1;
                out_redirect_pc = (rs1_fwd + in_imm) & 32'hFFFF_FFFE;
            end
            else if (branch_taken) begin
                out_redirect    = 1'b1;
                out_redirect_pc = in_pc + in_imm;
            end
        end
    end

    assign out_valid       = in_valid;
    assign out_alu_result  = alu_result;
    assign out_store_data  = rs2_fwd;
    assign out_rd_addr     = in_rd_addr;

    assign out_result_src  = in_result_src;
    assign out_reg_write   = in_valid & in_reg_write;
    assign out_mem_write   = in_valid & in_mem_write;
    assign out_funct3      = in_funct3;

    assign out_imm         = in_imm;
    assign out_pc_plus_4   = in_pc_plus_4;

endmodule

