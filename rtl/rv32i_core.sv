module rv32i_core (
    input  logic clk,
    input  logic reset,
    input  logic [31:0] instr,
    input  logic [31:0] data_read_data,
    output logic [31:0] current_pc,
    output logic [31:0] data_write_data,
    output logic [31:0] data_addr,
    output logic data_write_en,
    output logic [3:0] data_write_strb
);


logic [6:0]  opcode;
logic [2:0]  funct3;
logic [6:0]  funct7;
logic        reg_write_dec;
logic        alu_src;
logic        mem_write;
logic [1:0]  result_src;
logic        branch;
logic [2:0]  imm_type;
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
logic [2:0]  branch_type_dec;
logic        eq;
logic        lt_signed;
logic        lt_unsigned;
logic [31:0] load_data;
logic [7:0]  selected_byte;
logic [15:0] selected_half;
logic        alu_a_pc;
logic [1:0]  jump_type;
logic [31:0] alu_a;
logic [31:0] pc_plus_4;

assign opcode = instr[6:0];
assign funct3 = instr[14:12];
assign funct7 = instr[31:25];
assign rf_we = (reset) ? 1'b0 : reg_write_dec;
assign rs1_addr = instr[19:15];
assign rs2_addr = instr[24:20];
assign rd_addr = instr[11:7];
assign alu_b = (alu_src) ? imm : rs2_data;

always_comb begin
    case (result_src)
        2'b00: wb_data = alu_result;
        2'b01: wb_data = load_data;
        2'b10: wb_data = imm;
        2'b11: wb_data = pc_plus_4;
        default: wb_data = alu_result;
    endcase
end

assign data_addr = alu_result;
always_comb begin
    data_write_data = 32'b0;
    data_write_strb = 4'b0000;

    if (mem_write && !reset) begin
        case (funct3)
            3'b000: begin
                case (alu_result[1:0])
                    2'b00: begin
                        data_write_data = {24'b0, rs2_data[7:0]};
                        data_write_strb = 4'b0001;
                    end
                    2'b01: begin
                        data_write_data = {16'b0, rs2_data[7:0], 8'b0};
                        data_write_strb = 4'b0010;
                    end
                    2'b10: begin
                        data_write_data = {8'b0, rs2_data[7:0], 16'b0};
                        data_write_strb = 4'b0100;
                    end
                    2'b11: begin
                        data_write_data = {rs2_data[7:0], 24'b0};
                        data_write_strb = 4'b1000;
                    end
                    default: begin
                        data_write_data = 32'b0;
                        data_write_strb = 4'b0000;
                    end
                endcase
            end

            3'b001: begin
                case (alu_result[1:0])
                    2'b00: begin
                        data_write_data = {16'b0, rs2_data[15:0]};
                        data_write_strb = 4'b0011;
                    end
                    2'b10: begin
                        data_write_data = {rs2_data[15:0], 16'b0};
                        data_write_strb = 4'b1100;
                    end
                    default: begin
                        data_write_data = 32'b0;
                        data_write_strb = 4'b0000;
                    end
                endcase
            end

            3'b010: begin
                if (alu_result[1:0] == 2'b00) begin
                    data_write_data = rs2_data;
                    data_write_strb = 4'b1111;
                end
                else begin
                    data_write_data = 32'b0;
                    data_write_strb = 4'b0000;
                end
            end

            default: begin
                data_write_data = 32'b0;
                data_write_strb = 4'b0000;
            end
        endcase
    end
end
assign data_write_en = (reset) ? 1'b0 : mem_write;
assign eq = (rs1_data == rs2_data);
assign lt_signed = ($signed(rs1_data) < $signed(rs2_data));
assign lt_unsigned = (rs1_data < rs2_data);
always_comb begin
    branch_taken = 1'b0;
    if (branch) begin
        case (branch_type_dec)
            3'b001: branch_taken =  eq;
            3'b010: branch_taken = ~eq;
            3'b011: branch_taken =  lt_signed;
            3'b100: branch_taken = ~lt_signed;
            3'b101: branch_taken =  lt_unsigned;
            3'b110: branch_taken = ~lt_unsigned;
            default: branch_taken = 1'b0;
        endcase
    end
end
assign take_target = branch_taken | (jump_type == 2'b01) | (jump_type == 2'b10);
always_comb begin
    case (jump_type)
        2'b00: target_pc = current_pc + imm;
        2'b01: target_pc = current_pc + imm;
        2'b10: target_pc = {alu_result[31:1], 1'b0};
        default: target_pc = current_pc + imm;
    endcase
end
always_comb begin
    case (alu_result[1:0])
        2'b00: selected_byte = data_read_data[7:0];
        2'b01: selected_byte = data_read_data[15:8];
        2'b10: selected_byte = data_read_data[23:16];
        2'b11: selected_byte = data_read_data[31:24];
        default: selected_byte = 8'b0;
    endcase
end
always_comb begin
    case (alu_result[1:0])
        2'b00: selected_half = data_read_data[15:0];
        2'b10: selected_half = data_read_data[31:16];
        default: selected_half = 16'b0;
    endcase
end
always_comb begin
    case (funct3)
        3'b000: load_data = {{24{selected_byte[7]}}, selected_byte};
        3'b001: load_data = {{16{selected_half[15]}}, selected_half};
        3'b010: load_data = data_read_data;
        3'b100: load_data = {24'b0, selected_byte};
        3'b101: load_data = {16'b0, selected_half};
        default: load_data = 32'b0;
    endcase
end
assign pc_plus_4 = current_pc + 4;
assign alu_a = (alu_a_pc) ? current_pc : rs1_data;





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
    .alu_op     (alu_op),
    .branch_type(branch_type_dec),
    .alu_a_pc   (alu_a_pc),
    .jump_type  (jump_type)
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
    .a          (alu_a),
    .b          (alu_b),
    .alu_op     (alu_op),
    .result     (alu_result)
);


endmodule
