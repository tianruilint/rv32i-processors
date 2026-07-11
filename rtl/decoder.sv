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
    output logic [3:0] alu_op,
    output logic [2:0] branch_type
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
localparam logic [3:0] ALU_XOR = 4'b0100;
localparam logic [3:0] ALU_SLTU = 4'b1001;
localparam logic [3:0] ALU_SLL = 4'b0101;
localparam logic [3:0] ALU_SRL = 4'b0110;
localparam logic [3:0] ALU_SRA = 4'b0111;

localparam logic [1:0] IMM_I = 2'b00;
localparam logic [1:0] IMM_S = 2'b01;
localparam logic [1:0] IMM_B = 2'b10;

localparam logic [2:0] NONE = 3'b000;
localparam logic [2:0] BEQ  = 3'b001;
localparam logic [2:0] BNE  = 3'b010;
localparam logic [2:0] BLT  = 3'b011;
localparam logic [2:0] BGE  = 3'b100;
localparam logic [2:0] BLTU = 3'b101;
localparam logic [2:0] BGEU = 3'b110;

always_comb begin
    reg_write   = 1'b0;
    alu_src     = 1'b0;
    mem_write   = 1'b0;
    result_src  = 1'b0;
    branch      = 1'b0;
    imm_type    = IMM_I;
    alu_op      = ALU_ADD;
    branch_type = NONE;

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
                {7'b0000000, 3'b100}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_XOR;
                end
                {7'b0000000, 3'b011}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_SLTU;
                end
                {7'b0000000, 3'b001}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_SLL;
                end
                {7'b0000000, 3'b101}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_SRL;
                end
                {7'b0100000, 3'b101}: begin
                    reg_write = 1'b1;
                    alu_op    = ALU_SRA;
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
                3'b100: begin
                    reg_write = 1'b1;
                    alu_src   = 1'b1;
                    imm_type  = IMM_I;
                    alu_op    = ALU_XOR;
                end
                3'b011: begin
                    reg_write = 1'b1;
                    alu_src   = 1'b1;
                    imm_type  = IMM_I;
                    alu_op    = ALU_SLTU;
                end
                3'b001: begin
                    if (funct7 == 7'b0000000) begin
                        reg_write = 1'b1;
                        alu_src   = 1'b1;
                        imm_type  = IMM_I;
                        alu_op    = ALU_SLL;
                    end
                end
                3'b101: begin
                    if (funct7 == 7'b0100000) begin
                        alu_op = ALU_SRA;
                        reg_write = 1'b1;
                        alu_src   = 1'b1;
                        imm_type  = IMM_I;
                    end
                    else if (funct7 == 7'b0000000) begin
                        alu_op = ALU_SRL;
                        reg_write = 1'b1;
                        alu_src   = 1'b1;
                        imm_type  = IMM_I;
                    end
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
                branch_type = BEQ;
            end
            if (funct3 == 3'b001) begin
                branch   = 1'b1;
                imm_type = IMM_B;
                alu_op   = ALU_SUB;
                branch_type = BNE;
            end
            if (funct3 == 3'b100) begin
                branch   = 1'b1;
                imm_type = IMM_B;
                alu_op   = ALU_SUB;
                branch_type = BLT;
            end
            if (funct3 == 3'b101) begin
                branch   = 1'b1;
                imm_type = IMM_B;
                alu_op   = ALU_SUB;
                branch_type = BGE;
            end
            if (funct3 == 3'b110) begin
                branch   = 1'b1;
                imm_type = IMM_B;
                alu_op   = ALU_SUB;
                branch_type = BLTU;
            end
            if (funct3 == 3'b111) begin
                branch   = 1'b1;
                imm_type = IMM_B;
                alu_op   = ALU_SUB;
                branch_type = BGEU;
            end
        end

        default: begin
        end
    endcase
end

endmodule
