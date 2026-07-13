module immediate_generator (
    input  logic [31:0] instr,
    input  logic [2:0]  imm_type,
    output logic [31:0] imm
);

localparam logic [2:0] IMM_I  = 3'b000;
localparam logic [2:0] IMM_S  = 3'b001;
localparam logic [2:0] IMM_B  = 3'b010;
localparam logic [2:0] IMM_U  = 3'b011;
localparam logic [2:0] IMM_J  = 3'b100;

always_comb begin
    case (imm_type)
        IMM_I: imm = {{20{instr[31]}}, instr[31:20]};
        IMM_S: imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};
        IMM_B: imm = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
        IMM_U: imm = {instr[31:12], 12'b0};
        IMM_J: imm = {{12{instr[31]}}, instr[19:12], instr[20], instr[30:21], 1'b0};
        default: imm = 32'b0;
    endcase
end

endmodule
