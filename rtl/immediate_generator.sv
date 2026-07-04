module immediate_generator (
    input  logic [31:0] instr,
    input  logic [1:0]  imm_type,
    output logic [31:0] imm
);

localparam logic [1:0] IMM_I  = 2'b00;
localparam logic [1:0] IMM_S  = 2'b01;
localparam logic [1:0] IMM_B  = 2'b10;

always_comb begin
    case (imm_type)
        IMM_I: imm = {{20{instr[31]}}, instr[31:20]};
        IMM_S:  imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};
        IMM_B:  imm = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};

        default: imm = 32'b0;
    endcase
end

endmodule
