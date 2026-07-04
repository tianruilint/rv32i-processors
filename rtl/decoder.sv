module decoder (
    input  logic [6:0] opcode,
    input  logic [2:0] funct3,
    input  logic [6:0] funct7,

    output logic       reg_write,
    output logic       alu_src,
    output logic       mem_write,
    output logic       result_src,
    output logic       branch,
    output logic [1:0] imm_type,
    output logic [3:0] alu_op
);

localparam logic [6:0] R_TYPE = 7'b0110011;
localparam logic [6:0] I_TYPE = 7'b0010011;
localparam logic [6:0] LW     = 7'b0000011;
localparam logic [6:0] SW     = 7'b0100011;
localparam logic [6:0] BRANCH = 7'b1100011;

localparam logic [3:0] ALU_ADD = 4'b0000;
localparam logic [3:0] ALU_SUB = 4'b0001;
localparam logic [3:0] ALU_AND = 4'b0010;
localparam logic [3:0] ALU_OR  = 4'b0011;
localparam logic [3:0] ALU_SLT = 4'b1000;

localparam logic [1:0] IMM_I = 2'b00;
localparam logic [1:0] IMM_S = 2'b01;
localparam logic [1:0] IMM_B = 2'b10;

always_comb begin
    reg_write  = 1'b0;
    alu_src    = 1'b0;
    mem_write  = 1'b0;
    result_src = 1'b0;
    branch     = 1'b0;
    imm_type   = IMM_I;
    alu_op     = ALU_ADD;

    case (opcode)
        R_TYPE: begin
            case ({funct7, funct3})
                {7'b0000000, 3'b000}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_ADD;
                end
                {7'b0100000, 3'b000}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_SUB;
                end
                {7'b0000000, 3'b111}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_AND;
                end
                {7'b0000000, 3'b110}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_OR;
                end
                {7'b0000000, 3'b010}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_SLT;
                end
                default: begin
                end
            endcase
        end

        I_TYPE: begin
            case (funct3)
                3'b000: begin
                    reg_write = 1'b1;
                    alu_src   = 1'b1;
                    imm_type  = IMM_I;
                    alu_op    = ALU_ADD;
                end
                3'b111: begin
                    reg_write = 1'b1;
                    alu_src   = 1'b1;
                    imm_type  = IMM_I;
                    alu_op    = ALU_AND;
                end
                3'b110: begin
                    reg_write = 1'b1;
                    alu_src   = 1'b1;
                    imm_type  = IMM_I;
                    alu_op    = ALU_OR;
                end
                3'b010: begin
                    reg_write = 1'b1;
                    alu_src   = 1'b1;
                    imm_type  = IMM_I;
                    alu_op    = ALU_SLT;
                end
                default: begin
                end
            endcase
        end

        LW: begin
            if (funct3 == 3'b010) begin
                reg_write  = 1'b1;
                alu_src    = 1'b1;
                result_src = 1'b1;
                imm_type   = IMM_I;
                alu_op     = ALU_ADD;
            end
        end

        SW: begin
            if (funct3 == 3'b010) begin
                alu_src   = 1'b1;
                mem_write = 1'b1;
                imm_type  = IMM_S;
                alu_op    = ALU_ADD;
            end
        end

        BRANCH: begin
            if (funct3 == 3'b000) begin
                branch   = 1'b1;
                imm_type = IMM_B;
                alu_op   = ALU_SUB;
            end
        end

        default: begin
        end
    endcase
end

endmodule
