module alu (
    input logic [31:0] a,
    input logic [31:0] b,
    input logic [3:0] alu_op,
    output logic [31:0] result
);

localparam logic [3:0] ALU_ADD  = 4'b0000;
localparam logic [3:0] ALU_SUB  = 4'b0001;
localparam logic [3:0] ALU_AND  = 4'b0010;
localparam logic [3:0] ALU_OR   = 4'b0011;
localparam logic [3:0] ALU_XOR  = 4'b0100;
localparam logic [3:0] ALU_SLL  = 4'b0101;
localparam logic [3:0] ALU_SRL  = 4'b0110;
localparam logic [3:0] ALU_SRA  = 4'b0111;
localparam logic [3:0] ALU_SLT  = 4'b1000;
localparam logic [3:0] ALU_SLTU = 4'b1001;

always_comb begin
    case (alu_op)
        ALU_ADD : result = a + b;
        ALU_SUB : result = a - b;
        ALU_AND : result = a & b;
        ALU_OR  : result = a | b;
        ALU_XOR : result = a ^ b;
        ALU_SLL : result = a << b[4:0];
        ALU_SRL : result = a >> b[4:0];
        ALU_SRA : result = $signed(a) >>> b[4:0];
        ALU_SLT : result = {
                31'b0, $signed(a) < $signed(b)
        };
        ALU_SLTU: result = {31'b0, a < b};
        default: result = 32'b0;
    endcase
end

endmodule
